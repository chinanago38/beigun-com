#!/usr/bin/env python3
"""米軍の演習・訓練の NOTAM を notam.tokyo の取り込み結果から抜き出して data/usmil_notam.json に書く（2026-11-28）。

元のデータ: notam.tokyo（ちんあなご編集部）が国土交通省 SWIM から毎時取り直している NOTAM。
  既定は E:/claudecode/notam-code/data/notams.json（読むだけ・書き換えない）。--src で別のファイルも読める。
拾うもの:
  usmil … E項に「U.S. MIL」と書かれた NOTAM（米軍の活動と明記されたもの）
  base  … 米軍の飛行場（横田・嘉手納・普天間・三沢）が A項の NOTAM、岩国の臨時留保空域（ITRA）、
           W で始まる警戒区域（W-181 など）。使う部隊は NOTAM に書かれていない
  自衛隊と書かれたもの（SOURCE/JSDF・JAPAN SELF DEFENCE FORCE）、花火、障害物（木など）は拾わない。
出力は「変わったか」を見やすいように、取得日時（fetched_at）以外は並び順を固定する。
"""
import argparse, json, math, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = "E:/claudecode/notam-code/data/notams.json"
OUT = os.path.join(ROOT, "data", "usmil_notam.json")
WD = "月火水木金土日"

# 米軍の施設（位置は目安。場所の言い方「〇〇から△の方向 約□km」にだけ使う）
BASES = [
    ("三沢飛行場", "青森県", 40.703, 141.368), ("横田飛行場", "東京都", 35.749, 139.348),
    ("厚木海軍飛行場", "神奈川県", 35.455, 139.450), ("横須賀海軍施設", "神奈川県", 35.290, 139.670),
    ("キャンプ富士", "静岡県", 35.330, 138.860), ("岩国飛行場", "山口県", 34.144, 132.236),
    ("佐世保海軍施設", "長崎県", 33.160, 129.720), ("嘉手納飛行場", "沖縄県", 26.356, 127.768),
    ("普天間飛行場", "沖縄県", 26.274, 127.756),
]
US_AD = {"RJTY": "横田飛行場", "RODN": "嘉手納飛行場", "ROTM": "普天間飛行場", "RJSM": "三沢飛行場"}
PREF = {"HOKKAIDO": "北海道", "AOMORI": "青森県", "IWATE": "岩手県", "MIYAGI": "宮城県", "AKITA": "秋田県", "YAMAGATA": "山形県",
        "FUKUSHIMA": "福島県", "IBARAKI": "茨城県", "TOCHIGI": "栃木県", "GUNMA": "群馬県", "SAITAMA": "埼玉県", "CHIBA": "千葉県",
        "TOKYO": "東京都", "KANAGAWA": "神奈川県", "NIIGATA": "新潟県", "TOYAMA": "富山県", "ISHIKAWA": "石川県", "FUKUI": "福井県",
        "YAMANASHI": "山梨県", "NAGANO": "長野県", "GIFU": "岐阜県", "SHIZUOKA": "静岡県", "AICHI": "愛知県", "MIE": "三重県",
        "SHIGA": "滋賀県", "KYOTO": "京都府", "OSAKA": "大阪府", "HYOGO": "兵庫県", "NARA": "奈良県", "WAKAYAMA": "和歌山県",
        "TOTTORI": "鳥取県", "SHIMANE": "島根県", "OKAYAMA": "岡山県", "HIROSHIMA": "広島県", "YAMAGUCHI": "山口県",
        "TOKUSHIMA": "徳島県", "KAGAWA": "香川県", "EHIME": "愛媛県", "KOCHI": "高知県", "FUKUOKA": "福岡県", "SAGA": "佐賀県",
        "NAGASAKI": "長崎県", "KUMAMOTO": "熊本県", "OITA": "大分県", "MIYAZAKI": "宮崎県", "KAGOSHIMA": "鹿児島県", "OKINAWA": "沖縄県"}


def utc(s):
    """NOTAM の B項・C項（YYMMDDHHMM・UTC）を datetime に。EST・PERM は None"""
    m = re.match(r"(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", s or "")
    if not m: return None
    y, mo, d, h, mi = map(int, m.groups())
    return datetime.datetime(2000 + y, mo, d, h, mi, tzinfo=datetime.timezone.utc)


def jst(dt):
    t = dt + datetime.timedelta(hours=9)
    return t


def jday(dt):
    t = jst(dt)
    return f"{t.year}年{t.month}月{t.day}日（{WD[t.weekday()]}）"


def jhm(dt):
    t = jst(dt)
    return f"{t.hour}:{t.minute:02d}"


def dist_dir(lat1, lon1, lat2, lon2):
    """1→2 の距離（km）と8方位"""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    d = 2 * r * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
    b = (math.degrees(math.atan2(math.sin(dl) * math.cos(p2), math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl))) + 360) % 360
    return d, ["北", "北東", "東", "南東", "南", "南西", "西", "北西"][int((b + 22.5) // 45) % 8]


def place_of(lat, lon, prefs):
    d, base = min((dist_dir(b[2], b[3], lat, lon)[0], b) for b in BASES)
    dd, dr = dist_dir(base[2], base[3], lat, lon)
    pos = f"北緯{lat:.1f}度・東経{lon:.1f}度"
    if prefs: return "・".join(prefs), pos
    if dd < 15: return f"{base[0]}（{base[1]}）", pos
    if dd < 400: return f"{base[0]}（{base[1]}）から{dr}へ約{round(dd, -1):.0f}km", pos
    return f"{base[0]}から{dr}へ約{round(dd, -1):.0f}kmの海上", pos


CLUSTER = {"嘉手納飛行場": "沖縄の周辺", "普天間飛行場": "沖縄の周辺", "三沢飛行場": "三沢（青森県）の周辺", "岩国飛行場": "岩国（山口県）の周辺",
           "横田飛行場": "関東の周辺", "厚木海軍飛行場": "関東の周辺", "横須賀海軍施設": "関東の周辺", "キャンプ富士": "関東の周辺",
           "佐世保海軍施設": "九州の北西の周辺"}


def cluster_of(lat, lon):
    d, base = min((dist_dir(b[2], b[3], lat, lon)[0], b) for b in BASES)
    return CLUSTER.get(base[0], base[0] + "の周辺") if d < 600 else "日本から遠い海上"


def parse(raw):
    q = re.search(r"Q\)\s*(\w+)/(Q\w{4})/[^/]*/[^/]*/[^/]*/(\d{3})/(\d{3})/(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])(\d{3})", raw)
    b = re.search(r"B\)\s*(\d{10})", raw)
    c = re.search(r"C\)\s*(\d{10}|PERM)(EST)?", raw)
    dd = re.search(r"\bD\)\s*(.*?)\s*\bE\)", raw, re.S)
    e = re.search(r"\bE\)\s*(.*?)(?:\n\s*F\)|\)\s*$)", raw, re.S)
    f = re.search(r"\bF\)\s*([^\n]*?)\s+G\)\s*([^\n)]*)", raw)
    num = re.match(r"\(\s*([A-Z]\d{4}/\d{2})\s+(NOTAM[NRC])", raw)
    if not (q and b and num): return None
    lat = int(q.group(5)) + int(q.group(6)) / 60
    lon = int(q.group(8)) + int(q.group(9)) / 60
    if q.group(7) == "S": lat = -lat
    if q.group(10) == "W": lon = -lon
    etext = e.group(1).strip() if e else ""
    return {
        "id": num.group(1), "type": num.group(2), "qcode": q.group(2),
        "lat": round(lat, 4), "lon": round(lon, 4), "radius_nm": int(q.group(11)),
        "lower_fl": int(q.group(3)), "upper_fl": int(q.group(4)),
        "start": utc(b.group(1)), "end": utc(c.group(1)) if c and c.group(1) != "PERM" else None,
        "end_est": bool(c and c.group(2)), "sched": re.sub(r"\s+", " ", dd.group(1)).strip() if dd else "",
        "e": etext, "e_head": re.sub(r"\s+", " ", etext.split("\n")[0]).strip().rstrip(",:"),
        "lower": f.group(1).strip() if f else "", "upper": f.group(2).strip() if f else "",
    }


def kind_of(loc, p, raw):
    e = p["e"].upper()
    if re.search(r"SOURCE\s*/?\s*JSDF|SELF DEFEN[CS]E FORCE", raw.upper()): return None
    if re.search(r"FIREWORK|OBST|TREES|BALLOON|CRANE", e): return None
    if "U.S. MIL" in e or re.search(r"\bU\.?S\.? (MIL|FORCES|NAVY|AIR FORCE|MARINE|ARMY)", e): return "usmil"
    if "IWAKUNI TEMPO RESERVED AIRSPACE" in e: return "base"
    if re.search(r"WARNING AREA W-?\d", e): return "base"
    if loc in US_AD and p["qcode"][1] in "WR": return "base"
    return None


# 種類（日本語）。E項の見出しから決める。決まらないものは Q コードの主題で
def what_of(p):
    e = p["e_head"].upper()
    if "U.S. MIL ACT" in e: return "米軍機の訓練（空域の使用）", "訓練空域"
    if "IWAKUNI TEMPO RESERVED AIRSPACE" in e: return "岩国の臨時留保空域（ITRA）の使用", "臨時留保空域"
    m = re.search(r"WARNING AREA (W-?\d+)(\(([A-Z ]+)\))?", e)
    if m: return f"警戒区域 {m.group(1)}" + (f"（{m.group(3).title()}）" if m.group(3) else "") + " の使用", "警戒区域"
    sub = p["qcode"][1:3]
    return {"WM": "射撃・ミサイルなど", "WP": "パラシュート降下", "WE": "演習", "WU": "無人機の飛行", "WA": "展示飛行",
            "WB": "曲技飛行", "RA": "空域の使用", "RD": "危険区域の使用", "RR": "制限区域の使用", "RT": "臨時制限区域"}.get(sub, "訓練・演習"), "その他"


def hm(s):
    s = int(s[:2]) * 60 + int(s[2:])
    s = (s + 9 * 60) % (24 * 60)
    return f"{s // 60}:{s % 60:02d}"


def sched_jp(s):
    """D項のうち「HHMM/HHMM」だけの並びは日本時間に直す。それ以外は None（原文を出す）"""
    if not s: return None
    pairs = re.findall(r"(\d{4})/(\d{4})", s)
    if pairs and re.fullmatch(r"(\s*\d{4}/\d{4}\s*)+", s):
        return "毎日 " + "・".join(f"{hm(a)}〜{hm(b)}" for a, b in pairs)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--now", default=None, help="テスト用（ISO8601 UTC）")
    a = ap.parse_args()
    src = json.load(open(a.src, encoding="utf-8"))
    now = datetime.datetime.fromisoformat(a.now.replace("Z", "+00:00")) if a.now else datetime.datetime.now(datetime.timezone.utc)
    rows = []
    for it in src.get("items", []):
        raw, loc = it.get("r", ""), it.get("l", "")
        p = parse(raw)
        if not p or p["type"] == "NOTAMC": continue
        k = kind_of(loc, p, raw)
        if not k: continue
        if p["end"] and p["end"] < now: continue          # 終わったものは載せない
        what, group = what_of(p)
        places = [m for m in re.findall(r"\(([^()]*\bIN [A-Z]+[^()]*)\)", raw)]
        prefs = sorted({PREF[w] for pl in places for w in re.findall(r"\bIN ([A-Z]+)", pl) if w in PREF})
        place, pos = place_of(p["lat"], p["lon"], prefs)
        if loc in US_AD and k == "base": place = f"{US_AD[loc]}（A項 {loc}）"
        rows.append({
            "id": p["id"], "kind": k, "what": what, "group": group, "a": loc, "qcode": p["qcode"],
            "start_utc": p["start"].isoformat().replace("+00:00", "Z"),
            "end_utc": p["end"].isoformat().replace("+00:00", "Z") if p["end"] else None, "end_est": p["end_est"],
            "start_jst": jday(p["start"]) + " " + jhm(p["start"]),
            "end_jst": (jday(p["end"]) + " " + jhm(p["end"])) if p["end"] else "終わりの日時は未定（PERM）",
            "sched_utc": p["sched"], "sched_jst": sched_jp(p["sched"]),
            "lat": p["lat"], "lon": p["lon"], "radius_nm": p["radius_nm"], "radius_km": round(p["radius_nm"] * 1.852),
            "lower": p["lower"], "upper": p["upper"], "place": place, "pos": pos,
            "e_head": p["e_head"], "cluster": cluster_of(p["lat"], p["lon"]),
            "mission": (re.search(r"MISSION NAME\s*:?\s*([A-Z0-9][A-Z0-9 \-]*[A-Z0-9])", raw) or [None, None])[1],
            "url": f"https://notam.tokyo/kuko/{loc.lower()}/#n-{p['id'].replace('/', '-')}",
        })
    rows.sort(key=lambda r: (r["start_utc"], r["id"]))
    out = {"fetched_at": src.get("fetched_at"), "source": src.get("source"),
           "via": "notam.tokyo（ちんあなご編集部）の取り込み結果", "count": len(rows), "items": rows}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    old = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    changed = old.get("items") != rows
    if changed or old.get("fetched_at") != out["fetched_at"]:
        json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"usmil {len(rows)} items, changed={changed}")
    sys.exit(0 if changed else 3)   # 3 = 中身は変わっていない（取得日時だけ）


if __name__ == "__main__":
    main()
