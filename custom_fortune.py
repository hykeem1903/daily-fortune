#!/usr/bin/env python3
"""
임의 사주 일일운세 데이터 산출기 (고도화 버전)

핵심 보강:
- 24절기 boundary 기반 월주·년주 계산
- 진태양시 보정 (도시별 경도)
- 한국 서머타임 (1948~1988) 처리
- 자형, 巳申 합형 동시, 방국·삼합 화국 형성 가중
- 천간 충 강도 강화 (일간 직격)
- 신살 (천을귀인·역마·도화·화개·문창·양인) 일진 발동
- 격국 자동 산정 + 용신 결정 반영
"""
import json, sys, argparse
from datetime import date, timedelta, datetime, timezone

KST = timezone(timedelta(hours=9))

STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEMS_KR = ["갑","을","병","정","무","기","경","신","임","계"]
BRANCH   = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCH_KR= ["자","축","인","묘","진","사","오","미","신","유","술","해"]

REF_DATE  = date(2026, 3, 25)
REF_INDEX = 34

def get_ganzhi(target: date):
    delta = (target - REF_DATE).days
    idx   = (REF_INDEX + delta) % 60
    return idx, STEMS[idx % 10], BRANCH[idx % 12], STEMS_KR[idx % 10], BRANCH_KR[idx % 12]

# 24절기 boundary (양력 평균 mm-dd) → 월지
SOLAR_TERMS = [
    ((1, 5),  "丑"),
    ((2, 4),  "寅"),
    ((3, 6),  "卯"),
    ((4, 5),  "辰"),
    ((5, 5),  "巳"),
    ((6, 6),  "午"),
    ((7, 7),  "未"),
    ((8, 7),  "申"),
    ((9, 8),  "酉"),
    ((10, 8), "戌"),
    ((11, 7), "亥"),
    ((12, 7), "子"),
]

def month_branch_solar(month: int, day: int) -> str:
    md = (month, day)
    if md < (1, 5):
        return "子"
    current = "子"
    for boundary, zhi in SOLAR_TERMS:
        if md >= boundary:
            current = zhi
        else:
            break
    return current

# 한국 서머타임 (양력 시작/종료 - inclusive)
KST_DST = [
    ((1948, 5, 31),  (1948, 9, 22)),
    ((1949, 4, 3),   (1949, 9, 30)),
    ((1950, 4, 1),   (1950, 9, 10)),
    ((1951, 5, 6),   (1951, 9, 8)),
    ((1955, 5, 5),   (1955, 9, 8)),
    ((1956, 5, 20),  (1956, 9, 29)),
    ((1957, 5, 5),   (1957, 9, 21)),
    ((1958, 5, 4),   (1958, 9, 20)),
    ((1959, 5, 3),   (1959, 9, 19)),
    ((1960, 5, 1),   (1960, 9, 17)),
    ((1987, 5, 10),  (1987, 10, 11)),
    ((1988, 5, 8),   (1988, 10, 9)),
]

def is_dst(birth_date: date) -> bool:
    d = (birth_date.year, birth_date.month, birth_date.day)
    return any(s <= d <= e for s, e in KST_DST)

# 도시별 진태양시 보정 (분 단위, 표준시 기준)
CITY_LON_OFFSET = {
    "서울":-32,"부산":-24,"대구":-25,"인천":-33,"광주":-32,
    "대전":-30,"울산":-23,"세종":-31,"제주":-34,"수원":-32,
    "춘천":-29,"강릉":-22,"청주":-30,"전주":-32,"포항":-23,
    "기타":-32,
}

def apply_solar_time(birth_date: date, hour: int, minute: int, city: str = "서울"):
    """입력 표준시 → 서머타임 보정 → 진태양시 보정. (date, hour, minute) 반환."""
    if is_dst(birth_date):
        hour -= 1
        if hour < 0:
            birth_date -= timedelta(days=1)
            hour += 24
    offset = CITY_LON_OFFSET.get(city, -32)
    total = hour * 60 + minute + offset
    while total < 0:
        birth_date -= timedelta(days=1)
        total += 24 * 60
    while total >= 24 * 60:
        birth_date += timedelta(days=1)
        total -= 24 * 60
    return birth_date, total // 60, total % 60

HOUR_TO_ZHI = [(1,3,"丑"),(3,5,"寅"),(5,7,"卯"),(7,9,"辰"),(9,11,"巳"),(11,13,"午"),(13,15,"未"),(15,17,"申"),(17,19,"酉"),(19,21,"戌"),(21,23,"亥")]
def hour_to_zhi(h: int) -> str:
    if h >= 23 or h < 1: return "子"
    for s, e, b in HOUR_TO_ZHI:
        if s <= h < e: return b
    return "子"

def year_ganzhi(year: int):
    idx = (year - 1984) % 60
    return STEMS[idx % 10], BRANCH[idx % 12]

def year_ganzhi_solar(year: int, month: int, day: int):
    """입춘(2/4) 이전 출생자는 전년 년주."""
    actual = year - 1 if (month, day) < (2, 4) else year
    return year_ganzhi(actual)

YEAR_STEM_MONTH_BASE = {"甲":2,"己":2,"乙":4,"庚":4,"丙":6,"辛":6,"丁":8,"壬":8,"戊":0,"癸":0}
def month_ganzhi_solar(year_stem: str, month: int, day: int):
    zhi = month_branch_solar(month, day)
    zi = BRANCH.index(zhi)
    adj = zi if zi >= 2 else zi + 12
    si = (YEAR_STEM_MONTH_BASE.get(year_stem, 0) + (adj - 2)) % 10
    return STEMS[si], zhi

HOUR_STEM_BASE = {"甲":0,"己":0,"乙":2,"庚":2,"丙":4,"辛":4,"丁":6,"壬":6,"戊":8,"癸":8}
def time_ganzhi(day_stem: str, hour: int):
    zhi = hour_to_zhi(hour)
    si = (HOUR_STEM_BASE.get(day_stem, 0) + BRANCH.index(zhi)) % 10
    return STEMS[si], zhi

GONGMANG_MAP = {0:{"戌","亥"},10:{"申","酉"},20:{"午","未"},30:{"辰","巳"},40:{"寅","卯"},50:{"子","丑"}}
def get_gongmang(day_idx: int) -> set:
    return GONGMANG_MAP.get((day_idx // 10) * 10, set())

WOON12_TABLE = {
    "甲":{"亥":"장생","子":"목욕","丑":"관대","寅":"건록","卯":"제왕","辰":"쇠","巳":"병","午":"사","未":"묘","申":"절","酉":"태","戌":"양"},
    "乙":{"午":"장생","巳":"목욕","辰":"관대","卯":"건록","寅":"제왕","丑":"쇠","子":"병","亥":"사","戌":"묘","酉":"절","申":"태","未":"양"},
    "丙":{"寅":"장생","卯":"목욕","辰":"관대","巳":"건록","午":"제왕","未":"쇠","申":"병","酉":"사","戌":"묘","亥":"절","子":"태","丑":"양"},
    "丁":{"酉":"장생","申":"목욕","未":"관대","午":"건록","巳":"제왕","辰":"쇠","卯":"병","寅":"사","丑":"묘","子":"절","亥":"태","戌":"양"},
    "戊":{"寅":"장생","卯":"목욕","辰":"관대","巳":"건록","午":"제왕","未":"쇠","申":"병","酉":"사","戌":"묘","亥":"절","子":"태","丑":"양"},
    "己":{"酉":"장생","申":"목욕","未":"관대","午":"건록","巳":"제왕","辰":"쇠","卯":"병","寅":"사","丑":"묘","子":"절","亥":"태","戌":"양"},
    "庚":{"巳":"장생","午":"목욕","未":"관대","申":"건록","酉":"제왕","戌":"쇠","亥":"병","子":"사","丑":"묘","寅":"절","卯":"태","辰":"양"},
    "辛":{"子":"장생","亥":"목욕","戌":"관대","酉":"건록","申":"제왕","未":"쇠","午":"병","巳":"사","辰":"묘","卯":"절","寅":"태","丑":"양"},
    "壬":{"申":"장생","酉":"목욕","戌":"관대","亥":"건록","子":"제왕","丑":"쇠","寅":"병","卯":"사","辰":"묘","巳":"절","午":"태","未":"양"},
    "癸":{"卯":"장생","寅":"목욕","丑":"관대","子":"건록","亥":"제왕","戌":"쇠","酉":"병","申":"사","未":"묘","午":"절","巳":"태","辰":"양"},
}
WOON12_LEVEL = {"장생":7,"목욕":5,"관대":8,"건록":9,"제왕":10,"쇠":4,"병":3,"사":2,"묘":4,"절":1,"태":6,"양":7}

OHAENG_ORDER = ["木","火","土","金","水"]
STEM_OH  = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
BRANCH_OH= {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
OH_KR    = {"木":"목","火":"화","土":"토","金":"금","水":"수"}
YIN_S = {"乙","丁","己","辛","癸"}
YIN_B = {"丑","卯","巳","未","酉","亥"}

def get_sipsong(ilgan: str, target: str, is_b: bool = False) -> str:
    io = STEM_OH.get(ilgan,"?"); to = (BRANCH_OH if is_b else STEM_OH).get(target,"?")
    if "?" in (io, to): return "?"
    sy = (ilgan in YIN_S) == (target in (YIN_B if is_b else YIN_S))
    ii = OHAENG_ORDER.index(io); ti = OHAENG_ORDER.index(to)
    if ii == ti: return "비견" if sy else "겁재"
    if OHAENG_ORDER[(ii+1)%5] == to: return "식신" if sy else "상관"
    if OHAENG_ORDER[(ii+2)%5] == to: return "편재" if sy else "정재"
    if OHAENG_ORDER[(ti+2)%5] == io: return "편관" if sy else "정관"
    if OHAENG_ORDER[(ti+1)%5] == io: return "편인" if sy else "정인"
    return "?"

YOOKCHUNG = {"子":"午","午":"子","丑":"未","未":"丑","寅":"申","申":"寅","卯":"酉","酉":"卯","辰":"戌","戌":"辰","巳":"亥","亥":"巳"}
YOOKHAP   = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯","辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
YOOKHAE   = {"子":"未","未":"子","丑":"午","午":"丑","寅":"巳","巳":"寅","卯":"辰","辰":"卯","申":"亥","亥":"申","酉":"戌","戌":"酉"}
SAMHYUNG  = {"寅":"巳","巳":"申","申":"寅","丑":"戌","戌":"未","未":"丑"}
JAHYUNG   = {"辰","午","酉","亥"}  # 자형 (같은 글자 모이면 발동)
CK_HAP    = {("丙","辛"):("水","合水"),("辛","丙"):("水","合水"),("甲","己"):("土","合土"),("己","甲"):("土","合土"),("乙","庚"):("金","合金"),("庚","乙"):("金","合金"),("丁","壬"):("木","合木"),("壬","丁"):("木","合木"),("戊","癸"):("火","合火"),("癸","戊"):("火","合火")}
CK_CHUNG  = {"甲":"庚","庚":"甲","乙":"辛","辛":"乙","丙":"壬","壬":"丙","丁":"癸","癸":"丁"}

# 삼합 / 방국
SAMHAP_GROUPS = [
    ({"亥","卯","未"}, "목국(木局)", "木"),
    ({"寅","午","戌"}, "화국(火局)", "火"),
    ({"巳","酉","丑"}, "금국(金局)", "金"),
    ({"申","子","辰"}, "수국(水局)", "水"),
]
BANG_GROUPS = [
    ({"寅","卯","辰"}, "목방(木方)", "木"),
    ({"巳","午","未"}, "화방(火方)", "火"),
    ({"申","酉","戌"}, "금방(金方)", "金"),
    ({"亥","子","丑"}, "수방(水方)", "水"),
]

# 신살 (일간/일지 기준)
CHEONUL = {  # 천을귀인
    "甲":{"丑","未"}, "戊":{"丑","未"}, "庚":{"丑","未"},
    "乙":{"子","申"}, "己":{"子","申"},
    "丙":{"亥","酉"}, "丁":{"亥","酉"},
    "辛":{"寅","午"},
    "壬":{"卯","巳"}, "癸":{"卯","巳"},
}
MUNCHANG = {  # 문창귀인 (일간 기준)
    "甲":"巳","乙":"午","丙":"申","戊":"申","丁":"酉","己":"酉",
    "庚":"亥","辛":"子","壬":"寅","癸":"卯",
}
YANGIN = {  # 양인 (일간 기준)
    "甲":"卯","丙":"午","戊":"午","庚":"酉","壬":"子",
    "乙":"辰","丁":"未","己":"未","辛":"戌","癸":"丑",
}
SAMHAP_FIRST = {  # 일지 → 삼합 첫 글자
    "申":"申","子":"申","辰":"申",
    "寅":"寅","午":"寅","戌":"寅",
    "巳":"巳","酉":"巳","丑":"巳",
    "亥":"亥","卯":"亥","未":"亥",
}
DOHWA_MAP = {"申":"酉","寅":"卯","巳":"午","亥":"子"}  # 도화: 삼합 첫의 다음
YEOKMA_MAP= {"申":"寅","寅":"申","巳":"亥","亥":"巳"}  # 역마: 삼합 첫의 충
HWAGAE_MAP= {"申":"辰","寅":"戌","巳":"丑","亥":"未"}  # 화개: 삼합 마지막

def check_sinsal(ilgan: str, ilji: str, target_branch: str) -> list:
    """오늘 일진 지지가 본인 일주 기준 신살 발동시키는지 체크."""
    sinsal = []
    if target_branch in CHEONUL.get(ilgan, set()):
        sinsal.append("천을귀인(매우 길)")
    if target_branch == MUNCHANG.get(ilgan):
        sinsal.append("문창귀인(학습·문서)")
    if target_branch == YANGIN.get(ilgan):
        sinsal.append("양인(강한 행동력·갈등)")
    first = SAMHAP_FIRST.get(ilji)
    if first:
        if target_branch == DOHWA_MAP.get(first):
            sinsal.append("도화(이성·매력·연애)")
        if target_branch == YEOKMA_MAP.get(first):
            sinsal.append("역마(이동·변화)")
        if target_branch == HWAGAE_MAP.get(first):
            sinsal.append("화개(고독·예술·종교)")
    return sinsal

def detect_local_groups(branches: list, target: str) -> list:
    """원국 + 일진 지지로 방국·삼합 형성 여부 체크."""
    all_b = set(branches) | {target}
    formed = []
    for group, name, oh in SAMHAP_GROUPS:
        inter = group & all_b
        if len(inter) == 3:
            formed.append({"type":"삼합완성","name":name,"오행":OH_KR[oh],"강화":2})
        elif len(inter) == 2 and target in inter:
            formed.append({"type":"부분삼합","name":name,"오행":OH_KR[oh],"강화":1})
    for group, name, oh in BANG_GROUPS:
        inter = group & all_b
        if len(inter) == 3:
            formed.append({"type":"방국완성","name":name,"오행":OH_KR[oh],"강화":2})
        elif len(inter) == 2 and target in inter:
            formed.append({"type":"부분방국","name":name,"오행":OH_KR[oh],"강화":1})
    return formed

# 격국 (월지 십성 = 격, 단순화)
def determine_gyeokguk(ilgan: str, month_branch: str) -> str:
    ss = get_sipsong(ilgan, month_branch, True)
    GYEOK_NAME = {
        "비견":"비견격(독립·자존)","겁재":"겁재격(경쟁·동업)",
        "식신":"식신격(꾸준한 결과·여유)","상관":"상관격(창의·표현·반항)",
        "정재":"정재격(안정 재물·실리)","편재":"편재격(역동·기획·창업)",
        "정관":"정관격(질서·관리·명예)","편관":"편관격(추진·돌파·특수직)",
        "정인":"정인격(학문·문서·안정)","편인":"편인격(직관·연구·예술)",
    }
    return GYEOK_NAME.get(ss, "혼합격")

SAENG_NEXT = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
GUK_NEXT   = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
SAENG_PREV = {v:k for k,v in SAENG_NEXT.items()}
GUK_PREV   = {v:k for k,v in GUK_NEXT.items()}

def auto_yongsin(ilgan: str, stems: list, branches: list) -> dict:
    """오행 분포(월지·일지 ×2) 기반 신강/신약 → 용신·희신·기신 산정."""
    ilgan_oh = STEM_OH.get(ilgan, "土")
    counts = {"木":0, "火":0, "土":0, "金":0, "水":0}
    for s in stems:
        if s in STEM_OH: counts[STEM_OH[s]] += 1
    for i, b in enumerate(branches):
        if b not in BRANCH_OH: continue
        weight = 2 if i in (1, 2) else 1
        counts[BRANCH_OH[b]] += weight

    bigyeop  = ilgan_oh
    insung   = SAENG_PREV[ilgan_oh]
    siksang  = SAENG_NEXT[ilgan_oh]
    jaesung  = GUK_NEXT[ilgan_oh]
    gwansung = GUK_PREV[ilgan_oh]

    friendly = counts[bigyeop] + counts[insung]
    hostile  = counts[siksang] + counts[jaesung] + counts[gwansung]

    if friendly > hostile:
        ys, hs = (siksang, jaesung) if counts[siksang] <= counts[jaesung] else (jaesung, siksang)
        gs = insung
        body = "신강(身强)"
    else:
        ys, hs = (insung, bigyeop) if counts[insung] <= counts[bigyeop] else (bigyeop, insung)
        gs = gwansung
        body = "신약(身弱)"

    return {
        "용신": OH_KR[ys], "희신": OH_KR[hs], "기신": OH_KR[gs],
        "오행분포": {OH_KR[k]: v for k, v in counts.items()},
        "친화_점수": friendly, "적대_점수": hostile, "체질": body,
    }


def calc_custom(birth_date: date, birth_hour, birth_minute: int = 0, city: str = "서울", name: str = ""):
    today = datetime.now(KST).date()
    has_hour = birth_hour is not None
    actual_date = birth_date

    if has_hour:
        actual_date, h, m = apply_solar_time(birth_date, birth_hour, birth_minute, city)
        ts, tb = time_ganzhi(STEMS[(REF_INDEX + (actual_date - REF_DATE).days) % 10], h)

    ys, yb = year_ganzhi_solar(actual_date.year, actual_date.month, actual_date.day)
    ms, mb = month_ganzhi_solar(ys, actual_date.month, actual_date.day)
    di, ds, db, ds_kr, db_kr = get_ganzhi(actual_date)

    if has_hour:
        ts, tb = time_ganzhi(ds, h)
        wonkuk_b = [yb, mb, db, tb]
        wonkuk_s = [ys, ms, ds, ts]
    else:
        ts, tb = "", ""
        wonkuk_b = [yb, mb, db]
        wonkuk_s = [ys, ms, ds]

    gongmang = get_gongmang(di)
    bc = {}
    for b in wonkuk_b: bc[b] = bc.get(b, 0) + 1

    auto    = auto_yongsin(ds, wonkuk_s, wonkuk_b)
    yongsin = auto["용신"]; huisin = auto["희신"]; gisin = auto["기신"]
    gyeok   = determine_gyeokguk(ds, mb)

    ti2, ts2, tb2, ts2_kr, tb2_kr = get_ganzhi(today)
    woon12  = WOON12_TABLE.get(ds, {}).get(tb2, "?")
    w12_lv  = WOON12_LEVEL.get(woon12, 5)
    today_gm = tb2 in gongmang
    ts2_oh = OH_KR.get(STEM_OH.get(ts2,""),"?")
    tb2_oh = OH_KR.get(BRANCH_OH.get(tb2,""),"?")

    SCORE = {yongsin:2, huisin:1, gisin:-2}
    def elabel(oh): return {yongsin:"용신(필요·강화)",huisin:"희신(보조·도움)",gisin:"기신(가장 해로움)"}.get(oh, "한신(중립)")

    events, seen = [], set()
    for ow in wonkuk_b:
        intensity = bc.get(ow, 1)
        ss = get_sipsong(ds, ow, True)
        for ev_type, table, note in [
            ("충(沖)", YOOKCHUNG, "직접 충돌"),
            ("합(合)", YOOKHAP,   "합화"),
            ("해(害)", YOOKHAE,   "만성 불편"),
            ("형(刑)", SAMHYUNG,  "사건성 마찰"),
        ]:
            if table.get(tb2) == ow:
                k = f"{ev_type[0]}{tb2}{ow}"
                if k not in seen:
                    seen.add(k)
                    events.append({"type":ev_type,"pair":f"{tb2}×{ow}","강도":intensity,"ss":ss,"note":note})
    # 자형
    if tb2 in JAHYUNG and tb2 in wonkuk_b:
        events.append({"type":"형(刑)","pair":f"{tb2}×{tb2}","강도":1,"ss":get_sipsong(ds, tb2, True),"note":"자형(자기 복제·내적 갈등)"})

    # 천간 합/충 (일간 직격은 강도 1.5 가중)
    stem_ev = []
    for i, ow_s in enumerate(wonkuk_s):
        is_ilgan_pos = (i == 2)
        key, rkey = (ts2, ow_s), (ow_s, ts2)
        if key in CK_HAP or rkey in CK_HAP:
            hi = CK_HAP.get(key) or CK_HAP.get(rkey)
            stem_ev.append({"type":"합(合)","pair":f"{ts2}×{ow_s}","result":hi[1],"일간직격":is_ilgan_pos})
        if CK_CHUNG.get(ts2) == ow_s:
            stem_ev.append({"type":"충(沖)","pair":f"{ts2}↔{ow_s}","일간직격":is_ilgan_pos,"강도":1.5 if is_ilgan_pos else 1.0})

    # 방국·삼합 형성
    groups = detect_local_groups(wonkuk_b, tb2)

    # 신살
    sinsal = check_sinsal(ds, db, tb2) if has_hour or True else []

    # 에너지 점수
    base = 5.0 + (w12_lv - 5) * 0.3
    s_sc = SCORE.get(ts2_oh, 0) * 0.4
    b_sc = SCORE.get(tb2_oh, 0) * 0.4
    ev_sc = 0.0
    for e in events:
        g = e.get("강도", 1); t = e["type"]
        if t == "충(沖)": ev_sc -= 0.8 * g
        elif t == "형(刑)": ev_sc -= 0.7
        elif t == "해(害)": ev_sc -= 0.5
        elif t == "합(合)": ev_sc += 0.3
    for e in stem_ev:
        g = e.get("강도", 1.0); t = e["type"]
        if t == "충(沖)": ev_sc -= 0.6 * g
        elif t == "합(合)": ev_sc += 0.2

    # 화국 등 형성 시 기신/용신 강화로 점수 보정
    for g in groups:
        boost = g["강화"] * 0.4
        if g["오행"] == gisin:   ev_sc -= boost
        if g["오행"] == yongsin: ev_sc += boost

    # 신살 보정
    if any("천을귀인" in s for s in sinsal): ev_sc += 0.6
    if any("문창귀인" in s for s in sinsal): ev_sc += 0.3
    if any("양인" in s for s in sinsal):    ev_sc -= 0.3

    energy = round(max(1.0, min(10.0, base + s_sc + b_sc + ev_sc)), 1)

    return {
        "name":name,
        "birth_date":str(birth_date),
        "birth_hour":birth_hour if has_hour else None,
        "birth_minute":birth_minute if has_hour else None,
        "city":city if has_hour else None,
        "생시_입력여부": has_hour,
        "보정정보": {
            "서머타임_적용": is_dst(birth_date) if has_hour else False,
            "진태양시_적용일": str(actual_date) if has_hour else None,
            "도시_경도보정_분": CITY_LON_OFFSET.get(city, -32) if has_hour else None,
        },
        "today":str(today),
        "원국":{
            "년주":f"{ys}{yb}","월주":f"{ms}{mb}","일주":f"{ds}{db}",
            "시주":f"{ts}{tb}" if has_hour else "(미입력)",
            "일간":ds,"일지":db,"공망":list(gongmang),
        },
        "격국": gyeok,
        "자동산정": auto,
        "용신":yongsin,"희신":huisin,"기신":gisin,
        "오늘_일진":f"{ts2}{tb2}({ts2_kr}{tb2_kr})",
        "12운성":woon12,"12운성_레벨":w12_lv,
        "에너지_총점":energy,"공망_발동":today_gm,
        "천간_오행":f"{ts2}({ts2_oh}) = {elabel(ts2_oh)}",
        "지지_오행":f"{tb2}({tb2_oh}) = {elabel(tb2_oh)}",
        "충합해형":events,
        "천간_합충":stem_ev,
        "방국삼합":groups,
        "신살":sinsal,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--birth-date", required=True)
    p.add_argument("--birth-hour", default="")
    p.add_argument("--birth-minute", default="0")
    p.add_argument("--city", default="서울")
    p.add_argument("--name", default="")
    args = p.parse_args()
    bh = int(args.birth_hour) if args.birth_hour.strip() else None
    bm = int(args.birth_minute) if args.birth_minute.strip() else 0
    result = calc_custom(date.fromisoformat(args.birth_date), bh, bm, args.city, args.name)
    print(json.dumps(result, ensure_ascii=False, indent=2))
