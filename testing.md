# 1 See real interface mapping per switch
(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch1 ip -br a
lo               UNKNOWN        127.0.0.1/8 ::1/128 
eth0@if38        UP             172.16.10.2/24 
eth1@if41        UP             172.16.20.2/24 
eth2@if43        UP             10.10.1.30/24 
(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch2 ip -br a
lo               UNKNOWN        127.0.0.1/8 ::1/128 
eth0@if39        UP             10.10.1.40/24 
eth1@if40        UP             172.16.10.3/24 
eth2@if42        UP             172.16.20.3/24

# 2 Confirm FRR sees same interfaces

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch1 vtysh -c "show interface brief"
Interface       Status  VRF             Addresses
---------       ------  ---             ---------
eth0            up      default         172.16.10.2/24
eth1            up      default         172.16.20.2/24
eth2            up      default         10.10.1.30/24
lo              up      default         

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch2 vtysh -c "show interface brief"
Interface       Status  VRF             Addresses
---------       ------  ---             ---------
eth0            up      default         10.10.1.40/24
eth1            up      default         172.16.10.3/24
eth2            up      default         172.16.20.3/24
lo              up      default         

# 3 Provision chosen interface on SW1 (edit interface/ip as needed)

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ curl -s -X POST "http://localhost:8000/api/devices/3/interfaces/provision" \
  -H "Content-Type: application/json" \
  -d '{
    "interface":"eth1",
    "ip_cidr":"172.16.10.2/24",
    "description":"Transit-1 SW1"
  }' | jq
{
  "success": true,
  "device_id": 3,
  "container": "frr-switch1",
  "interface": "eth1",
  "ip_cidr": "172.16.10.2/24",
  "summary": {
    "status": "PASSED",
    "recap_line": "localhost                  : ok=5    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0",
    "metrics": {
      "ok": 5,
      "changed": 2,
      "unreachable": 0,
      "failed": 0,
      "skipped": 1,
      "rescued": 0,
      "ignored": 0
    },
    "has_stderr": true
  },
  "result": {
    "success": true,
    "stdout": "\nPLAY [Provision Interface on FRR Device] ***************************************\n\nTASK [Validate interface exists on device] *************************************\nchanged: [localhost]\n\nTASK [Configure interface IP and admin state] **********************************\nchanged: [localhost]\n\nTASK [Configure static route if requested] *************************************\nskipping: [localhost]\n\nTASK [Verify interface config] *************************************************\nok: [localhost]\n\nTASK [Verify route config] *****************************************************\nok: [localhost]\n\nTASK [Display verification snapshot] *******************************************\nok: [localhost] => {\n    \"msg\": \"Interface verification:\\nInterface eth1 is up, line protocol is up\\\\n  Link ups:       0    last: (never)\\\\n  Link downs:     0    last: (never)\\\\n  vrf: default\\\\n  Description: Transit-1 SW1\\\\n  index 3 metric 0 mtu 1500 speed 10000 \\\\n  flags: <UP,BROADCAST,RUNNING,MULTICAST>\\\\n  Type: Ethernet\\\\n  HWaddr: a6:8e:57:a4:22:49\\\\n  inet 172.16.10.2/24\\\\n  inet 172.16.20.2/24\\\\n  Interface Type VETH\\n\\nRoute verification (first lines):\\nCodes: K - kernel route, C - connected, S - static, R - RIP,\\\\n       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,\\\\n       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,\\\\n       f - OpenFabric,\\\\n       > - selected route, * - FIB route, q - queued, r - rejected, b - backup\\\\n       t - trapped, o - offload failure\\\\n\\\\nK>* 0.0.0.0/0 [0/0] via 10.10.1.1, eth2, 02:24:02\\\\nC>* 10.10.1.0/24 is directly connected, eth2, 02:24:02\\\\nC * 172.16.10.0/24 is directly connected, eth1, 00:00:01\\\\nC>* 172.16.10.0/24 is directly connected, eth0, 02:24:02\\\\nC>* 172.16.20.0/24 is directly connected, eth1, 02:24:02\"\n}\n\nPLAY RECAP *********************************************************************\nlocalhost                  : ok=5    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0   \n\n",
    "stderr": "[WARNING]: provided hosts list is empty, only localhost is available. Note that\nthe implicit localhost does not match 'all'\n",
    "return_code": 0,
    "command": "ansible-playbook /home/dims/projects/network-monitoring/ansible/playbooks/interface-provision.yml -e {\"device_container\": \"frr-switch1\", \"interface\": \"eth1\", \"ip_cidr\": \"172.16.10.2/24\", \"if_description\": \"Transit-1 SW1\", \"route_prefix\": \"\", \"route_next_hop\": \"\"}",
    "summary": {
      "status": "PASSED",
      "recap_line": "localhost                  : ok=5    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0",
      "metrics": {
        "ok": 5,
        "changed": 2,
        "unreachable": 0,
        "failed": 0,
        "skipped": 1,
        "rescued": 0,
        "ignored": 0
      },
      "has_stderr": true
    }
  },
  "timestamp": "2026-03-20T23:40:01.816027"
}

# 4 Provision matching interface on SW2

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ curl -s -X POST "http://localhost:8000/api/devices/4/interfaces/provision" \
  -H "Content-Type: application/json" \
  -d '{
    "interface":"eth1",
    "ip_cidr":"172.16.10.3/24",
    "description":"Transit-1 SW2"
  }' | jq
{
  "success": true,
  "device_id": 4,
  "container": "frr-switch2",
  "interface": "eth1",
  "ip_cidr": "172.16.10.3/24",
  "summary": {
    "status": "PASSED",
    "recap_line": "localhost                  : ok=5    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0",
    "metrics": {
      "ok": 5,
      "changed": 2,
      "unreachable": 0,
      "failed": 0,
      "skipped": 1,
      "rescued": 0,
      "ignored": 0
    },
    "has_stderr": true
  },
  "result": {
    "success": true,
    "stdout": "\nPLAY [Provision Interface on FRR Device] ***************************************\n\nTASK [Validate interface exists on device] *************************************\nchanged: [localhost]\n\nTASK [Configure interface IP and admin state] **********************************\nchanged: [localhost]\n\nTASK [Configure static route if requested] *************************************\nskipping: [localhost]\n\nTASK [Verify interface config] *************************************************\nok: [localhost]\n\nTASK [Verify route config] *****************************************************\nok: [localhost]\n\nTASK [Display verification snapshot] *******************************************\nok: [localhost] => {\n    \"msg\": \"Interface verification:\\nInterface eth1 is up, line protocol is up\\\\n  Link ups:       0    last: (never)\\\\n  Link downs:     0    last: (never)\\\\n  vrf: default\\\\n  Description: Transit-1 SW2\\\\n  index 3 metric 0 mtu 1500 speed 10000 \\\\n  flags: <UP,BROADCAST,RUNNING,MULTICAST>\\\\n  Type: Ethernet\\\\n  HWaddr: 22:c5:f3:38:8a:47\\\\n  inet 172.16.10.3/24\\\\n  Interface Type VETH\\\\n  Interface Slave Type None\\n\\nRoute verification (first lines):\\nCodes: K - kernel route, C - connected, S - static, R - RIP,\\\\n       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,\\\\n       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,\\\\n       f - OpenFabric,\\\\n       > - selected route, * - FIB route, q - queued, r - rejected, b - backup\\\\n       t - trapped, o - offload failure\\\\n\\\\nK>* 0.0.0.0/0 [0/0] via 10.10.1.1, eth0, 02:24:42\\\\nC>* 10.10.1.0/24 is directly connected, eth0, 02:24:42\\\\nC>* 172.16.10.0/24 is directly connected, eth1, 02:24:42\\\\nC>* 172.16.20.0/24 is directly connected, eth2, 02:24:42\"\n}\n\nPLAY RECAP *********************************************************************\nlocalhost                  : ok=5    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0   \n\n",
    "stderr": "[WARNING]: provided hosts list is empty, only localhost is available. Note that\nthe implicit localhost does not match 'all'\n",
    "return_code": 0,
    "command": "ansible-playbook /home/dims/projects/network-monitoring/ansible/playbooks/interface-provision.yml -e {\"device_container\": \"frr-switch2\", \"interface\": \"eth1\", \"ip_cidr\": \"172.16.10.3/24\", \"if_description\": \"Transit-1 SW2\", \"route_prefix\": \"\", \"route_next_hop\": \"\"}",
    "summary": {
      "status": "PASSED",
      "recap_line": "localhost                  : ok=5    changed=2    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0",
      "metrics": {
        "ok": 5,
        "changed": 2,
        "unreachable": 0,
        "failed": 0,
        "skipped": 1,
        "rescued": 0,
        "ignored": 0
      },
      "has_stderr": true
    }
  },
  "timestamp": "2026-03-20T23:40:40.861532"
}

# 5 Validate L3 reachability

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch1 ping -c 3 172.16.10.3
PING 172.16.10.3 (172.16.10.3): 56 data bytes
64 bytes from 172.16.10.3: seq=0 ttl=64 time=3.190 ms
64 bytes from 172.16.10.3: seq=1 ttl=64 time=0.083 ms
64 bytes from 172.16.10.3: seq=2 ttl=64 time=0.082 ms

--- 172.16.10.3 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.082/1.118/3.190 ms

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch2 ping -c 3 172.16.10.2
PING 172.16.10.2 (172.16.10.2): 56 data bytes
64 bytes from 172.16.10.2: seq=0 ttl=64 time=0.288 ms
64 bytes from 172.16.10.2: seq=1 ttl=64 time=0.076 ms
64 bytes from 172.16.10.2: seq=2 ttl=64 time=0.084 ms

--- 172.16.10.2 ping statistics ---
3 packets transmitted, 3 packets received, 0% packet loss
round-trip min/avg/max = 0.076/0.149/0.288 ms

# 6 Validate saved running config view

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch1 vtysh -c "show running-config"
Building configuration...

Current configuration:
!
frr version 8.4_git
frr defaults traditional
hostname switch1
domainname localdomain
no ipv6 forwarding
service integrated-vtysh-config
!
interface eth1
 description Transit-1 SW1  
 ip address 172.16.10.2/24
exit
!
end

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch2 vtysh -c "show running-config"
Building configuration...

Current configuration:
!
frr version 8.4_git
frr defaults traditional
hostname switch2
domainname localdomain
no ipv6 forwarding
service integrated-vtysh-config
!
interface eth1
 description Transit-1 SW2
 ip address 172.16.10.3/24
exit
!
end


# ACL TESTING

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ curl -s -X POST "http://localhost:8000/api/devices/3/acl/apply" \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "eth1",
    "direction": "in",
    "acl_name": "LAB-IN",
    "acl_lines": [
      "ip saddr 172.16.10.0/24 accept",
      "counter drop"
    ]
  }' | jq
{
  "success": false,
  "device_id": 3,
  "container": "frr-switch1",
  "interface": "eth1",
  "direction": "in",
  "acl_name": "LAB-IN",
  "summary": {
    "status": "FAILED",
    "recap_line": "localhost                  : ok=1    changed=1    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0",
    "metrics": {
      "ok": 1,
      "changed": 1,
      "unreachable": 0,
      "failed": 1,
      "skipped": 0,
      "rescued": 0,
      "ignored": 0
    },
    "has_stderr": true
  },
  "result": {
    "success": false,
    "stdout": "\nPLAY [Apply nftables ACL on Linux data plane] **********************************\n\nTASK [Validate interface exists] ***********************************************\nchanged: [localhost]\n\nTASK [Validate nft command exists] *********************************************\nfatal: [localhost]: FAILED! => {\"changed\": true, \"cmd\": \"docker exec frr-switch1 sh -lc \\\"command -v nft\\\"\", \"delta\": \"0:00:00.099550\", \"end\": \"2026-03-25 16:43:49.351132\", \"failed_when_result\": true, \"msg\": \"non-zero return code\", \"rc\": 127, \"start\": \"2026-03-25 16:43:49.251582\", \"stderr\": \"\", \"stderr_lines\": [], \"stdout\": \"\", \"stdout_lines\": []}\n\nPLAY RECAP *********************************************************************\nlocalhost                  : ok=1    changed=1    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0   \n\n",
    "stderr": "[WARNING]: provided hosts list is empty, only localhost is available. Note that\nthe implicit localhost does not match 'all'\n",
    "return_code": 2,
    "command": "ansible-playbook /home/dims/projects/network-monitoring/ansible/playbooks/apply-acl.yml -e {\"device_container\": \"frr-switch1\", \"interface\": \"eth1\", \"direction\": \"in\", \"acl_name\": \"LAB-IN\", \"acl_lines\": [\"ip saddr 172.16.10.0/24 accept\", \"counter drop\"]}",
    "summary": {
      "status": "FAILED",
      "recap_line": "localhost                  : ok=1    changed=1    unreachable=0    failed=1    skipped=0    rescued=0    ignored=0",
      "metrics": {
        "ok": 1,
        "changed": 1,
        "unreachable": 0,
        "failed": 1,
        "skipped": 0,
        "rescued": 0,
        "ignored": 0
      },
      "has_stderr": true
    }
  },
  "timestamp": "2026-03-25T16:43:49.478932"
}

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec frr-switch1 sh -lc "nft list table inet nm_acl"
sh: nft: not found

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ curl -s -X POST "http://localhost:8000/api/devices/3/acl/remove" \
  -H "Content-Type: application/json" \
  -d '{
    "interface": "eth1",
    "direction": "in",
    "acl_name": "LAB-IN"
  }' | jq
{
  "success": true,
  "device_id": 3,
  "container": "frr-switch1",
  "interface": "eth1",
  "direction": "in",
  "acl_name": "LAB-IN",
  "summary": {
    "status": "PASSED",
    "recap_line": "localhost                  : ok=5    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0",
    "metrics": {
      "ok": 5,
      "changed": 1,
      "unreachable": 0,
      "failed": 0,
      "skipped": 0,
      "rescued": 0,
      "ignored": 0
    },
    "has_stderr": true
  },
  "result": {
    "success": true,
    "stdout": "\nPLAY [Remove nftables ACL on Linux data plane] *********************************\n\nTASK [Validate interface exists] ***********************************************\nchanged: [localhost]\n\nTASK [Set chain and ACL tag by direction] **************************************\nok: [localhost]\n\nTASK [Remove rules by ACL tag (safe if missing)] *******************************\nok: [localhost]\n\nTASK [Verify chain after removal] **********************************************\nok: [localhost]\n\nTASK [Show removal verification] ***********************************************\nok: [localhost] => {\n    \"msg\": \"ACL LAB-IN removed from frr-switch1\\nDirection: in\\nChain: input\\n\\nChain state:\\n\"\n}\n\nPLAY RECAP *********************************************************************\nlocalhost                  : ok=5    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0   \n\n",
    "stderr": "[WARNING]: provided hosts list is empty, only localhost is available. Note that\nthe implicit localhost does not match 'all'\n",
    "return_code": 0,
    "command": "ansible-playbook /home/dims/projects/network-monitoring/ansible/playbooks/remove-acl.yml -e {\"device_container\": \"frr-switch1\", \"interface\": \"eth1\", \"direction\": \"in\", \"acl_name\": \"LAB-IN\"}",
    "summary": {
      "status": "PASSED",
      "recap_line": "localhost                  : ok=5    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0",
      "metrics": {
        "ok": 5,
        "changed": 1,
        "unreachable": 0,
        "failed": 0,
        "skipped": 0,
        "rescued": 0,
        "ignored": 0
      },
      "has_stderr": true
    }
  },
  "timestamp": "2026-03-25T16:44:26.992020"
}

# Remove ACL test

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ curl -s -X POST "http://localhost:8000/api/devices/3/acl/remove" \
  -H "Content-Type: application/json" \
  -d '{"interface":"eth1","direction":"in","acl_name":"LAB-IN"}' \
  | jq '.success, .summary'
true
{
  "status": "PASSED",
  "recap_line": "localhost                  : ok=8    changed=3    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0",
  "metrics": {
    "ok": 8,
    "changed": 3,
    "unreachable": 0,
    "failed": 0,
    "skipped": 1,
    "rescued": 0,
    "ignored": 0
  },
  "has_stderr": true
}

(.venv) dims@LAPTOP-KQR4014L:~/projects/network-monitoring$ docker exec -u 0 frr-switch1 sh -lc 'nft -a list chain inet nm_acl input | grep nm_acl_LAB-IN || echo ACL tag removed'
ACL tag removed


# dummy / current test
