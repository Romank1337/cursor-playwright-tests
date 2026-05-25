import os
import re
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

L = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
base = f"{urlsplit(L).scheme}://{urlsplit(L).netloc}"


def open_form(pg):
    pg.goto(f"{base}/list/production-structure?tab=productionUnits")
    pg.wait_for_timeout(1500)
    pg.locator("table.MuiTable-root").first.wait_for(state="visible", timeout=20_000)
    btns = pg.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
    for i in range(btns.count()):
        if btns.nth(i).is_visible():
            btns.nth(i).click()
            break
    pg.locator("#ProductionUnit_Code").wait_for(state="visible", timeout=20_000)


def pick_type_index(pg, idx: int) -> None:
    w = pg.locator(".ant-select").filter(has=pg.locator("#ProductionUnit_Type")).first
    w.locator(".ant-select-selector").click()
    pg.wait_for_timeout(400)
    dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    dd.locator(".ant-select-item-option").nth(idx).click()
    pg.wait_for_timeout(500)
    pg.keyboard.press("Escape")


with sync_playwright() as p:
    pg = p.chromium.launch(headless=True).new_context(ignore_https_errors=True).new_page()
    pg.goto(L)
    pg.locator("#login").fill("Admin")
    pg.locator("#password").fill("123")
    pg.locator("button[type='submit']").click()
    pg.wait_for_timeout(1200)
    open_form(pg)
    pick_type_index(pg, 0)  # Enterprise
    pg.wait_for_timeout(800)
    disabled = pg.locator("#ProductionUnit_MainId").evaluate(
        "(el) => el.closest('.ant-select')?.className || ''"
    )
    print("Main after Enterprise:", disabled)
    w = pg.locator(".ant-select.ant-tree-select").filter(has=pg.locator("#ProductionUnit_MainId")).first
    if "disabled" in disabled:
        print("Main still disabled")
    else:
        w.locator(".ant-select-selector").click()
        pg.wait_for_timeout(600)
        dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
        nodes = dd.locator(".ant-select-tree-title")
        for i in range(min(nodes.count(), 15)):
            print(i, repr(nodes.nth(i).inner_text()))
