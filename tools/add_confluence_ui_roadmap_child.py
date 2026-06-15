"""Restore UI-тесты parent page and add roadmap child page."""
from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request

PARENT_ID = "60806279"
SPACE_KEY = "MDCQA"
PARENT_TITLE = "UI-тесты"
CHILD_TITLE = "Покрытие разделов и roadmap UI-автотестов"
BASE = "https://jira.zyfra.com/wiki"

PARENT_BODY = """
<p>Подробная информация по UI-тестам находится <a href="https://jira.zyfra.com/wiki/pages/viewpage.action?pageId=44731139">тут</a>.</p>
<p><a href="https://docs.google.com/spreadsheets/d/1gBz2I7rh9GMCIJzJERKo9bXcd87pRWAo01GSIOkchSs/edit#gid=2091986316">План написания/актуализации</a></p>
"""

CHILD_BODY = """
<p>Краткий обзор того, какие зоны Диспетчера уже затронуты UI-автотестами и куда развивать покрытие дальше.</p>
<p>Репозиторий: <a href="https://github.com/Romank1337/cursor-playwright-tests">cursor-playwright-tests</a>. Настройка окружения — в соседней статье раздела <strong>UI-тесты</strong>.</p>

<h2>Что уже затронуто</h2>
<p><em>Состав сценариев может меняться — ориентир на зоны приложения, не на список тест-кейсов.</em></p>
<ul>
<li><strong>Авторизация</strong> — вход, негатив, язык, переход после логина.</li>
<li><strong>Справочники</strong> — устройства, персонал, production units, роли: списки и формы; изменение данных — под <code>RUN_DESTRUCTIVE_*</code>.</li>
<li><strong>Параметры оборудования</strong> — состояния и параметры (<code>/list/machineParams</code>).</li>
<li><strong>Мониторинг</strong> — пока только редирект после входа.</li>
</ul>

<h2>Roadmap</h2>
<table><tbody>
<tr><th>Приоритет</th><th>Направление</th></tr>
<tr><td>P0</td><td>Стабилизация machineParams и production units</td></tr>
<tr><td>P1</td><td>Единый шаблон для справочников: smoke → форма → CRUD за флагом</td></tr>
<tr><td>P2</td><td>Smoke <code>/monitoring/realtime</code></td></tr>
<tr><td>P3</td><td>Другие вкладки production-structure и пункты Directories</td></tr>
<tr><td>P4</td><td>CI на тестовом стенде, результаты в Test IT</td></tr>
</tbody></table>

<p><em>Обновлено: 2026-06.</em></p>
"""


def _auth(user: str, password: str) -> str:
    import base64

    return "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode("ascii")


def _req(method: str, url: str, user: str, password: str, payload: dict | None = None) -> dict:
    headers = {"Authorization": _auth(user, password), "Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, context=ssl.create_default_context(), timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:2500]}") from exc


def _find_child_by_title(user: str, password: str, title: str) -> dict | None:
    import urllib.parse

    cql = urllib.parse.quote(f'parent={PARENT_ID} and title="{title}"')
    data = _req("GET", f"{BASE}/rest/api/content/search?cql={cql}", user, password)
    results = data.get("results") or []
    return results[0] if results else None


def main() -> None:
    user = os.getenv("JIRA_USER") or os.getenv("CONFLUENCE_USER")
    password = os.getenv("JIRA_PASS") or os.getenv("CONFLUENCE_PASS")
    if not user or not password:
        raise SystemExit("Set JIRA_USER and JIRA_PASS.")

    parent = _req("GET", f"{BASE}/rest/api/content/{PARENT_ID}?expand=version", user, password)
    restored = _req(
        "PUT",
        f"{BASE}/rest/api/content/{PARENT_ID}",
        user,
        password,
        {
            "id": PARENT_ID,
            "type": "page",
            "title": PARENT_TITLE,
            "version": {"number": parent["version"]["number"] + 1},
            "body": {"storage": {"value": PARENT_BODY.strip(), "representation": "storage"}},
        },
    )
    print(f"Parent restored v{restored['version']['number']}")

    existing = _find_child_by_title(user, password, CHILD_TITLE)
    if existing:
        page_id = existing["id"]
        cur = _req("GET", f"{BASE}/rest/api/content/{page_id}?expand=version", user, password)
        updated = _req(
            "PUT",
            f"{BASE}/rest/api/content/{page_id}",
            user,
            password,
            {
                "id": page_id,
                "type": "page",
                "title": CHILD_TITLE,
                "version": {"number": cur["version"]["number"] + 1},
                "body": {"storage": {"value": CHILD_BODY.strip(), "representation": "storage"}},
            },
        )
        print(f"Child updated v{updated['version']['number']}")
        print(f"URL: {BASE}{updated['_links']['webui']}")
        return

    created = _req(
        "POST",
        f"{BASE}/rest/api/content",
        user,
        password,
        {
            "type": "page",
            "title": CHILD_TITLE,
            "ancestors": [{"id": PARENT_ID}],
            "space": {"key": SPACE_KEY},
            "body": {"storage": {"value": CHILD_BODY.strip(), "representation": "storage"}},
        },
    )
    print(f"Child created id={created['id']} v{created['version']['number']}")
    print(f"URL: {BASE}{created['_links']['webui']}")


if __name__ == "__main__":
    main()
