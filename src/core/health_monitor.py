"""
Comprehensive health monitoring system for the AI Trading Bot.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

from .logging import get_logger, log_system_event, log_error_with_context
from .error_handler import with_error_handling
from .exceptions import TradingBotException

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check definition."""

    name: str
    check_function: Callable[[], bool]
    interval_seconds: int = 30
    timeout_seconds: int = 10
    critical: bool = False
    last_check: Optional[datetime] = None
    last_status: HealthStatus = HealthStatus.UNKNOWN
    consecutive_failures: int = 0
    max_failures: int = 3
    error_message: Optional[str] = None


@dataclass
class SystemHealth:
    """System health status."""

    overall_status: HealthStatus
    components: Dict[str, HealthStatus] = field(default_factory=dict)
    checks: Dict[str, HealthCheck] = field(default_factory=dict)
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    uptime_seconds: float = 0
    error_count_24h: int = 0
    warning_count_24h: int = 0


class HealthMonitor:
    """Comprehensive health monitoring system."""

    def __init__(self):
        self.health_checks: Dict[str, HealthCheck] = {}
        self.health_history: List[SystemHealth] = []
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.start_time = time.time()

        # Register default health checks
        self._register_default_checks()

    def _register_default_checks(self):
        """Register default system health checks."""
        self.register_health_check(
            "system_memory",
            self._check_memory_usage,
            interval_seconds=60,
            critical=True,
        )

        self.register_health_check(
            "disk_space",
            self._check_disk_space,
            interval_seconds=300,  # 5 minutes
            critical=True,
        )

        self.register_health_check(
            "active_connections",
            self._check_active_connections,
            interval_seconds=30,
            critical=False,
        )

    def register_health_check(
        self,
        name: str,
        check_function: Callable,
        interval_seconds: int = 30,
        timeout_seconds: int = 10,
        critical: bool = False,
        max_failures: int = 3,
    ):
        """Register a health check."""
        self.health_checks[name] = HealthCheck(
            name=name,
            check_function=check_function,
            interval_seconds=interval_seconds,
            timeout_seconds=timeout_seconds,
            critical=critical,
            max_failures=max_failures,
        )
        logger.info(f"Registered health check: {name}")

    async def start_monitoring(self):
        """Start health monitoring."""
        if self.is_running:
            logger.warning("Health monitoring already running")
            return

        self.is_running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        log_system_event("health_monitor", "started", "Health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_running = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        log_system_event("health_monitor", "stopped", "Health monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.is_running:
            try:
                current_time = datetime.now(timezone.utc)

                # Run health checks that are due
                for check_name, health_check in self.health_checks.items():
                    if self._should_run_check(health_check, current_time):
                        await self._run_health_check(health_check)

                # Update system health status
                await self._update_system_health()

                await asyncio.sleep(5)  # Check every 5 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error_with_context(e, {"operation": "health_monitoring_loop"})
                await asyncio.sleep(10)  # Longer pause on error

    def _should_run_check(
        self, health_check: HealthCheck, current_time: datetime
    ) -> bool:
        """Determine if a health check should run."""
        if health_check.last_check is None:
            return True

        time_since_last = (current_time - health_check.last_check).total_seconds()
        return time_since_last >= health_check.interval_seconds

    async def _run_health_check(self, health_check: HealthCheck):
        """Run individual health check."""
        health_check.last_check = datetime.now(timezone.utc)

        try:
            # Run check with timeout
            result = await asyncio.wait_for(
                self._execute_check(health_check.check_function),
                timeout=health_check.timeout_seconds,
            )

            if result:
                health_check.last_status = HealthStatus.HEALTHY
                health_check.consecutive_failures = 0
                health_check.error_message = None
            else:
                self._handle_check_failure(health_check, "Check returned False")

        except asyncio.TimeoutError:
            self._handle_check_failure(health_check, "Check timeout")
        except Exception as e:
            self._handle_check_failure(health_check, str(e))

    async def _execute_check(self, check_function: Callable) -> bool:
        """Execute check function safely."""
        if asyncio.iscoroutinefunction(check_function):
            return await check_function()
        else:
            return check_function()

    def _handle_check_failure(self, health_check: HealthCheck, error_message: str):
        """Handle health check failure."""
        health_check.consecutive_failures += 1
        health_check.error_message = error_message

        if health_check.consecutive_failures >= health_check.max_failures:
            health_check.last_status = (
                HealthStatus.CRITICAL if health_check.critical else HealthStatus.WARNING
            )

            log_system_event(
                "health_monitor",
                "check_failed",
                f"Health check {health_check.name} failed {health_check.consecutive_failures} times",
                context={"error": error_message, "critical": health_check.critical},
            )
        else:
            health_check.last_status = HealthStatus.WARNING

    async def _update_system_health(self):
        """Update overall system health status."""
        component_statuses = {}
        critical_failures = 0
        warnings = 0

        for check_name, health_check in self.health_checks.items():
            component_statuses[check_name] = health_check.last_status

            if health_check.last_status == HealthStatus.CRITICAL:
                critical_failures += 1
            elif health_check.last_status == HealthStatus.WARNING:
                warnings += 1

        # Determine overall status
        if critical_failures > 0:
            overall_status = HealthStatus.CRITICAL
        elif warnings > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY

        # Create system health snapshot
        system_health = SystemHealth(
            overall_status=overall_status,
            components=component_statuses,
            checks=self.health_checks.copy(),
            uptime_seconds=time.time() - self.start_time,
        )

        # Store in history (keep last 100 entries)
        self.health_history.append(system_health)
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]

    def get_current_health(self) -> SystemHealth:
        """Get current system health."""
        if self.health_history:
            return self.health_history[-1]

        return SystemHealth(
            overall_status=HealthStatus.UNKNOWN,
            uptime_seconds=time.time() - self.start_time,
        )

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for API endpoints."""
        current_health = self.get_current_health()

        return {
            "status": current_health.overall_status.value,
            "uptime_seconds": current_health.uptime_seconds,
            "components": {
                name: status.value for name, status in current_health.components.items()
            },
            "checks": {
                name: {
                    "status": check.last_status.value,
                    "last_check": (
                        check.last_check.isoformat() if check.last_check else None
                    ),
                    "consecutive_failures": check.consecutive_failures,
                    "error_message": check.error_message,
                }
                for name, check in current_health.checks.items()
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Default health check implementations
    async def _check_memory_usage(self) -> bool:
        """Check system memory usage."""
        try:
            import psutil

            memory = psutil.virtual_memory()
            return memory.percent < 90  # Alert if over 90% memory usage
        except ImportError:
            logger.warning("psutil not available for memory monitoring")
            return True  # Assume healthy if can't check
        except Exception as e:
            logger.error(f"Memory check error: {e}")
            return False

    async def _check_disk_space(self) -> bool:
        """Check disk space availability."""
        try:
            import psutil

            disk = psutil.disk_usage("/")
            return (disk.free / disk.total) > 0.1  # Alert if less than 10% free
        except ImportError:
            return True  # Assume healthy if can't check
        except Exception as e:
            logger.error(f"Disk space check error: {e}")
            return False

    async def _check_active_connections(self) -> bool:
        """Check if critical connections are active."""
        try:
            # Check if we can import main components
            from ..main import telegram_bot, socketio_bridge, platform_manager

            mt5_healthy = False
            if platform_manager:
                # Check if MT5 platform is available and connected
                mt5_executor = platform_manager.get_executor("mt5")
                mt5_healthy = mt5_executor and mt5_executor.is_connected
            telegram_healthy = telegram_bot and telegram_bot.is_running
            bridge_healthy = socketio_bridge and socketio_bridge.get_status().get(
                "connected", False
            )

            # At least MT5 or bridge should be healthy
            return mt5_healthy or bridge_healthy

        except Exception as e:
            logger.error(f"Connection check error: {e}")
            return False


# Global health monitor instance
health_monitor = HealthMonitor()
