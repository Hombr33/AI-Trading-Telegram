"""
Enhanced workflow management for the AI Trading Bot.
"""

import asyncio
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .error_handler import ErrorContext, with_error_handling
from .exceptions import TradingBotException
from .logging import (
    get_logger,
    log_error_with_context,
    log_operation_timing,
    log_system_event,
)

logger = get_logger(__name__)


class ComponentStatus(Enum):
    """Component status enumeration."""

    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RECOVERING = "recovering"


class Component:
    """Base component with lifecycle management."""

    def __init__(self, name: str):
        self.name = name
        self.status = ComponentStatus.STOPPED
        self.start_time = None
        self.last_error = None
        self.error_count = 0
        self.restart_count = 0
        self.max_restarts = 3

    async def start(self) -> bool:
        """Start the component."""
        self.status = ComponentStatus.STARTING
        start_time = time.time()

        try:
            result = await self._start_implementation()
            if result:
                self.status = ComponentStatus.RUNNING
                self.start_time = start_time
                self.error_count = 0
                log_system_event(self.name, "started", "Component started successfully")
            else:
                self.status = ComponentStatus.ERROR
                log_system_event(self.name, "start_failed", "Component failed to start")
            return result
        except Exception as e:
            self.status = ComponentStatus.ERROR
            self.last_error = e
            self.error_count += 1
            log_error_with_context(e, {"component": self.name, "operation": "start"})
            return False

    async def stop(self) -> bool:
        """Stop the component."""
        self.status = ComponentStatus.STOPPING

        try:
            result = await self._stop_implementation()
            self.status = ComponentStatus.STOPPED
            log_system_event(self.name, "stopped", "Component stopped successfully")
            return result
        except Exception as e:
            self.status = ComponentStatus.ERROR
            self.last_error = e
            log_error_with_context(e, {"component": self.name, "operation": "stop"})
            return False

    async def restart(self) -> bool:
        """Restart the component."""
        if self.restart_count >= self.max_restarts:
            logger.error(f"Maximum restart attempts reached for {self.name}")
            return False

        self.restart_count += 1
        log_system_event(
            self.name,
            "restarting",
            f"Restarting component (attempt {self.restart_count})",
        )

        await self.stop()
        await asyncio.sleep(2)  # Brief pause between stop and start
        return await self.start()

    async def health_check(self) -> bool:
        """Check component health."""
        try:
            return await self._health_check_implementation()
        except Exception as e:
            log_error_with_context(
                e, {"component": self.name, "operation": "health_check"}
            )
            return False

    async def _start_implementation(self) -> bool:
        """Override in subclasses."""
        return True

    async def _stop_implementation(self) -> bool:
        """Override in subclasses."""
        return True

    async def _health_check_implementation(self) -> bool:
        """Override in subclasses."""
        return self.status == ComponentStatus.RUNNING

    def get_status(self) -> Dict[str, Any]:
        """Get component status information."""
        uptime = time.time() - self.start_time if self.start_time else 0
        return {
            "name": self.name,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "error_count": self.error_count,
            "restart_count": self.restart_count,
            "last_error": str(self.last_error) if self.last_error else None,
        }


class WorkflowManager:
    """Manages application workflow and component orchestration."""

    def __init__(self):
        self.components: Dict[str, Component] = {}
        self.startup_order: List[str] = []
        self.shutdown_order: List[str] = []
        self.health_check_interval = 30  # seconds
        self.monitoring_task = None
        self.is_running = False

    def register_component(self, component: Component, startup_priority: int = 0):
        """Register a component with the workflow manager."""
        self.components[component.name] = component

        # Insert in startup order based on priority
        if component.name not in self.startup_order:
            self.startup_order.insert(startup_priority, component.name)

        # Reverse order for shutdown
        if component.name not in self.shutdown_order:
            self.shutdown_order.insert(0, component.name)

    @with_error_handling("workflow_startup", notify_telegram=True)
    async def startup(self) -> bool:
        """Start all components in the correct order."""
        log_system_event("workflow", "startup_begin", "Starting application components")

        startup_start = time.time()
        failed_components = []

        for component_name in self.startup_order:
            component = self.components.get(component_name)
            if not component:
                logger.warning(f"Component {component_name} not found")
                continue

            try:
                component_start = time.time()
                success = await component.start()
                log_operation_timing(
                    f"startup_{component_name}", component_start, time.time()
                )

                if not success:
                    failed_components.append(component_name)
                    logger.error(f"Failed to start component: {component_name}")
                else:
                    logger.info(f"Component started successfully: {component_name}")

            except Exception as e:
                failed_components.append(component_name)
                log_error_with_context(
                    e, {"component": component_name, "operation": "startup"}
                )

        # Start health monitoring
        if not failed_components:
            self.is_running = True
            self.monitoring_task = asyncio.create_task(self._health_monitoring_loop())

        startup_time = time.time() - startup_start
        log_operation_timing("workflow_startup", startup_start, time.time())

        if failed_components:
            log_system_event(
                "workflow",
                "startup_partial",
                f"Startup completed with failures: {failed_components}",
            )
            return False
        else:
            log_system_event(
                "workflow",
                "startup_complete",
                f"All components started successfully in {startup_time:.2f}s",
            )
            return True

    @with_error_handling("workflow_shutdown", notify_telegram=False)
    async def shutdown(self) -> bool:
        """Shutdown all components in reverse order."""
        log_system_event(
            "workflow", "shutdown_begin", "Shutting down application components"
        )

        self.is_running = False

        # Stop health monitoring
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        shutdown_start = time.time()
        failed_components = []

        for component_name in self.shutdown_order:
            component = self.components.get(component_name)
            if not component:
                continue

            try:
                success = await component.stop()
                if not success:
                    failed_components.append(component_name)

            except Exception as e:
                failed_components.append(component_name)
                log_error_with_context(
                    e, {"component": component_name, "operation": "shutdown"}
                )

        shutdown_time = time.time() - shutdown_start
        log_operation_timing("workflow_shutdown", shutdown_start, time.time())

        if failed_components:
            log_system_event(
                "workflow",
                "shutdown_partial",
                f"Shutdown completed with failures: {failed_components}",
            )
            return False
        else:
            log_system_event(
                "workflow",
                "shutdown_complete",
                f"All components shut down successfully in {shutdown_time:.2f}s",
            )
            return True

    async def _health_monitoring_loop(self):
        """Monitor component health and restart failed components."""
        while self.is_running:
            try:
                await asyncio.sleep(self.health_check_interval)

                for component_name, component in self.components.items():
                    try:
                        is_healthy = await component.health_check()

                        if (
                            not is_healthy
                            and component.status == ComponentStatus.RUNNING
                        ):
                            logger.warning(
                                f"Component {component_name} health check failed"
                            )

                            # Attempt restart if within limits
                            if component.restart_count < component.max_restarts:
                                logger.info(
                                    f"Attempting to restart unhealthy component: {component_name}"
                                )
                                await component.restart()
                            else:
                                logger.error(
                                    f"Component {component_name} exceeded restart limit"
                                )
                                component.status = ComponentStatus.ERROR

                    except Exception as e:
                        log_error_with_context(
                            e,
                            {"component": component_name, "operation": "health_check"},
                        )

            except asyncio.CancelledError:
                logger.info("Health monitoring cancelled")
                break
            except Exception as e:
                log_error_with_context(e, {"operation": "health_monitoring"})

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        component_statuses = {}
        healthy_count = 0
        total_count = len(self.components)

        for name, component in self.components.items():
            status = component.get_status()
            component_statuses[name] = status

            if status["status"] == ComponentStatus.RUNNING.value:
                healthy_count += 1

        return {
            "overall_health": healthy_count / total_count if total_count > 0 else 0,
            "healthy_components": healthy_count,
            "total_components": total_count,
            "components": component_statuses,
            "is_running": self.is_running,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
        self.operation_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self.start_time = time.time()

    def record_operation(
        self, operation: str, duration_ms: float, success: bool = True
    ):
        """Record operation performance."""
        if operation not in self.metrics:
            self.metrics[operation] = []
            self.operation_counts[operation] = 0
            self.error_counts[operation] = 0

        self.metrics[operation].append(duration_ms)
        self.operation_counts[operation] += 1

        if not success:
            self.error_counts[operation] += 1

        # Keep only last 1000 measurements
        if len(self.metrics[operation]) > 1000:
            self.metrics[operation] = self.metrics[operation][-1000:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}

        for operation, measurements in self.metrics.items():
            if measurements:
                summary[operation] = {
                    "count": self.operation_counts[operation],
                    "errors": self.error_counts[operation],
                    "error_rate": self.error_counts[operation]
                    / self.operation_counts[operation],
                    "avg_duration_ms": sum(measurements) / len(measurements),
                    "min_duration_ms": min(measurements),
                    "max_duration_ms": max(measurements),
                    "last_duration_ms": measurements[-1],
                }

        return {
            "uptime_seconds": time.time() - self.start_time,
            "operations": summary,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global instances
performance_monitor = PerformanceMonitor()
workflow_manager = WorkflowManager()
