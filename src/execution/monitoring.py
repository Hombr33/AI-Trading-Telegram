"""
Production-grade monitoring and health check utilities for execution module.
"""

from __future__ import annotations

import asyncio
import threading
import time
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..core.error_handler import with_error_handling
from ..core.logging import get_logger
from .interfaces import HealthStatus, IExecutor, IHealthCheckable

logger = get_logger(__name__)


class MetricType(Enum):
    """Types of metrics to collect."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    status: HealthStatus
    component: str
    timestamp: datetime
    response_time_ms: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class MetricData:
    """Metric data point."""

    name: str
    value: float
    timestamp: datetime
    type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)


class CircularBuffer:
    """Thread-safe circular buffer for storing metrics."""

    def __init__(self, maxsize: int):
        self._buffer = deque(maxlen=maxsize)
        self._lock = threading.Lock()

    def append(self, item: Any) -> None:
        """Add item to buffer."""
        with self._lock:
            self._buffer.append(item)

    def get_all(self) -> List[Any]:
        """Get all items from buffer."""
        with self._lock:
            return list(self._buffer)

    def get_recent(self, count: int) -> List[Any]:
        """Get most recent items."""
        with self._lock:
            return list(self._buffer)[-count:]

    def clear(self) -> None:
        """Clear buffer."""
        with self._lock:
            self._buffer.clear()

    def size(self) -> int:
        """Get current size."""
        with self._lock:
            return len(self._buffer)


class PerformanceMonitor:
    """Monitor performance metrics for executors."""

    def __init__(self, max_metrics: int = 10000):
        self._metrics = CircularBuffer(max_metrics)
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, CircularBuffer] = {}
        self._timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        with self._lock:
            self._counters[name] += value
            self._add_metric(name, value, MetricType.COUNTER, labels)

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric."""
        with self._lock:
            self._gauges[name] = value
            self._add_metric(name, value, MetricType.GAUGE, labels)

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a histogram value."""
        with self._lock:
            if name not in self._histograms:
                self._histograms[name] = CircularBuffer(1000)
            self._histograms[name].append(value)
            self._add_metric(name, value, MetricType.HISTOGRAM, labels)

    def record_timer(
        self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a timer duration."""
        with self._lock:
            self._timers[name].append(duration_ms)
            if len(self._timers[name]) > 1000:  # Keep only recent 1000 measurements
                self._timers[name] = self._timers[name][-1000:]
            self._add_metric(name, duration_ms, MetricType.TIMER, labels)

    def _add_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        labels: Optional[Dict[str, str]],
    ) -> None:
        """Add metric to buffer."""
        metric = MetricData(
            name=name,
            value=value,
            timestamp=datetime.now(timezone.utc),
            type=metric_type,
            labels=labels or {},
        )
        self._metrics.append(metric)

    def get_counter(self, name: str) -> float:
        """Get counter value."""
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        """Get gauge value."""
        return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Optional[Dict[str, float]]:
        """Get histogram statistics."""
        if name not in self._histograms:
            return None

        values = self._histograms[name].get_all()
        if not values:
            return None

        values.sort()
        count = len(values)
        return {
            "count": count,
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / count,
            "p50": values[int(count * 0.5)],
            "p90": values[int(count * 0.9)],
            "p95": values[int(count * 0.95)],
            "p99": values[int(count * 0.99)],
        }

    def get_timer_stats(self, name: str) -> Optional[Dict[str, float]]:
        """Get timer statistics."""
        if name not in self._timers:
            return None

        values = self._timers[name]
        if not values:
            return None

        sorted_values = sorted(values)
        count = len(sorted_values)
        return {
            "count": count,
            "min_ms": min(sorted_values),
            "max_ms": max(sorted_values),
            "mean_ms": sum(sorted_values) / count,
            "p50_ms": sorted_values[int(count * 0.5)],
            "p90_ms": sorted_values[int(count * 0.9)],
            "p95_ms": sorted_values[int(count * 0.95)],
            "p99_ms": sorted_values[int(count * 0.99)],
        }

    def get_recent_metrics(self, count: int = 100) -> List[MetricData]:
        """Get recent metrics."""
        return self._metrics.get_recent(count)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: self.get_histogram_stats(name) for name in self._histograms
            },
            "timers": {name: self.get_timer_stats(name) for name in self._timers},
            "total_metrics": self._metrics.size(),
        }


class HealthMonitor:
    """Monitor health of execution components."""

    def __init__(self, max_results: int = 1000):
        self._results = CircularBuffer(max_results)
        self._component_status: Dict[str, HealthStatus] = {}
        self._check_intervals: Dict[str, float] = {}
        self._check_tasks: Dict[str, asyncio.Task] = {}
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        self._shutdown_event = asyncio.Event()

    def register_component(
        self,
        component: str,
        check_interval: float = 60.0,
        initial_status: HealthStatus = HealthStatus.UNKNOWN,
    ) -> None:
        """Register a component for health monitoring."""
        self._component_status[component] = initial_status
        self._check_intervals[component] = check_interval
        logger.debug(f"Registered component for health monitoring: {component}")

    def unregister_component(self, component: str) -> None:
        """Unregister a component from health monitoring."""
        # Cancel monitoring task if exists
        if component in self._check_tasks:
            self._check_tasks[component].cancel()
            del self._check_tasks[component]

        # Remove from tracking
        self._component_status.pop(component, None)
        self._check_intervals.pop(component, None)
        self._callbacks.pop(component, None)

        logger.debug(f"Unregistered component from health monitoring: {component}")

    def add_status_callback(
        self, component: str, callback: Callable[[HealthCheckResult], None]
    ) -> None:
        """Add callback for health status changes."""
        self._callbacks[component].append(callback)

    @with_error_handling("perform_health_check", fallback_value=None)
    async def perform_health_check(
        self, component: str, checker: IHealthCheckable
    ) -> Optional[HealthCheckResult]:
        """Perform health check on a component."""
        start_time = time.time()

        try:
            health_data = await checker.health_check()
            response_time = (time.time() - start_time) * 1000

            # Determine status from health data
            if isinstance(health_data, dict):
                status_str = health_data.get("status", "unknown").lower()
                if status_str == "healthy":
                    status = HealthStatus.HEALTHY
                elif status_str == "degraded":
                    status = HealthStatus.DEGRADED
                elif status_str == "unhealthy":
                    status = HealthStatus.UNHEALTHY
                else:
                    status = HealthStatus.UNKNOWN
                details = health_data
            else:
                status = HealthStatus.HEALTHY if health_data else HealthStatus.UNHEALTHY
                details = {"raw_result": health_data}

            result = HealthCheckResult(
                status=status,
                component=component,
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time,
                details=details,
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            result = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                component=component,
                timestamp=datetime.now(timezone.utc),
                response_time_ms=response_time,
                error=str(e),
            )

        # Update component status
        old_status = self._component_status.get(component, HealthStatus.UNKNOWN)
        self._component_status[component] = result.status

        # Store result
        self._results.append(result)

        # Notify callbacks if status changed
        if old_status != result.status:
            for callback in self._callbacks.get(component, []):
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Health callback error for {component}: {e}")

        return result

    def start_monitoring(self, component: str, checker: IHealthCheckable) -> None:
        """Start continuous health monitoring for a component."""
        if component in self._check_tasks:
            logger.warning(f"Health monitoring already started for {component}")
            return

        async def monitor_loop():
            interval = self._check_intervals.get(component, 60.0)
            while not self._shutdown_event.is_set():
                try:
                    await self.perform_health_check(component, checker)
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error for {component}: {e}")
                    await asyncio.sleep(interval)

        task = asyncio.create_task(monitor_loop())
        self._check_tasks[component] = task
        logger.info(f"Started health monitoring for {component}")

    def stop_monitoring(self, component: str) -> None:
        """Stop health monitoring for a component."""
        if component in self._check_tasks:
            self._check_tasks[component].cancel()
            del self._check_tasks[component]
            try:
                logger.info(f"Stopped health monitoring for {component}")
            except RuntimeError:
                # Avoid logging deadlock during shutdown
                pass

    async def shutdown(self) -> None:
        """Shutdown health monitor."""
        logger.info("Shutting down health monitor")
        self._shutdown_event.set()

        # Cancel all monitoring tasks
        if self._check_tasks:
            for task in self._check_tasks.values():
                task.cancel()

            await asyncio.gather(*self._check_tasks.values(), return_exceptions=True)
            self._check_tasks.clear()

    def get_component_status(self, component: str) -> HealthStatus:
        """Get current status of a component."""
        return self._component_status.get(component, HealthStatus.UNKNOWN)

    def get_all_statuses(self) -> Dict[str, HealthStatus]:
        """Get all component statuses."""
        return self._component_status.copy()

    def get_recent_results(
        self, component: Optional[str] = None, count: int = 100
    ) -> List[HealthCheckResult]:
        """Get recent health check results."""
        results = self._results.get_recent(count)
        if component:
            return [r for r in results if r.component == component]
        return results

    def get_component_history(
        self, component: str, hours: int = 24
    ) -> List[HealthCheckResult]:
        """Get health history for a component."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        results = self._results.get_all()
        return [
            r for r in results if r.component == component and r.timestamp > cutoff_time
        ]


class ExecutorMonitor:
    """Comprehensive monitor for executor instances."""

    def __init__(self):
        self._performance_monitor = PerformanceMonitor()
        self._health_monitor = HealthMonitor()
        self._executor_refs: Dict[str, weakref.ReferenceType] = {}
        self._start_time = datetime.now(timezone.utc)

    def register_executor(self, platform: str, executor: IExecutor) -> None:
        """Register executor for monitoring."""
        # Store weak reference to avoid keeping executor alive
        self._executor_refs[platform] = weakref.ref(executor)

        # Register for health monitoring
        self._health_monitor.register_component(platform, check_interval=60.0)

        # Start health monitoring
        self._health_monitor.start_monitoring(platform, executor)

        logger.info(f"Registered executor for monitoring: {platform}")

    def unregister_executor(self, platform: str) -> None:
        """Unregister executor from monitoring."""
        self._health_monitor.stop_monitoring(platform)
        self._health_monitor.unregister_component(platform)
        self._executor_refs.pop(platform, None)

        try:
            logger.info(f"Unregistered executor from monitoring: {platform}")
        except RuntimeError:
            # Avoid logging deadlock during shutdown
            pass

    def record_order_placed(
        self, platform: str, response_time_ms: float, success: bool
    ) -> None:
        """Record order placement metrics."""
        self._performance_monitor.increment_counter(
            "orders_placed_total",
            labels={"platform": platform, "status": "success" if success else "failed"},
        )
        self._performance_monitor.record_timer(
            "order_placement_duration", response_time_ms, labels={"platform": platform}
        )

    def record_connection_event(self, platform: str, event_type: str) -> None:
        """Record connection events."""
        self._performance_monitor.increment_counter(
            "connection_events_total",
            labels={"platform": platform, "event": event_type},
        )

    def record_api_call(
        self, platform: str, endpoint: str, response_time_ms: float, success: bool
    ) -> None:
        """Record API call metrics."""
        self._performance_monitor.increment_counter(
            "api_calls_total",
            labels={
                "platform": platform,
                "endpoint": endpoint,
                "status": "success" if success else "failed",
            },
        )
        self._performance_monitor.record_timer(
            "api_call_duration",
            response_time_ms,
            labels={"platform": platform, "endpoint": endpoint},
        )

    def set_account_balance(
        self, platform: str, balance: float, currency: str = "USD"
    ) -> None:
        """Set current account balance."""
        self._performance_monitor.set_gauge(
            "account_balance",
            balance,
            labels={"platform": platform, "currency": currency},
        )

    def set_open_positions(self, platform: str, count: int) -> None:
        """Set number of open positions."""
        self._performance_monitor.set_gauge(
            "open_positions", count, labels={"platform": platform}
        )

    async def shutdown(self) -> None:
        """Shutdown the executor monitor."""
        await self._health_monitor.shutdown()
        logger.info("Executor monitor shutdown complete")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance monitoring summary."""
        return self._performance_monitor.get_summary()

    def get_health_summary(self) -> Dict[str, Any]:
        """Get health monitoring summary."""
        return {
            "component_statuses": self._health_monitor.get_all_statuses(),
            "recent_results": self._health_monitor.get_recent_results(count=10),
        }

    def get_overall_status(self) -> Dict[str, Any]:
        """Get overall monitoring status."""
        uptime = datetime.now(timezone.utc) - self._start_time

        # Calculate overall health
        statuses = self._health_monitor.get_all_statuses()
        healthy_count = sum(
            1 for status in statuses.values() if status == HealthStatus.HEALTHY
        )
        total_count = len(statuses)

        overall_health = (
            "healthy"
            if healthy_count == total_count and total_count > 0
            else "degraded"
        )
        if healthy_count == 0 and total_count > 0:
            overall_health = "unhealthy"

        return {
            "overall_health": overall_health,
            "uptime_seconds": int(uptime.total_seconds()),
            "monitored_executors": total_count,
            "healthy_executors": healthy_count,
            "performance_metrics": self._performance_monitor.get_summary(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Global monitor instance
_executor_monitor = ExecutorMonitor()


def get_executor_monitor() -> ExecutorMonitor:
    """Get the global executor monitor instance."""
    return _executor_monitor
