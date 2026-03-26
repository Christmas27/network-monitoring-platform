# Network Monitoring Project - Context

## Current Status:
- FastAPI backend with device monitoring
- FRR routers in Docker containers  
- Enhanced dashboard with dark mode
- Real-time device status updates
- **🚨 MIGRATION IN PROGRESS: Moving to Linux filesystem for optimal performance**

## Development Environment:
- **Current Location**: `/mnt/d/Network Project` (Windows filesystem - temporary)
- **Target Location**: `~/projects/network-monitoring` (Linux filesystem - better performance)
- **Environment**: WSL2 Ubuntu on Windows
- **Python**: 3.10.12 with virtual environment (.venv)

## Setup Status:
### ✅ Completed:
- WSL2 environment verified
- Python virtual environment created
- Dependencies installed via requirements.txt
- Basic VS Code setup (github.copilot-chat only)

### 🔄 In Progress:
- **Linux filesystem migration** (performance critical)
- VS Code extension installation for optimal development

### 📋 Required Extensions:
```bash
code --install-extension ms-python.python
code --install-extension ms-azuretools.vscode-docker  
code --install-extension bradlc.vscode-tailwindcss
code --install-extension redhat.vscode-yaml
code --install-extension ms-vscode.vscode-json
```

## Migration Commands:
```bash
# Complete migration to Linux filesystem
cd ~
mkdir -p ~/projects
cp -r "/mnt/d/Network Project" ~/projects/network-monitoring
cd ~/projects/network-monitoring

# Rebuild environment
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
code .
```

## Technical Stack:
- **Backend**: FastAPI (Python)
- **Frontend**: HTML/JS with Tailwind CSS
- **Network**: FRR routers (Docker)
- **Automation**: Ansible (planned)

## Current Features:
1. Device dashboard with live monitoring
2. Device details pages with interfaces/routes
3. Network topology visualization
4. Dark/light mode toggle

## Next Phase: 
Network Management via Ansible
- Interface enable/disable via web UI
- Route management through playbooks
- OSPF configuration changes

## File Structure (After Migration):
```
~/projects/network-monitoring/
├── app/
│   ├── main.py (FastAPI app)
│   ├── static/ (CSS/JS)
│   ├── templates/ (HTML)
│   └── services/ (API clients)
├── ansible/ (automation playbooks)  
├── docker-compose.yml (FRR containers)
├── requirements.txt
└── PROJECT_CONTEXT.md (this file)
```

## Running the Project (After Migration):
```bash
# From ~/projects/network-monitoring/
source .venv/bin/activate
docker-compose up -d  
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Key APIs:
- GET /api/devices - List all devices
- GET /api/devices/{id}/interfaces - Interface details  
- GET /api/devices/{id}/routes - Routing table
- POST /api/devices/{id}/interfaces/{name}/manage - Ansible automation (planned)

## Development Notes:
- **Performance**: Linux filesystem provides 5-10x better file operations
- **Docker Integration**: Better container performance on native Linux
- **VS Code**: Extensions work optimally on Linux filesystem
- **Future AWS Deployment**: Already in Linux-compatible environment

---
**🚀 Next Agent: Complete Linux migration and install VS Code extensions above**