import subprocess
import json
from pathlib import Path
from typing import Dict, Any
import logging
import os
import re

logger = logging.getLogger(__name__)

class AnsibleClient:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.playbook_path = self.project_root / "ansible" / "playbooks"
        self.inventory_path = self.project_root / "ansible" / "inventory" / "hosts.yml"
    
    async def manage_interface(self, device_id: int, interface_name: str, action: str) -> Dict[str, Any]:
        """Enable or disable network interface using Ansible"""
        try:
            # Map device_id to ansible host names
            device_mapping = {
                1: "router1", 
                2: "router2"
            }
            
            if device_id not in device_mapping:
                return {"success": False, "error": f"Device {device_id} not found"}
            
            host = device_mapping[device_id]
            playbook = self.playbook_path / "interface-control.yml"
            
            # Verify files exist
            if not playbook.exists():
                return {"success": False, "error": f"Playbook not found: {playbook}"}
            if not self.inventory_path.exists():
                return {"success": False, "error": f"Inventory not found: {self.inventory_path}"}
            
            # Build ansible-playbook command
            cmd = [
                "ansible-playbook",
                str(playbook),
                "-i", str(self.inventory_path),
                "--limit", host,
                "-e", f"interface={interface_name}",
                "-e", f"action={action}",
                "-vvv"
            ]
            
            # DEBUG PRINTS - Add these lines
            print(f"🔧 Working directory: {self.project_root}")
            print(f"🔧 Playbook path: {playbook}")
            print(f"🔧 Inventory path: {self.inventory_path}")
            print(f"🔧 Command: {' '.join(cmd)}")
            
            # Execute playbook
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # DEBUG PRINTS - Add these lines
            print(f"🔧 Return code: {result.returncode}")
            print(f"🔧 STDOUT:\n{result.stdout}")
            print(f"🔧 STDERR:\n{result.stderr}")
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "action": action,
                "interface": interface_name,
                "device_id": device_id,
                "return_code": result.returncode,
                "command": " ".join(cmd)
            }
            
        except Exception as e:
            print(f"🔧 Exception occurred: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_playbook_status(self) -> Dict[str, Any]:
        """Check if Ansible setup is working"""
        try:
            # Test ansible installation
            result = subprocess.run(
                ["ansible", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return {
                "ansible_installed": result.returncode == 0,
                "ansible_version": result.stdout.split('\n')[0] if result.returncode == 0 else None,
                "playbook_exists": (self.playbook_path / "interface_management.yml").exists(),
                "inventory_exists": self.inventory_path.exists(),
                "project_root": str(self.project_root)
            }
        except Exception as e:
            return {"error": str(e), "ansible_installed": False}
    
    async def run_vlan_playbook(self, playbook_name: str, variables: dict) -> dict:
        """Run VLAN management playbooks"""
        try:
            playbook_path = f"ansible/playbooks/{playbook_name}"
            
            # Build ansible-playbook command with variables
            var_string = " ".join([f"-e {key}={value}" for key, value in variables.items()])
            command = f"ansible-playbook {playbook_path} {var_string}"
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_interface_playbook(self, playbook_name: str, variables: dict) -> dict:
        """Run interface management playbooks"""
        try:
            playbook_path = f"ansible/playbooks/{playbook_name}"
            
            # Build ansible-playbook command with variables
            var_string = " ".join([f"-e {key}={value}" for key, value in variables.items()])
            command = f"ansible-playbook {playbook_path} {var_string}"
            
            print(f"Running interface management command: {command}")
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timeout - interface operation took too long"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
            
    async def run_network_test_playbook(self, playbook_name: str, variables: dict) -> dict:
        """Run network test playbooks"""
        try:
            playbook = self.playbook_path / playbook_name
            if not playbook.exists():
                return {"success": False, "error": f"Playbook not found: {playbook}"}

            cmd = ["ansible-playbook", str(playbook)]
            for key, value in variables.items():
                cmd.extend(["-e", f"{key}={value}"])

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=90,
            )

            summary = self._extract_ansible_summary(result.stdout, result.stderr, result.returncode)

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd),
                "summary": summary
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Network test playbook timed out",
                "summary": {
                    "status": "FAILED",
                    "reason": "TIMEOUT"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": {
                    "status": "FAILED",
                    "reason": "EXCEPTION"
                }
            }

    async def run_interface_provision_playbook(self, playbook_name: str, variables: dict) -> dict:
        """Run interface provisioning playbooks"""
        try:
            playbook = self.playbook_path / playbook_name
            if not playbook.exists():
                return {"success": False, "error": f"Playbook not found: {playbook}"}

            # Use JSON extra-vars so values with spaces are preserved safely.
            extra_vars_json = json.dumps(variables)
            cmd = ["ansible-playbook", str(playbook), "-e", extra_vars_json]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=90
            )

            summary = self._extract_ansible_summary(result.stdout, result.stderr, result.returncode)

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd),
                "summary": summary
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Interface provisioning timed out",
                "summary": {"status": "FAILED", "reason": "TIMEOUT"}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": {"status": "FAILED", "reason": "EXCEPTION"}
            }

    async def run_acl_playbook(self, playbook_name: str, variables: dict) -> dict:
        """Run ACL apply/remove playbooks"""
        try:
            playbook = self.playbook_path / playbook_name
            if not playbook.exists():
                return {"success": False, "error": f"Playbook not found: {playbook}"}

            extra_vars_json = json.dumps(variables)
            cmd = ["ansible-playbook", str(playbook), "-e", extra_vars_json]

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=90
            )

            summary = self._extract_ansible_summary(result.stdout, result.stderr, result.returncode)

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode,
                "command": " ".join(cmd),
                "summary": summary
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "ACL playbook timed out",
                "summary": {"status": "FAILED", "reason": "TIMEOUT"}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "summary": {"status": "FAILED", "reason": "EXCEPTION"}
            }

    def _extract_ansible_summary(self, stdout: str, stderr: str, return_code: int) -> dict:
        recap_line = ""
        metrics = {
            "ok": 0,
            "changed": 0,
            "unreachable": 0,
            "failed": 0,
            "skipped": 0,
            "rescued": 0,
            "ignored": 0
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
                recap_line
            )
            if m:
                metrics = {
                    "ok": int(m.group(1)),
                    "changed": int(m.group(2)),
                    "unreachable": int(m.group(3)),
                    "failed": int(m.group(4)),
                    "skipped": int(m.group(5)),
                    "rescued": int(m.group(6)),
                    "ignored": int(m.group(7))
                }

        status = "PASSED" if return_code == 0 and metrics["failed"] == 0 and metrics["unreachable"] == 0 else "FAILED"

        return {
            "status": status,
            "recap_line": recap_line,
            "metrics": metrics,
            "has_stderr": bool(stderr and stderr.strip())
        }

