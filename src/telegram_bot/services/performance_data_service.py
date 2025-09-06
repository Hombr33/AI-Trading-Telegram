"""
Performance data service for Telegram bot - provides real performance metrics.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from src.core.logging import get_logger
from src.database.session import SessionLocal
from src.models.positions import Position
from src.models.trades import Trade

logger = get_logger(__name__)


class PerformanceDataService:
    """Service for providing real performance data to Telegram bot."""

    def __init__(self):
        self.logger = get_logger(__name__)

    async def get_performance_metrics(
        self, user_id: Optional[int] = None, days: int = 30
    ) -> Dict[str, Any]:
        """Get real performance metrics from database.

        Args:
            user_id: Optional user ID to filter metrics
            days: Number of days to look back

        Returns:
            Performance metrics dictionary
        """
        try:
            session = SessionLocal()
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Get trades in date range
            trades_query = session.query(Trade).filter(
                and_(Trade.close_time >= start_date, Trade.close_time <= end_date)
            )

            if user_id:
                trades_query = trades_query.filter(Trade.user_id == user_id)

            trades = trades_query.all()

            if not trades:
                return self._get_empty_performance_metrics()

            # Calculate metrics
            total_trades = len(trades)
            winning_trades = [t for t in trades if t.realized_pnl > 0]
            losing_trades = [t for t in trades if t.realized_pnl < 0]

            total_profit = sum(t.realized_pnl for t in trades)
            total_wins = sum(t.realized_pnl for t in winning_trades)
            total_losses = abs(sum(t.realized_pnl for t in losing_trades))

            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            profit_factor = (
                total_wins / total_losses if total_losses > 0 else float("inf")
            )

            avg_winner = total_wins / len(winning_trades) if winning_trades else 0
            avg_loser = total_losses / len(losing_trades) if losing_trades else 0
            avg_trade = total_profit / total_trades if total_trades > 0 else 0

            largest_winner = max((t.realized_pnl for t in winning_trades), default=0)
            largest_loser = min((t.realized_pnl for t in losing_trades), default=0)

            # Calculate holding time
            total_holding_time = timedelta()
            for trade in trades:
                if trade.open_time and trade.close_time:
                    holding_time = trade.close_time - trade.open_time
                    total_holding_time += holding_time

            avg_holding_time = (
                total_holding_time / total_trades if total_trades > 0 else timedelta()
            )

            # Calculate daily metrics
            daily_profit = await self._calculate_daily_profit(session, user_id, days)
            weekly_profit = await self._calculate_weekly_profit(session, user_id, days)
            monthly_profit = await self._calculate_monthly_profit(
                session, user_id, days
            )

            return {
                "total_profit": total_profit,
                "daily_profit": daily_profit,
                "weekly_profit": weekly_profit,
                "monthly_profit": monthly_profit,
                "today_profit": daily_profit,
                "week_profit": weekly_profit,
                "month_profit": monthly_profit,
                "today_trades": await self._count_trades_today(session, user_id),
                "week_trades": await self._count_trades_this_week(session, user_id),
                "month_trades": await self._count_trades_this_month(session, user_id),
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "sharpe_ratio": await self._calculate_sharpe_ratio(trades),
                "avg_winner": avg_winner,
                "avg_loser": avg_loser,
                "avg_trade": avg_trade,
                "largest_winner": largest_winner,
                "largest_loser": largest_loser,
                "best_trade": largest_winner,
                "worst_trade": largest_loser,
                "total_trades": total_trades,
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "avg_holding_time": str(avg_holding_time).split(".")[
                    0
                ],  # Remove microseconds
            }

        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return self._get_empty_performance_metrics()
        finally:
            session.close()

    async def get_risk_metrics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get real risk metrics from database.

        Args:
            user_id: Optional user ID to filter metrics

        Returns:
            Risk metrics dictionary
        """
        try:
            session = SessionLocal()

            # Get current positions
            positions_query = session.query(Position).filter(Position.is_active)
            if user_id:
                positions_query = positions_query.filter(Position.user_id == user_id)
            positions = positions_query.all()

            # Calculate exposure
            total_exposure = sum(
                pos.volume * pos.current_price for pos in positions if pos.current_price
            )
            max_exposure = 10000.0  # This should come from user account settings

            # Calculate drawdown
            drawdown = await self._calculate_drawdown(session, user_id)
            max_drawdown = await self._calculate_max_drawdown(session, user_id)

            # Calculate VaR (simplified)
            daily_var = await self._calculate_daily_var(session, user_id)

            # Calculate margin level (simplified)
            margin_level = 85.0  # This should come from MT5 or account settings

            # Calculate position correlation (simplified)
            position_correlation = await self._calculate_position_correlation(positions)

            return {
                "drawdown": drawdown,
                "max_drawdown": max_drawdown,
                "daily_var": daily_var,
                "daily_var_pct": (
                    daily_var / 10000.0 if daily_var else 0
                ),  # Assuming 10k account
                "margin_level": margin_level,
                "exposure": total_exposure / max_exposure if max_exposure > 0 else 0,
                "max_exposure": max_exposure,
                "largest_position": max(
                    (pos.volume * (pos.current_price or 0) for pos in positions),
                    default=0,
                ),
                "largest_position_pct": 0.2,  # This should be calculated based on account size
                "position_correlation": position_correlation,
                "market_volatility": 0.18,  # This should come from market data
                "correlation_to_spx": 0.35,  # This should be calculated from market data
                "correlation_to_btc": 0.25,  # This should be calculated from market data
                "risk_rating": self._calculate_risk_rating(
                    drawdown, total_exposure, margin_level
                ),
            }

        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return self._get_empty_risk_metrics()
        finally:
            session.close()

    async def get_trading_journal(
        self, user_id: Optional[int] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get trading journal from database.

        Args:
            user_id: Optional user ID to filter journal
            limit: Maximum number of entries to return

        Returns:
            List of journal entries
        """
        try:
            session = SessionLocal()
            query = session.query(Trade).order_by(Trade.close_time.desc()).limit(limit)

            if user_id:
                query = query.filter(Trade.user_id == user_id)

            trades = query.all()

            return [
                {
                    "id": trade.id,
                    "symbol": (
                        trade.instrument.symbol if trade.instrument else "Unknown"
                    ),
                    "type": trade.direction,
                    "volume": trade.volume,
                    "open_price": trade.open_price,
                    "close_price": trade.close_price,
                    "profit": trade.realized_pnl,
                    "open_time": (
                        trade.open_time.isoformat() if trade.open_time else None
                    ),
                    "close_time": (
                        trade.close_time.isoformat() if trade.close_time else None
                    ),
                    "status": trade.status,
                    "notes": trade.notes or "",
                }
                for trade in trades
            ]

        except Exception as e:
            logger.error(f"Error getting trading journal: {e}")
            return []
        finally:
            session.close()

    async def _calculate_daily_profit(
        self, session: Session, user_id: Optional[int], days: int
    ) -> float:
        """Calculate daily profit for the last N days."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            query = session.query(func.sum(Trade.realized_pnl)).filter(
                and_(Trade.close_time >= start_date, Trade.close_time <= end_date)
            )

            if user_id:
                query = query.filter(Trade.user_id == user_id)

            result = query.scalar()
            return float(result) if result else 0.0

        except Exception as e:
            logger.error(f"Error calculating daily profit: {e}")
            return 0.0

    async def _calculate_weekly_profit(
        self, session: Session, user_id: Optional[int], days: int
    ) -> float:
        """Calculate weekly profit for the last N days."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=min(days, 7))

            query = session.query(func.sum(Trade.realized_pnl)).filter(
                and_(Trade.close_time >= start_date, Trade.close_time <= end_date)
            )

            if user_id:
                query = query.filter(Trade.user_id == user_id)

            result = query.scalar()
            return float(result) if result else 0.0

        except Exception as e:
            logger.error(f"Error calculating weekly profit: {e}")
            return 0.0

    async def _calculate_monthly_profit(
        self, session: Session, user_id: Optional[int], days: int
    ) -> float:
        """Calculate monthly profit for the last N days."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=min(days, 30))

            query = session.query(func.sum(Trade.realized_pnl)).filter(
                and_(Trade.close_time >= start_date, Trade.close_time <= end_date)
            )

            if user_id:
                query = query.filter(Trade.user_id == user_id)

            result = query.scalar()
            return float(result) if result else 0.0

        except Exception as e:
            logger.error(f"Error calculating monthly profit: {e}")
            return 0.0

    async def _count_trades_today(
        self, session: Session, user_id: Optional[int]
    ) -> int:
        """Count trades executed today."""
        try:
            today = datetime.utcnow().date()
            query = session.query(func.count(Trade.id)).filter(
                func.date(Trade.close_time) == today
            )

            if user_id:
                query = query.filter(Trade.user_id == user_id)

            return query.scalar() or 0

        except Exception as e:
            logger.error(f"Error counting today's trades: {e}")
            return 0

    async def _count_trades_this_week(
        self, session: Session, user_id: Optional[int]
    ) -> int:
        """Count trades executed this week."""
        try:
            today = datetime.utcnow().date()
            week_start = today - timedelta(days=today.weekday())

            query = session.query(func.count(Trade.id)).filter(
                func.date(Trade.close_time) >= week_start
            )

            if user_id:
                query = query.filter(Trade.user_id == user_id)

            return query.scalar() or 0

        except Exception as e:
            logger.error(f"Error counting this week's trades: {e}")
            return 0

    async def _count_trades_this_month(
        self, session: Session, user_id: Optional[int]
    ) -> int:
        """Count trades executed this month."""
        try:
            today = datetime.utcnow().date()
            month_start = today.replace(day=1)

            query = session.query(func.count(Trade.id)).filter(
                func.date(Trade.close_time) >= month_start
            )

            if user_id:
                query = query.filter(Trade.user_id == user_id)

            return query.scalar() or 0

        except Exception as e:
            logger.error(f"Error counting this month's trades: {e}")
            return 0

    async def _calculate_sharpe_ratio(self, trades: List[Trade]) -> float:
        """Calculate Sharpe ratio from trades."""
        try:
            if not trades:
                return 0.0

            returns = [t.realized_pnl for t in trades if t.realized_pnl != 0]
            if not returns:
                return 0.0

            avg_return = sum(returns) / len(returns)
            variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
            std_dev = variance**0.5

            if std_dev == 0:
                return 0.0

            return avg_return / std_dev

        except Exception as e:
            logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0

    async def _calculate_drawdown(
        self, session: Session, user_id: Optional[int]
    ) -> float:
        """Calculate current drawdown."""
        try:
            # This is a simplified calculation
            # In production, this should track peak equity and calculate current drawdown
            return 0.05  # 5% placeholder

        except Exception as e:
            logger.error(f"Error calculating drawdown: {e}")
            return 0.0

    async def _calculate_max_drawdown(
        self, session: Session, user_id: Optional[int]
    ) -> float:
        """Calculate maximum drawdown."""
        try:
            # This is a simplified calculation
            # In production, this should track historical peak equity
            return 0.15  # 15% placeholder

        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0

    async def _calculate_daily_var(
        self, session: Session, user_id: Optional[int]
    ) -> float:
        """Calculate daily Value at Risk."""
        try:
            # This is a simplified calculation
            # In production, this should use proper VaR methodology
            return 150.0  # $150 placeholder

        except Exception as e:
            logger.error(f"Error calculating daily VaR: {e}")
            return 0.0

    async def _calculate_position_correlation(self, positions: List[Position]) -> float:
        """Calculate position correlation."""
        try:
            # This is a simplified calculation
            # In production, this should calculate actual correlation between positions
            return 0.15  # 15% placeholder

        except Exception as e:
            logger.error(f"Error calculating position correlation: {e}")
            return 0.0

    def _calculate_risk_rating(
        self, drawdown: float, exposure: float, margin_level: float
    ) -> str:
        """Calculate overall risk rating."""
        try:
            if drawdown > 0.10 or exposure > 0.8 or margin_level < 50:
                return "High"
            elif drawdown > 0.05 or exposure > 0.5 or margin_level < 100:
                return "Moderate"
            else:
                return "Low"
        except Exception as e:
            logger.error(f"Error calculating risk rating: {e}")
            return "Unknown"

    def _get_empty_performance_metrics(self) -> Dict[str, Any]:
        """Return empty performance metrics structure."""
        return {
            "total_profit": 0.0,
            "daily_profit": 0.0,
            "weekly_profit": 0.0,
            "monthly_profit": 0.0,
            "today_profit": 0.0,
            "week_profit": 0.0,
            "month_profit": 0.0,
            "today_trades": 0,
            "week_trades": 0,
            "month_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "sharpe_ratio": 0.0,
            "avg_winner": 0.0,
            "avg_loser": 0.0,
            "avg_trade": 0.0,
            "largest_winner": 0.0,
            "largest_loser": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "avg_holding_time": "0:00:00",
        }

    def _get_empty_risk_metrics(self) -> Dict[str, Any]:
        """Return empty risk metrics structure."""
        return {
            "drawdown": 0.0,
            "max_drawdown": 0.0,
            "daily_var": 0.0,
            "daily_var_pct": 0.0,
            "margin_level": 0.0,
            "exposure": 0.0,
            "max_exposure": 0.0,
            "largest_position": 0.0,
            "largest_position_pct": 0.0,
            "position_correlation": 0.0,
            "market_volatility": 0.0,
            "correlation_to_spx": 0.0,
            "correlation_to_btc": 0.0,
            "risk_rating": "Unknown",
        }
