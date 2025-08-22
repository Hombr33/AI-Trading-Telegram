# System Architecture

## Overview

The AI Trading Bot system follows a modular, event-driven architecture designed for high performance, reliability, and maintainability. The system is built around a Python-based API server that communicates with MetaTrader 4/5 through HTTP REST endpoints.

## Architecture Principles

### 1. Modularity
- **Single Responsibility**: Each module has a single, well-defined purpose
- **Loose Coupling**: Modules communicate through defined interfaces
- **High Cohesion**: Related functionality is grouped together

### 2. Event-Driven Design
- **Asynchronous Processing**: Non-blocking operations for better performance
- **Event Sourcing**: All system events are logged and can be replayed
- **Message Queuing**: Reliable message delivery between components

### 3. Security First
- **Authentication**: Bridge token-based authentication
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive input sanitization
- **Audit Logging**: Complete action history tracking

## System Components

### 1. MetaTrader Bridge (EA)
```
┌─────────────────────────────────────────────────────────────┐
│                    BridgeEA.mq4/mq5                        │
├─────────────────────────────────────────────────────────────┤
│ • Heartbeat Management                                      │
│ • Tick Data Streaming                                       │
│ • Position Snapshot                                         │
│ • Order Request Forwarding                                  │
│ • Auto-reconnection Logic                                   │
└─────────────────────────────────────────────────────────────┘
```

**Responsibilities:**
- Maintain connection to Python API
- Send periodic heartbeats
- Stream real-time tick data
- Provide position snapshots
- Handle order requests from Python

### 2. Python API Server
```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│ • Bridge Routes (/bridge/*)                                │
│ • Health Monitoring (/healthz, /readyz)                   │
│ • Metrics Collection (/metrics)                            │
│ • Trading API (/v1/*)                                      │
│ • Risk Management Engine                                   │
│ • Telegram Bot Integration                                 │
└─────────────────────────────────────────────────────────────┘
```

**Responsibilities:**
- Handle EA communication
- Process trading signals
- Manage risk parameters
- Execute trading logic
- Provide monitoring endpoints

### 3. Database Layer
```
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                          │
├─────────────────────────────────────────────────────────────┤
│ • User Management                                          │
│ • Trading Data (signals, orders, trades, positions)       │
│ • Risk Events                                              │
│ • Audit Logs                                               │
│ • Performance Metrics                                       │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- ACID compliance
- WAL mode for better concurrency
- Automatic migrations with Alembic
- Backup and recovery procedures

### 4. Risk Management Engine
```
┌─────────────────────────────────────────────────────────────┐
│                  Risk Management                            │
├─────────────────────────────────────────────────────────────┤
│ • Position Sizing Calculator                               │
│ • Daily Risk Limits                                        │
│ • Correlation Management                                    │
│ • Volatility Adjustments                                   │
│ • Emergency Stop Procedures                                │
└─────────────────────────────────────────────────────────────┘
```

**Risk Controls:**
- 2% risk per trade maximum
- 6% daily drawdown limit
- $25 daily loss limit
- Position correlation monitoring
- Volatility-based adjustments

## Data Flow

### 1. EA to API Communication
```
MT4/MT5 EA → HTTP POST → Python API → Database
     ↓              ↓           ↓         ↓
  Heartbeat    Tick Data   Validation   Storage
  Positions    Orders      Processing   Logging
```

### 2. Signal Processing
```
AI Analysis → Signal Validation → Risk Check → Order Generation
     ↓              ↓              ↓           ↓
  Pattern      Schema Check    Limits      MT4/MT5
  Recognition  Confidence     Validation  Execution
```

### 3. Risk Management Flow
```
Order Request → Risk Validation → Position Sizing → Execution
     ↓              ↓              ↓           ↓
  Parameters    Daily Limits    Calculator   MT4/MT5
  Validation    Correlation     Risk %       Orders
```

## Communication Protocol

### HTTP REST Endpoints

#### Bridge Endpoints
- `POST /bridge/heartbeat` - EA connection status
- `POST /bridge/tick` - Real-time price data
- `POST /bridge/order_request` - Order validation
- `POST /bridge/order_exec_report` - Execution feedback
- `POST /bridge/position_snapshot` - Position updates

#### Monitoring Endpoints
- `GET /healthz` - Basic health check
- `GET /readyz` - Readiness check
- `GET /metrics` - Prometheus metrics

#### API Endpoints
- `GET /v1/signals` - Trading signals
- `GET /v1/positions` - Open positions
- `GET /v1/trades` - Trade history
- `GET /v1/performance` - Performance metrics

### Authentication
- **Bridge Token**: Static bearer token for EA communication
- **Rate Limiting**: 50 requests/second with burst allowance
- **Retry Logic**: Exponential backoff for failed requests

## Performance Characteristics

### Latency Targets
- **Signal Generation**: < 500ms
- **Order Execution**: < 100ms
- **API Response**: < 150ms

### Throughput
- **Ticks per Second**: 1000+
- **Orders per Second**: 10+
- **Concurrent Users**: 100+

### Resource Usage
- **Memory**: < 2GB
- **CPU**: < 70%
- **Disk I/O**: < 80%

## Scalability Considerations

### Horizontal Scaling
- **API Servers**: Multiple instances behind load balancer
- **Database**: Read replicas for analytics
- **Cache Layer**: Redis for high-frequency data

### Vertical Scaling
- **Resource Limits**: Configurable memory and CPU limits
- **Connection Pooling**: Database connection management
- **Batch Processing**: Efficient bulk operations

## Security Architecture

### Network Security
- **Localhost Only**: API runs on 127.0.0.1 for security
- **Firewall Rules**: Restrict external access
- **VPN Access**: Secure remote access if needed

### Application Security
- **Input Validation**: All inputs sanitized and validated
- **SQL Injection Protection**: Parameterized queries
- **XSS Prevention**: Output encoding
- **CSRF Protection**: Token-based validation

### Data Security
- **Encryption**: Sensitive data encrypted at rest
- **Access Control**: Role-based permissions
- **Audit Trail**: Complete action logging
- **Data Retention**: Configurable retention policies

## Monitoring and Observability

### Health Checks
- **Liveness**: Service availability
- **Readiness**: Service readiness for traffic
- **Startup**: Initialization status

### Metrics Collection
- **Business Metrics**: Trades, P&L, win rate
- **System Metrics**: CPU, memory, disk usage
- **Application Metrics**: Response times, error rates

### Alerting
- **Critical**: System failures, connection loss
- **Warning**: High error rates, performance degradation
- **Info**: Daily summaries, weekly reports

## Deployment Architecture

### Development Environment
```
┌─────────────────┐    ┌─────────────────┐
│   MT4/MT5      │    │   Python App    │
│   (Local)      │◄──►│   (Local)       │
└─────────────────┘    └─────────────────┘
```

### Production Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MT4/MT5      │    │   Load Balancer │    │   API Servers   │
│   (Trading)    │◄──►│   (Nginx)       │◄──►│   (Multiple)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   (SQLite/PostgreSQL) │
                       └─────────────────┘
```

## Error Handling and Recovery

### Error Categories
- **Connection Errors**: Network issues, timeouts
- **Validation Errors**: Invalid data, schema violations
- **Business Logic Errors**: Risk limit violations
- **System Errors**: Database failures, memory issues

### Recovery Strategies
- **Automatic Retry**: Exponential backoff for transient errors
- **Circuit Breaker**: Prevent cascade failures
- **Graceful Degradation**: Reduce functionality under stress
- **Emergency Stop**: Immediate halt for critical issues

## Future Enhancements

### Planned Features
- **WebSocket Support**: Real-time bidirectional communication
- **Multiple Exchange Support**: Additional trading platforms
- **Advanced AI Models**: Machine learning integration
- **Mobile App**: iOS/Android trading interface

### Technical Improvements
- **Microservices**: Service decomposition
- **Event Streaming**: Apache Kafka integration
- **Container Orchestration**: Kubernetes deployment
- **Service Mesh**: Istio for service communication