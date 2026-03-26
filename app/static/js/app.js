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
            <div style="text-align: center; padding: 60px; color: var(--text-secondary);">
                <div style="font-size: 2rem; margin-bottom: 10px;">🔄</div>
                <div>Loading devices...</div>
            </div>`;
    }

    showError(message) {
        this.devicesGrid.innerHTML = `
            <div style="text-align: center; padding: 60px;">
                <div style="color: #ef4444; font-size: 1.5rem; margin-bottom: 10px;">❌ ${message}</div>
                <button onclick="location.reload()" style="
                    background: #3b82f6;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                ">🔄 Retry</button>
            </div>`;
    }

    renderDevices(devices) {
        // Store devices globally for tooltip access
        window.currentDevices = devices;
        
        if (!devices || devices.length === 0) {
            this.devicesGrid.innerHTML = '<div style="text-align: center; padding: 60px; color: var(--text-secondary);">No devices found</div>';
            return;
        }

        this.devicesGrid.innerHTML = `
            <div class="monitoring-dashboard" style="
                background: var(--bg-primary);
                color: var(--text-primary);
                padding: 20px;
                max-width: 1400px;
                margin: 0 auto;
            ">
                <!-- Network Topology -->
                <div id="network-topology"></div>
                
                <!-- Header Stats -->
                <div class="stats-grid" style="
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                ">
                    ${this.createStatsCards(devices)}
                </div>
                
                <!-- Device Table (existing) -->
                <div class="device-table-container" style="
                    background: var(--card-bg-dark);
                    border: 1px solid var(--card-border);
                    border-radius: var(--border-radius);
                    overflow: hidden;
                ">
                    <div class="table-header" style="
                        background: #374151;
                        padding: 16px 20px;
                        border-bottom: 1px solid var(--card-border);
                    ">
                        <h2 style="margin: 0; color: var(--text-primary); font-size: 1.25rem; font-weight: 600;">
                            📊 Device Status Table
                        </h2>
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
            <div class="stat-card" style="
                background: var(--card-bg-dark);
                border: 1px solid var(--card-border);
                border-radius: var(--border-radius);
                padding: 20px;
                text-align: center;
            ">
                <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 8px;">Total Devices</div>
                <div style="color: var(--primary-blue); font-size: 2rem; font-weight: 700;">${totalDevices}</div>
            </div>
            
            <div class="stat-card" style="
                background: var(--card-bg-dark);
                border: 1px solid var(--card-border);
                border-radius: var(--border-radius);
                padding: 20px;
                text-align: center;
            ">
                <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 8px;">Online</div>
                <div style="color: var(--success-green); font-size: 2rem; font-weight: 700;">${onlineDevices}</div>
            </div>
            
            <div class="stat-card" style="
                background: var(--card-bg-dark);
                border: 1px solid var(--card-border);
                border-radius: var(--border-radius);
                padding: 20px;
                text-align: center;
            ">
                <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 8px;">Offline</div>
                <div style="color: var(--danger-red); font-size: 2rem; font-weight: 700;">${offlineDevices}</div>
            </div>
            
            <div class="stat-card" style="
                background: var(--card-bg-dark);
                border: 1px solid var(--card-border);
                border-radius: var(--border-radius);
                padding: 20px;
                text-align: center;
            ">
                <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 8px;">OSPF Neighbors</div>
                <div style="color: var(--warning-orange); font-size: 2rem; font-weight: 700;">${totalNeighbors}</div>
            </div>
        `;
    }

    createDeviceTable(devices) {
        const tableHeader = `
            <div style="
                display: grid;
                grid-template-columns: 40px 1fr 150px 120px 120px 180px 200px;
                gap: 15px;
                padding: 16px 20px;
                background: #4b5563;
                color: var(--text-primary);
                font-weight: 600;
                font-size: 0.875rem;
                border-bottom: 1px solid var(--card-border);
            ">
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
        <div class="device-row" data-device-id="${device.id}" style="
            display: grid;
            grid-template-columns: 40px 1fr 150px 120px 120px 180px 380px;
            gap: 15px;
            padding: 16px 20px;
            border-bottom: 1px solid var(--card-border);
            transition: var(--transition-fast);
            color: var(--text-primary);
        " onmouseover="this.style.background='#374151'" onmouseout="this.style.background='transparent'">

        <div class="status-icon" style="font-size: 1.2rem;">${statusIcon}</div>

        <div>
            <div style="font-weight: 600; margin-bottom: 4px;">${device.name}</div>
            <div style="color: var(--text-secondary); font-size: 0.8rem;">${device.device_type}</div>
        </div>

        <div style="
            font-family: 'Courier New', monospace;
            font-weight: 600;
            color: #2563eb;
        ">${device.ip}</div>

        <div>
            <span class="status-badge" style="
                background: ${isOnline ? '#065f46' : '#7f1d1d'};
                color: ${isOnline ? '#10b981' : '#ef4444'};
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 0.75rem;
                font-weight: 600;
                transition: all 0.3s ease;
            ">${device.status}</span>
        </div>

        <div style="text-align: center;">
            <span class="ospf-count" style="color: #d97706; font-weight: 600;">
                ${device.ospf_neighbors || 0}
            </span>
        </div>

        <div class="last-update" style="color: var(--text-secondary); font-size: 0.875rem;">
            ${new Date().toLocaleTimeString()}
        </div>

        <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
            <button onclick="window.location.href='/devices/${device.id}'" style="
                padding: 6px 10px; font-size: 0.78rem; background: #3b82f6; color: #fff;
                border: none; border-radius: 4px; cursor: pointer;
            ">Details</button>

            <button onclick="manageInterface(${device.id}, 'eth0', 'disable', this)" style="
                padding: 6px 10px; font-size: 0.78rem; background: #dc2626; color: #fff;
                border: none; border-radius: 4px; cursor: pointer;
            ">Disable</button>

            <button onclick="manageInterface(${device.id}, 'eth0', 'enable', this)" style="
                padding: 6px 10px; font-size: 0.78rem; background: #059669; color: #fff;
                border: none; border-radius: 4px; cursor: pointer;
            ">Enable</button>

            <button onclick="manageInterface(${device.id}, 'eth0', 'reset', this)" style="
                padding: 6px 10px; font-size: 0.78rem; background: #d97706; color: #fff;
                border: none; border-radius: 4px; cursor: pointer;
            ">Reset</button>

            <select id="test-type-${device.id}" style="
                padding: 6px 8px;
                font-size: 0.78rem;
                border-radius: 4px;
                border: 1px solid #4b5563;
                background: #111827;
                color: #e5e7eb;
            ">
                <option value="full">Test: Full</option>
                <option value="ping">Ping</option>
                <option value="interfaces">Interfaces</option>
                ${isRouter ? '<option value="ospf">OSPF</option><option value="routes">Routes</option>' : ''}
                ${isSwitch ? '<option value="routes">Routes</option>' : ''}
            </select>

            <button onclick="runSelectedNetworkTest(${device.id}, this)" style="
                padding: 6px 10px; font-size: 0.78rem; background: #2563eb; color: #fff;
                border: none; border-radius: 4px; cursor: pointer;
            ">Run Test</button>
        </div>
    </div>
    `;
}

    createStatusIndicator() {
        const container = document.querySelector('.container');
        const statusDiv = document.createElement('div');
        statusDiv.innerHTML = `
            <div style="
                text-align: center; 
                margin: 20px 0; 
                padding: 15px; 
                background: var(--bg-card); 
                border-radius: 10px;
                border: 2px solid var(--border-color);
            ">
                <span id="monitoring-status" style="
                    display: inline-block;
                    background: #10b981;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 25px;
                    font-size: 14px;
                    font-weight: 600;
                    margin-right: 20px;
                ">🟢 Live Monitoring</span>
                <span id="last-update" style="
                    font-size: 14px;
                    color: var(--text-secondary);
                    font-weight: 500;
                ">Initializing...</span>
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
    tooltip.style.cssText = `
        position: fixed;
        left: ${x}px;
        top: ${y}px;
        background: var(--card-bg-dark);
        border: 1px solid var(--card-border);
        border-radius: var(--border-radius);
        padding: 15px;
        color: var(--text-primary);
        font-size: 0.875rem;
        z-index: 1000;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    `;
    
    tooltip.innerHTML = `
        <div style="font-weight: bold; margin-bottom: 8px;">${device.name}</div>
        <div>Status: <span style="color: ${device.status === 'UP' ? '#10b981' : '#ef4444'}">${device.status}</span></div>
        <div>IP: ${device.ip}</div>
        <div>OSPF Neighbors: ${device.ospf_neighbors || 0}</div>
        <div style="margin-top: 10px;">
            <button onclick="window.location.href='/devices/${device.id}'" style="
                background: var(--primary-blue);
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.8rem;
            ">View Details</button>
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
    notification.className = 'notification';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        z-index: 10000;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
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
        wrapper.style.cssText = `
            margin-top: 16px;
            background: #111827;
            color: #e5e7eb;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 12px;
        `;

        const container = document.querySelector('.device-table-container');
        if (container && container.parentNode) {
            container.parentNode.insertBefore(wrapper, container.nextSibling);
        } else {
            document.body.appendChild(wrapper);
        }

        wrapper.innerHTML = `
            <div id="network-test-header" style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:8px;">
                <div id="network-test-meta" style="font-size:12px;color:#93c5fd;"></div>
                <div style="display:flex;gap:8px;">
                    <button id="copy-test-output-btn" style="padding:4px 8px;font-size:12px;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:4px;cursor:pointer;">Copy Output</button>
                    <button id="clear-test-output-btn" style="padding:4px 8px;font-size:12px;background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:4px;cursor:pointer;">Clear</button>
                </div>
            </div>
            <div id="network-test-summary" style="font-size:12px;margin-bottom:8px;"></div>
            <pre id="network-test-output" style="
                max-height: 320px;
                overflow: auto;
                white-space: pre-wrap;
                margin: 0;
                font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                font-size: 12px;
                line-height: 1.4;
            "></pre>
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