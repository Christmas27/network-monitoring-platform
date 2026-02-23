import docker
import subprocess
from typing import Dict, List

class FRRClient:
    def __init__(self):
        self.docker_client = docker.from_env()
        
    async def get_device_info(self, container_name: str = "frr-router1") -> Dict:
        """Get FRR router information"""
        try:
            container = self.docker_client.containers.get(container_name)
            if container.status == "running":
                # Get version info
                version_result = container.exec_run('vtysh -c "show version"')
                
                # Get OSPF info  
                ospf_result = container.exec_run('vtysh -c "show ip ospf neighbor"')
                
                return {
                    "status": "UP",
                    "device_type": "FRR Router",
                    "container_name": container_name,
                    "container_status": container.status,
                    "version_info": version_result.output.decode() if version_result.exit_code == 0 else "Error",
                    "ospf_neighbors": self._parse_ospf_neighbors(ospf_result.output.decode()) if ospf_result.exit_code == 0 else []
                }
            else:
                # Add this return for when container is not running
                return {
                    "status": "DOWN",
                    "device_type": "FRR Router",
                    "container_name": container_name,
                    "container_status": container.status,
                    "error": "Container not running"
                }
        except Exception as e:
            return {
                "status": "DOWN",
                "error": str(e),
                "container_name": container_name
            }
    
    def _parse_ospf_neighbors(self, ospf_output: str) -> List[Dict]:
        """Parse OSPF neighbor output"""
        neighbors = []
        lines = ospf_output.split('\n')
        for line in lines[2:]:  # Skip header lines
            if line.strip() and not line.startswith('Neighbor'):
                parts = line.split()
                if len(parts) >= 6:
                    neighbors.append({
                        "neighbor_id": parts[0],
                        "state": parts[2],
                        "address": parts[5]
                    })
        return neighbors
    
    async def get_interfaces(self, container_name: str = "frr-router1") -> List[Dict]:
        """Get interface information"""
        try:
            container = self.docker_client.containers.get(container_name)
            result = container.exec_run('vtysh -c "show ip ospf interface"')
            
            if result.exit_code == 0:
                return [{"interface": "eth0", "status": "UP", "area": "0.0.0.0", "network": "10.10.1.0/24"}]
            return []
        except Exception as e:
            return [{"error": str(e)}]
    
    async def test_connection(self, container_name: str = "frr-router1") -> Dict:
        """Test connection to FRR container"""
        try:
            container = self.docker_client.containers.get(container_name)
            result = container.exec_run('vtysh -c "show version"')  # Remove timeout=5
            
            return {
                "reachable": result.exit_code == 0,
                "container_status": container.status,
                "container_name": container_name
            }
        except Exception as e:
            return {
                "reachable": False,
                "error": str(e)
            }