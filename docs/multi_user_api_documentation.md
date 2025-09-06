# Multi-User API Documentation

## Overview

The Multi-User API provides comprehensive REST endpoints for managing the multi-user trading system. This API enables user management, platform connections, configuration, signal distribution, trading operations, and administrative functions.

## Base URL

```
/api/v1/multi-user
```

## Authentication

All endpoints require proper authentication. Admin endpoints require admin privileges.

## API Endpoints

### User Management

#### Create User
```http
POST /users
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user"
}
```

**Response:**
```json
{
  "telegram_id": 123456789,
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "role": "user",
  "subscription_status": "active",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "last_activity": null,
  "subscription_expires_at": null
}
```

#### Get All Users (Admin Only)
```http
GET /users?admin_telegram_id=123456789
```

**Query Parameters:**
- `admin_telegram_id` (required): Admin user ID
- `include_inactive`: Include inactive users (default: false)
- `role_filter`: Filter by user role
- `subscription_filter`: Filter by subscription status

#### Get Specific User
```http
GET /users/{telegram_id}
```

#### Update User
```http
PUT /users/{telegram_id}
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "username": "john_doe_updated",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true
}
```

#### Delete User (Admin Only)
```http
DELETE /users/{telegram_id}?admin_telegram_id=123456789
```

### Subscription Management

#### Update User Subscription (Admin Only)
```http
POST /users/subscription?admin_telegram_id=123456789
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "status": "active",
  "expires_at": "2024-12-31T23:59:59",
  "plan_type": "premium",
  "auto_renew": true
}
```

#### Get User Subscription
```http
GET /users/{telegram_id}/subscription
```

### Platform Connection Management

#### Register Platform Connection
```http
POST /users/platform-connection
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "platform_type": "mt5",
  "connection_name": "My MT5 Account",
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "server_endpoint": "mt5.server.com",
  "test_connection": true
}
```

#### Get User Platform Connections
```http
GET /users/{telegram_id}/connections?include_inactive=false
```

#### Update Platform Connection
```http
PUT /users/connections/{connection_id}
```

#### Delete Platform Connection
```http
DELETE /users/connections/{connection_id}?telegram_id=123456789
```

### Configuration Management

#### Set User Configuration
```http
POST /users/configuration
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "config_type": "risk",
  "config_data": {
    "risk_per_trade_pct": 2.0,
    "max_daily_drawdown_pct": 6.0,
    "max_daily_loss_usd": 25.0
  },
  "validate": true
}
```

#### Get User Configuration
```http
GET /users/{telegram_id}/configuration?config_type=risk
```

#### Apply Configuration Template
```http
POST /users/configuration/template
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "template_name": "conservative"
}
```

Available templates: `conservative`, `aggressive`, `scalping`

#### Backup User Configuration
```http
POST /users/configuration/backup
```

#### Restore User Configuration
```http
POST /users/configuration/restore
```

### Signal Management

#### Process Signal
```http
POST /signal/process
```

**Request Body:**
```json
{
  "symbol": "XAUUSD",
  "bias": "BULLISH",
  "setups": [
    {
      "type": "BUY",
      "entry_zone": [1950.00, 1960.00],
      "sl": 1940.00,
      "tp": [1970.00, 1980.00],
      "confidence": 75
    }
  ],
  "confidence": 75,
  "timestamp": "2024-01-01T12:00:00Z",
  "source": "api"
}
```

#### Subscribe to Symbol
```http
POST /users/{telegram_id}/signal-subscription
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "symbol": "EURUSD",
  "min_confidence": 70
}
```

#### Get User Signal Subscriptions
```http
GET /users/{telegram_id}/signal-subscriptions
```

#### Unsubscribe from Symbol
```http
DELETE /users/{telegram_id}/signal-subscriptions/{symbol}
```

### Trading Management

#### Submit User Order
```http
POST /users/{telegram_id}/orders
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "symbol": "XAUUSD",
  "order_type": "BUY",
  "volume": 0.1,
  "price": 1950.00,
  "sl": 1940.00,
  "tp": 1970.00,
  "platform": "mt5"
}
```

#### Get User Trading Status
```http
GET /users/{telegram_id}/trading-status
```

#### Modify User Position
```http
PUT /users/{telegram_id}/positions/{ticket}
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "ticket": 12345,
  "sl": 1945.00,
  "tp": 1975.00
}
```

#### Close User Position
```http
DELETE /users/{telegram_id}/positions/{ticket}?volume=0.05
```

#### Cancel User Order
```http
DELETE /users/{telegram_id}/orders/{order_id}
```

#### Emergency Stop User Trading
```http
POST /users/{telegram_id}/emergency-stop
```

### Admin Operations

#### Get Admin Statistics
```http
GET /admin/stats?admin_telegram_id=123456789
```

#### Promote User to Admin
```http
POST /admin/users/{telegram_id}/promote?admin_telegram_id=123456789
```

#### Demote User from Admin
```http
POST /admin/users/{telegram_id}/demote?admin_telegram_id=123456789
```

#### Get All Users Trading Status (Admin)
```http
GET /admin/users/trading-status?admin_telegram_id=123456789
```

#### Force Process Batch Signals (Admin)
```http
POST /admin/signal/batch-process?admin_telegram_id=123456789
```

### Monitoring and Statistics

#### Get Service Statistics
```http
GET /stats
```

#### Get System Health
```http
GET /health
```

#### Get Signal Distribution Statistics
```http
GET /stats/signal-distribution
```

### Security

#### Check Authentication
```http
POST /auth/check
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "token": "optional_token"
}
```

#### Check Permissions
```http
POST /auth/permissions
```

**Request Body:**
```json
{
  "telegram_id": 123456789,
  "resource": "trading",
  "action": "execute"
}
```

### Utility Endpoints

#### Initialize User Trading Session
```http
POST /users/{telegram_id}/initialize-trading-session
```

#### Get User Risk Metrics
```http
GET /users/{telegram_id}/risk-metrics
```

## Error Responses

All endpoints return standardized error responses:

```json
{
  "detail": "Error description"
}
```

Common HTTP status codes:
- `400`: Bad Request - Invalid input data
- `401`: Unauthorized - Authentication required
- `403`: Forbidden - Insufficient privileges
- `404`: Not Found - Resource not found
- `422`: Validation Error - Input validation failed
- `500`: Internal Server Error - Server error
- `503`: Service Unavailable - Service not initialized

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- User endpoints: 100 requests per minute
- Admin endpoints: 50 requests per minute
- Signal processing: 10 requests per minute

## WebSocket Support

For real-time updates, consider using WebSocket connections:

```
ws://your-server/api/v1/multi-user/ws/{telegram_id}
```

## Examples

### Python Client Example

```python
import requests

BASE_URL = "http://your-server/api/v1/multi-user"

# Create a user
user_data = {
    "telegram_id": 123456789,
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "role": "user"
}

response = requests.post(f"{BASE_URL}/users", json=user_data)
user = response.json()

# Set user configuration
config_data = {
    "telegram_id": 123456789,
    "config_type": "risk",
    "config_data": {
        "risk_per_trade_pct": 2.0,
        "max_daily_drawdown_pct": 6.0
    }
}

response = requests.post(f"{BASE_URL}/users/configuration", json=config_data)

# Process a signal
signal_data = {
    "symbol": "XAUUSD",
    "bias": "BULLISH",
    "setups": [
        {
            "type": "BUY",
            "entry_zone": [1950.00, 1960.00],
            "sl": 1940.00,
            "tp": [1970.00, 1980.00],
            "confidence": 75
        }
    ],
    "confidence": 75
}

response = requests.post(f"{BASE_URL}/signal/process", json=signal_data)
```

## Configuration Templates

### Conservative Template
- Risk per trade: 1%
- Max daily drawdown: 3%
- Min confidence: 75
- Max open positions: 5

### Aggressive Template
- Risk per trade: 3%
- Max daily drawdown: 8%
- Min confidence: 55
- Max open positions: 15

### Scalping Template
- Risk per trade: 0.5%
- Max daily drawdown: 2%
- Analysis frequency: 2 minutes
- Timeframes: M15, M5, M1

## Best Practices

1. **Always validate** configuration data before submission
2. **Use appropriate error handling** for API responses
3. **Implement retry logic** for transient failures
4. **Monitor rate limits** and implement backoff strategies
5. **Use WebSocket connections** for real-time updates when possible
6. **Backup configurations** before making significant changes
7. **Test in staging** before deploying to production

## Security Considerations

- All sensitive data is encrypted in transit and at rest
- API keys are masked in responses
- Admin operations require explicit authorization
- Audit logs are maintained for all operations
- Rate limiting prevents abuse
- Input validation prevents injection attacks

## Support

For API support or questions, contact the development team or refer to the main project documentation.
