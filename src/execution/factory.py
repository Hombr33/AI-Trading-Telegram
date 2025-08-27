"""
Factory patterns and dependency injection for the execution module.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Any, Type, Union, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import weakref

from .interfaces import (
    IExecutor, IPlatformManager, PlatformType, 
    OrderRequest, OrderResponse, PositionData, AccountInfo
)
from .platform_compatibility import (
    get_compatibility_manager, PlatformCompatibilityManager,
    init_platform_compatibility, log_platform_status
)
from ..core.logging import get_logger
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import TradingBotException

logger = get_logger(__name__)


@dataclass
class ExecutorConfig:
    """Configuration for executor creation."""
    platform: str
    config: Dict[str, Any]
    auto_connect: bool = True
    health_check_interval: float = 60.0
    retry_attempts: int = 3
    timeout: float = 30.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ExecutorFactory:
    """Factory for creating executor instances with dependency injection."""
    
    def __init__(self):
        self._compatibility_manager = get_compatibility_manager()
        self._executor_cache: Dict[str, weakref.ReferenceType] = {}
        self._config_validators: Dict[str, Callable[[Dict[str, Any]], bool]] = {}
        self._middleware_stack: List[Callable] = []
        self._creation_hooks: List[Callable] = []
    
    def register_config_validator(self, platform: str, validator: Callable[[Dict[str, Any]], bool]) -> None:
        """Register configuration validator for a platform."""
        self._config_validators[platform] = validator
        logger.debug(f"Registered config validator for platform: {platform}")
    
    def register_middleware(self, middleware: Callable) -> None:
        """Register middleware for executor creation."""
        self._middleware_stack.append(middleware)
        logger.debug(f"Registered middleware: {middleware.__name__}")
    
    def register_creation_hook(self, hook: Callable) -> None:
        """Register hook to be called after executor creation."""
        self._creation_hooks.append(hook)
        logger.debug(f"Registered creation hook: {hook.__name__}")
    
    @with_error_handling("validate_config", fallback_value=False)
    def validate_config(self, platform: str, config: Dict[str, Any]) -> bool:
        """Validate configuration for platform."""
        # Platform availability check
        if not self._compatibility_manager.is_platform_available(platform):
            logger.error(f"Platform '{platform}' is not available on this system")
            return False
        
        # System-level validation
        errors = self._compatibility_manager.validate_configuration(platform, config)
        if errors:
            logger.error(f"Configuration validation failed for {platform}: {errors}")
            return False
        
        # Custom validator if registered
        if platform in self._config_validators:
            try:
                return self._config_validators[platform](config)
            except Exception as e:
                logger.error(f"Custom config validation failed for {platform}: {e}")
                return False
        
        return True
    
    @with_error_handling("create_executor", fallback_value=None)
    async def create_executor(self, executor_config: ExecutorConfig) -> Optional[IExecutor]:
        """Create executor instance with full dependency injection."""
        platform = executor_config.platform
        
        logger.info(f"Creating executor for platform: {platform}")
        
        # Validate configuration
        if not self.validate_config(platform, executor_config.config):
            return None
        
        # Check cache first
        cache_key = f"{platform}_{hash(str(executor_config.config))}"
        if cache_key in self._executor_cache:
            cached_executor = self._executor_cache[cache_key]()
            if cached_executor is not None:
                logger.debug(f"Returning cached executor for {platform}")
                return cached_executor
        
        # Create executor through compatibility manager
        executor = self._compatibility_manager.create_platform_executor(
            platform, executor_config.config
        )
        
        if executor is None:
            logger.error(f"Failed to create executor for platform: {platform}")
            return None
        
        # Apply middleware stack
        for middleware in self._middleware_stack:
            try:
                executor = await middleware(executor, executor_config)
                if executor is None:
                    logger.error(f"Middleware {middleware.__name__} returned None")
                    return None
            except Exception as e:
                logger.error(f"Middleware {middleware.__name__} failed: {e}")
                return None
        
        # Auto-connect if requested
        if executor_config.auto_connect:
            try:
                connected = await asyncio.wait_for(
                    executor.connect(),
                    timeout=executor_config.timeout
                )
                if not connected:
                    logger.warning(f"Auto-connect failed for {platform}")
            except asyncio.TimeoutError:
                logger.error(f"Connection timeout for {platform}")
                return None
            except Exception as e:
                logger.error(f"Connection failed for {platform}: {e}")
                return None
        
        # Run creation hooks
        for hook in self._creation_hooks:
            try:
                await hook(executor, executor_config)
            except Exception as e:
                logger.warning(f"Creation hook {hook.__name__} failed: {e}")
        
        # Cache executor with weak reference
        self._executor_cache[cache_key] = weakref.ref(executor)
        
        logger.info(f"Successfully created executor for platform: {platform}")
        return executor
    
    def clear_cache(self) -> None:
        """Clear executor cache."""
        self._executor_cache.clear()
        logger.debug("Executor cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        alive_refs = sum(1 for ref in self._executor_cache.values() if ref() is not None)
        return {
            "total_cached": len(self._executor_cache),
            "alive_references": alive_refs,
            "dead_references": len(self._executor_cache) - alive_refs
        }


class PlatformManager(IPlatformManager):
    """Production-grade platform manager with dependency injection."""
    
    def __init__(self, factory: Optional[ExecutorFactory] = None):
        self._factory = factory or ExecutorFactory()
        self._executors: Dict[str, IExecutor] = {}
        self._executor_configs: Dict[str, ExecutorConfig] = {}
        self._health_check_tasks: Dict[str, asyncio.Task] = {}
        self._is_initialized = False
        self._shutdown_event = asyncio.Event()
        self._compatibility_manager = get_compatibility_manager()
    
    async def initialize(self) -> bool:
        """Initialize platform manager."""
        if self._is_initialized:
            logger.warning("Platform manager already initialized")
            return True
        
        logger.info("Initializing platform manager")
        
        try:
            # Initialize platform compatibility
            init_platform_compatibility()
            log_platform_status()
            
            self._is_initialized = True
            logger.info("Platform manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize platform manager: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown platform manager and all executors."""
        if not self._is_initialized:
            return True
        
        logger.info("Shutting down platform manager")
        
        try:
            # Signal shutdown
            self._shutdown_event.set()
            
            # Cancel health check tasks
            for task in self._health_check_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to complete
            if self._health_check_tasks:
                await asyncio.gather(
                    *self._health_check_tasks.values(),
                    return_exceptions=True
                )
            
            # Disconnect all executors
            disconnect_tasks = []
            for platform, executor in self._executors.items():
                if executor.is_connected:
                    disconnect_tasks.append(self._safe_disconnect(platform, executor))
            
            if disconnect_tasks:
                await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
            # Clear state
            self._executors.clear()
            self._executor_configs.clear()
            self._health_check_tasks.clear()
            self._factory.clear_cache()
            
            self._is_initialized = False
            logger.info("Platform manager shutdown complete")
            return True
            
        except Exception as e:
            logger.error(f"Error during platform manager shutdown: {e}")
            return False
    
    async def _safe_disconnect(self, platform: str, executor: IExecutor) -> None:
        """Safely disconnect an executor."""
        try:
            await executor.disconnect()
            logger.info(f"Disconnected executor for platform: {platform}")
        except Exception as e:
            logger.error(f"Error disconnecting {platform}: {e}")
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platforms."""
        return self._compatibility_manager.get_available_platforms()
    
    def is_platform_supported(self, platform: str) -> bool:
        """Check if platform is supported on current OS."""
        return self._compatibility_manager.is_platform_available(platform)
    
    async def create_executor(self, platform: str, config: Dict[str, Any]) -> Optional[IExecutor]:
        """Create executor for specified platform."""
        if not self._is_initialized:
            logger.error("Platform manager not initialized")
            return None
        
        if platform in self._executors:
            logger.warning(f"Executor for {platform} already exists")
            return self._executors[platform]
        
        executor_config = ExecutorConfig(
            platform=platform,
            config=config,
            auto_connect=config.get("auto_connect", True),
            health_check_interval=config.get("health_check_interval", 60.0),
            retry_attempts=config.get("retry_attempts", 3),
            timeout=config.get("timeout", 30.0)
        )
        
        executor = await self._factory.create_executor(executor_config)
        if executor is None:
            return None
        
        # Store executor and config
        self._executors[platform] = executor
        self._executor_configs[platform] = executor_config
        
        # Start health monitoring
        if executor_config.health_check_interval > 0:
            self._start_health_monitoring(platform, executor_config.health_check_interval)
        
        return executor
    
    def get_executor(self, platform: str) -> Optional[IExecutor]:
        """Get existing executor instance."""
        return self._executors.get(platform)
    
    async def remove_executor(self, platform: str) -> bool:
        """Remove executor instance."""
        if platform not in self._executors:
            logger.warning(f"Executor for {platform} does not exist")
            return False
        
        try:
            # Cancel health monitoring
            if platform in self._health_check_tasks:
                self._health_check_tasks[platform].cancel()
                del self._health_check_tasks[platform]
            
            # Disconnect executor
            executor = self._executors[platform]
            if executor.is_connected:
                await executor.disconnect()
            
            # Remove from registry
            del self._executors[platform]
            del self._executor_configs[platform]
            
            logger.info(f"Removed executor for platform: {platform}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing executor for {platform}: {e}")
            return False
    
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all executors."""
        results = {}
        
        health_tasks = []
        platforms = []
        
        for platform, executor in self._executors.items():
            health_tasks.append(executor.health_check())
            platforms.append(platform)
        
        if health_tasks:
            health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
            
            for platform, result in zip(platforms, health_results):
                if isinstance(result, Exception):
                    results[platform] = {
                        "status": "error",
                        "error": str(result),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                else:
                    results[platform] = result
        
        return results
    
    def _start_health_monitoring(self, platform: str, interval: float) -> None:
        """Start health monitoring task for platform."""
        async def health_monitor():
            while not self._shutdown_event.is_set():
                try:
                    await asyncio.sleep(interval)
                    if platform in self._executors:
                        executor = self._executors[platform]
                        health_result = await executor.health_check()
                        
                        # Log health status
                        if isinstance(health_result, dict):
                            status = health_result.get("status", "unknown")
                            if status != "healthy":
                                logger.warning(f"Health check warning for {platform}: {health_result}")
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error for {platform}: {e}")
        
        task = asyncio.create_task(health_monitor())
        self._health_check_tasks[platform] = task
        logger.debug(f"Started health monitoring for {platform} (interval: {interval}s)")
    
    def get_status(self) -> Dict[str, Any]:
        """Get platform manager status."""
        return {
            "initialized": self._is_initialized,
            "active_executors": list(self._executors.keys()),
            "available_platforms": self.get_available_platforms(),
            "health_monitoring": list(self._health_check_tasks.keys()),
            "cache_stats": self._factory.get_cache_stats(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global factory and manager instances
_executor_factory = ExecutorFactory()
_platform_manager = PlatformManager(_executor_factory)


def get_executor_factory() -> ExecutorFactory:
    """Get the global executor factory instance."""
    return _executor_factory


def get_platform_manager() -> PlatformManager:
    """Get the global platform manager instance."""
    return _platform_manager


# Convenience functions
async def create_executor(platform: str, config: Dict[str, Any]) -> Optional[IExecutor]:
    """Convenience function to create executor."""
    manager = get_platform_manager()
    if not manager._is_initialized:
        await manager.initialize()
    return await manager.create_executor(platform, config)


async def initialize_execution_system() -> bool:
    """Initialize the entire execution system."""
    manager = get_platform_manager()
    return await manager.initialize()


async def shutdown_execution_system() -> bool:
    """Shutdown the entire execution system."""
    manager = get_platform_manager()
    return await manager.shutdown()
