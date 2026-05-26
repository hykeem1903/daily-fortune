#!/usr/bin/env python3
"""GitHub Issue 본문(issue forms 형식)을 파싱해 custom_fortune.py 를 실행.

결과를 두 곳에 저장:
- requests/pending.json — routine 정시 발동 시 풀해설 카톡 발송용
- output/YYYY-MM-DD-<slug>.txt — build_page.py 가 자동으로 정식 사이트 페이지로 발행
"""
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VALID_CITIES = {"서울","부산","대구","인천","광주","대전","울산","세종","제주","수원","춘천","강릉","청주","전주","포항","기타"}
WEEKDAY_KR = ['월','화','수','목','금','토','일']

LUCK_COLOR = {'목':'녹색·청록','화':'붉은색·핫핑크','토':'황토·브라운','금':'화이트·실버','수':'검정·진청'}
LUCK_DIR   = {'목':'동(東)','화':'남(南)','토':'중앙·남서','금':'서(西)','수':'북(北)'}
LUCK_NUM   = {'목':'3·8','화':'2·7','토':'5·0','금':'4·9','수':'1·6'}


def extract(body, label):
    pattern = rf"###\s*{re.escape(label)}[^\n]*\n+(.+?)(?=\n###|\Z)"
    m = re.search(pattern, body, re.DOTALL)
    if not m:
        return ""
    val = m.group(1).strip()
    if val in ("_No response_", "_없음_", "없음", "No response"):
        return ""
    return val


def slugify(name):
    """영문/숫자/하이픈만 있으면 그대로, 아니면 issue 번호로 fallback"""
    issue_num = os.environ.get("ISSUE_NUMBER", "0")
    if name and re.match(r"^[A-Za-z0-9_-]+$", name):
        return name.lower()
    return f"issue{issue_num}"


def generate_text(data, name):
    """custom_fortune JSON → 풀운세 평문 (강 코치 톤, 기본 자동 생성본)

    routine 이 정시 발동 때 이 파일을 더 풍부한 풀해설로 덮어쓸 수 있음.
    """
    today = data['today']
    d = datetime.date.fromisoformat(today)
    weekday = WEEKDAY_KR[d.weekday()]
    won = data['원국']
    auto = data['자동산정']
    energy = data['에너지_총점']
    iljin = data['오늘_일진']
    woon12 = data['12운성']
    yongsin = data['용신']
    huisin = data['희신']
    gisin = data['기신']
    gongmang = '·'.join(won['공망']) if won['공망'] else '없음'

    cheon = data.get('천간_합충', [])
    iljik_list = [e for e in cheon if e.get('일간직격') and '충' in e['type']]
    bangguk = data.get('방국삼합', [])

    nucleus = []
    for e in iljik_list:
        nucleus.append(f"{e['pair']} 천간충(일간직격, 강도 {e.get('강도', 1.0)})")
    for g in bangguk:
        nucleus.append(f"{g['name']} 부분삼합 → {g['오행']} 기운 형성")
    nucleus_str = ' / '.join(nucleus) if nucleus else '특이 변수 없음 — 평이한 흐름'

    if energy >= 7.0:
        tone = "공세 — 오늘 치고 나가라. 큰 결정·신규 착수 OK."
    elif energy >= 5.0:
        tone = "중립 — 정상 흐름. 무리하지 말고 평소대로."
    else:
        tone = "수비 — 새 결정 미루고 기존 업무 마무리에만 집중."

    strategy_lines = []
    if iljik_list:
        strategy_lines.append("일간이 천간 직충을 받아 판단력·결단력이 흔들린다. 계약·서명·중요 협상·재무 결정은 전부 다음날 이후로 미뤄라.")
    if energy < 5.0:
        strategy_lines.append("에너지 낮은 날이다. 외부 활동·새 미팅보단 혼자 처리하는 실행 작업에 집중.")
    if any(g['오행'] == yongsin for g in bangguk):
        strategy_lines.append(f"방국·삼합으로 {yongsin}(용신) 기운이 보강된다. 사고·직관·내면 작업 능력 살아있다.")
    if not strategy_lines:
        strategy_lines.append("특별한 변수 없는 평이한 날. 평소 루틴 그대로 진행.")
    strategy = "\n".join(strategy_lines)

    BRANCH_HOUR = [
        ("23~01시", "子"),("01~03시", "丑"),("03~05시", "寅"),
        ("05~07시", "卯"),("07~09시", "辰"),("09~11시", "巳"),
        ("11~13시", "午"),("13~15시", "未"),("15~17시", "申"),
        ("17~19시", "酉"),("19~21시", "戌"),("21~23시", "亥"),
    ]
    BRANCH_OH = {'子':'수','丑':'토','寅':'목','卯':'목','辰':'토','巳':'화','午':'화','未':'토','申':'금','酉':'금','戌':'토','亥':'수'}

    luck_hours = []
    bad_hours = []
    for hour, br in BRANCH_HOUR:
        oh = BRANCH_OH.get(br, '')
        if oh == yongsin:
            luck_hours.append(f"{hour}({br})")
        elif oh == gisin:
            bad_hours.append(f"{hour}({br})")

    luck_h_str = " / ".join(luck_hours[:4]) if luck_hours else "없음"
    bad_h_str = " / ".join(bad_hours[:4]) if bad_hours else "없음"

    text = f"""🔮 {name} 맞춤 운세 — {today} ({weekday}요일)

일주     : {won['일주']} — 일간 {won['일간']} / 일지 {won['일지']}
격국     : {data['격국']}
체질     : {auto['체질']}
용신     : {yongsin} / 희신 {huisin} / 기신 {gisin}
공망     : {gongmang}

일진     : {iljin}
12운성   : {woon12} — 레벨 {data['12운성_레벨']}
에너지   : {energy}/10 — {tone}
핵심변수 : {nucleus_str}

행운시간 : {luck_h_str}
주의시간 : {bad_h_str}


📋 오늘 전략

{strategy}


🎯 영역별 전략

💰 재물: {"일간 직격 충 → 재물 판단력 흔들림. 큰 돈 결정·투자·결제 NO." if iljik_list else "특이 충돌 없음. 평이한 재물 흐름."}

💼 직업: {"수비 모드. 새 프로젝트 착수·신규 제안은 다음날 이후로 미뤄라. 보고·기획 작성처럼 혼자 하는 실행 작업이 답." if energy < 5 else "정상 업무 흐름. 평소대로 진행."}

❤️ 관계: {"기신 강화 구간 협상·논쟁 피해라. 부탁·청탁도 다음 기회에." if energy < 5 else "관계 흐름 평이. 무리한 부탁은 피해라."}

🌿 건강: {"신약 + 기신 강화일 가능. 충분한 수분·휴식, 23시 전 잠자리." if energy < 5 else "건강 흐름 평이. 평소 루틴 유지."}


✅ 오늘 할 것

• 행운시간 ({luck_h_str.split(' /')[0] if luck_h_str != '없음' else '용신 시간'}) 에 집중 작업 배치
• 혼자 처리하는 실행 업무 위주
• 충분한 수분 섭취 (특히 {yongsin} 용신 강화)


🚫 오늘 하지 말 것

• {"계약·서명·투자·큰 돈 결정" if iljik_list else "충동적 큰 결정"}
• 주의시간 협상·논쟁·중요 미팅
• 새 프로젝트 착수·신규 제안 (에너지 충분할 때 발의)


🍀 행운 — 색상 {LUCK_COLOR.get(yongsin, '')} / 방향 {LUCK_DIR.get(yongsin, '')} / 숫자 {LUCK_NUM.get(yongsin, '')}


※ 이 페이지는 사이트 자동 발행본입니다. 다음 routine 정시 발동 시 풀해설 카톡 발송 예정.
"""
    return text


def main():
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

    data = json.loads(result.stdout)
    today_str = data['today']

    Path("requests").mkdir(exist_ok=True)
    Path("requests/pending.json").write_text(result.stdout, encoding="utf-8")

    slug = slugify(name)
    Path("output").mkdir(exist_ok=True)
    output_file = Path(f"output/{today_str}-{slug}.txt")
    output_file.write_text(generate_text(data, name or "익명"), encoding="utf-8")

    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"page_url=https://hykeem1903.github.io/daily-fortune/{today_str}-{slug}.html\n")
            f.write(f"page_path=output/{today_str}-{slug}.txt\n")

    print(f"✅ requests/pending.json + {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
