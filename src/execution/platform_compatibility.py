"""
Cross-platform compatibility layer for the execution module.
"""

from __future__ import annotations

import sys
import platform
import importlib
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass
from enum import Enum
import logging

from ..core.logging import get_logger

logger = get_logger(__name__)


class OSType(Enum):
    """Operating system types."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"


@dataclass
class PlatformCapability:
    """Platform capability information."""
    name: str
    module_path: str
    class_name: str
    os_requirements: Set[OSType]
    python_requirements: Optional[str] = None
    dependencies: List[str] = None
    fallback_platform: Optional[str] = None
    is_production_ready: bool = True
    description: str = ""

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class PlatformCompatibilityManager:
    """Manages cross-platform compatibility for trading platforms."""
    
    def __init__(self):
        self._current_os = self._detect_os()
        self._python_version = self._get_python_version()
        self._platform_capabilities: Dict[str, PlatformCapability] = {}
        self._available_platforms: Set[str] = set()
        self._unavailable_platforms: Dict[str, str] = {}
        self._initialize_platform_capabilities()
    
    def _detect_os(self) -> OSType:
        """Detect current operating system."""
        system = platform.system().lower()
        
        if system == "windows" or sys.platform == "win32":
            return OSType.WINDOWS
        elif system == "linux":
            return OSType.LINUX
        elif system == "darwin":
            return OSType.MACOS
        else:
            return OSType.UNKNOWN
    
    def _get_python_version(self) -> str:
        """Get Python version string."""
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    def _initialize_platform_capabilities(self) -> None:
        """Initialize platform capability definitions."""
        
        # MT5 Platform (Windows only)
        self._platform_capabilities["mt5"] = PlatformCapability(
            name="MetaTrader 5",
            module_path="src.execution.platforms.forex.mt5_executor",
            class_name="MT5Executor",
            os_requirements={OSType.WINDOWS},
            dependencies=["MetaTrader5"],
            description="MetaTrader 5 trading platform (Windows only)",
            is_production_ready=True
        )
        
        # AioMQL Platform (Windows only, alternative MT5)
        self._platform_capabilities["aiomql"] = PlatformCapability(
            name="AioMQL",
            module_path="src.execution.platforms.forex.aiomql_executor",
            class_name="AioMQLExecutor",
            os_requirements={OSType.WINDOWS},
            dependencies=["aiomql"],
            fallback_platform="mt5",
            description="Async MetaTrader 5 library (Windows only)",
            is_production_ready=True
        )
        
        # Crypto exchanges using CCXT unified library
        self._platform_capabilities["binance"] = PlatformCapability(
            name="Binance",
            module_path="src.execution.platforms.crypto.ccxt_executor",
            class_name="CCXTExecutor",
            os_requirements={OSType.WINDOWS, OSType.LINUX, OSType.MACOS},
            dependencies=["ccxt"],
            description="Binance cryptocurrency exchange via CCXT",
            is_production_ready=True
        )
        
        self._platform_capabilities["bybit"] = PlatformCapability(
            name="Bybit",
            module_path="src.execution.platforms.crypto.ccxt_executor",
            class_name="CCXTExecutor",
            os_requirements={OSType.WINDOWS, OSType.LINUX, OSType.MACOS},
            dependencies=["ccxt"],
            description="Bybit cryptocurrency exchange via CCXT",
            is_production_ready=True
        )
        
        self._platform_capabilities["bitget"] = PlatformCapability(
            name="Bitget",
            module_path="src.execution.platforms.crypto.ccxt_executor",
            class_name="CCXTExecutor",
            os_requirements={OSType.WINDOWS, OSType.LINUX, OSType.MACOS},
            dependencies=["ccxt"],
            description="Bitget cryptocurrency exchange via CCXT",
            is_production_ready=True
        )
        
        # Demo Platform (Cross-platform)
        self._platform_capabilities["demo"] = PlatformCapability(
            name="Demo Trading",
            module_path="src.execution.platforms.simulation.demo_executor",
            class_name="DemoExecutor",
            os_requirements={OSType.WINDOWS, OSType.LINUX, OSType.MACOS},
            dependencies=[],
            description="Simulated trading for testing",
            is_production_ready=True
        )
        
        # Paper Trading Platform (Cross-platform)
        self._platform_capabilities["paper"] = PlatformCapability(
            name="Paper Trading",
            module_path="src.execution.platforms.simulation.paper_executor",
            class_name="PaperExecutor",
            os_requirements={OSType.WINDOWS, OSType.LINUX, OSType.MACOS},
            dependencies=[],
            description="Paper trading with live market data",
            is_production_ready=True
        )
    
    def scan_available_platforms(self) -> None:
        """Scan and determine which platforms are available."""
        logger.info(f"Scanning platforms for {self._current_os.value} OS")
        
        self._available_platforms.clear()
        self._unavailable_platforms.clear()
        
        for platform_id, capability in self._platform_capabilities.items():
            reason = self._check_platform_availability(capability)
            
            if reason is None:
                self._available_platforms.add(platform_id)
                logger.info(f"Platform '{platform_id}' is available")
            else:
                self._unavailable_platforms[platform_id] = reason
                logger.warning(f"Platform '{platform_id}' is unavailable: {reason}")
    
    def _check_platform_availability(self, capability: PlatformCapability) -> Optional[str]:
        """Check if a platform is available on current system."""
        
        # Check OS compatibility
        if self._current_os not in capability.os_requirements:
            return f"Not supported on {self._current_os.value}"
        
        # Check Python version if specified
        if capability.python_requirements:
            # Simplified version check - in production, use packaging.version
            if capability.python_requirements > self._python_version:
                return f"Requires Python {capability.python_requirements}, got {self._python_version}"
        
        # Check module availability
        try:
            module = importlib.import_module(capability.module_path)
            if not hasattr(module, capability.class_name):
                return f"Class {capability.class_name} not found in module"
        except ImportError as e:
            return f"Module import failed: {str(e)}"
        except Exception as e:
            return f"Module check failed: {str(e)}"
        
        # Check dependencies
        for dep in capability.dependencies:
            try:
                importlib.import_module(dep.replace("-", "_"))
            except ImportError:
                return f"Missing dependency: {dep}"
        
        return None
    
    def is_platform_available(self, platform_id: str) -> bool:
        """Check if a platform is available."""
        return platform_id in self._available_platforms
    
    def get_available_platforms(self) -> List[str]:
        """Get list of available platform IDs."""
        return list(self._available_platforms)
    
    def get_unavailable_platforms(self) -> Dict[str, str]:
        """Get unavailable platforms with reasons."""
        return self._unavailable_platforms.copy()
    
    def get_platform_capability(self, platform_id: str) -> Optional[PlatformCapability]:
        """Get platform capability information."""
        return self._platform_capabilities.get(platform_id)
    
    def get_fallback_platform(self, platform_id: str) -> Optional[str]:
        """Get fallback platform for unavailable platform."""
        capability = self._platform_capabilities.get(platform_id)
        if capability and capability.fallback_platform:
            if self.is_platform_available(capability.fallback_platform):
                return capability.fallback_platform
        return None
    
    def get_recommended_platforms(self) -> List[str]:
        """Get recommended platforms for current OS."""
        recommended = []
        
        # OS-specific recommendations
        if self._current_os == OSType.WINDOWS:
            preferred_order = ["mt5", "aiomql", "binance", "bybit", "bitget", "demo", "paper"]
        else:
            preferred_order = ["binance", "bybit", "bitget", "demo", "paper"]
        
        for platform in preferred_order:
            if self.is_platform_available(platform):
                recommended.append(platform)
        
        return recommended
    
    def get_cross_platform_alternatives(self, platform_id: str) -> List[str]:
        """Get cross-platform alternatives for a platform."""
        alternatives = []
        
        # If it's a Windows-only platform, suggest cross-platform crypto exchanges
        capability = self._platform_capabilities.get(platform_id)
        if capability and OSType.WINDOWS in capability.os_requirements and len(capability.os_requirements) == 1:
            for alt_id, alt_capability in self._platform_capabilities.items():
                if (alt_id != platform_id and 
                    len(alt_capability.os_requirements) > 1 and 
                    self.is_platform_available(alt_id)):
                    alternatives.append(alt_id)
        
        return alternatives
    
    def create_platform_executor(self, platform_id: str, config: Dict[str, Any]) -> Optional[Any]:
        """Create executor instance for platform."""
        if not self.is_platform_available(platform_id):
            logger.error(f"Platform '{platform_id}' is not available")
            return None
        
        capability = self._platform_capabilities[platform_id]
        
        try:
            module = importlib.import_module(capability.module_path)
            executor_class = getattr(module, capability.class_name)
            return executor_class(config)
        except Exception as e:
            logger.error(f"Failed to create executor for '{platform_id}': {e}")
            return None
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for debugging."""
        return {
            "os": self._current_os.value,
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "platform_machine": platform.machine(),
            "python_version": self._python_version,
            "python_implementation": platform.python_implementation(),
            "available_platforms": list(self._available_platforms),
            "unavailable_platforms": self._unavailable_platforms,
            "total_platforms": len(self._platform_capabilities)
        }
    
    def validate_configuration(self, platform_id: str, config: Dict[str, Any]) -> List[str]:
        """Validate configuration for a platform."""
        errors = []
        
        if not self.is_platform_available(platform_id):
            errors.append(f"Platform '{platform_id}' is not available on this system")
            return errors
        
        capability = self._platform_capabilities.get(platform_id)
        if not capability:
            errors.append(f"Unknown platform '{platform_id}'")
            return errors
        
        # Platform-specific validation would go here
        # For now, just basic checks
        required_keys = ["enabled"]
        for key in required_keys:
            if key not in config:
                errors.append(f"Missing required configuration key: {key}")
        
        return errors


# Global compatibility manager instance
_compatibility_manager = PlatformCompatibilityManager()


def get_compatibility_manager() -> PlatformCompatibilityManager:
    """Get the global compatibility manager instance."""
    return _compatibility_manager


def init_platform_compatibility() -> None:
    """Initialize platform compatibility scanning."""
    _compatibility_manager.scan_available_platforms()


def is_windows() -> bool:
    """Check if running on Windows."""
    return _compatibility_manager._current_os == OSType.WINDOWS


def is_linux() -> bool:
    """Check if running on Linux."""
    return _compatibility_manager._current_os == OSType.LINUX


def is_macos() -> bool:
    """Check if running on macOS."""
    return _compatibility_manager._current_os == OSType.MACOS


def get_safe_import(module_path: str, fallback=None):
    """Safely import a module with fallback."""
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        logger.warning(f"Failed to import {module_path}: {e}")
        return fallback


def log_platform_status() -> None:
    """Log current platform status for debugging."""
    manager = get_compatibility_manager()
    info = manager.get_system_info()
    
    logger.info("=== Platform Compatibility Status ===")
    logger.info(f"OS: {info['os']} ({info['platform_system']} {info['platform_release']})")
    logger.info(f"Python: {info['python_version']} ({info['python_implementation']})")
    logger.info(f"Available platforms ({len(info['available_platforms'])}): {', '.join(info['available_platforms'])}")
    
    if info['unavailable_platforms']:
        logger.info("Unavailable platforms:")
        for platform, reason in info['unavailable_platforms'].items():
            logger.info(f"  - {platform}: {reason}")
    
    logger.info("=" * 40)
