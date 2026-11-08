const { chromium } = require('playwright');
const CLICK = [['LG','https://careers.lg.com/apply','[class*=title], [class*=Title], li a, .list a'],['현대차','https://talent.hyundai.com/apply/applyList.hc','.list_wrap a, .tit a, a[href*="javascript"]'],['CJ','https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo','a[onclick*="goNewDetail"]']];
const SNIFF = [['네이버','https://recruit.navercorp.com/rcrt/list.do'],['삼성','https://www.samsungcareers.com/hr/'],['배민','https://career.woowahan.com/recruitment'],['한화','https://www.hanwhain.com/portal/apply/notice/list'],['롯데','https://www.lotteinfo.com/recruit'],['Google','https://www.google.com/about/careers/applications/jobs/results/?location=Seoul']];
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36', locale: 'ko-KR' });
  for (const [n, u, sel] of CLICK) {
    const p = await ctx.newPage();
    try {
      await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(8000);
      const before = p.url();
      const els = await p.$$(sel);
      let done = false;
      for (const e of els.slice(0, 40)) {
        const t = ((await e.innerText().catch(() => '')) || '').trim();
        if (t.length < 6) continue;
        const [popup] = await Promise.all([ctx.waitForEvent('page', { timeout: 6000 }).catch(() => null), e.click({ timeout: 4000 }).catch(() => null)]);
        await p.waitForTimeout(4000);
        const now = popup ? popup.url() : p.url();
        if (now !== before) { console.log(`CLK ${n} text=${t.slice(0, 40).replace(/\s+/g,' ')} -> ${now}`); done = true; break; }
      }
      if (!done) console.log(`CLK ${n} no navigation (els=${els.length})`);
    } catch (e) { console.log(`CLK ${n} ERR ${String(e).slice(0, 80)}`); }
    await p.close();
  }
  for (const [n, u] of SNIFF) {
    const p = await ctx.newPage(); const seen = [];
    p.on('response', async (r) => { const rq = r.request(); if (!['xhr', 'fetch', 'document'].includes(rq.resourceType())) return; const ct = r.headers()['content-type'] || ''; let t = ''; try { t = await r.text(); } catch (e) {} if (/(공고|채용|recruit|job|anno|position)/i.test(t.slice(0, 5000)) && rq.resourceType() !== 'document') seen.push(`${rq.method()} ${r.url().slice(0, 200)} [${ct.slice(0, 25)}] body=${(rq.postData() || '').slice(0, 150)} :: ${t.slice(0, 200).replace(/\s+/g, ' ')}`); });
    try { await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(10000); } catch (e) { seen.push('ERR ' + String(e).slice(0, 80)); }
    console.log(`SNF ${n} final=${p.url().slice(0, 100)} n=${seen.length}`); seen.slice(0, 5).forEach((s) => console.log(`  SNF ${n} ${s}`));
    await p.close();
  }
  await b.close();
})();
