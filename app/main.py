import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from services.devnet_client import DevNetClient
from services.frr_client import FRRClient
import uvicorn

app = FastAPI(title="Network Monitoring Platform")
devnet = DevNetClient()
frr = FRRClient()

# Serve static files (CSS, JS, images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates for HTML
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/devices")
async def get_devices():
    # Get info for both routers
    router1_info = await frr.get_device_info("frr-router1")
    router2_info = await frr.get_device_info("frr-router2")
    
    return {
        "devices": [
            {
                "id": 1,
                "name": "FRR-Router-01", 
                "ip": "10.10.1.10",
                "status": router1_info.get("status", "DOWN"),
                "device_type": "FRR Container",
                "ospf_neighbors": len(router1_info.get("ospf_neighbors", [])),
                "is_real": True
            },
            {
                "id": 2,
                "name": "FRR-Router-02", 
                "ip": "10.10.1.20",
                "status": router2_info.get("status", "DOWN"),
                "device_type": "FRR Container", 
                "ospf_neighbors": len(router2_info.get("ospf_neighbors", [])),
                "is_real": True
            }
        ]
    }

@app.get("/api/devices/{device_id}/details")
async def get_device_details(device_id: int):
    if device_id == 3:  # DevNet device
        device_info = await devnet.get_device_info()
        interfaces = await devnet.get_interfaces()
        return {
            "device_info": device_info,
            "interfaces": interfaces
        }
    return {"message": "Device details not available for mock devices"}

@app.get("/api/test-devnet")
async def test_devnet():
    """Test endpoint to check DevNet connectivity"""
    result = await devnet.test_connection()
    return result

@app.post("/api/devices")
async def add_device(device_data: dict):
    # Add new device to monitoring
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)