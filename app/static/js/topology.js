class NetworkTopology {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.width = 800;
        this.height = 400;
        this.svg = null;
        this.devices = [];
        this.connections = [];
    }

    async init(devices) {
        this.devices = devices;
        this.createTopology();
        this.renderTopology();
        // Start lightweight status updates
        this.startStatusUpdates();
    }

    createTopology() {
        // Enhanced topology with switches
        this.topology = {
            nodes: [
                { id: 1, name: 'Router-01', x: 150, y: 150, ip: '10.10.1.10', type: 'router' },
                { id: 3, name: 'Switch-01', x: 350, y: 150, ip: '10.10.1.30', type: 'switch' },
                { id: 4, name: 'Switch-02', x: 550, y: 150, ip: '10.10.1.40', type: 'switch' },
                { id: 2, name: 'Router-02', x: 750, y: 150, ip: '10.10.1.20', type: 'router' }
            ],
            connections: [
                { from: 1, to: 3, type: 'ethernet' },
                { from: 3, to: 4, type: 'trunk' },
                { from: 4, to: 2, type: 'ethernet' },
                { from: 1, to: 2, type: 'ospf', area: '0.0.0.0' }
            ]
        };
    }

    renderTopology() {
        // Create SVG instantly (no loading delay)
        this.container.innerHTML = `
            <div style="
                background: var(--card-bg-dark);
                border: 1px solid var(--card-border);
                border-radius: var(--border-radius);
                padding: 20px;
                margin-bottom: 20px;
            ">
                <h3 style="margin: 0 0 20px 0; color: var(--text-primary);">
                    🌐 Network Topology
                </h3>
                <svg width="${this.width}" height="${this.height}" style="border: 1px solid var(--card-border); border-radius: 8px;">
                    <defs>
                        <!-- Connection line styles -->
                        <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                                refX="9" refY="3.5" orient="auto">
                            <polygon points="0 0, 10 3.5, 0 7" fill="#10b981" />
                        </marker>
                        
                        <!-- OSPF area background -->
                        <pattern id="ospfPattern" patternUnits="userSpaceOnUse" width="20" height="20">
                            <rect width="20" height="20" fill="var(--card-bg-dark)"/>
                            <circle cx="10" cy="10" r="1" fill="#3b82f6" opacity="0.3"/>
                        </pattern>
                    </defs>
                    
                    <!-- OSPF Area -->
                    <rect x="50" y="50" width="700" height="300" 
                          fill="url(#ospfPattern)" 
                          stroke="#3b82f6" 
                          stroke-width="2" 
                          stroke-dasharray="5,5" 
                          rx="10"/>
                    
                    <text x="70" y="75" fill="#3b82f6" font-size="14" font-weight="bold">
                        OSPF Area 0.0.0.0
                    </text>
                    
                    <!-- Connection Lines -->
                    ${this.renderConnections()}
                    
                    <!-- Router Nodes -->
                    ${this.renderNodes()}
                </svg>
                
                <!-- Topology Legend -->
                <div style="
                    margin-top: 15px;
                    display: flex;
                    gap: 20px;
                    font-size: 0.875rem;
                    color: var(--text-secondary);
                ">
                    <div>🟢 Online Device</div>
                    <div>🔴 Offline Device</div>
                    <div style="color: #10b981;">━ OSPF Neighbor</div>
                    <div style="color: #3b82f6;">┅ OSPF Area</div>
                </div>
            </div>
        `;
    }

    renderNodes() {
        return this.topology.nodes.map(node => {
            const device = this.devices.find(d => d.id === node.id);
            const isOnline = device && device.status === 'UP';
            const nodeColor = isOnline ? '#10b981' : '#ef4444';
            
            // Different icons for device types
            const deviceIcon = node.type === 'router' ? '🔀' : '🔗';
            const deviceColor = node.type === 'router' ? '#3b82f6' : '#8b5cf6';
            
            return `
                <!-- Router Node -->
                <g class="topology-node" data-device-id="${node.id}" style="cursor: pointer;"
                   onclick="showDeviceTooltip(${node.id}, ${node.x}, ${node.y})">
                   
                    <!-- Node Circle -->
                    <circle cx="${node.x}" cy="${node.y}" r="35" 
                            fill="${nodeColor}" 
                            stroke="${deviceColor}" 
                            stroke-width="3"
                            opacity="0.9"/>
                    
                    <!-- Device Icon -->
                    <text x="${node.x}" y="${node.y + 5}" 
                          text-anchor="middle" 
                          font-size="20">${deviceIcon}</text>
                    
                    <!-- Device Name -->
                    <text x="${node.x}" y="${node.y + 55}" 
                          text-anchor="middle" 
                          fill="var(--text-primary)" 
                          font-size="11" 
                          font-weight="bold">${node.name}</text>
                    
                    <!-- Device Type -->
                    <text x="${node.x}" y="${node.y + 70}" 
                          text-anchor="middle" 
                          fill="${deviceColor}" 
                          font-size="9" 
                          font-weight="bold">${node.type.toUpperCase()}</text>
                </g>
            `;
        }).join('');
    }

    renderConnections() {
        return this.topology.connections.map(conn => {
            const fromNode = this.topology.nodes.find(n => n.id === conn.from);
            const toNode = this.topology.nodes.find(n => n.id === conn.to);
            
            if (!fromNode || !toNode) return '';
            
            // Both devices online = green connection
            const fromDevice = this.devices.find(d => d.id === conn.from);
            const toDevice = this.devices.find(d => d.id === conn.to);
            const bothOnline = fromDevice?.status === 'UP' && toDevice?.status === 'UP';
            const lineColor = bothOnline ? '#10b981' : '#ef4444';
            
            return `
                <line x1="${fromNode.x}" y1="${fromNode.y}" 
                      x2="${toNode.x}" y2="${toNode.y}" 
                      stroke="${lineColor}" 
                      stroke-width="3" 
                      marker-end="url(#arrowhead)"/>
                
                <!-- Connection Label -->
                <text x="${(fromNode.x + toNode.x) / 2}" 
                      y="${(fromNode.y + toNode.y) / 2 - 10}" 
                      text-anchor="middle" 
                      fill="#6b7280" 
                      font-size="10">
                    OSPF Neighbor
                </text>
            `;
        }).join('');
    }

    // Lightweight status updates (no heavy fetching)
    startStatusUpdates() {
        setInterval(async () => {
            try {
                // Quick status check (reuse existing API)
                const response = await fetch('/api/devices');
                const devices = await response.json();
                
                if (devices && devices.devices) {
                    this.devices = devices.devices;
                    this.updateTopologyStatus();
                }
            } catch (error) {
                console.log('Topology status update failed:', error);
            }
        }, 10000); // Update every 10 seconds
    }

    updateTopologyStatus() {
        // Update only colors, no DOM rebuilding
        this.topology.nodes.forEach(node => {
            const device = this.devices.find(d => d.id === node.id);
            const isOnline = device && device.status === 'UP';
            const nodeColor = isOnline ? '#10b981' : '#ef4444';
            
            const circleElement = document.querySelector(`circle[cx="${node.x}"][cy="${node.y}"]`);
            if (circleElement) {
                circleElement.setAttribute('fill', nodeColor);
            }
        });
        
        // Update connection colors
        this.updateConnectionColors();
    }

    updateConnectionColors() {
        const lines = document.querySelectorAll('line[marker-end]');
        lines.forEach((line, index) => {
            const conn = this.topology.connections[index];
            if (conn) {
                const fromDevice = this.devices.find(d => d.id === conn.from);
                const toDevice = this.devices.find(d => d.id === conn.to);
                const bothOnline = fromDevice?.status === 'UP' && toDevice?.status === 'UP';
                const lineColor = bothOnline ? '#10b981' : '#ef4444';
                
                line.setAttribute('stroke', lineColor);
            }
        });
    }
}

window.NetworkTopology = NetworkTopology;