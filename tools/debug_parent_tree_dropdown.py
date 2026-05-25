"""Проверка dropdown для Parent (TreeSelect) после выбора Type."""

from __future__ import annotations

import os
import re
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

LOGIN = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
U = os.environ.get("TEST_USER_LOGIN", "Admin")
P = os.environ.get("TEST_USER_PASSWORD", "123")
TAB = "/list/production-structure?tab=productionUnits"


def _click_visible_create(page) -> None:
    page.locator("table.MuiTable-root, .ant-table").first.wait_for(state="visible", timeout=20_000)
    btns = page.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
    for i in range(btns.count()):
        b = btns.nth(i)
        if b.is_visible():
            b.click()
            return
    raise RuntimeError("no Create")


def _pick_flat(page, select_id: str) -> None:
    w = page.locator(".ant-select").filter(has=page.locator(f"#{select_id}")).first
    w.locator(".ant-select-selector").first.click()
    page.wait_for_timeout(400)
    dd = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    dd.wait_for(state="visible", timeout=5000)
    dd.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)").first.click()
    page.wait_for_timeout(400)
    page.keyboard.press("Escape")


def main() -> None:
    base = f"{urlsplit(LOGIN).scheme}://{urlsplit(LOGIN).netloc}"
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        pg = br.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900}).new_page()
        pg.goto(LOGIN, wait_until="domcontentloaded")
        pg.locator("#login").fill(U)
        pg.locator("#password").fill(P)
        pg.locator("button[type='submit']").click()
        pg.wait_for_timeout(1200)
        pg.goto(f"{base}{TAB}", wait_until="domcontentloaded")
        pg.wait_for_timeout(1200)
        if "/user/login" in pg.url:
            pg.locator("#login").fill(U)
            pg.locator("#password").fill(P)
            pg.locator("button[type='submit']").click()
            pg.wait_for_timeout(1200)
            pg.goto(f"{base}{TAB}", wait_until="domcontentloaded")
            pg.wait_for_timeout(1200)
        _click_visible_create(pg)
        pg.wait_for_timeout(1200)
        _pick_flat(pg, "ProductionUnit_Type")
        pg.wait_for_timeout(600)

        w = pg.locator(".ant-select.ant-tree-select").filter(has=pg.locator("#ProductionUnit_ParentId")).first
        w.locator(".ant-select-selector").first.click()
        pg.wait_for_timeout(600)
        dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
        html = dd.inner_html()
        print("dropdown len", len(html))
        print(html[:2500])
        # попробовать кликнуть первый узел
        for sel in (
            ".ant-select-tree-node-content-wrapper",
            ".ant-select-tree-title",
            "[role='treeitem']",
        ):
            n = dd.locator(sel).first
            if n.count() > 0:
                print("first match", sel, "count", dd.locator(sel).count())
        br.close()


if __name__ == "__main__":
    main()
