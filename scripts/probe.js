const { chromium } = require('playwright');
const S = require('./probe_samples.json');
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36', locale: 'ko-KR', ignoreHTTPSErrors: false });
  for (const s of S) {
    const p = await ctx.newPage();
    try {
      const r = await p.goto(s.url, { waitUntil: 'domcontentloaded', timeout: 30000 }); await p.waitForTimeout(7000);
      const body = await p.evaluate(() => document.body ? document.body.innerText : '');
      const key = s.title.replace(/\[.*?\]|\(.*?\)/g, '').trim().slice(0, 14);
      console.log(`RES ${s.company} | status=${r && r.status()} | ok=${key ? body.includes(key) : 'n/a'} | title=${(await p.title()).slice(0, 40)} | final=${p.url().slice(0, 90)} | key=${key}`);
    } catch (e) { console.log(`RES ${s.company} | ERR ${String(e).slice(0, 70)} | ${s.url}`); }
    await p.close();
  }
  await b.close();
})();
