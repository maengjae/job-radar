import json, re, urllib.request, urllib.robotparser, urllib.parse
H = {"User-Agent": "job-radar/1.0 (personal job dashboard)"}
def get(u, data=None, ct=None):
    h = dict(H)
    if ct: h["Content-Type"] = ct
    return urllib.request.urlopen(urllib.request.Request(u, data=data, headers=h), timeout=30).read().decode("utf-8", "replace")
def robots(u):
    p = urllib.parse.urlparse(u); site = f"{p.scheme}://{p.netloc}"
    try: txt = get(site + "/robots.txt")
    except Exception as e: return f"no robots.txt ({getattr(e,'code',e)})"
    rp = urllib.robotparser.RobotFileParser(); rp.parse(txt.splitlines()); return f"allowed={rp.can_fetch('job-radar', u)} :: {txt[:200]!r}"
for u in ["https://career.woowahan.com/w1/recruits", "https://www.samsungcareers.com/hr/list.data", "https://recruit.navercorp.com/rcrt/list.do", "https://recruit.navercorp.com/rcrt/loadJobList.do", "https://www.skcareers.com/Recruit/GetRecruitList", "https://api.careers.lg.com/rmk/search/retrieveJobNoticesList", "https://careers.kakao.com/public/api/job-list"]:
    print("ROB", u, robots(u), flush=True)
d = json.loads(get("https://career.woowahan.com/w1/recruits?recruitCampaignSeq=0&page=0&size=60&sort=updateDate%2Cdesc"))
it = d["data"]["list"]; print("WOO n", len(it), "keys", list(it[0].keys())); print("WOO ex", json.dumps({k: str(v)[:50] for k, v in it[0].items()}, ensure_ascii=False)[:900])
h = get("https://www.samsungcareers.com/hr/list.data", b"currentPageNo=1&intNo=0&strVal=&strTxt=&strKey=&strCompany=&strType=&strOrderBy=&strEntity=", "application/x-www-form-urlencoded; charset=UTF-8")
print("SAM", re.sub(r"\s+", " ", h)[:1800])
n = get("https://recruit.navercorp.com/rcrt/list.do")
i = n.find("annoId"); print("NAV len", len(n), "annoId at", i, re.sub(r"\s+", " ", n[max(0, i-600): i+900]) if i > 0 else re.findall(r"(?:loadJobList|\.do)[^\"']{0,80}", n)[:20])
try:
    j = get("https://recruit.navercorp.com/rcrt/loadJobList.do?annoId=&sw=&subJobCdArr=&sysCompanyCdArr=&empTypeCdArr=&entTypeCdArr=&workAreaCdArr=&firstIndex=0")
    print("NAVAPI", j[:800])
except Exception as e: print("NAVAPI ERR", e)
