const { chromium } = require('playwright');
const https = require('https');
https.get({ host: 'recruit.lotte.co.kr', path: '/robots.txt', headers: { 'User-Agent': 'job-radar/1.0' } }, (r) => { let b = ''; r.on('data', (c) => (b += c)); r.on('end', () => console.log('ROB', r.statusCode, JSON.stringify(b.slice(0, 400)))); }).on('error', (e) => console.log('ROB ERR', e.message));
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36', locale: 'ko-KR' });
  const p = await ctx.newPage(); const hits = [];
  p.on('response', async (r) => { const rq = r.request(); if (!['xhr', 'fetch'].includes(rq.resourceType())) return; let t = ''; try { t = await r.text(); } catch (e) {} if (t.length > 200) hits.push(`${rq.method()} ${r.url().slice(0, 200)} [${(r.headers()['content-type'] || '').slice(0, 20)}] body=${(rq.postData() || '').slice(0, 250)} :: ${t.slice(0, 300).replace(/\s+/g, ' ')}`); });
  await p.goto('https://recruit.lotte.co.kr/apply/announcement/', { waitUntil: 'domcontentloaded', timeout: 40000 }).catch((e) => console.log('GOTO', e.message)); await p.waitForTimeout(10000);
  console.log('FINAL', p.url(), await p.title()); hits.slice(0, 8).forEach((h) => console.log('API', h));
  const links = await p.evaluate(() => [...document.querySelectorAll('a[href]')].map((a) => a.href).filter((h) => /detail/.test(h)).slice(0, 5)); console.log('LNK', JSON.stringify(links));
  await b.close();
})();
