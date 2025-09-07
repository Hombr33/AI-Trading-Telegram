"""
Enhanced error handling framework for the AI Trading Bot.
"""

import asyncio
import functools
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, TypeVar

from .logging import get_logger, log_error_with_context

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def with_error_handling(
    operation_name: str,
    notify_telegram: bool = False,
    fallback_value: Any = None,
    max_retries: int = 0,
    retry_delay: float = 1.0,
):
    """Decorator for enhanced error handling with retries and notifications.

    Args:
        operation_name: Human-readable operation name for logging
        notify_telegram: Whether to send error to Telegram
        fallback_value: Value to return on error
        max_retries: Number of retry attempts
        retry_delay: Delay between retries in seconds
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):

            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except Exception as e:

                    # Log the error with context
                    context = {
                        "operation": operation_name,
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "args": str(args)[:200],  # Truncate long args
                        "kwargs": str(kwargs)[:200],
                    }

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {operation_name}: {e}"
                        )
                        await asyncio.sleep(
                            retry_delay * (attempt + 1)
                        )  # Exponential backoff
                        continue
                    else:
                        # Final attempt failed
                        log_error_with_context(e, context)

                        # Send to Telegram if requested
                        if notify_telegram:
                            await _send_error_to_telegram(operation_name, e, context)

                        # Return fallback value or re-raise
                        if fallback_value is not None:
                            logger.info(
                                f"Returning fallback value for {operation_name}"
                            )
                            return fallback_value
                        else:
                            raise

            return fallback_value

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "operation": operation_name,
                    "args": str(args)[:200],
                    "kwargs": str(kwargs)[:200],
                }
                log_error_with_context(e, context)

                if fallback_value is not None:
                    return fallback_value
                else:
                    raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def _send_error_to_telegram(
    operation_name: str, error: Exception, context: Dict[str, Any]
):
    """Send error notification to Telegram."""
    try:
        # Import here to avoid circular imports
        from ..main import telegram_bot

        if telegram_bot and telegram_bot.notification_manager:
            error_message = (
                f"🚨 *System Error*\n\n"
                f"Operation: `{operation_name}`\n"
                f"Error: `{str(error)[:100]}...`\n"
                f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            )

            await telegram_bot.notification_manager.send_notification(
                error_message, notification_type="error", parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Failed to send error to Telegram: {e}")


class ErrorContext:
    """Context manager for error handling with automatic logging."""

    def __init__(
        self,
        operation_name: str,
        context: Optional[Dict[str, Any]] = None,
        notify_telegram: bool = False,
        suppress_errors: bool = False,
    ):
        self.operation_name = operation_name
        self.context = context or {}
        self.notify_telegram = notify_telegram
        self.suppress_errors = suppress_errors
        self.start_time = None

    async def __aenter__(self):
        self.start_time = datetime.now(timezone.utc)
        logger.debug(f"Starting operation: {self.operation_name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now(timezone.utc) - self.start_time).total_seconds()

        if exc_type is None:
            logger.debug(
                f"Operation completed successfully: {self.operation_name} ({duration:.2f}s)"
            )
            return False

        # Error occurred
        error_context = {
            **self.context,
            "operation": self.operation_name,
            "duration_seconds": duration,
            "error_type": exc_type.__name__,
        }

        log_error_with_context(exc_val, error_context)

        if self.notify_telegram:
            await _send_error_to_telegram(self.operation_name, exc_val, error_context)

        return self.suppress_errors  # Suppress error if requested


def safe_async_task(
    coro, operation_name: str, context: Optional[Dict[str, Any]] = None
):
    """Safely create and run an async task with error handling."""

    async def wrapped_coro():
        try:
            return await coro
        except Exception as e:
            log_error_with_context(
                e,
                {
                    "operation": operation_name,
                    "context": context or {},
                    "task_type": "background_task",
                },
            )

    return asyncio.create_task(wrapped_coro())


class CircuitBreaker:
    """Circuit breaker pattern for external service calls."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if self.last_failure_time:
                time_since_failure = (
                    datetime.now(timezone.utc) - self.last_failure_time
                ).total_seconds()
                if time_since_failure >= self.recovery_timeout:
                    self.state = "HALF_OPEN"
                    return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False

    def record_success(self):
        """Record successful execution."""
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if not self.can_execute():
            raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self.record_success()
            return result
        except self.expected_exception as e:
            self.record_failure()
            raise e
