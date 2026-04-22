import asyncio
from typing import Any, cast

import pytest
from fastapi import HTTPException

from app.services.interface_management import InterfaceManagement
from app.services.drivers.base import DeviceDriver
from app.services.drivers.registry import DriverRegistry


def _detail_dict(exc: HTTPException) -> dict[str, Any]:
    # FastAPI types detail broadly; narrow to dict for typed assertions.
    return cast(dict[str, Any], exc.detail)


class FakeAnsibleClient:
    def __init__(self, acl_result=None):
        self._acl_result = acl_result or {}

    async def run_acl_playbook(self, playbook_name: str, variables: dict) -> dict:
        return self._acl_result


class FakeDriver(DeviceDriver):
    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        return {"status": "UP"}

    async def get_running_config(self, device_id: str) -> dict[str, Any]:
        return {"success": True, "config": ""}

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


def make_service(acl_result=None):
    fake_ansible = FakeAnsibleClient(acl_result=acl_result)
    return InterfaceManagement(_make_registry(), fake_ansible)


def test_remove_acl_success_sets_passed_final_status():
    svc = make_service(
        acl_result={
            "success": True,
            "return_code": 0,
            "stdout": "ACL LAB-IN removed from frr-switch1",
            "summary": {"status": "PASSED"},
        }
    )

    result = asyncio.run(
        svc.remove_acl(
            3,
            {
                "interface": "eth1",
                "direction": "in",
                "acl_name": "LAB-IN",
            },
        )
    )

    assert result["success"] is True
    assert result["final_status"] == "PASSED"
    assert result["stages"]["verify"]["status"] == "passed"
    assert result["stages"]["apply"]["status"] == "passed"


def test_remove_acl_verify_failure_when_marker_missing():
    svc = make_service(
        acl_result={
            "success": True,
            "return_code": 0,
            "stdout": "playbook completed but marker is absent",
            "summary": {"status": "PASSED"},
        }
    )

    result = asyncio.run(
        svc.remove_acl(
            3,
            {
                "interface": "eth1",
                "direction": "in",
                "acl_name": "LAB-IN",
            },
        )
    )

    assert result["success"] is False
    assert result["final_status"] == "FAILED"
    assert result["stages"]["verify"]["status"] == "failed"
    assert "ACL LAB-IN removed" in result["stages"]["verify"]["details"]["missing_markers"]


def test_remove_acl_invalid_interface_returns_validation_error():
    svc = make_service(
        acl_result={
            "success": True,
            "return_code": 0,
            "stdout": "ACL LAB-IN removed from frr-switch1",
            "summary": {"status": "PASSED"},
        }
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            svc.remove_acl(
                3,
                {
                    "interface": "bad0",
                    "direction": "in",
                    "acl_name": "LAB-IN",
                },
            )
        )

    err = exc.value
    detail = _detail_dict(err)
    assert err.status_code == 400
    assert detail["error_type"] == "validation_error"
    assert detail["message"] == "Invalid interface name"


def test_remove_acl_unknown_device_returns_not_found_error():
    svc = make_service(
        acl_result={
            "success": True,
            "return_code": 0,
            "stdout": "ACL LAB-IN removed from frr-switch1",
            "summary": {"status": "PASSED"},
        }
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            svc.remove_acl(
                99,
                {
                    "interface": "eth1",
                    "direction": "in",
                    "acl_name": "LAB-IN",
                },
            )
        )

    err = exc.value
    detail = _detail_dict(err)
    context = cast(dict[str, Any], detail["context"])
    assert err.status_code == 400
    assert detail["error_type"] == "not_found"
    assert context["device_id"] == 99