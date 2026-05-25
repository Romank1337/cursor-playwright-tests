"""
Разведка раздела Directories -> Production structure -> Production units.

Что делает:
1) логинится Admin/123,
2) идёт на /list/production-structure?tab=productionUnits,
3) сохраняет скриншоты и метаданные ключевых интерактивных элементов
   (кнопки, поля, селекты, таблица/список, тулбар) в tools/_probe/.

Запуск:
    python tools/probe_production_units.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


LOGIN_URL = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
USERNAME = os.environ.get("TEST_USER_LOGIN", "Admin")
PASSWORD = os.environ.get("TEST_USER_PASSWORD", "123")
TARGET_PATH = "/list/production-structure?tab=productionUnits"

OUT_DIR = Path(__file__).resolve().parent / "_probe"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _probe_elements(page) -> dict:
    """Собирает читаемое описание интерактивных элементов для подбора селекторов."""

    js = r"""
    () => {
      const visible = (el) => {
        const r = el.getBoundingClientRect();
        const s = window.getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
      };
      const describe = (el, limit = 80) => {
        const text = (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, limit);
        return {
          tag: el.tagName.toLowerCase(),
          id: el.id || null,
          class: el.className && typeof el.className === 'string' ? el.className : null,
          name: el.getAttribute('name'),
          type: el.getAttribute('type'),
          placeholder: el.getAttribute('placeholder'),
          ariaLabel: el.getAttribute('aria-label'),
          title: el.getAttribute('title'),
          dataTestid: el.getAttribute('data-testid'),
          text,
        };
      };

      const buttons = Array.from(document.querySelectorAll('button, [role="button"]'))
        .filter(visible)
        .map((el) => describe(el, 60));

      const inputs = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"]'))
        .filter(visible)
        .map((el) => describe(el, 60));

      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, [role="heading"]'))
        .filter(visible)
        .map((el) => describe(el, 80));

      const tables = Array.from(document.querySelectorAll('table, .ant-table, .ant-list'))
        .filter(visible)
        .map((el) => ({
          tag: el.tagName.toLowerCase(),
          class: el.className && typeof el.className === 'string' ? el.className : null,
          headers: Array.from(el.querySelectorAll('th, .ant-table-cell:not(.ant-table-cell-row-hover)'))
            .slice(0, 12)
            .map((h) => (h.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 40)),
          rowsCount: el.querySelectorAll('.ant-table-row, .ant-list-item, tbody tr').length,
        }));

      const tabs = Array.from(document.querySelectorAll('[role="tab"], .ant-tabs-tab'))
        .filter(visible)
        .map((el) => describe(el, 60));

      return { url: location.href, buttons, inputs, headings, tables, tabs };
    }
    """
    return page.evaluate(js)


def main() -> None:
    parsed = urlsplit(LOGIN_URL)
    base = f"{parsed.scheme}://{parsed.netloc}"
    target_url = f"{base}{TARGET_PATH}"

    print(f"login -> {LOGIN_URL}")
    print(f"target -> {target_url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.goto(LOGIN_URL, wait_until="domcontentloaded")
        page.locator("#login").fill(USERNAME)
        page.locator("#password").fill(PASSWORD)
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1200)

        page.goto(target_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1500)
        print("after-goto url:", page.url)

        if "/user/login" in page.url:
            page.locator("#login").fill(USERNAME)
            page.locator("#password").fill(PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1200)
            page.goto(target_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
            print("after-relogin url:", page.url)

        page.screenshot(path=str(OUT_DIR / "01_list.png"), full_page=True)
        info_list = _probe_elements(page)
        (OUT_DIR / "01_list.json").write_text(json.dumps(info_list, ensure_ascii=False, indent=2), encoding="utf-8")
        print("list elements: buttons=%d inputs=%d tables=%d" %
              (len(info_list.get("buttons", [])), len(info_list.get("inputs", [])), len(info_list.get("tables", []))))

        # Пробуем открыть форму создания: типовые варианты текста/иконок в этом UI.
        candidates = [
            ("text=Create", page.get_by_text("Create", exact=True).first),
            ("text=Создать", page.get_by_text("Создать", exact=True).first),
            ("button index_button+Создать", page.locator("button[class*='index_button']").filter(has_text="Создать").first),
            ("button index_button+Create", page.locator("button[class*='index_button']").filter(has_text="Create").first),
            ("button :has(.anticon-plus)", page.locator("button:has(.anticon-plus)").first),
        ]
        opened = False
        for label, btn in candidates:
            if btn.count() > 0 and btn.first.is_visible():
                print(f"clicking create candidate: {label}")
                try:
                    btn.first.click(timeout=2500)
                except Exception:
                    btn.first.click(force=True)
                page.wait_for_timeout(1200)
                opened = True
                break
        print("create form opened:", opened, "url:", page.url)

        page.screenshot(path=str(OUT_DIR / "02_create_form.png"), full_page=True)
        info_form = _probe_elements(page)
        (OUT_DIR / "02_create_form.json").write_text(json.dumps(info_form, ensure_ascii=False, indent=2), encoding="utf-8")
        print("form elements: buttons=%d inputs=%d" %
              (len(info_form.get("buttons", [])), len(info_form.get("inputs", []))))

        browser.close()


if __name__ == "__main__":
    main()
