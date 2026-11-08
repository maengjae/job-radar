"""채용 공고 수집기.

sources.json에 적힌 회사들의 공개 채용 API(Greenhouse, Lever, Ashby, Workable,
SmartRecruiters)에서 공고를 받아 직무·지역으로 거른 뒤 docs/data/에 저장한다.
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
    ("클라우드/인프라", r"cloud|infra|devops|\bsre\b|site reliability|platform engineer|kubernetes|클라우드|인프라|데브옵스"),
    ("백엔드", r"back[- ]?end|server|api|java|kotlin|spring|golang|\bgo\b|백엔드|서버"),
    ("소프트웨어", r"software engineer|software developer|product engineer|소프트웨어|개발자"),
]
EXCLUDE = r"intern(ship)?\b|new grad|graduate|sales|account exec|recruit|marketing|designer|android|\bios\b|front[- ]?end|data scientist|machine learning research|manager,|counsel|legal"
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


def from_greenhouse(board):
    d = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs")
    for j in d.get("jobs", []):
        yield {
            "jid": str(j["id"]),
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
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
        }


def from_smartrecruiters(board):
    offset, total = 0, None
    while total is None or offset < min(total, 1000):
        d = fetch_json(f"https://api.smartrecruiters.com/v1/companies/{board}/postings?limit=100&offset={offset}")
        total = d.get("totalFound", 0)
        for j in d.get("content", []):
            loc = j.get("location") or {}
            yield {
                "jid": j["id"],
                "title": j.get("name", ""),
                "location": ", ".join(x for x in [loc.get("city"), loc.get("country")] if x) + (" (Remote)" if loc.get("remote") else ""),
                "url": f"https://jobs.smartrecruiters.com/{board}/{j['id']}",
                "posted": iso(j.get("releasedDate")),
            }
        offset += 100
        if not d.get("content"):
            break


FETCHERS = {
    "greenhouse": from_greenhouse,
    "lever": from_lever,
    "ashby": from_ashby,
    "workable": from_workable,
    "smartrecruiters": from_smartrecruiters,
}


def classify(title):
    t = title.lower()
    if re.search(EXCLUDE, t):
        return None
    for name, pat in ROLE_RULES:
        if re.search(pat, t):
            return name
    return None


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
                cat = classify(r["title"])
                reg = region_of(r["location"])
                if not cat or not reg:
                    continue
                jid = f'{src["ats"]}:{src["board"]}:{r["jid"]}'
                jobs[jid] = {
                    "id": jid,
                    "company": src["company"],
                    "title": r["title"].strip(),
                    "category": cat,
                    "senior": bool(re.search(SENIOR, r["title"].lower())),
                    "location": r["location"],
                    "region": reg,
                    "url": r["url"],
                    "posted": r["posted"],
                    "firstSeen": prev.get(jid, {}).get("firstSeen", today),
                    "source": src["ats"],
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
