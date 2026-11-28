"""面の組み替え（2026-11-29 運営者「文字ばっかりだから 画像 ブロック 表 を 入れて かっこよくデザイン」）。
本文の字は変えず、順番も変えずに、見出しのアイコン・カード・事実の箱・注意の箱・時系列・写真に組み替える。
build.py の render() が blockify() の後に decorate() を呼ぶ。"""
import html, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

P = {  # 24x24 の線のアイコン（stroke=currentColor）
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4M7 14h3M14 14h3M7 18h3"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    "plane": '<path d="M10.5 21l1.5-1.2 1.5 1.2v-3l-1-1V13l8 2.5V13l-8-5V4a1 1 0 0 0-2 0v4l-8 5v2.5L10.5 13v4l-1 1z"/>',
    "id": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="9" cy="11" r="2.2"/><path d="M5.8 16.2c.6-1.6 1.8-2.4 3.2-2.4s2.6.8 3.2 2.4M14.5 10h4M14.5 13.5h3"/>',
    "ban": '<circle cx="12" cy="12" r="9"/><path d="M5.6 5.6l12.8 12.8"/>',
    "bus": '<rect x="4" y="3.5" width="16" height="14" rx="3"/><path d="M4 11h16M7.5 20.5v-3M16.5 20.5v-3"/><circle cx="8" cy="14.3" r=".6"/><circle cx="16" cy="14.3" r=".6"/>',
    "phone": '<path d="M5 4h3.5l1.7 4.3-2.2 1.4a11 11 0 0 0 6.3 6.3l1.4-2.2L20 15.5V19a1.5 1.5 0 0 1-1.6 1.5A16.5 16.5 0 0 1 3.5 5.6 1.5 1.5 0 0 1 5 4z"/>',
    "alert": '<path d="M12 3.5l9.5 16.5h-19z"/><path d="M12 10v4.5M12 17.2v.3"/>',
    "news": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 8h10M7 12h6M7 16h10M15.5 11.5h1.5v1.5h-1.5z"/>',
    "question": '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.3a2.6 2.6 0 1 1 3.6 2.4c-.7.3-1.1.9-1.1 1.6v.7M12 16.8v.4"/>',
    "shield": '<path d="M12 3l7.5 3v5.5c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5V6z"/><path d="M8.8 12l2.2 2.2 4.3-4.4"/>',
    "pin": '<path d="M12 21s-6.5-6.2-6.5-11.3a6.5 6.5 0 0 1 13 0C18.5 14.8 12 21 12 21z"/><circle cx="12" cy="9.7" r="2.4"/>',
    "book": '<path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15H6.5A2.5 2.5 0 0 0 4 20.5z"/><path d="M4 20.5A2.5 2.5 0 0 0 6.5 23H20v-5"/>',
    "search": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
    "list": '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1"/><circle cx="4.5" cy="12" r="1"/><circle cx="4.5" cy="18" r="1"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 6l8.5 7 8.5-7"/>',
    "camera": '<path d="M4 7.5h3.2L9 5h6l1.8 2.5H20a1 1 0 0 1 1 1V19a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V8.5a1 1 0 0 1 1-1z"/><circle cx="12" cy="13.5" r="3.6"/>',
    "chart": '<path d="M4 20V4M4 20h16"/><path d="M8 16v-4M12 16V8M16 16v-6"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V7.5a4 4 0 0 1 8 0v3"/>',
    "link": '<path d="M10 14a4.5 4.5 0 0 0 6.4 0l3-3a4.5 4.5 0 0 0-6.4-6.4l-1.2 1.2"/><path d="M14 10a4.5 4.5 0 0 0-6.4 0l-3 3a4.5 4.5 0 0 0 6.4 6.4l1.2-1.2"/>',
    "cloud": '<path d="M7 18.5a4.5 4.5 0 0 1-.6-9 6 6 0 0 1 11.4 1.6A3.8 3.8 0 0 1 17.5 18.5z"/>',
    "walk": '<circle cx="13" cy="4.5" r="1.8"/><path d="M10 21l2-6 2.5 2.5V21M9 11l2.5-3.5 3 1.5 1.5 3.5M11.5 7.5L10 13"/>',
    "exit": '<path d="M14 4h5v16h-5"/><path d="M10 8l-4 4 4 4M6 12h9"/>',
    "parking": '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="M10 17V8h3a2.5 2.5 0 0 1 0 5h-3"/>',
    "bike": '<circle cx="6" cy="16" r="3.5"/><circle cx="18" cy="16" r="3.5"/><path d="M6 16l4-7h5l3 7M10 9l2.5 7M13.5 6.5h2.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
    "gate": '<path d="M4 21V8l8-5 8 5v13"/><path d="M9 21v-7h6v7"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8 12.3l2.7 2.7L16.3 9.5"/>',
    "star": '<path d="M12 3.5l2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.9z"/>',
    "dot": '<circle cx="12" cy="12" r="4"/>',
}

# 見出しの語 → アイコン（先に当たったもの）
HEAD = [
    (r"出典|参考", "book"), (r"ニュース|何が報じ|報道の流れ", "news"), (r"身分証", "id"), (r"禁止", "ban"),
    (r"注意|お答えできない", "alert"), (r"交通|ゲート", "bus"), (r"問い合わせ|連絡先", "phone"),
    (r"飛行展示|地上展示|デモチーム|出演者", "plane"), (r"止まった|影響", "alert"), (r"不明|分かって", "question"),
    (r"Cloud One", "cloud"), (r"日程|これまで|移り変わり|2027|変更", "calendar"), (r"歴史|回数", "book"),
    (r"基地|かかわり|在日", "pin"), (r"方針|中立|説明|情報源|確かめ方|編集|食い違う|訂正", "shield"),
    (r"調べ方|続報", "search"), (r"写真|著作権", "camera"), (r"広告|Cookie|解析", "chart"),
    (r"個人情報|プライバシー|第三者|管理", "lock"), (r"外部|リンク", "link"), (r"基本情報|概要|目的|について|とは|三沢|横田", "info"),
    (r"ページ|一覧|予定|お受け|内容", "list"),
]
# カードの見出しの語 → アイコン
KEY = [
    (r"徒歩", "walk"), (r"シャトル|バス", "bus"), (r"退出", "exit"), (r"ゲート", "gate"), (r"検査", "shield"),
    (r"駐車場", "parking"), (r"バイク", "bike"), (r"身分証", "id"), (r"入場の可否", "check"), (r"持ち込み|禁止", "ban"),
    (r"交通", "bus"), (r"暑さ", "sun"), (r"時間", "clock"), (r"Cloud|Command|System", "cloud"),
]
WARN = r"注意|禁止|お答えできない|止まった作業"


def ic(name, cls="ic"):
    return f'<span class="{cls}" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{P.get(name, P["dot"])}</svg></span>'


def pick(text, table, default="dot"):
    for pat, name in table:
        if re.search(pat, text): return name
    return default


def strip(s): return re.sub(r"<[^>]+>", "", s).strip()


def kcards(ul):
    """<li><strong>見出し</strong>：本文</li> だけの箇条書き → アイコン付きのカード"""
    items = re.findall(r"<li>\s*<(strong|b)>(.*?)</\1>\s*[：:]?\s*(.*?)</li>", ul, re.S)
    lis = re.findall(r"<li>", ul)
    if len(items) < 2 or len(items) != len(lis): return None
    cards = "".join(f'<div class="kcard">{ic(pick(strip(h), KEY))}<div><b>{h}</b><p>{t.strip()}</p></div></div>' for _, h, t in items)
    return f'<div class="kcards">{cards}</div>'


def lists(sec, h2):
    def rep(m):
        ul = m.group(0)
        k = kcards(ul)
        if k: return k
        lis = re.findall(r"<li>(.*?)</li>", ul, re.S)
        if re.search(r"禁止", h2): return ul.replace("<ul>", '<ul class="ng">', 1)
        if "<a " not in ul and len(lis) >= 3 and all(len(strip(x)) <= 48 for x in lis):
            return ul.replace("<ul>", '<ul class="tiles">', 1)
        if "<a " not in ul and len(lis) >= 3:
            return ul.replace("<ul>", '<ul class="dots">', 1)
        return ul
    return re.sub(r"<ul>.*?</ul>", rep, sec, flags=re.S)


def facts(tbl):
    """見出しの列と値の列だけの短い表 → 事実の箱"""
    rows = re.findall(r"<tr>\s*<th>(.*?)</th>\s*<td>(.*?)</td>\s*</tr>", tbl, re.S)
    if len(rows) < 2 or len(rows) != len(re.findall(r"<tr>", tbl)): return None
    return '<div class="facts">' + "".join(f'<div class="fact"><span>{th}</span><b>{td}</b></div>' for th, td in rows) + "</div>"


def timeline(tbl):
    """「日付」で始まる表 → 時系列"""
    hd = re.findall(r"<th>(.*?)</th>", re.search(r"<tr>.*?</tr>", tbl, re.S).group(0))
    if not hd or hd[0] != "日付": return None
    rows = [re.findall(r"<td>(.*?)</td>", r, re.S) for r in re.findall(r"<tr>(.*?)</tr>", tbl, re.S)[1:]]
    li = "".join(f'<li><span class="d">{r[0]}</span><b>{r[1]}</b>' + (f'<small>{hd[2]}：{r[2]}</small>' if len(r) > 2 else "") + "</li>" for r in rows)
    return f'<ol class="tline">{li}</ol>'


def tables(sec, h2):
    def rep(m):
        w = m.group(0); tbl = m.group(1)
        if re.search(r"基本情報|概要", h2):
            f = facts(tbl)
            if f: return f
        t = timeline(tbl)
        if t: return t
        first = re.search(r"<tr>(.*?)</tr>", tbl, re.S)
        if first and len(re.findall(r"<t[hd]", first.group(1))) >= 3:
            return w.replace('<div class="table-wrap">', '<div class="table-wrap wide">', 1)
        return w
    sec = re.sub(r'<div class="table-wrap">(<table\b.*?</table>)</div>', rep, sec, flags=re.S)
    sec = re.sub(r"<td>(現時点で不明|公式の発表は見当たらない)</td>", r'<td><span class="unk">\1</span></td>', sec)
    return sec


def subs(sec):
    """h3 ごとに小さな箱にする（h3 にもアイコン）"""
    if "<h3>" not in sec: return sec
    head, *parts = re.split(r"(?=<h3>)", sec)
    out = [head]
    for p in parts:
        end = ""
        if p.rstrip().endswith("</section>"):
            p = p.rstrip()[:-10]; end = "</section>"
        h = re.match(r"<h3>(.*?)</h3>", p, re.S)
        name = pick(strip(h.group(1)), HEAD, "star")
        p = p.replace("<h3>", f'<h3>{ic(name, "ic sm")}', 1)
        out.append(f'<div class="sub">{p.strip()}</div>{end}')
    return "".join(out)


def inline_photos(url):
    f = os.path.join(ROOT, "tools", "photos", "inline.tsv")
    out = {}
    if not os.path.exists(f): return out
    for l in open(f, encoding="utf-8").read().splitlines()[1:]:
        c = l.split("\t")
        if len(c) >= 8 and c[0] == url: out[c[1]] = c
    return out


def photo_fig(c):
    _, _, src, page, author, lic, lic_url, alt = c[:8]
    e = lambda s: html.escape(s, quote=True)
    lh = f'<a href="{e(lic_url)}" rel="noopener license" target="_blank">{e(lic)}</a>' if lic_url.startswith("http") else e(lic)
    return (f'<figure class="photo inpage"><img src="{e(src)}" alt="{e(alt)}" loading="lazy" decoding="async">'
            f'<figcaption>{e(alt)}　写真：{e(author)} / {lh}（<a href="{e(page)}" rel="noopener" target="_blank">Wikimedia Commons</a>）</figcaption></figure>')


def decorate(url, main):
    photos = inline_photos(url)

    def sec_rep(m):
        sec = m.group(0)
        h = re.search(r"<h2>(.*?)</h2>", sec, re.S)
        if not h: return sec
        h2 = strip(h.group(1))
        sec = sec.replace("<h2>", f"<h2>{ic(pick(h2, HEAD))}", 1)
        if re.search(WARN, h2) and "sources" not in sec[:40]:
            sec = sec.replace('<section class="block">', '<section class="block warn">', 1)
        sec = tables(lists(sec, h2), h2)
        sec = subs(sec)
        for key, c in photos.items():  # 見出し（h2・h3）の直後に写真
            sec = re.sub(r"(<h[23]>(?:(?!</h[23]>).)*?" + re.escape(key) + r"(?:(?!</h[23]>).)*?</h[23]>)", lambda mm: mm.group(1) + photo_fig(c), sec, count=1, flags=re.S)
        return sec
    return re.sub(r'<section class="(?:block|sources block)">.*?</section>(?=\s*(?:<section|<div class="block|$|<script))', sec_rep, main, flags=re.S)
