# Job Radar

매일 자동으로 갱신되는 백엔드·클라우드 채용 공고 대시보드입니다. 한국과 일본, 싱가포르 등 아시아 지역 공고, 그리고 원격 공고를 모읍니다.

## 동작 방식

1. GitHub Actions가 매일 07:30(KST)에 `scripts/collect.py`를 실행합니다.
2. `sources.json`에 적힌 회사들의 공개 채용 API(Greenhouse, Lever, Ashby, Workable, SmartRecruiters)에서 공고를 받습니다.
3. 직무(백엔드·클라우드/인프라·IT운영/플랫폼·AI/데이터·소프트웨어 개발)와 지역(한국·일본·싱가포르·아시아·원격)으로 거릅니다.
4. 결과를 `docs/data/`에 저장하고 커밋합니다. GitHub Pages가 `docs/`를 웹페이지로 보여줍니다.

## 바꾸는 법

- **회사 추가·삭제**: `sources.json`을 수정합니다. 수정해서 push하면 바로 다시 수집합니다. 국내·해외 모두 대기업·계열사·상장사, 또는 매출 규모가 큰 비상장사(당근·토스·Stripe·OpenAI 등)만 넣습니다. 중소기업·스타트업과 원격 공고 모음 사이트는 넣지 않습니다.
- **바로가기 링크**: 자동 수집이 안 되는 회사의 채용 페이지는 `docs/data/sites.json`에서 추가·삭제합니다.
- **직접 공고 추가**: 자동 수집이 닿지 않는 공고(국내 대기업 공채 등)는 `docs/data/curated.json`에 추가합니다. `deadline`이 지나면 자동으로 빠집니다.
- **수동 실행**: Actions 탭 → "채용 공고 갱신" → Run workflow를 누릅니다.
- **직무·지역 키워드**: `scripts/collect.py` 위쪽의 `ROLE_RULES`, `REGION_RULES`를 수정합니다.

## 로컬 실행

```bash
python scripts/collect.py
python -m http.server -d docs 8000
```

## 이력서 받기 (비밀번호)

대시보드의 "내 이력서 받기"는 `docs/private/resume.json`(암호화된 이력서·경력기술서)을 비밀번호로 풀어서 내려받습니다. 복호화는 브라우저 안에서만 이뤄지고, 원본 PDF는 저장소에 올리지 않습니다(`.gitignore`에 `*.pdf`).

이력서나 비밀번호를 바꾸려면:

```bash
pip install cryptography
python scripts/encrypt_resume.py "새 비밀번호" 맹재영_이력서.pdf 맹재영_경력기술서.pdf
git add docs/private/resume.json && git commit -m "이력서 갱신" && git push
```
