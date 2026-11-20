const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  await context.addCookies([{ name: '_open_project_session', value: '06e1ddb8e85385e78a2424c2733c8dd8', domain: '127.0.0.1', path: '/' }]);
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:18088/projects/ai-dev-demo/qldapm-ai?ui=modern');
  await page.waitForLoadState('networkidle');

  const forms = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('form')).map(f => ({
      id: f.id,
      className: f.className,
      action: f.action,
      method: f.method,
      btnText: f.querySelector('button') ? f.querySelector('button').innerText.trim() : null,
      inputs: Array.from(f.querySelectorAll('input')).map(i => ({ name: i.name, value: i.value }))
    }));
  });

  console.log('FORMS ON PAGE:');
  console.log(JSON.stringify(forms, null, 2));

  await browser.close();
})();
