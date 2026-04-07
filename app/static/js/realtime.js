// Real-time updates for dashboard
class NetworkMonitor {
    constructor() {
        this.updateInterval = 5000; // 5 seconds
        this.isRunning = false;
    }

    start() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        console.log('🔄 Starting real-time monitoring...');
        
        // Update immediately, then every 5 seconds
        this.updateDevices();
        this.intervalId = setInterval(() => this.updateDevices(), this.updateInterval);
        
        // Show status indicator
        this.showMonitoringStatus(true);
    }

    stop() {
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        console.log('⏸️ Stopped real-time monitoring');
        this.showMonitoringStatus(false);
    }

    async updateDevices() {
        try {
            const response = await fetch('/api/devices');
            const data = await response.json();
            
            // Update device cards with new data
            this.refreshDeviceCards(data.devices);
            
            // Update last refresh time
            this.updateTimestamp();
            
        } catch (error) {
            console.error('❌ Error updating devices:', error);
            this.showError('Connection lost. Retrying...');
        }
    }

    refreshDeviceCards(devices) {
        const devicesGrid = document.getElementById('devices-grid');
        if (!devicesGrid) return;

        // Store current scroll position
        const scrollPos = window.scrollY;
        
        // Update grid with new data
        devicesGrid.innerHTML = devices.map(createDeviceCard).join('');
        
        // Restore scroll position
        window.scrollTo(0, scrollPos);
    }

    updateTimestamp() {
        let timestamp = document.getElementById('last-update');
        if (!timestamp) {
            // Create timestamp element if it doesn't exist
            this.createTimestamp();
            timestamp = document.getElementById('last-update');
        }
        
        const now = new Date().toLocaleTimeString();
        timestamp.textContent = `Last updated: ${now}`;
        timestamp.style.color = 'var(--text-secondary)';
    }

    createTimestamp() {
        const container = document.querySelector('.container');
        const timestampDiv = document.createElement('div');
        timestampDiv.innerHTML = `
            <div style="text-align: center; margin: 20px 0;">
                <span id="monitoring-status" style="
                    display: inline-block;
                    background: #10b981;
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    margin-right: 15px;
                ">🟢 Live</span>
                <span id="last-update" style="
                    font-size: 14px;
                    color: var(--text-secondary);
                ">Connecting...</span>
            </div>
        `;
        container.appendChild(timestampDiv);
    }

    showMonitoringStatus(isActive) {
        const status = document.getElementById('monitoring-status');
        if (status) {
            if (isActive) {
                status.innerHTML = '🟢 Live';
                status.style.background = '#10b981';
            } else {
                status.innerHTML = '⏸️ Paused';
                status.style.background = '#6b7280';
            }
        }
    }

    showError(message) {
        const status = document.getElementById('monitoring-status');
        if (status) {
            status.innerHTML = '🔴 Error';
            status.style.background = '#ef4444';
        }
        
        const timestamp = document.getElementById('last-update');
        if (timestamp) {
            timestamp.textContent = message;
            timestamp.style.color = '#ef4444';
        }
    }
}

// Initialize monitor
const networkMonitor = new NetworkMonitor();

// Auto-start monitoring when page loads
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => networkMonitor.start(), 1000);
});