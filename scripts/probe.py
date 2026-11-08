import urllib.request, re
UA={"User-Agent":"Mozilla/5.0 job-radar"}
tests=[("coupang","8344977"),("daangn","8043876003"),("furiosaai","4008625201"),("stripe","8318509"),("thunes","8011534003"),("sendbird","8395379002")]
import json
for b,i in tests:
    d=json.loads(urllib.request.urlopen(urllib.request.Request(f"https://boards-api.greenhouse.io/v1/boards/{b}/jobs/{i}",headers=UA),timeout=20).read())
    title=d.get("title","")
    for u in [f"https://job-boards.greenhouse.io/{b}/jobs/{i}", f"https://boards.greenhouse.io/embed/job_app?for={b}&token={i}"]:
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=20); body=r.read().decode("utf-8","replace")
            print("RES",b,r.status,"final=",r.geturl()[:90],"title_in_page=",title[:30] in body, "|", title[:40])
        except Exception as e:
            print("RES",b,"ERR",getattr(e,"code",e),u)
