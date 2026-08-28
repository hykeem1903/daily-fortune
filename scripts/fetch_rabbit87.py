#!/usr/bin/env python3
"""매일신문 더사주 띠별운세에서 87년생 토끼띠 한 줄을 추출해 output/rabbit87.json 저장.

GitHub Actions(fetch-rabbit87.yml)가 매일 KST 06:20/06:45에 실행.
날짜 매칭은 og:title의 "M월 D일"만 신뢰 (URL 숫자 ID는 업로드 시각이라 불일치).
"""
import json, re, html, os, sys, urllib.request, urllib.parse
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
now = datetime.now(KST)
today_str = f"{now.month}월 {now.day}일"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def out(payload):
    os.makedirs("output", exist_ok=True)
    payload["fetched_at"] = now.isoformat()
    with open("output/rabbit87.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(json.dumps(payload, ensure_ascii=False))


def fetch(url, data=None):
    req = urllib.request.Request(url, data=data, headers=UA)
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


# 오늘자 ok 데이터가 이미 있으면 종료 — 백업 트리거 재실행이 실패로 덮어쓰는 것 방지
try:
    with open("output/rabbit87.json", encoding="utf-8") as f:
        _prev = json.load(f)
    if _prev.get("status") == "ok" and _prev.get("date") == today_str:
        print(json.dumps(_prev, ensure_ascii=False))
        sys.exit(0)
except (FileNotFoundError, json.JSONDecodeError):
    pass

try:
    ids = []
    for st in ("1", "21"):
        data = urllib.parse.urlencode({"qt": "더사주", "nh": "20", "st": st, "adv": "0", "sw": "0", "searchType": "0"}).encode()
        page = fetch("http://search.imaeil.com/RSA/front_new/Search.jsp", data)
        ids += re.findall(r"page/view/(\d+)", page)
    ids = list(dict.fromkeys(ids))
    if not ids:
        out({"status": "fail", "date": today_str, "reason": "검색 결과 0건"})
        sys.exit(0)

    found = None
    for aid in ids:
        body = fetch(f"https://www.imaeil.com/page/view/{aid}")
        m = re.search(r'og:title" content="([^"]*)"', body)
        title = html.unescape(m.group(1)) if m else ""
        norm = re.sub(r"\s+", " ", title)
        if today_str in norm:
            found = (aid, norm, body)
            break
    if not found:
        out({"status": "fail", "date": today_str, "reason": f"오늘자 기사 없음 (후보 {len(ids)}건)"})
        sys.exit(0)

    aid, title, body = found
    wd = re.search(r"([월화수목금토일])요일", title)
    weekday = wd.group(1) if wd else ""
    sec_m = re.search(r"토끼띠(.*?)용띠", body, re.S)
    line_m = re.search(r"▶\s*87년생[^<▶]*", sec_m.group(1)) if sec_m else None
    if not line_m:
        out({"status": "fail", "date": today_str, "reason": "87년생 토끼띠 문장 추출 실패", "article_id": aid})
        sys.exit(0)
    line = html.unescape(line_m.group(0)).strip()
    line = re.sub(r"^▶\s*87년생\s*", "", line).strip()
    out({"status": "ok", "date": today_str, "weekday": weekday, "line": line, "article_id": aid, "title": title})
except Exception as e:
    out({"status": "fail", "date": today_str, "reason": f"예외: {e}"})
    sys.exit(0)
