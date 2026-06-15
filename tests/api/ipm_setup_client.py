"""
Подготовка бэкенда для тестирования ИПМ через Web Client Web API (порт 8089).

Цикл:
1. PUT /api/Personnel — персонал с табельным номером и WorkerId
2. POST /api/AddMachine — станок с протоколом Universal (Type 23)
3. PUT /api/MachineProtocols — разблокировка протокола (IsBlocked=false)
4. PATCH /api/WorkerRolesOnMachines — назначение роли работнику на станке
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class IpmBackendSetup:
    suffix: str
    tab_number: str
    personnel_id: int
    worker_id: int
    machine_id: int
    machine_code: str
    machine_short_name: str
    protocol_id: int
    protocol_ip: str
    worker_role_id: int


def _protocol_ip_from_suffix(suffix: str) -> str:
    oct3 = int(suffix[-3:]) % 250 + 1
    return f"10.{int(suffix[:2]) % 250}.{int(suffix[2:4]) % 250}.{oct3}"


def prepare_ipm_backend(
    *,
    base_url: str,
    user_id: str = "1",
    dept_id: int = 2,
    worker_role_id: int = 1,
    protocol_type: int = 23,
    timeout_sec: float = 30,
) -> IpmBackendSetup:
    headers = {
        "user-id": user_id,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    suffix = str(int(time.time()))[-8:]
    tab_number = suffix
    protocol_ip = _protocol_ip_from_suffix(suffix)

    person_body = {
        "LastName": f"WR{suffix}",
        "FirstName": "Auto",
        "IsMaster": False,
        "Code": f"W{suffix}",
        "Name": f"Auto WR {suffix}",
        "Number": tab_number,
        "IsCreateWorker": True,
    }
    person_resp = requests.put(
        f"{base_url}/api/Personnel",
        json=person_body,
        headers=headers,
        timeout=timeout_sec,
    )
    person_resp.raise_for_status()
    person_data = person_resp.json()
    if not person_data.get("Success"):
        raise RuntimeError(f"Personnel create failed: {person_data}")
    person = person_data["Payload"]
    worker_id = person["WorkerId"]
    if worker_id is None:
        raise RuntimeError("WorkerId is null — проверьте IsCreateWorker=true")

    before_ids = {
        item["ID"]
        for item in requests.get(
            f"{base_url}/api/MachineProtocols",
            headers=headers,
            timeout=timeout_sec,
        ).json()
    }

    machine_body = {
        "IsMachineCopyMode": False,
        "List": [
            {
                "ShortName": f"M{suffix}",
                "FullName": f"Auto Machine {suffix}",
                "DeptId": dept_id,
                "Position": 0,
                "MachineNum": f"M{suffix}",
                "Code": f"MC{suffix}",
                "Protocols": [
                    {
                        "Type": protocol_type,
                        "Name": "Universal",
                        "IPAddress": protocol_ip,
                    }
                ],
            }
        ],
    }
    machine_resp = requests.post(
        f"{base_url}/api/AddMachine",
        json=machine_body,
        headers=headers,
        timeout=timeout_sec,
    )
    machine_resp.raise_for_status()
    machine_data = machine_resp.json()
    if not machine_data.get("IsSuccess"):
        raise RuntimeError(f"Machine create failed: {machine_data}")

    machine = machine_data["SuccessfullyCreated"][0]["Value"]
    machine_id = machine["Id"]

    after = requests.get(
        f"{base_url}/api/MachineProtocols",
        headers=headers,
        timeout=timeout_sec,
    ).json()
    new_protocols = [item for item in after if item["ID"] not in before_ids]
    if not new_protocols:
        new_protocols = [item for item in after if item.get("IPAddress") == protocol_ip]
    if not new_protocols:
        raise RuntimeError("Protocol for new machine was not found")

    protocol_id = new_protocols[0]["ID"]
    proto = requests.get(
        f"{base_url}/api/MachineProtocols/{protocol_id}",
        headers=headers,
        timeout=timeout_sec,
    ).json()

    unlock_body = {
        "MachineProtocolTypeID": proto["MachineProtocolTypeID"],
        "DefaultProtocol": {
            "ID": proto["ID"],
            "MachineId": machine_id,
            "MachineProtocolTypeID": proto["MachineProtocolTypeID"],
            "IsBlocked": False,
            "IPAddress": proto.get("IPAddress") or protocol_ip,
            "Code": proto.get("Code") or "",
            "EdgeId": proto.get("EdgeId"),
            "PollingRate": proto.get("PollingRate") or 1000,
            "Description": proto.get("Description") or "",
            "DeviceId": proto.get("DeviceId"),
        },
    }
    unlock_resp = requests.put(
        f"{base_url}/api/MachineProtocols",
        json=unlock_body,
        headers=headers,
        timeout=timeout_sec,
    )
    if unlock_resp.status_code != 200:
        raise RuntimeError(f"Protocol unlock failed: {unlock_resp.text}")

    role_body = {
        "WorkerRoles": [
            {
                "ID": 0,
                "WorkerRoleId": worker_role_id,
                "MachineID": machine_id,
                "WorkerID": worker_id,
            }
        ]
    }
    role_resp = requests.patch(
        f"{base_url}/api/WorkerRolesOnMachines",
        json=role_body,
        headers=headers,
        timeout=timeout_sec,
    )
    if role_resp.status_code != 200:
        raise RuntimeError(f"Worker role assign failed: {role_resp.text}")

    return IpmBackendSetup(
        suffix=suffix,
        tab_number=tab_number,
        personnel_id=person["Id"],
        worker_id=worker_id,
        machine_id=machine_id,
        machine_code=machine.get("Code") or f"MC{suffix}",
        machine_short_name=machine.get("ShortName") or f"M{suffix}",
        protocol_id=protocol_id,
        protocol_ip=protocol_ip,
        worker_role_id=worker_role_id,
    )
