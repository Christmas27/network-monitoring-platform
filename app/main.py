# app/main.py - FIXED IMPORTS
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime

# CORRECTED Service imports - Add 'app.' prefix
from app.services.device_management import DeviceManagement
from app.services.interface_management import InterfaceManagement
from app.services.vlan_management import VlanManagement
from app.services.frr_client import FRRClient
from app.services.ansible_client import AnsibleClient

# Initialize services
frr = FRRClient()
ansible = AnsibleClient()
device_service = DeviceManagement(frr, ansible)
interface_service = InterfaceManagement(frr, ansible)
vlan_service = VlanManagement(frr, ansible)

app = FastAPI(title="Network Monitoring API Gateway")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# === ROUTE DEFINITIONS (Clean & Simple) ===

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/devices")
async def get_devices():
    return await device_service.get_devices()

@app.get("/devices/{device_id}")
async def device_details(request: Request, device_id: int):
    return await device_service.get_device_details(request, device_id)

@app.post("/api/devices/{device_id}/interfaces/{interface_name}/{action}")
async def manage_interface(device_id: int, interface_name: str, action: str):
    return await interface_service.manage_interface(device_id, interface_name, action)

@app.get("/api/devices/{device_id}/interfaces")
async def get_device_interfaces(device_id: int):
    return await interface_service.get_interfaces(device_id)

@app.post("/api/devices/{device_id}/vlans")
async def create_vlan(device_id: int, vlan_data: dict):
    return await vlan_service.create_vlan(device_id, vlan_data)

@app.delete("/api/devices/{device_id}/vlans/{vlan_id}")
async def delete_vlan(device_id: int, vlan_id: int):
    return await vlan_service.delete_vlan(device_id, vlan_id)

@app.get("/api/devices/{device_id}/config")
async def get_device_config(device_id: int):
    """Get device running configuration"""
    return await device_service.get_device_config(device_id)

@app.get("/api/devices/{device_id}/routes")
async def get_device_routes(device_id: int):
    """Get device routing table"""
    return await device_service.get_device_routes(device_id)

@app.get("/api/devices/{device_id}/vlans")
async def get_device_vlans(device_id: int):
    """Get device VLANs (for switches)"""
    return await vlan_service.get_device_vlans(device_id)

@app.get("/api/devices/{device_id}/ospf")
async def get_device_ospf(device_id: int):
    """Get OSPF neighbors (for routers)"""
    return await device_service.get_device_ospf(device_id)

@app.post("/api/devices/{device_id}/test/{test_type}")
async def run_network_test(device_id: int, test_type: str):
    allowed = ["full", "ping", "interfaces", "ospf", "routes"]
    if test_type not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid test_type. Use one of: {allowed}")

    # Step 2 will implement this method in service layer
    if not hasattr(device_service, "run_network_tests"):
        raise HTTPException(status_code=501, detail="Network test service not implemented yet (Step 2 pending).")

    return await device_service.run_network_tests(device_id, test_type)

@app.post("/api/devices/{device_id}/test")
async def run_full_network_test(device_id: int):
    if not hasattr(device_service, "run_network_tests"):
        raise HTTPException(status_code=501, detail="Network test service not implemented yet (Step 2 pending).")

    return await device_service.run_network_tests(device_id, "full")

@app.post("/api/devices/{device_id}/interfaces/provision")
async def provision_interface(device_id: int, payload: dict):
    return await interface_service.provision_interface(device_id, payload)

@app.post("/api/devices/{device_id}/acl/apply")
async def apply_acl(device_id: int, payload: dict):
    return await interface_service.apply_acl(device_id, payload)

@app.post("/api/devices/{device_id}/acl/remove")
async def remove_acl(device_id: int, payload: dict):
    return await interface_service.remove_acl(device_id, payload)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)