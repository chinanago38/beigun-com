# HANDOFF
- 2026-11-29 トップのヒーローを 3Dちんあなご（Higgsfield gpt_image_2_5 low 1k・0.25・基準の絵を参照・assets/hero-720/1344.webp・元は E:/claudecode/chinanago-dist/hero-20261129/）にし、全9面を組み替え（tools/design.py：見出しのアイコン・カード・事実の箱・注意の箱・時系列・横に動く表、本文の文は機械で照らして消え0）。写真は横田・三沢・ニュースに Commons の3枚（tools/photos/inline.tsv）と /event/ の1枚（picked.tsv）。次：gh-photos.js は inline.tsv を見ないので、写真を足すときは重なりに注意。
- 2026-11-28 米軍の演習の節のリンク先を notam.tokyo/us-military/ に（notam.tokyo の席が usmil.json と専用の面を作った・手元の site/data/usmil.json の url を使う）。次：毎時の相乗り（usmil_refresh.py）はハブの判断待ち。
- 2026-11-28 ニュース1本 /news/cloudone202611/（米空軍 Cloud One への不正侵入の報道・ロイター11/27と時事11/28、Cloud One の説明は AFLCMC 2024/9/12）とトップの「新着ニュース」欄。合う手持ちの写真が無いので写真は置かず表と箱で。/news/ の一覧はまだ無い。次：公式発表が出たら追記。
- 2026-11-28 トップに「米軍の演習・訓練（NOTAM）」の節（地図の赤い丸・期間・場所・種類・notam.tokyo へのリンク）。元は notam-code/data/notams.json を tools/notam_usmil.py で抜き出した data/usmil_notam.json。次：毎時の更新は tools/usmil_refresh.py を CRON-notam-refresh の後に呼ぶ案をハブに出した（まだつないでいない）。
- 2026-11-27 写真カードと「要点の箱・手順・よくある質問」の見た目を足し、Commons の自由ライセンスの写真を 0 面に割り当てた（tools/photos/picked.tsv）。次：面の追加と箱の追記は seo-system/tools/gh-grow.js。
- 2026-11-27 「非公式」「個人運営」の字をなくし、運営を ちんあなご編集部に（公式と関係の無い断りはフッターに1行）。次：AGENTS.md の表記の行は直していない（運営者かハブが直す）。
- 2026-11-27 Bing の確認ファイル（BingSiteAuth.xml）と ads.txt を追加。次：なし（消さない）。
