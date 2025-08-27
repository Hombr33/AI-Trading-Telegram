/**
 * Admin Dashboard JavaScript
 * Provides interactive functionality for the admin dashboard.
 */

class AdminDashboard {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeTooltips();
        this.setupAutoRefresh();
        this.initializeCharts();
    }

    setupEventListeners() {
        // Global error handler
        window.addEventListener('error', (e) => {
            console.error('JavaScript error:', e.error);
            this.showToast('An unexpected error occurred', 'error');
        });

        // Handle form submissions
        document.addEventListener('submit', (e) => {
            if (e.target.matches('form[data-ajax="true"]')) {
                e.preventDefault();
                this.handleAjaxForm(e.target);
            }
        });

        // Handle button clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action]')) {
                e.preventDefault();
                this.handleAction(e.target);
            }
        });
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    setupAutoRefresh() {
        // Auto-refresh functionality for certain pages
        const autoRefreshInterval = 30000; // 30 seconds

        if (document.querySelector('[data-auto-refresh]')) {
            setInterval(() => {
                this.refreshData();
            }, autoRefreshInterval);
        }
    }

    initializeCharts() {
        // Initialize any charts on the page
        const chartCanvases = document.querySelectorAll('canvas[data-chart-type]');
        chartCanvases.forEach(canvas => {
            this.initializeChart(canvas);
        });
    }

    initializeChart(canvas) {
        const chartType = canvas.dataset.chartType;
        const chartData = JSON.parse(canvas.dataset.chartData || '{}');

        // Chart.js initialization would go here
        // This is a placeholder for chart initialization
    }

    async handleAjaxForm(form) {
        const formData = new FormData(form);
        const action = form.action || window.location.href;

        try {
            this.showLoading(form);

            const response = await fetch(action, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(result.message || 'Operation completed successfully', 'success');
                if (result.redirect) {
                    setTimeout(() => window.location.href = result.redirect, 1000);
                } else {
                    setTimeout(() => location.reload(), 1000);
                }
            } else {
                this.showToast(result.error || 'Operation failed', 'error');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            this.showToast('Network error occurred', 'error');
        } finally {
            this.hideLoading(form);
        }
    }

    handleAction(button) {
        const action = button.dataset.action;
        const params = JSON.parse(button.dataset.params || '{}');

        switch (action) {
            case 'delete':
                this.confirmDelete(params);
                break;
            case 'toggle':
                this.toggleStatus(params);
                break;
            case 'refresh':
                this.refreshData();
                break;
            default:
                console.warn('Unknown action:', action);
        }
    }

    async confirmDelete(params) {
        const message = params.message || 'Are you sure you want to delete this item?';
        if (!confirm(message)) {
            return;
        }

        try {
            const response = await fetch(params.url, {
                method: 'DELETE',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(result.message || 'Item deleted successfully', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showToast(result.error || 'Delete operation failed', 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showToast('Delete operation failed', 'error');
        }
    }

    async toggleStatus(params) {
        try {
            const response = await fetch(params.url, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ status: params.newStatus })
            });

            const result = await response.json();

            if (result.success) {
                this.showToast(result.message || 'Status updated successfully', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                this.showToast(result.error || 'Status update failed', 'error');
            }
        } catch (error) {
            console.error('Status toggle error:', error);
            this.showToast('Status update failed', 'error');
        }
    }

    async refreshData() {
        try {
            const response = await fetch(window.location.href, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                const html = await response.text();
                // Update specific parts of the page instead of full reload
                this.updatePageContent(html);
                this.showToast('Data refreshed successfully', 'success');
            } else {
                throw new Error('Refresh failed');
            }
        } catch (error) {
            console.error('Refresh error:', error);
            this.showToast('Failed to refresh data', 'error');
        }
    }

    updatePageContent(html) {
        // Parse the new HTML and update specific sections
        const parser = new DOMParser();
        const newDoc = parser.parseFromString(html, 'text/html');

        // Update statistics cards
        const statsCards = newDoc.querySelectorAll('.stats-card');
        statsCards.forEach((newCard, index) => {
            const oldCard = document.querySelectorAll('.stats-card')[index];
            if (oldCard) {
                oldCard.innerHTML = newCard.innerHTML;
            }
        });
    }

    showLoading(element) {
        element.style.opacity = '0.6';
        element.style.pointerEvents = 'none';

        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-overlay';
        loadingIndicator.innerHTML = `
            <div class="d-flex justify-content-center align-items-center h-100">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;

        element.style.position = 'relative';
        element.appendChild(loadingIndicator);
    }

    hideLoading(element) {
        element.style.opacity = '1';
        element.style.pointerEvents = 'auto';

        const loadingIndicator = element.querySelector('.loading-overlay');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }

    showToast(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            // Create toast container if it doesn't exist
            const container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');

        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        document.querySelector('.toast-container').appendChild(toast);

        // Initialize and show the toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Utility methods
    formatDate(date) {
        return new Date(date).toLocaleString();
    }

    formatNumber(number) {
        return new Intl.NumberFormat().format(number);
    }

    formatCurrency(amount, currency = 'USD') {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
}

// DataTables integration
class DataTableManager {
    constructor() {
        this.tables = new Map();
        this.init();
    }

    init() {
        // Initialize DataTables for tables with data-table attribute
        document.querySelectorAll('table[data-table]').forEach(table => {
            this.initializeTable(table);
        });
    }

    initializeTable(table) {
        const tableId = table.id || `table_${Date.now()}`;
        table.id = tableId;

        const config = JSON.parse(table.dataset.tableConfig || '{}');

        const defaultConfig = {
            pageLength: 25,
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
            responsive: true,
            order: [[0, 'desc']],
            language: {
                search: "Search:",
                lengthMenu: "Show _MENU_ entries",
                info: "Showing _START_ to _END_ of _TOTAL_ entries",
                paginate: {
                    first: "First",
                    last: "Last",
                    next: "Next",
                    previous: "Previous"
                }
            }
        };

        const finalConfig = { ...defaultConfig, ...config };

        this.tables.set(tableId, $(table).DataTable(finalConfig));
    }

    refresh(tableId) {
        const dataTable = this.tables.get(tableId);
        if (dataTable) {
            dataTable.ajax.reload();
        }
    }

    destroy(tableId) {
        const dataTable = this.tables.get(tableId);
        if (dataTable) {
            dataTable.destroy();
            this.tables.delete(tableId);
        }
    }
}

// Real-time updates
class RealTimeManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 5000;
    }

    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/admin/ws`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                adminDashboard.showToast('Real-time connection established', 'success');
            };

            this.ws.onmessage = (event) => {
                this.handleMessage(JSON.parse(event.data));
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                this.handleDisconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };

        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
        }
    }

    handleMessage(data) {
        switch (data.type) {
            case 'stats_update':
                this.updateStats(data.payload);
                break;
            case 'user_activity':
                this.updateUserActivity(data.payload);
                break;
            case 'system_alert':
                this.showSystemAlert(data.payload);
                break;
            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    handleDisconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect();
            }, this.reconnectInterval);
        } else {
            adminDashboard.showToast('Real-time connection lost. Please refresh the page.', 'warning');
        }
    }

    updateStats(stats) {
        // Update statistics in real-time
        Object.keys(stats).forEach(key => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) {
                element.textContent = adminDashboard.formatNumber(stats[key]);
            }
        });
    }

    updateUserActivity(activity) {
        // Update user activity indicators
        const activityElement = document.querySelector(`[data-user-activity="${activity.user_id}"]`);
        if (activityElement) {
            activityElement.className = `badge bg-${activity.status === 'online' ? 'success' : 'secondary'}`;
            activityElement.textContent = activity.status;
        }
    }

    showSystemAlert(alert) {
        adminDashboard.showToast(alert.message, alert.severity);
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin dashboard
    window.adminDashboard = new AdminDashboard();

    // Initialize DataTable manager
    window.dataTableManager = new DataTableManager();

    // Initialize real-time manager if WebSocket is supported
    if ('WebSocket' in window) {
        window.realTimeManager = new RealTimeManager();
        window.realTimeManager.connect();
    }

    // Add loading class to body
    document.body.classList.add('fade-in');
});

// Export for global access
window.AdminDashboard = AdminDashboard;
window.DataTableManager = DataTableManager;
window.RealTimeManager = RealTimeManager;