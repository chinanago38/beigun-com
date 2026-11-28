"""トップの「米軍の演習・訓練（NOTAM）」の節（2026-11-28 運営者「米軍 演習情報を NOTAMから 追加する」）。
data/usmil_notam.json（tools/notam_usmil.py が notam.tokyo の取り込み結果から作る）を、まとまりごとのカードにする。
地図は notam.tokyo と同じ「地理院タイル（淡色地図）に赤い丸」。赤い丸は NOTAM の Q項の中心と半径（実際の区域はその中の多角形）。"""
import html, json, math, os, re, datetime
from design import ic

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def mini_map(circles, W=360, H=210):
    """circles: [(lat, lon, radius_nm)] を全部入れた地図（地理院タイル＋赤い丸）"""
    def merc(la, lo, z):
        n = 2 ** z * 256
        return (lo + 180) / 360 * n, (1 - math.log(math.tan(math.pi / 4 + math.radians(la) / 2)) / math.pi) / 2 * n
    la0 = min(c[0] - c[2] / 60 for c in circles); la1 = max(c[0] + c[2] / 60 for c in circles)
    lo0 = min(c[1] - c[2] / 60 / math.cos(math.radians(c[0])) for c in circles)
    lo1 = max(c[1] + c[2] / 60 / math.cos(math.radians(c[0])) for c in circles)
    z = 11
    while z > 3:
        x0, y0 = merc(la1, lo0, z); x1, y1 = merc(la0, lo1, z)
        if x1 - x0 <= W * .92 and y1 - y0 <= H * .92: break
        z -= 1
    xa, ya = merc(la1, lo0, z); xb, yb = merc(la0, lo1, z)
    cx, cy = (xa + xb) / 2, (ya + yb) / 2
    ox, oy = cx - W / 2, cy - H / 2
    n = 2 ** z
    imgs = []
    for tx in range(int(ox // 256), int((ox + W - 1) // 256) + 1):
        for ty in range(int(oy // 256), int((oy + H - 1) // 256) + 1):
            if 0 <= ty < n:
                imgs.append(f'<img src="https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{tx % n}/{ty}.png" alt="" width="256" height="256" loading="lazy" decoding="async" '
                            f'style="left:{(tx * 256 - ox) / W * 100:.2f}%;top:{(ty * 256 - oy) / H * 100:.2f}%;width:{256 / W * 100:.2f}%">')
    svg = []
    for la, lo, nm in circles:
        px, py = merc(la, lo, z)
        mpp = 156543.03392 * math.cos(math.radians(la)) / n
        r = nm * 1852 / mpp
        svg.append(f'<circle cx="{px - ox:.1f}" cy="{py - oy:.1f}" r="{max(r, 3):.1f}" fill="rgba(209,73,91,.16)" stroke="#d1495b" stroke-width="2"/>')
    for la, lo, nm in circles:
        px, py = merc(la, lo, z)
        svg.append(f'<circle cx="{px - ox:.1f}" cy="{py - oy:.1f}" r="3.5" fill="#d1495b" stroke="#fff" stroke-width="1.5"/>')
    la, lo = (la0 + la1) / 2, (lo0 + lo1) / 2
    href = f"https://www.google.com/maps/@{la:.4f},{lo:.4f},{max(z, 5)}z"
    return (f'<a class="um-map" href="{href}" target="_blank" rel="noopener noreferrer" aria-label="範囲の地図を開く（Google マップ）">'
            f'<span class="um-tiles">{"".join(imgs)}</span><svg viewBox="0 0 {W} {H}" aria-hidden="true">{"".join(svg)}</svg><small>地理院タイル</small></a>')


def alt_jp(s):
    s = (s or "").strip().upper()
    if s in ("SFC", "GND"): return "地表"
    m = re.match(r"FL(\d+)", s)
    if m: return f"FL{m.group(1)}（約{round(int(m.group(1)) * 100 * .3048, -2):,.0f}m）"
    m = re.match(r"(\d+)\s*FT\s*(AMSL|AGL)?", s)
    if m:
        ft = int(m.group(1)); base = "地表から" if m.group(2) == "AGL" else "海面から"
        return f"{base}{ft:,}ft（約{round(ft * .3048, -1):,.0f}m）"
    return s


def alt_val(s):
    s = (s or "").strip().upper()
    if s in ("SFC", "GND"): return 0
    m = re.match(r"FL(\d+)", s)
    if m: return int(m.group(1)) * 100
    m = re.match(r"(\d+)", s)
    return int(m.group(1)) if m else 0


def title_of(what, cluster):
    if what.startswith("米軍機の訓練"): return f"{cluster}の空域で米軍機の訓練"
    if "ITRA" in what: return "岩国の臨時留保空域（ITRA）が使われる"
    return what.replace(" の使用", "が使われる")


def usmil_block():
    f = os.path.join(ROOT, "data", "usmil_notam.json")
    d = json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {"items": []}
    items = d.get("items", [])
    got = ""
    if d.get("fetched_at"):
        t = datetime.datetime.fromisoformat(d["fetched_at"].replace("Z", "+00:00")) + datetime.timedelta(hours=9)
        got = f"{t.year}年{t.month}月{t.day}日 {t.hour}時{t.minute:02d}分"
    groups = {}
    for r in items: groups.setdefault((r["what"], r["cluster"], r["kind"]), []).append(r)
    order = sorted(groups.items(), key=lambda kv: (kv[0][2] != "usmil", min(r["start_utc"] for r in kv[1])))
    cards = []
    for (what, cluster, kind), rs in order:
        rs.sort(key=lambda r: (r["start_utc"], r["id"]))
        first = rs[0]; last = max(rs, key=lambda r: r["end_utc"] or "9999")
        circles = sorted({(r["lat"], r["lon"], r["radius_nm"]) for r in rs})
        missions = sorted({r["mission"] for r in rs if r.get("mission")})
        lo = min((r["lower"] for r in rs), key=alt_val); hi = max((r["upper"] for r in rs), key=alt_val)
        places = sorted({r["place"] for r in rs})
        place = places[0] if len(places) == 1 else f"{cluster}の{len(circles)}か所の区域（表を開くと1つずつ見られます）"
        tag = "米軍と明記" if kind == "usmil" else "使う部隊の記載なし"
        rows = "".join(
            f'<tr data-from="{esc(r["start_utc"])}" data-to="{esc(r["end_utc"] or "")}"><td>{esc(r["start_jst"])}〜<br>{esc(r["end_jst"])}{"（見込み）" if r["end_est"] else ""}</td>'
            f'<td>{esc(r["sched_jst"] or ("D項（UTC）" + r["sched_utc"] if r["sched_utc"] else "期間中ずっと"))}</td>'
            f'<td>{esc(alt_jp(r["lower"]))}〜{esc(alt_jp(r["upper"]))}</td><td>{esc(r["place"])}<br><small>{esc(r["pos"])}・半径約{r["radius_km"]}km</small></td>'
            f'<td><a href="{esc(r["url"])}" target="_blank" rel="noopener">{esc(r["id"])}</a>{"<br><small>" + esc(r["mission"]) + "</small>" if r.get("mission") else ""}</td></tr>'
            for r in rs)
        chips = "".join(f'<span class="um-chip">{esc(m)}</span>' for m in missions[:8]) + (f'<span class="um-chip">ほか{len(missions) - 8}</span>' if len(missions) > 8 else "")
        cards.append(
            f'<article class="um-card um-{kind}">{mini_map(circles)}'
            f'<div class="um-body"><p class="um-top"><span class="um-tag">{tag}</span><span class="um-now" hidden>期間中</span></p>'
            f'<h3>{esc(title_of(what, cluster))}</h3>'
            f'<dl class="um-kv"><div><dt>期間</dt><dd>{esc(first["start_jst"])} 〜 {esc(last["end_jst"])}<small>（日本時間）</small></dd></div>'
            f'<div><dt>場所</dt><dd>{esc(place)}</dd></div>'
            f'<div><dt>種類</dt><dd>{esc(what)}</dd></div>'
            f'<div><dt>高さ</dt><dd>{esc(alt_jp(lo))}〜{esc(alt_jp(hi))}</dd></div>'
            + (f'<div><dt>訓練の名前</dt><dd class="um-chips">{chips}</dd></div>' if missions else "") +
            f'</dl><details{" open" if len(rs) <= 2 else ""}><summary>NOTAM ごとの期間と場所（{len(rs)}件）</summary>'
            f'<div class="table-wrap"><table><tr><th>期間（日本時間）</th><th>時間帯</th><th>高さ</th><th>場所</th><th>NOTAM</th></tr>{rows}</table></div></details>'
            f'<p class="um-link"><a class="btn" href="{esc(first["url"])}" target="_blank" rel="noopener">notam.tokyo で原文と要点を見る</a></p></div></article>')
    none = '<p class="um-none"{}>いま出ている演習の NOTAM はありません。新しい NOTAM が出たら、ここに載せます。</p>'.format("" if not cards else " hidden")
    js = ("<script>(function(){var n=Date.now(),s=document.getElementById('usmil'),v=0;s.querySelectorAll('.um-card').forEach(function(c){"
          "var rs=c.querySelectorAll('tr[data-from]'),live=0,on=0;rs.forEach(function(r){var t=r.dataset.to?Date.parse(r.dataset.to):1/0;"
          "if(t<n){r.hidden=true}else{live++;if(Date.parse(r.dataset.from)<=n)on=1}});if(!live){c.hidden=true}else{v++;if(on)c.querySelector('.um-now').hidden=false}});"
          "if(!v)s.querySelector('.um-none').hidden=false})();</script>")
    return (f'<section class="block usmil" id="usmil"><h2>{ic("plane")}米軍の演習・訓練（NOTAM）</h2>'
            f'<p class="lead">国の航空情報 NOTAM（ノータム）のうち、米軍の活動と書かれたものと、米軍の基地や訓練区域の空域のものを、地図と日本時間でまとめています'
            f'（{esc(got)}取得・{len(items)}件）。</p>'
            f'{none}<div class="um-grid">{"".join(cards)}</div>'
            f'<p class="note">NOTAM は操縦する人向けの空域の知らせで、訓練の中身や部隊名までは書かれていないことがあります（「使う部隊の記載なし」は、岩国の臨時留保空域・W で始まる警戒区域・米軍の飛行場の NOTAM で、部隊名が書かれていないもの）。'
            f'地図の赤い丸は NOTAM の Q項の中心と半径で、実際の区域はその中の多角形などです。押すと Google マップが開きます。'
            f'航空機の運航には使えません。米軍の NOTAM の一覧と原文は <a href="https://notam.tokyo/us-military/" target="_blank" rel="noopener">notam.tokyo の米軍の演習・訓練のページ</a>で見られます。</p>{js}</section>\n')
