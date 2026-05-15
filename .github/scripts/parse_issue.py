#!/usr/bin/env python3
"""GitHub Issue 본문(issue forms 형식)을 파싱해 custom_fortune.py 를 실행.

결과를 requests/pending.json 에 저장.
용신/희신/기신은 자동 계산. 진태양시·서머타임 보정 적용.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

VALID_CITIES = {"서울","부산","대구","인천","광주","대전","울산","세종","제주","수원","춘천","강릉","청주","전주","포항","기타"}


def extract(body: str, label: str) -> str:
    pattern = rf"###\s*{re.escape(label)}[^\n]*\n+(.+?)(?=\n###|\Z)"
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
    birth_min   = extract(body, "생분")
    city        = extract(body, "출생지")

    errors = []
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", birth_date):
        errors.append(f"생년월일 형식 오류: '{birth_date}' (YYYY-MM-DD 필요)")
    if birth_hour and (not birth_hour.isdigit() or not 0 <= int(birth_hour) <= 23):
        errors.append(f"생시 범위 오류: '{birth_hour}' (0~23)")
    if birth_min and (not birth_min.isdigit() or not 0 <= int(birth_min) <= 59):
        errors.append(f"생분 범위 오류: '{birth_min}' (0~59)")
    if city and city not in VALID_CITIES:
        errors.append(f"출생지 오류: '{city}' — 허용: {sorted(VALID_CITIES)}")

    if errors:
        print("입력 검증 실패:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        sys.exit(1)

    cmd = [
        "python3", "custom_fortune.py",
        "--birth-date", birth_date,
        "--name", name or "익명",
        "--city", city or "서울",
    ]
    if birth_hour:
        cmd += ["--birth-hour", birth_hour]
    if birth_min:
        cmd += ["--birth-minute", birth_min]

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
