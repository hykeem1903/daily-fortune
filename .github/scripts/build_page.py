#!/usr/bin/env python3
"""output/today.txt 를 모바일 친화 HTML 로 변환해 _site/index.html 으로 저장."""
import html
import datetime
import os

try:
    import zoneinfo
    KST = zoneinfo.ZoneInfo('Asia/Seoul')
except Exception:
    KST = datetime.timezone(datetime.timedelta(hours=9))


def main() -> None:
    with open('output/today.txt', 'r', encoding='utf-8') as f:
        raw = f.read()
    escaped = html.escape(raw)

    today = datetime.datetime.now(KST)
    date_str = today.strftime('%Y-%m-%d')
    weekday_kr = ['월', '화', '수', '목', '금', '토', '일'][today.weekday()]

    template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>오늘의 운세 — {date_str} ({weekday_kr})</title>
<meta property="og:title" content="신미 일일운세 — {date_str}">
<meta property="og:description" content="오늘의 사주 운세를 확인하세요">
<style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', 'Noto Sans KR', sans-serif;
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 18px 56px;
  line-height: 1.85;
  color: #2c2c2c;
  background: #fbf7f0;
  -webkit-text-size-adjust: 100%;
  word-break: keep-all;
}}
h1 {{
  font-size: 14px;
  font-weight: 500;
  color: #8a7a5a;
  margin: 0 0 12px;
  letter-spacing: 0.02em;
}}
pre {{
  white-space: pre-wrap;
  word-wrap: break-word;
  word-break: keep-all;
  font-family: inherit;
  font-size: 16px;
  margin: 0;
  color: inherit;
  background: transparent;
}}
.footer {{
  margin-top: 48px;
  text-align: center;
  color: #b0a890;
  font-size: 12px;
  border-top: 1px solid #e8dfcb;
  padding-top: 18px;
}}
.footer a {{ color: inherit; text-decoration: none; }}
@media (prefers-color-scheme: dark) {{
  body {{ background: #1c1a17; color: #e8e0d0; }}
  h1 {{ color: #c8b890; }}
  .footer {{ color: #6b6452; border-top-color: #3a352e; }}
}}
</style>
</head>
<body>
<h1>일일운세 · {date_str} ({weekday_kr})</h1>
<pre>{escaped}</pre>
<div class="footer">매일 KST 07:00 자동 업데이트<br><a href="https://github.com/hykeem1903/daily-fortune">github.com/hykeem1903/daily-fortune</a></div>
</body>
</html>
"""

    os.makedirs('_site', exist_ok=True)
    with open('_site/index.html', 'w', encoding='utf-8') as f:
        f.write(template)
    print(f'_site/index.html 생성 완료 ({len(template)} bytes)')


if __name__ == '__main__':
    main()
