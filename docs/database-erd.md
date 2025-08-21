# Database Entity Relationship Diagram

## Overview

The AI Trading Bot system uses a SQLite database with a comprehensive schema designed to support trading operations, risk management, and system monitoring.

## Database Schema

### Core Tables

#### Users and Authentication
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│    users    │    │  api_keys   │    │  sessions   │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │◄───│ user_id (FK)│    │ user_id (FK)│
│ username    │    │ key_hash    │    │ session_token│
│ email       │    │ name        │    │ ip_address  │
│ password_hash│   │ is_active   │    │ user_agent  │
│ is_active   │    │ expires_at  │    │ expires_at  │
│ is_admin    │    │ permissions │    │ is_active   │
│ last_login  │    └─────────────┘    └─────────────┘
│ login_attempts│
│ locked_until │
└─────────────┘
```

#### Trading Instruments
```
┌─────────────┐
│ instruments │
├─────────────┤
│ id (PK)     │
│ symbol      │
│ name        │
│ type        │
│ base_currency│
│ quote_currency│
│ pip_value   │
│ point_value │
│ min_lot_size│
│ max_lot_size│
│ lot_step    │
│ is_active   │
│ trading_hours│
│ spread_avg  │
│ volatility_avg│
└─────────────┘
```

#### Trading Signals
```
┌─────────────┐    ┌─────────────┐
│ instruments │    │   signals   │
├─────────────┤    ├─────────────┤
│ id (PK)     │◄───│ instrument_id(FK)│
│ symbol      │    │ signal_id   │
│ name        │    │ bias        │
│ type        │    │ confidence  │
│ ...         │    │ timeframe   │
└─────────────┘    │ analysis_data│
                   │ setups      │
                   │ risk_parameters│
                   │ management_rules│
                   │ is_active   │
                   │ expires_at  │
                   │ source      │
                   └─────────────┘
```

#### Orders and Execution
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   signals   │    │   orders    │    │    fills    │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │◄───│ signal_id (FK)│  │ order_id (FK)│
│ signal_id   │    │ instrument_id(FK)│ │ fill_id     │
│ bias        │    │ user_id (FK)│    │ instrument_id(FK)│
│ ...         │    │ action      │    │ volume      │
└─────────────┘    │ order_type  │    │ price       │
                   │ volume      │    │ fill_time   │
                   │ price       │    │ commission  │
                   │ stop_loss   │    │ swap        │
                   │ take_profit │    │ magic_number│
                   │ comment     │    │ fill_data   │
                   │ status      │    └─────────────┘
                   │ mt_ticket   │
                   │ execution_data│
                   └─────────────┘
```

#### Trades and Positions
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   orders    │    │   trades    │    │  positions  │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │◄───│ order_id (FK)│  │ trade_id (FK)│
│ order_id    │    │ instrument_id(FK)│ │ instrument_id(FK)│
│ ...         │    │ user_id (FK)│    │ user_id (FK)│
└─────────────┘    │ signal_id (FK)│  │ direction   │
                   │ direction   │    │ volume      │
                   │ volume      │    │ open_price  │
                   │ open_price  │    │ current_price│
                   │ close_price │    │ stop_loss   │
                   │ stop_loss   │    │ take_profit │
                   │ take_profit │    │ open_time   │
                   │ open_time   │    │ unrealized_pnl│
                   │ close_time  │    │ swap        │
                   │ profit_loss │    │ commission  │
                   │ swap        │    │ is_active   │
                   │ commission  │    │ mt_ticket   │
                   │ status      │    │ position_data│
                   │ mt_ticket   │    └─────────────┘
                   │ trade_data  │
                   └─────────────┘
```

#### Risk Management
```
┌─────────────┐    ┌─────────────┐
│   users     │    │ risk_events │
├─────────────┤    ├─────────────┤
│ id (PK)     │◄───│ user_id (FK)│
│ username    │    │ event_id    │
│ email       │    │ event_type  │
│ ...         │    │ severity    │
└─────────────┘    │ description │
                   │ trade_id (FK)│
                   │ position_id (FK)│
                   │ threshold_value│
                   │ actual_value │
                   │ is_resolved  │
                   │ resolved_at  │
                   │ resolution_notes│
                   │ event_data   │
                   └─────────────┘
```

#### Journaling and Alerts
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   users     │    │  journals   │    │   alerts    │
├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │◄───│ user_id (FK)│    │ user_id (FK)│
│ username    │    │ trade_id (FK)│   │ trade_id (FK)│
│ ...         │    │ signal_id (FK)│  │ signal_id (FK)│
└─────────────┘    │ entry_type  │    │ alert_type  │
                   │ title       │    │ severity    │
                   │ content     │    │ title       │
                   │ analysis_data│   │ message     │
                   │ sentiment_score│  │ is_read     │
                   │ confidence_score│ │ read_at     │
                   │ tags        │    │ delivery_method│
                   │ is_public   │    │ delivery_status│
                   │ journal_data│    │ delivery_data│
                   └─────────────┘    │ alert_data  │
                                      └─────────────┘
```

#### System Monitoring
```
┌─────────────┐    ┌─────────────┐
│   users     │    │   audits    │
├─────────────┤    ├─────────────┤
│ id (PK)     │◄───│ user_id (FK)│
│ username    │    │ audit_id    │
│ ...         │    │ action      │
└─────────────┘    │ resource_type│
                   │ resource_id │
                   │ ip_address  │
                   │ user_agent  │
                   │ request_data│
                   │ response_data│
                   │ status      │
                   │ error_message│
                   │ audit_data  │
                   └─────────────┘
```

## Database Relationships

### One-to-Many Relationships
- **User → API Keys**: One user can have multiple API keys
- **User → Sessions**: One user can have multiple active sessions
- **User → Trades**: One user can have multiple trades
- **User → Journals**: One user can have multiple journal entries
- **Instrument → Signals**: One instrument can have multiple signals
- **Instrument → Orders**: One instrument can have multiple orders
- **Signal → Orders**: One signal can generate multiple orders
- **Order → Fills**: One order can have multiple fills
- **Trade → Positions**: One trade can have multiple positions

### Many-to-Many Relationships
- **Users ↔ Instruments**: Users can trade multiple instruments
- **Signals ↔ Risk Events**: Signals can trigger multiple risk events

## Database Configuration

### SQLite Settings
```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA cache_size = -64000;  -- 64MB
PRAGMA temp_store = MEMORY;
```

### Performance Optimizations
- **Indexes**: On frequently queried fields
- **WAL Mode**: Better concurrency for multiple readers
- **Memory Cache**: 64MB cache for better performance
- **Memory Temp Tables**: Temporary tables stored in memory

## Data Retention Policies

### Trading Data
- **Signals**: 90 days
- **Orders**: 1 year
- **Trades**: 7 years (regulatory requirement)
- **Positions**: 1 year
- **Fills**: 1 year

### System Data
- **Audit Logs**: 1 year
- **Risk Events**: 180 days
- **Journals**: 365 days
- **Alerts**: 90 days

### User Data
- **User Accounts**: 5 years
- **Sessions**: 90 days
- **API Keys**: 90 days

## Backup and Recovery

### Backup Strategy
- **Daily Incremental**: Automated daily backups
- **Weekly Full**: Complete database backup
- **Monthly Archive**: Long-term storage

### Recovery Procedures
- **Point-in-Time Recovery**: Using WAL files
- **Full Restore**: From backup files
- **Data Validation**: Integrity checks after recovery

## Migration Management

### Alembic Migrations
- **Version Control**: Database schema versioning
- **Rollback Support**: Ability to revert changes
- **Data Migration**: Safe data transformation
- **Environment Support**: Different configs for dev/prod

### Migration Process
1. **Development**: Create migration files
2. **Testing**: Validate on test database
3. **Staging**: Test on staging environment
4. **Production**: Deploy with rollback plan

## Security Considerations

### Data Protection
- **Encryption**: Sensitive data encrypted at rest
- **Access Control**: Role-based permissions
- **Audit Logging**: All changes tracked
- **Data Masking**: PII protection in logs

### SQL Injection Prevention
- **Parameterized Queries**: Using SQLAlchemy ORM
- **Input Validation**: Schema validation with Pydantic
- **Escape Functions**: Proper data escaping
- **Least Privilege**: Minimal database permissions