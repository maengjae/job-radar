"""임시: 채용 API 회사 ID 후보 확인."""
import json, urllib.request, collections
UA={"User-Agent":"job-radar-probe/1.0"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20) as r:
            return r.status, json.loads(r.read())
    except Exception as e:
        return getattr(e,'code',str(e)[:60]), None
C={
 "greenhouse":"https://boards-api.greenhouse.io/v1/boards/{}/jobs",
 "lever":"https://api.lever.co/v0/postings/{}?mode=json",
 "ashby":"https://api.ashbyhq.com/posting-api/job-board/{}",
 "workable":"https://apply.workable.com/api/v1/widget/accounts/{}",
}
cands=["smartnews","smartnewsinc","paypay","paypaycorp","paypay-corp","jamm","jammjp","airwallex","toss","vivarepublica","tossbank","toss-bank","tosspayments","dunamu","dunamuinc","upbit","rakuten","moneyforward","money-forward","line","lycorp","preferrednetworks","wovenbytoyota","hennge","paidy","grab","shopee","seagroup","agoda","bytedance","gojek","tiktok","hyperconnect","devsisters","kraftonjobs","krafton","daangn","karrot","riiid","channelcorp","channeltalk","musinsa","yanolja","nexon","ncsoft","linepluscorp","naverz","woowahan","kurly","socar","bucketplace","lunit","upstage","twelvelabs","rebellions","furiosa","sendbird","datadog","cloudflare"]
for c in cands:
    for ats,u in C.items():
        s,d=get(u.format(c))
        if d is None: continue
        jobs=d if isinstance(d,list) else d.get("jobs",[])
        if not jobs: continue
        print(f"FOUND {ats}:{c} {len(jobs)}",flush=True)
# 0건 출처의 위치 샘플
for b in ["datadog","cloudflare","databricks","mongodb","gitlab","okta","stripe"]:
    s,d=get(C["greenhouse"].format(b))
    if d:
        cnt=collections.Counter(j.get("location",{}).get("name","") for j in d["jobs"])
        asia=[l for l in cnt if any(k in l.lower() for k in ["tokyo","japan","seoul","korea","singapore","apac","asia","taipei","sydney"])]
        print("LOC",b,asia[:8],flush=True)
