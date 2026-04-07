"""Registry that maps device IDs to their driver and metadata.

Replaces the duplicated device_map dicts that were copy-pasted into
every service method.  Adding a new device (or a new vendor) is now
a single registration call.
"""

from typing import Any
from app.services.drivers.base import DeviceDriver


class DeviceEntry:
    """Metadata for one registered device."""

    __slots__ = ("device_id", "name", "container", "device_type", "ip", "driver")

    def __init__(
        self,
        device_id: int,
        name: str,
        container: str,
        device_type: str,
        ip: str,
        driver: DeviceDriver,
    ):
        self.device_id = device_id
        self.name = name
        self.container = container
        self.device_type = device_type
        self.ip = ip
        self.driver = driver


class DriverRegistry:
    """Central lookup for devices and their drivers."""

    def __init__(self) -> None:
        self._devices: dict[int, DeviceEntry] = {}

    def register(
        self,
        device_id: int,
        name: str,
        container: str,
        device_type: str,
        ip: str,
        driver: DeviceDriver,
    ) -> None:
        self._devices[device_id] = DeviceEntry(
            device_id=device_id,
            name=name,
            container=container,
            device_type=device_type,
            ip=ip,
            driver=driver,
        )

    def get(self, device_id: int) -> DeviceEntry | None:
        return self._devices.get(device_id)

    def all_devices(self) -> list[DeviceEntry]:
        return list(self._devices.values())

    def get_driver(self, device_id: int) -> DeviceDriver | None:
        entry = self._devices.get(device_id)
        return entry.driver if entry else None
