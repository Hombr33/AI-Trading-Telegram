"""
EA API routes for MT5 Expert Advisor communication.
Provides endpoints for EA to communicate with the trading system.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from src.core.logging import log_system_event, log_trade_event
from src.database.session import get_db_session
from src.execution.order_manager import OrderManager
from src.models import Instrument, Order, Position, Signal, Trade
from src.services.config_manager import ConfigManager
from src.services.user_manager import UserManager
from src.telegram_bot.core.trading_bot import TradingBot

logger = structlog.get_logger(__name__)
router = APIRouter()

# Global instances (will be set by main.py)
user_manager: Optional[UserManager] = None
config_manager: Optional[ConfigManager] = None
order_manager: Optional[OrderManager] = None
telegram_bot: Optional[TradingBot] = None


def set_ea_globals(
    usr_mgr: UserManager,
    cfg_mgr: ConfigManager,
    ord_mgr: OrderManager,
    tg_bot: TradingBot,
):
    """Set global instances for EA routes."""
    global user_manager, config_manager, order_manager, telegram_bot
    user_manager = usr_mgr
    config_manager = cfg_mgr
    order_manager = ord_mgr
    telegram_bot = tg_bot


# Request/Response Models
class EAAuthRequest(BaseModel):
    """EA authentication request."""

    api_key: str = Field(..., description="EA API key for authentication")


class EAAuthResponse(BaseModel):
    """EA authentication response."""

    valid: bool = Field(..., description="Whether the API key is valid")
    user_id: Optional[int] = Field(None, description="User ID if valid")
    message: str = Field(..., description="Response message")


class EAOrderRequest(BaseModel):
    """EA order request."""

    api_key: str = Field(..., description="EA API key")
    order: Dict[str, Any] = Field(..., description="Order data")


class EAOrderResponse(BaseModel):
    """EA order response."""

    success: bool = Field(..., description="Whether the order was successful")
    ticket: Optional[str] = Field(None, description="Order ticket if successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class EAPositionsRequest(BaseModel):
    """EA positions request."""

    api_key: str = Field(..., description="EA API key")


class EAPositionsResponse(BaseModel):
    """EA positions response."""

    positions: List[Dict[str, Any]] = Field(..., description="List of positions")


class EAAccountRequest(BaseModel):
    """EA account request."""

    api_key: str = Field(..., description="EA API key")


class EAAccountResponse(BaseModel):
    """EA account response."""

    account: Dict[str, Any] = Field(..., description="Account information")


class EAModifyRequest(BaseModel):
    """EA position modify request."""

    api_key: str = Field(..., description="EA API key")
    ticket: int = Field(..., description="Position ticket")
    new_sl: Optional[float] = Field(None, description="New stop loss")
    new_tp: Optional[float] = Field(None, description="New take profit")


class EAModifyResponse(BaseModel):
    """EA position modify response."""

    success: bool = Field(..., description="Whether the modification was successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class EACloseRequest(BaseModel):
    """EA position close request."""

    api_key: str = Field(..., description="EA API key")
    ticket: int = Field(..., description="Position ticket")
    volume: Optional[float] = Field(
        None, description="Volume to close (None for full close)"
    )


class EACloseResponse(BaseModel):
    """EA position close response."""

    success: bool = Field(..., description="Whether the close was successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class EAHistoryRequest(BaseModel):
    """EA trade history request."""

    api_key: str = Field(..., description="EA API key")
    days: int = Field(7, description="Number of days of history")


class EAHistoryResponse(BaseModel):
    """EA trade history response."""

    trades: List[Dict[str, Any]] = Field(..., description="List of trades")


class EASettingsRequest(BaseModel):
    """EA settings update request."""

    api_key: str = Field(..., description="EA API key")
    settings: Dict[str, Any] = Field(..., description="Settings to update")


class EASettingsResponse(BaseModel):
    """EA settings update response."""

    success: bool = Field(..., description="Whether the update was successful")
    error: Optional[str] = Field(None, description="Error message if failed")


class EAHealthResponse(BaseModel):
    """EA health check response."""

    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="API version")


async def authenticate_ea_request(api_key: str) -> Optional[int]:
    """Authenticate EA request and return user ID if valid."""
    try:
        if not user_manager:
            logger.error("User manager not initialized")
            return None

        # Validate API key and get user
        user = await user_manager.get_user_by_api_key(api_key)
        if not user:
            logger.warning(f"Invalid API key provided: {api_key[:8]}...")
            return None

        return user.id

    except Exception as e:
        logger.error(f"Error authenticating EA request: {e}")
        return None


@router.post("/validate", response_model=EAAuthResponse)
async def validate_ea_api_key(request: EAAuthRequest):
    """Validate EA API key."""
    try:
        user_id = await authenticate_ea_request(request.api_key)

        if user_id:
            logger.info(f"EA API key validated for user {user_id}")
            return EAAuthResponse(
                valid=True, user_id=user_id, message="API key is valid"
            )
        else:
            return EAAuthResponse(valid=False, message="Invalid API key")

    except Exception as e:
        logger.error(f"Error validating EA API key: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/order", response_model=EAOrderResponse)
async def ea_order(request: EAOrderRequest):
    """Process order from EA."""
    try:
        # Authenticate request
        user_id = await authenticate_ea_request(request.api_key)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if not order_manager:
            raise HTTPException(status_code=503, detail="Order manager not initialized")

        # Process order
        order_data = request.order
        result = await order_manager.execute_signal(order_data, user_id)

        if result and result.get("success"):
            ticket = result.get("ticket", "unknown")
            logger.info(
                f"Order executed successfully for user {user_id}, ticket: {ticket}"
            )

            # Send notification if telegram bot is available
            try:
                if telegram_bot and hasattr(telegram_bot, "notification_manager"):
                    await telegram_bot.notification_manager.send_order_notification(
                        {
                            "ticket": ticket,
                            "symbol": order_data.get("symbol"),
                            "type": order_data.get("action"),
                            "volume": order_data.get("volume"),
                            "price": order_data.get("price"),
                            "user_id": user_id,
                        }
                    )
            except Exception as notify_error:
                logger.warning(f"Failed to send order notification: {notify_error}")

            return EAOrderResponse(success=True, ticket=str(ticket))
        else:
            error_msg = (
                result.get("error", "Unknown error")
                if result
                else "Order execution failed"
            )
            logger.error(f"Order execution failed for user {user_id}: {error_msg}")
            return EAOrderResponse(success=False, error=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing EA order: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/positions", response_model=EAPositionsResponse)
async def ea_positions(request: EAPositionsRequest):
    """Get positions for EA."""
    try:
        # Authenticate request
        user_id = await authenticate_ea_request(request.api_key)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if not order_manager:
            raise HTTPException(status_code=503, detail="Order manager not initialized")

        # Get positions from database
        try:
            positions = []
            db_session = get_db_session()

            # Query positions for the user
            db_positions = (
                db_session.query(Position)
                .filter(Position.user_id == user_id, Position.status == "open")
                .all()
            )

            for pos in db_positions:
                positions.append(
                    {
                        "ticket": pos.ticket,
                        "symbol": pos.symbol,
                        "type": pos.position_type,
                        "volume": pos.volume,
                        "price_open": pos.price_open,
                        "sl": pos.stop_loss,
                        "tp": pos.take_profit,
                        "profit": pos.profit or 0.0,
                        "swap": pos.swap or 0.0,
                        "commission": pos.commission or 0.0,
                        "time_open": (
                            pos.time_open.isoformat() if pos.time_open else None
                        ),
                    }
                )

            db_session.close()

            logger.info(f"Retrieved {len(positions)} positions for user {user_id}")
            return EAPositionsResponse(positions=positions)

        except Exception as db_error:
            logger.error(f"Database error getting positions: {db_error}")
            # Return empty list on database error
            return EAPositionsResponse(positions=[])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EA positions: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/account", response_model=EAAccountResponse)
async def ea_account(request: EAAccountRequest):
    """Get account information for EA."""
    try:
        # Authenticate request
        user_id = await authenticate_ea_request(request.api_key)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Get account information from database or trading platform
        try:
            account_info = {
                "user_id": user_id,
                "balance": 0.0,
                "equity": 0.0,
                "margin": 0.0,
                "free_margin": 0.0,
                "margin_level": 0.0,
                "currency": "USD",
                "leverage": 100,
                "account_type": "demo",
            }

            # Try to get real account info from platform manager
            if order_manager and hasattr(order_manager, "platform_manager"):
                try:
                    platform_status = (
                        order_manager.platform_manager.get_platform_status()
                    )
                    if platform_status.get("connected_platforms", 0) > 0:
                        # Get account info from primary platform
                        primary_platform = platform_status.get("primary_platform")
                        if primary_platform and hasattr(
                            primary_platform, "get_account_info"
                        ):
                            real_account = await primary_platform.get_account_info()
                            if real_account:
                                account_info.update(real_account)
                except Exception as platform_error:
                    logger.warning(f"Could not get real account info: {platform_error}")

            logger.info(f"Retrieved account info for user {user_id}")
            return EAAccountResponse(account=account_info)

        except Exception as db_error:
            logger.error(f"Error getting account info: {db_error}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve account information"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EA account info: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/modify", response_model=EAModifyResponse)
async def ea_modify_position(request: EAModifyRequest):
    """Modify position from EA."""
    try:
        # Authenticate request
        user_id = await authenticate_ea_request(request.api_key)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if not order_manager:
            raise HTTPException(status_code=503, detail="Order manager not initialized")

        # Modify position
        try:
            success = await order_manager.modify_position(
                ticket=request.ticket,
                new_sl=request.new_sl,
                new_tp=request.new_tp,
                user_id=user_id,
            )

            if success:
                logger.info(f"Position {request.ticket} modified for user {user_id}")

                # Send notification
                try:
                    if telegram_bot and hasattr(telegram_bot, "notification_manager"):
                        await telegram_bot.notification_manager.send_position_notification(
                            {
                                "ticket": request.ticket,
                                "action": "modified",
                                "new_sl": request.new_sl,
                                "new_tp": request.new_tp,
                                "user_id": user_id,
                            },
                            "modified",
                        )
                except Exception as notify_error:
                    logger.warning(
                        f"Failed to send modification notification: {notify_error}"
                    )

                return EAModifyResponse(success=True)
            else:
                return EAModifyResponse(
                    success=False, error="Position modification failed"
                )

        except Exception as modify_error:
            logger.error(f"Error modifying position: {modify_error}")
            return EAModifyResponse(success=False, error=str(modify_error))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing EA position modification: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/close", response_model=EACloseResponse)
async def ea_close_position(request: EACloseRequest):
    """Close position from EA."""
    try:
        # Authenticate request
        user_id = await authenticate_ea_request(request.api_key)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if not order_manager:
            raise HTTPException(status_code=503, detail="Order manager not initialized")

        # Close position
        try:
            success = await order_manager.close_position(
                ticket=request.ticket, volume=request.volume, user_id=user_id
            )

            if success:
                logger.info(f"Position {request.ticket} closed for user {user_id}")

                # Send notification
                try:
                    if telegram_bot and hasattr(telegram_bot, "notification_manager"):
                        await telegram_bot.notification_manager.send_position_notification(
                            {
                                "ticket": request.ticket,
                                "action": "closed",
                                "volume": request.volume,
                                "user_id": user_id,
                            },
                            "closed",
                        )
                except Exception as notify_error:
                    logger.warning(f"Failed to send close notification: {notify_error}")

                return EACloseResponse(success=True)
            else:
                return EACloseResponse(success=False, error="Position close failed")

        except Exception as close_error:
            logger.error(f"Error closing position: {close_error}")
            return EACloseResponse(success=False, error=str(close_error))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing EA position close: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/history", response_model=EAHistoryResponse)
async def ea_trade_history(request: EAHistoryRequest):
    """Get trade history for EA."""
    try:
        # Authenticate request
        user_id = await authenticate_ea_request(request.api_key)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Get trade history from database
        try:
            trades = []
            db_session = get_db_session()

            # Query trades for the user within the specified days
            from datetime import timedelta

            cutoff_date = datetime.now(timezone.utc) - timedelta(days=request.days)

            db_trades = (
                db_session.query(Trade)
                .filter(Trade.user_id == user_id, Trade.time_close >= cutoff_date)
                .order_by(Trade.time_close.desc())
                .all()
            )

            for trade in db_trades:
                trades.append(
                    {
                        "ticket": trade.ticket,
                        "symbol": trade.symbol,
                        "type": trade.trade_type,
                        "volume": trade.volume,
                        "price_open": trade.price_open,
                        "price_close": trade.price_close,
                        "sl": trade.stop_loss,
                        "tp": trade.take_profit,
                        "profit": trade.profit,
                        "swap": trade.swap,
                        "commission": trade.commission,
                        "time_open": (
                            trade.time_open.isoformat() if trade.time_open else None
                        ),
                        "time_close": (
                            trade.time_close.isoformat() if trade.time_close else None
                        ),
                    }
                )

            db_session.close()

            logger.info(f"Retrieved {len(trades)} trades for user {user_id}")
            return EAHistoryResponse(trades=trades)

        except Exception as db_error:
            logger.error(f"Database error getting trade history: {db_error}")
            return EAHistoryResponse(trades=[])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting EA trade history: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/settings", response_model=EASettingsResponse)
async def ea_update_settings(request: EASettingsRequest):
    """Update EA settings."""
    try:
        # Authenticate request
        user_id = await authenticate_ea_request(request.api_key)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if not config_manager:
            raise HTTPException(
                status_code=503, detail="Config manager not initialized"
            )

        # Update user settings
        try:
            success = await config_manager.update_user_config(
                user_id, "ea_settings", request.settings
            )

            if success:
                logger.info(f"EA settings updated for user {user_id}")
                return EASettingsResponse(success=True)
            else:
                return EASettingsResponse(success=False, error="Settings update failed")

        except Exception as settings_error:
            logger.error(f"Error updating EA settings: {settings_error}")
            return EASettingsResponse(success=False, error=str(settings_error))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing EA settings update: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health", response_model=EAHealthResponse)
async def ea_health_check():
    """EA health check endpoint."""
    try:
        return EAHealthResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc).isoformat(),
            version="1.0.0",
        )

    except Exception as e:
        logger.error(f"Error in EA health check: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
