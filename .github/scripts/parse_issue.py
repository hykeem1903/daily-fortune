#!/usr/bin/env python3
"""GitHub Issue 본문(issue forms 형식)을 파싱해 custom_fortune.py 를 실행.

결과를 requests/pending.json 에 저장.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

VALID_OHAENG = {"토", "금", "수", "목", "화"}


def extract(body: str, label: str) -> str:
    """### <label> 다음 줄(들) 값을 추출. _No response_ 는 빈 문자열로 처리."""
    pattern = rf"###\s*{re.escape(label)}\s*\n+(.+?)(?=\n###|\Z)"
    m = re.search(pattern, body, re.DOTALL)
    if not m:
        return ""
    val = m.group(1).strip()
    if val in ("_No response_", "_없음_", "없음", "No response"):
        return ""
    return val


def main() -> None:
    body = os.environ.get("ISSUE_BODY", "")
    if not body:
        sys.exit("ISSUE_BODY 환경변수 없음")

    name        = extract(body, "이름")
    birth_date  = extract(body, "생년월일")
    birth_hour  = extract(body, "생시")
    yongsin     = extract(body, "용신 (가장 도움되는 오행)")
    huisin      = extract(body, "희신 (보조 오행)")
    gisin       = extract(body, "기신 (가장 해로운 오행)")

    errors = []
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", birth_date):
        errors.append(f"생년월일 형식 오류: '{birth_date}' (YYYY-MM-DD 필요)")
    if not birth_hour.isdigit() or not 0 <= int(birth_hour) <= 23:
        errors.append(f"생시 범위 오류: '{birth_hour}' (0~23)")
    if yongsin not in VALID_OHAENG:
        errors.append(f"용신 오행 오류: '{yongsin}' (토/금/수/목/화)")
    if gisin not in VALID_OHAENG:
        errors.append(f"기신 오행 오류: '{gisin}' (토/금/수/목/화)")
    if huisin and huisin not in VALID_OHAENG:
        errors.append(f"희신 오행 오류: '{huisin}'")

    if errors:
        print("입력 검증 실패:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)

    cmd = [
        "python3", "custom_fortune.py",
        "--birth-date", birth_date,
        "--birth-hour", birth_hour,
        "--yongsin", yongsin,
        "--gisin", gisin,
        "--name", name or "익명",
    ]
    if huisin:
        cmd += ["--huisin", huisin]

    print("실행:", " ".join(cmd), file=sys.stderr)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit("custom_fortune.py 실행 실패")

    out_dir = Path("requests")
    out_dir.mkdir(exist_ok=True)
    (out_dir / "pending.json").write_text(result.stdout, encoding="utf-8")
    print(f"✅ requests/pending.json 생성 ({len(result.stdout)} bytes)", file=sys.stderr)


if __name__ == "__main__":
    main()
