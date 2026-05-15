#!/usr/bin/env python3
"""
임의 사주 일일운세 데이터 산출기
생년월일·생시·용신 입력 → 오늘 운세 데이터 계산
"""
import json, sys, argparse
from datetime import date, timedelta, datetime, timezone

KST = timezone(timedelta(hours=9))

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

HOUR_TO_ZHI = [(1,3,"丑"),(3,5,"寅"),(5,7,"卯"),(7,9,"辰"),(9,11,"巳"),(11,13,"午"),(13,15,"未"),(15,17,"申"),(17,19,"酉"),(19,21,"戌"),(21,23,"亥")]
def hour_to_zhi(h: int) -> str:
    if h >= 23 or h < 1: return "子"
    for s, e, b in HOUR_TO_ZHI:
        if s <= h < e: return b
    return "子"

def year_ganzhi(year: int):
    idx = (year - 1984) % 60
    return STEMS[idx % 10], BRANCH[idx % 12]

MONTH_TO_ZHI = {1:"丑",2:"寅",3:"卯",4:"辰",5:"巳",6:"午",7:"未",8:"申",9:"酉",10:"戌",11:"亥",12:"子"}
YEAR_STEM_MONTH_BASE = {"甲":2,"己":2,"乙":4,"庚":4,"丙":6,"辛":6,"丁":8,"壬":8,"戊":0,"癸":0}
def month_ganzhi(year_stem: str, month: int):
    zhi = MONTH_TO_ZHI.get(month, "寅")
    zi = BRANCH.index(zhi)
    yi = 2
    adj = zi if zi >= yi else zi + 12
    si = (YEAR_STEM_MONTH_BASE.get(year_stem, 0) + (adj - yi)) % 10
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
YOOKHAP  = {"子":"丑","丑":"子","寅":"亥","亥":"寅","卯":"戌","戌":"卯","辰":"酉","酉":"辰","巳":"申","申":"巳","午":"未","未":"午"}
YOOKHAE  = {"子":"未","未":"子","丑":"午","午":"丑","寅":"巳","巳":"寅","卯":"辰","辰":"卯","申":"亥","亥":"申","酉":"戌","戌":"酉"}
SAMHYUNG = {"寅":"巳","巳":"申","申":"寅","丑":"戌","戌":"未","未":"丑"}
CK_HAP   = {("丙","辛"):("水","合水"),("辛","丙"):("水","合水"),("甲","己"):("土","合土"),("己","甲"):("土","合土"),("乙","庚"):("金","合金"),("庚","乙"):("金","合金"),("丁","壬"):("木","合木"),("壬","丁"):("木","合木"),("戊","癸"):("火","合火"),("癸","戊"):("火","合火")}
CK_CHUNG = {"甲":"庚","庚":"甲","乙":"辛","辛":"乙","丙":"壬","壬":"丙","丁":"癸","癸":"丁"}

def calc_custom(birth_date: date, birth_hour: int, yongsin: str, huisin: str, gisin: str, name: str = ""):
    today = datetime.now(KST).date()
    ys, yb = year_ganzhi(birth_date.year)
    ms, mb = month_ganzhi(ys, birth_date.month)
    di, ds, db, ds_kr, db_kr = get_ganzhi(birth_date)
    ts, tb = time_ganzhi(ds, birth_hour)
    gongmang = get_gongmang(di)
    wonkuk_b = [yb, mb, db, tb]
    wonkuk_s = [ys, ms, ds, ts]
    bc = {}
    for b in wonkuk_b: bc[b] = bc.get(b, 0) + 1
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
        if YOOKCHUNG.get(tb2) == ow:
            k = f"충{tb2}{ow}"
            if k not in seen: seen.add(k); events.append({"type":"충(沖)","pair":f"{tb2}×{ow}","강도":intensity,"ss":ss})
        if YOOKHAP.get(tb2) == ow:
            k = f"합{tb2}{ow}"
            if k not in seen: seen.add(k); events.append({"type":"합(合)","pair":f"{tb2}×{ow}","강도":intensity,"ss":ss})
        if YOOKHAE.get(tb2) == ow:
            k = f"해{tb2}{ow}"
            if k not in seen: seen.add(k); events.append({"type":"해(害)","pair":f"{tb2}×{ow}","강도":intensity,"ss":ss})
        if SAMHYUNG.get(tb2) == ow:
            k = f"형{tb2}{ow}"
            if k not in seen: seen.add(k); events.append({"type":"형(刑)","pair":f"{tb2}×{ow}","강도":intensity,"ss":ss})
    stem_ev = []
    for ow_s in wonkuk_s:
        key, rkey = (ts2, ow_s), (ow_s, ts2)
        if key in CK_HAP or rkey in CK_HAP:
            hi = CK_HAP.get(key) or CK_HAP.get(rkey)
            stem_ev.append({"type":"합(合)","pair":f"{ts2}×{ow_s}","result":hi[1]})
        if CK_CHUNG.get(ts2) == ow_s:
            stem_ev.append({"type":"충(沖)","pair":f"{ts2}↔{ow_s}"})
    base = 5.0 + (w12_lv - 5) * 0.3
    s_sc = SCORE.get(ts2_oh, 0) * 0.4; b_sc = SCORE.get(tb2_oh, 0) * 0.4; ev_sc = 0.0
    for e in events + stem_ev:
        g = e.get("강도", 1); t = e["type"]
        if t == "충(沖)": ev_sc -= 0.8 * g
        elif t == "형(刑)": ev_sc -= 0.8
        elif t == "해(害)": ev_sc -= 0.5
        elif t == "합(合)": ev_sc += 0.3
    energy = round(max(1.0, min(10.0, base + s_sc + b_sc + ev_sc)), 1)
    return {"name":name,"birth_date":str(birth_date),"birth_hour":birth_hour,"today":str(today),
            "월운":{"년주":f"{ys}{yb}","월주":f"{ms}{mb}","일주":f"{ds}{db}","시주":f"{ts}{tb}","일간":ds,"일지":db,"공망":list(gongmang)},
            "용신":yongsin,"희신":huisin,"기신":gisin,
            "오늘_일진":f"{ts2}{tb2}({ts2_kr}{tb2_kr})","12운성":woon12,"12운성_레벨":w12_lv,
            "에너지_총점":energy,"공망_발동":today_gm,
            "천간_오행":f"{ts2}({ts2_oh}) = {elabel(ts2_oh)}","지지_오행":f"{tb2}({tb2_oh}) = {elabel(tb2_oh)}",
            "충합해형":events,"천간_합충":stem_ev}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--birth-date", required=True); p.add_argument("--birth-hour", type=int, default=12)
    p.add_argument("--yongsin", required=True); p.add_argument("--huisin", default="")
    p.add_argument("--gisin", required=True); p.add_argument("--name", default="")
    args = p.parse_args()
    result = calc_custom(date.fromisoformat(args.birth_date), args.birth_hour, args.yongsin, args.huisin, args.gisin, args.name)
    print(json.dumps(result, ensure_ascii=False, indent=2))
