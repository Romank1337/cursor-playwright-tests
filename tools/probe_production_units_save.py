"""
Пробуем сохранить запись Production unit с разным набором полей,
чтобы понять, какие поля действительно обязательные.

Лог пишет, что именно нажимали, какой URL после Save, и появились ли
сообщения валидации в DOM.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LOGIN_URL = os.environ.get("LOGIN_URL", "https://localhost:8001/user/login")
USERNAME = os.environ.get("TEST_USER_LOGIN", "Admin")
PASSWORD = os.environ.get("TEST_USER_PASSWORD", "123")
TARGET_PATH = "/list/production-structure?tab=productionUnits"

OUT_DIR = Path(__file__).resolve().parent / "_probe"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _collect_errors(page) -> dict:
    return page.evaluate(
        r"""
        () => {
          const visible = (el) => {
            const r = el.getBoundingClientRect();
            const s = window.getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
          };
          const list = (sel) => Array.from(document.querySelectorAll(sel))
            .filter(visible)
            .map((el) => (el.innerText || '').trim().replace(/\s+/g, ' ').slice(0, 120))
            .filter(Boolean);
          const requiredRows = Array.from(document.querySelectorAll('.ant-form-item-has-error'))
            .filter(visible)
            .map((row) => {
              const label = row.querySelector('.ant-form-item-label label, .ant-form-item-label');
              const labelText = (label && (label.innerText || '').trim()) || '';
              const explain = (row.querySelector('.ant-form-item-explain-error') || {}).innerText || '';
              return {
                label: labelText.replace(/\s+/g, ' ').slice(0, 80),
                explain: String(explain).replace(/\s+/g, ' ').slice(0, 80),
              };
            });
          return {
            formExplain: list('.ant-form-item-explain-error'),
            antMessage: list('.ant-message-notice-content'),
            antNotification: list('.ant-notification-notice-message, .ant-notification-notice-description'),
            antModalErrors: list('.ant-modal .ant-form-item-explain-error'),
            requiredRows,
            url: location.href,
          };
        }
        """
    )


def _login(page) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    page.locator("#login").fill(USERNAME)
    page.locator("#password").fill(PASSWORD)
    page.locator("button[type='submit']").click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1200)


def _open_create(page, base: str) -> None:
    target = f"{base}{TARGET_PATH}"
    last_err: Exception | None = None
    for round_idx in range(3):
        page.goto(target, wait_until="domcontentloaded")
        page.wait_for_timeout(1200 + round_idx * 500)
        if "/user/login" in page.url:
            page.locator("#login").fill(USERNAME)
            page.locator("#password").fill(PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(1200)
            page.goto(target, wait_until="domcontentloaded")
            page.wait_for_timeout(1200)

        # Дождаться, что список/тулбар реально отрисовались (SPA после возврата с карточки).
        try:
            page.locator("table.MuiTable-root, .ant-table").first.wait_for(state="visible", timeout=20_000)
        except Exception as exc:
            last_err = exc
            try:
                page.reload(wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
            except Exception:
                pass
            continue

        # Берём первую ВИДИМУЮ кнопку Create/Создать (в DOM часто есть дубликаты со `display:none`).
        toolbar_btns = page.locator("button.index_button__EOmvq").filter(has_text=re.compile(r"Create|Создать"))
        clicked = False
        for i in range(toolbar_btns.count()):
            btn = toolbar_btns.nth(i)
            if btn.count() == 0:
                continue
            try:
                if not btn.is_visible():
                    continue
            except Exception:
                continue
            try:
                btn.click(timeout=5000)
            except Exception:
                btn.click(force=True)
            page.wait_for_timeout(1200)
            if "/production-unit/" in page.url:
                clicked = True
                break

        if not clicked:
            candidates = (
                page.get_by_text("Create", exact=True).first,
                page.get_by_text("Создать", exact=True).first,
                page.locator("button[class*='index_button']").filter(has_text="Create").first,
                page.locator("button[class*='index_button']").filter(has_text="Создать").first,
                page.locator("button:has(.anticon-plus)").first,
            )
            for btn in candidates:
                if btn.count() > 0 and btn.first.is_visible():
                    try:
                        btn.first.click(timeout=5000)
                    except Exception:
                        btn.first.click(force=True)
                    page.wait_for_timeout(1200)
                    if "/production-unit/" in page.url:
                        clicked = True
                        break

        if clicked:
            return

        last_err = TimeoutError("Кнопка Create была не видна после ожидания списка")
        try:
            page.screenshot(path=str(OUT_DIR / f"open_create_fail_r{round_idx}.png"), full_page=True)
        except Exception:
            pass
        try:
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(1500)
        except Exception:
            pass

    raise TimeoutError(f"Не найдена кнопка создания Production unit (Create/Создать). last_err={last_err!r}")


def _pick_first_ant_option(page, select_id: str) -> bool:
    """Открыть AntD-select по id combobox-input и выбрать первую активную опцию.

    Кликаем по `.ant-select-selector` родительского `.ant-select`, а не по самому
    readonly/disabled input — иначе dropdown часто не открывается.
    """

    inner = page.locator(f"#{select_id}").first
    if inner.count() == 0:
        return False

    widget = page.locator(".ant-select").filter(has=page.locator(f"#{select_id}")).first
    if widget.count() == 0:
        try:
            page.screenshot(path=str(OUT_DIR / f"pick_no_widget_{select_id}.png"), full_page=True)
        except Exception:
            pass
        return False

    for _ in range(40):
        klass = (widget.get_attribute("class") or "") + (
            inner.evaluate(
                "(el) => { const root = el.closest('.ant-select'); return root ? root.className : ''; }"
            )
            or ""
        )
        if "ant-select-disabled" not in klass:
            break
        page.wait_for_timeout(200)

    try:
        widget.scroll_into_view_if_needed()
    except Exception:
        pass

    handle = widget.locator(".ant-select-selector").first
    if handle.count() == 0:
        return False
    try:
        handle.click(timeout=3000)
    except Exception:
        handle.click(force=True)
    page.wait_for_timeout(400)

    dropdown = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    try:
        dropdown.wait_for(state="visible", timeout=5000)
    except Exception:
        try:
            page.screenshot(path=str(OUT_DIR / f"pick_fail_{select_id}.png"), full_page=True)
        except Exception:
            pass
        return False

    opt = dropdown.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)").first
    if opt.count() == 0:
        try:
            page.screenshot(path=str(OUT_DIR / f"pick_fail_{select_id}_no_opt.png"), full_page=True)
        except Exception:
            pass
        return False
    opt.click(force=True)
    page.wait_for_timeout(450)
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    return True


def _pick_first_rc_select_near_code(page) -> bool:
    """Первый ant-select над полем Code (часто иерархия / родитель) — id вида rc_select_*."""

    anchor = page.locator("#ProductionUnit_Code").first
    if anchor.count() == 0:
        return False
    widgets = page.locator(".ant-select:visible")
    count = widgets.count()
    code_box = anchor.bounding_box()
    if not code_box:
        return False
    best_i = -1
    best_y = -1e9
    for i in range(count):
        w = widgets.nth(i)
        if not w.is_visible():
            continue
        bb = w.bounding_box()
        if not bb:
            continue
        if bb["y"] + bb["height"] <= code_box["y"] + 5 and bb["y"] > best_y:
            best_y = bb["y"]
            best_i = i
    if best_i < 0:
        return False
    w = widgets.nth(best_i)
    try:
        w.scroll_into_view_if_needed()
    except Exception:
        pass
    h = w.locator(".ant-select-selector").first
    if h.count() == 0:
        return False
    try:
        h.click(timeout=3000)
    except Exception:
        h.click(force=True)
    page.wait_for_timeout(400)
    dropdown = page.locator(".ant-select-dropdown:not(.ant-select-dropdown-hidden)").first
    try:
        dropdown.wait_for(state="visible", timeout=5000)
    except Exception:
        return False
    opt = dropdown.locator(".ant-select-item-option:not(.ant-select-item-option-disabled)").first
    if opt.count() == 0:
        return False
    opt.click(force=True)
    page.wait_for_timeout(400)
    page.keyboard.press("Escape")
    page.wait_for_timeout(150)
    return True


def _save(page) -> None:
    page.get_by_text("Save", exact=True).first.click()
    page.wait_for_timeout(1500)


def _attempt(
    page,
    base: str,
    label: str,
    *,
    fill_top_select: bool,
    fill_type: bool,
    fill_parent: bool,
    fill_status: bool,
    fill_company: bool,
    fill_dept: bool,
    fill_main: bool,
) -> dict:
    print(f"\n--- attempt: {label} ---")
    _open_create(page, base)
    suffix = f"{int(time.time())}-{label}"
    code = f"AT-{suffix}"[:20]
    name = f"AUTOTEST-{suffix}"[:60]
    page.locator("#ProductionUnit_Code").fill(code)
    page.locator("#ProductionUnit_Name").fill(name)

    if fill_top_select:
        ok = _pick_first_rc_select_near_code(page)
        print(f"  picked top select (above Code): {ok}")

    if fill_type:
        ok = _pick_first_ant_option(page, "ProductionUnit_Type")
        print(f"  picked Type: {ok}")
    if fill_parent:
        ok = _pick_first_ant_option(page, "ProductionUnit_ParentId")
        print(f"  picked ParentId: {ok}")
    if fill_status:
        ok = _pick_first_ant_option(page, "ProductionUnit_Status")
        print(f"  picked Status: {ok}")
    if fill_company:
        ok = _pick_first_ant_option(page, "ProductionUnit_CompanyId")
        print(f"  picked CompanyId: {ok}")
    if fill_dept:
        ok = _pick_first_ant_option(page, "ProductionUnit_DeptId")
        print(f"  picked DeptId: {ok}")
    if fill_main:
        ok = _pick_first_ant_option(page, "ProductionUnit_MainId")
        print(f"  picked MainId: {ok}")

    url_before = page.url
    _save(page)
    err = _collect_errors(page)
    print(f"  url before save: {url_before}")
    print(f"  url after  save: {page.url}")
    if err.get("requiredRows"):
        print(f"  requiredRows: {err['requiredRows']}")
    if err["formExplain"]:
        print(f"  formExplain: {err['formExplain']}")
    if err["antMessage"]:
        print(f"  antMessage: {err['antMessage']}")
    if err["antNotification"]:
        print(f"  antNotification: {err['antNotification']}")

    saved = "/production-unit/0" not in page.url and "/production-unit" in page.url
    print(f"  saved={saved}")
    return {
        "label": label,
        "code": code,
        "name": name,
        "url_before_save": url_before,
        "url_after_save": page.url,
        "errors": err,
        "saved": saved,
    }


def main() -> None:
    parsed = urlsplit(LOGIN_URL)
    base = f"{parsed.scheme}://{parsed.netloc}"
    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True, viewport={"width": 1440, "height": 900})
        page = context.new_page()
        _login(page)

        attempts = [
            ("min", dict(fill_top_select=False, fill_type=False, fill_parent=False, fill_status=False, fill_company=False, fill_dept=False, fill_main=False)),
            ("type_parent", dict(fill_top_select=False, fill_type=True, fill_parent=True, fill_status=False, fill_company=False, fill_dept=False, fill_main=False)),
            ("type_parent_status", dict(fill_top_select=False, fill_type=True, fill_parent=True, fill_status=True, fill_company=False, fill_dept=False, fill_main=False)),
            ("type_parent_status_company", dict(fill_top_select=False, fill_type=True, fill_parent=True, fill_status=True, fill_company=True, fill_dept=False, fill_main=False)),
            ("all_main", dict(fill_top_select=False, fill_type=True, fill_parent=True, fill_status=True, fill_company=True, fill_dept=True, fill_main=True)),
        ]

        for label, kwargs in attempts:
            try:
                res = _attempt(page, base, label, **kwargs)
                results.append(res)
                page.screenshot(path=str(OUT_DIR / f"save_{label}.png"), full_page=True)
                if res["saved"]:
                    print(f"  >>> first successful save attempt: {label}")
                    break
            except Exception as exc:
                results.append({"label": label, "error": repr(exc), "url": page.url})
                print(f"  EXC: {exc!r}")

        (OUT_DIR / "save_attempts.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        browser.close()


if __name__ == "__main__":
    main()
