from fastapi import HTTPException
from datetime import datetime
from uuid import uuid4
from typing import Any, NoReturn

from app.services.drivers.registry import DriverRegistry

class InterfaceManagement:
    def __init__(self, registry: DriverRegistry, ansible_client):
        self.registry = registry
        self.ansible = ansible_client

    def _get_container_name(self, device_id: int) -> str:
        entry = self.registry.get(device_id)
        if not entry:
            self._raise_not_found("Device not found", {"device_id": device_id}, status_code=400)
        return entry.container

    def _get_driver(self, device_id: int):
        entry = self.registry.get(device_id)
        if not entry:
            self._raise_not_found("Device not found", {"device_id": device_id}, status_code=400)
        return entry.driver

    def _error_detail(self, error_type: str, message: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "error_type": error_type,
            "message": message,
            "context": context or {}
        }

    def _raise_validation(self, message: str, context: dict[str, Any] | None = None) -> NoReturn:
        raise HTTPException(status_code=400, detail=self._error_detail("validation_error", message, context))

    def _raise_not_found(self, message: str, context: dict[str, Any] | None = None, status_code: int = 404) -> NoReturn:
        raise HTTPException(status_code=status_code, detail=self._error_detail("not_found", message, context))

    def _raise_execution(self, message: str, context: dict[str, Any] | None = None) -> NoReturn:
        raise HTTPException(status_code=500, detail=self._error_detail("execution_error", message, context))

    def _validate_interface_name(self, interface_name: object) -> None:
        if not interface_name or not isinstance(interface_name, str):
            self._raise_validation("interface is required")
        if not interface_name.startswith(("eth", "vlan", "lo")):
            self._raise_validation("Invalid interface name", {"interface": interface_name})

    def _validate_direction(self, direction: object) -> None:
        if not isinstance(direction, str):
            self._raise_validation("direction must be 'in' or 'out'", {"direction": direction})
        if direction not in ["in", "out"]:
            self._raise_validation("direction must be 'in' or 'out'", {"direction": direction})

    def _init_transaction(self) -> dict:
        return {
            "transaction_id": str(uuid4()),
            "started_at": datetime.now().isoformat(),
            "stages": {
                "precheck": {"status": "pending"},
                "apply": {"status": "pending"},
                "verify": {"status": "pending"},
                "rollback": {"status": "not_requested"}
            }
        }

    def _finalize_transaction(self, tx: dict, success: bool, summary: dict) -> dict:
        tx["final_status"] = "PASSED" if success else "FAILED"
        tx["finished_at"] = datetime.now().isoformat()
        tx["summary"] = summary
        return tx

    def _verify_markers(self, stdout: object, expected_markers: list[str], check_name: str) -> dict:
        text = stdout if isinstance(stdout, str) else ""
        missing = [m for m in expected_markers if m not in text]
        passed = len(missing) == 0
        return {
            "status": "passed" if passed else "failed",
            "details": {
                "check": check_name,
                "expected_markers": expected_markers,
                "missing_markers": missing,
                "marker_found": passed
            }
        }
        
    async def manage_interface(self, device_id: int, interface_name: str, action: str):
        """Enable/disable/reset network interfaces"""
        try:
            container_name = self._get_container_name(device_id)
            
            # Validate action
            valid_actions = ['enable', 'disable', 'reset']
            if action not in valid_actions:
                self._raise_validation(
                    f"Invalid action. Must be one of: {valid_actions}",
                    {"action": action, "allowed": valid_actions}
                )
            
            self._validate_interface_name(interface_name)
            
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

        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "manage_interface"})

    async def get_interfaces(self, device_id: int):
        """Get all interfaces for a device"""
        try:
            entry = self.registry.get(device_id)
            if not entry:
                self._raise_not_found("Device not found", {"device_id": device_id}, status_code=400)
            
            interfaces = await entry.driver.get_interfaces(entry.container)
            
            return {
                "device_id": device_id,
                "device_name": entry.name,
                "device_type": entry.device_type,
                "container": entry.container,
                "interfaces": interfaces,
                "timestamp": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "get_interfaces"})

    async def provision_interface(self, device_id: int, payload: dict):
        try:
            tx = self._init_transaction()
            container_name = self._get_container_name(device_id)

            interface_name = payload.get("interface")
            ip_cidr = payload.get("ip_cidr")
            description = payload.get("description", "")
            route_prefix = payload.get("route_prefix", "")
            route_next_hop = payload.get("route_next_hop", "")

            self._validate_interface_name(interface_name)
            interface_name_str = interface_name if isinstance(interface_name, str) else ""

            if not ip_cidr or not isinstance(ip_cidr, str):
                self._raise_validation("ip_cidr is required")
            ip_cidr_str = ip_cidr

            if (route_prefix and not route_next_hop) or (route_next_hop and not route_prefix):
                self._raise_validation(
                    "route_prefix and route_next_hop must both be set",
                    {
                        "route_prefix_set": bool(route_prefix),
                        "route_next_hop_set": bool(route_next_hop)
                    }
                )

            tx["stages"]["precheck"] = {
                "status": "passed",
                "details": {
                    "device_id": device_id,
                    "container": container_name,
                    "interface": interface_name
                }
            }

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

            apply_ok = result.get("success", False)
            summary = result.get("summary", {})
            verify_stage = self._verify_markers(
                result.get("stdout", ""),
                [f"Interface {interface_name_str}", ip_cidr_str],
                "interface_provision"
            )
            verify_ok = verify_stage["status"] == "passed"
            overall_ok = apply_ok and verify_ok

            tx["stages"]["apply"] = {
                "status": "passed" if apply_ok else "failed",
                "return_code": result.get("return_code")
            }
            tx["stages"]["verify"] = verify_stage
            tx["stages"]["verify"]["details"]["summary_status"] = summary.get("status")
            tx = self._finalize_transaction(tx, overall_ok, summary)

            return {
                "success": overall_ok,
                "device_id": device_id,
                "container": container_name,
                "interface": interface_name_str,
                "ip_cidr": ip_cidr_str,
                "summary": result.get("summary", {}),
                "result": result,
                "transaction_id": tx["transaction_id"],
                "started_at": tx["started_at"],
                "finished_at": tx["finished_at"],
                "final_status": tx["final_status"],
                "stages": tx["stages"],
                "timestamp": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "provision_interface"})

    async def apply_acl(self, device_id: int, payload: dict):
        try:
            tx = self._init_transaction()
            container_name = self._get_container_name(device_id)

            interface_name = payload.get("interface")
            direction = payload.get("direction", "in")
            acl_name = payload.get("acl_name")
            acl_lines = payload.get("acl_lines", [])

            self._validate_interface_name(interface_name)
            self._validate_direction(direction)

            if not acl_name or not isinstance(acl_name, str):
                self._raise_validation("acl_name is required")

            if not isinstance(acl_lines, list) or len(acl_lines) == 0:
                self._raise_validation("acl_lines must be a non-empty list")

            tx["stages"]["precheck"] = {
                "status": "passed",
                "details": {
                    "device_id": device_id,
                    "container": container_name,
                    "interface": interface_name,
                    "direction": direction,
                    "acl_name": acl_name
                }
            }

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

            apply_ok = result.get("success", False)
            summary = result.get("summary", {})
            verify_stage = self._verify_markers(
                result.get("stdout", ""),
                [f"ACL {acl_name} applied"],
                "acl_apply"
            )
            verify_ok = verify_stage["status"] == "passed"
            overall_ok = apply_ok and verify_ok

            tx["stages"]["apply"] = {
                "status": "passed" if apply_ok else "failed",
                "return_code": result.get("return_code")
            }
            tx["stages"]["verify"] = verify_stage
            tx["stages"]["verify"]["details"]["summary_status"] = summary.get("status")
            tx = self._finalize_transaction(tx, overall_ok, summary)

            return {
                "success": overall_ok,
                "device_id": device_id,
                "container": container_name,
                "interface": interface_name,
                "direction": direction,
                "acl_name": acl_name,
                "summary": result.get("summary", {}),
                "result": result,
                "transaction_id": tx["transaction_id"],
                "started_at": tx["started_at"],
                "finished_at": tx["finished_at"],
                "final_status": tx["final_status"],
                "stages": tx["stages"],
                "timestamp": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "apply_acl"})

    async def remove_acl(self, device_id: int, payload: dict):
        try:
            tx = self._init_transaction()
            container_name = self._get_container_name(device_id)

            interface_name = payload.get("interface")
            direction = payload.get("direction", "in")
            acl_name = payload.get("acl_name")

            self._validate_interface_name(interface_name)
            self._validate_direction(direction)

            if not acl_name or not isinstance(acl_name, str):
                self._raise_validation("acl_name is required")

            tx["stages"]["precheck"] = {
                "status": "passed",
                "details": {
                    "device_id": device_id,
                    "container": container_name,
                    "interface": interface_name,
                    "direction": direction,
                    "acl_name": acl_name
                }
            }

            result = await self.ansible.run_acl_playbook(
                "remove-acl.yml",
                {
                    "device_container": container_name,
                    "interface": interface_name,
                    "direction": direction,
                    "acl_name": acl_name
                }
            )

            apply_ok = result.get("success", False)
            summary = result.get("summary", {})
            verify_stage = self._verify_markers(
                result.get("stdout", ""),
                [f"ACL {acl_name} removed"],
                "acl_remove"
            )
            verify_ok = verify_stage["status"] == "passed"
            overall_ok = apply_ok and verify_ok

            tx["stages"]["apply"] = {
                "status": "passed" if apply_ok else "failed",
                "return_code": result.get("return_code")
            }
            tx["stages"]["verify"] = verify_stage
            tx["stages"]["verify"]["details"]["summary_status"] = summary.get("status")
            tx = self._finalize_transaction(tx, overall_ok, summary)

            return {
                "success": overall_ok,
                "device_id": device_id,
                "container": container_name,
                "interface": interface_name,
                "direction": direction,
                "acl_name": acl_name,
                "summary": result.get("summary", {}),
                "result": result,
                "transaction_id": tx["transaction_id"],
                "started_at": tx["started_at"],
                "finished_at": tx["finished_at"],
                "final_status": tx["final_status"],
                "stages": tx["stages"],
                "timestamp": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            self._raise_execution(str(e), {"operation": "remove_acl"})

