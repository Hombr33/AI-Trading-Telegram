"""
Multi-user API routes for user management and configuration.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from ...services.user_manager import UserManager
from ...services.config_manager import ConfigManager
from ...services.multi_user_service import MultiUserService
from ...models.telegram_users import SubscriptionStatus, PlatformType

logger = logging.getLogger(__name__)

router = APIRouter()

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


# Request/Response models
class SignalRequest(BaseModel):
    """Signal processing request."""
    symbol: str = Field(..., description="Trading symbol")
    bias: str = Field(..., description="Market bias (BULLISH/BEARISH/NEUTRAL)")
    setups: List[Dict[str, Any]] = Field(..., description="Trading setups")
    confidence: int = Field(..., ge=0, le=100, description="Signal confidence percentage")
    timestamp: Optional[str] = Field(None, description="Signal timestamp")


class UserSubscriptionRequest(BaseModel):
    """User subscription management request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    status: str = Field(..., description="Subscription status (active/expired/suspended)")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")


class PlatformConnectionRequest(BaseModel):
    """Platform connection request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    platform_type: str = Field(..., description="Platform type (mt5/crypto)")
    connection_name: str = Field(..., description="Connection name")
    api_key: str = Field(..., description="API key")
    api_secret: Optional[str] = Field(None, description="API secret (for crypto)")
    server_endpoint: Optional[str] = Field(None, description="Custom server endpoint")


class ConfigurationRequest(BaseModel):
    """User configuration request."""
    telegram_id: int = Field(..., description="Telegram user ID")
    config_type: str = Field(..., description="Configuration type")
    config_data: Dict[str, Any] = Field(..., description="Configuration data")


@router.post("/signal/process")
async def process_signal(
    signal_request: SignalRequest,
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
                "execution_results": result["execution_results"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Signal processing failed: {result['error']}"
            )
            
    except Exception as e:
        logger.error(f"Failed to process signal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users")
async def get_all_users(
    admin_telegram_id: int,
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Get all registered users (admin only)."""
    try:
        users = await service.user_manager.get_all_users(admin_telegram_id)
        
        if users is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        return {
            "status": "success",
            "users": users,
            "total_count": len(users)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get users: {e}")
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


@router.post("/users/platform-connection")
async def register_platform_connection(
    request: PlatformConnectionRequest,
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Register platform connection for user."""
    try:
        # Parse platform type
        if request.platform_type.lower() == "mt5":
            platform_type = PlatformType.MT5
        elif request.platform_type.lower() == "crypto":
            platform_type = PlatformType.CRYPTO
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid platform type. Use: mt5 or crypto"
            )
        
        success = await service.user_manager.register_platform_connection(
            telegram_id=request.telegram_id,
            platform_type=platform_type,
            connection_name=request.connection_name,
            api_key=request.api_key,
            api_secret=request.api_secret,
            server_endpoint=request.server_endpoint
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Platform connection registered for user {request.telegram_id}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to register platform connection. User may not be authorized or connection already exists."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register platform connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}/connections")
async def get_user_connections(
    telegram_id: int,
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Get user's platform connections."""
    try:
        connections = await service.user_manager.get_user_platform_connections(telegram_id)
        
        return {
            "status": "success",
            "connections": connections,
            "total_count": len(connections)
        }
        
    except Exception as e:
        logger.error(f"Failed to get user connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/users/configuration")
async def set_user_configuration(
    request: ConfigurationRequest,
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Set user configuration."""
    try:
        # Validate configuration
        is_valid, error_message = await service.config_manager.validate_config(
            request.config_type, request.config_data
        )
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid configuration: {error_message}"
            )
        
        success = await service.config_manager.set_user_config(
            request.telegram_id, request.config_type, request.config_data
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Configuration updated for user {request.telegram_id}"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update configuration. User may not exist or invalid config type."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set user configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/users/{telegram_id}/configuration")
async def get_user_configuration(
    telegram_id: int,
    config_type: Optional[str] = None,
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Get user configuration."""
    try:
        if config_type:
            config_data = await service.config_manager.get_user_config(telegram_id, config_type)
            return {
                "status": "success",
                "config_type": config_type,
                "config_data": config_data
            }
        else:
            all_configs = await service.config_manager.get_all_user_configs(telegram_id)
            return {
                "status": "success",
                "configurations": all_configs
            }
            
    except Exception as e:
        logger.error(f"Failed to get user configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/stats")
async def get_service_stats(
    service: MultiUserService = Depends(get_multi_user_service)
) -> Dict[str, Any]:
    """Get service statistics."""
    try:
        stats = await service.get_service_stats()
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get service stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


def set_multi_user_service(service: MultiUserService) -> None:
    """Set the global multi-user service instance."""
    global multi_user_service
    multi_user_service = service
