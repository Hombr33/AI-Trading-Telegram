# Monitoring and Observability

## Overview

The AI Trading Bot system includes comprehensive monitoring and observability features to ensure reliable operation and provide insights into system performance.

## Health Checks

### Basic Health Check
```bash
curl http://127.0.0.1:8000/healthz
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00.000Z",
  "version": "1.0.0",
  "environment": "production"
}
```

### Detailed Health Check
```bash
curl http://127.0.0.1:8000/healthz/detailed
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00.000Z",
  "version": "1.0.0",
  "environment": "production",
  "components": {
    "api": "healthy",
    "database": "healthy",
    "logging": "healthy"
  },
  "uptime": "2:15:30"
}
```

### Readiness Check
```bash
curl http://127.0.0.1:8000/readyz
```

### Liveness Check
```bash
curl http://127.0.0.1:8000/live
```

## Metrics

### Prometheus Metrics
```bash
curl http://127.0.0.1:8000/metrics
```

### Trading Metrics
```bash
curl http://127.0.0.1:8000/metrics/trading
```

### System Metrics
```bash
curl http://127.0.0.1:8000/metrics/system
```

## Logging

### Log Format
The system uses structured JSON logging with the following format:

```json
{
  "timestamp": "2025-01-27T10:30:00.000Z",
  "level": "info",
  "logger": "trading_bot.api",
  "message": "Order executed successfully",
  "order_id": "12345",
  "symbol": "EURUSD",
  "action": "buy",
  "volume": 0.1,
  "price": 1.0850,
  "correlation_id": "abc-123-def-456"
}
```

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General operational information
- **WARNING**: Potential issues that don't stop operation
- **ERROR**: Errors that affect functionality
- **CRITICAL**: Critical errors that may cause system failure

### Log Categories
- **Trade Logs**: All trading operations and decisions
- **System Logs**: System events and status changes
- **Risk Logs**: Risk management events and decisions
- **Audit Logs**: User actions and system modifications

## Monitoring Dashboard

### Key Metrics to Monitor
1. **System Health**
   - API response times
   - Database connection status
   - Memory and CPU usage

2. **Trading Performance**
   - Number of active positions
   - Win/loss ratio
   - Daily P&L
   - Risk exposure

3. **Bridge Communication**
   - MT4/MT5 connection status
   - Heartbeat frequency
   - Data transmission rates
   - Error rates

### Alerting
The system can be configured to send alerts for:
- System health degradation
- High error rates
- Risk limit breaches
- Connection failures
- Performance issues

## Performance Monitoring

### Response Time Targets
- **API Endpoints**: < 150ms
- **Database Queries**: < 50ms
- **EA Communication**: < 100ms

### Resource Usage Limits
- **Memory**: < 2GB
- **CPU**: < 70%
- **Disk I/O**: < 80%

### Throughput Targets
- **API Requests**: 50+ requests/second
- **Tick Processing**: Real-time without delays
- **Order Execution**: < 100ms latency

## Troubleshooting

### Common Issues
1. **High Response Times**
   - Check database performance
   - Monitor resource usage
   - Review logging levels

2. **Connection Failures**
   - Verify MT4/MT5 settings
   - Check network configuration
   - Review bridge token

3. **Performance Degradation**
   - Monitor system resources
   - Check for memory leaks
   - Review database queries

### Debug Mode
Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

This will provide detailed information about system operations and help identify issues.
