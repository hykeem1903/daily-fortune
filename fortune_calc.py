#!/usr/bin/env python3
"""
신미(辛未) 일주 일일운세 데이터 산출기
기준 원국: 丁癸辛丙 / 卯卯未申
"""

from datetime import date, timedelta, datetime, timezone
import json, sys, math

KST = timezone(timedelta(hours=9))

def today_kst() -> date:
    return datetime.now(KST).date()

STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEMS_KR = ["갑","을","병","정","무","기","경","신","임","계"]
BRANCH    = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCH_KR = ["자","축","인","묘","진","사","오","미","신","유","술","해"]

REF_DATE  = date(2026, 3, 25)
REF_INDEX = 34

def get_ganzhi(target: date):
    delta = (target - REF_DATE).days
    idx   = (REF_INDEX + delta) % 60
    s, b  = STEMS[idx % 10], BRANCH[idx % 12]
    return idx, s, b, STEMS_KR[idx % 10], BRANCH_KR[idx % 12]

WONKUK_BRANCH = ["卯","卯","未","申"]
WONKUK_STEM   = ["丁","癸","辛","丙"]
ILGAN = "辛"

WONKUK_BRANCH_COUNT: dict = {}
for _br in WONKUK_BRANCH:
    WONKUK_BRANCH_COUNT[_br] = WONKUK_BRANCH_COUNT.get(_br, 0) + 1

SIPSONG = {
    "甲":"정재","乙":"편재","丙":"정관","丁":"편관",
    "戊":"정인","己":"편인","庚":"겁재","辛":"비견",
    "壬":"상관","癸":"식신",
    "子":"식신","丑":"편인","寅":"정재","卯":"편재",
    "辰":"정인","巳":"정관","午":"편관","未":"편인",
    "申":"겁재","酉":"비견","戌":"정인","亥":"상관",
}

WOON12 = {
    "子":"장생","亥":"목욕","戌":"관대","酉":"건록",
    "申":"제왕","未":"쇠","午":"병","巳":"사",
    "辰":"묘","卯":"절","寅":"태","丑":"양",
}
WOON12_LEVEL = {
    "장생":7,"목욕":4,"관대":8,"건록":9,
    "제왕":10,"쇠":4,"병":3,"사":2,
    "묘":3,"절":1,"태":5,"양":6,
}

GONGMANG = {"戌","亥"}

YOOKCHUNG = {
    "子":"午","午":"子","丑":"未","未":"丑",
    "寅":"申","申":"寅","卯":"酉","酉":"卯",
    "辰":"戌","戌":"辰","巳":"亥","亥":"巳",
}
YOOKHAP = {
    "子":"丑","丑":"子","寅":"亥","亥":"寅",
    "卯":"戌","戌":"卯","辰":"酉","酉":"辰",
    "巳":"申","申":"巳","午":"未","未":"午",
}
YOOKHAE = {
    "子":"未","未":"子","丑":"午","午":"丑",
    "寅":"巳","巳":"寅","卯":"辰","辰":"卯",
    "申":"亥","亥":"申","酉":"戌","戌":"酉",
}
SAMHYUNG = {
    "寅":"巳","巳":"申","申":"寅",
    "丑":"戌","戌":"未","未":"丑",
}
SAMHAP_GROUPS = [
    ({"亥","卯","未"}, "목국(木局)", "재성"),
    ({"寅","午","戌"}, "화국(火局)", "관성"),
    ({"巳","酉","丑"}, "금국(金局)", "비겁"),
    ({"申","子","辰"}, "수국(水局)", "식상"),
]

CHUNGKAN_HAP = {
    ("丙","辛"):("水","合水"),("辛","丙"):("水","合水"),
    ("甲","己"):("土","合土"),("己","甲"):("土","合土"),
    ("乙","庚"):("金","合金"),("庚","乙"):("金","合金"),
    ("丁","壬"):("木","合木"),("壬","丁"):("木","合木"),
    ("戊","癸"):("火","合火"),("癸","戊"):("火","合火"),
}
CHUNGKAN_CHUNG = {
    "甲":"庚","庚":"甲","乙":"辛","辛":"乙",
    "丙":"壬","壬":"丙","丁":"癸","癸":"丁",
}

SEUN_2026 = {
    "stem":"丙", "branch":"午",
    "십성_천간":"정관", "십성_지지":"편관",
    "notes": [
        "일간 辛과 丙辛合水 — 일간 자체가 세운과 합, 자기 주도권 약화",
        "일지 未와 午未合火 — 편인(안식처)이 관성으로 변질, 내면 피로 누적",
    ]
}

DAEWOON_CURRENT = {
    "stem": "己", "branch": "亥",
    "십성_천간": "편인", "십성_지지": "식신",
    "period": "2023~2032",
}

# 월운(월주)은 절기 천문계산으로 산출 → get_wolun() 참조 (연도 하드코딩 테이블 제거, 연도무관)

# ── 절기 천문계산 (연도무관, Jean Meeus 태양황경 저차 알고리즘) ──
_J2000 = 2451545.0
def _julian_day(dt: datetime) -> float:
    y, m = dt.year, dt.month
    d = dt.day + dt.hour/24 + dt.minute/1440 + dt.second/86400
    if m <= 2: y -= 1; m += 12
    a = y // 100; b = 2 - a + a // 4
    return math.floor(365.25*(y+4716)) + math.floor(30.6001*(m+1)) + d + b - 1524.5

def _sun_longitude(jd_tt: float) -> float:
    T = (jd_tt - _J2000) / 36525.0
    L0 = (280.46646 + 36000.76983*T + 0.0003032*T*T) % 360
    M = math.radians((357.52911 + 35999.05029*T - 0.0001537*T*T) % 360)
    C = ((1.914602 - 0.004817*T - 0.000014*T*T)*math.sin(M)
         + (0.019993 - 0.000101*T)*math.sin(2*M) + 0.000289*math.sin(3*M))
    omega = math.radians(125.04 - 1934.136*T)
    return (L0 + C - 0.00569 - 0.00478*math.sin(omega)) % 360

def _delta_t(year: int) -> float:
    t = year - 2000
    return 62.92 + 0.32217*t + 0.005589*t*t

def solar_term_date(year: int, target_deg: float, guess_month: int) -> date:
    """태양 겉보기황경이 target_deg(°) 도달하는 KST 날짜. 이분탐색 60회(<1초 수렴)."""
    lo = datetime(year, guess_month, 1) - timedelta(days=20)
    hi = lo + timedelta(days=40)
    dT = _delta_t(year)
    def diff(d):
        return (_sun_longitude(_julian_day(d) + dT/86400.0) - target_deg + 180) % 360 - 180
    for _ in range(60):
        mid = lo + (hi - lo) / 2
        if diff(lo) * diff(mid) <= 0: hi = mid
        else: lo = mid
    return (lo + (hi - lo)/2 + timedelta(hours=9)).date()

# 12절(節) 황경 → 월지 (소한 285°=丑 1월 시작). 오호둔 월간두
_TIGER_HEAD = {"甲":"丙","己":"丙","乙":"戊","庚":"戊","丙":"庚",
               "辛":"庚","丁":"壬","壬":"壬","戊":"甲","癸":"甲"}
_MONTH_BR = ["寅","卯","辰","巳","午","未","申","酉","戌","亥","子","丑"]
_JEOL = [(285,"丑",1),(315,"寅",2),(345,"卯",3),(15,"辰",4),(45,"巳",5),
         (75,"午",6),(105,"未",7),(135,"申",8),(165,"酉",9),(195,"戌",10),
         (225,"亥",11),(255,"子",12)]

def get_wolun(today: date):
    """절기 천문계산으로 월주(월간·월지) 산출 — 연도무관. (오호둔: 연간→월간)"""
    year = today.year
    cands = [(solar_term_date(year, deg, mo), br) for deg, br, mo in _JEOL]
    cands.append((solar_term_date(year-1, 255, 12), "子"))  # 전년 대설(1월초 경계)
    cands.sort()
    cur_br = cands[0][1]
    for d, br in cands:
        if today >= d: cur_br = br
        else: break
    # 연주(입춘 315° 경계)로 월간두 결정
    ipchun = solar_term_date(year, 315, 2)
    eff_year = year if today >= ipchun else year - 1
    year_stem = STEMS[(eff_year - 4) % 10]
    head = _TIGER_HEAD[year_stem]
    month_stem = STEMS[(STEMS.index(head) + _MONTH_BR.index(cur_br)) % 10]
    return month_stem, cur_br

def get_seun(today: date):
    """세운(연주) — 입춘(315°) 경계 천문계산. 입춘 전이면 전년."""
    ipchun = solar_term_date(today.year, 315, 2)
    ey = today.year if today >= ipchun else today.year - 1
    return STEMS[(ey-4)%10], BRANCH[(ey-4)%12]

BRANCH_HOUR_STR = {
    "子": "23~01시", "丑": "01~03시", "寅": "03~05시", "卯": "05~07시",
    "辰": "07~09시", "巳": "09~11시", "午": "11~13시", "未": "13~15시",
    "申": "15~17시", "酉": "17~19시", "戌": "19~21시", "亥": "21~23시",
}

OHAENG_SCORE = {"토": 2, "금": 1, "수": 0, "목": -1, "화": -2}
STEM_OHAENG_MAP = {
    "甲":"목","乙":"목","丙":"화","丁":"화","戊":"토","己":"토",
    "庚":"금","辛":"금","壬":"수","癸":"수",
}
BRANCH_OHAENG_MAP = {
    "子":"수","丑":"토","寅":"목","卯":"목","辰":"토","巳":"화",
    "午":"화","未":"토","申":"금","酉":"금","戌":"토","亥":"수",
}
ENERGY_JUDGE = {
    "토":"용신(최우선·강화)", "금":"희신(보조·도움)",
    "수":"한신(중립·소모)", "목":"구신(소모·역작용)",
    "화":"기신(가장 해로움)",
}

YONGSIN_BRANCHES = ["丑","辰","未","戌","申","酉"]
GISIN_BRANCHES   = ["巳","午","寅","卯"]

# 신살 (일간 辛 / 일지 未 기준)
JAHYUNG_SET = {"辰","午","酉","亥"}
SINSAL_RULES = {
    "천을귀인": {"寅","午"},   # 辛 일간
    "문창귀인": {"子"},
    # 양인 삭제: 삼명통회 "五陰干無刃" — 辛(음간)은 양인 없음. 申은 辛의 제왕+겁재(신약 용신)이지 양인 아님
    "도화":    {"子"},        # 일지 未 (亥卯未) → 도화 = 子
    "역마":    {"巳"},
    "화개":    {"未"},
}
SINSAL_DESC = {
    "천을귀인":"매우 길 — 대인관계·도움·구원자",
    "문창귀인":"학습·문서·시험·기획",
    "도화":   "이성·매력·인기",
    "역마":   "이동·변화·여행",
    "화개":   "고독·예술·종교·집중",
}
# 사맹지(寅申巳亥) — 역마 성질을 띠는 이동성 글자 (광의 보조 표기. 巳는 정통 역마로 이미 커버)
SAMENG_BRANCHES = {"寅","申","亥"}

# 지장간 (정통 표 — 여기·중기·본기 순). 일진 지지의 숨은 글자를 십성으로 노출 (v2.2)
JIJANGGAN = {
    "子":["壬","癸"],       "丑":["癸","辛","己"], "寅":["戊","丙","甲"],
    "卯":["甲","乙"],       "辰":["乙","癸","戊"], "巳":["戊","庚","丙"],
    "午":["丙","己","丁"],  "未":["丁","乙","己"], "申":["戊","壬","庚"],
    "酉":["庚","辛"],       "戌":["辛","丁","戊"], "亥":["戊","甲","壬"],
}

def _stem_label(stem: str) -> str:
    """천간 라벨 — 일간 辛은 십성(비견)이 아니라 '나(일간)'로 표기 (v2.2 버그픽스)"""
    return "나(일간)" if stem == ILGAN else SIPSONG.get(stem, "?")

# 방국·삼합 그룹 (오행 강화 detection)
SAMHAP_OH_GROUPS = [
    ({"亥","卯","未"}, "목국(木局)", "목"),
    ({"寅","午","戌"}, "화국(火局)", "화"),
    ({"巳","酉","丑"}, "금국(金局)", "금"),
    ({"申","子","辰"}, "수국(水局)", "수"),
]
BANG_OH_GROUPS = [
    ({"寅","卯","辰"}, "목방(木方)", "목"),
    ({"巳","午","未"}, "화방(火方)", "화"),
    ({"申","酉","戌"}, "금방(金方)", "금"),
    ({"亥","子","丑"}, "수방(水方)", "수"),
]

GYEOKGUK = "편재격(역동·기획·창업) — 월지 卯 = 편재"

# 월운 십성 → 인생영역 매핑 (거시 방향 도출용)
SIPSONG_DOMAIN = {
    "정관":"직장·명예·승진·책임", "편관":"압박·도전·경쟁·권한",
    "정재":"안정수입·저축·실속",   "편재":"유동재물·투자·사업기회",
    "식신":"표현·창작·먹을복·루틴", "상관":"재능발산·구설·이직충동",
    "정인":"학업·자격·문서·휴식",   "편인":"전문기술·재충전·고독",
    "비견":"독립·동료·협업·자존",   "겁재":"경쟁·지출·동업위험",
}

# 오행 → 신체 부위 (신금 일간 기본 = 폐·호흡기·피부. 그날 기신/구신 오행이 강하면 추가 경고)
OHAENG_BODY = {
    "금":"폐·호흡기·피부·대장", "화":"심장·혈압·눈·염증",
    "목":"간·담·신경·근육",    "수":"신장·방광·비뇨·귀",  "토":"비위·소화·피부",
}

# 신약 신금 십성 기능 점수 (사용자 30년 실경험 후보정: 비겁>인성>식상>0>재성>관성)
# 실제 평균: 비겁+1.75 인성+1.0 식상+0.83 재성-1.0 관성-1.4 와 정합
SIPSONG_FUNC = {
    "비견":1.6, "겁재":1.5,   # 부조(신약 용신급) — 사업·인맥 길
    "정인":1.0, "편인":0.9,   # 생조 — 학습·문서·발전
    "식신":0.7, "상관":0.6,   # 활동·표현 (금전엔 약)
    "정재":-0.8,"편재":-0.8,  # 재다부담 (건강·관계 소모로 발현)
    "정관":-1.0,"편관":-1.4,  # 관살 직극 (칠살 최흉) — 직업 압박
}


def _cross_events(b: str, s: str, target_b: str, target_s: str, layer: str) -> list:
    evts = []
    tb_ss = SIPSONG.get(target_b, "?")
    ts_ss = SIPSONG.get(target_s, "?")
    if YOOKCHUNG.get(b) == target_b:
        evts.append({"type":"충(沖)","pair":f"{b}×{target_b}({layer}지)","ow_ss":tb_ss,"layer":layer})
    if YOOKHAP.get(b) == target_b:
        evts.append({"type":"합(合)","pair":f"{b}×{target_b}({layer}지)","ow_ss":tb_ss,"layer":layer})
    if YOOKHAE.get(b) == target_b:
        evts.append({"type":"해(害)","pair":f"{b}×{target_b}({layer}지)","ow_ss":tb_ss,"layer":layer})
    if SAMHYUNG.get(b) == target_b or SAMHYUNG.get(target_b) == b:
        evts.append({"type":"형(刑)","pair":f"{b}×{target_b}({layer}지)","ow_ss":tb_ss,"layer":layer})
    key, rkey = (s, target_s), (target_s, s)
    if key in CHUNGKAN_HAP or rkey in CHUNGKAN_HAP:
        hi = CHUNGKAN_HAP.get(key) or CHUNGKAN_HAP.get(rkey)
        evts.append({"type":"합(合)","pair":f"{s}×{target_s}({layer}간)",
                     "result":hi[1] if hi else "합","ow_ss":ts_ss,"layer":layer})
    if CHUNGKAN_CHUNG.get(s) == target_s:
        evts.append({"type":"충(沖)","pair":f"{s}↔{target_s}({layer}간)","ow_ss":ts_ss,"layer":layer})
    return evts


def calc(today: date = None):
    if today is None:
        today = today_kst()
    idx, s, b, s_kr, b_kr = get_ganzhi(today)
    ilgan_sipsong = SIPSONG.get(s, "?")
    ilji_sipsong  = SIPSONG.get(b, "?")
    woon12        = WOON12.get(b, "?")
    woon12_level  = WOON12_LEVEL.get(woon12, 5)
    is_gongmang   = b in GONGMANG
    ws, wb = get_wolun(today)
    wol_stem_ss   = SIPSONG.get(ws, "?")
    wol_branch_ss = SIPSONG.get(wb, "?")
    events: list = []
    seen_pairs: set = set()
    for ow in WONKUK_BRANCH:
        ow_ss     = SIPSONG.get(ow, "?")
        intensity = WONKUK_BRANCH_COUNT.get(ow, 1)
        if YOOKCHUNG.get(b) == ow:
            k = f"충{b}{ow}"
            if k not in seen_pairs:
                seen_pairs.add(k)
                events.append({"type":"충(沖)","pair":f"{b}×{ow}","ow_ss":ow_ss,"강도":intensity,"note":"직접 충돌·파괴력"})
        if YOOKHAP.get(b) == ow:
            k = f"합{b}{ow}"
            if k not in seen_pairs:
                seen_pairs.add(k)
                events.append({"type":"합(合)","pair":f"{b}×{ow}","ow_ss":ow_ss,"강도":intensity,"note":"합화"})
        if YOOKHAE.get(b) == ow:
            k = f"해{b}{ow}"
            if k not in seen_pairs:
                seen_pairs.add(k)
                events.append({"type":"해(害)","pair":f"{b}×{ow}","ow_ss":ow_ss,"강도":intensity,"note":"만성 불편·소통 왜곡"})
        if SAMHYUNG.get(b) == ow or SAMHYUNG.get(ow) == b:
            k = f"형{b}{ow}"
            if k not in seen_pairs:
                seen_pairs.add(k)
                events.append({"type":"형(刑)","pair":f"{b}×{ow}","ow_ss":ow_ss,"강도":intensity,"note":"사건성 마찰"})
    all_b = set(WONKUK_BRANCH) | {b}
    samhap_complete = [
        {"name": name, "meaning": meaning}
        for group, name, meaning in SAMHAP_GROUPS
        if group.issubset(all_b)
    ]
    stem_events: list = []
    for ow_s in WONKUK_STEM:
        key, rkey = (s, ow_s), (ow_s, s)
        if key in CHUNGKAN_HAP or rkey in CHUNGKAN_HAP:
            hi = CHUNGKAN_HAP.get(key) or CHUNGKAN_HAP.get(rkey)
            stem_events.append({"type":"합(合)","pair":f"{s}×{ow_s}",
                                "result":hi[1] if hi else "합",
                                "ow_ss":_stem_label(ow_s)})
        if CHUNGKAN_CHUNG.get(s) == ow_s:
            stem_events.append({"type":"충(沖)","pair":f"{s}↔{ow_s}",
                                "ow_ss":_stem_label(ow_s),"note":"천간 직접 충돌"})
    seun_events    = _cross_events(b, s, SEUN_2026["branch"],       SEUN_2026["stem"],       "세운")
    daewoon_events = _cross_events(b, s, DAEWOON_CURRENT["branch"], DAEWOON_CURRENT["stem"], "대운")
    # ── 세운·대운·월운이 원국 8글자를 직접 충합 (유년충·대운충·월충 — 일진보다 큰 흐름) ──
    #  ★코드가 '일진↔세운'만 봐서 놓쳤던 부분. 올해/이달이 내 원국 뿌리를 흔드는가를 본다.
    _se_s, _se_b = get_seun(today)
    won_cross = []
    for _ln, _ls, _lb in [("세운", _se_s, _se_b),
                          ("대운", DAEWOON_CURRENT["stem"], DAEWOON_CURRENT["branch"]),
                          ("월운", ws, wb)]:
        for _wb in WONKUK_BRANCH:
            if YOOKCHUNG.get(_lb) == _wb:
                won_cross.append({"layer":_ln, "type":"충(沖)", "pair":f"{_lb}×{_wb}", "대상":SIPSONG.get(_wb,"?"), "note":f"{_ln}이 원국 {_wb}({SIPSONG.get(_wb)}) 충"})
            elif YOOKHAP.get(_lb) == _wb:
                won_cross.append({"layer":_ln, "type":"합(合)", "pair":f"{_lb}×{_wb}", "대상":SIPSONG.get(_wb,"?"), "note":f"{_ln}이 원국 {_wb} 합"})
        for _wst in WONKUK_STEM:
            if CHUNGKAN_CHUNG.get(_ls) == _wst:
                won_cross.append({"layer":_ln, "type":"충(沖)", "pair":f"{_ls}↔{_wst}", "대상":_stem_label(_wst), "note":f"{_ln} 천간이 원국 {_wst} 충"})
    # 충 대상이 용신/뿌리(인성·비겁·일간)면 흔들림 흉, 그 외 충은 변동, 합은 안정
    woncross_sc = 0.0
    for _e in won_cross:
        if _e["type"].startswith("충"):
            woncross_sc -= 0.18 if _e["대상"] in ("정인","편인","비견","겁재","나(일간)") else 0.10
        else:
            woncross_sc += 0.05
    # 자형 (일진 지지가 自刑 글자이고 원국에 같은 글자 있음)
    if b in JAHYUNG_SET and b in WONKUK_BRANCH:
        events.append({"type":"형(刑)","pair":f"{b}×{b}","ow_ss":SIPSONG.get(b,"?"),"강도":1,"note":"자형(自刑)·내적 갈등"})
    # 신살 발동
    sinsal_active = [
        f"{name}({SINSAL_DESC[name]})"
        for name, branches in SINSAL_RULES.items() if b in branches
    ]
    # 사맹지 이동성 보조 (v2.2 — 정통 역마 巳와 별개의 광의 표기)
    if b in SAMENG_BRANCHES:
        sinsal_active.append("이동성글자·사맹지(보조 — 이동·변화 기운이 보조적으로 작동)")
    # 지장간 십성 레이어 (v2.2 — 일진 지지의 숨은 글자 전체를 십성으로. 辛도 '비견'=통근 표기, 원국 일간 자리가 아님)
    jijanggan_sipsong = [f"{js}({SIPSONG.get(js, '?')})" for js in JIJANGGAN.get(b, [])]
    # 방국·삼합 형성 (원국 + 일진)
    all_b_full = list(WONKUK_BRANCH) + [b]
    bset = set(all_b_full)
    groups_formed = []
    for grp, gname, oh in SAMHAP_OH_GROUPS + BANG_OH_GROUPS:
        inter = grp & bset
        if len(inter) >= 2 and b in inter:
            comp = "완성" if len(inter) == 3 else "부분"
            groups_formed.append({"이름":gname,"오행":oh,"상태":comp,"강화":2 if comp=="완성" else 1})

    # 천간 충 일간 직격 강도 가중
    for e in stem_events:
        if e["type"] == "충(沖)" and e["pair"].startswith(s):
            e["강도"] = 1.5
            e["일간직격"] = True

    gongmang_note = (
        f"{b}(일진 지지)는 공망 — 충합해 효력 반감, 기회가 잡히지 않는 날"
        if is_gongmang else ""
    )
    ohaeng   = BRANCH_OHAENG_MAP.get(b, "?")
    s_ohaeng = STEM_OHAENG_MAP.get(s, "?")
    base = 5.0 + (woon12_level - 5) * 0.3
    s_sc = OHAENG_SCORE.get(s_ohaeng, 0) * 0.4
    b_sc = OHAENG_SCORE.get(ohaeng, 0) * 0.4
    # 원국 8글자 오행 분포(성향)와의 공명 — 일진 천간·지지 오행이 원국에 많을수록 그 기운 증폭.
    #  네 원국: 화2(기신)·목2(구신)·금2·수1·토1. → 기신운(화)은 원국 화부담(2)만큼 더 흉,
    #  희신운(금)은 원국 금받침(2)만큼 더 길, 용신운(토)은 원국에 1개뿐이라 그만큼 작동.
    #  ★일지/원국 8글자가 다르면 이 분포가 달라져 같은 운(일진·월·세)도 해석이 갈린다 = 통근·공명.
    _won_oh = [STEM_OHAENG_MAP.get(x,"?") for x in WONKUK_STEM] + [BRANCH_OHAENG_MAP.get(x,"?") for x in WONKUK_BRANCH]
    tg_sc = (OHAENG_SCORE.get(s_ohaeng,0) * _won_oh.count(s_ohaeng)
             + OHAENG_SCORE.get(ohaeng,0) * _won_oh.count(ohaeng)) * 0.08
    ev_sc = 0.0
    for e in events + stem_events + seun_events + daewoon_events:
        intensity = e.get("강도", 1)
        t = e["type"]
        if t == "충(沖)": ev_sc -= 0.8 * intensity
        elif t == "형(刑)": ev_sc -= 0.8
        elif t == "해(害)": ev_sc -= 0.5
        elif t == "합(合)": ev_sc += 0.3
    # 화국 등 형성 시 기신/용신 가중
    for g in groups_formed:
        boost = g["강화"] * 0.4
        if g["오행"] == "화":  ev_sc -= boost   # 기신 강화
        if g["오행"] in ("토","금"): ev_sc += boost  # 용신/희신 강화
    # 신살 보정 (절댓값 상한 — 충합의 절반 이하: 신살은 색채 보정)
    if any("천을귀인" in s_ for s_ in sinsal_active): ev_sc += 0.25
    if any("문창귀인" in s_ for s_ in sinsal_active): ev_sc += 0.15
    # 양인 申 제거(음간 無양인). 신약 사주: 비겁 일진은 일간 부조 → 가점
    if ilgan_sipsong == "비견": ev_sc += 0.20
    elif ilgan_sipsong == "겁재": ev_sc += 0.15
    energy_score = round(max(1.0, min(10.0, base + s_sc + b_sc + tg_sc + ev_sc + woncross_sc)), 1)
    ilji_hour   = BRANCH_HOUR_STR.get(b, "?")
    best_hours  = [BRANCH_HOUR_STR[br] for br in YONGSIN_BRANCHES]
    worst_hours = [BRANCH_HOUR_STR[br] for br in GISIN_BRANCHES]
    # 거시 방향 — 월운+세운+대운 십성기능 합산 (후보정: 대운 포함 시 설명력 19%→39%, LOOCV 0.12→0.32)
    def _lf(ss, bs):  # 천간 0.6 + 지지 0.4 (歲用天元 천간 우위)
        return 0.6*SIPSONG_FUNC.get(ss,0) + 0.4*SIPSONG_FUNC.get(bs,0)
    se_s, se_b = get_seun(today)
    wol_f = _lf(wol_stem_ss, wol_branch_ss)
    se_f  = _lf(SIPSONG.get(se_s,"?"), SIPSONG.get(se_b,"?"))
    de_f  = _lf(DAEWOON_CURRENT["십성_천간"], DAEWOON_CURRENT["십성_지지"])
    macro_raw = round(0.40*wol_f + 0.35*se_f + 0.25*de_f, 2)   # 층위 가중(월/세/대운)
    macro_tone = "추진월" if macro_raw>=0.5 else "수성월" if macro_raw<=-0.5 else "중립월"
    wolun_domains = [SIPSONG_DOMAIN.get(wol_stem_ss,""), SIPSONG_DOMAIN.get(wol_branch_ss,"")]
    # 신체 주의 (신금=폐·피부 기본 + 그날 기신 화/구신 목이 강하면 해당 장부 추가)
    body_warn = [f"폐·호흡기·피부·대장(신금 기본)"]
    if "화" in (s_ohaeng, ohaeng): body_warn.append(f"{OHAENG_BODY['화']}(기신 화 발동)")
    if "목" in (s_ohaeng, ohaeng): body_warn.append(f"{OHAENG_BODY['목']}(구신 목)")
    # 수비모드 (v2.2 버그픽스 — 지지 충 합산 2건 이상이면 '폭풍 속 전력질주' 차단, GO를 수비형으로 강제)
    chung_cnt = sum(e.get("강도", 1) for e in events if e["type"].startswith("충"))
    subi_mode = chung_cnt >= 2
    subi_reason = (
        f"일진 지지 충 합산 {chung_cnt}건 — 힘이 있어도 사방에서 부딪히는 날. "
        "큰 결정 금지, 기존 업무 마무리·루틴 유지·중요 일정 조정으로 강제"
        if subi_mode else ""
    )
    return {
        "date":            str(today),
        "일진":            f"{s}{b}({s_kr}{b_kr})",
        "일간십성":        ilgan_sipsong,
        "일지십성":        ilji_sipsong,
        "12운성":          woon12,
        "12운성_레벨":     woon12_level,
        "공망여부":        is_gongmang,
        "공망노트":        gongmang_note,
        "천간오행판정":    f"{s}({s_ohaeng}) = {ENERGY_JUDGE.get(s_ohaeng,'?')}",
        "지지오행판정":    f"{b}({ohaeng}) = {ENERGY_JUDGE.get(ohaeng,'?')}",
        "에너지_총점":     energy_score,
        "일진_시간대":     ilji_hour,
        "용신_추천시간":   best_hours,
        "기신_주의시간":   worst_hours,
        "지지_충합해형":   events,
        "천간_합충":       stem_events,
        "세운_교차":       seun_events,
        "대운_교차":       daewoon_events,
        "원국_충합":       won_cross,
        "신체_주의":       body_warn,
        "삼합완성":        samhap_complete,
        "방국삼합형성":    groups_formed,
        "신살_발동":       sinsal_active,
        "숨은글자_지장간": jijanggan_sipsong,
        "수비모드":        subi_mode,
        "수비모드_사유":   subi_reason,
        "격국":            GYEOKGUK,
        "세운_notes":      SEUN_2026["notes"],
        "대운":            DAEWOON_CURRENT,
        "월운": {"interval":f"{ws}{wb}","천간십성":wol_stem_ss,"지지십성":wol_branch_ss,
                 "영역":wolun_domains,"거시톤":macro_tone,"거시점수":macro_raw},
        "원국": {"일간":"辛(-金)","일지":"未(-土)=편인","지지":"卯卯未申","천간":"丁癸辛丙","체질":"신약(身弱)","용신":"토(土)","기신":"화(火)"},
    }


if __name__ == "__main__":
    target = today_kst()
    if len(sys.argv) > 1:
        target = date.fromisoformat(sys.argv[1])
    data = calc(target)
    print(json.dumps(data, ensure_ascii=False, indent=2))
