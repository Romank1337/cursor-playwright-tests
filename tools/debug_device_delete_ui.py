from playwright.sync_api import sync_playwright
import time
from urllib.parse import urlsplit


def main() -> None:
    login_url = "https://localhost:8001/user/login"
    username = "Admin"
    password = "123"
    suffix = str(int(time.time()))
    device_name = f"AUTOTEST-DEBUG-{suffix}"
    device_uid = f"AUTOTEST-DEBUG-UID-{suffix}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        page.goto(login_url, wait_until="domcontentloaded")
        page.locator("#login").fill(username)
        page.locator("#password").fill(password)
        page.locator("button[type='submit']").click()
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(800)

        parsed = urlsplit(login_url)
        page.goto(f"{parsed.scheme}://{parsed.netloc}/list/devices", wait_until="domcontentloaded")
        page.wait_for_timeout(1200)

        page.get_by_text("New device", exact=True).click()
        page.wait_for_timeout(400)
        page.locator("#control-device_Name").fill(device_name)
        page.locator("#control-device_UniqueDeviceID").fill(device_uid)
        page.locator("#control-device_Comment").fill("debug delete ui")

        native_options = page.locator("#control-device_DeviceTypeId option")
        if native_options.count() > 1:
            page.locator("#control-device_DeviceTypeId").select_option(index=1)
        else:
            root = page.locator("#control-device_DeviceTypeId").first
            if root.count() > 0:
                root.click()
                page.wait_for_timeout(200)
                first_option = page.locator(".ant-select-item-option").first
                if first_option.count() > 0:
                    first_option.click()

        page.get_by_text("Save", exact=True).click()
        page.wait_for_timeout(400)
        page.get_by_text("Apply", exact=True).click()
        page.wait_for_timeout(800)

        row = page.locator(".ant-list-item", has_text=device_name).first
        print("ROW FOUND:", row.count() > 0)
        if row.count() == 0:
            browser.close()
            return

        page.get_by_text("Delete all", exact=True).click()
        page.wait_for_timeout(500)
        modal_buttons = page.locator(".ant-modal .ant-modal-footer button")
        print("MODAL BUTTONS:", modal_buttons.count())
        for i in range(modal_buttons.count()):
            b = modal_buttons.nth(i)
            text = (b.inner_text(timeout=500) or "").strip().replace("\n", " ")
            cls = b.get_attribute("class")
            print(f"modal[{i}] text={text!r} class={cls!r}")

        browser.close()


if __name__ == "__main__":
    main()
