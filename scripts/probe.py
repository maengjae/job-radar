import json, urllib.request, urllib.robotparser, urllib.parse
H = {"User-Agent": "job-radar/1.0 (personal job dashboard)", "Accept": "application/json"}
def call(u, body=None, form=False):
    h = dict(H); data = None
    if body is not None:
        if form: data = urllib.parse.urlencode(body).encode(); h["Content-Type"] = "application/x-www-form-urlencoded"
        else: data = json.dumps(body).encode(); h["Content-Type"] = "application/json"
    return json.loads(urllib.request.urlopen(urllib.request.Request(u, data=data, headers=h), timeout=30).read().decode("utf-8", "replace"))
def robots(u):
    p = urllib.parse.urlparse(u); site = f"{p.scheme}://{p.netloc}"
    try: txt = urllib.request.urlopen(urllib.request.Request(site + "/robots.txt", headers=H), timeout=15).read().decode("utf-8", "replace")
    except Exception as e: return f"no robots.txt ({getattr(e,'code',e)})"
    rp = urllib.robotparser.RobotFileParser(); rp.parse(txt.splitlines())
    return f"allowed={rp.can_fetch('job-radar', u)}"
T = [
 ("LG", "https://api.careers.lg.com/rmk/search/retrieveJobNoticesList", {"lnbSearch":"","hashTagText":"","recDate":"POST_START_DATE","order":"DESC","careerList":[],"companyCodeList":[],"desireLocList":[],"jobGroupList":[]}, False, lambda d: d["data"]["jobNoticeList"]),
 ("SK", "https://www.skcareers.com/Recruit/GetRecruitList", {"sort":"2","searchText":"","corpCode":"","jobRole":"0","recruitType":"","workingType":"","workingRegion":""}, True, lambda d: d["list"]),
 ("현대차", "https://talent.hyundai.com/api/rec/AP-HM-FO-02700?hgrCd=1&lang=ko&page=1&pageblock=100&searchFieldList=&searchOccupList=&searchPlaceList=&searchSectorList=&searchText=&jdSec=&srcOrd=", None, False, lambda d: d["data"]["list"]),
 ("CJ", "https://recruit.cj.net/recruit/ko/recruit/recruit/searchNewGonggoList.fo", {"pageVal":"1","pageIndex":"100","orderDesc":"1","sch_title":"","arrGubun":"","arrRecBu":"","arrRecJob":"","arrRecArea":"","schArea":"N"}, False, lambda d: d["ds_newRecruitList"]),
 ("KB", "https://careers.kbfg.com/api/career/recruites?page=1&pageSize=50&totalCount=0&totalPageCount=-1&ord=EDDT&affcomCd=&enggTypCd=&carrTypCd=&jbClsfiCd=", None, False, lambda d: d["result"]["recruties"]),
 ("카카오", "https://careers.kakao.com/public/api/job-list?skillSet=&part=TECHNOLOGY&company=ALL&keyword=&employeeType=&page=1", None, False, lambda d: d["jobList"]),
 ("카카오뱅크", "https://recruit.kakaobank.com/api/recruits", {"pageNumber":1,"pageSize":20}, False, lambda d: d["list"]),
 ("Microsoft", "https://apply.careers.microsoft.com/api/pcsx/search?domain=microsoft.com&query=&location=Korea&start=0", None, False, lambda d: d["data"]["positions"]),
 ("Oracle", "https://eeho.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList&finder=findReqs;siteNumber=CX_45001,limit=50,keyword=Korea", None, False, lambda d: d["items"][0]["requisitionList"]),
]
for name, u, body, form, pick in T:
    print("ROB", name, robots(u), flush=True)
    try:
        d = call(u, body, form); items = pick(d)
        print("DAT", name, "n=", len(items), "keys=", list(items[0].keys())[:40] if items else None, flush=True)
        if items:
            x = items[0]; print("EX ", name, json.dumps({k: (str(v)[:60] if not isinstance(v,(dict,list)) else '...') for k, v in x.items()}, ensure_ascii=False)[:1200], flush=True)
        if name == "Microsoft": print("EX ", name, "count", d["data"].get("count"), [p["locations"] for p in items[:5]])
    except Exception as e:
        print("ERR", name, repr(e)[:200], flush=True)
