from playwright.sync_api import sync_playwright


def dump_buttons(page, title: str) -> None:
    print(f"\n== {title} ==")
    btns = page.locator("button, .ant-btn")
    seen = set()
    for i in range(min(btns.count(), 80)):
        t = (btns.nth(i).inner_text() or "").strip().replace("\n", " ")
        if t and t not in seen:
            seen.add(t)
            print("-", t)


def main() -> None:
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        c = b.new_context(ignore_https_errors=True)
        page = c.new_page()

        page.goto("https://localhost:8001/user/login", wait_until="domcontentloaded")
        page.locator("#login").fill("Admin")
        page.locator("#password").fill("123")
        page.locator("button[type='submit']").click()
        page.wait_for_timeout(1500)

        page.get_by_text("Directories", exact=True).click()
        page.wait_for_timeout(400)
        page.get_by_text("Devices", exact=True).click()
        page.wait_for_timeout(1500)

        print("URL:", page.url)
        dump_buttons(page, "Devices page buttons")

        items = page.locator(".ant-list-item")
        print("list items:", items.count())
        if items.count() > 0:
            items.first.click()
            page.wait_for_timeout(800)
            dump_buttons(page, "After opening first device")

        if page.get_by_text("New device", exact=True).count() > 0:
            page.get_by_text("New device", exact=True).click()
            page.wait_for_timeout(800)
            dump_buttons(page, "After opening new device form")

        page.screenshot(path="probe-device-actions.png", full_page=True)
        print("saved probe-device-actions.png")

        c.close()
        b.close()


if __name__ == "__main__":
    main()

