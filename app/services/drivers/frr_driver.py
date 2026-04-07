"""FRR device driver — implements DeviceDriver for FRRouting containers.

Wraps the existing FRRClient methods behind the vendor-neutral interface
so the service layer never touches Docker / vtysh directly.
"""

from typing import Any
from app.services.drivers.base import DeviceDriver
from app.services.frr_client import FRRClient


class FrrDriver(DeviceDriver):
    """Driver for FRRouting containers managed via Docker exec + vtysh."""

    def __init__(self, frr_client: FRRClient | None = None):
        self.frr = frr_client or FRRClient()

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        return await self.frr.get_device_info(device_id)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    async def get_running_config(self, device_id: str) -> dict[str, Any]:
        return await self.frr.get_running_config(device_id)

    # ------------------------------------------------------------------
    # Interfaces
    # ------------------------------------------------------------------
    async def get_interfaces(self, device_id: str) -> list[dict[str, Any]]:
        return await self.frr.get_interface_details(device_id)

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    async def get_routes(self, device_id: str) -> dict[str, Any]:
        return await self.frr.get_routing_table(device_id)

    # ------------------------------------------------------------------
    # OSPF
    # ------------------------------------------------------------------
    async def get_ospf_neighbors(self, device_id: str) -> list[dict[str, Any]]:
        info = await self.frr.get_device_info(device_id)
        return info.get("ospf_neighbors", [])

    # ------------------------------------------------------------------
    # VLANs
    # ------------------------------------------------------------------
    async def get_vlans(self, device_id: str) -> list[dict[str, Any]]:
        return await self.frr.get_device_vlans(device_id)

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------
    async def test_connection(self, device_id: str) -> dict[str, Any]:
        return await self.frr.test_connection(device_id)
