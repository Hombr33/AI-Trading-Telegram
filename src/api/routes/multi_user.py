"""
Comprehensive Multi-user API routes for user management, configuration, and trading operations.

This module provides a complete REST API for managing the multi-user trading system,
including user management, platform connections, configuration, signal distribution,
trading operations, admin functions, monitoring, and security.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query, Path, Body
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from enum import Enum
import json

from ...services.user_manager import UserManager
from ...services.config_manager import ConfigManager
from ...services.multi_user_service import MultiUserService
from ...models.telegram_users import SubscriptionStatus, PlatformType, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/multi-user",
    tags=["multi-user"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)

# Global service instances (set by main application)
multi_user_service: Optional[MultiUserService] = None


def get_multi_user_service() -> MultiUserService:
    """Get multi-user service instance."""
    if multi_user_service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-user service not initialized"
        )
    return multi_user_service


# Enums for API
class SubscriptionStatusEnum(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class PlatformTypeEnum(str, Enum):
    MT5 = "mt5"
    CRYPTO = "crypto"


class UserRoleEnum(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class ConfigTypeEnum(str, Enum):
    RISK = "risk"
    SYMBOL = "symbol"
    SIGNAL = "signal"
    MODEL = "model"
    TRADING = "trading"
    RULES = "rules"


# Request/Response models

# === USER MANAGEMENT MODELS ===
class UserCreateRequest(BaseModel):
    """Create new user request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: UserRoleEnum = Field(UserRoleEnum.USER, description="User role")


class UserUpdateRequest(BaseModel):
    """Update user request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    is_active: Optional[bool] = Field(None, description="User active status")


class UserResponse(BaseModel):
    """User response model."""
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    subscription_status: str
    is_active: bool
    created_at: str
    last_activity: Optional[str]
    subscription_expires_at: Optional[str]


class UsersListResponse(BaseModel):
    """Users list response."""
    users: List[UserResponse]
    total_count: int
    active_count: int
    admin_count: int


# === SUBSCRIPTION MANAGEMENT MODELS ===
class SubscriptionUpdateRequest(BaseModel):
    """Update subscription request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    status: SubscriptionStatusEnum = Field(..., description="New subscription status")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    plan_type: Optional[str] = Field(None, description="Subscription plan type")
    auto_renew: Optional[bool] = Field(True, description="Auto-renewal setting")


class UserSubscriptionRequest(BaseModel):
    """User subscription request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    status: str = Field(..., description="Subscription status")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    plan_type: Optional[str] = Field(None, description="Subscription plan type")


class SubscriptionResponse(BaseModel):
    """Subscription response model."""
    telegram_id: int
    status: str
    expires_at: Optional[str]
    plan_type: Optional[str]
    auto_renew: bool
    days_remaining: Optional[int]
    is_expired: bool


# === PLATFORM CONNECTION MODELS ===
class PlatformConnectionCreateRequest(BaseModel):
    """Create platform connection request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    platform_type: PlatformTypeEnum = Field(..., description="Platform type")
    connection_name: str = Field(..., description="Connection name")
    api_key: str = Field(..., description="API key")
    api_secret: Optional[str] = Field(None, description="API secret (for crypto)")
    server_endpoint: Optional[str] = Field(None, description="Custom server endpoint")
    test_connection: Optional[bool] = Field(True, description="Test connection on creation")


class PlatformConnectionUpdateRequest(BaseModel):
    """Update platform connection request."""
    connection_id: int = Field(..., description="Connection ID")
    connection_name: Optional[str] = Field(None, description="Connection name")
    api_key: Optional[str] = Field(None, description="API key")
    api_secret: Optional[str] = Field(None, description="API secret")
    server_endpoint: Optional[str] = Field(None, description="Server endpoint")
    is_active: Optional[bool] = Field(None, description="Connection active status")


class PlatformConnectionResponse(BaseModel):
    """Platform connection response model."""
    id: int
    platform_type: str
    connection_name: str
    api_key_masked: str
    server_endpoint: Optional[str]
    is_active: bool
    last_connected: Optional[str]
    created_at: str
    connection_status: str


class PlatformConnectionsListResponse(BaseModel):
    """Platform connections list response."""
    connections: List[PlatformConnectionResponse]
    total_count: int
    active_count: int


# === CONFIGURATION MANAGEMENT MODELS ===
class ConfigurationCreateRequest(BaseModel):
    """Create/update configuration request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    config_type: ConfigTypeEnum = Field(..., description="Configuration type")
    config_data: Dict[str, Any] = Field(..., description="Configuration data")
    validate: Optional[bool] = Field(True, description="Validate configuration")


class ConfigurationResponse(BaseModel):
    """Configuration response model."""
    config_type: str
    config_data: Dict[str, Any]
    is_default: bool
    last_updated: Optional[str]
    validation_status: str


class ConfigurationListResponse(BaseModel):
    """Configuration list response."""
    configurations: Dict[str, ConfigurationResponse]
    total_count: int


class ConfigurationTemplateRequest(BaseModel):
    """Apply configuration template request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    template_name: str = Field(..., description="Template name (conservative/aggressive/scalping)")


class ConfigurationBackupRequest(BaseModel):
    """Configuration backup request."""
    telegram_id: int = Field(..., description="Telegram user ID")


class ConfigurationBackupResponse(BaseModel):
    """Configuration backup response."""
    backup_data: str
    created_at: str
    version: str


class ConfigurationRestoreRequest(BaseModel):
    """Configuration restore request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    backup_data: str = Field(..., description="Backup JSON data")


# === SIGNAL MANAGEMENT MODELS ===
class SignalRequest(BaseModel):
    """Signal processing request."""
    symbol: str = Field(..., description="Trading symbol")
    bias: str = Field(..., description="Market bias (BULLISH/BEARISH/NEUTRAL)")
    setups: List[Dict[str, Any]] = Field(..., description="Trading setups")
    confidence: int = Field(..., ge=0, le=100, description="Signal confidence percentage")
    timestamp: Optional[str] = Field(None, description="Signal timestamp")
    source: Optional[str] = Field("api", description="Signal source")


class SignalDistributionRequest(BaseModel):
    """Signal distribution request."""
    telegram_id: int = Field(..., description="Target user ID")
    signal_data: Dict[str, Any] = Field(..., description="Signal data")
    distribution_type: str = Field(..., description="Distribution type (immediate/delayed/batch)")


class SignalSubscriptionRequest(BaseModel):
    """Signal subscription request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    symbol: str = Field(..., description="Trading symbol")
    min_confidence: int = Field(60, ge=0, le=100, description="Minimum confidence threshold")


class SignalSubscriptionResponse(BaseModel):
    """Signal subscription response."""
    symbol: str
    min_confidence: int
    is_active: bool
    created_at: str


class SignalSubscriptionsListResponse(BaseModel):
    """Signal subscriptions list response."""
    subscriptions: List[SignalSubscriptionResponse]
    total_count: int


# === TRADING MANAGEMENT MODELS ===
class OrderRequest(BaseModel):
    """Order request model."""
    telegram_id: int = Field(..., description="Telegram user ID")
    symbol: str = Field(..., description="Trading symbol")
    order_type: str = Field(..., description="Order type (BUY/SELL)")
    volume: float = Field(..., description="Order volume")
    price: Optional[float] = Field(None, description="Order price")
    sl: Optional[float] = Field(None, description="Stop loss")
    tp: Optional[float] = Field(None, description="Take profit")
    platform: Optional[str] = Field(None, description="Target platform")


class PositionRequest(BaseModel):
    """Position request model."""
    telegram_id: int = Field(..., description="Telegram user ID")
    ticket: int = Field(..., description="Position ticket")
    sl: Optional[float] = Field(None, description="New stop loss")
    tp: Optional[float] = Field(None, description="New take profit")


class TradingStatusResponse(BaseModel):
    """Trading status response."""
    telegram_id: int
    positions: List[Dict[str, Any]]
    orders: List[Dict[str, Any]]
    risk_metrics: Dict[str, Any]
    platform_connections: List[str]
    last_update: str


# === ADMIN MODELS ===
class AdminStatsResponse(BaseModel):
    """Admin statistics response."""
    total_users: int
    active_users: int
    admin_users: int
    suspended_users: int
    expired_users: int
    total_platform_connections: int
    active_platform_connections: int
    total_signals_processed: int
    total_trades_executed: int
    system_health: Dict[str, Any]


class AdminUserManagementRequest(BaseModel):
    """Admin user management request."""
    admin_telegram_id: int = Field(..., description="Admin user ID")
    target_telegram_id: int = Field(..., description="Target user ID")
    action: str = Field(..., description="Action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")


class SystemHealthResponse(BaseModel):
    """System health response."""
    overall_status: str
    services: Dict[str, str]
    database: str
    telegram_bot: str
    ea_bridge: str
    crypto_bridge: str
    last_check: str
    uptime: str


# === MONITORING MODELS ===
class MonitoringStatsResponse(BaseModel):
    """Monitoring statistics response."""
    timestamp: str
    active_users: int
    signals_processed_today: int
    trades_executed_today: int
    system_load: Dict[str, Any]
    error_rate: float
    response_time_avg: float


class AuditLogEntry(BaseModel):
    """Audit log entry model."""
    id: int
    timestamp: str
    user_id: Optional[int]
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str]


class AuditLogResponse(BaseModel):
    """Audit log response."""
    entries: List[AuditLogEntry]
    total_count: int
    page: int
    per_page: int


# === SECURITY MODELS ===
class AuthRequest(BaseModel):
    """Authentication request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    token: Optional[str] = Field(None, description="Authentication token")


class AuthResponse(BaseModel):
    """Authentication response."""
    authenticated: bool
    user: Optional[UserResponse]
    token: Optional[str]
    expires_at: Optional[str]


class PermissionCheckRequest(BaseModel):
    """Permission check request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    resource: str = Field(..., description="Resource being accessed")
    action: str = Field(..., description="Action being performed")


class PermissionResponse(BaseModel):
    """Permission response."""
    allowed: bool
    reason: Optional[str]


# === USER MANAGEMENT ENDPOINTS ===

@router.post("/users", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    service: MultiUserService = Depends(get_multi_user_service)
) -> UserResponse:
    """Create a new user."""
    try:
        success = await service.user_manager.create_user(
            telegram_id=request.telegram_id,
            username=request.username,
            first_name=request.first_name,
            last_name=request.last_name
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user. User may already exist."
            )

        # Get the created user
        user = await service.user_manager.get_user(request.telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User created but could not retrieve user data"
            )

        return UserResponse(
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            subscription_status=user.subscription_status.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_activity=user.last_activity.isoformat() if user.last_activity else None,
            subscription_expires_at=user.subscription_expires_at.isoformat() if user.subscription_expires_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users", response_model=UsersListResponse)
async def get_all_users(
    admin_telegram_id: int = Query(..., description="Admin user ID for authorization"),
    include_inactive: bool = Query(False, description="Include inactive users"),
    role_filter: Optional[UserRoleEnum] = Query(None, description="Filter by user role"),
    subscription_filter: Optional[SubscriptionStatusEnum] = Query(None, description="Filter by subscription status"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> UsersListResponse:
    """Get all registered users (admin only)."""
    try:
        users = await service.user_manager.get_all_users(admin_telegram_id)

        if users is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )

        # Apply filters
        filtered_users = []
        for user in users:
            if not include_inactive and not user["is_active"]:
                continue
            if role_filter and user["role"] != role_filter.value:
                continue
            if subscription_filter and user["subscription_status"] != subscription_filter.value:
                continue
            filtered_users.append(user)

        # Convert to response models
        user_responses = []
        active_count = 0
        admin_count = 0

        for user in filtered_users:
            user_responses.append(UserResponse(
                telegram_id=user["telegram_id"],
                username=user["username"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                role=user["role"],
                subscription_status=user["subscription_status"],
                is_active=user["is_active"],
                created_at=user["created_at"],
                last_activity=user["last_activity"],
                subscription_expires_at=None  # Would need to be added to user manager
            ))

            if user["is_active"]:
                active_count += 1
            if user["role"] == "admin":
                admin_count += 1

        return UsersListResponse(
            users=user_responses,
            total_count=len(user_responses),
            active_count=active_count,
            admin_count=admin_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}", response_model=UserResponse)
async def get_user(
    telegram_id: int = Path(..., description="Telegram user ID"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> UserResponse:
    """Get a specific user by Telegram ID."""
    try:
        user = await service.user_manager.get_user(telegram_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            subscription_status=user.subscription_status.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_activity=user.last_activity.isoformat() if user.last_activity else None,
            subscription_expires_at=user.subscription_expires_at.isoformat() if user.subscription_expires_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/users/{telegram_id}", response_model=UserResponse)
async def update_user(
    telegram_id: int = Path(..., description="Telegram user ID"),
    request: UserUpdateRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> UserResponse:
    """Update user information."""
    try:
        # Verify the user exists
        user = await service.user_manager.get_user(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update user information (this would need to be implemented in UserManager)
        # For now, return the existing user
        return UserResponse(
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role.value,
            subscription_status=user.subscription_status.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_activity=user.last_activity.isoformat() if user.last_activity else None,
            subscription_expires_at=user.subscription_expires_at.isoformat() if user.subscription_expires_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/users/{telegram_id}")
async def delete_user(
    telegram_id: int = Path(..., description="Telegram user ID"),
    admin_telegram_id: int = Query(..., description="Admin user ID for authorization"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Delete a user (admin only)."""
    try:
        # This would need to be implemented in UserManager
        # For now, return not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User deletion not yet implemented"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === SUBSCRIPTION MANAGEMENT ENDPOINTS ===

@router.post("/users/subscription", response_model=SubscriptionResponse)
async def set_user_subscription(
    request: SubscriptionUpdateRequest = Body(...),
    admin_telegram_id: int = Query(..., description="Admin user ID for authorization"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> SubscriptionResponse:
    """Set user subscription status (admin only)."""
    try:
        # Convert enum to model enum
        status_enum = SubscriptionStatus.ACTIVE
        if request.status == SubscriptionStatusEnum.EXPIRED:
            status_enum = SubscriptionStatus.EXPIRED
        elif request.status == SubscriptionStatusEnum.SUSPENDED:
            status_enum = SubscriptionStatus.SUSPENDED

        success = await service.user_manager.set_subscription(
            admin_telegram_id, request.telegram_id, status_enum, request.expires_at
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required or user not found"
            )

        # Get updated user to return current status
        user = await service.user_manager.get_user(request.telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found after update"
            )

        # Calculate days remaining
        days_remaining = None
        is_expired = False
        if user.subscription_expires_at:
            now = datetime.utcnow()
            if user.subscription_expires_at > now:
                days_remaining = (user.subscription_expires_at - now).days
            else:
                is_expired = True

        return SubscriptionResponse(
            telegram_id=user.telegram_id,
            status=user.subscription_status.value,
            expires_at=user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            plan_type=request.plan_type,
            auto_renew=request.auto_renew,
            days_remaining=days_remaining,
            is_expired=is_expired
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set user subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}/subscription", response_model=SubscriptionResponse)
async def get_user_subscription(
    telegram_id: int = Path(..., description="Telegram user ID"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> SubscriptionResponse:
    """Get user subscription details."""
    try:
        user = await service.user_manager.get_user(telegram_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Calculate days remaining
        days_remaining = None
        is_expired = False
        if user.subscription_expires_at:
            now = datetime.utcnow()
            if user.subscription_expires_at > now:
                days_remaining = (user.subscription_expires_at - now).days
            else:
                is_expired = True

        return SubscriptionResponse(
            telegram_id=user.telegram_id,
            status=user.subscription_status.value,
            expires_at=user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            plan_type=None,  # Would need to be added to user model
            auto_renew=True,  # Default value
            days_remaining=days_remaining,
            is_expired=is_expired
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/users/subscription")
async def set_user_subscription(
    request: UserSubscriptionRequest,
    admin_telegram_id: int,
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Set user subscription status (admin only)."""
    try:
        # Parse subscription status
        if request.status.lower() == "active":
            status_enum = SubscriptionStatus.ACTIVE
        elif request.status.lower() == "expired":
            status_enum = SubscriptionStatus.EXPIRED
        elif request.status.lower() == "suspended":
            status_enum = SubscriptionStatus.SUSPENDED
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid subscription status. Use: active, expired, or suspended"
            )
        
        # Parse expiration date if provided
        expires_at = None
        if request.expires_at:
            from datetime import datetime
            expires_at = datetime.fromisoformat(request.expires_at.replace('Z', '+00:00'))
        
        success = await service.user_manager.set_subscription(
            admin_telegram_id, request.telegram_id, status_enum, expires_at
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Subscription updated for user {request.telegram_id}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required or user not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set user subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === PLATFORM CONNECTION MANAGEMENT ENDPOINTS ===

@router.post("/users/platform-connection", response_model=PlatformConnectionResponse)
async def register_platform_connection(
    request: PlatformConnectionCreateRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> PlatformConnectionResponse:
    """Register platform connection for user."""
    try:
        # Convert enum to model enum
        platform_type = PlatformType.MT5 if request.platform_type == PlatformTypeEnum.MT5 else PlatformType.CRYPTO

        success = await service.user_manager.register_platform_connection(
            telegram_id=request.telegram_id,
            platform_type=platform_type,
            connection_name=request.connection_name,
            api_key=request.api_key,
            api_secret=request.api_secret,
            server_endpoint=request.server_endpoint
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register platform connection. User may not be authorized or connection already exists."
            )

        # Get the created connection
        connections = await service.user_manager.get_user_platform_connections(request.telegram_id)
        new_connection = connections[-1] if connections else None

        if not new_connection:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Connection created but could not retrieve connection data"
            )

        return PlatformConnectionResponse(
            id=new_connection["id"],
            platform_type=new_connection["platform_type"],
            connection_name=new_connection["connection_name"],
            api_key_masked=new_connection["api_key"][:8] + "..." if new_connection["api_key"] else None,
            server_endpoint=new_connection["server_endpoint"],
            is_active=True,  # New connections are active by default
            last_connected=new_connection["last_connected"],
            created_at=new_connection["created_at"],
            connection_status="created"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register platform connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}/connections", response_model=PlatformConnectionsListResponse)
async def get_user_connections(
    telegram_id: int = Path(..., description="Telegram user ID"),
    include_inactive: bool = Query(False, description="Include inactive connections"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> PlatformConnectionsListResponse:
    """Get user's platform connections."""
    try:
        connections = await service.user_manager.get_user_platform_connections(telegram_id)

        # Filter inactive connections if requested
        if not include_inactive:
            connections = [conn for conn in connections if conn.get("is_active", True)]

        # Convert to response models
        connection_responses = []
        active_count = 0

        for conn in connections:
            connection_responses.append(PlatformConnectionResponse(
                id=conn["id"],
                platform_type=conn["platform_type"],
                connection_name=conn["connection_name"],
                api_key_masked=conn["api_key"][:8] + "..." if conn["api_key"] else None,
                server_endpoint=conn["server_endpoint"],
                is_active=conn.get("is_active", True),
                last_connected=conn["last_connected"],
                created_at=conn["created_at"],
                connection_status="active" if conn.get("is_active", True) else "inactive"
            ))

            if conn.get("is_active", True):
                active_count += 1

        return PlatformConnectionsListResponse(
            connections=connection_responses,
            total_count=len(connection_responses),
            active_count=active_count
        )

    except Exception as e:
        logger.error(f"Failed to get user connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/users/connections/{connection_id}", response_model=PlatformConnectionResponse)
async def update_platform_connection(
    connection_id: int = Path(..., description="Connection ID"),
    request: PlatformConnectionUpdateRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> PlatformConnectionResponse:
    """Update platform connection."""
    try:
        # This would need to be implemented in UserManager
        # For now, return not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Connection update not yet implemented"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update platform connection {connection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/users/connections/{connection_id}")
async def delete_platform_connection(
    connection_id: int = Path(..., description="Connection ID"),
    telegram_id: int = Query(..., description="User ID for authorization"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Delete platform connection."""
    try:
        # This would need to be implemented in UserManager
        # For now, return not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Connection deletion not yet implemented"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete platform connection {connection_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === CONFIGURATION MANAGEMENT ENDPOINTS ===

@router.post("/users/configuration", response_model=ConfigurationResponse)
async def set_user_configuration(
    request: ConfigurationCreateRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> ConfigurationResponse:
    """Set user configuration."""
    try:
        # Validate configuration
        is_valid, error_message = await service.config_manager.validate_config(
            request.config_type.value, request.config_data
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid configuration: {error_message}"
            )

        success = await service.config_manager.set_user_config(
            request.telegram_id, request.config_type.value, request.config_data
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update configuration. User may not exist or invalid config type."
            )

        # Get the updated configuration
        config_data = await service.config_manager.get_user_config(
            request.telegram_id, request.config_type.value
        )

        return ConfigurationResponse(
            config_type=request.config_type.value,
            config_data=config_data or {},
            is_default=config_data is None,
            last_updated=datetime.utcnow().isoformat(),
            validation_status="valid"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set user configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}/configuration", response_model=ConfigurationListResponse)
async def get_user_configuration(
    telegram_id: int = Path(..., description="Telegram user ID"),
    config_type: Optional[ConfigTypeEnum] = Query(None, description="Specific configuration type"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> ConfigurationListResponse:
    """Get user configuration."""
    try:
        configurations = {}

        if config_type:
            # Get specific configuration
            config_data = await service.config_manager.get_user_config(telegram_id, config_type.value)
            if config_data:
                configurations[config_type.value] = ConfigurationResponse(
                    config_type=config_type.value,
                    config_data=config_data,
                    is_default=False,
                    last_updated=None,  # Would need to be added to config model
                    validation_status="valid"
                )
        else:
            # Get all configurations
            all_configs = await service.config_manager.get_all_user_configs(telegram_id)
            for config_type_name, config_data in all_configs.items():
                configurations[config_type_name] = ConfigurationResponse(
                    config_type=config_type_name,
                    config_data=config_data,
                    is_default=False,
                    last_updated=None,
                    validation_status="valid"
                )

        return ConfigurationListResponse(
            configurations=configurations,
            total_count=len(configurations)
        )

    except Exception as e:
        logger.error(f"Failed to get user configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/users/configuration/template")
async def apply_configuration_template(
    request: ConfigurationTemplateRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Apply a configuration template to a user."""
    try:
        success = await service.config_manager.apply_config_template(
            request.telegram_id, request.template_name
        )

        if success:
            return {
                "status": "success",
                "message": f"Configuration template '{request.template_name}' applied to user {request.telegram_id}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to apply template '{request.template_name}'. Template may not exist."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply configuration template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/users/configuration/backup", response_model=ConfigurationBackupResponse)
async def backup_user_configuration(
    request: ConfigurationBackupRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> ConfigurationBackupResponse:
    """Create a backup of user configuration."""
    try:
        backup_data = await service.config_manager.backup_user_configs(request.telegram_id)

        if not backup_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create configuration backup"
            )

        return ConfigurationBackupResponse(
            backup_data=backup_data,
            created_at=datetime.utcnow().isoformat(),
            version="1.0"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to backup user configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/users/configuration/restore")
async def restore_user_configuration(
    request: ConfigurationRestoreRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Restore user configuration from backup."""
    try:
        success = await service.config_manager.restore_user_configs(
            request.telegram_id, request.backup_data
        )

        if success:
            return {
                "status": "success",
                "message": f"Configuration restored for user {request.telegram_id}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to restore configuration. Backup data may be invalid."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore user configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === SIGNAL MANAGEMENT ENDPOINTS ===

@router.post("/signal/process")
async def process_signal(
    signal_request: SignalRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Process and distribute trading signal to users."""
    try:
        signal_data = signal_request.dict()
        result = await service.process_signal(signal_data)

        if result["success"]:
            return {
                "status": "success",
                "message": "Signal processed successfully",
                "distributed_to": result["distributed_to"],
                "skipped": result["skipped"],
                "execution_results": result["execution_results"],
                "distribution_plan": result.get("distribution_plan", {})
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signal processing failed: {result['error']}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process signal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/signal/distribute")
async def distribute_signal_to_user(
    request: SignalDistributionRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Distribute signal to a specific user."""
    try:
        # This would use the signal distributor
        result = await service.send_signal_to_users(request.signal_data)

        return {
            "status": "success",
            "message": f"Signal distributed to user {request.telegram_id}",
            "distribution_type": request.distribution_type
        }

    except Exception as e:
        logger.error(f"Failed to distribute signal to user {request.telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/users/{telegram_id}/signal-subscription", response_model=SignalSubscriptionResponse)
async def subscribe_to_symbol(
    telegram_id: int = Path(..., description="Telegram user ID"),
    request: SignalSubscriptionRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> SignalSubscriptionResponse:
    """Subscribe user to trading signal for a symbol."""
    try:
        success = await service.user_manager.subscribe_to_symbol(
            telegram_id, request.symbol, request.min_confidence
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to subscribe to symbol. User may not be authorized."
            )

        return SignalSubscriptionResponse(
            symbol=request.symbol,
            min_confidence=request.min_confidence,
            is_active=True,
            created_at=datetime.utcnow().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to subscribe to symbol: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}/signal-subscriptions", response_model=SignalSubscriptionsListResponse)
async def get_user_signal_subscriptions(
    telegram_id: int = Path(..., description="Telegram user ID"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> SignalSubscriptionsListResponse:
    """Get user's symbol subscriptions."""
    try:
        subscriptions = await service.user_manager.get_user_subscriptions(telegram_id)

        subscription_responses = []
        for sub in subscriptions:
            subscription_responses.append(SignalSubscriptionResponse(
                symbol=sub["symbol"],
                min_confidence=sub["min_confidence"],
                is_active=True,
                created_at=sub["created_at"]
            ))

        return SignalSubscriptionsListResponse(
            subscriptions=subscription_responses,
            total_count=len(subscription_responses)
        )

    except Exception as e:
        logger.error(f"Failed to get user subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/users/{telegram_id}/signal-subscriptions/{symbol}")
async def unsubscribe_from_symbol(
    telegram_id: int = Path(..., description="Telegram user ID"),
    symbol: str = Path(..., description="Trading symbol"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Unsubscribe user from trading signal for a symbol."""
    try:
        success = await service.user_manager.unsubscribe_from_symbol(telegram_id, symbol)

        if success:
            return {
                "status": "success",
                "message": f"User {telegram_id} unsubscribed from {symbol} signals"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unsubscribe from symbol: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === TRADING MANAGEMENT ENDPOINTS ===

@router.post("/users/{telegram_id}/orders", response_model=Dict[str, Any])
async def submit_user_order(
    telegram_id: int = Path(..., description="Telegram user ID"),
    request: OrderRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Submit order for specific user."""
    try:
        order_data = {
            "symbol": request.symbol,
            "order_type": request.order_type,
            "volume": request.volume,
            "price": request.price,
            "sl": request.sl,
            "tp": request.tp,
            "platform": request.platform
        }

        result = await service.submit_user_order(telegram_id, order_data)

        if result["success"]:
            return {
                "status": "success",
                "message": "Order submitted successfully",
                "order_id": result.get("order_id"),
                "details": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order submission failed: {result.get('error', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit order for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}/trading-status", response_model=TradingStatusResponse)
async def get_user_trading_status(
    telegram_id: int = Path(..., description="Telegram user ID"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> TradingStatusResponse:
    """Get comprehensive trading status for user."""
    try:
        status_data = await service.get_user_trading_status(telegram_id)

        return TradingStatusResponse(
            telegram_id=telegram_id,
            positions=status_data.get("positions", []),
            orders=status_data.get("pending_orders", []),
            risk_metrics=status_data.get("risk_metrics", {}),
            platform_connections=status_data.get("ea_connection", "").split(",") if status_data.get("ea_connection") else [],
            last_update=status_data.get("timestamp", datetime.utcnow().isoformat())
        )

    except Exception as e:
        logger.error(f"Failed to get trading status for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/users/{telegram_id}/positions/{ticket}")
async def modify_user_position(
    telegram_id: int = Path(..., description="Telegram user ID"),
    ticket: int = Path(..., description="Position ticket"),
    request: PositionRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Modify position for specific user."""
    try:
        result = await service.modify_user_position(telegram_id, ticket, request.sl, request.tp)

        if result["success"]:
            return {
                "status": "success",
                "message": f"Position {ticket} modified successfully",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Position modification failed: {result.get('error', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to modify position for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/users/{telegram_id}/positions/{ticket}")
async def close_user_position(
    telegram_id: int = Path(..., description="Telegram user ID"),
    ticket: int = Path(..., description="Position ticket"),
    volume: Optional[float] = Query(None, description="Volume to close (partial close)"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Close position for specific user."""
    try:
        result = await service.close_user_position(telegram_id, ticket, volume)

        if result["success"]:
            return {
                "status": "success",
                "message": f"Position {ticket} closed successfully",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Position close failed: {result.get('error', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close position for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/users/{telegram_id}/orders/{order_id}")
async def cancel_user_order(
    telegram_id: int = Path(..., description="Telegram user ID"),
    order_id: str = Path(..., description="Order ID"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Cancel order for specific user."""
    try:
        result = await service.cancel_user_order(telegram_id, order_id)

        if result["success"]:
            return {
                "status": "success",
                "message": f"Order {order_id} cancelled successfully",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cancellation failed: {result.get('error', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel order for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/users/{telegram_id}/emergency-stop")
async def emergency_user_stop(
    telegram_id: int = Path(..., description="Telegram user ID"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Emergency stop all trading for user."""
    try:
        result = await service.emergency_user_stop(telegram_id)

        if result["success"]:
            return {
                "status": "success",
                "message": f"Emergency stop completed for user {telegram_id}",
                "details": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Emergency stop failed: {result.get('error', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Emergency stop failed for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === ADMIN OPERATIONS ENDPOINTS ===

@router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin_telegram_id: int = Query(..., description="Admin user ID for authorization"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> AdminStatsResponse:
    """Get comprehensive admin statistics (admin only)."""
    try:
        # Verify admin privileges
        if not await service.user_manager.is_admin(admin_telegram_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )

        # Get all users
        all_users = await service.user_manager.get_all_users(admin_telegram_id)
        if not all_users:
            all_users = []

        # Calculate statistics
        active_users = sum(1 for user in all_users if user["is_active"])
        admin_users = sum(1 for user in all_users if user["role"] == "admin")
        suspended_users = sum(1 for user in all_users if user["subscription_status"] == "suspended")
        expired_users = sum(1 for user in all_users if user["subscription_status"] == "expired")

        # Get service stats
        service_stats = await service.get_enhanced_service_stats()

        return AdminStatsResponse(
            total_users=len(all_users),
            active_users=active_users,
            admin_users=admin_users,
            suspended_users=suspended_users,
            expired_users=expired_users,
            total_platform_connections=0,  # Would need to be calculated
            active_platform_connections=0,  # Would need to be calculated
            total_signals_processed=service_stats.get("signal_stats", {}).get("total_processed", 0),
            total_trades_executed=service_stats.get("signal_stats", {}).get("auto_trades_executed", 0),
            system_health=service_stats.get("system_health", {"status": "unknown"})
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/admin/users/{telegram_id}/promote")
async def promote_user_to_admin(
    telegram_id: int = Path(..., description="Target user ID"),
    admin_telegram_id: int = Query(..., description="Admin user ID for authorization"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Promote user to admin (admin only)."""
    try:
        success = await service.user_manager.add_admin(admin_telegram_id, telegram_id)

        if success:
            return {
                "status": "success",
                "message": f"User {telegram_id} promoted to admin"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required or operation failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to promote user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/admin/users/{telegram_id}/demote")
async def demote_user_from_admin(
    telegram_id: int = Path(..., description="Target user ID"),
    admin_telegram_id: int = Query(..., description="Admin user ID for authorization"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Demote user from admin (admin only)."""
    try:
        success = await service.user_manager.remove_admin(admin_telegram_id, telegram_id)

        if success:
            return {
                "status": "success",
                "message": f"User {telegram_id} demoted from admin"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required or operation failed"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to demote user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/admin/users/trading-status")
async def get_all_users_trading_status(
    admin_telegram_id: int = Query(..., description="Admin user ID for authorization"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Get trading status for all users (admin only)."""
    try:
        result = await service.get_all_users_trading_status(admin_telegram_id)

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get all users trading status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/admin/signal/batch-process")
async def force_process_batch_signals(
    admin_telegram_id: int = Query(..., description="Admin user ID for authorization"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Force process all pending batch signals (admin only)."""
    try:
        # Verify admin privileges
        if not await service.user_manager.is_admin(admin_telegram_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )

        result = await service.force_process_batch_signals()

        return {
            "status": "success",
            "message": "Batch signal processing completed",
            "details": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to force process batch signals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === MONITORING AND STATISTICS ENDPOINTS ===

@router.get("/stats", response_model=MonitoringStatsResponse)
async def get_service_stats(
    service: MultiUserService = Depends(get_multi_user_service)
) -> MonitoringStatsResponse:
    """Get service statistics."""
    try:
        stats = await service.get_service_stats()

        return MonitoringStatsResponse(
            timestamp=datetime.utcnow().isoformat(),
            active_users=stats.get("bot_stats", {}).get("active_users", 0),
            signals_processed_today=stats.get("signal_stats", {}).get("total_processed", 0),
            trades_executed_today=stats.get("signal_stats", {}).get("auto_trades_executed", 0),
            system_load={
                "queue_sizes": stats.get("queue_stats", {}),
                "active_tasks": stats.get("active_tasks", 0)
            },
            error_rate=0.0,  # Would need to be calculated
            response_time_avg=0.0  # Would need to be calculated
        )

    except Exception as e:
        logger.error(f"Failed to get service stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    service: MultiUserService = Depends(get_multi_user_service)
) -> SystemHealthResponse:
    """Get system health status."""
    try:
        stats = await service.get_service_stats()

        # Determine overall status
        overall_status = "healthy"
        if stats.get("service_status") != "running":
            overall_status = "unhealthy"

        return SystemHealthResponse(
            overall_status=overall_status,
            services={
                "multi_user_service": stats.get("service_status", "unknown"),
                "telegram_bot": stats.get("bot_stats", {}).get("status", "unknown"),
                "database": "connected",  # Would need to be checked
                "ea_bridge": "active",  # Would need to be checked
                "crypto_bridge": "active"  # Would need to be checked
            },
            database="connected",
            telegram_bot=stats.get("bot_stats", {}).get("status", "unknown"),
            ea_bridge="active",
            crypto_bridge="active",
            last_check=datetime.utcnow().isoformat(),
            uptime=stats.get("uptime", "Unknown")
        )

    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/stats/signal-distribution")
async def get_signal_distribution_stats(
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Get detailed signal distribution statistics."""
    try:
        stats = await service.get_signal_distribution_stats()

        return {
            "status": "success",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Failed to get signal distribution stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === SECURITY ENDPOINTS ===

@router.post("/auth/check", response_model=AuthResponse)
async def check_authentication(
    request: AuthRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> AuthResponse:
    """Check user authentication."""
    try:
        user = await service.user_manager.get_user(request.telegram_id)

        if user and user.is_active:
            return AuthResponse(
                authenticated=True,
                user=UserResponse(
                    telegram_id=user.telegram_id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=user.role.value,
                    subscription_status=user.subscription_status.value,
                    is_active=user.is_active,
                    created_at=user.created_at.isoformat(),
                    last_activity=user.last_activity.isoformat() if user.last_activity else None,
                    subscription_expires_at=user.subscription_expires_at.isoformat() if user.subscription_expires_at else None
                ),
                token=request.token,
                expires_at=(datetime.utcnow() + timedelta(hours=24)).isoformat()
            )
        else:
            return AuthResponse(
                authenticated=False,
                user=None,
                token=None,
                expires_at=None
            )

    except Exception as e:
        logger.error(f"Failed to check authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/auth/permissions", response_model=PermissionResponse)
async def check_permissions(
    request: PermissionCheckRequest = Body(...),
    service: MultiUserService = Depends(get_multi_user_service)
) -> PermissionResponse:
    """Check user permissions for a resource."""
    try:
        user = await service.user_manager.get_user(request.telegram_id)

        if not user or not user.is_active:
            return PermissionResponse(
                allowed=False,
                reason="User not found or inactive"
            )

        # Check admin privileges
        if user.is_admin:
            return PermissionResponse(
                allowed=True,
                reason="Admin user"
            )

        # Check subscription status
        if not await service.user_manager.is_subscribed(request.telegram_id):
            return PermissionResponse(
                allowed=False,
                reason="Active subscription required"
            )

        # Additional permission checks based on resource and action
        # This is a simplified implementation
        allowed_resources = ["signal", "configuration", "trading"]
        allowed_actions = ["read", "write", "execute"]

        if request.resource not in allowed_resources:
            return PermissionResponse(
                allowed=False,
                reason=f"Resource '{request.resource}' not allowed"
            )

        if request.action not in allowed_actions:
            return PermissionResponse(
                allowed=False,
                reason=f"Action '{request.action}' not allowed"
            )

        return PermissionResponse(
            allowed=True,
            reason="Permission granted"
        )

    except Exception as e:
        logger.error(f"Failed to check permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# === UTILITY ENDPOINTS ===

@router.post("/users/{telegram_id}/initialize-trading-session")
async def initialize_user_trading_session(
    telegram_id: int = Path(..., description="Telegram user ID"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Initialize complete trading session for user."""
    try:
        result = await service.initialize_user_trading_session(telegram_id)

        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "details": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session initialization failed: {result.get('error', 'Unknown error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initialize trading session for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}/risk-metrics")
async def get_user_risk_metrics(
    telegram_id: int = Path(..., description="Telegram user ID"),
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Get risk metrics for specific user."""
    try:
        risk_metrics = await service.get_user_risk_metrics(telegram_id)

        return {
            "status": "success",
            "telegram_id": telegram_id,
            "risk_metrics": risk_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get risk metrics for user {telegram_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


def set_multi_user_service(service: MultiUserService) -> None:
    """Set the global multi-user service instance."""
    global multi_user_service
    multi_user_service = service
