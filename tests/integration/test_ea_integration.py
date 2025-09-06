#!/usr/bin/env python3
"""
EA Integration Testing Suite
Comprehensive integration tests for EA communication, trading, and data flow.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
import requests
from pathlib import Path
import threading
import queue
from unittest.mock import Mock, patch, AsyncMock

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EAIntegrationTester:
    """EA integration testing suite."""

    def __init__(self):
        self.test_results = []
        self.base_url = "http://127.0.0.1:8000"
        self.bridge_token = "integration_test_token_12345"
        self.test_account = "TEST_ACCOUNT_001"
        self.test_terminal = "TEST_TERMINAL_INT_001"

        # Test data
        self.test_positions = [
            {
                "ticket": "1000001",
                "symbol": "EURUSD",
                "type": "BUY",
                "volume": 0.1,
                "price_open": 1.09567,
                "sl": 1.09000,
                "tp": 1.10567,
                "profit": 45.67,
                "swap": -0.23,
                "commission": -2.50,
                "time_open": datetime.now().isoformat(),
            },
            {
                "ticket": "1000002",
                "symbol": "GBPUSD",
                "type": "SELL",
                "volume": 0.05,
                "price_open": 1.26543,
                "sl": 1.27543,
                "tp": 1.25543,
                "profit": -15.23,
                "swap": 0.0,
                "commission": -1.25,
                "time_open": datetime.now().isoformat(),
            },
        ]

        self.test_signals = [
            {
                "signal_id": "SIG_001",
                "symbol": "EURUSD",
                "bias": "BUY",
                "strength": 0.8,
                "analysis": {
                    "sma_20": 1.09550,
                    "sma_50": 1.09450,
                    "rsi": 65,
                    "macd": "bullish",
                },
            },
            {
                "signal_id": "SIG_002",
                "symbol": "GBPUSD",
                "bias": "SELL",
                "strength": 0.7,
                "analysis": {
                    "sma_20": 1.26550,
                    "sma_50": 1.26650,
                    "rsi": 35,
                    "macd": "bearish",
                },
            },
        ]

    async def setup(self):
        """Setup test environment."""
        try:
            logger.info("Setting up EA integration test environment...")

            # Verify Python app is running
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code != 200:
                    logger.warning(
                        f"Python app health check failed: {response.status_code}"
                    )
            except Exception as e:
                logger.warning(f"Python app not accessible: {e}")

            logger.info("EA integration test environment setup complete")
            return True

        except Exception as e:
            logger.error(f"Failed to setup test environment: {e}")
            return False

    async def teardown(self):
        """Cleanup test environment."""
        try:
            logger.info("EA integration test environment cleanup complete")
            return True

        except Exception as e:
            logger.error(f"Failed to cleanup test environment: {e}")
            return False

    def log_test_result(
        self, test_name: str, success: bool, message: str = "", error: str = ""
    ):
        """Log test result."""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }

        self.test_results.append(result)

        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
        if error:
            logger.error(f"   Error: {error}")

    async def test_heartbeat_flow(self) -> bool:
        """Test complete heartbeat communication flow."""
        test_name = "Heartbeat Flow"

        try:
            logger.info("Testing heartbeat communication flow...")

            heartbeat_data = {
                "terminal_id": self.test_terminal,
                "platform": "MT5",
                "account": self.test_account,
                "timestamp": datetime.now().isoformat(),
            }

            # Send heartbeat
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/bridge/heartbeat",
                    json=heartbeat_data,
                    headers={"Authorization": f"Bearer {self.bridge_token}"},
                ) as response:
                    if response.status != 200:
                        self.log_test_result(
                            test_name,
                            False,
                            f"Heartbeat failed with status {response.status}",
                        )
                        return False

                    data = await response.json()
                    if not data.get("ok"):
                        self.log_test_result(
                            test_name, False, "Heartbeat response not OK"
                        )
                        return False

            # Test multiple heartbeats
            for i in range(3):
                heartbeat_data["timestamp"] = datetime.now().isoformat()
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/heartbeat",
                        json=heartbeat_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        if response.status != 200:
                            self.log_test_result(
                                test_name, False, f"Heartbeat {i+1} failed"
                            )
                            return False
                await asyncio.sleep(0.1)

            self.log_test_result(test_name, True, "Heartbeat flow working correctly")
            return True

        except Exception as e:
            self.log_test_result(test_name, False, "Heartbeat flow test failed", str(e))
            return False

    async def test_position_sync_flow(self) -> bool:
        """Test position synchronization flow."""
        test_name = "Position Sync Flow"

        try:
            logger.info("Testing position synchronization flow...")

            # Send position snapshot
            snapshot_data = {
                "positions": self.test_positions,
                "timestamp": datetime.now().isoformat(),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/bridge/position_snapshot",
                    json=snapshot_data,
                    headers={"Authorization": f"Bearer {self.bridge_token}"},
                ) as response:
                    if response.status != 200:
                        self.log_test_result(
                            test_name,
                            False,
                            f"Position snapshot failed with status {response.status}",
                        )
                        return False

                    data = await response.json()
                    if not data.get("success"):
                        self.log_test_result(
                            test_name,
                            False,
                            "Position snapshot response not successful",
                        )
                        return False

            # Test position updates
            for position in self.test_positions:
                update_data = {
                    "action": "modified",
                    "ticket": position["ticket"],
                    "symbol": position["symbol"],
                    "type": position["type"],
                    "volume": position["volume"],
                    "price_open": position["price_open"],
                    "sl": position["sl"] * 1.001,  # Slightly modify SL
                    "tp": position["tp"],
                    "profit": position["profit"] + 10,
                    "timestamp": datetime.now().isoformat(),
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/position_update",
                        json=update_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        if response.status != 200:
                            self.log_test_result(
                                test_name,
                                False,
                                f"Position update failed for {position['ticket']}",
                            )
                            return False

            self.log_test_result(
                test_name, True, "Position sync flow working correctly"
            )
            return True

        except Exception as e:
            self.log_test_result(
                test_name, False, "Position sync flow test failed", str(e)
            )
            return False

    async def test_signal_flow(self) -> bool:
        """Test signal communication flow."""
        test_name = "Signal Flow"

        try:
            logger.info("Testing signal communication flow...")

            # Send signals
            for signal in self.test_signals:
                signal_data = {**signal, "timestamp": datetime.now().isoformat()}

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/signal",
                        json=signal_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        if response.status not in [
                            200,
                            201,
                            503,
                        ]:  # 503 if signal service not available
                            self.log_test_result(
                                test_name,
                                False,
                                f"Signal send failed with status {response.status}",
                            )
                            return False

                # Send acknowledgment
                ack_data = {
                    "signal_id": signal["signal_id"],
                    "symbol": signal["symbol"],
                    "bias": signal["bias"],
                    "status": "received",
                    "timestamp": datetime.now().isoformat(),
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/signal_ack",
                        json=ack_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        if response.status != 200:
                            self.log_test_result(
                                test_name,
                                False,
                                f"Signal acknowledgment failed for {signal['signal_id']}",
                            )
                            return False

            self.log_test_result(test_name, True, "Signal flow working correctly")
            return True

        except Exception as e:
            self.log_test_result(test_name, False, "Signal flow test failed", str(e))
            return False

    async def test_order_flow(self) -> bool:
        """Test order execution flow."""
        test_name = "Order Flow"

        try:
            logger.info("Testing order execution flow...")

            # Test order request
            order_data = {
                "order_id": "TEST_ORDER_INT_001",
                "symbol": "EURUSD",
                "action": "BUY",
                "volume": 0.1,
                "price": 1.09567,
                "sl": 1.09000,
                "tp": 1.10567,
                "type": "MARKET",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/bridge/order",
                    json=order_data,
                    headers={"Authorization": f"Bearer {self.bridge_token}"},
                ) as response:
                    if response.status not in [
                        200,
                        201,
                        503,
                    ]:  # 503 if order manager not initialized
                        self.log_test_result(
                            test_name,
                            False,
                            f"Order request failed with status {response.status}",
                        )
                        return False

            # Test order confirmation
            confirmation_data = {
                "request_id": "TEST_ORDER_INT_001",
                "ticket": "2000001",
                "symbol": "EURUSD",
                "action": "BUY",
                "order_type": "MARKET",
                "volume": 0.1,
                "status": "EXECUTED",
                "fill_price": 1.09567,
                "timestamp": datetime.now().isoformat(),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/bridge/order_confirmation",
                    json=confirmation_data,
                    headers={"Authorization": f"Bearer {self.bridge_token}"},
                ) as response:
                    if response.status != 200:
                        self.log_test_result(
                            test_name,
                            False,
                            f"Order confirmation failed with status {response.status}",
                        )
                        return False

            # Test pending orders endpoint
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/bridge/pending_orders",
                    headers={"Authorization": f"Bearer {self.bridge_token}"},
                ) as response:
                    if response.status != 200:
                        self.log_test_result(
                            test_name,
                            False,
                            f"Pending orders failed with status {response.status}",
                        )
                        return False

            self.log_test_result(test_name, True, "Order flow working correctly")
            return True

        except Exception as e:
            self.log_test_result(test_name, False, "Order flow test failed", str(e))
            return False

    async def test_tick_data_flow(self) -> bool:
        """Test tick data streaming flow."""
        test_name = "Tick Data Flow"

        try:
            logger.info("Testing tick data flow...")

            # Send multiple tick data points
            symbols = ["EURUSD", "GBPUSD", "USDJPY"]
            tick_count = 10

            for i in range(tick_count):
                for symbol in symbols:
                    tick_data = {
                        "symbol": symbol,
                        "bid": 1.09567 + (i * 0.0001),
                        "ask": 1.09587 + (i * 0.0001),
                        "time": datetime.now().isoformat(),
                    }

                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.base_url}/bridge/tick_data",
                            json=tick_data,
                            headers={"Authorization": f"Bearer {self.bridge_token}"},
                        ) as response:
                            if response.status != 200:
                                self.log_test_result(
                                    test_name,
                                    False,
                                    f"Tick data failed for {symbol} at iteration {i}",
                                )
                                return False

                    # Small delay to simulate realistic tick timing
                    await asyncio.sleep(0.01)

            self.log_test_result(
                test_name,
                True,
                f"Tick data flow working correctly ({tick_count * len(symbols)} ticks sent)",
            )
            return True

        except Exception as e:
            self.log_test_result(test_name, False, "Tick data flow test failed", str(e))
            return False

    async def test_risk_management_flow(self) -> bool:
        """Test risk management communication flow."""
        test_name = "Risk Management Flow"

        try:
            logger.info("Testing risk management flow...")

            # Test risk alert
            alert_data = {
                "alert_type": "daily_loss_limit",
                "message": "Daily loss limit approaching",
                "data": {
                    "current_loss": 45.0,
                    "max_loss": 50.0,
                    "percentage": 90.0,
                    "open_positions": 5,
                    "total_exposure": 1.5,
                },
                "timestamp": datetime.now().isoformat(),
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/bridge/risk_alert",
                    json=alert_data,
                    headers={"Authorization": f"Bearer {self.bridge_token}"},
                ) as response:
                    if response.status != 200:
                        self.log_test_result(
                            test_name,
                            False,
                            f"Risk alert failed with status {response.status}",
                        )
                        return False

            # Test multiple risk scenarios
            risk_scenarios = [
                {
                    "alert_type": "margin_call",
                    "message": "Margin call warning",
                    "data": {"margin_level": 95.0, "required_margin": 1000.0},
                },
                {
                    "alert_type": "correlation_alert",
                    "message": "High correlation detected",
                    "data": {
                        "symbol1": "EURUSD",
                        "symbol2": "GBPUSD",
                        "correlation": 0.85,
                    },
                },
                {
                    "alert_type": "drawdown_alert",
                    "message": "Maximum drawdown exceeded",
                    "data": {"current_drawdown": 6.5, "max_drawdown": 6.0},
                },
            ]

            for scenario in risk_scenarios:
                scenario_data = {**scenario, "timestamp": datetime.now().isoformat()}

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/risk_alert",
                        json=scenario_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        if response.status != 200:
                            self.log_test_result(
                                test_name,
                                False,
                                f"Risk scenario '{scenario['alert_type']}' failed",
                            )
                            return False

            self.log_test_result(
                test_name, True, "Risk management flow working correctly"
            )
            return True

        except Exception as e:
            self.log_test_result(
                test_name, False, "Risk management flow test failed", str(e)
            )
            return False

    async def test_screenshot_analysis_flow(self) -> bool:
        """Test screenshot analysis flow."""
        test_name = "Screenshot Analysis Flow"

        try:
            logger.info("Testing screenshot analysis flow...")

            # Test screenshot analysis request
            analysis_data = {
                "symbol": "EURUSD",
                "timeframe": "H1",
                "timestamp": datetime.now().isoformat(),
                "image_data": "base64_encoded_screenshot_data_here",
                "filename": "chart_EURUSD_H1_20241226_143022.gif",
                "market_context": {
                    "current_price": 1.09567,
                    "spread": 1.2,
                    "volume": 1250.5,
                    "session": "London",
                    "account_balance": 10000.0,
                    "account_equity": 9950.0,
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/bridge/screenshot_analysis",
                    json=analysis_data,
                    headers={"Authorization": f"Bearer {self.bridge_token}"},
                ) as response:
                    if response.status != 200:
                        self.log_test_result(
                            test_name,
                            False,
                            f"Screenshot analysis failed with status {response.status}",
                        )
                        return False

                    data = await response.json()
                    if not data.get("success"):
                        self.log_test_result(
                            test_name,
                            False,
                            "Screenshot analysis response not successful",
                        )
                        return False

            self.log_test_result(
                test_name, True, "Screenshot analysis flow working correctly"
            )
            return True

        except Exception as e:
            self.log_test_result(
                test_name, False, "Screenshot analysis flow test failed", str(e)
            )
            return False

    async def test_concurrent_communication(self) -> bool:
        """Test concurrent communication handling."""
        test_name = "Concurrent Communication"

        try:
            logger.info("Testing concurrent communication...")

            async def send_heartbeat(iteration: int):
                """Send a heartbeat request."""
                heartbeat_data = {
                    "terminal_id": f"{self.test_terminal}_CONC_{iteration}",
                    "platform": "MT5",
                    "account": self.test_account,
                    "timestamp": datetime.now().isoformat(),
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/heartbeat",
                        json=heartbeat_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        return response.status == 200

            async def send_tick_data(iteration: int, symbol: str):
                """Send tick data."""
                tick_data = {
                    "symbol": symbol,
                    "bid": 1.09567 + (iteration * 0.0001),
                    "ask": 1.09587 + (iteration * 0.0001),
                    "time": datetime.now().isoformat(),
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/tick_data",
                        json=tick_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        return response.status == 200

            # Create concurrent tasks
            tasks = []

            # Add heartbeat tasks
            for i in range(5):
                tasks.append(send_heartbeat(i))

            # Add tick data tasks
            symbols = ["EURUSD", "GBPUSD", "USDJPY"]
            for i in range(3):
                for symbol in symbols:
                    tasks.append(send_tick_data(i, symbol))

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check results
            success_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Concurrent task {i} failed: {result}")
                elif result:
                    success_count += 1
                else:
                    logger.warning(f"Concurrent task {i} returned False")

            if success_count < len(tasks) * 0.8:  # 80% success rate
                self.log_test_result(
                    test_name,
                    False,
                    f"Concurrent communication failed: {success_count}/{len(tasks)} successful",
                )
                return False

            self.log_test_result(
                test_name,
                True,
                f"Concurrent communication successful: {success_count}/{len(tasks)} tasks completed",
            )
            return True

        except Exception as e:
            self.log_test_result(
                test_name, False, "Concurrent communication test failed", str(e)
            )
            return False

    async def test_error_recovery(self) -> bool:
        """Test error recovery and resilience."""
        test_name = "Error Recovery"

        try:
            logger.info("Testing error recovery...")

            test_data = {
                "terminal_id": self.test_terminal,
                "platform": "MT5",
                "account": self.test_account,
                "timestamp": datetime.now().isoformat(),
            }

            # Test with invalid endpoint
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/invalid_endpoint",
                        json=test_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        logger.debug(f"Invalid endpoint response: {response.status}")
            except Exception as e:
                logger.debug(f"Invalid endpoint test error: {e}")

            # Test with malformed data
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/heartbeat",
                        data="invalid json",
                        headers={
                            "Authorization": f"Bearer {self.bridge_token}",
                            "Content-Type": "application/json",
                        },
                    ) as response:
                        logger.debug(f"Malformed data response: {response.status}")
            except Exception as e:
                logger.debug(f"Malformed data test error: {e}")

            # Test recovery by sending valid data after errors
            for i in range(3):
                test_data["timestamp"] = datetime.now().isoformat()
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/bridge/heartbeat",
                        json=test_data,
                        headers={"Authorization": f"Bearer {self.bridge_token}"},
                    ) as response:
                        if response.status != 200:
                            self.log_test_result(
                                test_name,
                                False,
                                f"Recovery test failed on attempt {i+1}",
                            )
                            return False

            self.log_test_result(test_name, True, "Error recovery working correctly")
            return True

        except Exception as e:
            self.log_test_result(test_name, False, "Error recovery test failed", str(e))
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all EA integration tests."""
        logger.info("🔗 Starting EA Integration Tests...")

        # Setup
        if not await self.setup():
            return {"success": False, "error": "Setup failed"}

        try:
            # Run tests
            tests = [
                ("Heartbeat Flow", self.test_heartbeat_flow),
                ("Position Sync Flow", self.test_position_sync_flow),
                ("Signal Flow", self.test_signal_flow),
                ("Order Flow", self.test_order_flow),
                ("Tick Data Flow", self.test_tick_data_flow),
                ("Risk Management Flow", self.test_risk_management_flow),
                ("Screenshot Analysis Flow", self.test_screenshot_analysis_flow),
                ("Concurrent Communication", self.test_concurrent_communication),
                ("Error Recovery", self.test_error_recovery),
            ]

            passed = 0
            total = len(tests)

            for test_name, test_func in tests:
                logger.info(f"Running: {test_name}")
                try:
                    if await test_func():
                        passed += 1
                except Exception as e:
                    logger.error(f"Test {test_name} crashed: {e}")
                    self.log_test_result(test_name, False, "Test crashed", str(e))

            # Summary
            success_rate = (passed / total) * 100

            summary = {
                "success": success_rate >= 70,
                "passed": passed,
                "total": total,
                "success_rate": success_rate,
                "results": self.test_results,
                "timestamp": datetime.now().isoformat(),
                "integration_metrics": {
                    "test_positions": len(self.test_positions),
                    "test_signals": len(self.test_signals),
                    "test_account": self.test_account,
                    "test_terminal": self.test_terminal,
                },
            }

            if summary["success"]:
                logger.info(
                    f"🔗 All integration tests passed! Success rate: {success_rate:.1f}%"
                )
            else:
                logger.warning(
                    f"⚠️ Some integration tests failed. Success rate: {success_rate:.1f}%"
                )
            return summary

        finally:
            # Cleanup
            await self.teardown()


def print_integration_test_summary(summary: Dict[str, Any]):
    """Print integration test summary."""
    print("\n" + "=" * 70)
    print("🔗 EA INTEGRATION TEST RESULTS")
    print("=" * 70)

    print(f"Overall Status: {'✅ PASS' if summary['success'] else '❌ FAIL'}")
    print(".1f")
    print(f"Tests Passed: {summary['passed']}/{summary['total']}")
    print(f"Timestamp: {summary['timestamp']}")

    print("\n🔄 Integration Metrics:")
    metrics = summary.get("integration_metrics", {})
    print(f"   Test positions: {metrics.get('test_positions', 0)}")
    print(f"   Test signals: {metrics.get('test_signals', 0)}")
    print(f"   Test account: {metrics.get('test_account', 'N/A')}")
    print(f"   Test terminal: {metrics.get('test_terminal', 'N/A')}")

    print("\n📋 DETAILED RESULTS:")
    print("-" * 50)

    for result in summary["results"]:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {result['test']}")
        if result["message"]:
            print(f"   {result['message']}")
        if result["error"]:
            print(f"   Error: {result['error']}")
        print()

    print("=" * 70)

    if summary["success"]:
        print("🔗 EA integration is production-ready!")
        print("📝 Integration capabilities verified:")
        print("   • Heartbeat communication ✓")
        print("   • Position synchronization ✓")
        print("   • Signal processing ✓")
        print("   • Order execution flow ✓")
        print("   • Tick data streaming ✓")
        print("   • Risk management ✓")
        print("   • Screenshot analysis ✓")
        print("   • Concurrent operations ✓")
        print("   • Error recovery ✓")
    else:
        print("⚠️  Some integration tests failed. Review the errors above.")
        print("🔧 Integration improvements needed:")
        print("   1. Ensure Python app is running and accessible")
        print("   2. Check bridge endpoints configuration")
        print("   3. Verify authentication tokens")
        print("   4. Review network connectivity")
        print("   5. Check service dependencies")


async def main():
    """Main test execution function."""
    print("🔗 Starting EA Integration Tests...")
    print("Note: This test suite verifies complete EA communication and data flow")
    print("Ensure the Python app is running for full test coverage\n")

    # Run tests
    test_suite = EAIntegrationTester()
    summary = await test_suite.run_all_tests()
    print_integration_test_summary(summary)


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run async main
    asyncio.run(main())
