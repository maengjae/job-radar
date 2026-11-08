"""채용 공고 수집기.

sources.json에 적힌 회사들의 공개 채용 API(Greenhouse, Lever, Ashby, Workable,
SmartRecruiters, Workday, Amazon·토스·LINE 공식 API)에서 공고를 받아 직무·지역으로 거른 뒤 docs/data/에 저장한다.
표준 라이브러리만 사용한다.
"""
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "docs" / "data"
KST = dt.timezone(dt.timedelta(hours=9))
UA = "job-radar/1.0 (+https://github.com/)"

# 직무 키워드: 제목에 하나라도 있으면 수집 대상
ROLE_RULES = [
    ("IT운영/플랫폼", r"servicenow|itsm|service ?now"),
    ("클라우드/인프라", r"cloud|infra|devops|solutions? architect|\bsre\b|site reliability|platform engineer|kubernetes|클라우드|인프라|데브옵스"),
    ("백엔드", r"back[- ]?end|server|\bapi\b|java|kotlin|spring|golang|\bgo\b|백엔드|서버"),
    ("소프트웨어", r"software\b.{0,40}\b(engineer|developer)|software development|product engineer|소프트웨어|개발자"),
]
EXCLUDE = r"intern(ship)?\b|산업기능요원|전문연구요원|인턴|contract|contractor|계약직|temporary|\btemp\b|fixed[- ]term|part[- ]time|freelance|\d+[- ]?month|파견|new grad|graduate|sales|account exec|recruit|marketing|designer|android|\bios\b|front[- ]?end|data scientist|machine learning research|manager,|counsel|legal|assistant|project manager|program manager|product manager"
SENIOR = r"senior|\bsr\.?\b|staff|principal|lead|head of|director|manager|architect|distinguished|시니어|리드|수석"

# 지역 판별: 아시아·원격만 남긴다
REGION_RULES = [
    ("한국", r"korea|seoul|pangyo|busan|서울|판교|한국"),
    ("일본", r"japan|tokyo|osaka|fukuoka|kyoto|nagoya|日本|東京"),
    ("싱가포르", r"singapore"),
    ("아시아 기타", r"taiwan|taipei|hong kong|vietnam|ho chi minh|hanoi|thailand|bangkok|malaysia|kuala lumpur|indonesia|jakarta|philippines|manila|apac|asia"),
    ("원격", r"remote.*(anywhere|global|worldwide|emea.*apac|apac)|anywhere|worldwide"),
]


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def iso(v):
    """여러 형식의 날짜를 YYYY-MM-DD로."""
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return dt.datetime.fromtimestamp(v / 1000, dt.timezone.utc).date().isoformat()
    return str(v)[:10]


# 자체 채용 사이트를 쓰는 회사는 absolute_url이 채용 홈페이지(?gh_jid=)로 가므로, 브라우저에서 확인한 공고 전용 주소를 쓴다.
GH_JOB_URL = {
    "daangn": "https://careers.daangn.com/jobs/role/{id}/",
    "coupang": "https://job-boards.greenhouse.io/coupang/jobs/{id}",  # coupang.jobs의 해당 공고 페이지로 이동
    "stripe": "https://stripe.com/jobs/listing/x/{id}",
    "thunes": "https://job-boards.greenhouse.io/embed/job_app?for=thunes&token={id}",
}


def gh_url(board, j):
    if board in GH_JOB_URL:
        return GH_JOB_URL[board].format(id=j["id"])
    return j.get("absolute_url", "")


def from_greenhouse(board):
    d = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
    for j in d.get("jobs", []):
        yield {
            "jid": str(j["id"]),
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": gh_url(board, j),
            "posted": iso(j.get("first_published") or j.get("updated_at")),
        }


def from_lever(board):
    d = fetch_json(f"https://api.lever.co/v0/postings/{board}?mode=json")
    for j in d:
        cat = j.get("categories") or {}
        locs = cat.get("allLocations") or [cat.get("location", "")]
        yield {
            "jid": j["id"],
            "title": j.get("text", ""),
            "location": " / ".join(x for x in locs if x),
            "url": j.get("hostedUrl", ""),
            "posted": iso(j.get("createdAt")),
            "etype": cat.get("commitment", ""),
        }


def from_ashby(board):
    d = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}")
    for j in d.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locs = [j.get("location", "")] + [x.get("location", "") for x in j.get("secondaryLocations") or []]
        yield {
            "jid": j["id"],
            "title": j.get("title", ""),
            "location": " / ".join(x for x in locs if x) + (" (Remote)" if j.get("isRemote") else ""),
            "url": j.get("jobUrl", ""),
            "posted": iso(j.get("publishedAt")),
            "etype": j.get("employmentType", ""),
        }


def from_workable(board):
    d = fetch_json(f"https://apply.workable.com/api/v1/widget/accounts/{board}")
    for j in d.get("jobs", []):
        loc = ", ".join(x for x in [j.get("city"), j.get("state"), j.get("country")] if x)
        if j.get("telecommuting"):
            loc += " (Remote)"
        yield {
            "jid": j.get("shortcode") or j.get("url"),
            "title": j.get("title", ""),
            "location": loc,
            "url": j.get("url") or j.get("application_url", ""),
            "posted": iso(j.get("published_on") or j.get("created_at")),
            "etype": j.get("employment_type") or j.get("type") or "",
        }


def from_smartrecruiters(board):
    board, _, country = board.partition("|")
    cq = f"&country={country}" if country else ""
    offset, total = 0, None
    while total is None or offset < min(total, 1000):
        d = fetch_json(f"https://api.smartrecruiters.com/v1/companies/{board}/postings?limit=100&offset={offset}{cq}")
        total = d.get("totalFound", 0)
        for j in d.get("content", []):
            loc = j.get("location") or {}
            yield {
                "jid": j["id"],
                "title": j.get("name", ""),
                "location": ", ".join(x for x in [loc.get("city"), loc.get("country")] if x) + (" (Remote)" if loc.get("remote") else ""),
                "url": f"https://jobs.smartrecruiters.com/{board}/{j['id']}",
                "posted": iso(j.get("releasedDate")),
                "etype": (j.get("typeOfEmployment") or {}).get("label", ""),
            }
        offset += 100
        if not d.get("content"):
            break


# ── 대기업·외국계 자체 채용 시스템 ──

def post_json(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def from_workday(board):
    """board = "tenant|wdN|site|검색어" (예: nvidia|wd5|NVIDIAExternalCareerSite|Seoul)"""
    tenant, wd, site, query = (board.split("|") + ["Seoul"])[:4]
    base = f"https://{tenant}.{wd}.myworkdayjobs.com"
    offset, total = 0, None
    while total is None or offset < min(total, 400):
        d = post_json(f"{base}/wday/cxs/{tenant}/{site}/jobs", {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": query})
        if total is None:
            total = d.get("total", 0)
        posts = d.get("jobPostings", [])
        for j in posts:
            path = j.get("externalPath", "")
            loc = j.get("locationsText", "")
            if not re.search(r"korea|seoul|서울", loc, re.I):
                loc = path.split("/")[2].replace("-", " ") if path.count("/") >= 2 else loc  # "2 Locations"이면 경로의 첫 위치 사용
            yield {
                "jid": path.rsplit("_", 1)[-1] or path,
                "title": j.get("title", ""),
                "location": loc,
                "url": f"{base}/en-US/{site}{path}",
                "posted": None,
            }
        offset += 20
        if not posts:
            break


def from_amazon(board):
    """board = 국가 코드 (예: KOR)"""
    offset, hits = 0, None
    while hits is None or offset < min(hits, 500):
        d = fetch_json(f"https://www.amazon.jobs/en/search.json?normalized_country_code%5B%5D={board}&result_limit=100&offset={offset}&sort=recent")
        if hits is None:
            hits = d.get("hits", 0)
        for j in d.get("jobs", []):
            if j.get("is_intern"):
                continue
            yield {
                "jid": str(j.get("id_icims") or j.get("id")),
                "title": j.get("title", ""),
                "company": "Amazon / AWS",
                "location": j.get("location", ""),
                "url": "https://www.amazon.jobs" + j.get("job_path", ""),
                "posted": None,
                "etype": j.get("job_schedule_type", ""),
            }
        offset += 100
        if not d.get("jobs"):
            break


def from_toss(board):
    d = fetch_json("https://api-public.toss.im/api/v3/ipd-eggnog/career/jobs")
    for j in d.get("success", []):
        meta = {m.get("name"): m.get("value") for m in j.get("metadata") or []}
        etype = str(meta.get("Employment_Type") or "")
        yield {
            "jid": str(j["id"]),
            "title": j.get("title", ""),
            "company": meta.get("포지션의 소속 자회사를 선택해 주세요.") or "토스",
            "location": (j.get("location") or {}).get("name", "") or "Seoul",
            "url": j.get("absolute_url", ""),
            "posted": iso(j.get("first_published")),
            "etype": "regular" if etype.startswith("정규직") else etype,
        }


def from_line(board):
    d = fetch_json("https://careers.linecorp.com/page-data/ko/jobs/page-data.json")
    for e in d["result"]["data"]["allStrapiJobs"]["edges"]:
        n = e["node"]
        cities = " / ".join(f'{c.get("name", "")} {c.get("country", "")}' for c in n.get("cities") or [])
        jid = n.get("strapiId") or n.get("id")
        yield {
            "jid": str(jid),
            "title": n.get("title", ""),
            "company": ((n.get("companies") or [{}])[0].get("name") or "LINE Plus"),
            "location": cities,
            "url": f"https://careers.linecorp.com/ko/jobs/{jid}",
            "posted": iso(n.get("start_date") or n.get("published_at")),
            "etype": ((n.get("employment_type") or [{}])[0].get("name") or ""),
        }


# ── 공고 모음 사이트 (공개 API, 출처 표기 조건 준수: 각 공고 링크가 원 사이트로 연결됨) ──

def remote_loc(restr):
    """원격 공고의 지원 가능 지역을 위치 문자열로."""
    restr = [r for r in (restr or []) if r]
    return "Remote - " + (", ".join(restr) if restr else "Worldwide")


def from_remoteok(board):
    d = fetch_json("https://remoteok.com/api")
    for j in d:
        if not isinstance(j, dict) or "position" not in j:
            continue  # 첫 항목은 이용 약관 안내
        loc = (j.get("location") or "").strip()
        yield {
            "jid": str(j["id"]),
            "title": j.get("position", ""),
            "company": j.get("company", ""),
            "location": remote_loc([loc] if loc and loc.lower() not in ("remote", "anywhere") else []),
            "url": j.get("url", ""),
            "posted": iso(j.get("date")),
        }


def from_remotive(board):
    d = fetch_json(f"https://remotive.com/api/remote-jobs?category={board}")
    for j in d.get("jobs", []):
        loc = (j.get("candidate_required_location") or "").strip()
        yield {
            "jid": str(j["id"]),
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "location": remote_loc([] if loc.lower() in ("", "worldwide", "anywhere") else [loc]),
            "url": j.get("url", ""),
            "posted": iso(j.get("publication_date")),
            "etype": j.get("job_type", ""),
        }


def from_himalayas(board):
    cursor, pages = None, 0
    while pages < 10:
        d = fetch_json("https://himalayas.app/jobs/api?limit=100" + (f"&cursor={cursor}" if cursor else ""))
        for j in d.get("jobs", []):
            pub = j.get("pubDate")
            yield {
                "jid": str(j.get("guid") or j.get("applicationLink")),
                "title": j.get("title", ""),
                "company": j.get("companyName", ""),
                "location": remote_loc(j.get("locationRestrictions")),
                "url": j.get("applicationLink") or j.get("guid", ""),
                "posted": iso(pub * 1000 if isinstance(pub, (int, float)) and pub < 1e12 else pub),
                "etype": j.get("employmentType", ""),
            }
        cursor, pages = d.get("nextCursor"), pages + 1
        if not cursor or not d.get("jobs"):
            break


FETCHERS = {
    "greenhouse": from_greenhouse,
    "lever": from_lever,
    "ashby": from_ashby,
    "workable": from_workable,
    "smartrecruiters": from_smartrecruiters,
    "remoteok": from_remoteok,
    "remotive": from_remotive,
    "himalayas": from_himalayas,
    "workday": from_workday,
    "amazon": from_amazon,
    "toss": from_toss,
    "line": from_line,
}
AGGREGATORS = {"remoteok": "Remote OK", "remotive": "Remotive", "himalayas": "Himalayas"}


FOREIGN = re.compile(r"[぀-ヿ㐀-䶿一-鿿ｦ-ﾟ]")  # 일본어 가나·한자(중국어 포함)


def classify(title):
    t = title.lower()
    if re.search(EXCLUDE, t):
        return None
    if FOREIGN.search(t):
        # 영어·한국어가 아닌 글자가 섞인 제목은 영어 부분만으로 직무를 판단한다.
        # 일본어로만 된 공고(예: バックエンドエンジニア)는 여기서 빠진다.
        t = FOREIGN.sub(" ", t)
        # 영어 부분에 직무명이 있어야 남긴다 (예: "テクニカル プロジェクト マネージャー・City Infrastructure"는 제외)
        if not re.search(r"engineer|developer|\bsre\b", t):
            return None
    for name, pat in ROLE_RULES:
        if re.search(pat, t):
            return name
    return None


def is_permanent(etype):
    """채용 시스템이 알려준 고용 형태가 계약직·인턴·파트타임이면 제외. 정보가 없으면 제목 필터에 맡긴다."""
    e = str(etype or "").lower().replace("-", "").replace("_", "").replace(" ", "")
    bad = ("contract", "temp", "fixed", "intern", "parttime", "freelance", "seasonal",
           "\u5951\u7d04", "\u6d3e\u9063", "\u30a4\u30f3\u30bf\u30fc\u30f3", "\u30a2\u30eb\u30d0\u30a4\u30c8",  # 契約, 派遣, インターン, アルバイト
           "\uacc4\uc57d", "\uc778\ud134", "\ud30c\uacac")  # 계약, 인턴, 파견
    return not any(b in e for b in bad)


def clean_title(title):
    """영어·일본어 병기 제목에서 일본어 부분을 지워 영어만 남긴다."""
    if not FOREIGN.search(title):
        return title.strip()
    t = re.sub(r"[　-〿぀-ヿ㐀-䶿一-鿿！-ﾟ・（）【】]+", " ", title)
    t = re.sub(r"\s*/\s*(?=[,/)\-]|$)|(?<=^)\s*/\s*|\(\s*\)", "", t)
    t = re.sub(r"\s*/\s*,", ",", t)
    return re.sub(r"\s{2,}", " ", t).strip(" /,-")


def region_of(location):
    loc = location.lower()
    for name, pat in REGION_RULES:
        if re.search(pat, loc):
            return name
    return None


def load(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def main():
    now = dt.datetime.now(KST)
    today = now.date().isoformat()
    cfg = load(ROOT / "sources.json", {"sources": []})
    prev = {j["id"]: j for j in load(DATA / "jobs.json", {"jobs": []}).get("jobs", [])}

    jobs, status = {}, []
    for src in cfg["sources"]:
        name = f'{src["company"]} ({src["ats"]}:{src["board"]})'
        entry = {"company": src["company"], "ats": src["ats"], "board": src["board"], "total": 0, "kept": 0}
        try:
            raw = list(FETCHERS[src["ats"]](src["board"]))
            entry["total"] = len(raw)
            for r in raw:
                if not is_permanent(r.get("etype", "")):
                    continue
                cat = classify(r["title"])
                reg = region_of(r["location"])
                if not cat or not reg:
                    continue
                jid = f'{src["ats"]}:{src["board"]}:{r["jid"]}'
                jobs[jid] = {
                    "id": jid,
                    "company": (r.get("company") or src["company"]).strip(),
                    "title": clean_title(r["title"]),
                    "category": cat,
                    "senior": bool(re.search(SENIOR, r["title"].lower())),
                    "location": r["location"],
                    "region": reg,
                    "url": r["url"],
                    "posted": r["posted"],
                    "firstSeen": prev.get(jid, {}).get("firstSeen", today),
                    "source": AGGREGATORS.get(src["ats"], src["ats"]),
                    "foreign": bool(src.get("foreign")),
                }
                entry["kept"] += 1
            entry["ok"] = True
        except urllib.error.HTTPError as e:
            entry.update(ok=False, error=f"HTTP {e.code}")
        except Exception as e:  # noqa: BLE001 — 출처 하나가 실패해도 나머지는 계속
            entry.update(ok=False, error=f"{type(e).__name__}: {e}"[:200])
        status.append(entry)
        print(f'{"OK " if entry.get("ok") else "ERR"} {name}: {entry["kept"]}/{entry["total"]} {entry.get("error", "")}', flush=True)

    # 직접 추가한 공고(마감 전이고 자동 수집과 겹치지 않는 것만)
    seen_urls = {j["url"].rstrip("/") for j in jobs.values()}
    for c in load(DATA / "curated.json", {"jobs": []}).get("jobs", []):
        dl = c.get("deadline", "상시")
        if re.match(r"\d{4}-\d{2}-\d{2}$", dl) and dl < today:
            continue
        if c.get("url", "").rstrip("/") in seen_urls:
            continue
        cid = "curated:" + c["id"]
        jobs[cid] = {**c, "id": cid, "source": "직접 추가", "firstSeen": prev.get(cid, {}).get("firstSeen", c.get("foundAt", today))}

    out = sorted(jobs.values(), key=lambda j: (j["firstSeen"], j.get("posted") or ""), reverse=True)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "jobs.json").write_text(json.dumps({"updatedAt": now.isoformat(timespec="minutes"), "jobs": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    (DATA / "status.json").write_text(json.dumps({"updatedAt": now.isoformat(timespec="minutes"), "sources": status}, ensure_ascii=False, indent=1), encoding="utf-8")

    hist = load(DATA / "history.json", [])
    hist = [h for h in hist if h["date"] != today]
    counts = {}
    for j in out:
        counts[j["region"]] = counts.get(j["region"], 0) + 1
    hist.append({"date": today, "total": len(out), "new": sum(j["firstSeen"] == today for j in out), "byRegion": counts})
    (DATA / "history.json").write_text(json.dumps(hist[-120:], ensure_ascii=False, indent=1), encoding="utf-8")

    ok = sum(s.get("ok", False) for s in status)
    print(f"\n{len(out)} jobs kept, {ok}/{len(status)} sources OK")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
