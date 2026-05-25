import os
import re
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

L = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
base = f"{urlsplit(L).scheme}://{urlsplit(L).netloc}"


def open_form(pg):
    pg.goto(f"{base}/list/production-structure?tab=productionUnits")
    pg.wait_for_timeout(1200)
    pg.locator("table.MuiTable-root").first.wait_for(state="visible", timeout=20_000)
    for i in range(pg.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать")).count()):
        b = pg.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать")).nth(i)
        if b.is_visible():
            b.click()
            break
    pg.locator("#ProductionUnit_Code").wait_for(state="visible", timeout=20_000)


def main_cls(pg, field: str) -> str:
    return pg.locator(f"#{field}").evaluate(
        "(el) => el.closest('.ant-select')?.className || ''"
    )


def pick_type_idx(pg, idx: int) -> str:
    w = pg.locator(".ant-select").filter(has=pg.locator("#ProductionUnit_Type")).first
    w.locator(".ant-select-selector").click()
    pg.wait_for_timeout(350)
    dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    opt = dd.locator(".ant-select-item-option").nth(idx)
    label = (opt.inner_text() or "").strip()
    opt.click()
    pg.wait_for_timeout(400)
    pg.keyboard.press("Escape")
    return label


def pick_parent_first(pg) -> None:
    w = pg.locator(".ant-select.ant-tree-select").filter(has=pg.locator("#ProductionUnit_ParentId")).first
    w.locator(".ant-select-selector").click()
    pg.wait_for_timeout(500)
    dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    dd.locator(".ant-select-tree-treenode:not([aria-hidden='true']) .ant-select-tree-node-content-wrapper").first.click()
    pg.wait_for_timeout(400)
    pg.keyboard.press("Escape")


with sync_playwright() as p:
    pg = p.chromium.launch(headless=True).new_context(ignore_https_errors=True).new_page()
    pg.goto(L)
    pg.locator("#login").fill("Admin")
    pg.locator("#password").fill("123")
    pg.locator("button[type='submit']").click()
    pg.wait_for_timeout(1200)

    open_form(pg)
    n = 0
    w = pg.locator(".ant-select").filter(has=pg.locator("#ProductionUnit_Type")).first
    w.locator(".ant-select-selector").click()
    pg.wait_for_timeout(350)
    n = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").count()
    pg.keyboard.press("Escape")

    for idx in range(n):
        open_form(pg)
        label = pick_type_idx(pg, idx)
        pick_parent_first(pg)
        pg.wait_for_timeout(500)
        main_c = main_cls(pg, "ProductionUnit_MainId")
        status_c = main_cls(pg, "ProductionUnit_Status")
        print(f"type[{idx}]={label!r} main_disabled={'disabled' in main_c} status_disabled={'disabled' in status_c}")
