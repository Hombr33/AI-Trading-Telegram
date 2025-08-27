#!/usr/bin/env python3
"""Test MT5 installation scanning."""

import asyncio
from src.execution.platforms.forex.mt5_executor import MT5Executor
from src.core.config import MT5Config

async def test_mt5_scan():
    """Test MT5 installation scanning."""
    config = MT5Config(
        login="123456",
        password="password", 
        server="broker-server",
        path=""
    )
    
    executor = MT5Executor(config)
    installations = executor._find_mt5_installations()
    
    print(f"Found {len(installations)} MT5 installations:")
    for path in installations:
        print(f"  - {path}")
    
    if installations:
        print("\n✅ MT5 path scanning working!")
    else:
        print("\n⚠️ No installations found (expected on macOS)")

if __name__ == "__main__":
    asyncio.run(test_mt5_scan())
