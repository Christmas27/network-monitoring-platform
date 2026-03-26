import requests
import base64
import asyncio
import aiohttp
from aiohttp import ClientTimeout
from typing import Dict, List
import urllib3

# Disable SSL warnings for DevNet sandbox
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DevNetClient:
    def __init__(self):
        # Keep HTTPS as specified in the documentation (port 443)
        self.base_url = "https://devnetsandboxiosxec8k.cisco.com"
        self.username = "christiandimas78" 
        self.password = "B9_bvQVy3Dx3s_"
        # Reduce timeout since shared resource might be busy
        self.timeout = ClientTimeout(total=15, connect=5)
        
    def get_auth_header(self) -> Dict[str, str]:
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/yang-data+json",
            "Content-Type": "application/yang-data+json"
        }
    
    async def test_connection(self) -> Dict:
        """Test RESTCONF root endpoint"""
        url = None
        try:
            # Try the exact RESTCONF root endpoint
            url = f"{self.base_url}/restconf"
            headers = self.get_auth_header()
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False, limit=1),
                timeout=self.timeout
            ) as session:
                async with session.get(url, headers=headers) as response:
                    response_text = await response.text()
                    return {
                        "reachable": True,
                        "status_code": response.status,
                        "sandbox": "Cat8000V Shared",
                        "url_tested": url,
                        "response_text": response_text[:500],
                        "headers": dict(response.headers)
                    }
        except aiohttp.ClientConnectorError as e:
            return {
                "reachable": False,
                "error": f"Connection rejected: {str(e)}",
                "url_tested": url,
                "note": "Shared sandbox may be overloaded or RESTCONF temporarily unavailable"
            }
        except asyncio.TimeoutError:
            return {
                "reachable": False,
                "error": f"Connection timeout",
                "url_tested": url,
                "note": "Shared sandbox may be busy - try again later"
            }
        except Exception as e:
            return {
                "reachable": False,
                "error": str(e),
                "url_tested": url
            }
    
    async def get_device_info(self) -> Dict:
        """Get device info using working RESTCONF endpoints"""
        # Try multiple known working endpoints
        test_endpoints = [
            "/restconf/data/Cisco-IOS-XE-native:native/hostname",
            "/restconf/data/ietf-yang-library:yang-library", 
            "/restconf/data/ietf-interfaces:interfaces-state/interface=GigabitEthernet1",
            "/restconf/data"  # Basic data endpoint
        ]
        
        for endpoint in test_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                headers = self.get_auth_header()
                
                async with aiohttp.ClientSession(
                    connector=aiohttp.TCPConnector(ssl=False), 
                    timeout=self.timeout
                ) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            try:
                                data = await response.json()
                                return {
                                    "status": "UP",
                                    "device_type": "Cat8000V IOS XE",
                                    "hostname": "DevNet-Cat8k",
                                    "response_code": response.status,
                                    "working_endpoint": endpoint,
                                    "data_sample": str(data)[:200] + "..." if len(str(data)) > 200 else str(data)
                                }
                            except:
                                # Even if JSON parsing fails, we got a 200 response
                                return {
                                    "status": "UP",
                                    "device_type": "Cat8000V IOS XE", 
                                    "hostname": "DevNet-Cat8k",
                                    "response_code": response.status,
                                    "working_endpoint": endpoint,
                                    "note": "RESTCONF responding but non-JSON response"
                                }
                        elif response.status == 401:
                            return {
                                "status": "DOWN",
                                "error": "Authentication failed - check username/password",
                                "response_code": response.status
                            }
                        elif response.status == 404:
                            continue  # Try next endpoint
                        else:
                            return {
                                "status": "PARTIAL",
                                "error": f"HTTP {response.status}",
                                "response_code": response.status,
                                "tested_endpoint": endpoint
                            }
            except Exception as e:
                continue  # Try next endpoint
        
        return {
            "status": "DOWN",
            "error": "All RESTCONF endpoints failed",
            "tested_endpoints": test_endpoints
        }
    
    async def get_interfaces(self) -> List[Dict]:
        """Get interface status"""
        try:
            url = f"{self.base_url}/restconf/data/ietf-interfaces:interfaces"
            headers = self.get_auth_header()
            
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=False),
                timeout=self.timeout
            ) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        interfaces = []
                        
                        for interface in data.get('ietf-interfaces:interfaces', {}).get('interface', []):
                            interfaces.append({
                                "name": interface.get('name'),
                                "status": interface.get('oper-status', 'unknown'),
                                "admin_status": interface.get('admin-status', 'unknown'),
                                "type": interface.get('type', 'unknown')
                            })
                        
                        return interfaces[:5]
                    else:
                        return [{"error": f"HTTP {response.status}"}]
        except Exception as e:
            return [{"error": str(e)}]