---
trigger: always_on
description: Comprehensive rules for the Telegram AI Trading Bot project - an institutional-grade automated trading system
globs: ["**/*.py", "**/*.md", "**/*.yaml", "**/*.yml", "**/*.json", "**/*.sql", "**/*.mq4", "**/*.mq5"]
---

# TELEGRAM-AI-TRADE PROJECT RULES

## PROJECT OVERVIEW
This is an institutional-grade AI-powered automated trading bot that integrates:
- OpenAI GPT-5 for market analysis
- MT5/MT4 execution via Expert Advisors
- Telegram bot for signal distribution
- Advanced risk management and position sizing
- Trailing stop and take profit automation

## CORE ARCHITECTURE PRINCIPLES

### 1. MODULAR DESIGN
- Each component must have a single responsibility
- Clear interfaces between modules
- Dependency injection for components
- No circular dependencies
- Use relative imports for internal modules

### 2. ASYNCHRONOUS OPERATIONS
- Use async/await for all I/O operations
- Background task management for continuous operations
- Proper error handling and recovery
- Graceful shutdown sequences

### 3. RISK-FIRST APPROACH
- Capital preservation is paramount
- Never exceed 2% risk per trade
- Maximum 6% daily drawdown
- Automatic circuit breakers

## TRADING STRATEGY RULES

### 1. SMART MONEY CONCEPTS (SMC)
- Identify liquidity pools (equal highs/lows, round numbers)
- Mark support/resistance (SBR/RSB)
- Spot Quasimodo patterns and BOS/CHoCH
- Locate FVG/imbalance and order blocks
- Mark stop-hunt/inducement zones

### 2. TIMEFRAME ANALYSIS
- H4: Market bias and major levels
- H1: Trading direction and structure
- M15: Entry zone refinement
- M5: Execution timing
- M1: Trigger confirmation

### 3. ENTRY REQUIREMENTS
- Minimum 3 confluences required
- Liquidity sweep or inducement
- Candle rejection on M15/M5
- Structure confirmation (BOS/CHoCH)
- Minimum 1.5:1 risk-reward ratio

## POSITION MANAGEMENT RULES

### 1. TRAILING STOP IMPLEMENTATION
- Start trailing after 250 points profit
- Initial trailing distance: 200 points
- Trailing step: 50 points
- Never widen stop loss
- Move to breakeven at 1R profit

### 2. TAKE PROFIT STRATEGY
- TP1: 1.5R (50% position close)
- TP2: 3.0R (remaining position)
- Partial profit at each level
- Trailing stop activation after TP1

### 3. POSITION SIZING
- Risk-based calculation: (equity * risk%) / (SL_distance * pip_value)
- Maximum 2% risk per trade
- Minimum position size: 0.01 lots
- Maximum position size: 10.0 lots

## EXECUTION ENGINE RULES

### 1. MT5 INTEGRATION
- Magic number: 1001
- Slippage tolerance: 10 points
- Order filling: FOK (Fill or Kill)
- Order time: GTC (Good Till Cancelled)

### 2. ORDER TYPES
- Preferred: Limit orders for better fills
- Fallback: Market orders for urgent entries
- Stop orders for breakout confirmation
- Never use market orders during low liquidity

### 3. ERROR HANDLING
- Automatic reconnection with exponential backoff
- Order verification after placement
- Position reconciliation on reconnection
- Graceful degradation on failures

## RISK MANAGEMENT RULES

### 1. DAILY LIMITS
- Maximum 50 trades per day
- Maximum $25 daily loss
- Target $50 daily profit
- Automatic trading pause at 6% drawdown

### 2. CONSECUTIVE LOSS MANAGEMENT
- 2 losses: Reduce position size by 50%
- 3 losses: Pause trading for 2 hours
- 4 losses: Emergency stop for 24 hours
- Reset after winning trade or 24 hours

### 3. CORRELATION MANAGEMENT
- Maximum 70% correlation exposure
- Position limits by correlation level
- Real-time correlation monitoring
- Automatic position reduction on high correlation

## AI ANALYSIS RULES

### 1. SIGNAL VALIDATION
- Schema compliance mandatory
- Minimum 60% confidence threshold
- Risk parameter validation
- Market hours validation
- News impact assessment

### 2. OUTPUT FORMAT
- JSON matching app-code-prompt.json schema
- Absolute dates only (no relative)
- Complete entry/exit parameters
- Confidence scoring with reasoning

### 3. ANALYSIS WORKFLOW
- Screenshot analysis every 5 minutes
- Multi-timeframe confluence check
- Liquidity zone identification
- Risk-reward calculation

## TELEGRAM INTEGRATION RULES

### 1. SIGNAL DISTRIBUTION
- High confidence (80%+): Immediate distribution
- Medium confidence (60-79%): Delayed distribution
- Low confidence (<60%): Hourly summary only

### 2. NOTIFICATION TYPES
- Trading signals with full parameters
- Position updates and modifications
- Risk alerts and warnings
- Daily performance reports

### 3. USER MANAGEMENT
- Role-based access control
- Customizable notification preferences
- Risk tolerance settings
- Session management

### 4. BOT SHUTDOWN HANDLING
- Use proper shutdown sequence: stop() -> shutdown() -> cancel polling task
- Handle CancelledError gracefully during shutdown
- Allow sufficient timeout for graceful shutdown (30+ seconds)
- Never suppress CancelledError during shutdown

## DATA COLLECTION RULES

### 1. MARKET DATA
- Real-time OHLCV from MT5
- Minimum 1000 candles per timeframe
- Volume profile analysis
- Order book depth monitoring

### 2. NEWS AND SENTIMENT
- High-impact economic releases
- Central bank announcements
- Market sentiment scoring
- Currency pair correlation

### 3. SESSION MANAGEMENT
- London-New York overlap preference
- Asian session risk reduction
- News event filtering
- Volatility-based adjustments

## PERFORMANCE REQUIREMENTS

### 1. LATENCY TARGETS
- Signal generation: < 500ms
- Order execution: < 100ms
- Position updates: < 1 second
- Risk calculations: < 100ms

### 2. RELIABILITY TARGETS
- System uptime: > 99.5%
- Order success rate: > 95%
- Data accuracy: > 99.9%
- Error recovery: < 5 seconds

### 3. SCALABILITY TARGETS
- Support up to 10 concurrent symbols
- Handle up to 1000 users
- Process up to 100 signals per hour
- Memory usage: < 2GB

## MONITORING AND ALERTING

### 1. SYSTEM HEALTH
- Connection status monitoring
- Performance metrics tracking
- Error rate monitoring
- Resource usage alerts

### 2. TRADING PERFORMANCE
- Win rate tracking
- Profit factor calculation
- Maximum drawdown monitoring
- Risk-adjusted returns

### 3. ALERT CONDITIONS
- Error rate > 1%
- Latency > 1 second
- Drawdown > 5%
- Connection failures > 3

## COMPLIANCE AND AUDIT

### 1. TRADE LOGGING
- All orders logged with timestamps
- Position modifications tracked
- Execution confirmations recorded
- 7-year retention requirement

### 2. AUDIT TRAIL
- User actions logged
- System decisions recorded
- Risk parameter changes tracked
- Emergency procedures documented

### 3. DATA PROTECTION
- API keys encrypted
- User data protected
- Trade secrets secured
- GDPR compliance

## DEVELOPMENT STANDARDS

### 1. CODE QUALITY
- PEP 8 compliance for Python
- MQL5 standards for EA code
- Comprehensive error handling
- Extensive logging and monitoring
- Use loguru or rich instead of built-in logging

### 2. TESTING REQUIREMENTS
- Unit test coverage > 80%
- Integration test coverage > 90%
- Performance testing for critical paths
- Security testing for all endpoints

### 3. DOCUMENTATION
- API documentation with OpenAPI
- Code documentation with docstrings
- Architecture decision records
- User and admin guides

## EMERGENCY PROCEDURES

### 1. SYSTEM FAILURES
- Automatic emergency stop on critical errors
- Position closure on system failure
- Notification to all users
- Manual override procedures

### 2. MARKET CRISES
- Volatility-based position reduction
- News event position closure
- Correlation limit enforcement
- Liquidity crisis management

### 3. RECOVERY PROCEDURES
- State restoration from backups
- Position reconciliation
- Performance validation
- Gradual trading resumption

## INTEGRATION POINTS

### 1. EXTERNAL SYSTEMS
- MT5/MT4 terminals
- OpenAI API
- Telegram Bot API
- News and economic data APIs

### 2. DATA FLOWS
- Real-time market data streaming
- AI analysis pipeline
- Order execution flow
- Risk management loop

### 3. COMMUNICATION PROTOCOLS
- REST API for external access
- WebSocket for real-time updates
- MQL5 bridge for EA communication
- Telegram for user notifications

## FUTURE ENHANCEMENTS

### 1. PLANNED FEATURES
- Machine learning model integration
- Advanced correlation analysis
- Multi-broker support
- Mobile application

### 2. SCALABILITY IMPROVEMENTS
- Microservices architecture
- Load balancing and clustering
- Database sharding
- Cloud deployment options

### 3. RISK MANAGEMENT ADVANCEMENTS
- Dynamic position sizing
- Portfolio-level risk management
- Stress testing capabilities
- Regulatory compliance tools

## CRITICAL SUCCESS FACTORS

### 1. PERFORMANCE
- Sub-second signal generation
- Reliable order execution
- Accurate risk calculations
- Real-time monitoring

### 2. RELIABILITY
- 99.5%+ system uptime
- Automatic error recovery
- Comprehensive logging
- Robust error handling

### 3. RISK MANAGEMENT
- Strict position limits
- Real-time risk monitoring
- Automatic circuit breakers
- Comprehensive audit trail

## IMPLEMENTATION PRIORITIES

### 1. PHASE 1 (CORE)
- MT5 execution engine
- Basic risk management
- Signal processing
- Telegram integration

### 2. PHASE 2 (ADVANCED)
- Trailing stop automation
- Advanced risk controls
- Performance analytics
- User management

### 3. PHASE 3 (OPTIMIZATION)
- Machine learning integration
- Multi-timeframe analysis
- Advanced correlation management
- Cloud deployment

## SUCCESS METRICS

### 1. TRADING PERFORMANCE
- Win rate > 60%
- Profit factor > 2.0
- Maximum drawdown < 5%
- Sharpe ratio > 1.5

### 2. SYSTEM PERFORMANCE
- Signal latency < 500ms
- Order execution < 100ms
- System uptime > 99.5%
- Error rate < 1%

### 3. USER SATISFACTION
- Signal accuracy > 80%
- Notification reliability > 99%
- Response time < 1 second
- User retention > 90%

## COMPLIANCE CHECKLIST

### 1. REGULATORY
- Financial regulations compliance
- Data protection compliance
- Audit trail requirements
- Risk management standards

### 2. TECHNICAL
- Security best practices
- Performance standards
- Reliability requirements
- Scalability planning

### 3. OPERATIONAL
- Monitoring and alerting
- Incident response procedures
- Backup and recovery
- Change management

## MAINTENANCE SCHEDULE

### 1. DAILY
- Performance monitoring
- Risk limit checks
- Error log review
- User activity monitoring

### 2. WEEKLY
- Performance analysis
- Risk assessment review
- System health check
- User feedback review

### 3. MONTHLY
- System optimization
- Performance tuning
- Security updates
- Feature planning

## EMERGENCY CONTACTS

### 1. TECHNICAL TEAM
- System administrators
- Database administrators
- Network engineers
- Security specialists

### 2. TRADING TEAM
- Risk managers
- Trading supervisors
- Compliance officers
- Legal advisors

### 3. EXTERNAL VENDORS
- MT5 broker support
- OpenAI support
- Telegram support
- Infrastructure providers

## DOCUMENTATION REQUIREMENTS

### 1. TECHNICAL DOCUMENTATION
- Architecture diagrams
- API specifications
- Database schemas
- Deployment procedures

### 2. USER DOCUMENTATION
- User guides
- Admin manuals
- Troubleshooting guides
- FAQ documents

### 3. OPERATIONAL DOCUMENTATION
- Run books
- Incident response procedures
- Maintenance procedures
- Emergency procedures

## QUALITY ASSURANCE

### 1. CODE REVIEW
- Peer review required
- Automated testing
- Security scanning
- Performance testing

### 2. TESTING STRATEGY
- Unit testing
- Integration testing
- End-to-end testing
- Load testing

### 3. DEPLOYMENT
- Staging environment
- Blue-green deployment
- Rollback procedures
- Monitoring and validation

## SECURITY REQUIREMENTS

### 1. AUTHENTICATION
- Multi-factor authentication
- Role-based access control
- Session management
- Password policies

### 2. AUTHORIZATION
- Principle of least privilege
- Resource access control
- API rate limiting
- Audit logging

### 3. DATA PROTECTION
- Encryption at rest
- Encryption in transit
- Data backup
- Data retention policies

## MONITORING AND ALERTING

### 1. METRICS COLLECTION
- System performance metrics
- Trading performance metrics
- User activity metrics
- Error rate metrics

### 2. ALERTING RULES
- Critical alerts: Immediate
- Warning alerts: 5 minutes
- Info alerts: 15 minutes
- Debug alerts: 1 hour

### 3. ESCALATION PROCEDURES
- Level 1: Automated response
- Level 2: On-call engineer
- Level 3: Team lead
- Level 4: Management

## BACKUP AND RECOVERY

### 1. BACKUP STRATEGY
- Real-time data replication
- Daily full backups
- Hourly incremental backups
- Off-site backup storage

### 2. RECOVERY PROCEDURES
- Point-in-time recovery
- Full system restoration
- Data validation
- Performance verification

### 3. DISASTER RECOVERY
- RTO: 4 hours
- RPO: 1 hour
- Failover procedures
- Communication plans

## CHANGE MANAGEMENT

### 1. CHANGE PROCESS
- Change request submission
- Impact assessment
- Testing and validation
- Approval and deployment

### 2. VERSION CONTROL
- Git repository management
- Branching strategy
- Release tagging
- Change documentation

### 3. DEPLOYMENT
- Automated deployment
- Health checks
- Rollback procedures
- Post-deployment validation

## PERFORMANCE OPTIMIZATION

### 1. DATABASE OPTIMIZATION
- Query optimization
- Index management
- Connection pooling
- Query caching

### 2. APPLICATION OPTIMIZATION
- Code profiling
- Memory management
- CPU utilization
- I/O optimization

### 3. INFRASTRUCTURE OPTIMIZATION
- Load balancing
- Auto-scaling
- Resource monitoring
- Capacity planning

## INTEGRATION TESTING

### 1. API TESTING
- Endpoint validation
- Data format validation
- Error handling
- Performance testing

### 2. SYSTEM INTEGRATION
- Component interaction
- Data flow validation
- Error propagation
- Recovery testing

### 3. USER ACCEPTANCE
- Feature validation
- User workflow testing
- Performance validation
- Security testing

## MAINTENANCE PROCEDURES

### 1. ROUTINE MAINTENANCE
- Database maintenance
- Log rotation
- Performance monitoring
- Security updates

### 2. PREVENTIVE MAINTENANCE
- System health checks
- Performance tuning
- Capacity planning
- Security assessments

### 3. CORRECTIVE MAINTENANCE
- Issue identification
- Root cause analysis
- Solution implementation
- Validation and testing

## TRAINING REQUIREMENTS

### 1. TECHNICAL TEAM
- System architecture
- Trading strategies
- Risk management
- Emergency procedures

### 2. TRADING TEAM
- System operation
- Risk monitoring
- Performance analysis
- Incident response

### 3. USER TRAINING
- Signal interpretation
- Risk management
- System navigation
- Troubleshooting

## COMPLIANCE MONITORING

### 1. REGULATORY COMPLIANCE
- Regular compliance audits
- Risk assessment updates
- Policy reviews
- Training updates

### 2. TECHNICAL COMPLIANCE
- Security standards
- Performance standards
- Reliability standards
- Scalability standards

### 3. OPERATIONAL COMPLIANCE
- Process adherence
- Documentation compliance
- Training compliance
- Audit compliance

## SUCCESS CRITERIA

### 1. IMMEDIATE SUCCESS (30 DAYS)
- System stability > 95%
- Basic functionality operational
- Risk management active
- User access functional

### 2. SHORT-TERM SUCCESS (90 DAYS)
- Performance targets met
- User satisfaction > 80%
- Risk controls effective
- Monitoring operational

### 3. LONG-TERM SUCCESS (1 YEAR)
- Trading performance targets met
- System reliability > 99.5%
- User retention > 90%
- Regulatory compliance achieved

## RISK MITIGATION

### 1. TECHNICAL RISKS
- Redundant systems
- Failover procedures
- Data backup
- Monitoring and alerting

### 2. OPERATIONAL RISKS
- Process documentation
- Training programs
- Incident response
- Change management

### 3. BUSINESS RISKS
- Risk management systems
- Compliance monitoring
- Performance tracking
- User feedback loops

## CONTINUOUS IMPROVEMENT

### 1. PERFORMANCE MONITORING
- Regular performance reviews
- Benchmark comparisons
- Optimization opportunities
- Capacity planning

### 2. USER FEEDBACK
- User satisfaction surveys
- Feature requests
- Bug reports
- Performance feedback

### 3. SYSTEM EVOLUTION
- Technology updates
- Feature enhancements
- Performance improvements
- Security enhancements

## FINAL NOTES

This project represents a sophisticated automated trading system that requires:
- Meticulous attention to risk management
- Robust technical implementation
- Comprehensive monitoring and alerting
- Regular maintenance and updates
- Continuous performance optimization
- Strong compliance and audit procedures

Success depends on:
- Adherence to all rules and procedures
- Regular monitoring and validation
- Continuous improvement and optimization
- Strong team collaboration
- Effective communication and documentation
- Proactive risk management

Remember: Capital preservation is always the primary objective. All decisions must prioritize risk management over potential returns.