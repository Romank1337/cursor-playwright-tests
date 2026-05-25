"""Какой Type + Parent даёт успешный save (id != 0 или строка в таблице)."""

import os
import re
import time
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

L = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
base = f"{urlsplit(L).scheme}://{urlsplit(L).netloc}"


def toast(pg) -> list[str]:
    return pg.evaluate(
        "() => Array.from(document.querySelectorAll('.ant-notification-notice-message, .ant-message-notice-content')).map(e => (e.innerText||'').trim()).filter(Boolean)"
    )


def open_form(pg):
    pg.goto(f"{base}/list/production-structure?tab=productionUnits", wait_until="domcontentloaded")
    pg.wait_for_timeout(1500)
    if "/user/login" in pg.url:
        pg.locator("#login").fill("Admin")
        pg.locator("#password").fill("123")
        pg.locator("button[type='submit']").click()
        pg.wait_for_timeout(1200)
        pg.goto(f"{base}/list/production-structure?tab=productionUnits", wait_until="domcontentloaded")
        pg.wait_for_timeout(1500)
    pg.locator("table.MuiTable-root").first.wait_for(state="visible", timeout=25_000)
    btns = pg.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
    for i in range(btns.count()):
        if btns.nth(i).is_visible():
            btns.nth(i).click()
            break
    pg.locator("#ProductionUnit_Code").wait_for(state="visible", timeout=20_000)


def pick_type_idx(pg, idx: int) -> str:
    w = pg.locator(".ant-select").filter(has=pg.locator("#ProductionUnit_Type")).first
    w.locator(".ant-select-selector").click(force=True)
    pg.wait_for_timeout(350)
    dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    opt = dd.locator(".ant-select-item-option").nth(idx)
    label = (opt.inner_text() or "").strip()
    opt.click(force=True)
    pg.wait_for_timeout(400)
    pg.keyboard.press("Escape")
    return label


def pick_parent(pg) -> bool:
    w = pg.locator(".ant-select.ant-tree-select").filter(has=pg.locator("#ProductionUnit_ParentId")).first
    if w.count() == 0:
        return False
    w.locator(".ant-select-selector").click(force=True)
    pg.wait_for_timeout(500)
    dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    n = dd.locator(".ant-select-tree-treenode:not([aria-hidden='true']) .ant-select-tree-node-content-wrapper").first
    if n.count() == 0:
        return False
    n.click(force=True)
    pg.wait_for_timeout(400)
    pg.keyboard.press("Escape")
    return True


def pick_main_company_node(pg) -> bool:
    inner = pg.locator("#ProductionUnit_MainId")
    cls = inner.evaluate("(el) => el.closest('.ant-select')?.className || ''")
    if "disabled" in cls:
        return False
    w = pg.locator(".ant-select.ant-tree-select").filter(has=inner).first
    w.locator(".ant-select-selector").click(force=True)
    pg.wait_for_timeout(500)
    dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    titles = dd.locator(".ant-select-tree-title")
    for i in range(titles.count()):
        t = (titles.nth(i).inner_text() or "").strip()
        if re.search(r"company|компан|организац|enterprise|станк", t, re.I):
            titles.nth(i).click(force=True)
            pg.keyboard.press("Escape")
            return True
    if titles.count():
        titles.first.click(force=True)
        pg.keyboard.press("Escape")
        return True
    return False


with sync_playwright() as p:
    pg = p.chromium.launch(headless=True).new_context(ignore_https_errors=True).new_page()
    pg.goto(L, wait_until="domcontentloaded")
    pg.locator("#login").fill("Admin")
    pg.locator("#password").fill("123")
    pg.locator("button[type='submit']").click()
    pg.wait_for_timeout(1200)

    open_form(pg)
    w = pg.locator(".ant-select").filter(has=pg.locator("#ProductionUnit_Type")).first
    w.locator(".ant-select-selector").click(force=True)
    pg.wait_for_timeout(350)
    type_count = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden) .ant-select-item-option").count()
    pg.keyboard.press("Escape")

    for idx in range(type_count):
        open_form(pg)
        suf = str(int(time.time()))[-6:]
        code = f"T{idx}{suf}"
        label = pick_type_idx(pg, idx)
        pg.locator("#ProductionUnit_Code").fill(code)
        pg.locator("#ProductionUnit_Name").fill(f"NAME{code}")
        parent_ok = pick_parent(pg)
        main_ok = pick_main_company_node(pg)
        pg.locator("button.ant-btn-dangerous").filter(has_text=re.compile(r"Save|Сохранить")).first.click(force=True)
        pg.wait_for_timeout(2000)
        ab = pg.locator("button:has-text('Apply'), button:has-text('Применить')").first
        if ab.count() and ab.is_visible():
            ab.click()
            pg.wait_for_timeout(2000)
        url = pg.url
        m = re.search(r"/production-unit/(\d+)", url)
        uid = m.group(1) if m else None
        msgs = toast(pg)
        pg.goto(f"{base}/list/production-structure?tab=productionUnits")
        pg.wait_for_timeout(1500)
        rows = pg.locator("table.MuiTable-root tbody tr", has_text=code).count()
        print(
            f"idx={idx} type={label!r} parent={parent_ok} main={main_ok} "
            f"uid={uid} rows={rows} toast={msgs[:2]}"
        )
