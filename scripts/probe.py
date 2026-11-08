"""임시: 회사 후보·공고 사이트 확인."""
import json, re, urllib.request, urllib.robotparser
UA={"User-Agent":"job-radar/1.0 (personal job dashboard)"}
def get(u, raw=False):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20) as r:
            b=r.read().decode("utf-8","replace"); return r.status,(b if raw else json.loads(b))
    except Exception as e:
        return getattr(e,"code",str(e)[:60]), None
ASIA=re.compile(r"japan|tokyo|osaka|fukuoka|singapore|korea|seoul|taiwan|taipei|hong kong|vietnam|thailand|bangkok|malaysia|kuala|indonesia|jakarta|philippines|manila|apac|asia|anywhere|worldwide",re.I)
ENG=re.compile(r"engineer|developer|sre|devops",re.I)
C={
 "greenhouse":("https://boards-api.greenhouse.io/v1/boards/{}/jobs",lambda d:[(j["title"],(j.get("location") or {}).get("name","")) for j in d.get("jobs",[])]),
 "lever":("https://api.lever.co/v0/postings/{}?mode=json",lambda d:[(j["text"]," / ".join((j.get("categories") or {}).get("allLocations") or [(j.get("categories") or {}).get("location","")])) for j in d] if isinstance(d,list) else []),
 "ashby":("https://api.ashbyhq.com/posting-api/job-board/{}",lambda d:[(j["title"],j.get("location","")+" "+" ".join(x.get("location","") for x in j.get("secondaryLocations") or [])) for j in d.get("jobs",[])]),
 "workable":("https://apply.workable.com/api/v1/widget/accounts/{}",lambda d:[(j["title"],f'{j.get("city","")} {j.get("country","")}') for j in d.get("jobs",[])]),
}
cands="""paidy ubie autify layerx smarthr moneyforward freee sansan kraken octopusenergy wise indeed rakuten mercariglobal mercari-india hennge tier4 preferred-networks pfn rapyuta mujin telexistence beatrust gaudiy plaid treasuredata treasure-data degica komoju gojek grab ninjavan ninja-van xendit thunes nium airwallex aspire aspireapp funding-societies fundingsocieties carousell propertyguru shopback 2c2p kredivo stashaway endowus syfe tiktok bytedance binance cryptocom crypto okx bybit circle ripple kraken-digital coinhako sendbird moloco hyperconnect devsisters riiid rebellions furiosaai furiosa upstage twelvelabs lunit vuno sendbird-korea channelcorp ab180 mathpresso classting dable buzzvil socar bucketplace ohouse daangn karrot musinsa krafton nexon netmarble pubg yanolja noluniversi noluniverse kurly coupang woowahan toss viva-republica vivarepublica dunamu lambda256 hashed chainalysis consensys alchemy anthropic openai databricks snowflake confluent hashicorp elastic grafanalabs grafana-labs temporal vercel netlify supabase cockroachlabs pingcap timescale clickhouse redpanda posthog sentry docker canonical mozilla automattic toptal zapier gitlab deel remote rippling oyster papayaglobal hubspot atlassian canva-careers employmenthero safetyculture airtasker linktree culture-amp cultureamp tyro"""
cands=sorted(set(cands.split()))
for c in cands:
    for ats,(u,f) in C.items():
        s,d=get(u.format(c))
        if d is None: continue
        try: jobs=f(d)
        except Exception: continue
        if not jobs: continue
        hit=[t for t,l in jobs if ASIA.search(l or "") and ENG.search(t)]
        print(f"FOUND {ats}:{c} total={len(jobs)} asia_eng={len(hit)} ex={hit[:2]}",flush=True)
# 공고 모음 사이트: API·robots 확인
for name,api in [("remoteok","https://remoteok.com/api"),("remotive","https://remotive.com/api/remote-jobs?category=software-dev&limit=5"),("himalayas","https://himalayas.app/jobs/api?limit=5"),("arbeitnow","https://www.arbeitnow.com/api/job-board-api")]:
    s,d=get(api); print("API",name,s,(str(d)[:300] if d else ""),flush=True)
for site,path in [("https://japan-dev.com","/jobs"),("https://www.tokyodev.com","/jobs"),("https://weworkremotely.com","/categories/remote-back-end-programming-jobs.rss"),("https://www.wanted.co.kr","/wdlist/518"),("https://career.rememberapp.co.kr","/job/postings"),("https://jasoseol.com","/recruit"),("https://www.jumpit.co.kr","/positions"),("https://www.catch.co.kr","/NCS/RecruitSearch"),("https://www.saramin.co.kr","/zf_user/jobs/list/job-category"),("https://www.jobkorea.co.kr","/recruit/joblist"),("https://www.linkedin.com","/jobs/search"),("https://www.mycareersfuture.gov.sg","/search")]:
    rp=urllib.robotparser.RobotFileParser(); s,txt=get(site+"/robots.txt",raw=True)
    if txt is None: print("ROBOTS",site,"no robots",s); continue
    rp.parse(txt.splitlines()); print("ROBOTS",site,path,"allowed(*)=",rp.can_fetch("*",site+path),"allowed(job-radar)=",rp.can_fetch("job-radar",site+path),flush=True)
