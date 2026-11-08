const { chromium } = require('playwright');
const samples = require('./probe_samples.json');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36', locale: 'ko-KR' });
  for (const s of samples) {
    const p = await ctx.newPage();
    try {
      await p.goto(s.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await p.waitForTimeout(8000);
      const body = await p.evaluate(() => document.body ? document.body.innerText : '');
      const key = s.title.replace(/\[.*?\]|\(.*?\)/g, '').trim().slice(0, 18);
      console.log(`RES ${s.company} | ok=${body.includes(key)} | final=${p.url().slice(0, 100)} | key=${key}`);
    } catch (e) { console.log(`RES ${s.company} | ERR ${String(e).slice(0, 60)} | ${s.url}`); }
    await p.close();
  }
  await b.close();
})();
