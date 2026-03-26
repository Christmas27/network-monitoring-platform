from fastapi import HTTPException
from datetime import datetime

# app/services/vlan_management.py  
class VlanManagement:
    def __init__(self, frr_client, ansible_client):
        self.frr = frr_client
        self.ansible = ansible_client
        
    async def create_vlan(self, device_id: int, vlan_data: dict):
        """Create VLAN on switch"""
        try:
            # Only allow VLANs on switches
            switch_map = {3: "frr-switch1", 4: "frr-switch2"}
            
            container_name = switch_map.get(device_id)
            if not container_name:
                raise HTTPException(status_code=400, detail="VLANs can only be created on switches")
            
            # Extract VLAN data
            vlan_id = vlan_data.get("vlan_id")
            vlan_name = vlan_data.get("name", f"VLAN_{vlan_id}")
            
            if not vlan_id:
                raise HTTPException(status_code=400, detail="VLAN ID is required")
            
            # Run ansible playbook
            result = await self.ansible.run_vlan_playbook(
                "create-vlan.yml",
                {
                    "switch_container": container_name,
                    "vlan_number": vlan_id,
                    "vlan_name": vlan_name
                }
            )
            
            return {
                "success": result.get("success", False),
                "message": f"VLAN {vlan_id} created on {container_name}",
                "vlan_id": vlan_id,
                "vlan_name": vlan_name,
                "device_id": device_id,
                "container": container_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def delete_vlan(self, device_id: int, vlan_id: int):
        """Delete VLAN from switch"""
        try:
            switch_map = {3: "frr-switch1", 4: "frr-switch2"}
            
            container_name = switch_map.get(device_id)
            if not container_name:
                raise HTTPException(status_code=400, detail="VLANs can only be deleted from switches")
            
            # Run ansible playbook for VLAN deletion
            result = await self.ansible.run_vlan_playbook(
                "delete-vlan.yml",  # You'll need to create this
                {
                    "switch_container": container_name,
                    "vlan_number": vlan_id
                }
            )
            
            return {
                "success": result.get("success", False),
                "message": f"VLAN {vlan_id} deleted from {container_name}",
                "vlan_id": vlan_id,
                "device_id": device_id,
                "container": container_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_device_vlans(self, device_id: int):
        """Get device VLANs (for switches)"""
        try:
            # Only switches have VLANs
            switch_map = {3: "frr-switch1", 4: "frr-switch2"}
            
            container_name = switch_map.get(device_id)
            if not container_name:
                return {
                    "device_id": device_id,
                    "vlans": [],
                    "message": "VLANs only available on switches",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Get VLANs from FRR
            vlans = await self.frr.get_device_vlans(container_name)
            
            return {
                "device_id": device_id,
                "container": container_name,
                "vlans": vlans,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))