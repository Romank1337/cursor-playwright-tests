import os, re, time
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

L = "https://localhost:8001/user/login"
base = "https://localhost:8001"

with sync_playwright() as p:
    pg = p.chromium.launch(headless=True).new_context(ignore_https_errors=True).new_page()
    pg.goto(L)
    pg.locator("#login").fill("Admin")
    pg.locator("#password").fill("123")
    pg.locator("button[type='submit']").click()
    pg.wait_for_timeout(1200)
    pg.goto(f"{base}/list/production-structure?tab=productionUnits")
    pg.wait_for_timeout(1500)
    for i in range(pg.locator("button.index_button__EOmvq").filter(has_text=re.compile("Create")).count()):
        b = pg.locator("button.index_button__EOmvq").filter(has_text=re.compile("Create")).nth(i)
        if b.is_visible():
            b.click()
            break
    pg.locator("#ProductionUnit_Code").wait_for(state="visible")
    suf = str(int(time.time()))
    pg.locator("#ProductionUnit_Code").fill(f"DEL{suf}")
    pg.locator("#ProductionUnit_Name").fill(f"DELNAME{suf}")
    # type division
    w = pg.locator(".ant-select").filter(has=pg.locator("#ProductionUnit_Type")).first
    w.locator(".ant-select-selector").click()
    pg.wait_for_timeout(400)
    pg.locator(".ant-select-dropdown .ant-select-item-option").nth(1).click()
    pg.keyboard.press("Escape")
    pg.wait_for_timeout(400)
    w = pg.locator(".ant-select.ant-tree-select").filter(has=pg.locator("#ProductionUnit_ParentId")).first
    w.locator(".ant-select-selector").click()
    pg.wait_for_timeout(500)
    pg.locator(".ant-select-dropdown .ant-select-tree-node-content-wrapper").first.click()
    pg.keyboard.press("Escape")
    pg.locator("button.ant-btn-dangerous").filter(has_text=re.compile("Save")).first.click()
    pg.wait_for_timeout(2500)
    print("url", pg.url)
    data = pg.evaluate(
        """() => Array.from(document.querySelectorAll('button')).filter(b => {
          const r = b.getBoundingClientRect();
          return r.width>0 && r.height>0;
        }).map(b => ({
          text: (b.innerText||'').trim().slice(0,40),
          cls: (b.className||'').slice(0,120),
          aria: b.getAttribute('aria-label'),
        }))"""
    )
    for d in data:
        if 'danger' in d['cls'] or 'delete' in (d['cls']+d['text']+str(d['aria'])).lower():
            print(d)
