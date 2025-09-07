"""
V1 API routes for general functionality.
"""

from datetime import datetime, timedelta
from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from ...core.config import config
from ...core.logging import get_logger
from ...database.session import get_db_session
from ...models import Instrument, Position, Signal, Trade

logger = get_logger(__name__)
router = APIRouter()


class SignalResponse(BaseModel):
    """Trading signal response."""

    id: str
    symbol: str
    bias: str
    confidence: int
    timeframe: str
    setups: List[dict]
    risk: dict
    management: dict
    created_at: datetime
    expires_at: Optional[str] = None


class SignalListResponse(BaseModel):
    """List of trading signals."""

    signals: List[SignalResponse]


class PositionResponse(BaseModel):
    """Position response."""

    id: str
    symbol: str
    direction: str
    volume: float
    open_price: float
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    open_time: str


class TradeResponse(BaseModel):
    """Trade response."""

    id: str
    symbol: str
    direction: str
    volume: float
    open_price: float
    close_price: Optional[float] = None
    profit_loss: Optional[float] = None
    status: str
    open_time: str
    close_time: Optional[str] = None


class InstrumentResponse(BaseModel):
    """Instrument response."""

    id: int
    symbol: str
    name: Optional[str] = None
    type: str
    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None
    is_active: bool


class PerformanceResponse(BaseModel):
    """Performance metrics response."""

    total_trades: int
    win_rate: float
    profit_factor: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    daily_pnl: float
    weekly_pnl: float
    monthly_pnl: float


@router.get("/signals", response_model=SignalListResponse)
async def get_signals(
    limit: int = 50, active_only: bool = True, db: Session = Depends(get_db_session)
):
    """Get available trading signals."""
    try:
        query = db.query(Signal).join(Instrument)

        if active_only:
            query = query.filter(Signal.is_active == True)

        # Filter out expired signals
        current_time = datetime.utcnow().isoformat()
        query = query.filter(
            (Signal.expires_at.is_(None)) | (Signal.expires_at > current_time)
        )

        signals = query.order_by(desc(Signal.created_at)).limit(limit).all()

        signal_responses = []
        for signal in signals:
            signal_responses.append(
                SignalResponse(
                    id=signal.signal_id,
                    symbol=signal.symbol,
                    bias=signal.bias,
                    confidence=signal.confidence,
                    timeframe=signal.timeframe,
                    setups=signal.setups or [],
                    risk=signal.risk_parameters or {},
                    management=signal.management_rules or {},
                    created_at=signal.created_at,
                    expires_at=signal.expires_at,
                )
            )

        return SignalListResponse(signals=signal_responses)

    except Exception as e:
        logger.error(f"Error retrieving signals: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve signals")


@router.get("/signals/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: str, db: Session = Depends(get_db_session)):
    """Get a specific trading signal."""
    try:
        signal = (
            db.query(Signal)
            .join(Instrument)
            .filter(Signal.signal_id == signal_id)
            .first()
        )

        if not signal:
            raise HTTPException(status_code=404, detail="Signal not found")

        return SignalResponse(
            id=signal.signal_id,
            symbol=signal.symbol,
            bias=signal.bias,
            confidence=signal.confidence,
            timeframe=signal.timeframe,
            setups=signal.setups or [],
            risk=signal.risk_parameters or {},
            management=signal.management_rules or {},
            created_at=signal.created_at,
            expires_at=signal.expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving signal {signal_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve signal")


@router.get("/positions")
async def get_positions(
    user_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db_session),
):
    """Get current open positions."""
    try:
        query = db.query(Position).join(Instrument)

        if active_only:
            query = query.filter(Position.is_active == True)

        if user_id:
            query = query.filter(Position.user_id == user_id)

        positions = query.all()

        position_responses = []
        for position in positions:
            position_responses.append(
                PositionResponse(
                    id=position.position_id,
                    symbol=position.instrument.symbol,
                    direction=position.direction,
                    volume=position.volume,
                    open_price=position.open_price,
                    current_price=position.current_price,
                    stop_loss=position.stop_loss,
                    take_profit=position.take_profit,
                    unrealized_pnl=position.unrealized_pnl,
                    open_time=position.open_time,
                )
            )

        return {"positions": position_responses}

    except Exception as e:
        logger.error(f"Error retrieving positions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve positions")


@router.get("/trades")
async def get_trades(
    user_id: Optional[int] = None,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    """Get trading history."""
    try:
        query = db.query(Trade).join(Instrument)

        if user_id:
            query = query.filter(Trade.user_id == user_id)

        if status:
            query = query.filter(Trade.status == status)

        trades = query.order_by(desc(Trade.open_time)).limit(limit).all()

        trade_responses = []
        for trade in trades:
            trade_responses.append(
                TradeResponse(
                    id=trade.trade_id,
                    symbol=trade.instrument.symbol,
                    direction=trade.direction,
                    volume=trade.volume,
                    open_price=trade.open_price,
                    close_price=trade.close_price,
                    profit_loss=trade.profit_loss,
                    status=trade.status,
                    open_time=trade.open_time,
                    close_time=trade.close_time,
                )
            )

        return {"trades": trade_responses}

    except Exception as e:
        logger.error(f"Error retrieving trades: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve trades")


@router.get("/performance", response_model=PerformanceResponse)
async def get_performance(
    user_id: Optional[int] = None, days: int = 30, db: Session = Depends(get_db_session)
):
    """Get trading performance metrics."""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Base query
        query = db.query(Trade).join(Instrument)

        if user_id:
            query = query.filter(Trade.user_id == user_id)

        # Filter by date range
        query = query.filter(Trade.open_time >= start_date.isoformat())

        # Get all trades in the period
        trades = query.all()

        if not trades:
            return PerformanceResponse(
                total_trades=0,
                win_rate=0.0,
                profit_factor=0.0,
                total_pnl=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
                daily_pnl=0.0,
                weekly_pnl=0.0,
                monthly_pnl=0.0,
            )

        # Calculate metrics
        total_trades = len(trades)
        closed_trades = [
            t for t in trades if t.status == "CLOSED" and t.profit_loss is not None
        ]

        if closed_trades:
            winning_trades = [t for t in closed_trades if t.profit_loss > 0]
            losing_trades = [t for t in closed_trades if t.profit_loss < 0]

            win_rate = (
                len(winning_trades) / len(closed_trades) * 100 if closed_trades else 0.0
            )

            total_profit = sum(t.profit_loss for t in winning_trades)
            total_loss = abs(sum(t.profit_loss for t in losing_trades))
            profit_factor = (
                total_profit / total_loss if total_loss > 0 else float("inf")
            )

            total_pnl = sum(t.profit_loss for t in closed_trades)

            # Calculate max drawdown (simplified)
            cumulative_pnl = 0
            peak = 0
            max_drawdown = 0
            for trade in sorted(closed_trades, key=lambda x: x.close_time):
                cumulative_pnl += trade.profit_loss
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                drawdown = peak - cumulative_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            # Calculate daily, weekly, monthly PnL
            daily_trades = [
                t
                for t in closed_trades
                if t.close_time
                and datetime.fromisoformat(t.close_time.replace("Z", "+00:00")).date()
                == end_date.date()
            ]
            weekly_trades = [
                t
                for t in closed_trades
                if t.close_time
                and datetime.fromisoformat(t.close_time.replace("Z", "+00:00"))
                >= end_date - timedelta(days=7)
            ]
            monthly_trades = [
                t
                for t in closed_trades
                if t.close_time
                and datetime.fromisoformat(t.close_time.replace("Z", "+00:00"))
                >= end_date - timedelta(days=30)
            ]

            daily_pnl = sum(t.profit_loss for t in daily_trades)
            weekly_pnl = sum(t.profit_loss for t in weekly_trades)
            monthly_pnl = sum(t.profit_loss for t in monthly_trades)

            # Simple Sharpe ratio calculation (assuming risk-free rate = 0)
            if len(closed_trades) > 1:
                returns = [t.profit_loss for t in closed_trades]
                mean_return = sum(returns) / len(returns)
                variance = sum((r - mean_return) ** 2 for r in returns) / (
                    len(returns) - 1
                )
                std_dev = variance**0.5
                sharpe_ratio = mean_return / std_dev if std_dev > 0 else 0.0
            else:
                sharpe_ratio = 0.0
        else:
            win_rate = 0.0
            profit_factor = 0.0
            total_pnl = 0.0
            max_drawdown = 0.0
            sharpe_ratio = 0.0
            daily_pnl = 0.0
            weekly_pnl = 0.0
            monthly_pnl = 0.0

        return PerformanceResponse(
            total_trades=total_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            daily_pnl=daily_pnl,
            weekly_pnl=weekly_pnl,
            monthly_pnl=monthly_pnl,
        )

    except Exception as e:
        logger.error(f"Error calculating performance metrics: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to calculate performance metrics"
        )


@router.get("/instruments")
async def get_instruments(
    active_only: bool = True,
    instrument_type: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    """Get available trading instruments."""
    try:
        query = db.query(Instrument)

        if active_only:
            query = query.filter(Instrument.is_active == True)

        if instrument_type:
            query = query.filter(Instrument.type == instrument_type.upper())

        instruments = query.order_by(Instrument.symbol).all()

        instrument_responses = []
        for instrument in instruments:
            instrument_responses.append(
                InstrumentResponse(
                    id=instrument.id,
                    symbol=instrument.symbol,
                    name=instrument.name,
                    type=instrument.type,
                    base_currency=instrument.base_currency,
                    quote_currency=instrument.quote_currency,
                    is_active=instrument.is_active,
                )
            )

        return {"instruments": instrument_responses}

    except Exception as e:
        logger.error(f"Error retrieving instruments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve instruments")


@router.get("/status")
async def get_status():
    """Get system status."""
    return {
        "status": "running",
        "version": "1.0.0",
        "environment": config.environment,
        "timezone": "UTC",
        "database": "connected",
        "api": "running",
        "bridge": "active",
    }
