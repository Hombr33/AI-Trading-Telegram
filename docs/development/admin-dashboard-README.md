# Admin Dashboard

A comprehensive web-based administrative interface for the AI Trading Bot multi-user system.

## Features

### 1. User Management
- View all registered users with filtering and search
- User details with platform connections and trading status
- User activation/deactivation
- Role management (User, Admin, Super Admin)
- Subscription management

### 2. System Monitoring
- Real-time system health status
- Performance metrics and resource usage
- Service status monitoring
- Platform connection monitoring
- System logs and alerts

### 3. Signal Monitoring
- Signal distribution statistics
- Real-time signal processing status
- User signal subscriptions
- Signal success rates and performance

### 4. Platform Management
- Platform connection overview
- Connection testing and management
- Platform-specific statistics
- Connection logs and troubleshooting

### 5. Configuration Management
- System-wide configuration settings
- User-specific configuration management
- Configuration templates (Conservative, Balanced, Aggressive)
- Backup and restore functionality

### 6. Audit Logs
- Comprehensive audit trail
- User activity monitoring
- Security event logging
- Log filtering and export

## Installation

The admin dashboard is automatically included when you run the main application. No additional installation is required.

## Usage

### Accessing the Admin Dashboard

1. Start the main application:
   ```bash
   python run.py
   ```

2. Navigate to the admin dashboard:
   ```
   http://localhost:8000/admin/?admin_id=YOUR_ADMIN_TELEGRAM_ID
   ```

   Replace `YOUR_ADMIN_TELEGRAM_ID` with your actual Telegram user ID that has admin privileges.

### Authentication

The admin dashboard uses a simple query parameter authentication system. In production, this should be replaced with proper session-based authentication.

### Navigation

The dashboard features a responsive sidebar navigation with the following sections:

- **Dashboard**: Overview of system statistics and health
- **User Management**: Comprehensive user administration
- **System Monitor**: Real-time system monitoring
- **Signal Monitor**: Signal processing and distribution monitoring
- **Platform Mgmt**: Platform connection management
- **Configuration**: System and user configuration management
- **Audit Logs**: Security and activity logging

## API Endpoints

The admin dashboard provides several AJAX endpoints for dynamic functionality:

### Statistics
- `GET /admin/api/stats/realtime` - Get real-time system statistics

### User Management
- `POST /admin/api/users/{telegram_id}/status` - Update user status

### System Control
- `POST /admin/api/system/emergency-stop` - Emergency stop all trading

## Security Considerations

### Current Implementation
- Simple query parameter authentication
- No session management
- Basic authorization checks

### Recommended Improvements
1. **Session Management**: Implement proper session-based authentication
2. **Role-Based Access Control**: Enhanced permission system
3. **Two-Factor Authentication**: Additional security layer
4. **Audit Logging**: Comprehensive security event logging
5. **Rate Limiting**: Prevent brute force attacks
6. **HTTPS Only**: Enforce secure connections

## Customization

### Styling
The dashboard uses custom CSS located in `static/css/admin.css`. You can modify this file to customize the appearance.

### Templates
Jinja2 templates are located in the `templates/` directory. You can modify these to change the UI layout and functionality.

### JavaScript
Custom JavaScript functionality is in `static/js/admin.js`. This handles dynamic features like real-time updates and AJAX requests.

## Development

### Adding New Pages
1. Create a new template in `templates/`
2. Add a route in `router.py`
3. Update the sidebar navigation in `base.html`

### Adding New API Endpoints
1. Add the endpoint to `router.py`
2. Implement the handler function
3. Update the frontend JavaScript if needed

### Extending Functionality
The dashboard is built with modularity in mind. You can easily extend it by:

1. Adding new service integrations
2. Implementing additional monitoring features
3. Creating custom widgets and charts
4. Adding new user management features

## Troubleshooting

### Common Issues

1. **Access Denied**: Ensure your Telegram ID has admin privileges
2. **Page Not Found**: Check that the admin router is properly included in the main app
3. **Static Files Not Loading**: Verify the static files are properly mounted
4. **Real-time Updates Not Working**: Check WebSocket connection and browser support

### Debug Mode
Enable debug mode in the main application to get detailed error messages and logging.

## Contributing

When contributing to the admin dashboard:

1. Follow the existing code structure and naming conventions
2. Add proper error handling and validation
3. Include comprehensive documentation
4. Test thoroughly across different browsers and devices
5. Ensure responsive design principles are maintained

## License

This admin dashboard is part of the AI Trading Bot project and follows the same license terms.
