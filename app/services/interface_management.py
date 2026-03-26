from fastapi import HTTPException
from datetime import datetime

class InterfaceManagement:
    def __init__(self, frr_client, ansible_client):
        self.frr = frr_client
        self.ansible = ansible_client
        
    async def manage_interface(self, device_id: int, interface_name: str, action: str):
        """Enable/disable/reset network interfaces"""
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
                raise HTTPException(status_code=400, detail="Device not found")
            
            # Validate action
            valid_actions = ['enable', 'disable', 'reset']
            if action not in valid_actions:
                raise HTTPException(status_code=400, detail=f"Invalid action. Must be one of: {valid_actions}")
            
            # Validate interface name (basic validation)
            if not interface_name.startswith(('eth', 'vlan', 'lo')):
                raise HTTPException(status_code=400, detail="Invalid interface name")
            
            # Run ansible playbook
            result = await self.ansible.run_interface_playbook(
                "interface-control.yml",
                {
                    "device_container": container_name,
                    "interface": interface_name,
                    "operation": action
                }
            )
            
            return {
                "success": result.get("success", False),
                "message": f"Interface {interface_name} {action} command sent to {container_name}",
                "device_id": device_id,
                "interface": interface_name,
                "action": action,
                "container": container_name,
                "ansible_output": result.get("stdout", ""),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_interfaces(self, device_id: int):
        """Get all interfaces for a device"""
        try:
            device_map = {
                1: "frr-router1", 2: "frr-router2", 
                3: "frr-switch1", 4: "frr-switch2"
            }
            
            container_name = device_map.get(device_id)
            if not container_name:
                raise HTTPException(status_code=400, detail="Device not found")
            
            # Get interface details from FRR
            interfaces = await self.frr.get_interface_details(container_name)
            
            # Add device type info
            device_type = "router" if "router" in container_name else "switch"
            
            return {
                "device_id": device_id,
                "device_name": container_name.replace("frr-", "").upper(),
                "device_type": device_type,
                "container": container_name,
                "interfaces": interfaces,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def provision_interface(self, device_id: int, payload: dict):
        try:
            device_map = {
                1: "frr-router1",
                2: "frr-router2",
                3: "frr-switch1",
                4: "frr-switch2"
            }

            container_name = device_map.get(device_id)
            if not container_name:
                raise HTTPException(status_code=400, detail="Device not found")

            interface_name = payload.get("interface")
            ip_cidr = payload.get("ip_cidr")
            description = payload.get("description", "")
            route_prefix = payload.get("route_prefix", "")
            route_next_hop = payload.get("route_next_hop", "")

            if not interface_name or not isinstance(interface_name, str):
                raise HTTPException(status_code=400, detail="interface is required")
            if not ip_cidr or not isinstance(ip_cidr, str):
                raise HTTPException(status_code=400, detail="ip_cidr is required")
            if not interface_name.startswith(("eth", "vlan", "lo")):
                raise HTTPException(status_code=400, detail="Invalid interface name")

            if (route_prefix and not route_next_hop) or (route_next_hop and not route_prefix):
                raise HTTPException(status_code=400, detail="route_prefix and route_next_hop must both be set")

            result = await self.ansible.run_interface_provision_playbook(
                "interface-provision.yml",
                {
                    "device_container": container_name,
                    "interface": interface_name,
                    "ip_cidr": ip_cidr,
                    "if_description": description,
                    "route_prefix": route_prefix,
                    "route_next_hop": route_next_hop
                }
            )

            return {
                "success": result.get("success", False),
                "device_id": device_id,
                "container": container_name,
                "interface": interface_name,
                "ip_cidr": ip_cidr,
                "summary": result.get("summary", {}),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def apply_acl(self, device_id: int, payload: dict):
        try:
            device_map = {
                1: "frr-router1",
                2: "frr-router2",
                3: "frr-switch1",
                4: "frr-switch2"
            }

            container_name = device_map.get(device_id)
            if not container_name:
                raise HTTPException(status_code=400, detail="Device not found")

            interface_name = payload.get("interface")
            direction = payload.get("direction", "in")
            acl_name = payload.get("acl_name")
            acl_lines = payload.get("acl_lines", [])

            if not interface_name or not isinstance(interface_name, str):
                raise HTTPException(status_code=400, detail="interface is required")
            if not interface_name.startswith(("eth", "vlan", "lo")):
                raise HTTPException(status_code=400, detail="Invalid interface name")

            if direction not in ["in", "out"]:
                raise HTTPException(status_code=400, detail="direction must be 'in' or 'out'")

            if not acl_name or not isinstance(acl_name, str):
                raise HTTPException(status_code=400, detail="acl_name is required")

            if not isinstance(acl_lines, list) or len(acl_lines) == 0:
                raise HTTPException(status_code=400, detail="acl_lines must be a non-empty list")

            result = await self.ansible.run_acl_playbook(
                "apply-acl.yml",
                {
                    "device_container": container_name,
                    "interface": interface_name,
                    "direction": direction,
                    "acl_name": acl_name,
                    "acl_lines": acl_lines
                }
            )

            return {
                "success": result.get("success", False),
                "device_id": device_id,
                "container": container_name,
                "interface": interface_name,
                "direction": direction,
                "acl_name": acl_name,
                "summary": result.get("summary", {}),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def remove_acl(self, device_id: int, payload: dict):
        try:
            device_map = {
                1: "frr-router1",
                2: "frr-router2",
                3: "frr-switch1",
                4: "frr-switch2"
            }

            container_name = device_map.get(device_id)
            if not container_name:
                raise HTTPException(status_code=400, detail="Device not found")

            interface_name = payload.get("interface")
            direction = payload.get("direction", "in")
            acl_name = payload.get("acl_name")

            if not interface_name or not isinstance(interface_name, str):
                raise HTTPException(status_code=400, detail="interface is required")
            if not interface_name.startswith(("eth", "vlan", "lo")):
                raise HTTPException(status_code=400, detail="Invalid interface name")

            if direction not in ["in", "out"]:
                raise HTTPException(status_code=400, detail="direction must be 'in' or 'out'")

            if not acl_name or not isinstance(acl_name, str):
                raise HTTPException(status_code=400, detail="acl_name is required")

            result = await self.ansible.run_acl_playbook(
                "remove-acl.yml",
                {
                    "device_container": container_name,
                    "interface": interface_name,
                    "direction": direction,
                    "acl_name": acl_name
                }
            )

            return {
                "success": result.get("success", False),
                "device_id": device_id,
                "container": container_name,
                "interface": interface_name,
                "direction": direction,
                "acl_name": acl_name,
                "summary": result.get("summary", {}),
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

