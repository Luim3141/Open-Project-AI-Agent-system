from playwright.sync_api import sync_playwright

tunnel_url = "https://instance-presence-testing-eclipse.trycloudflare.com"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(ignore_https_errors=True)
    page.goto(f"{tunnel_url}/login", wait_until="domcontentloaded")
    
    page.fill("#username", "pm")
    page.fill("#password", "PUBLICATION_REDACTED")
    
    print("Clicking submit inside Form 1...")
    page.click("form:has(#username) button[type='submit']")
    page.wait_for_timeout(4000)
    
    print("URL after login click:", page.url)
    print("Title after login click:", page.title())
    
    flashes = [el.text_content().strip() for el in page.query_selector_all(".flash, .op-toast, [role='alert'], .notification-box")]
    print("Flashes/Alerts found:", flashes)
    
    # Check if user is logged in
    user_menu = page.query_selector("#user-menu, .op-app-header--user-menu, #account-nav")
    print("User menu found:", user_menu is not None)
    
    browser.close()
