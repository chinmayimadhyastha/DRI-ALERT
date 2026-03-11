// Real-Time Admin Dashboard Manager
class AdminDashboard {
    constructor() {
        this.refreshInterval = null;
        this.detections = [];
        this.users = [];
        this.stats = {};
    }

    // Load complete dashboard data
    async loadDashboard() {
        console.log('📊 Loading admin dashboard...');
        try {
            await Promise.all([
                this.loadStats(),
                this.loadDetections(),
                this.loadUsers()
            ]);
            await this.renderDashboard();
            console.log('📊 Dashboard rendered to DOM');
            console.log('✅ Dashboard loaded successfully');
        } catch (error) {
            console.error('❌ Dashboard load error:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    // Get auth token from session
    getAuthToken() {
        const session = localStorage.getItem('driAlertadminsession');
        if (session) {
            try {
                const data = JSON.parse(session);
                return data.token;
            } catch (e) {
                console.error('Session parse error:', e);
            }
        }
        return null;
    }

    // Load analytics stats
    async loadStats() {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('No admin token found');
        }

        const response = await fetch('http://localhost:5000/api/admin/analytics', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            this.stats = await response.json();
            console.log('📈 Stats loaded:', this.stats);
        } else {
            throw new Error('Failed to load stats');
        }
    }

    // Load all detections
    async loadDetections() {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('No admin token found');
        }

        const response = await fetch('http://localhost:5000/api/admin/logs?limit=100', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            this.detections = data.logs || [];
            console.log(`🔍 Loaded ${this.detections.length} detections`);
        } else {
            throw new Error('Failed to load detections');
        }
    }

    // Load all users
    async loadUsers() {
        const token = this.getAuthToken();
        if (!token) {
            throw new Error('No admin token found');
        }

        const response = await fetch('http://localhost:5000/api/admin/users', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            this.users = data.users || [];
            console.log(`👥 Loaded ${this.users.length} users`);
        } else {
            throw new Error('Failed to load users');
        }
    }

    // Render complete dashboard
    renderDashboard() {
        console.log('🎨 Rendering dashboard with data...');
        this.renderStats();
        this.renderRecentDetections();
        this.renderUsersTable();
        this.renderCharts();
    }

    // Render stats cards
    renderStats() {
        const statsContainer = document.getElementById('dashboard-stats');
        if (!statsContainer) return;

        const html = `
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-info">
                    <h3>${this.stats.total_users || 0}</h3>
                    <p>Total Users</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🚨</div>
                <div class="stat-info">
                    <h3>${this.stats.total_detections || 0}</h3>
                    <p>Total Detections</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📊</div>
                <div class="stat-info">
                    <h3>${this.stats.recent_activity || 0}</h3>
                    <p>This Week</p>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">⚠️</div>
                <div class="stat-info">
                    <h3>${this.stats.status_counts?.High || 0}</h3>
                    <p>High Risk Alerts</p>
                </div>
            </div>
        `;

        statsContainer.innerHTML = html;
    }

// admin-dashboard.js - renderRecentDetections() method

renderRecentDetections() {
    // ✅ FIX: Target the first .data-table (Recent Detections)
    const container = document.querySelector('.table-container');
    const tableBody = container ? container.querySelector('table.data-table tbody') : null;
    
    if (!tableBody) {
        console.error('❌ Detection table tbody not found');
        return;
    }

    if (!this.detections || this.detections.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: #888;">No detections recorded yet</td></tr>';
        console.log('ℹ️ No detections to render');
        return;
    }

    console.log(`🔄 Rendering ${this.detections.length} detections`);

    const html = this.detections.slice(0, 10).map(detection => {
        // ✅ FIX: Access nested detection_data object
        const detectionData = detection.detection_data || {};
        const sessionData = detection.session_data || {};
        
        const ear = parseFloat(detectionData.ear) || 0;
        const mar = parseFloat(detectionData.mar) || 0;
        const riskLevel = detectionData.risk_level || 'Unknown';
        const alertTriggered = detectionData.alert_triggered ? 'YES' : 'NO';
        
        // Format timestamp
        let timestamp = 'N/A';
        if (detection.timestamp) {
            try {
                const date = new Date(detection.timestamp);
                timestamp = date.toLocaleString('en-IN', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (e) {
                timestamp = String(detection.timestamp).substring(0, 19);
            }
        }

        // Risk level badge styling
        const badgeClass = {
            'Low': 'badge-success',
            'Medium': 'badge-warning',
            'High': 'badge-danger',
            'Critical': 'badge-danger'
        }[riskLevel] || 'badge-secondary';

        return `
            <tr>
                <td style="padding: 10px;">${detection.user_email || 'Unknown'}</td>
                <td style="padding: 10px;">${ear.toFixed(3)}</td>
                <td style="padding: 10px;">${mar.toFixed(3)}</td>
                <td style="padding: 10px;"><span class="badge ${badgeClass}">${riskLevel}</span></td>
                <td style="padding: 10px;">${alertTriggered}</td>
                <td style="padding: 10px;">${timestamp}</td>
                <td style="padding: 10px;">
                    <button class="btn btn-sm btn-info" onclick="alert('Details: ${detection.id || 'N/A'}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    tableBody.innerHTML = html;
    console.log('✅ Recent detections rendered successfully');
}

    // Render users table
    renderUsersTable() {
        const tableBody = document.getElementById('users-table-body');
        if (!tableBody) return;

        if (this.users.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" style="text-align:center;">No users found</td></tr>';
            return;
        }

        const html = this.users.map(user => {
            const createdAt = user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A';
            const statusClass = user.is_active ? 'success' : 'danger';
            
            return `
                <tr>
                    <td>${user.email}</td>
                    <td><span class="badge badge-${user.role === 'admin' ? 'warning' : 'info'}">${user.role}</span></td>
                    <td><span class="badge badge-${statusClass}">${user.is_active ? 'Active' : 'Inactive'}</span></td>
                    <td>${createdAt}</td>
                </tr>
            `;
        }).join('');

        tableBody.innerHTML = html;
    }

    // Render charts (risk distribution)
    renderCharts() {
        const chartContainer = document.getElementById('risk-chart');
        if (!chartContainer) return;

        const statusCounts = this.stats.status_counts || {};
        const total = Object.values(statusCounts).reduce((a, b) => a + b, 0);

        const html = `
            <div class="chart-bars">
                ${Object.entries(statusCounts).map(([risk, count]) => {
                    const percentage = total > 0 ? (count / total * 100).toFixed(1) : 0;
                    const color = this.getRiskColor(risk);
                    return `
                        <div class="chart-bar-item">
                            <div class="chart-bar-label">
                                <span>${risk}</span>
                                <span class="count">${count}</span>
                            </div>
                            <div class="chart-bar-bg">
                                <div class="chart-bar-fill" style="width: ${percentage}%; background: ${color};"></div>
                            </div>
                            <div class="chart-bar-percentage">${percentage}%</div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        chartContainer.innerHTML = html;
    }

    // Helper: Get risk badge class
    getRiskClass(risk) {
        const map = {
            'Low': 'success',
            'Medium': 'warning',
            'High': 'danger',
            'Critical': 'danger'
        };
        return map[risk] || 'secondary';
    }

    // Helper: Get risk color
    getRiskColor(risk) {
        const map = {
            'Low': '#10b981',
            'Medium': '#f59e0b',
            'High': '#ef4444',
            'Critical': '#dc2626'
        };
        return map[risk] || '#6b7280';
    }

    // View detailed detection
    viewDetection(id) {
        const detection = this.detections.find(d => d.id === id);
        if (!detection) return;

        const modal = document.getElementById('detection-modal');
        if (!modal) return;

        const data = detection.detection_data || {};
        const session = detection.session_data || {};

        const html = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Detection Details</h2>
                    <button onclick="adminDashboard.closeModal()" class="close-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <p><strong>User:</strong> ${detection.user_email}</p>
                    <p><strong>EAR:</strong> ${(data.eye_aspect_ratio || 0).toFixed(3)}</p>
                    <p><strong>MAR:</strong> ${(data.mouth_aspect_ratio || 0).toFixed(3)}</p>
                    <p><strong>Risk Level:</strong> <span class="badge badge-${this.getRiskClass(data.risk_level)}">${data.risk_level}</span></p>
                    <p><strong>Alert Triggered:</strong> ${data.alert_triggered ? 'Yes' : 'No'}</p>
                    <p><strong>Session Duration:</strong> ${session.session_duration || 0}s</p>
                    <p><strong>Total Detections:</strong> ${session.total_detections || 0}</p>
                    <p><strong>Timestamp:</strong> ${detection.timestamp ? new Date(detection.timestamp).toLocaleString() : 'N/A'}</p>
                </div>
            </div>
        `;

        modal.innerHTML = html;
        modal.style.display = 'block';
    }

    // Close modal
    closeModal() {
        const modal = document.getElementById('detection-modal');
        if (modal) modal.style.display = 'none';
    }

    // Show error message
    showError(message) {
        const container = document.getElementById('dashboard-container');
        if (container) {
            container.innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Error</h3>
                    <p>${message}</p>
                    <button onclick="adminDashboard.loadDashboard()" class="btn-primary">Retry</button>
                </div>
            `;
        }
    }

    // Start auto-refresh
    startAutoRefresh(interval = 30000) {
        console.log(`🔄 Auto-refresh enabled (${interval/1000}s)`);
        this.stopAutoRefresh();
        this.refreshInterval = setInterval(() => {
            console.log('🔄 Auto-refreshing dashboard...');
            this.loadDashboard();
        }, interval);
    }

    // Stop auto-refresh
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    // Export data as CSV
    exportDetections() {
        if (this.detections.length === 0) {
            alert('No detections to export');
            return;
        }

        const csv = [
            ['User Email', 'EAR', 'MAR', 'Risk Level', 'Alert', 'Timestamp'].join(','),
            ...this.detections.map(d => {
                const data = d.detection_data || {};
                return [
                    d.user_email,
                    data.eye_aspect_ratio || 0,
                    data.mouth_aspect_ratio || 0,
                    data.risk_level || 'Unknown',
                    data.alert_triggered ? 'Yes' : 'No',
                    d.timestamp || ''
                ].join(',');
            })
        ].join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `detections-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Initialize global instance
window.adminDashboard = new AdminDashboard();
