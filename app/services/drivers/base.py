"""Abstract base class for all device drivers.

Every vendor driver (FRR, Cisco IOS-XE, Arista, etc.) must implement this
interface so the service layer stays vendor-agnostic.
"""

from abc import ABC, abstractmethod
from typing import Any


class DeviceDriver(ABC):
    """Vendor-neutral operations that every network device must support."""

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        """Return device status, type, and basic metadata.

        Must include at minimum: {"status": "UP"|"DOWN"}
        """

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_running_config(self, device_id: str) -> dict[str, Any]:
        """Return the running configuration.

        Must include: {"success": bool, "config": str}
        """

    # ------------------------------------------------------------------
    # Interfaces
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_interfaces(self, device_id: str) -> list[dict[str, Any]]:
        """Return a list of interface dicts.

        Each dict should contain at minimum:
        {"name": str, "status": str, "ip_address": str}
        """

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_routes(self, device_id: str) -> dict[str, Any]:
        """Return the routing table.

        Must include: {"success": bool, "routes": list}
        """

    # ------------------------------------------------------------------
    # OSPF
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_ospf_neighbors(self, device_id: str) -> list[dict[str, Any]]:
        """Return OSPF neighbor list (empty list if not applicable)."""

    # ------------------------------------------------------------------
    # VLANs (switches)
    # ------------------------------------------------------------------
    @abstractmethod
    async def get_vlans(self, device_id: str) -> list[dict[str, Any]]:
        """Return VLAN list (empty list if device is not a switch)."""

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------
    @abstractmethod
    async def test_connection(self, device_id: str) -> dict[str, Any]:
        """Quick reachability / health check.

        Must include: {"reachable": bool}
        """
