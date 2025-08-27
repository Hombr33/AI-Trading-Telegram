#!/usr/bin/env python3
"""
Test script for bridge endpoints to debug 500 errors.
"""

import asyncio
import httpx
import json
from datetime import datetime, timezone

async def test_bridge_endpoints():
    """Test bridge endpoints."""
    base_url = "http://localhost:8000/api/v1/bridge"

    # Test data
    heartbeat_data = {
        "terminal_id": "test_terminal",
        "platform": "MT5",
        "account": "123456",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    signal_data = {
        "symbol": "EURUSD",
        "action": "BUY",
        "entry_price": 1.0950,
        "stop_loss": 1.0900,
        "take_profit": 1.1000,
        "volume": 0.01
    }

    async with httpx.AsyncClient() as client:
        print("Testing bridge endpoints...")

        # Test heartbeat
        print("\n1. Testing heartbeat endpoint...")
        try:
            response = await client.post(
                f"{base_url}/heartbeat",
                json=heartbeat_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test signal
        print("\n2. Testing signal endpoint...")
        try:
            response = await client.post(
                f"{base_url}/signal",
                json=signal_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

        # Test pending orders
        print("\n3. Testing pending orders endpoint...")
        try:
            response = await client.get(
                f"{base_url}/pending_orders",
                headers={"Content-Type": "application/json"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bridge_endpoints())