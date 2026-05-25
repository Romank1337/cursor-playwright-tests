import os
import re
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

L = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
base = f"{urlsplit(L).scheme}://{urlsplit(L).netloc}"

with sync_playwright() as p:
    pg = p.chromium.launch(headless=True).new_context(ignore_https_errors=True).new_page()
    pg.goto(L)
    pg.locator("#login").fill("Admin")
    pg.locator("#password").fill("123")
    pg.locator("button[type='submit']").click()
    pg.wait_for_timeout(1200)
    pg.goto(f"{base}/list/production-structure?tab=productionUnits")
    pg.wait_for_timeout(1500)
    if "/user/login" in pg.url:
        pg.locator("#login").fill("Admin")
        pg.locator("#password").fill("123")
        pg.locator("button[type='submit']").click()
        pg.wait_for_timeout(1200)
        pg.goto(f"{base}/list/production-structure?tab=productionUnits")
        pg.wait_for_timeout(1500)
    pg.locator("table.MuiTable-root").first.wait_for(state="visible", timeout=20_000)
    btns = pg.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
    for i in range(btns.count()):
        if btns.nth(i).is_visible():
            btns.nth(i).click()
            break
    pg.wait_for_timeout(1200)
    pg.locator("#ProductionUnit_Code").wait_for(state="visible", timeout=20_000)
    w = pg.locator(".ant-select").filter(has=pg.locator("#ProductionUnit_Type")).first
    w.locator(".ant-select-selector").click()
    pg.wait_for_timeout(500)
    dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    n = dd.locator(".ant-select-item-option").count()
    for i in range(n):
        print(i, repr(dd.locator(".ant-select-item-option").nth(i).inner_text()))

    # MainId widget class
    main_inner = pg.locator("#ProductionUnit_MainId")
    if main_inner.count():
        cls = main_inner.evaluate(
            "(el) => { const r = el.closest('.ant-select'); return r ? r.className : 'no'; }"
        )
        print("MainId root class:", cls)
