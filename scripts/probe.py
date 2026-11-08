"""임시: 외국계 회사 채용 시스템·서울 공고 확인."""
import json, re, urllib.request, urllib.robotparser
UA = {"User-Agent": "job-radar/1.0 (personal job dashboard)", "Accept": "application/json", "Content-Type": "application/json"}
SEOUL = re.compile(r"seoul|korea|서울|한국|pangyo|판교", re.I)
def req(u, body=None):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(body).encode() if body is not None else None, headers=UA), timeout=25)
        return r.status, json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:
        return getattr(e, "code", str(e)[:70]), None
def robots(site, path):
    rp = urllib.robotparser.RobotFileParser()
    try:
        txt = urllib.request.urlopen(urllib.request.Request(site + "/robots.txt", headers={"User-Agent": UA["User-Agent"]}), timeout=15).read().decode("utf-8", "replace")
    except Exception as e:
        return f"no robots ({getattr(e,'code',e)})"
    rp.parse(txt.splitlines()); return rp.can_fetch("job-radar", site + path)
# Workday
WD = [("salesforce","wd12","External_Career_Site"),("nvidia","wd5","NVIDIAExternalCareerSite"),("redhat","wd5","jobs"),("broadcom","wd1","External_Career"),
      ("adobe","wd5","external_experienced"),("dell","wd1","External"),("intel","wd1","External"),("amdocs","wd3","Amdocs"),("keysight","wd5","Keysight"),
      ("aptiv","wd5","APTIV_CAREERS"),("thermofisher","wd5","ThermoFisherCareers"),("abinbev","wd3","AB_InBev_Careers"),("3ds","wd3","DS_Careers"),
      ("workday","wd5","Workday"),("mastercard","wd1","CorporateCareers"),("citi","wd5","2"),("hpe","wd5","Jobsathpe"),("autodesk","wd1","Ext"),("paypal","wd1","jobs")]
print("ROBOTS workday", robots("https://salesforce.wd12.myworkdayjobs.com", "/wday/cxs/salesforce/External_Career_Site/jobs"))
for t, w, s in WD:
    st, d = req(f"https://{t}.{w}.myworkdayjobs.com/wday/cxs/{t}/{s}/jobs", {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "Seoul"})
    if d is None: print("WD", t, w, s, "ERR", st); continue
    posts = d.get("jobPostings", [])
    seoul = [p for p in posts if SEOUL.search(p.get("locationsText", "") + " " + p.get("title", ""))]
    print("WD", t, w, s, "total", d.get("total"), "seoulish", len(seoul), [ (p["title"][:45], p.get("locationsText"), p.get("externalPath","")[:50]) for p in seoul[:3]], flush=True)
# SmartRecruiters
for c in ["ServiceNow", "BoschGroup", "Visa", "Canva", "SiemensHealthineers", "Equinix", "Wise"]:
    st, d = req(f"https://api.smartrecruiters.com/v1/companies/{c}/postings?limit=100&country=kr")
    print("SR", c, st if d is None else f"total(kr)={d.get('totalFound')} ex={[ (j['name'][:40], j.get('location',{}).get('city')) for j in d.get('content',[])[:3]]}", flush=True)
# Greenhouse / Lever / Ashby
for ats, u in [("gh","https://boards-api.greenhouse.io/v1/boards/{}/jobs"),("lever","https://api.lever.co/v0/postings/{}?mode=json"),("ashby","https://api.ashbyhq.com/posting-api/job-board/{}")]:
    for c in ["yanolja","noluniverse","interparktriple","linepluscorp","lineplus","toss","amdocs","keysight","queueit","snowflakecomputing","confluent","hashicorp","servicenow","nvidia","redhat","salesforce","sap","oracle","ibm","dynatrace","newrelic","pagerduty","atlassian","zendesk","freshworks","okta","twilio","segment","docusign","dropbox","airbnb","uber","doordash","spotify","linkedin","figma","notion","miro","sendbird","channelio"]:
        st, d = req(u.format(c))
        if d is None: continue
        jobs = d if isinstance(d, list) else d.get("jobs", [])
        if not jobs: continue
        loc = lambda j: (j.get("location") or {}).get("name", "") if ats=="gh" else ((j.get("categories") or {}).get("location","") if ats=="lever" else j.get("location",""))
        sj = [j for j in jobs if SEOUL.search(loc(j) or "")]
        print("ATS", ats, c, "total", len(jobs), "seoul", len(sj), [ (j.get("title") or j.get("text"))[:40] for j in sj[:3]], flush=True)
# Amazon / Toss / LINE
print("ROBOTS amazon", robots("https://www.amazon.jobs", "/en/search.json"))
st, d = req("https://www.amazon.jobs/en/search.json?normalized_country_code%5B%5D=KOR&result_limit=100&offset=0")
print("AMZ", st if d is None else f"hits={d.get('hits')} ex={[ (j['title'][:40], j.get('location'), j.get('job_path')) for j in d.get('jobs',[])[:3]]} keys={list(d.get('jobs',[{}])[0].keys())[:20] if d.get('jobs') else None}", flush=True)
print("ROBOTS toss", robots("https://api-public.toss.im", "/api/v3/ipd-eggnog/career/jobs"), robots("https://toss.im", "/career/jobs"))
st, d = req("https://api-public.toss.im/api/v3/ipd-eggnog/career/jobs")
print("TOSS", st if d is None else str(d)[:600], flush=True)
print("ROBOTS line", robots("https://careers.linecorp.com", "/page-data/ko/jobs/page-data.json"))
st, d = req("https://careers.linecorp.com/page-data/ko/jobs/page-data.json")
print("LINE", st if d is None else str(d)[:500], flush=True)
