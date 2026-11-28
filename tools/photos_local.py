#!/usr/bin/env python3
"""面に出す写真（commons.tsv・picked.tsv・inline.tsv）を webp（幅1200px以下）にして assets/photos/ に置く（2026-11-29）。
対応表は tools/photos/local.json（元の URL → /assets/photos/<名前>.webp）。build.py が出力の HTML の URL を置き換える。
写真ギャラリー（gallery.tsv）は対象外。使い方：python tools/photos_local.py（ffmpeg が要る・取得は1枚ずつ間をあける）"""
import hashlib, json, os, re, subprocess, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PD = os.path.join(ROOT, "tools", "photos")
OUT = os.path.join(ROOT, "assets", "photos")
MAP = os.path.join(PD, "local.json")
UA = {"User-Agent": "beigun-com-photo-bot/1.0 (https://xn--v5zv98a.com/)"}


def srcs():
    out = []
    for name, col in (("commons.tsv", 1), ("picked.tsv", 1), ("inline.tsv", 2), ("gallery_ok.tsv", 0)):
        f = os.path.join(PD, name)
        if not os.path.exists(f): continue
        for l in open(f, encoding="utf-8").read().splitlines()[1:]:
            c = l.split("\t")
            if len(c) > col and c[col].startswith("https://"): out.append(c[col].split("?")[0])
    return out


def name_of(u):
    base = re.sub(r"\.[A-Za-z]+$", "", u.rstrip("/").split("/")[-2] if "/thumb/" in u else u.split("/")[-1])
    base = re.sub(r"[^A-Za-z0-9]+", "-", urllib.request.unquote(base)).strip("-").lower()[:60]
    return f"{base}-{hashlib.md5(u.encode()).hexdigest()[:6]}.webp"


def main():
    os.makedirs(OUT, exist_ok=True)
    m = json.load(open(MAP, encoding="utf-8")) if os.path.exists(MAP) else {}
    for u in srcs():
        if u in m and os.path.exists(os.path.join(ROOT, m[u].lstrip("/"))): continue
        name = name_of(u); tmp = os.path.join(OUT, name + ".src")
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r: open(tmp, "wb").write(r.read())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-vf", "scale='min(1200,iw)':-2", "-c:v", "libwebp", "-quality", "78", os.path.join(OUT, name)], check=True)
        os.remove(tmp)
        m[u] = "/assets/photos/" + name
        print("ok", name)
        time.sleep(2)
    json.dump(m, open(MAP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
