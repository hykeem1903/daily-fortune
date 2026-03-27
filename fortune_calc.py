#!/usr/bin/env python3
"""
신미(辛未) 일주 일일운세 데이터 산출기
기준 원국: 丁癸辛丙 / 卯卯未申
"""

from datetime import date, timedelta
import json, sys

# ── 60갑자 ──────────────────────────────────────────────
STEMS  = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEMS_KR = ["갑","을","병","정","무","기","경","신","임","계"]
BRANCH = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCH_KR = ["자","축","인","묘","진","사","오","미","신","유","술","해"]

# 기준: 2026-03-25 = 戊戌 (index 34)
REF_DATE  = date(2026, 3, 25)
REF_INDEX = 34  # 甲子=0 기준

def get_ganzhi(target: date):
    delta = (target - REF_DATE).days
    idx   = (REF_INDEX + delta) % 60
    s, b  = STEMS[idx % 10], BRANCH[idx % 12]
    return idx, s, b, STEMS_KR[idx % 10], BRANCH_KR[idx % 12]

# ── 원국 고정값 (辛未 일주) ──────────────────────────────
WONKUK_BRANCH = ["卯","卯","未","申"]  # 년·월·일·시지
WONKUK_STEM   = ["丁","癸","辛","丙"]  # 년·월·일간(=일간)·시간
ILGAN = "辛"  # 일간

# ── 십성표 (辛 일간 기준) ────────────────────────────────
# 지지는 본기(정기) 오행으로 산출
SIPSONG = {
    # 천간
    "甲":"정재","乙":"편재","丙":"정관","丁":"편관",
    "戊":"정인","己":"편인","庚":"겁재","辛":"비견",
    "壬":"상관","癸":"식신",
    # 지지 (본기 기준)
    "子":"식신","丑":"편인","寅":"정재","卯":"편재",
    "辰":"정인","巳":"정관","午":"편관","未":"편인",
    "申":"겁재","酉":"비견","戌":"정인","亥":"상관",
}

# ── 12운성 (辛 일간, 음간역행) ───────────────────────────
# 子=長生, 亥=沐浴, 戌=冠帶, 酉=建祿, 申=帝旺, 未=衰,
# 午=病, 巳=死, 辰=墓, 卯=絶, 寅=胎, 丑=養
WOON12 = {
    "子":"장생","亥":"목욕","戌":"관대","酉":"건록",
    "申":"제왕","未":"쇠","午":"병","巳":"사",
    "辰":"묘","卯":"절","寅":"태","丑":"양",
}
WOON12_LEVEL = {  # 에너지 수준 (높을수록 좋음)
    "장생":7,"목욕":5,"관대":8,"건록":9,
    "제왕":10,"쇠":4,"병":3,"사":2,
    "묘":4,"절":1,"태":6,"양":7,
}

# ── 공망 (辛未 일주 = 甲子旬 → 戌·亥 공망) ────────────────
GONGMANG = {"戌","亥"}

# ── 충합해형 테이블 ──────────────────────────────────────
YOOKCHUNG = {  # 육충
    "子":"午","午":"子","丑":"未","未":"丑",
    "寅":"申","申":"寅","卯":"酉","酉":"卯",
    "辰":"戌","戌":"辰","巳":"亥","亥":"巳",
}
YOOKHAP = {  # 육합
    "子":"丑","丑":"子","寅":"亥","亥":"寅",
    "卯":"戌","戌":"卯","辰":"酉","酉":"辰",
    "巳":"申","申":"巳","午":"未","未":"午",
}
YOOKHAE = {  # 육해
    "子":"未","未":"子","丑":"午","午":"丑",
    "寅":"巳","巳":"寅","卯":"辰","辰":"卯",
    "申":"亥","亥":"申","酉":"戌","戌":"酉",
}
SAMHYUNG = {  # 삼형 (간략)
    "寅":"巳","巳":"申","申":"寅",
    "丑":"戌","戌":"未","未":"丑",
}
# 삼합: 해묘미=목국, 인오술=화국, 사유축=금국, 신자진=수국
SAMHAP_GROUPS = [
    ({"亥","卯","未"}, "목국(木局)", "재성"),
    ({"寅","午","戌"}, "화국(火局)", "관성"),
    ({"巳","酉","丑"}, "금국(金局)", "비겁"),
    ({"申","子","辰"}, "수국(水局)", "식상"),
]

# ── 천간 합충 ────────────────────────────────────────────
CHUNGKAN_HAP = {  # 천간오합
    ("丙","辛"):("水","合水"),"(辛,丙)":("水","合水"),
    ("甲","己"):("土","合土"),("己","甲"):("土","合土"),
    ("乙","庚"):("金","合金"),("庚","乙"):("金","合金"),
    ("丁","壬"):("木","合木"),("壬","丁"):("木","合木"),
    ("戊","癸"):("火","合火"),("癸","戊"):("Fire","合火"),
}
CHUNGKAN_CHUNG = {  # 천간충
    "甲":"庚","庚":"甲","乙":"辛","辛":"乙",
    "丙":"壬","壬":"丙","丁":"癸","癸":"丁",
}

# ── 2026 세운·월운 고정 데이터 ───────────────────────────
SEUN_2026 = {
    "stem":"丙", "branch":"午",
    "십성_천간":"정관", "십성_지지":"편관",
    "notes": [
        "일간 辛과 丙辛合水 — 일간 자체가 세운과 합, 자기 주도권 약화",
        "일지 未와 午未合火 — 편인(안식처)이 관성으로 변질, 내면 피로 누적",
    ]
}
# 2026 丙午년: 丙/辛년 → 寅월=庚寅 기준 순행
# 각 절기 시작 날짜 → (월건 천간, 월건 지지)
JEOLGI_WOLUN_2026 = [
    # (절기 시작일, 천간, 지지)
    (date(2026,  1,  5), "辛", "丑"),  # 소한
    (date(2026,  2,  4), "庚", "寅"),  # 입춘
    (date(2026,  3,  6), "辛", "卯"),  # 경칩  ← 辛卯 확인
    (date(2026,  4,  5), "壬", "辰"),  # 청명
    (date(2026,  5,  5), "癸", "巳"),  # 입하
    (date(2026,  6,  6), "甲", "午"),  # 망종
    (date(2026,  7,  7), "乙", "未"),  # 소서
    (date(2026,  8,  7), "丙", "申"),  # 입추
    (date(2026,  9,  8), "丁", "酉"),  # 백로
    (date(2026, 10,  8), "戊", "戌"),  # 한로
    (date(2026, 11,  7), "己", "亥"),  # 입동
    (date(2026, 12,  7), "庚", "子"),  # 대설
]

def get_wolun(today: date):
    s, b = "庚", "子"  # 기본값 (연말 기준)
    for jd, js, jb in JEOLGI_WOLUN_2026:
        if today >= jd:
            s, b = js, jb
        else:
            break
    return s, b

# ── 메인 산출 ────────────────────────────────────────────
def calc(today: date = None):
    if today is None:
        today = date.today()

    idx, s, b, s_kr, b_kr = get_ganzhi(today)

    # 기본 정보
    ilgan_sipsong  = SIPSONG.get(s, "?")
    ilji_sipsong   = SIPSONG.get(b, "?")
    woon12         = WOON12.get(b, "?")
    woon12_level   = WOON12_LEVEL.get(woon12, 5)
    is_gongmang    = b in GONGMANG

    # 월운
    ws, wb = get_wolun(today)
    wol_stem_ss  = SIPSONG.get(ws, "?")
    wol_branch_ss= SIPSONG.get(wb, "?")

    # ── 지지 충합해형 (일진 지지 vs 원국 4지지) ──
    events = []
    for ow in WONKUK_BRANCH:
        ow_ss = SIPSONG.get(ow, "?")
        # 육충
        if YOOKCHUNG.get(b) == ow:
            events.append({"type":"충(沖)","pair":f"{b}×{ow}","ow_ss":ow_ss,"note":"직접 충돌, 파괴력"})
        # 육합
        if YOOKHAP.get(b) == ow:
            note = f"합화 결과 검토 필요"
            events.append({"type":"합(合)","pair":f"{b}×{ow}","ow_ss":ow_ss,"note":note})
        # 육해
        if YOOKHAE.get(b) == ow:
            events.append({"type":"해(害)","pair":f"{b}×{ow}","ow_ss":ow_ss,"note":"만성적 불편·소통 왜곡"})
        # 삼형
        if SAMHYUNG.get(b) == ow:
            events.append({"type":"형(刑)","pair":f"{b}×{ow}","ow_ss":ow_ss,"note":"사건성, 강한 마찰"})

    # 삼합 완성 체크
    all_b = set(WONKUK_BRANCH) | {b}
    samhap_complete = []
    for group, name, meaning in SAMHAP_GROUPS:
        if group.issubset(all_b):
            samhap_complete.append({"name":name,"meaning":meaning})

    # ── 천간 합충 (일진 천간 vs 원국 천간) ──
    stem_events = []
    for ow_s in WONKUK_STEM:
        key = (s, ow_s)
        if key in CHUNGKAN_HAP or (ow_s, s) in CHUNGKAN_HAP:
            hap_info = CHUNGKAN_HAP.get(key) or CHUNGKAN_HAP.get((ow_s, s))
            stem_events.append({
                "type":"합(合)",
                "pair":f"{s}×{ow_s}",
                "result":hap_info[1] if hap_info else "합",
                "ow_ss": SIPSONG.get(ow_s,"?"),
            })
        if CHUNGKAN_CHUNG.get(s) == ow_s:
            stem_events.append({
                "type":"충(沖)",
                "pair":f"{s}↔{ow_s}",
                "ow_ss": SIPSONG.get(ow_s,"?"),
                "note":"천간 직접 충돌",
            })

    # 공망 영향
    gongmang_note = ""
    if is_gongmang:
        gongmang_note = f"⚠️ {b}(일진 지지)는 공망 — 충합해의 효력 반감, 기회가 잡히지 않는 느낌"

    # 용신/기신 에너지 판정
    # 오행: 土=용신, 金=희신, 水=한신, 木=구신, 火=기신
    BRANCH_OHAENG = {
        "子":"水","丑":"土","寅":"木","卯":"Wood","辰":"土","巳":"Fire",
        "午":"Fire","未":"土","申":"Metal","酉":"Metal","戌":"土","亥":"Water",
    }
    OHAENG_KR = {"子":"수","丑":"토","寅":"목","卯":"목","辰":"토","巳":"화",
                 "午":"화","未":"토","申":"금","酉":"금","戌":"토","亥":"수"}
    ohaeng = OHAENG_KR.get(b,"?")
    STEM_OHAENG = {"甲":"목","乙":"목","丙":"화","丁":"화","戊":"토","己":"토",
                   "庚":"금","辛":"금","壬":"수","癸":"수"}
    s_ohaeng = STEM_OHAENG.get(s,"?")

    ENERGY_JUDGE = {"토":"용신(최우선 보충)","금":"희신(보충)","수":"한신(중립~소모)",
                    "목":"구신(소모)","화":"기신(가장 해로움)"}
    branch_energy = ENERGY_JUDGE.get(ohaeng,"?")
    stem_energy   = ENERGY_JUDGE.get(s_ohaeng,"?")

    result = {
        "date": str(today),
        "일진": f"{s}{b}({s_kr}{b_kr})",
        "일간십성": ilgan_sipsong,
        "일지십성": ilji_sipsong,
        "12운성": woon12,
        "12운성_레벨": woon12_level,
        "공망여부": is_gongmang,
        "공망노트": gongmang_note,
        "천간오행판정": f"{s}({s_ohaeng}) = {stem_energy}",
        "지지오행판정": f"{b}({ohaeng}) = {branch_energy}",
        "지지_충합해형": events,
        "천간_합충": stem_events,
        "삼합완성": samhap_complete,
        "월운": {
            "간지": f"{ws}{wb}",
            "천간십성": wol_stem_ss,
            "지지십성": wol_branch_ss,
        },
        "세운_notes": SEUN_2026["notes"],
        "원국": {
            "일간": "辛(-金)",
            "일지": "未(-土)=편인",
            "지지": "卯卯未申",
            "천간": "丁癸辛丙",
            "체질": "신약(身弱)",
            "용신": "토(土)",
            "기신": "화(火)",
        }
    }
    return result

if __name__ == "__main__":
    target = date.today()
    if len(sys.argv) > 1:
        target = date.fromisoformat(sys.argv[1])
    data = calc(target)
    print(json.dumps(data, ensure_ascii=False, indent=2))
