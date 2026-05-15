#!/usr/bin/env python3
"""output/today.txt 를 모바일 친화 HTML 로 변환해 _site/ 에 저장.

- _site/index.html  : 오늘 운세 + 지난 30일 링크 목록
- _site/YYYY-MM-DD.html : 일자별 아카이브 페이지

지난 일자 HTML 은 existing_site/ (gh-pages 체크아웃)에서 코찌온다.
30일 이전 파일은 코찌오지 않아 자연 삭제 (force_orphan 배포 때문).
"""
import html
import datetime
import re
import shutil
from pathlib import Path

try:
    import zoneinfo
    KST = zoneinfo.ZoneInfo('Asia/Seoul')
except Exception:
    KST = datetime.timezone(datetime.timedelta(hours=9))

KEEP_DAYS = 30
SITE_DIR = Path('_site')
EXISTING_DIR = Path('existing_site')
TODAY_TXT = Path('output/today.txt')
DATE_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})\.html$')
WEEKDAY_KR = ['월', '화', '수', '목', '금', '토', '일']


def render_page(content_raw, date_str, weekday_kr, archive_dates, is_dated_page):
    escaped = html.escape(content_raw)

    nav_top = ''
    if is_dated_page:
        nav_top = '<a class="back" href="./">← 오늘 운세 보기</a>'

    archive_section = ''
    if archive_dates:
        items = '\n'.join(
            '  <li><a href="{d}.html">{d} ({w})</a></li>'.format(
                d=d,
                w=WEEKDAY_KR[datetime.date.fromisoformat(d).weekday()],
            )
            for d in archive_dates
        )
        archive_section = (
            '\n<div class="archive">\n'
            '<h2>지난 운세 (최근 30일)</h2>\n'
            '<ul>\n' + items + '\n</ul>\n'
            '</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>일일운세 — {date_str} ({weekday_kr})</title>
<meta property="og:title" content="신미 일일운세 — {date_str}">
<meta property="og:description" content="오늘의 사주 운세">
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
.back {{
  display: inline-block;
  margin: 0 0 16px;
  padding: 6px 12px;
  font-size: 13px;
  color: #8a7a5a;
  background: #f0e8d4;
  border-radius: 6px;
  text-decoration: none;
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
.archive {{
  margin-top: 36px;
  padding-top: 18px;
  border-top: 1px solid #e8dfcb;
}}
.archive h2 {{
  font-size: 14px;
  font-weight: 500;
  color: #8a7a5a;
  margin: 0 0 10px;
  letter-spacing: 0.02em;
}}
.archive ul {{ list-style: none; padding: 0; margin: 0; }}
.archive li {{ margin: 4px 0; }}
.archive a {{
  display: inline-block;
  padding: 4px 8px;
  color: #6b5e44;
  text-decoration: none;
  font-size: 14px;
  border-radius: 4px;
}}
.archive a:hover {{ background: #f0e8d4; }}
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
  .back {{ background: #2a2520; color: #c8b890; }}
  .archive {{ border-top-color: #3a352e; }}
  .archive h2 {{ color: #c8b890; }}
  .archive a {{ color: #b8a880; }}
  .archive a:hover {{ background: #2a2520; }}
  .footer {{ color: #6b6452; border-top-color: #3a352e; }}
}}
</style>
</head>
<body>
{nav_top}
<h1>일일운세 · {date_str} ({weekday_kr})</h1>
<pre>{escaped}</pre>{archive_section}
<div class="footer">매일 KST 07:00 자동 업데이트 · 최근 30일 보관<br><a href="https://github.com/hykeem1903/daily-fortune">github.com/hykeem1903/daily-fortune</a></div>
</body>
</html>
"""


def main() -> None:
    today = datetime.datetime.now(KST)
    today_str = today.strftime('%Y-%m-%d')
    weekday_kr = WEEKDAY_KR[today.weekday()]
    cutoff = today.date() - datetime.timedelta(days=KEEP_DAYS - 1)

    SITE_DIR.mkdir(exist_ok=True)

    kept_dates = []
    if EXISTING_DIR.exists():
        for f in EXISTING_DIR.iterdir():
            m = DATE_RE.match(f.name)
            if not m:
                continue
            d_str = m.group(1)
            if d_str == today_str:
                continue
            try:
                d = datetime.date.fromisoformat(d_str)
            except ValueError:
                continue
            if d >= cutoff:
                shutil.copy(f, SITE_DIR / f.name)
                kept_dates.append(d_str)

    today_raw = TODAY_TXT.read_text(encoding='utf-8')

    today_page = render_page(
        today_raw, today_str, weekday_kr,
        archive_dates=None,
        is_dated_page=False,
    )
    (SITE_DIR / f'{today_str}.html').write_text(today_page, encoding='utf-8')

    archive_sorted = sorted(kept_dates, reverse=True)
    index_page = render_page(
        today_raw, today_str, weekday_kr,
        archive_dates=archive_sorted,
        is_dated_page=False,
    )
    (SITE_DIR / 'index.html').write_text(index_page, encoding='utf-8')

    print(f'_site/index.html, _site/{today_str}.html 생성 완료')
    print(f'아카이브 명수: {len(archive_sorted)}일')


if __name__ == '__main__':
    main()
