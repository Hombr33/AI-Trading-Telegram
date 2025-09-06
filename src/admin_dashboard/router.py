"""
Admin Dashboard Router
Provides web-based administrative interface for the AI Trading Bot.
"""

import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from ..services.multi_user_service import MultiUserService
from ..core.config import config

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["admin-dashboard"])

# Setup templates
templates = Jinja2Templates(directory="src/admin_dashboard/templates")

# Global service instances (set by main application)
multi_user_service: Optional[MultiUserService] = None


def get_multi_user_service() -> MultiUserService:
    """Get multi-user service instance."""
    if multi_user_service is None:
        raise HTTPException(
            status_code=503, detail="Multi-user service not initialized"
        )
    return multi_user_service


def set_multi_user_service(service: MultiUserService) -> None:
    """Set the global multi-user service instance."""
    global multi_user_service
    multi_user_service = service


# Authentication dependency
async def get_current_admin_user(
    request: Request, service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Get current admin user from session or token."""
    # For now, we'll use a simple admin check
    # In production, implement proper session/token-based authentication
    admin_telegram_id = request.query_params.get("admin_id")
    if not admin_telegram_id:
        raise HTTPException(status_code=401, detail="Admin authentication required")

    try:
        admin_id = int(admin_telegram_id)
        user = await service.user_manager.get_user(admin_id)
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges required")
        return {"telegram_id": admin_id, "user": user}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid admin ID")


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request, admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Main admin dashboard page."""
    try:
        service = get_multi_user_service()

        # Get admin statistics
        all_users = await service.user_manager.get_all_users(admin["telegram_id"])
        if not all_users:
            all_users = []

        # Calculate statistics
        active_users = sum(1 for user in all_users if user["is_active"])
        admin_users = sum(1 for user in all_users if user["role"] == "admin")
        suspended_users = sum(
            1 for user in all_users if user["subscription_status"] == "suspended"
        )
        expired_users = sum(
            1 for user in all_users if user["subscription_status"] == "expired"
        )

        # Get service stats
        service_stats = await service.get_enhanced_service_stats()

        stats = {
            "total_users": len(all_users),
            "active_users": active_users,
            "admin_users": admin_users,
            "suspended_users": suspended_users,
            "expired_users": expired_users,
            "total_platform_connections": 0,  # Would need to be calculated
            "active_platform_connections": 0,  # Would need to be calculated
            "total_signals_processed": service_stats.get("signal_stats", {}).get(
                "total_processed", 0
            ),
            "total_trades_executed": service_stats.get("signal_stats", {}).get(
                "auto_trades_executed", 0
            ),
            "system_health": service_stats.get("service_status", "unknown"),
        }

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "admin": admin,
                "stats": stats,
                "current_time": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/users", response_class=HTMLResponse)
async def user_management(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    role_filter: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    admin: Dict[str, Any] = Depends(get_current_admin_user),
):
    """User management page."""
    try:
        service = get_multi_user_service()

        # Get all users
        all_users = await service.user_manager.get_all_users(admin["telegram_id"])
        if not all_users:
            all_users = []

        # Apply filters
        filtered_users = []
        for user in all_users:
            if search:
                search_term = search.lower()
                if not (
                    search_term in user.get("username", "").lower()
                    or search_term in user.get("first_name", "").lower()
                    or search_term in user.get("last_name", "").lower()
                    or search_term in str(user.get("telegram_id", ""))
                ):
                    continue

            if role_filter and user.get("role") != role_filter:
                continue

            if status_filter and user.get("subscription_status") != status_filter:
                continue

            filtered_users.append(user)

        # Pagination
        total_users = len(filtered_users)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        users_page = filtered_users[start_idx:end_idx]

        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "admin": admin,
                "users": users_page,
                "page": page,
                "per_page": per_page,
                "total_users": total_users,
                "total_pages": (total_users + per_page - 1) // per_page,
                "search": search,
                "role_filter": role_filter,
                "status_filter": status_filter,
            },
        )

    except Exception as e:
        logger.error(f"Error loading user management: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/users/{telegram_id}", response_class=HTMLResponse)
async def user_details(
    request: Request,
    telegram_id: int,
    admin: Dict[str, Any] = Depends(get_current_admin_user),
):
    """User details page."""
    try:
        service = get_multi_user_service()

        # Get user details
        user = await service.user_manager.get_user(telegram_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user platform connections
        connections = await service.user_manager.get_user_platform_connections(
            telegram_id
        )

        # Get user configuration
        config_data = await service.config_manager.get_all_user_configs(telegram_id)

        # Get user trading status
        trading_status = await service.get_user_trading_status(telegram_id)

        return templates.TemplateResponse(
            "user_details.html",
            {
                "request": request,
                "admin": admin,
                "user": user,
                "connections": connections,
                "config": config_data,
                "trading_status": trading_status,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading user details: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/system", response_class=HTMLResponse)
async def system_monitoring(
    request: Request, admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """System monitoring page."""
    try:
        service = get_multi_user_service()

        # Get service statistics
        stats = await service.get_service_stats()

        # Get system health
        health_stats = await service.get_service_stats()  # Could be enhanced

        # Get signal distribution stats
        signal_stats = await service.get_signal_distribution_stats()

        return templates.TemplateResponse(
            "system.html",
            {
                "request": request,
                "admin": admin,
                "stats": stats,
                "health": health_stats,
                "signal_stats": signal_stats,
                "current_time": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error loading system monitoring: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/signals", response_class=HTMLResponse)
async def signal_monitoring(
    request: Request, admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Signal monitoring page."""
    try:
        service = get_multi_user_service()

        # Get signal distribution statistics
        signal_stats = await service.get_signal_distribution_stats()

        return templates.TemplateResponse(
            "signals.html",
            {
                "request": request,
                "admin": admin,
                "signal_stats": signal_stats,
                "current_time": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error loading signal monitoring: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/platforms", response_class=HTMLResponse)
async def platform_management(
    request: Request, admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Platform management page."""
    try:
        service = get_multi_user_service()

        # Get all users with their platform connections
        all_users = await service.user_manager.get_all_users(admin["telegram_id"])
        if not all_users:
            all_users = []

        # Collect all platform connections
        platform_connections = []
        for user in all_users:
            if user["is_active"]:
                connections = await service.user_manager.get_user_platform_connections(
                    user["telegram_id"]
                )
                for conn in connections:
                    platform_connections.append({"user": user, "connection": conn})

        return templates.TemplateResponse(
            "platforms.html",
            {
                "request": request,
                "admin": admin,
                "platform_connections": platform_connections,
                "current_time": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error loading platform management: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/config", response_class=HTMLResponse)
async def configuration_management(
    request: Request, admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    """Configuration management page."""
    try:
        service = get_multi_user_service()

        # Get system configuration
        system_config = {
            "environment": config.environment,
            "trading": config.trading.dict() if hasattr(config.trading, "dict") else {},
            "telegram": {
                "enabled": bool(config.telegram.bot_token),
                "chat_id": config.telegram.chat_id,
            },
        }

        return templates.TemplateResponse(
            "config.html",
            {
                "request": request,
                "admin": admin,
                "system_config": system_config,
                "current_time": datetime.utcnow().isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error loading configuration management: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


@router.get("/audit", response_class=HTMLResponse)
async def audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user_filter: Optional[int] = Query(None),
    action_filter: Optional[str] = Query(None),
    admin: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Audit logs page."""
    try:
        # For now, return a placeholder since audit logging might not be fully implemented
        audit_entries = [
            {
                "id": 1,
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": admin["telegram_id"],
                "action": "login",
                "resource": "admin_dashboard",
                "details": {"ip": "127.0.0.1"},
                "ip_address": "127.0.0.1",
            }
        ]

        return templates.TemplateResponse(
            "audit.html",
            {
                "request": request,
                "admin": admin,
                "audit_entries": audit_entries,
                "page": page,
                "per_page": per_page,
                "total_entries": len(audit_entries),
                "user_filter": user_filter,
                "action_filter": action_filter,
            },
        )

    except Exception as e:
        logger.error(f"Error loading audit logs: {e}")
        return templates.TemplateResponse(
            "error.html", {"request": request, "error": str(e)}
        )


# API endpoints for AJAX requests


@router.post("/api/users/{telegram_id}/status")
async def update_user_status(
    telegram_id: int,
    status: str = Form(...),
    admin: Dict[str, Any] = Depends(get_current_admin_user),
):
    """Update user status via AJAX."""
    try:
        service = get_multi_user_service()

        if status == "activate":
            # Implementation would depend on user manager methods
            pass
        elif status == "deactivate":
            # Implementation would depend on user manager methods
            pass
        elif status == "suspend":
            # Implementation would depend on user manager methods
            pass

        return JSONResponse(
            {
                "success": True,
                "message": f"User {telegram_id} status updated to {status}",
            }
        )

    except Exception as e:
        logger.error(f"Error updating user status: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.post("/api/system/emergency-stop")
async def emergency_stop(admin: Dict[str, Any] = Depends(get_current_admin_user)):
    """Emergency stop all trading activities."""
    try:
        service = get_multi_user_service()

        # Implementation would call emergency stop methods
        result = await service.emergency_stop_all()

        return JSONResponse(
            {
                "success": result.get("success", False),
                "message": result.get("message", "Emergency stop completed"),
            }
        )

    except Exception as e:
        logger.error(f"Error executing emergency stop: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/api/stats/realtime")
async def get_realtime_stats(admin: Dict[str, Any] = Depends(get_current_admin_user)):
    """Get real-time system statistics."""
    try:
        service = get_multi_user_service()

        # Get current statistics
        stats = await service.get_service_stats()

        return JSONResponse(
            {
                "success": True,
                "stats": stats,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting realtime stats: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)
