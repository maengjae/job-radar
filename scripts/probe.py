import json, urllib.request
UA = {"User-Agent": "job-radar/1.0 (personal job dashboard)", "Accept": "application/json"}
def get(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read().decode())
t = get("https://api-public.toss.im/api/v3/ipd-eggnog/career/jobs")
jobs = t["success"]; print("TOSS n", len(jobs), "keys", list(jobs[0].keys()))
j = jobs[0]; print("TOSS ex", {k: j[k] for k in j if k not in ("data_compliance","content","metadata")})
print("TOSS meta names", sorted({m["name"] for x in jobs for m in x.get("metadata") or []}))
print("TOSS meta sample", [(m["name"], m["value"]) for m in j.get("metadata") or []])
import collections
print("TOSS emp types", collections.Counter(next((m["value"] for m in x.get("metadata") or [] if m["name"]=="Employment_Type"), None) for x in jobs))
l = get("https://careers.linecorp.com/page-data/ko/jobs/page-data.json")
def walk(o, path="", depth=0):
    if depth > 6: return
    if isinstance(o, dict):
        for k, v in o.items():
            if isinstance(v, list) and v and isinstance(v[0], dict): print("LINE list", path + "/" + k, len(v), list(v[0].keys())[:25])
            walk(v, path + "/" + k, depth + 1)
    elif isinstance(o, list) and o: walk(o[0], path + "[0]", depth + 1)
walk(l)
