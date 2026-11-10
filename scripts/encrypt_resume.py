"""이력서 PDF를 비밀번호로 암호화해 docs/private/resume.json 으로 저장한다.

사용법:
    python scripts/encrypt_resume.py "비밀번호" 이력서.pdf 경력기술서.pdf

- 원본 PDF는 저장소에 올리지 마세요. 암호화된 resume.json만 커밋합니다.
- 암호화: PBKDF2-SHA256(600,000회)로 비밀번호에서 키를 만들고 AES-256-GCM으로 암호화합니다.
  대시보드는 브라우저의 Web Crypto로 같은 방식으로 복호화합니다.
"""
import base64
import json
import os
import sys
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600_000
OUT = Path(__file__).resolve().parent.parent / "docs" / "private" / "resume.json"


def b64(b):
    return base64.b64encode(b).decode()


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    password, files = sys.argv[1], sys.argv[2:]
    salt = os.urandom(16)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS).derive(password.encode())
    aes = AESGCM(key)
    items = []
    for f in files:
        p = Path(f)
        iv = os.urandom(12)
        items.append({"name": p.name, "iv": b64(iv), "data": b64(aes.encrypt(iv, p.read_bytes(), None))})
    # 비밀번호 확인용: 고정 문자열을 암호화해 둔다
    check_iv = os.urandom(12)
    doc = {"v": 1, "kdf": "PBKDF2-SHA256", "iterations": ITERATIONS, "salt": b64(salt),
           "check": {"iv": b64(check_iv), "data": b64(aes.encrypt(check_iv, b"job-radar", None))},
           "files": items}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc), encoding="utf-8")
    print(f"saved {OUT} ({OUT.stat().st_size:,} bytes, {len(items)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
