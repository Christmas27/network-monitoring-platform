# app/main.py - FIXED IMPORTS
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from datetime import datetime

# CORRECTED Service imports - Add 'app.' prefix
from app.services.device_management import DeviceManagement
from app.services.interface_management import InterfaceManagement
from app.services.vlan_management import VlanManagement
from app.services.frr_client import FRRClient
from app.services.ansible_client import AnsibleClient
from app.services.drivers import FrrDriver, DriverRegistry

# Initialize drivers and registry
frr = FRRClient()
frr_driver = FrrDriver(frr)
ansible = AnsibleClient()

registry = DriverRegistry()
registry.register(1, "Router1", "frr-router1", "router", "10.10.1.10", frr_driver)
registry.register(2, "Router2", "frr-router2", "router", "10.10.1.20", frr_driver)
registry.register(3, "Switch1", "frr-switch1", "switch", "10.10.1.30", frr_driver)
registry.register(4, "Switch2", "frr-switch2", "switch", "10.10.1.40", frr_driver)

# Initialize services with registry
device_service = DeviceManagement(registry, ansible)
interface_service = InterfaceManagement(registry, ansible)
vlan_service = VlanManagement(frr, ansible)

app = FastAPI(title="Network Monitoring API Gateway")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def _error_detail(error_type: str, message: str, context: dict | None = None) -> dict:
    return {
        "error_type": error_type,
        "message": message,
        "context": context or {}
    }


class VlanCreateRequest(BaseModel):
    vlan_id: int = Field(..., ge=1, le=4094)
    name: str | None = Field(default=None, max_length=64)


class InterfaceProvisionRequest(BaseModel):
    interface: str = Field(..., min_length=2, max_length=64)
    ip_cidr: str = Field(..., min_length=3, max_length=64)
    description: str = Field(default="", max_length=120)
    route_prefix: str = Field(default="", max_length=64)
    route_next_hop: str = Field(default="", max_length=64)


class ACLApplyRequest(BaseModel):
    interface: str = Field(..., min_length=2, max_length=64)
    direction: str = Field(default="in", pattern="^(in|out)$")
    acl_name: str = Field(..., min_length=1, max_length=64)
    acl_lines: list[str] = Field(..., min_length=1)


class ACLRemoveRequest(BaseModel):
    interface: str = Field(..., min_length=2, max_length=64)
    direction: str = Field(default="in", pattern="^(in|out)$")
    acl_name: str = Field(..., min_length=1, max_length=64)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

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
async def create_vlan(device_id: int, vlan_data: VlanCreateRequest):
    return await vlan_service.create_vlan(device_id, vlan_data.model_dump())

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
        raise HTTPException(
            status_code=400,
            detail=_error_detail(
                "validation_error",
                f"Invalid test_type. Use one of: {allowed}",
                {"test_type": test_type, "allowed": allowed}
            )
        )

    if not hasattr(device_service, "run_network_tests"):
        raise HTTPException(
            status_code=501,
            detail=_error_detail(
                "not_implemented",
                "Network test service not implemented yet (Step 2 pending)."
            )
        )

    return await device_service.run_network_tests(device_id, test_type)

@app.post("/api/devices/{device_id}/test")
async def run_full_network_test(device_id: int):
    if not hasattr(device_service, "run_network_tests"):
        raise HTTPException(
            status_code=501,
            detail=_error_detail(
                "not_implemented",
                "Network test service not implemented yet (Step 2 pending)."
            )
        )

    return await device_service.run_network_tests(device_id, "full")

@app.post("/api/devices/{device_id}/interfaces/provision")
async def provision_interface(device_id: int, payload: InterfaceProvisionRequest):
    return await interface_service.provision_interface(device_id, payload.model_dump())

@app.post("/api/devices/{device_id}/acl/apply")
async def apply_acl(device_id: int, payload: ACLApplyRequest):
    return await interface_service.apply_acl(device_id, payload.model_dump())

@app.post("/api/devices/{device_id}/acl/remove")
async def remove_acl(device_id: int, payload: ACLRemoveRequest):
    return await interface_service.remove_acl(device_id, payload.model_dump())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)