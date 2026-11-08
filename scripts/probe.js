const { chromium } = require('playwright');
const S = [['LG','https://careers.lg.com/apply'],['SK','https://www.skcareers.com/Recruit'],['현대차','https://talent.hyundai.com/apply/applyList.hc'],['CJ','https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo'],['KB','https://careers.kbfg.com/recruit'],['카카오','https://careers.kakao.com/jobs'],['카카오뱅크','https://recruit.kakaobank.com/jobs'],['Microsoft','https://apply.careers.microsoft.com/careers?location=Korea'],['Oracle','https://careers.oracle.com/en/sites/jobsearch/jobs?location=Korea']];
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36', locale: 'ko-KR' });
  for (const [n, u] of S) {
    const p = await ctx.newPage();
    try { await p.goto(u, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(9000);
      const links = await p.evaluate(() => [...document.querySelectorAll('a[href], [onclick]')].map(a => (a.getAttribute('href') || '') + ' ' + (a.getAttribute('onclick') || '')).filter(t => /detail|view|job|anno|recruit|position|\d{4,}/i.test(t)).slice(0, 400));
      const uniq = [...new Set(links)].filter(t => /\d{3,}/.test(t)).slice(0, 6);
      console.log(`LNK ${n} ${JSON.stringify(uniq).slice(0, 700)}`);
    } catch (e) { console.log(`LNK ${n} ERR ${String(e).slice(0, 80)}`); }
    await p.close();
  }
  await b.close();
})();
