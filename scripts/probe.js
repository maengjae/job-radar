const https = require('https');
https.get({host:'careers.linecorp.com', path:'/page-data/ko/jobs/page-data.json', headers:{'User-Agent':'job-radar/1.0'}}, r => { let b=''; r.on('data', c => b += c); r.on('end', () => {
  const e = JSON.parse(b).result.data.allStrapiJobs.edges.map(x => x.node);
  console.log('RES keys', Object.keys(e[0]).join(','));
  for (const n of e.filter(n => [154, 1123, 2956, '154', '1123', '2956'].includes(n.strapiId) || ['154','1123','2956'].includes(String(n.id)))) {
    const o = {}; for (const [k, v] of Object.entries(n)) if (typeof v !== 'object' || v === null) o[k] = String(v).slice(0, 40);
    console.log('RES node', JSON.stringify(o));
  }
  const cnt = {}; for (const n of e) for (const k of ['publish','is_open','status','end_date','active','is_active']) if (k in n) cnt[k+'='+String(n[k]).slice(0,10)] = (cnt[k+'='+String(n[k]).slice(0,10)]||0)+1;
  console.log('RES counts', JSON.stringify(cnt).slice(0, 600));
});});
