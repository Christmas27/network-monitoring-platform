# Network Monitoring & Automation Platform

A full-stack network monitoring and automation platform built with FastAPI and containerised FRR (Free Range Routing) devices. Designed as a portfolio project targeting cloud and networking roles.

## Features

- **Real-time Dashboard** — Live device status with auto-refresh, dark/light theme toggle
- **Device Details** — Running config, interfaces, OSPF neighbours, routing table per device
- **VLAN Management** — Create and delete VLANs on L3 switches via UI
- **ACL Management** — Apply and remove nftables-based firewall rules with in-app syntax guide
- **Interface Provisioning** — Assign IPs, toggle interfaces, add static routes via Ansible
- **Network Testing** — Full / ping / interfaces / OSPF / routes test suites per device
- **Device Driver Architecture** — Vendor-agnostic abstraction layer (ready for multi-vendor expansion)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.10, async |
| Frontend | Jinja2 templates, Tailwind CSS, vanilla JS |
| Network Lab | 4 FRR containers (2 routers + 2 L3 switches) via Docker Compose |
| Automation | Ansible playbooks (subprocess) for config changes |
| ACL Engine | nftables in Linux data plane (custom FRR image with `nft`) |
| Testing | pytest with structured error taxonomy assertions |

## Network Topology

```
          ┌────────────────┐         ┌────────────────┐
          │  frr-router1   │─────────│  frr-router2   │
          │  10.10.1.10    │         │  10.10.1.20    │
          └───────┬────────┘         └───────┬────────┘
                  │        lab_network        │
                  │       10.10.1.0/24        │
          ┌───────┴────────┐         ┌───────┴────────┐
          │  frr-switch1   │─────────│  frr-switch2   │
          │  10.10.1.30    │         │  10.10.1.40    │
          └────────────────┘         └────────────────┘
                  │    transit_net1 172.16.10.0/24   │
                  │    transit_net2 172.16.20.0/24   │
```

All four devices run OSPF for dynamic routing.

## Quick Start

```bash
# 1. Clone and set up Python
git clone https://github.com/YOUR_USERNAME/network-monitoring.git
cd network-monitoring
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
pip install -r requirements.txt

# 2. Start the network lab
docker-compose up -d --build

# 3. Fix zebra daemons (known FRR container issue)
docker exec -it frr-router1 /usr/lib/frr/zebra -d -f /etc/frr/frr.conf
docker exec -it frr-router2 /usr/lib/frr/zebra -d -f /etc/frr/frr.conf

# 4. Launch the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Run tests
pytest tests/ -v
```

- Dashboard: http://localhost:8000
- API docs: http://localhost:8000/docs

## API Reference

### Devices
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices` | List all devices with live status |
| GET | `/devices/{id}` | Device details page (HTML) |
| GET | `/api/devices/{id}/config` | Running configuration |
| GET | `/api/devices/{id}/interfaces` | Interface list |
| GET | `/api/devices/{id}/routes` | Routing table |
| GET | `/api/devices/{id}/ospf` | OSPF neighbours |
| GET | `/api/devices/{id}/vlans` | VLAN list (switches) |

### Actions
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/devices/{id}/interfaces/{name}/{action}` | Enable / disable interface |
| POST | `/api/devices/{id}/interfaces/provision` | Provision interface (IP, route) |
| POST | `/api/devices/{id}/vlans` | Create VLAN |
| DELETE | `/api/devices/{id}/vlans/{vlan_id}` | Delete VLAN |
| POST | `/api/devices/{id}/acl/apply` | Apply ACL (nftables) |
| POST | `/api/devices/{id}/acl/remove` | Remove ACL |
| POST | `/api/devices/{id}/test/{type}` | Run network test |

## ACL Usage Guide

This platform uses **nftables** — the modern Linux kernel packet filter — instead of traditional Cisco IOS ACLs. Rules are applied inside FRR containers via Ansible.

### Why nftables?

The FRR containers run on Linux. FRR handles routing (OSPF, BGP) but does **not** have a built-in ACL engine for data-plane filtering. nftables is the native Linux firewall and gives us real packet filtering on the containers.

### How to write rules

Each line in the ACL Rules text box is a single nftables **match + action** fragment. The system wraps it with the correct table, chain, interface binding, and tag automatically.

**Common examples:**

| Rule | What it does |
|------|-------------|
| `tcp dport 22 accept` | Allow SSH |
| `tcp dport {80, 443} accept` | Allow HTTP and HTTPS |
| `udp dport 53 accept` | Allow DNS |
| `icmp type echo-request accept` | Allow ping |
| `ip saddr 10.10.1.0/24 accept` | Allow traffic from a subnet |
| `ip saddr 192.168.1.100 drop` | Block a specific host |
| `tcp dport 22 ip saddr 10.10.1.0/24 accept` | Allow SSH from subnet only |
| `drop` | Drop everything else (default deny — put last) |

### Key differences from Cisco ACLs

- `accept` / `drop` instead of `permit` / `deny`
- Protocol comes before the port: `tcp dport 80` not `port 80 tcp`
- Curly braces for multiple ports: `tcp dport {22, 80, 443}`
- CIDR notation for subnets: `ip saddr 10.0.0.0/8`
- Rules are evaluated top to bottom — put `drop` last for default deny

### What happens internally

1. The API receives the ACL name, interface, direction, and rule lines
2. An Ansible playbook runs `nft` commands inside the target container
3. Rules are added to the `inet nm_acl` table under an `input` or `output` chain
4. Each rule is tagged with a comment (e.g., `nm_acl_LAB-IN`) so it can be cleanly removed later
5. Re-applying the same ACL name removes old rules first (idempotent)

### Verifying rules manually

```bash
# List all rules in a container
docker exec frr-switch1 nft list ruleset

# List a specific chain
docker exec frr-switch1 nft list chain inet nm_acl input
```

## Architecture

```
app/
├── main.py                        # FastAPI routes + Pydantic models
├── services/
│   ├── drivers/
│   │   ├── base.py                # DeviceDriver ABC (vendor-agnostic)
│   │   ├── frr_driver.py          # FRR implementation
│   │   └── registry.py            # DriverRegistry (device lookup)
│   ├── device_management.py       # Device info, config, routes, tests
│   ├── interface_management.py    # Interface + ACL operations
│   ├── vlan_management.py         # VLAN create/delete
│   ├── frr_client.py              # Docker/vtysh command execution
│   └── ansible_client.py          # Ansible playbook runner
├── templates/                     # Jinja2 HTML (dashboard, device details)
└── static/                        # CSS (design tokens), JS
```

The **driver architecture** abstracts device operations behind a `DeviceDriver` interface, so adding support for Cisco IOS, Arista, or other vendors requires only implementing a new driver class and registering it.

## Roadmap

- [x] Real-time monitoring dashboard
- [x] OSPF / routing / interface monitoring
- [x] VLAN management (create/delete)
- [x] ACL management with nftables
- [x] Device driver abstraction layer
- [x] Dark / light theme with CSS design tokens
- [x] Accessibility (ARIA landmarks, focus management, reduced motion)
- [ ] AWS deployment (EC2 Spot + Docker Compose)
- [ ] Safe change workflow (pre-check → apply → verify → rollback)
- [ ] EVE-NG / GNS3 topology integration
- [ ] CI/CD pipeline (GitHub Actions)

## License

MIT