from playwright.sync_api import sync_playwright

tunnel_url = "https://instance-presence-testing-eclipse.trycloudflare.com"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page(ignore_https_errors=True)
    page.goto(f"{tunnel_url}/login", wait_until="domcontentloaded")
    
    forms = page.query_selector_all("form")
    print(f"Forms count: {len(forms)}")
    for i, f in enumerate(forms):
        action = f.get_attribute("action")
        form_id = f.get_attribute("id")
        inputs = [(inp.get_attribute("name"), inp.get_attribute("id"), inp.is_visible()) for inp in f.query_selector_all("input")]
        buttons = [(btn.text_content().strip(), btn.get_attribute("id"), btn.is_visible()) for btn in f.query_selector_all("button")]
        print(f"Form {i}: id={form_id}, action={action}")
        print(f"  Inputs: {inputs}")
        print(f"  Buttons: {buttons}")
        
    browser.close()
