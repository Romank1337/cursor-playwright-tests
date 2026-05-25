"""Один save с полным набором селектов + вывод ошибок и поиск в таблице."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

L = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
U = os.environ.get("TEST_USER_LOGIN", "Admin")
P = os.environ.get("TEST_USER_PASSWORD", "123")
TAB = "/list/production-structure?tab=productionUnits"


def pick_flat(page, iid: str) -> bool:
    inner = page.locator(f"#{iid}").first
    w = page.locator(".ant-select").filter(has=inner).first
    if w.count() == 0:
        print(f"  flat {iid}: no widget")
        return False
    w.locator(".ant-select-selector").first.click(force=True)
    page.wait_for_timeout(450)
    dd = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    try:
        dd.wait_for(state="visible", timeout=5000)
    except Exception:
        print(f"  flat {iid}: no dropdown")
        return False
    o = dd.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)").first
    if o.count() == 0:
        print(f"  flat {iid}: no option")
        return False
    o.click(force=True)
    page.wait_for_timeout(350)
    page.keyboard.press("Escape")
    return True


def pick_tree(page, iid: str) -> bool:
    inner = page.locator(f"#{iid}").first
    w = page.locator(".ant-select.ant-tree-select").filter(has=inner).first
    if w.count() == 0:
        print(f"  tree {iid}: no widget")
        return False
    w.locator(".ant-select-selector").first.click(force=True)
    page.wait_for_timeout(500)
    dd = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    try:
        dd.wait_for(state="visible", timeout=6000)
    except Exception:
        print(f"  tree {iid}: no dropdown")
        return False
    n = dd.locator(
        ".ant-select-tree-treenode:not([aria-hidden='true']) .ant-select-tree-node-content-wrapper"
    ).first
    if n.count() == 0:
        print(f"  tree {iid}: no node")
        return False
    n.click(force=True)
    page.wait_for_timeout(400)
    page.keyboard.press("Escape")
    return True


def errors(page) -> dict:
    return page.evaluate(
        r"""() => {
          const rows = Array.from(document.querySelectorAll('.ant-form-item-has-error')).map((row) => {
            const label = row.querySelector('.ant-form-item-label');
            const explain = row.querySelector('.ant-form-item-explain-error');
            return {
              label: label ? (label.innerText||'').trim() : '',
              explain: explain ? (explain.innerText||'').trim() : '',
            };
          });
          const toast = Array.from(document.querySelectorAll('.ant-notification-notice-message, .ant-message-notice-content'))
            .map((e) => (e.innerText||'').trim()).filter(Boolean);
          return { rows, toast, url: location.href };
        }"""
    )


def open_create(page, base: str) -> None:
    page.goto(base + TAB, wait_until="domcontentloaded")
    page.wait_for_timeout(1500)
    page.locator("table.MuiTable-root").first.wait_for(state="visible", timeout=20_000)
    btns = page.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
    for i in range(btns.count()):
        if btns.nth(i).is_visible():
            btns.nth(i).click()
            break
    page.locator("#ProductionUnit_Code").wait_for(state="visible", timeout=15_000)


def main() -> None:
    base = f"{urlsplit(L).scheme}://{urlsplit(L).netloc}"
    suf = str(int(time.time()))
    code = f"DBG{suf}"[:12]
    name = f"DBGNAME{suf}"

    with sync_playwright() as p:
        br = p.chromium.launch(headless=True)
        pg = br.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900}).new_page()
        pg.goto(L, wait_until="domcontentloaded")
        pg.locator("#login").fill(U)
        pg.locator("#password").fill(P)
        pg.locator("button[type='submit']").click()
        pg.wait_for_timeout(1200)

        open_create(pg, base)
        print("form url", pg.url)
        pg.locator("#ProductionUnit_Code").fill(code)
        pg.locator("#ProductionUnit_Name").fill(name)
        pg.locator("#ProductionUnit_FullName").fill(name)

        print("picks:")
        company_pat = re.compile(r"company|компан|организац|organization", re.I)

        def pick_flat_pat(iid, pat):
            inner = pg.locator(f"#{iid}").first
            w = pg.locator(".ant-select").filter(has=inner).first
            if w.count() == 0:
                return False
            w.locator(".ant-select-selector").first.click(force=True)
            pg.wait_for_timeout(450)
            dd = pg.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
            try:
                dd.wait_for(state="visible", timeout=5000)
            except Exception:
                return False
            opts = dd.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)")
            for i in range(opts.count()):
                t = (opts.nth(i).inner_text() or "").strip()
                if pat.search(t):
                    opts.nth(i).click(force=True)
                    pg.keyboard.press("Escape")
                    return True
            if opts.count():
                opts.first.click(force=True)
                pg.keyboard.press("Escape")
                return True
            return False

        print("  type", pick_flat_pat("ProductionUnit_Type", company_pat))
        print("  parent", pick_tree(pg, "ProductionUnit_ParentId"))
        pg.wait_for_timeout(800)
        print("  main", pick_flat_pat("ProductionUnit_MainId", company_pat))
        print("  status", pick_flat(pg, "ProductionUnit_Status"))

        pg.locator("button.ant-btn-dangerous").filter(has_text=re.compile(r"Save|Сохранить")).first.click(force=True)
        pg.wait_for_timeout(2500)
        print("after save", json.dumps(errors(pg), ensure_ascii=False, indent=2))

        ab = pg.locator("button:has-text('Apply'), button:has-text('Применить')").first
        if ab.count() and ab.is_visible():
            ab.click()
            pg.wait_for_timeout(2500)
        print("after apply", json.dumps(errors(pg), ensure_ascii=False, indent=2))

        pg.goto(base + TAB, wait_until="domcontentloaded")
        pg.wait_for_timeout(2000)
        cnt = pg.locator("table.MuiTable-root tbody tr", has_text=code).count()
        print(f"rows with code {code!r}: {cnt}")

        br.close()


if __name__ == "__main__":
    main()
