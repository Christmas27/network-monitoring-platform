# app/services/device_management.py
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Any, NoReturn

templates = Jinja2Templates(directory="app/templates")

class DeviceManagement:
    def __init__(self, frr_client, ansible_client):
        self.frr = frr_client
        self.ansible = ansible_client

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
            device_map = {
                1: {"name": "Router1", "container": "frr-router1", "type": "router"},
                2: {"name": "Router2", "container": "frr-router2", "type": "router"},
                3: {"name": "Switch1", "container": "frr-switch1", "type": "switch"},
                4: {"name": "Switch2", "container": "frr-switch2", "type": "switch"}
            }
            
            for device_id, info in device_map.items():
                try:
                    # Get device status
                    device_info = await self.frr.get_device_info(info["container"])
                    
                    device = {
                        "id": device_id,
                        "name": info["name"],
                        "ip": f"10.10.1.{device_id}0",
                        "device_type": info["type"],
                        "status": device_info.get("status", "DOWN"),
                        "container": info["container"],
                        "ospf_neighbors": len(device_info.get("ospf_neighbors", [])),
                        "last_seen": datetime.now().isoformat()
                    }
                    devices.append(device)
                    
                except Exception as e:
                    print(f"Error getting info for {info['container']}: {e}")
                    # Add device with DOWN status if error
                    devices.append({
                        "id": device_id,
                        "name": info["name"],
                        "ip": f"10.10.1.{device_id}0",
                        "device_type": info["type"],
                        "status": "DOWN",
                        "container": info["container"],
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
        """Get device details page - FIXED METHOD SIGNATURE"""
        try:
            # Device mapping
            device_map = {
                1: "frr-router1", 
                2: "frr-router2", 
                3: "frr-switch1", 
                4: "frr-switch2"
            }
            
            container_name = device_map.get(device_id)
            if not container_name:
                self._raise_not_found("Device not found", {"device_id": device_id})
            
            # Get device information
            device_info = await self.frr.get_device_info(container_name)
            device_config = await self.frr.get_running_config(container_name)
            
            # Build device data object
            device_data = {
                "id": device_id,
                "name": container_name.replace("frr-", "").upper(),
                "ip": f"10.10.1.{device_id}0",
                "container_name": container_name,
                "status": device_info.get("status", "DOWN"),
                "is_router": "router" in container_name,
                "is_switch": "switch" in container_name
            }
            
            # Add router-specific data
            if device_data["is_router"]:
                device_data.update({
                    "ospf_neighbors": device_info.get("ospf_neighbors", []),
                    "interfaces": await self.frr.get_interface_details(container_name),
                    "routing_table": await self.frr.get_routing_table(container_name)
                })
            
            # Add switch-specific data
            elif device_data["is_switch"]:
                device_data.update({
                    "vlans": await self.frr.get_device_vlans(container_name),
                    "ports": device_info.get("ports", []),
                    "switch_info": await self.frr.get_switch_details(container_name)
                })
            
            # Return template with ALL required variables
            return templates.TemplateResponse("device_details.html", {
                "request": request,
                "device": device_data,
                "config": device_config,
                "device_type": "switch" if device_data["is_switch"] else "router",
                "device_id": device_id
            })
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error in get_device_details: {e}")
            self._raise_execution(str(e), {"operation": "get_device_details", "device_id": device_id})
    
    async def get_device_config(self, device_id: int):
        """Get device running configuration"""
        try:
            device_map = {
                1: "frr-router1", 
                2: "frr-router2", 
                3: "frr-switch1", 
                4: "frr-switch2"
            }
            
            container_name = device_map.get(device_id)
            if not container_name:
                self._raise_not_found("Device not found", {"device_id": device_id})
            
            # Get running config from FRR
            config = await self.frr.get_running_config(container_name)
            
            return {
                "device_id": device_id,
                "container": container_name,
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
            device_map = {
                1: "frr-router1", 
                2: "frr-router2", 
                3: "frr-switch1", 
                4: "frr-switch2"
            }
            
            container_name = device_map.get(device_id)
            if not container_name:
                self._raise_not_found("Device not found", {"device_id": device_id})
            
            # Get routing table from FRR
            routes = await self.frr.get_routing_table(container_name)
            
            return {
                "device_id": device_id,
                "container": container_name,
                "routes": routes,
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "get_device_routes", "device_id": device_id})
    
    async def get_device_ospf(self, device_id: int):
        """Get OSPF neighbors (for routers)"""
        try:
            # Only routers have OSPF
            router_map = {1: "frr-router1", 2: "frr-router2"}
            
            container_name = router_map.get(device_id)
            if not container_name:
                return {
                    "device_id": device_id,
                    "ospf_neighbors": [],
                    "message": "OSPF only available on routers",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get device info which includes OSPF neighbors
            device_info = await self.frr.get_device_info(container_name)
            
            return {
                "device_id": device_id,
                "container": container_name,
                "ospf_neighbors": device_info.get("ospf_neighbors", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "get_device_ospf", "device_id": device_id})

    async def run_network_tests(self, device_id: int, test_type: str = "full"):
        """Run network tests on a device"""
        try:
            device_map = {
                1: "frr-router1",
                2: "frr-router2",
                3: "frr-switch1",
                4: "frr-switch2",
            }
            
            container_name = device_map.get(device_id)
            if not container_name:
                self._raise_not_found("Device not found", {"device_id": device_id})

            allowed = ["full", "ping", "interfaces", "ospf", "routes"]
            if test_type not in allowed:
                self._raise_validation(
                    f"Invalid test_type. Use one of: {allowed}",
                    {"test_type": test_type, "allowed": allowed}
                )

            result = await self.ansible.run_network_test_playbook(
                "connectivity-test.yml",
                {
                    "device_container": container_name,
                    "test_operation": test_type
                }
            )

            return {
                "success": result.get("success", False),
                "device_id": device_id,
                "container": container_name,
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