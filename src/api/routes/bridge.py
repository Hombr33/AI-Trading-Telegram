"""
Bridge API routes for MT4/MT5 communication.
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import structlog

from src.core.logging import log_trade_event, log_system_event
from src.database.session import get_db_session
from src.models import Instrument, Signal, Order, Trade, Position

logger = structlog.get_logger(__name__)
router = APIRouter()

# Global instances (will be set by main.py)
order_manager = None
telegram_bot = None


def set_global_instances(ord_mgr, tg_bot):
    """Set global instances from main.py."""
    global order_manager, telegram_bot
    order_manager = ord_mgr
    telegram_bot = tg_bot


# Request/Response Models
class HeartbeatRequest(BaseModel):
    """Heartbeat request from EA."""

    terminal_id: str = Field(..., description="Terminal identifier")
    platform: str = Field(..., description="MT4 or MT5")
    account: str = Field(..., description="Account number")
    timestamp: str = Field(..., description="ISO8601 timestamp")


class HeartbeatResponse(BaseModel):
    """Heartbeat response to EA."""

    ok: bool = Field(..., description="Success status")
    server_time: str = Field(..., description="Server timestamp")


class TickRequest(BaseModel):
    """Tick data from EA."""

    symbol: str = Field(..., description="Trading symbol")
    bid: float = Field(..., description="Bid price")
    ask: float = Field(..., description="Ask price")
    time: str = Field(..., description="ISO8601 timestamp")


class TickResponse(BaseModel):
    """Tick response to EA."""

    ok: bool = Field(..., description="Success status")


class OrderRequest(BaseModel):
    """Order request from EA."""

    request_id: str = Field(..., description="Unique request identifier")
    action: str = Field(..., description="OPEN, CLOSE, or MODIFY")
    symbol: str = Field(..., description="Trading symbol")
    type: str = Field(..., description="Order type")
    volume: float = Field(..., description="Order volume")
    price: Optional[float] = Field(None, description="Order price")
    sl: Optional[float] = Field(None, description="Stop loss")
    tp: Optional[float] = Field(None, description="Take profit")
    magic: int = Field(..., description="Magic number")
    comment: Optional[str] = Field(None, description="Order comment")


class OrderResponse(BaseModel):
    """Order response to EA."""

    ok: bool = Field(..., description="Success status")
    decision: str = Field(..., description="APPROVE or REJECT")
    reason: Optional[str] = Field(None, description="Rejection reason")
    normalized: dict = Field(..., description="Normalized order parameters")


class OrderExecutionReport(BaseModel):
    """Order execution report from EA."""

    request_id: str = Field(..., description="Original request identifier")
    ticket: str = Field(..., description="MT ticket number")
    status: str = Field(..., description="Execution status")
    fill_price: Optional[float] = Field(None, description="Fill price")
    filled_volume: Optional[float] = Field(None, description="Filled volume")
    reason: Optional[str] = Field(None, description="Status reason")
    time: str = Field(..., description="ISO8601 timestamp")


class PositionData(BaseModel):
    """Position data from EA."""

    ticket: str = Field(..., description="MT ticket number")
    symbol: str = Field(..., description="Trading symbol")
    type: str = Field(..., description="BUY or SELL")
    volume: float = Field(..., description="Position volume")
    price_open: float = Field(..., description="Open price")
    sl: Optional[float] = Field(None, description="Stop loss")
    tp: Optional[float] = Field(None, description="Take profit")
    profit: float = Field(..., description="Current profit/loss")
    swap: float = Field(..., description="Swap charges")
    commission: float = Field(..., description="Commission")
    time_open: str = Field(..., description="Open time")


class PositionSnapshotRequest(BaseModel):
    """Position snapshot from EA."""

    positions: List[PositionData] = Field(..., description="List of positions")
    timestamp: str = Field(..., description="ISO8601 timestamp")


# Bridge endpoints for HTTP fallback communication
@router.post("/order")
async def bridge_order(order_data: Dict[str, Any]):
    """Handle order via HTTP bridge."""
    try:
        if not order_manager:
            logger.warning("Order manager not initialized")
            raise HTTPException(status_code=503, detail="Order manager not initialized")

        # Validate required fields
        required_fields = ["symbol", "action", "type", "volume"]
        missing_fields = [field for field in required_fields if field not in order_data]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        result = await order_manager.execute_signal(order_data, None)
        return {"success": True, "result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing bridge order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/signal")
async def bridge_signal(signal_data: Dict[str, Any]):
    """Handle signal via HTTP bridge."""
    try:
        if not order_manager:
            logger.warning("Order manager not initialized")
            raise HTTPException(status_code=503, detail="Order manager not initialized")

        # Validate required fields
        required_fields = ["symbol", "action"]
        missing_fields = [field for field in required_fields if field not in signal_data]
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )

        result = await order_manager.execute_signal(signal_data, None)

        # Send notification via Telegram (non-blocking)
        try:
            if telegram_bot and hasattr(telegram_bot, 'notification_manager') and telegram_bot.notification_manager:
                await telegram_bot.notification_manager.send_signal_notification(
                    signal_data
                )
        except Exception as notify_error:
            logger.warning(f"Failed to send Telegram notification: {notify_error}")

        return {"success": True, "result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing bridge signal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/position_update")
async def bridge_position_update(update_data: Dict[str, Any]):
    """Handle position update via HTTP bridge."""
    try:
        # Send notification via Telegram (non-blocking)
        try:
            if telegram_bot and hasattr(telegram_bot, 'notification_manager') and telegram_bot.notification_manager:
                action = update_data.get("action", "modified")
                await telegram_bot.notification_manager.send_position_notification(
                    update_data, action
                )
        except Exception as notify_error:
            logger.warning(f"Failed to send Telegram notification: {notify_error}")

        return {"success": True}

    except Exception as e:
        logger.error(f"Error processing bridge position update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/risk_alert")
async def bridge_risk_alert(alert_data: Dict[str, Any]):
    """Handle risk alert via HTTP bridge."""
    try:
        # Send notification via Telegram (non-blocking)
        try:
            if telegram_bot and hasattr(telegram_bot, 'notification_manager') and telegram_bot.notification_manager:
                alert_type = alert_data.get("alert_type", "general")
                message = alert_data.get("message", "Risk alert received")
                data = alert_data.get("data", {})
                await telegram_bot.notification_manager.send_risk_alert(
                    alert_type, message, data
                )
        except Exception as notify_error:
            logger.warning(f"Failed to send Telegram notification: {notify_error}")

        return {"success": True}

    except Exception as e:
        logger.error(f"Error processing bridge risk alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/heartbeat")
async def bridge_heartbeat(heartbeat_data: HeartbeatRequest):
    """Handle heartbeat from EA."""
    try:
        logger.info(f"Heartbeat received from {heartbeat_data.platform} terminal {heartbeat_data.terminal_id}")
        logger.debug(f"Global instances - order_manager: {order_manager is not None}, telegram_bot: {telegram_bot is not None}")

        return HeartbeatResponse(
            ok=True,
            server_time=datetime.now(timezone.utc).isoformat()
        )

    except Exception as e:
        logger.error(f"Error processing heartbeat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/tick_data")
async def bridge_tick_data(tick_data: TickRequest):
    """Handle tick data from EA."""
    try:
        logger.debug(f"Tick data received for {tick_data.symbol}: {tick_data.bid}/{tick_data.ask}")

        # Store tick data or process as needed
        # For now, just acknowledge receipt

        return TickResponse(ok=True)

    except Exception as e:
        logger.error(f"Error processing tick data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/position_snapshot")
async def bridge_position_snapshot(snapshot_data: PositionSnapshotRequest):
    """Handle position snapshot from EA."""
    try:
        logger.info(f"Position snapshot received with {len(snapshot_data.positions)} positions")

        # Process position data - could update local database or send notifications
        try:
            if telegram_bot and hasattr(telegram_bot, 'notification_manager') and telegram_bot.notification_manager:
                for position in snapshot_data.positions:
                    await telegram_bot.notification_manager.send_position_notification(
                        position.dict(), "snapshot"
                    )
        except Exception as notify_error:
            logger.warning(f"Failed to send Telegram notifications: {notify_error}")

        return {"success": True, "positions_received": len(snapshot_data.positions)}

    except Exception as e:
        logger.error(f"Error processing position snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/order_confirmation")
async def bridge_order_confirmation(confirmation_data: Dict[str, Any]):
    """Handle order confirmation from EA."""
    try:
        logger.info(f"Order confirmation received: {confirmation_data}")

        # Send notification via Telegram (non-blocking)
        try:
            if telegram_bot and hasattr(telegram_bot, 'notification_manager') and telegram_bot.notification_manager:
                await telegram_bot.notification_manager.send_order_notification(
                    confirmation_data
                )
        except Exception as notify_error:
            logger.warning(f"Failed to send Telegram notification: {notify_error}")

        return {"success": True}

    except Exception as e:
        logger.error(f"Error processing order confirmation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/signal_ack")
async def bridge_signal_ack(ack_data: Dict[str, Any]):
    """Handle signal acknowledgment from EA."""
    try:
        logger.info(f"Signal acknowledgment received: {ack_data}")

        return {"success": True}

    except Exception as e:
        logger.error(f"Error processing signal acknowledgment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/pending_orders")
async def bridge_pending_orders():
    """Get pending orders for EA to execute."""
    try:
        # This would typically return orders queued for execution
        # For now, return empty list
        return {"orders": []}

    except Exception as e:
        logger.error(f"Error getting pending orders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/screenshot_analysis")
async def bridge_screenshot_analysis(analysis_data: Dict[str, Any]):
    """Handle screenshot analysis request from EA."""
    try:
        logger.info(f"Screenshot analysis received for {analysis_data.get('symbol', 'unknown')}")

        # Process screenshot analysis - would typically use AI analyzer
        # For now, just acknowledge receipt

        return {"success": True, "analysis": "received"}

    except Exception as e:
        logger.error(f"Error processing screenshot analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
