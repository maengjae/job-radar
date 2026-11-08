"""임시: 피플앤잡 구조 확인."""
import re, urllib.request
UA={"User-Agent":"Mozilla/5.0 (job-radar personal dashboard)"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30) as r:
            return r.status, r.read().decode("utf-8","replace")
    except Exception as e:
        return getattr(e,"code",str(e)[:80]), ""
s,b=get("https://www.peoplenjob.com/robots.txt"); print("ROBOTS",s); print(b[:1500])
for u in ["https://www.peoplenjob.com/jobs","https://www.peoplenjob.com/jobs?page=2","https://www.peoplenjob.com/curations/tech","https://www.peoplenjob.com/jobfairs/it","https://www.peoplenjob.com/jobs/6170564"]:
    s,b=get(u); print("\n=== URL",u,s,len(b))
    links=sorted(set(re.findall(r'href="([^"]+)"',b)))
    print("LINKS(nav)",[l for l in links if not re.search(r'/jobs/\d+$',l)][:80])
    jl=re.findall(r'href="(/(?:jobfairs/\w+/)?jobs/\d+)"[^>]*>(.*?)</a>',b,re.S)
    print("JOBLINKS",len(jl),[ (h,re.sub(r"\s+"," ",re.sub("<[^>]+>"," ",t)).strip()[:90]) for h,t in jl[:6]])
    i=b.find("/jobs/6"); print("SNIPPET",re.sub(r"\s+"," ",b[max(0,i-1500):i+1500])[:3000] if i>0 else b[:1500])
    m=re.findall(r'<script type="application/ld\+json">(.*?)</script>',b,re.S); print("LDJSON",[x[:600] for x in m[:2]])
    f=re.findall(r'<(?:select|input)[^>]+name="([^"]+)"',b); print("FORM",sorted(set(f)))
