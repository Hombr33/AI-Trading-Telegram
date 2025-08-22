"""
Order Bridge for sending orders from Python to MT5 EA.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
import aiohttp
import websockets

from ..core.logging import get_logger
from ..core.config import BridgeConfig
from ..models.orders import Order
from ..models.signals import Signal

logger = get_logger(__name__)


class OrderBridge:
    """Bridge for sending orders from Python to MT5 EA."""
    
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.websocket_url = f"ws://127.0.0.1:8000/ws/orders"
        self.http_url = "http://127.0.0.1:8000/api/v1/orders"
        self.connected = False
        self.websocket = None
        
    async def connect(self) -> bool:
        """Connect to the order bridge."""
        try:
            # Try WebSocket first
            self.websocket = await websockets.connect(self.websocket_url)
            self.connected = True
            logger.info("Connected to order bridge via WebSocket")
            return True
            
        except Exception as e:
            logger.warning(f"WebSocket connection failed: {e}, falling back to HTTP")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the order bridge."""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        self.connected = False
        logger.info("Disconnected from order bridge")
    
    async def send_order(self, order: Order) -> Dict:
        """Send an order to the EA for execution."""
        try:
            order_data = self._prepare_order_data(order)
            
            if self.connected and self.websocket:
                # Send via WebSocket
                await self.websocket.send(json.dumps(order_data))
                logger.info(f"Order sent via WebSocket: {order.order_id}")
                return {"success": True, "method": "websocket"}
            else:
                # Fallback to HTTP
                return await self._send_order_http(order_data)
                
        except Exception as e:
            logger.error(f"Error sending order: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_signal(self, signal: Signal) -> Dict:
        """Send a trading signal to the EA for execution."""
        try:
            signal_data = self._prepare_signal_data(signal)
            
            if self.connected and self.websocket:
                # Send via WebSocket
                await self.websocket.send(json.dumps(signal_data))
                logger.info(f"Signal sent via WebSocket: {signal.id}")
                return {"success": True, "method": "websocket"}
            else:
                # Fallback to HTTP
                return await self._send_signal_http(signal_data)
                
        except Exception as e:
            logger.error(f"Error sending signal: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_position_update(self, position_data: Dict) -> Dict:
        """Send position update to the EA."""
        try:
            update_data = {
                "type": "position_update",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": position_data
            }
            
            if self.connected and self.websocket:
                await self.websocket.send(json.dumps(update_data))
                return {"success": True, "method": "websocket"}
            else:
                return await self._send_position_update_http(update_data)
                
        except Exception as e:
            logger.error(f"Error sending position update: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_risk_alert(self, alert_type: str, message: str, data: Dict = None) -> Dict:
        """Send risk alert to the EA."""
        try:
            alert_data = {
                "type": "risk_alert",
                "alert_type": alert_type,
                "message": message,
                "data": data or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if self.connected and self.websocket:
                await self.websocket.send(json.dumps(alert_data))
                return {"success": True, "method": "websocket"}
            else:
                return await self._send_risk_alert_http(alert_data)
                
        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_order_data(self, order: Order) -> Dict:
        """Prepare order data for transmission."""
        return {
            "type": "order",
            "order_id": order.order_id,
            "symbol": order.instrument.symbol if hasattr(order, 'instrument') else "UNKNOWN",
            "action": order.action,
            "order_type": order.order_type,
            "volume": order.volume,
            "price": order.price,
            "stop_loss": order.stop_loss,
            "take_profit": order.take_profit,
            "magic_number": order.magic_number,
            "comment": order.comment,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _prepare_signal_data(self, signal: Signal) -> Dict:
        """Prepare signal data for transmission."""
        return {
            "type": "signal",
            "signal_id": signal.id,
            "symbol": signal.symbol,
            "bias": signal.bias,
            "setups": signal.setups,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _send_order_http(self, order_data: Dict) -> Dict:
        """Send order via HTTP fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.http_url}/execute",
                    json=order_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Order sent via HTTP: {order_data['order_id']}")
                        return {"success": True, "method": "http", "response": result}
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP order send failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "method": "http"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP order send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "http"
            }
    
    async def _send_signal_http(self, signal_data: Dict) -> Dict:
        """Send signal via HTTP fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.http_url}/signal",
                    json=signal_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Signal sent via HTTP: {signal_data['signal_id']}")
                        return {"success": True, "method": "http", "response": result}
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP signal send failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "method": "http"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP signal send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "http"
            }
    
    async def _send_position_update_http(self, update_data: Dict) -> Dict:
        """Send position update via HTTP fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.http_url}/position_update",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return {"success": True, "method": "http"}
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP position update failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "method": "http"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP position update error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "http"
            }
    
    async def _send_risk_alert_http(self, alert_data: Dict) -> Dict:
        """Send risk alert via HTTP fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.http_url}/risk_alert",
                    json=alert_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return {"success": True, "method": "http"}
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP risk alert failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "method": "http"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP risk alert error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "http"
            }
    
    async def listen_for_responses(self, callback):
        """Listen for responses from the EA."""
        if not self.connected or not self.websocket:
            logger.warning("Cannot listen for responses: not connected")
            return
        
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await callback(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {e}")
                except Exception as e:
                    logger.error(f"Error processing response: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False
        except Exception as e:
            logger.error(f"WebSocket listening error: {e}")
            self.connected = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
