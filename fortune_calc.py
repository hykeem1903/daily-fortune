#!/usr/bin/env python3
"""
신미(辛未) 일주 일일운세 데이터 산출기
기준 원국: 丁癸辛丙 / 卯卯未申
"""

from datetime import date, timedelta, datetime, timezone
import json, sys

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
    "장생":7,"목욕":5,"관대":8,"건록":9,
    "제왕":10,"쇠":4,"병":3,"사":2,
    "묘":4,"절":1,"태":6,"양":7,
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

JEOLGI_WOLUN_2026 = [
    (date(2026,  1,  5), "辛", "丑"),
    (date(2026,  2,  4), "庚", "寅"),
    (date(2026,  3,  6), "辛", "卯"),
    (date(2026,  4,  5), "壬", "辰"),
    (date(2026,  5,  5), "癸", "巳"),
    (date(2026,  6,  6), "甲", "午"),
    (date(2026,  7,  7), "乙", "未"),
    (date(2026,  8,  7), "丙", "申"),
    (date(2026,  9,  8), "丁", "酉"),
    (date(2026, 10,  8), "戊", "戌"),
    (date(2026, 11,  7), "己", "亥"),
    (date(2026, 12,  7), "庚", "子"),
]

def get_wolun(today: date):
    s, b = "庚", "子"
    for jd, js, jb in JEOLGI_WOLUN_2026:
        if today >= jd:
            s, b = js, jb
        else:
            break
    return s, b

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
    "양인":    {"戌"},
    "도화":    {"子"},        # 일지 未 (亥卯未) → 도화 = 子
    "역마":    {"巳"},
    "화개":    {"未"},
}
SINSAL_DESC = {
    "천을귀인":"매우 길 — 대인관계·도움·구원자",
    "문창귀인":"학습·문서·시험·기획",
    "양인":   "강한 행동력·갈등·결단",
    "도화":   "이성·매력·인기",
    "역마":   "이동·변화·여행",
    "화개":   "고독·예술·종교·집중",
}

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
    if SAMHYUNG.get(b) == target_b:
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
        if SAMHYUNG.get(b) == ow:
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
                                "ow_ss":SIPSONG.get(ow_s,"?")})
        if CHUNGKAN_CHUNG.get(s) == ow_s:
            stem_events.append({"type":"충(沖)","pair":f"{s}↔{ow_s}",
                                "ow_ss":SIPSONG.get(ow_s,"?"),"note":"천간 직접 충돌"})
    seun_events    = _cross_events(b, s, SEUN_2026["branch"],       SEUN_2026["stem"],       "세운")
    daewoon_events = _cross_events(b, s, DAEWOON_CURRENT["branch"], DAEWOON_CURRENT["stem"], "대운")
    # 자형 (일진 지지가 自刑 글자이고 원국에 같은 글자 있음)
    if b in JAHYUNG_SET and b in WONKUK_BRANCH:
        events.append({"type":"형(刑)","pair":f"{b}×{b}","ow_ss":SIPSONG.get(b,"?"),"강도":1,"note":"자형(自刑)·내적 갈등"})
    # 신살 발동
    sinsal_active = [
        f"{name}({SINSAL_DESC[name]})"
        for name, branches in SINSAL_RULES.items() if b in branches
    ]
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
    # 신살 보정
    if any("천을귀인" in s_ for s_ in sinsal_active): ev_sc += 0.6
    if any("문창귀인" in s_ for s_ in sinsal_active): ev_sc += 0.3
    if any("양인"    in s_ for s_ in sinsal_active): ev_sc -= 0.3
    energy_score = round(max(1.0, min(10.0, base + s_sc + b_sc + ev_sc)), 1)
    ilji_hour   = BRANCH_HOUR_STR.get(b, "?")
    best_hours  = [BRANCH_HOUR_STR[br] for br in YONGSIN_BRANCHES]
    worst_hours = [BRANCH_HOUR_STR[br] for br in GISIN_BRANCHES]
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
        "삼합완성":        samhap_complete,
        "방국삼합형성":    groups_formed,
        "신살_발동":       sinsal_active,
        "격국":            GYEOKGUK,
        "세운_notes":      SEUN_2026["notes"],
        "대운":            DAEWOON_CURRENT,
        "월운": {"interval":f"{ws}{wb}","천간십성":wol_stem_ss,"지지십성":wol_branch_ss},
        "원국": {"일간":"辛(-金)","일지":"未(-土)=편인","지지":"卯卯未申","천간":"丁癸辛丙","체질":"신약(身弱)","용신":"토(土)","기신":"화(火)"},
    }


if __name__ == "__main__":
    target = today_kst()
    if len(sys.argv) > 1:
        target = date.fromisoformat(sys.argv[1])
    data = calc(target)
    print(json.dumps(data, ensure_ascii=False, indent=2))
