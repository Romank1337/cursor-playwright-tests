"""
Заливает результаты pytest-прогона в Test IT (testit.zyfra.com, проект MDC).

Что делает:
1. Читает JUnit XML с результатами прогона (по умолчанию reports/all-tests-junit.xml).
2. Сопоставляет каждый <testcase> с externalId автотеста через tools/testit_ui_smoke_autotests.json.
3. Создаёт новый TestRun в TMS (POST /api/v2/testRuns), стартует его.
4. Шлёт результаты пачкой (POST /api/v2/testRuns/{id}/testResults).
5. Завершает TestRun (POST /api/v2/testRuns/{id}/complete).

Зачем свой скрипт (а не testit-adapter-pytest):
- На этом сервере у адаптера несовместимость моделей API-клиента (workItemsCount/isFlakyAuto),
  и pip-версии под него нет. См. README, раздел про Test IT.

Запуск:
    python tools/testit_publish_results.py --token <PRIVATE_TOKEN>
    # либо через env:
    set TMS_PRIVATE_TOKEN=...
    python tools/testit_publish_results.py
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib3
import warnings
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_TMS_URL = "https://testit.zyfra.com"
DEFAULT_PROJECT_ID = "4974a48f-041b-44ac-a42e-ebab5bb3a74b"          # MDC
DEFAULT_CONFIGURATION_ID = "ce89a13c-0062-48bd-85c7-e051dfd72fe3"   # Any
DEFAULT_JUNIT_PATH = PROJECT_ROOT / "reports" / "all-tests-junit.xml"
DEFAULT_MAPPING_PATH = PROJECT_ROOT / "tools" / "testit_ui_smoke_autotests.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish pytest results to Test IT")
    parser.add_argument("--token", default=os.getenv("TMS_PRIVATE_TOKEN"))
    parser.add_argument("--tms-url", default=os.getenv("TMS_URL", DEFAULT_TMS_URL))
    parser.add_argument("--project-id", default=os.getenv("TMS_PROJECT_ID", DEFAULT_PROJECT_ID))
    parser.add_argument(
        "--configuration-id",
        default=os.getenv("TMS_CONFIGURATION_ID", DEFAULT_CONFIGURATION_ID),
    )
    parser.add_argument("--junit", default=str(DEFAULT_JUNIT_PATH))
    parser.add_argument("--mapping", default=str(DEFAULT_MAPPING_PATH))
    parser.add_argument(
        "--run-name",
        default=f"UI/Smoke pytest run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
    )
    return parser.parse_args()


def load_mapping(path: Path) -> dict[str, str]:
    items = json.loads(path.read_text(encoding="utf-8"))
    return {it["pytestId"]: it["externalId"] for it in items if "pytestId" in it}


def parse_junit(junit_path: Path, pid_to_eid: dict[str, str]) -> list[dict]:
    tree = ET.parse(junit_path)
    root = tree.getroot()
    suites = root.findall("testsuite") if root.tag != "testsuite" else [root]

    results: list[dict] = []
    now = datetime.now(timezone.utc)
    cursor = now

    for suite in suites:
        for tc in suite.findall("testcase"):
            classname = tc.get("classname", "")
            name = tc.get("name", "")
            name_base = re.sub(r"\[.*\]$", "", name)
            pid = f"{classname}::{name_base}"
            eid = pid_to_eid.get(pid)
            if eid is None:
                print(f"  WARN: no externalId mapping for {pid}", file=sys.stderr)
                continue

            duration_s = float(tc.get("time") or 0.0)
            duration_ms = int(duration_s * 1000)

            outcome = "Passed"
            message = ""
            traces = ""

            if tc.find("failure") is not None:
                outcome = "Failed"
                fail = tc.find("failure")
                message = (fail.get("message") or "").strip()
                traces = (fail.text or "").strip()
            elif tc.find("error") is not None:
                outcome = "Failed"
                err = tc.find("error")
                message = (err.get("message") or "").strip()
                traces = (err.text or "").strip()
            elif tc.find("skipped") is not None:
                outcome = "Skipped"
                skip = tc.find("skipped")
                message = (skip.get("message") or skip.text or "").strip()

            started = cursor
            completed = started + timedelta(milliseconds=duration_ms)
            cursor = completed

            results.append({
                "autoTestExternalId": eid,
                "configurationId": None,  # filled below in main()
                "outcome": outcome,
                "startedOn": started.isoformat().replace("+00:00", "Z"),
                "completedOn": completed.isoformat().replace("+00:00", "Z"),
                "duration": duration_ms,
                "message": message[:4000] if message else "",
                "traces": traces[:8000] if traces else "",
                "attachments": [],
                "stepResults": [],
                "links": [],
            })
    return results


def main() -> int:
    args = parse_args()
    if not args.token:
        print("ERROR: TMS token not provided. Use --token or TMS_PRIVATE_TOKEN env.", file=sys.stderr)
        return 2

    warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)

    junit_path = Path(args.junit)
    if not junit_path.exists():
        print(f"ERROR: JUnit XML not found at {junit_path}", file=sys.stderr)
        print("Run pytest first: python -m pytest tests/ --junitxml=reports/all-tests-junit.xml")
        return 2

    mapping_path = Path(args.mapping)
    if not mapping_path.exists():
        print(f"ERROR: mapping not found at {mapping_path}", file=sys.stderr)
        return 2

    pid_to_eid = load_mapping(mapping_path)
    print(f"Loaded {len(pid_to_eid)} pytestId -> externalId mappings.")

    results = parse_junit(junit_path, pid_to_eid)
    print(f"Parsed {len(results)} testcase results from {junit_path.name}.")

    for r in results:
        r["configurationId"] = args.configuration_id

    session = requests.Session()
    session.verify = False
    session.headers.update({
        "Authorization": f"PrivateToken {args.token}",
        "Content-Type": "application/json",
    })

    # 1) Create TestRun
    create_payload = {
        "projectId": args.project_id,
        "name": args.run_name,
        "description": f"Automatic upload of pytest results from {junit_path.name}",
        "testPlanId": None,
        "launchSource": "pytest",
    }
    print(f"Creating TestRun in project {args.project_id} ...")
    resp = session.post(f"{args.tms_url}/api/v2/testRuns", json=create_payload, timeout=30)
    resp.raise_for_status()
    run = resp.json()
    run_id = run["id"]
    print(f"  TestRun created: id={run_id}")

    # 2) Start TestRun (best effort - some servers return 409 if already in correct state)
    try:
        resp = session.post(f"{args.tms_url}/api/v2/testRuns/{run_id}/start", timeout=30)
        if resp.status_code >= 400:
            print(f"  WARN: start returned {resp.status_code}: {resp.text[:200]}")
    except Exception as e:  # noqa: BLE001
        print(f"  WARN: start failed (ignored): {e}")

    # 3) POST results
    print(f"Uploading {len(results)} results ...")
    upload_url = f"{args.tms_url}/api/v2/testRuns/{run_id}/testResults"
    resp = session.post(upload_url, json=results, timeout=120)
    if resp.status_code >= 400:
        print(f"  Bulk upload failed: {resp.status_code} {resp.text[:500]}", file=sys.stderr)
        print("  Falling back to per-result upload ...")
        ok = 0
        for r in results:
            r2 = session.post(upload_url, json=[r], timeout=60)
            if r2.status_code < 400:
                ok += 1
            else:
                print(f"  FAIL {r['autoTestExternalId']}: {r2.status_code} {r2.text[:200]}", file=sys.stderr)
        print(f"  Per-result upload: {ok}/{len(results)} succeeded.")
    else:
        print(f"  Bulk upload OK ({resp.status_code}).")

    # 4) Complete TestRun
    try:
        resp = session.post(f"{args.tms_url}/api/v2/testRuns/{run_id}/complete", timeout=30)
        if resp.status_code >= 400:
            print(f"  WARN: complete returned {resp.status_code}: {resp.text[:200]}")
        else:
            print("  TestRun completed.")
    except Exception as e:  # noqa: BLE001
        print(f"  WARN: complete failed (ignored): {e}")

    project_global_id = 3117  # MDC well-known globalId
    print()
    print(f"Done. Open TestRun in browser:")
    print(f"  {args.tms_url}/projects/{project_global_id}/test-runs/{run_id}")
    print(f"Autotests in UI/Smoke:")
    print(f"  {args.tms_url}/projects/{project_global_id}/autotests?type=Namespace&namespace=UI/Smoke")

    return 0


if __name__ == "__main__":
    sys.exit(main())
