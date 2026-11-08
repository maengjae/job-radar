// 임시: 실제 브라우저로 공고 링크 도착지 확인
const { chromium } = require('playwright');
const samples = require('./probe_samples.json');
const extra = [];
for (const s of samples) {
  const m = s.id.match(/^greenhouse:(\w+):(\d+)$/);
  if (m && ['daangn','sendbird','furiosaai','coupang','stripe','thunes'].includes(m[1])) {
    const [_, b, id] = m;
    const cands = {
      daangn: [`https://about.daangn.com/jobs/${id}/`, `https://about.daangn.com/jobs/${id}`, `https://about.daangn.com/jobs/?gh_jid=${id}`],
      sendbird: [`https://delight.ai/careers/${id}`, `https://sendbird.com/careers/${id}`],
      furiosaai: [`https://furiosa.ai/careers/${id}`],
      coupang: [`https://www.coupang.jobs/kr/jobs/${id}/`],
      stripe: [`https://stripe.com/jobs/listing/x/${id}`],
      thunes: [`https://www.thunes.com/jobs/${id}`],
    }[b] || [];
    cands.forEach(u => extra.push({ ...s, url: u, candidate: true }));
  }
}
(async () => {
  const b = await chromium.launch();
  for (const s of [...samples, ...extra]) {
    const p = await b.newPage();
    try {
      await p.goto(s.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await p.waitForTimeout(6000);
      const body = await p.evaluate(() => document.body ? document.body.innerText : '');
      const key = s.title.replace(/\[.*?\]/g, '').trim().slice(0, 25);
      console.log(`RES ${s.candidate ? 'CAND' : 'CUR '} ${s.company} | ok=${body.includes(key)} | final=${p.url().slice(0, 110)} | key=${key}`);
    } catch (e) {
      console.log(`RES ${s.candidate ? 'CAND' : 'CUR '} ${s.company} | ERR ${String(e).slice(0, 80)} | ${s.url}`);
    }
    await p.close();
  }
  await b.close();
})();
