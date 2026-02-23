# Network Monitoring & Automation Platform

A modern network monitoring platform built with FastAPI and FRR (Free Range Routing) containers.

## 🚀 Features

- **Real-time Network Monitoring**: Monitor FRR routers running in Docker containers
- **OSPF Protocol Support**: Track OSPF neighbors and routing information
- **REST API**: Complete API for device management and monitoring
- **Async Backend**: High-performance FastAPI with async operations
- **Containerized Network Lab**: Docker Compose orchestrated network topology

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.8+
- **Network Simulation**: FRR (Free Range Routing) in Docker
- **Protocols**: OSPF (BGP planned)
- **Containerization**: Docker & Docker Compose
- **API**: RESTful with automatic OpenAPI documentation

## 🏃‍♂️ Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/Christmas27/network-monitoring-platform.git
   cd network-monitoring-platform
   ```

2. **Set up Python environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. **Start the network lab**
   ```bash
   docker-compose up -d
   
   # Fix zebra daemons (temporary workaround)
   docker exec -it frr-router1 /usr/lib/frr/zebra -d -f /etc/frr/frr.conf
   docker exec -it frr-router2 /usr/lib/frr/zebra -d -f /etc/frr/frr.conf
   ```

4. **Launch the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the platform**
   - Dashboard: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Device Status: http://localhost:8000/api/devices

## 📡 API Endpoints

- `GET /api/devices` - List all network devices with status
- `GET /api/devices/{id}/details` - Get detailed device information
- `GET /api/test-devnet` - Test external network connectivity
- `POST /api/devices` - Add new device (planned)

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   FRR Router 1  │────│   FRR Router 2  │
│   10.10.1.10    │    │   10.10.1.20    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                   │
┌─────────────────────────────────────────┐
│        FastAPI Application              │
│     Network Monitoring Platform        │
└─────────────────────────────────────────┘
```

## 🔮 Roadmap

- [ ] Configuration management endpoints
- [ ] Network automation (VLAN, ACL, routing)
- [ ] SNMP integration
- [ ] Grafana dashboards
- [ ] BGP protocol support
- [ ] Cloud deployment (AWS)

## 🤝 Contributing

This is a portfolio project showcasing network automation and monitoring capabilities using modern Python frameworks and containerized network infrastructure.

## 📄 License

MIT License - feel free to use this project as inspiration for your own network automation journey!
