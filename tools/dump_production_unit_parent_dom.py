"""Дамп DOM вокруг #ProductionUnit_ParentId для выбора стратегии в автотестах."""

from __future__ import annotations

import json
import os
import re
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

LOGIN_URL = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
USER = os.environ.get("TEST_USER_LOGIN", "Admin")
PWD = os.environ.get("TEST_USER_PASSWORD", "123")
TAB = "/list/production-structure?tab=productionUnits"


def main() -> None:
    parsed = urlsplit(LOGIN_URL)
    base = f"{parsed.scheme}://{parsed.netloc}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        page.locator("#login").fill(USER)
        page.locator("#password").fill(PWD)
        page.locator("button[type='submit']").click()
        page.wait_for_timeout(1200)
        page.goto(f"{base}{TAB}", wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        if "/user/login" in page.url:
            page.locator("#login").fill(USER)
            page.locator("#password").fill(PWD)
            page.locator("button[type='submit']").click()
            page.wait_for_timeout(1200)
            page.goto(f"{base}{TAB}", wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

        page.locator("table.MuiTable-root, .ant-table").first.wait_for(state="visible", timeout=20_000)
        btns = page.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
        clicked = False
        for i in range(btns.count()):
            b = btns.nth(i)
            if b.is_visible():
                b.click()
                clicked = True
                break
        if not clicked:
            raise RuntimeError("Create button not found")
        page.wait_for_timeout(1500)
        data = page.evaluate(
            r"""() => {
              const inputs = Array.from(document.querySelectorAll('input[id], select[id], textarea[id]'))
                .map((e) => ({ id: e.id, tag: e.tagName, type: e.type, cls: (e.className||'').slice(0,80) }))
                .filter((x) => /production|parent|unit/i.test(x.id));
              const el = document.querySelector('[id*="Parent"], [id*="parent"], [name*="Parent"]');
              const chain = [];
              const target = document.getElementById('ProductionUnit_ParentId')
                || document.querySelector('input[id^="ProductionUnit_"][id*="arent"]');
              if (target) {
                let n = target;
                for (let d = 0; d < 12 && n; d++) {
                  chain.push({
                    d,
                    tag: n.tagName,
                    id: n.id || null,
                    class: (n.className && String(n.className).slice(0, 160)) || null,
                  });
                  n = n.parentElement;
                }
              }
              return { inputsMatching: inputs.slice(0, 40), chain, url: location.href };
            }"""
        )
        print(json.dumps(data, ensure_ascii=False, indent=2))
        browser.close()


if __name__ == "__main__":
    main()
