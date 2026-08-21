# social/ — X(Twitter)スレッド等の SNS 二次展開

Medium/note 記事(`articles/medium/*.md` / `articles/note/*.md`)を土台に、X スレッド等へ
再構成したものを置く。本体の禅語シリーズのパイプラインとは別の、都度リクエストで作成するアドホックな成果物。

## X スレッド作成時の注意点(実際に起きた不具合)

### 番号付きリスト「1. 」がXに誤ってリンク化される（2026-08-21 に実際に発生）

`1. Text` のように**ピリオドの直後に半角スペース**を挟む番号付きリストは、コピペや自動整形の過程で
スペースが失われると `1.Text` になり、X の自動リンク検出が「`1.am`」のような**実在する TLD
(`.am`＝アルメニア、`.co`／`.io`／`.me` 等も同様に実在)を含むドメイン名**と誤認識し、
勝手にハイパーリンク化してしまう。

**対策**: 番号付きリストは `1. ` ではなく **`1) `**（丸括弧）を使う。ピリオド由来のドメイン誤認識を避けられる。
本文中で `N.文字` のような「数字+ピリオド+英字」が隣接する箇所がないか、投稿前に必ず目視確認する。

```bash
# 執筆後、この種の危険パターンが残っていないか機械チェックする
grep -noP '\d\.\w' social/x-thread-<slug>.md
# medium.com 等の完全な URL 行はヒットして問題ない(意図したリンクのため)。
# それ以外(特に "数字.英字" の並び)がヒットしたら 1) 形式に直す。
```

## 文字数チェック（280字/ポスト、URL は t.co 換算で23字固定）

X は投稿に含まれる URL の実際の長さに関わらず、常に23字として文字数にカウントする
(t.co短縮リンクの固定長)。スレッド作成後、以下で全ポストが280字以内か確認する。

```bash
python3 << 'EOF'
import re
text = open('social/x-thread-<slug>.md').read()
segments = re.split(r'^\*\*(\d+)/\*\*\s*$', text, flags=re.M)
it = iter(segments[1:])
for num, body in zip(it, it):
    body_clean = body.strip().split('\n---')[0].strip()
    body_for_count = re.sub(r'https?://\S+', 'x'*23, body_clean)
    print(num, len(body_for_count), 'OVER' if len(body_for_count) > 280 else 'ok')
EOF
```

## 命名規則

`social/x-thread-<slug>.md`（`<slug>` は元記事の slug と揃える）。
先頭に元記事へのパスと、CTA で使う元記事 URL をメモとして残す。
