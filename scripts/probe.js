const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36', locale: 'ko-KR' });
  let p = await ctx.newPage();
  await p.goto('https://www.samsungcareers.com/hr/', { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(8000);
  const a = await p.$('a[data-value]');
  if (a) { const [pop] = await Promise.all([ctx.waitForEvent('page', { timeout: 6000 }).catch(() => null), a.click().catch(() => null)]); await p.waitForTimeout(5000); console.log('SAM click ->', pop ? pop.url() : p.url()); }
  const js = await p.evaluate(() => [...document.scripts].map(s => s.textContent).join('\n').match(/.{0,120}(detail|view)\.?[a-z]*\?.{0,120}/gi) || []);
  console.log('SAM js', JSON.stringify(js.slice(0, 5)).slice(0, 900));
  await p.close();
  p = await ctx.newPage(); const seen = [];
  p.on('request', (rq) => { if (/hwadm|api/.test(rq.url()) && ['xhr', 'fetch'].includes(rq.resourceType())) seen.push(`${rq.method()} ${rq.url().slice(0, 200)} body=${(rq.postData() || '').slice(0, 200)}`); });
  await p.goto('https://www.hanwhain.com/portal/apply/notice/list', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {}); await p.waitForTimeout(12000);
  console.log('HAN final', p.url()); seen.slice(0, 12).forEach((s) => console.log('HAN', s));
  const links = await p.evaluate(() => [...document.querySelectorAll('a[href]')].map(a => a.href).filter(h => /notice|apply|detail|\d{4,}/.test(h)).slice(0, 8));
  console.log('HAN links', JSON.stringify(links).slice(0, 800));
  await b.close();
})();
