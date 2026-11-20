from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    page = browser.new_page(ignore_https_errors=True)
    page.goto('https://instance-presence-testing-eclipse.trycloudflare.com/login')
    page.fill('#username', 'fe')
    page.fill('#password', 'PUBLICATION_REDACTED')
    page.click("form:has(#username) button[type='submit']")
    page.wait_for_load_state('domcontentloaded')
    time.sleep(2)
    print('FE Current URL:', page.url)
    flash = page.locator('.op-toast--content, .flash, .notification-box--content').all_text_contents()
    print('Flash messages:', flash)
    browser.close()
