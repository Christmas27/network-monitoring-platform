// Simple Network Monitoring Dashboard JS
class NetworkDashboard {
    constructor() {
        this.devicesGrid = document.getElementById('devices-grid');
        this.init();
    }

    async init() {
        await this.loadDevices();
        // Auto-refresh every 30 seconds
        setInterval(() => this.loadDevices(), 30000);
    }

    async loadDevices() {
        try {
            this.showLoading();
            const response = await fetch('/api/devices');
            const data = await response.json();
            this.renderDevices(data.devices);
        } catch (error) {
            console.error('Error loading devices:', error);
            this.showError('Failed to load devices');
        }
    }

    showLoading() {
        this.devicesGrid.innerHTML = '<div class="loading">Loading devices...</div>';
    }

    showError(message) {
        this.devicesGrid.innerHTML = `<div class="loading">${message}</div>`;
    }

    renderDevices(devices) {
        if (devices.length === 0) {
            this.devicesGrid.innerHTML = '<div class="loading">No devices found</div>';
            return;
        }

        const deviceCards = devices.map(device => this.createDeviceCard(device)).join('');
        this.devicesGrid.innerHTML = deviceCards;
    }

    createDeviceCard(device) {
        const statusClass = device.status.toLowerCase() === 'up' ? 'status-up' : 'status-down';
        
        return `
            <div class="device-card">
                <div class="device-name">${device.name}</div>
                <div class="device-ip">${device.ip}</div>
                <div class="device-status ${statusClass}">${device.status}</div>
            </div>
        `;
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new NetworkDashboard();
});