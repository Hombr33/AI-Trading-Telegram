"""
Trading API routes for order execution and position management.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ...common.interfaces import IOrderManager, IPositionManager
from ...core.logging import get_logger

# Import interface only, implementation will be injected

logger = get_logger(__name__)

router = APIRouter()

# Global instances (will be set by main.py)
order_manager: IOrderManager = None
position_manager: IPositionManager = None
telegram_bot = None  # Will be set by main.py


def get_order_manager() -> IOrderManager:
    """Get order manager instance."""
    if not order_manager:
        raise HTTPException(status_code=503, detail="Order manager not initialized")
    return order_manager


def get_position_manager() -> IPositionManager:
    """Get position manager instance."""
    if not position_manager:
        raise HTTPException(status_code=503, detail="Position manager not initialized")
    return position_manager


@router.get("/positions")
async def get_positions(pos_manager: IPositionManager = Depends(get_position_manager)):
    """Get current positions."""
    try:
        positions = await pos_manager.get_positions()
        return {"success": True, "positions": positions}

    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_orders(ord_manager: IOrderManager = Depends(get_order_manager)):
    """Get pending orders."""
    try:
        orders = await ord_manager.get_open_orders()
        return {"success": True, "orders": orders}

    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_signal(
    signal_data: Dict[str, Any], ord_manager: IOrderManager = Depends(get_order_manager)
):
    """Execute a trading signal."""
    try:
        result = await ord_manager.execute_signal(signal_data, None)

        # Send notification via Telegram if available
        if telegram_bot and telegram_bot.notification_manager:
            try:
                await telegram_bot.notification_manager.send_signal_notification(
                    signal_data
                )
                logger.info("Telegram notification sent for signal execution")
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {e}")

        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error executing signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))
