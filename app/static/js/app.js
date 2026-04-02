// Enhanced Network Monitoring Dashboard
class NetworkDashboard {
    constructor() {
        this.devicesGrid = document.getElementById('devices-grid');
        this.updateInterval = 5000; // 5 seconds for real-time feel
        this.isRunning = false;
        this.init();
    }

    async init() {
        await this.loadDevices();
        this.startRealTimeUpdates();
        this.createStatusIndicator();
    }

    startRealTimeUpdates() {
        if (this.isRunning) return;
        
        this.isRunning = true;
        console.log('🔄 Starting real-time monitoring...');
        
        // Update every 5 seconds for real-time feel
        this.intervalId = setInterval(() => this.loadDevices(), this.updateInterval);
        this.showMonitoringStatus(true);
    }

    stopRealTimeUpdates() {
        this.isRunning = false;
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        this.showMonitoringStatus(false);
    }

    async loadDevices() {
        try {
            const response = await fetch('/api/devices');
            const data = await response.json();
            
            // If no devices-grid exists yet, do full render
            if (!document.querySelector('.monitoring-dashboard')) {
                this.renderDevices(data.devices);
                this.updateTimestamp();
                return;
            }
            
            // Otherwise, just update the data smoothly
            this.updateDeviceData(data.devices);
            this.updateTimestamp();
            
        } catch (error) {
            console.error('Error loading devices:', error);
            this.showError('Failed to load devices');
        }
    }

    // NEW METHOD: Smooth data updates without re-rendering
    updateDeviceData(devices) {
        // Store devices globally
        window.currentDevices = devices;
        
        // Update stats cards
        this.updateStatsCards(devices);
        
        // Update device rows
        this.updateDeviceRows(devices);
        
        // Update topology nodes (without rebuilding)
        if (window.currentTopology) {
            window.currentTopology.updateDeviceStatus(devices);
        }
    }

    updateStatsCards(devices) {
        const totalDevices = devices.length;
        const onlineDevices = devices.filter(d => d.status === 'UP').length;
        const offlineDevices = totalDevices - onlineDevices;
        const totalNeighbors = devices.reduce((sum, d) => sum + (d.ospf_neighbors || 0), 0);
        
        // Update stat card values smoothly
        const statCards = document.querySelectorAll('.stat-card div:last-child');
        if (statCards.length >= 4) {
            statCards[0].textContent = totalDevices;
            statCards[1].textContent = onlineDevices;
            statCards[1].style.color = onlineDevices > 0 ? 'var(--success-green)' : 'var(--danger-red)';
            statCards[2].textContent = offlineDevices;
            statCards[3].textContent = totalNeighbors;
        }
    }

    updateDeviceRows(devices) {
        devices.forEach(device => {
            const deviceRow = document.querySelector(`[data-device-id="${device.id}"]`);
            if (deviceRow) {
                // Update status without rebuilding row
                const statusIcon = deviceRow.querySelector('.status-icon');
                const statusBadge = deviceRow.querySelector('.status-badge');
                const ospfCount = deviceRow.querySelector('.ospf-count');
                
                if (statusIcon) statusIcon.textContent = device.status === 'UP' ? '🟢' : '🔴';
                if (statusBadge) {
                    statusBadge.textContent = device.status;
                    statusBadge.style.background = device.status === 'UP' ? '#065f46' : '#7f1d1d';
                    statusBadge.style.color = device.status === 'UP' ? '#10b981' : '#ef4444';
                }
                if (ospfCount) ospfCount.textContent = device.ospf_neighbors || 0;
            }
        });
    }

    showLoading() {
        this.devicesGrid.innerHTML = `
            <div class="empty-state">
                <div style="font-size: 2rem; margin-bottom: 10px;">🔄</div>
                <div>Loading devices...</div>
            </div>`;
    }

    showError(message) {
        this.devicesGrid.innerHTML = `
            <div class="error-state">
                <div class="error-state__message">❌ ${message}</div>
                <button onclick="location.reload()" class="retry-btn">🔄 Retry</button>
            </div>`;
    }

    renderDevices(devices) {
        // Store devices globally for tooltip access
        window.currentDevices = devices;
        
        if (!devices || devices.length === 0) {
            this.devicesGrid.innerHTML = '<div class="empty-state">No devices found</div>';
            return;
        }

        this.devicesGrid.innerHTML = `
            <div class="monitoring-dashboard">
                <!-- Network Topology -->
                <div id="network-topology"></div>
                
                <!-- Header Stats -->
                <div class="stats-grid">
                    ${this.createStatsCards(devices)}
                </div>
                
                <!-- Device Table -->
                <div class="device-table-container">
                    <div class="table-header">
                        <h2>📊 Device Status Table</h2>
                    </div>
                    
                    <div class="device-table">
                        ${this.createDeviceTable(devices)}
                    </div>
                </div>
            </div>
        `;
        
        // Initialize topology after DOM is ready
        setTimeout(() => {
            const topology = new NetworkTopology('network-topology');
            topology.init(devices);
        }, 100);
    }

    createStatsCards(devices) {
        const totalDevices = devices.length;
        const onlineDevices = devices.filter(d => d.status === 'UP').length;
        const offlineDevices = totalDevices - onlineDevices;
        const totalNeighbors = devices.reduce((sum, d) => sum + (d.ospf_neighbors || 0), 0);
        
        return `
            <div class="stat-card">
                <div class="stat-label">Total Devices</div>
                <div class="stat-value stat-value--blue">${totalDevices}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Online</div>
                <div class="stat-value stat-value--green">${onlineDevices}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">Offline</div>
                <div class="stat-value stat-value--red">${offlineDevices}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-label">OSPF Neighbors</div>
                <div class="stat-value stat-value--orange">${totalNeighbors}</div>
            </div>
        `;
    }

    createDeviceTable(devices) {
        const tableHeader = `
            <div class="device-table-columns">
                <div>Status</div>
                <div>Device Name</div>
                <div>IP Address</div>
                <div>Type</div>
                <div>OSPF</div>
                <div>Last Seen</div>
                <div>Actions</div>
            </div>
        `;
        
        const tableRows = devices.map(device => this.createDeviceRow(device)).join('');
        
        return tableHeader + tableRows;
    }

    createDeviceRow(device) {
    const isOnline = device.status === 'UP';
    const statusIcon = isOnline ? '🟢' : '🔴';
    const isRouter = (device.device_type || '').toLowerCase().includes('router');
    const isSwitch = (device.device_type || '').toLowerCase().includes('switch');

    return `
        <div class="device-row" data-device-id="${device.id}">

        <div class="status-icon">${statusIcon}</div>

        <div>
            <div class="device-name-primary">${device.name}</div>
            <div class="device-name-secondary">${device.device_type}</div>
        </div>

        <div class="device-ip-cell">${device.ip}</div>

        <div>
            <span class="status-badge ${isOnline ? 'status-badge--up' : 'status-badge--down'}">${device.status}</span>
        </div>

        <div class="ospf-count">
                ${device.ospf_neighbors || 0}
        </div>

        <div class="last-update">
            ${new Date().toLocaleTimeString()}
        </div>

        <div class="device-actions">
            <button onclick="window.location.href='/devices/${device.id}'" class="action-btn action-btn--details">Details</button>

            <button onclick="manageInterface(${device.id}, 'eth0', 'disable', this)" class="action-btn action-btn--disable">Disable</button>

            <button onclick="manageInterface(${device.id}, 'eth0', 'enable', this)" class="action-btn action-btn--enable">Enable</button>

            <button onclick="manageInterface(${device.id}, 'eth0', 'reset', this)" class="action-btn action-btn--reset">Reset</button>

            <select id="test-type-${device.id}" class="test-type-select">
                <option value="full">Test: Full</option>
                <option value="ping">Ping</option>
                <option value="interfaces">Interfaces</option>
                ${isRouter ? '<option value="ospf">OSPF</option><option value="routes">Routes</option>' : ''}
                ${isSwitch ? '<option value="routes">Routes</option>' : ''}
            </select>

            <button onclick="runSelectedNetworkTest(${device.id}, this)" class="action-btn action-btn--test">Run Test</button>
        </div>
    </div>
    `;
}

    createStatusIndicator() {
        const container = document.querySelector('.container');
        const statusDiv = document.createElement('div');
        statusDiv.innerHTML = `
            <div class="monitoring-bar">
                <span id="monitoring-status" class="monitoring-badge">🟢 Live Monitoring</span>
                <span id="last-update" class="monitoring-timestamp">Initializing...</span>
            </div>
        `;
        container.appendChild(statusDiv);
    }

    updateTimestamp() {
        const timestamp = document.getElementById('last-update');
        if (timestamp) {
            const now = new Date().toLocaleTimeString();
            timestamp.textContent = `Last updated: ${now}`;
        }
    }

    showMonitoringStatus(isActive) {
        const status = document.getElementById('monitoring-status');
        if (status) {
            if (isActive) {
                status.innerHTML = '🟢 Live Monitoring';
                status.style.background = '#10b981';
            } else {
                status.innerHTML = '⏸️ Paused';
                status.style.background = '#6b7280';
            }
        }
    }
}

// Initialize enhanced dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 DOM loaded, starting dashboard...');
    
    const devicesGrid = document.getElementById('devices-grid');
    if (!devicesGrid) {
        console.error('❌ devices-grid element not found!');
        return;
    }
    
    // Initialize the NetworkDashboard class (this has the red/green buttons)
    new NetworkDashboard();
});


// Device tooltip function
function showDeviceTooltip(deviceId, x, y) {
    const device = window.currentDevices?.find(d => d.id === deviceId);
    if (!device) return;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'device-tooltip';
    tooltip.style.left = `${x}px`;
    tooltip.style.top = `${y}px`;
    
    tooltip.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 8px;">${device.name}</div>
        <div>Status: <span style="color: ${device.status === 'UP' ? '#10b981' : '#ef4444'}">${device.status}</span></div>
        <div>IP: ${device.ip}</div>
        <div>OSPF Neighbors: ${device.ospf_neighbors || 0}</div>
        <div style="margin-top: 10px;">
            <button onclick="window.location.href='/devices/${device.id}'" class="action-btn action-btn--details">View Details</button>
        </div>
    `;
    
    document.body.appendChild(tooltip);
    
    // Remove tooltip on click outside
    setTimeout(() => {
        document.addEventListener('click', () => tooltip.remove(), { once: true });
    }, 100);
}

// Enhanced interface management function
async function manageInterface(deviceId, interfaceName, action, button) {
    try {
        // Show loading state
        const originalText = button.textContent;
        const originalClass = button.className;
        button.textContent = 'Processing...';
        button.disabled = true;
        button.className = 'btn btn-secondary';
        
        console.log(`Managing interface: Device ${deviceId}, Interface ${interfaceName}, Action ${action}`);
        
        // Call API
        const response = await fetch(`/api/devices/${deviceId}/interfaces/${interfaceName}/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        console.log('Interface management result:', result);
        
        if (result.success) {
            // Success notification
            showNotification(`Interface ${interfaceName} ${action}d successfully on ${result.container}!`, 'success');
            
            // Update button states based on action
            updateInterfaceButtons(deviceId, interfaceName, action);
            
            // Optionally refresh device data after a delay
            setTimeout(() => {
                refreshDeviceData(deviceId);
            }, 2000);
            
        } else {
            showNotification(`Failed to ${action} interface ${interfaceName}`, 'error');
        }
        
    } catch (error) {
        console.error('Interface management error:', error);
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        // Reset button after a short delay
        setTimeout(() => {
            button.textContent = originalText;
            button.className = originalClass;
            button.disabled = false;
        }, 1000);
    }
}

// Update interface button states
function updateInterfaceButtons(deviceId, interfaceName, lastAction) {
    const deviceRow = document.querySelector(`[data-device-id="${deviceId}"]`);
    if (!deviceRow) return;
    
    const disableBtn = deviceRow.querySelector('.btn-danger');
    const enableBtn = deviceRow.querySelector('.btn-success');
    
    if (lastAction === 'disable') {
        if (disableBtn) {
            disableBtn.style.opacity = '0.5';
            disableBtn.textContent = 'Disabled';
        }
        if (enableBtn) {
            enableBtn.style.opacity = '1';
            enableBtn.style.fontWeight = 'bold';
        }
    } else if (lastAction === 'enable') {
        if (enableBtn) {
            enableBtn.style.opacity = '0.5';
            enableBtn.textContent = 'Enabled';
        }
        if (disableBtn) {
            disableBtn.style.opacity = '1';
            disableBtn.style.fontWeight = 'bold';
        }
    }
}

// Refresh specific device data
async function refreshDeviceData(deviceId) {
    try {
        console.log(`Refreshing data for device ${deviceId}`);
        
        // Get updated interfaces
        const interfaceResponse = await fetch(`/api/devices/${deviceId}/interfaces`);
        const interfaceData = await interfaceResponse.json();
        
        console.log('Updated interface data:', interfaceData);
        
        // Update the device row with new status
        const deviceRow = document.querySelector(`[data-device-id="${deviceId}"]`);
        if (deviceRow && interfaceData.interfaces) {
            // You can add more sophisticated status updates here
            const lastUpdate = deviceRow.querySelector('.last-update');
            if (lastUpdate) {
                lastUpdate.textContent = new Date().toLocaleTimeString();
            }
        }
        
    } catch (error) {
        console.error('Error refreshing device data:', error);
    }
}

// Enhanced notification function (if not already present)
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(n => n.remove());
    
    const notification = document.createElement('div');
    const typeClass = type === 'success' ? 'notification--success' : type === 'error' ? 'notification--error' : 'notification--info';
    notification.className = `notification ${typeClass}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove after 4 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

async function runNetworkTest(deviceId, testType = 'full', button) {
    const originalText = button.textContent;
    try {
        button.textContent = 'Testing...';
        button.disabled = true;

        const response = await fetch(`/api/devices/${deviceId}/test/${testType}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const payload = await response.json();

        if (!response.ok) {
            const detail = payload?.detail || 'Request failed';
            showNotification(`Test failed: ${detail}`, 'error');
            showTestOutput({
                deviceId,
                testType,
                status: 'FAILED',
                summary: detail,
                output: JSON.stringify(payload, null, 2)
            });
            return;
        }

        const ok = payload?.success === true;
        const apiSummary = payload?.summary || payload?.result?.summary || {};
        const metrics = apiSummary.metrics || {};
        const recap = apiSummary.recap_line || "No recap line";
        const status = apiSummary.status || (ok ? "PASSED" : "FAILED");

        const stdout = payload?.result?.stdout || "";
        const stderr = payload?.result?.stderr || "";
        const output = stdout || stderr || "No output returned";

        if (ok) {
            showNotification(`Network test ${testType} passed on device ${deviceId}`, "success");
        } else {
            const err = payload?.result?.error || stderr || "Unknown test error";
            showNotification(`Test error: ${err}`, "error");
        }

        const summaryText =
            `status=${status} | ok=${metrics.ok ?? 0} changed=${metrics.changed ?? 0} ` +
            `failed=${metrics.failed ?? 0} skipped=${metrics.skipped ?? 0} ` +
            `unreachable=${metrics.unreachable ?? 0}`;

        showTestOutput({
            deviceId,
            testType,
            status,
            summary: `${summaryText} | ${recap}`,
            output
        });
        
    } catch (err) {
        showNotification(`Network test request error: ${err.message}`, 'error');
        showTestOutput({
            deviceId,
            testType,
            status: 'FAILED',
            summary: err.message,
            output: String(err)
        });
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

async function runSelectedNetworkTest(deviceId, button) {
    const select = document.getElementById(`test-type-${deviceId}`);
    const testType = select ? select.value : 'full';
    await runNetworkTest(deviceId, testType, button);
}

function showTestOutput({ deviceId, testType, status, summary, output }) {
    let wrapper = document.getElementById('network-test-output-wrapper');
    if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.id = 'network-test-output-wrapper';
        wrapper.className = 'test-output-wrapper';

        const container = document.querySelector('.device-table-container');
        if (container && container.parentNode) {
            container.parentNode.insertBefore(wrapper, container.nextSibling);
        } else {
            document.body.appendChild(wrapper);
        }

        wrapper.innerHTML = `
            <div class="test-output-header">
                <div id="network-test-meta" class="test-output-meta"></div>
                <div style="display:flex;gap:8px;">
                    <button id="copy-test-output-btn" class="test-output-btn">Copy Output</button>
                    <button id="clear-test-output-btn" class="test-output-btn">Clear</button>
                </div>
            </div>
            <div id="network-test-summary" class="test-output-summary"></div>
            <pre id="network-test-output" class="test-output-pre"></pre>
        `;

        document.getElementById('copy-test-output-btn').addEventListener('click', async () => {
            const text = document.getElementById('network-test-output')?.textContent || '';
            try {
                await navigator.clipboard.writeText(text);
                showNotification('Test output copied', 'success');
            } catch {
                showNotification('Copy failed', 'error');
            }
        });

        document.getElementById('clear-test-output-btn').addEventListener('click', () => {
            document.getElementById('network-test-meta').textContent = '';
            document.getElementById('network-test-summary').textContent = '';
            document.getElementById('network-test-output').textContent = '';
        });
    }

    const now = new Date().toLocaleTimeString();
    const statusColor = status === 'PASSED' ? '#10b981' : '#ef4444';

    document.getElementById('network-test-meta').textContent =
        `[${now}] Device ${deviceId} • Test: ${testType} • ${status}`;

    const summaryEl = document.getElementById('network-test-summary');
    summaryEl.textContent = `Summary: ${summary}`;
    summaryEl.style.color = statusColor;

    const outputEl = document.getElementById('network-test-output');
    outputEl.textContent = output;
    outputEl.scrollTop = 0;
}

function extractPlayRecap(stdoutText) {
    if (!stdoutText) return null;
    const lines = stdoutText.split('\n');
    const recapIndex = lines.findIndex(line => line.includes('PLAY RECAP'));
    if (recapIndex === -1) return null;

    // Return first non-empty line after PLAY RECAP divider
    for (let i = recapIndex + 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line && !line.startsWith('*')) return line;
    }
    return null;
}