import asyncio
from typing import Any, cast

import pytest
from fastapi import HTTPException

from app.services.device_management import DeviceManagement
from app.services.drivers.base import DeviceDriver
from app.services.drivers.registry import DriverRegistry


def _detail_dict(exc: HTTPException) -> dict[str, Any]:
    # FastAPI types detail as Any/str, so narrow it for safe dict-style assertions.
    return cast(dict[str, Any], exc.detail)


class FakeAnsibleClient:
    async def run_network_test_playbook(self, playbook_name: str, variables: dict) -> dict:
        return {
            "success": True,
            "summary": {"status": "PASSED"},
            "stdout": "ok",
            "stderr": "",
            "return_code": 0,
        }


class FakeDriver(DeviceDriver):
    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        return {"status": "UP", "ospf_neighbors": []}

    async def get_running_config(self, device_id: str) -> dict[str, Any]:
        return {"success": True, "container": device_id, "config": "dummy"}

    async def get_interfaces(self, device_id: str) -> list[dict[str, Any]]:
        return []

    async def get_routes(self, device_id: str) -> dict[str, Any]:
        return {"success": True, "routes": []}

    async def get_ospf_neighbors(self, device_id: str) -> list[dict[str, Any]]:
        return []

    async def get_vlans(self, device_id: str) -> list[dict[str, Any]]:
        return []

    async def test_connection(self, device_id: str) -> dict[str, Any]:
        return {"success": True}


def _make_registry() -> DriverRegistry:
    reg = DriverRegistry()
    driver = FakeDriver()
    reg.register(1, "Router1", "frr-router1", "router", "10.10.1.10", driver)
    reg.register(2, "Router2", "frr-router2", "router", "10.10.1.20", driver)
    reg.register(3, "Switch1", "frr-switch1", "switch", "10.10.1.30", driver)
    reg.register(4, "Switch2", "frr-switch2", "switch", "10.10.1.40", driver)
    return reg


def make_service():
    return DeviceManagement(_make_registry(), FakeAnsibleClient())


def test_run_network_tests_invalid_type_returns_validation_error():
    svc = make_service()

    with pytest.raises(HTTPException) as exc:
        asyncio.run(svc.run_network_tests(1, "invalid-test"))

    err = exc.value
    detail = _detail_dict(err)
    assert err.status_code == 400
    assert detail["error_type"] == "validation_error"
    assert "Invalid test_type" in str(detail["message"])


def test_run_network_tests_unknown_device_returns_not_found():
    svc = make_service()

    with pytest.raises(HTTPException) as exc:
        asyncio.run(svc.run_network_tests(99, "full"))

    err = exc.value
    detail = _detail_dict(err)
    context = cast(dict[str, Any], detail["context"])
    assert err.status_code == 404
    assert detail["error_type"] == "not_found"
    assert context["device_id"] == 99


def test_get_device_config_unknown_device_returns_not_found():
    svc = make_service()

    with pytest.raises(HTTPException) as exc:
        asyncio.run(svc.get_device_config(99))

    err = exc.value
    detail = _detail_dict(err)
    context = cast(dict[str, Any], detail["context"])
    assert err.status_code == 404
    assert detail["error_type"] == "not_found"
    assert context["device_id"] == 99