# app/services/device_management.py
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Any, NoReturn

from app.services.drivers.registry import DriverRegistry

templates = Jinja2Templates(directory="app/templates")

class DeviceManagement:
    def __init__(self, registry: DriverRegistry, ansible_client):
        self.registry = registry
        self.ansible = ansible_client

    # ------------------------------------------------------------------
    # Lookup helper (replaces duplicated device_map dicts)
    # ------------------------------------------------------------------
    def _resolve(self, device_id: int):
        entry = self.registry.get(device_id)
        if not entry:
            self._raise_not_found("Device not found", {"device_id": device_id})
        return entry

    def _error_detail(self, error_type: str, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "error_type": error_type,
            "message": message,
            "context": context or {}
        }

    def _raise_validation(self, message: str, context: dict[str, Any] | None = None) -> NoReturn:
        raise HTTPException(status_code=400, detail=self._error_detail("validation_error", message, context))

    def _raise_not_found(self, message: str, context: dict[str, Any] | None = None) -> NoReturn:
        raise HTTPException(status_code=404, detail=self._error_detail("not_found", message, context))

    def _raise_execution(self, message: str, context: dict[str, Any] | None = None) -> NoReturn:
        raise HTTPException(status_code=500, detail=self._error_detail("execution_error", message, context))
        
    async def get_devices(self):
        """Get all devices with their status"""
        try:
            devices = []

            for entry in self.registry.all_devices():
                try:
                    device_info = await entry.driver.get_device_info(entry.container)
                    
                    device = {
                        "id": entry.device_id,
                        "name": entry.name,
                        "ip": entry.ip,
                        "device_type": entry.device_type,
                        "status": device_info.get("status", "DOWN"),
                        "container": entry.container,
                        "ospf_neighbors": len(device_info.get("ospf_neighbors", [])),
                        "last_seen": datetime.now().isoformat()
                    }
                    devices.append(device)
                    
                except Exception as e:
                    print(f"Error getting info for {entry.container}: {e}")
                    devices.append({
                        "id": entry.device_id,
                        "name": entry.name,
                        "ip": entry.ip,
                        "device_type": entry.device_type,
                        "status": "DOWN",
                        "container": entry.container,
                        "ospf_neighbors": 0,
                        "last_seen": datetime.now().isoformat()
                    })
            
            return {
                "devices": devices,
                "timestamp": datetime.now().isoformat(),
                "total_devices": len(devices),
                "online_devices": len([d for d in devices if d["status"] == "UP"])
            }
            
        except Exception as e:
            self._raise_execution(str(e), {"operation": "get_devices"})
    
    async def get_device_details(self, request: Request, device_id: int):
        """Get device details page"""
        try:
            entry = self._resolve(device_id)
            driver = entry.driver
            
            # Get device information
            device_info = await driver.get_device_info(entry.container)
            device_config = await driver.get_running_config(entry.container)
            
            # Build device data object
            device_data = {
                "id": device_id,
                "name": entry.name,
                "ip": entry.ip,
                "container_name": entry.container,
                "status": device_info.get("status", "DOWN"),
                "is_router": entry.device_type == "router",
                "is_switch": entry.device_type == "switch"
            }
            
            # Add router-specific data
            if device_data["is_router"]:
                device_data.update({
                    "ospf_neighbors": device_info.get("ospf_neighbors", []),
                    "interfaces": await driver.get_interfaces(entry.container),
                    "routing_table": await driver.get_routes(entry.container)
                })
            
            # Add switch-specific data
            elif device_data["is_switch"]:
                device_data.update({
                    "vlans": await driver.get_vlans(entry.container),
                    "ports": device_info.get("ports", []),
                    "switch_info": await self._get_switch_details(driver, entry.container)
                })
            
            return templates.TemplateResponse(
                request=request,
                name="device_details.html",
                context={
                    "device": device_data,
                    "config": device_config,
                    "device_type": entry.device_type,
                    "device_id": device_id,
                },
            )
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in get_device_details: {e}")
            self._raise_execution(str(e), {"operation": "get_device_details", "device_id": device_id})
    
    async def get_device_config(self, device_id: int):
        """Get device running configuration"""
        try:
            entry = self._resolve(device_id)
            config = await entry.driver.get_running_config(entry.container)
            
            return {
                "device_id": device_id,
                "container": entry.container,
                "config": config,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "get_device_config", "device_id": device_id})
    
    async def get_device_routes(self, device_id: int):
        """Get device routing table"""
        try:
            entry = self._resolve(device_id)
            routes = await entry.driver.get_routes(entry.container)
            
            return {
                "device_id": device_id,
                "container": entry.container,
                "routes": routes,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "get_device_routes", "device_id": device_id})
    
    async def get_device_ospf(self, device_id: int):
        """Get OSPF neighbors"""
        try:
            entry = self._resolve(device_id)
            
            if entry.device_type != "router":
                return {
                    "device_id": device_id,
                    "ospf_neighbors": [],
                    "message": "OSPF only available on routers",
                    "timestamp": datetime.now().isoformat()
                }
            
            neighbors = await entry.driver.get_ospf_neighbors(entry.container)
            
            return {
                "device_id": device_id,
                "container": entry.container,
                "ospf_neighbors": neighbors,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "get_device_ospf", "device_id": device_id})

    async def run_network_tests(self, device_id: int, test_type: str = "full"):
        """Run network tests on a device"""
        try:
            entry = self._resolve(device_id)

            allowed = ["full", "ping", "interfaces", "ospf", "routes"]
            if test_type not in allowed:
                self._raise_validation(
                    f"Invalid test_type. Use one of: {allowed}",
                    {"test_type": test_type, "allowed": allowed}
                )

            result = await self.ansible.run_network_test_playbook(
                "connectivity-test.yml",
                {
                    "device_container": entry.container,
                    "test_operation": test_type
                }
            )

            return {
                "success": result.get("success", False),
                "device_id": device_id,
                "container": entry.container,
                "test_type": test_type,
                "summary": result.get("summary", {}),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(
                str(e),
                {"operation": "run_network_tests", "device_id": device_id, "test_type": test_type}
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    async def _get_switch_details(self, driver, container: str) -> dict[str, Any]:
        """Get switch-specific details via the driver's underlying client."""
        # FrrDriver exposes .frr for switch-specific methods not yet in the interface
        if hasattr(driver, 'frr') and hasattr(driver.frr, 'get_switch_details'):
            return await driver.frr.get_switch_details(container)
        return {}