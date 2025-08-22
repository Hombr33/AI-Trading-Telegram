"""
Socket.IO Bridge for real-time communication with MT5 EA.
Provides fallback to long polling if Socket.IO fails.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timezone
import socketio
from fastapi import HTTPException
import aiohttp

from ..core.logging import get_logger
from ..core.config import BridgeConfig

logger = get_logger(__name__)


class SocketIOBridge:
    """Socket.IO bridge for real-time communication with MT5 EA."""
    
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.sio = socketio.AsyncClient()
        self.connected = False
        self.fallback_enabled = False
        self.fallback_url = "http://127.0.0.1:8000/api/v1/bridge"
        self.message_queue: List[Dict] = []
        self.callbacks: Dict[str, List[Callable]] = {}
        
        # Setup Socket.IO event handlers
        self._setup_socketio_handlers()
        
    def _setup_socketio_handlers(self):
        """Setup Socket.IO event handlers."""
        
        @self.sio.event
        async def connect():
            logger.info("Socket.IO connected to EA")
            self.connected = True
            self.fallback_enabled = False
            
            # Send authentication
            await self.sio.emit('authenticate', {
                'token': self.config.bridge_token,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Process queued messages
            await self._process_message_queue()
        
        @self.sio.event
        async def disconnect():
            logger.warning("Socket.IO disconnected from EA")
            self.connected = False
            self.fallback_enabled = True
        
        @self.sio.event
        async def order_confirmation(data):
            """Handle order confirmation from EA."""
            logger.info(f"Order confirmation received: {data}")
            await self._handle_callback('order_confirmation', data)
        
        @self.sio.event
        async def signal_ack(data):
            """Handle signal acknowledgment from EA."""
            logger.info(f"Signal acknowledgment received: {data}")
            await self._handle_callback('signal_ack', data)
        
        @self.sio.event
        async def position_update(data):
            """Handle position update from EA."""
            logger.info(f"Position update received: {data}")
            await self._handle_callback('position_update', data)
        
        @self.sio.event
        async def error(data):
            """Handle error from EA."""
            logger.error(f"Error from EA: {data}")
            await self._handle_callback('error', data)
    
    async def connect(self) -> bool:
        """Connect to the EA via Socket.IO."""
        try:
            # Connect to EA on a different port (e.g., 8001 for EA)
            await self.sio.connect(
                'http://127.0.0.1:8001',  # EA should run on different port
                auth={'token': self.config.bridge_token}
            )
            return True
        except Exception as e:
            logger.warning(f"Socket.IO connection failed: {e}, enabling fallback mode")
            self.fallback_enabled = True
            return False
    
    async def disconnect(self):
        """Disconnect from the EA."""
        if self.connected:
            await self.sio.disconnect()
            self.connected = False
    
    async def send_order(self, order_data: Dict) -> Dict:
        """Send an order to the EA."""
        try:
            if self.connected:
                # Send via Socket.IO
                await self.sio.emit('order', order_data)
                logger.info(f"Order sent via Socket.IO: {order_data.get('order_id')}")
                return {"success": True, "method": "socketio"}
            else:
                # Fallback to HTTP
                return await self._send_order_fallback(order_data)
                
        except Exception as e:
            logger.error(f"Error sending order: {e}")
            # Fallback to HTTP
            return await self._send_order_fallback(order_data)
    
    async def send_signal(self, signal_data: Dict) -> Dict:
        """Send a trading signal to the EA."""
        try:
            if self.connected:
                # Send via Socket.IO
                await self.sio.emit('signal', signal_data)
                logger.info(f"Signal sent via Socket.IO: {signal_data.get('signal_id')}")
                return {"success": True, "method": "socketio"}
            else:
                # Fallback to HTTP
                return await self._send_signal_fallback(signal_data)
                
        except Exception as e:
            logger.error(f"Error sending signal: {e}")
            # Fallback to HTTP
            return await self._send_signal_fallback(signal_data)
    
    async def send_position_update(self, position_data: Dict) -> Dict:
        """Send position update to the EA."""
        try:
            if self.connected:
                # Send via Socket.IO
                await self.sio.emit('position_update', position_data)
                return {"success": True, "method": "socketio"}
            else:
                # Fallback to HTTP
                return await self._send_position_update_fallback(position_data)
                
        except Exception as e:
            logger.error(f"Error sending position update: {e}")
            # Fallback to HTTP
            return await self._send_position_update_fallback(position_data)
    
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
            
            if self.connected:
                # Send via Socket.IO
                await self.sio.emit('risk_alert', alert_data)
                return {"success": True, "method": "socketio"}
            else:
                # Fallback to HTTP
                return await self._send_risk_alert_fallback(alert_data)
                
        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")
            # Fallback to HTTP
            return await self._send_risk_alert_fallback(alert_data)
    
    async def on_event(self, event: str, callback: Callable):
        """Register callback for specific events."""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    async def _handle_callback(self, event: str, data: Dict):
        """Handle callbacks for specific events."""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for event {event}: {e}")
    
    async def _process_message_queue(self):
        """Process queued messages after reconnection."""
        if not self.message_queue:
            return
        
        logger.info(f"Processing {len(self.message_queue)} queued messages")
        
        for message in self.message_queue:
            try:
                if message['type'] == 'order':
                    await self.send_order(message['data'])
                elif message['type'] == 'signal':
                    await self.send_signal(message['data'])
                elif message['type'] == 'position_update':
                    await self.send_position_update(message['data'])
                elif message['type'] == 'risk_alert':
                    await self.send_risk_alert(**message['data'])
            except Exception as e:
                logger.error(f"Error processing queued message: {e}")
        
        self.message_queue.clear()
    
    # Fallback HTTP methods
    async def _send_order_fallback(self, order_data: Dict) -> Dict:
        """Send order via HTTP fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.fallback_url}/order",
                    json=order_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Order sent via HTTP fallback: {order_data.get('order_id')}")
                        return {"success": True, "method": "http_fallback", "response": result}
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP fallback order send failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "method": "http_fallback"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP fallback order send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "http_fallback"
            }
    
    async def _send_signal_fallback(self, signal_data: Dict) -> Dict:
        """Send signal via HTTP fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.fallback_url}/signal",
                    json=signal_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Signal sent via HTTP fallback: {signal_data.get('signal_id')}")
                        return {"success": True, "method": "http_fallback", "response": result}
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP fallback signal send failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "method": "http_fallback"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP fallback signal send error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "http_fallback"
            }
    
    async def _send_position_update_fallback(self, update_data: Dict) -> Dict:
        """Send position update via HTTP fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.fallback_url}/position_update",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return {"success": True, "method": "http_fallback"}
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP fallback position update failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "method": "http_fallback"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP fallback position update error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "http_fallback"
            }
    
    async def _send_risk_alert_fallback(self, alert_data: Dict) -> Dict:
        """Send risk alert via HTTP fallback."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.fallback_url}/risk_alert",
                    json=alert_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return {"success": True, "method": "http_fallback"}
                    else:
                        error_text = await response.text()
                        logger.error(f"HTTP fallback risk alert failed: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {error_text}",
                            "method": "http_fallback"
                        }
                        
        except Exception as e:
            logger.error(f"HTTP fallback risk alert error: {e}")
            return {
                "success": False,
                "error": str(e),
                "method": "http_fallback"
            }
    
    def get_status(self) -> Dict:
        """Get bridge status."""
        return {
            "connected": self.connected,
            "fallback_enabled": self.fallback_enabled,
            "message_queue_size": len(self.message_queue),
            "registered_callbacks": list(self.callbacks.keys())
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
