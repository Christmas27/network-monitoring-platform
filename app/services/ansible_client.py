import subprocess
import json
from pathlib import Path
from typing import Dict, Any
import logging
import re

logger = logging.getLogger(__name__)


class AnsibleClient:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.playbook_path = self.project_root / "ansible" / "playbooks"
        self.inventory_path = self.project_root / "ansible" / "inventory" / "hosts.yml"

    def _run_playbook_sync(self, playbook_name: str, variables: dict, timeout: int = 90) -> dict:
        playbook = self.playbook_path / playbook_name
        cmd = ["ansible-playbook", str(playbook), "-e", json.dumps(variables)]

        if not playbook.exists():
            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "command": " ".join(cmd),
                "summary": {"status": "FAILED", "reason": "PLAYBOOK_NOT_FOUND"},
                "error_type": "not_found",
                "error_message": f"Playbook not found: {playbook}",
            }

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            summary = self._extract_ansible_summary(result.stdout, result.stderr, result.returncode)
            failed = result.returncode != 0

            return {
                "success": not failed,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "summary": summary,
                "error_type": "execution_error" if failed else None,
                "error_message": "Playbook execution failed" if failed else None,
            }

        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "return_code": None,
                "stdout": e.stdout or "",
                "stderr": e.stderr or "",
                "command": " ".join(cmd),
                "summary": {"status": "FAILED", "reason": "TIMEOUT"},
                "error_type": "timeout",
                "error_message": f"Playbook timed out after {timeout}s",
            }

        except Exception as e:
            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "command": " ".join(cmd),
                "summary": {"status": "FAILED", "reason": "EXCEPTION"},
                "error_type": "execution_error",
                "error_message": str(e),
            }

    async def manage_interface(self, device_id: int, interface_name: str, action: str) -> Dict[str, Any]:
        device_mapping = {1: "router1", 2: "router2"}
        if device_id not in device_mapping:
            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "command": "",
                "summary": {"status": "FAILED", "reason": "INVALID_DEVICE"},
                "error_type": "validation_error",
                "error_message": f"Device {device_id} not found",
            }

        host = device_mapping[device_id]
        playbook = self.playbook_path / "interface-control.yml"

        if not playbook.exists():
            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "command": "",
                "summary": {"status": "FAILED", "reason": "PLAYBOOK_NOT_FOUND"},
                "error_type": "not_found",
                "error_message": f"Playbook not found: {playbook}",
            }

        if not self.inventory_path.exists():
            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "command": "",
                "summary": {"status": "FAILED", "reason": "INVENTORY_NOT_FOUND"},
                "error_type": "not_found",
                "error_message": f"Inventory not found: {self.inventory_path}",
            }

        cmd = [
            "ansible-playbook",
            str(playbook),
            "-i",
            str(self.inventory_path),
            "--limit",
            host,
            "-e",
            f"interface={interface_name}",
            "-e",
            f"action={action}",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60,
            )

            summary = self._extract_ansible_summary(result.stdout, result.stderr, result.returncode)

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "summary": summary,
                "error_type": None if result.returncode == 0 else "execution_error",
                "error_message": None if result.returncode == 0 else "Playbook execution failed",
                "action": action,
                "interface": interface_name,
                "device_id": device_id,
            }

        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "return_code": None,
                "stdout": e.stdout or "",
                "stderr": e.stderr or "",
                "command": " ".join(cmd),
                "summary": {"status": "FAILED", "reason": "TIMEOUT"},
                "error_type": "timeout",
                "error_message": "Interface operation timed out",
                "action": action,
                "interface": interface_name,
                "device_id": device_id,
            }

        except Exception as e:
            return {
                "success": False,
                "return_code": None,
                "stdout": "",
                "stderr": "",
                "command": " ".join(cmd),
                "summary": {"status": "FAILED", "reason": "EXCEPTION"},
                "error_type": "execution_error",
                "error_message": str(e),
                "action": action,
                "interface": interface_name,
                "device_id": device_id,
            }

    async def get_playbook_status(self) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                ["ansible", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            return {
                "ansible_installed": result.returncode == 0,
                "ansible_version": result.stdout.split("\n")[0] if result.returncode == 0 else None,
                "playbook_exists": (self.playbook_path / "interface_management.yml").exists(),
                "inventory_exists": self.inventory_path.exists(),
                "project_root": str(self.project_root),
            }
        except Exception as e:
            return {"error": str(e), "ansible_installed": False}

    async def run_vlan_playbook(self, playbook_name: str, variables: dict) -> dict:
        return self._run_playbook_sync(playbook_name, variables, timeout=30)

    async def run_interface_playbook(self, playbook_name: str, variables: dict) -> dict:
        return self._run_playbook_sync(playbook_name, variables, timeout=60)

    async def run_network_test_playbook(self, playbook_name: str, variables: dict) -> dict:
        return self._run_playbook_sync(playbook_name, variables, timeout=90)

    async def run_interface_provision_playbook(self, playbook_name: str, variables: dict) -> dict:
        return self._run_playbook_sync(playbook_name, variables, timeout=90)

    async def run_acl_playbook(self, playbook_name: str, variables: dict) -> dict:
        return self._run_playbook_sync(playbook_name, variables, timeout=90)

    def _extract_ansible_summary(self, stdout: str, stderr: str, return_code: int) -> dict:
        recap_line = ""
        metrics = {
            "ok": 0,
            "changed": 0,
            "unreachable": 0,
            "failed": 0,
            "skipped": 0,
            "rescued": 0,
            "ignored": 0,
        }

        lines = stdout.splitlines() if stdout else []
        recap_idx = -1
        for i, line in enumerate(lines):
            if "PLAY RECAP" in line:
                recap_idx = i
                break

        if recap_idx >= 0:
            for i in range(recap_idx + 1, len(lines)):
                line = lines[i].strip()
                if line and not line.startswith("*"):
                    recap_line = line
                    break

        if recap_line:
            m = re.search(
                r"ok=(\d+)\s+changed=(\d+)\s+unreachable=(\d+)\s+failed=(\d+)\s+skipped=(\d+)\s+rescued=(\d+)\s+ignored=(\d+)",
                recap_line,
            )
            if m:
                metrics = {
                    "ok": int(m.group(1)),
                    "changed": int(m.group(2)),
                    "unreachable": int(m.group(3)),
                    "failed": int(m.group(4)),
                    "skipped": int(m.group(5)),
                    "rescued": int(m.group(6)),
                    "ignored": int(m.group(7)),
                }

        status = "PASSED" if return_code == 0 and metrics["failed"] == 0 and metrics["unreachable"] == 0 else "FAILED"

        return {
            "status": status,
            "recap_line": recap_line,
            "metrics": metrics,
            "has_stderr": bool(stderr and stderr.strip()),
        }

