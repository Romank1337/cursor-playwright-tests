"""Один прогон: создать PU, save+apply, вывести URL."""

import os
import re
import time
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

L = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
U, P = os.environ.get("TEST_USER_LOGIN", "Admin"), os.environ.get("TEST_USER_PASSWORD", "123")
TAB = "/list/production-structure?tab=productionUnits"


def pick_flat(page, iid: str) -> bool:
    inner = page.locator(f"#{iid}").first
    w = page.locator(".ant-select").filter(has=inner).first
    if w.count() == 0:
        return False
    w.locator(".ant-select-selector").first.click()
    page.wait_for_timeout(400)
    dd = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    if dd.count() == 0:
        return False
    o = dd.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)").first
    if o.count() == 0:
        return False
    o.click(force=True)
    page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    return True


def pick_tree(page, iid: str) -> bool:
    inner = page.locator(f"#{iid}").first
    w = page.locator(".ant-select.ant-tree-select").filter(has=inner).first
    if w.count() == 0:
        return False
    w.locator(".ant-select-selector").first.click()
    page.wait_for_timeout(500)
    dd = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    n = dd.locator(".ant-select-tree-treenode:not([aria-hidden='true']) .ant-select-tree-node-content-wrapper").first
    if n.count() == 0:
        return False
    n.click(force=True)
    page.wait_for_timeout(400)
    page.keyboard.press("Escape")
    return True


def main() -> None:
    base = f"{urlsplit(L).scheme}://{urlsplit(L).netloc}"
    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        pg = br.new_context(ignore_https_errors=True).new_page()
        pg.goto(L)
        pg.locator("#login").fill(U)
        pg.locator("#password").fill(P)
        pg.locator("button[type='submit']").click()
        pg.wait_for_timeout(1200)
        pg.goto(base + TAB)
        pg.wait_for_timeout(1500)
        btns = pg.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
        for i in range(btns.count()):
            if btns.nth(i).is_visible():
                btns.nth(i).click()
                break
        pg.wait_for_timeout(1200)
        suf = str(int(time.time()))
        pg.locator("#ProductionUnit_Code").fill(f"QS{suf}"[:12])
        pg.locator("#ProductionUnit_Name").fill(f"QNAME{suf}")
        print("type", pick_flat(pg, "ProductionUnit_Type"))
        print("parent", pick_tree(pg, "ProductionUnit_ParentId"))
        print("status", pick_flat(pg, "ProductionUnit_Status"))
        pg.locator("button.ant-btn-dangerous").filter(has_text=re.compile(r"Save|Сохранить")).first.click(force=True)
        pg.wait_for_timeout(2000)
        print("after save1", pg.url)
        ab = pg.locator("button:has-text('Apply'), button:has-text('Применить')").first
        if ab.count() and ab.is_visible():
            ab.click()
            pg.wait_for_timeout(2000)
        print("after apply", pg.url)
        pg.close()
        br.close()


if __name__ == "__main__":
    main()
