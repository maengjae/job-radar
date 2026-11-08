// 임시: 채용 페이지가 공고를 불러오는 API 주소 찾기
const { chromium } = require('playwright');
const SITES = [
  ['삼성', 'https://www.samsungcareers.com/hr/'],
  ['LG', 'https://careers.lg.com/apply'],
  ['SK', 'https://www.skcareers.com/Recruit'],
  ['현대차', 'https://talent.hyundai.com/apply/applyList.hc'],
  ['한화', 'https://www.hanwhain.com/web/apply/notification/list.do'],
  ['롯데', 'https://recruit.lotte.com/apply/RecruitList'],
  ['CJ', 'https://recruit.cj.net/recruit/ko/recruit/recruit/list.fo'],
  ['KB', 'https://careers.kbfg.com'],
  ['네이버', 'https://recruit.navercorp.com/rcrt/list.do'],
  ['카카오', 'https://careers.kakao.com/jobs'],
  ['카카오뱅크', 'https://recruit.kakaobank.com/jobs'],
  ['배민', 'https://career.woowahan.com/'],
  ['Microsoft', 'https://jobs.careers.microsoft.com/global/en/search?lc=Korea'],
  ['Google', 'https://www.google.com/about/careers/applications/jobs/results/?location=Seoul'],
  ['Oracle', 'https://careers.oracle.com/jobs/#en/sites/jobsearch/requisitions?location=Korea'],
  ['SAP', 'https://jobs.sap.com/search/?locationsearch=Korea'],
  ['IBM', 'https://www.ibm.com/careers/search?field_keyword_05[0]=South%20Korea'],
  ['Rakuten', 'https://rakuten.careers/'],
  ['Grab', 'https://www.grab.careers/en/jobs/'],
  ['Shopee', 'https://careers.shopee.sg/jobs'],
  ['LY', 'https://www.lycorp.co.jp/en/recruit/'],
  ['Amdocs', 'https://www.amdocs.com/careers'],
  ['Keysight', 'https://jobs.keysight.com'],
  ['Dassault', 'https://www.3ds.com/careers'],
];
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36', locale: 'ko-KR' });
  for (const [name, url] of SITES) {
    const p = await ctx.newPage(); const hits = [];
    p.on('response', async (r) => {
      try {
        const ct = r.headers()['content-type'] || '';
        const rq = r.request();
        if (!/json/.test(ct) || !['xhr', 'fetch'].includes(rq.resourceType())) return;
        const t = await r.text();
        if (t.length < 300 || !/(title|subject|name|공고|job|recruit|anno)/i.test(t)) return;
        hits.push(`${rq.method()} ${r.url().slice(0, 230)} | body=${(rq.postData() || '').slice(0, 200)} | ${r.status()} | ${t.slice(0, 260).replace(/\s+/g, ' ')}`);
      } catch (e) {}
    });
    try { await p.goto(url, { waitUntil: 'domcontentloaded', timeout: 40000 }); await p.waitForTimeout(10000); }
    catch (e) { hits.push('GOTO ERR ' + String(e).slice(0, 80)); }
    console.log(`SITE ${name} final=${p.url().slice(0, 120)} hits=${hits.length}`);
    hits.slice(0, 6).forEach((h) => console.log(`  API ${name} ${h}`));
    await p.close();
  }
  await b.close();
})();
