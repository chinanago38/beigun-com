#!/usr/bin/env python3
"""米軍の演習 NOTAM の更新（notam.tokyo の毎時の取り込みに相乗りする用・2026-11-28）。
notam.tokyo の CRON-notam-refresh が data/notams.json を書いた後に1回呼ぶ想定:
    python E:/claudecode/_gh/beigun-com/tools/usmil_refresh.py
中身（NOTAM の組）が変わったときだけ、作り直して commit・push する（GitHub Pages が公開・IndexNow は Actions が送る）。
変わっていなければ何もしない（取得日時だけの差では push しない）。トークンは使わない。"""
import os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
py = sys.executable


def run(*a):
    return subprocess.run(a, cwd=ROOT, text=True, capture_output=True)


r = run(py, "tools/notam_usmil.py", *sys.argv[1:])
print(r.stdout.strip(), r.stderr.strip())
if r.returncode == 3: sys.exit(0)          # 変わっていない
if r.returncode != 0: sys.exit(r.returncode)
run("git", "pull", "--rebase", "-q", "origin", "main")
b = run(py, "tools/build.py"); print(b.stdout.strip(), b.stderr.strip())
if b.returncode != 0: sys.exit(b.returncode)
run("git", "add", "data/usmil_notam.json", "index.html", "sitemap.xml")
c = run("git", "commit", "-q", "-m", "米軍の演習 NOTAM を更新（notam.tokyo の取り込みから）")
if c.returncode == 0:
    p = run("git", "push", "-q", "origin", "HEAD:main"); print("push", p.returncode, p.stderr.strip())
    sys.exit(p.returncode)
print("nothing to commit")
