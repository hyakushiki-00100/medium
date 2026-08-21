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

## 執筆前後のチェック（Opus 精査で発見・2026-08-21〜）

utekisei/houu/ukiseikou/un の4本を Opus に横断評価させた結果、以下が判明した。新規スレッド作成時は
必ず確認する。

### 最優先（正確性・誠実さに直結、CLAUDE.md の非交渉基準に抵触しうる）

1. **鍵括弧の中は原典の逐語のみ。地の文の解釈を、登場人物の発言として引用符付きで書かない。**
   実例: utekisei 1/ が、著者の解釈文(元記事 L49)を師の台詞として引用符付きで提示し、2/ の逐語(師の
   本物の台詞)と食い違った。
   ```bash
   # 元記事にその文字列が実在するか確認する
   grep -o '"[^"]*"' social/x-thread-<slug>.md | while read q; do
     grep -qF "${q//\"/}" articles/medium/<slug>-en.md || echo "NOT IN SOURCE: $q"
   done
   ```
2. **元記事の断り書き・限定条件を、字数を理由に落とさない。** 元記事に Appendix／「for accuracy」／
   「harder to confirm」／「author's modern framing」／「Before questioning X, it's worth asking Y」
   のような留保がある場合、対応する断りをスレッド内のどこかに必ず1ビート確保する。
   実例: un が元記事冒頭の「吽は禅由来ではなくサンスクリットhūṃの音写」という断りを12ツイート中どこにも
   載せていなかった。houu 6/ が元記事の「フィードバックの質を疑う前に」という順序指定を落として言い切りに
   なっていた。
3. **断定の強度を元記事より上げない。** 元記事にない強調副詞(far / always / never 等)を追加しない。
   「the parable shows」のような帰属付きの記述を、無帰属の一般命題に変えない。
   実例: un 8/ が元記事の「more stubbornly」を「far more stubbornly」に強め、Appendix が明記した
   「著者の現代的な枠付け」という帰属を落として「Psychology has a name for this」に書き換えていた。
4. **フック(1/)が2/以降の事実と矛盾していないか確認する。** キャッチーさのために事実を曲げない。
   実例: un 1/「It has no sound.」が2/「the very last sound in the Siddham alphabet」と正面衝突。

### 推奨（クリック率・プラットフォームネイティブ感に直結）

5. **各ツイートは単独で意味が通る形で始める。** 矢印(→)始まり、番号リストのツイート跨ぎ(1)2)は同じ
   ツイート内にまとめる、3)から始まるツイートを作らない)、コロンで宙吊りにして次ツイートに繋ぐ書き方は
   禁止。X ではツイートが単独で(引用RT・検索経由等で)表示されるため、これらは「記事を機械的に分割した」
   ことが読者にバレる原因になる。
6. **CTA の冒頭句をスレッド間で使い回さない。** 「Full piece ... 👇」を複数本で使わない。付録的な
   関連語(例: 複数記事にまたがる「一雨潤千山」)を毎回の特典として売らない — 使い回しに見える。
   代わりに、そのスレッドで意図的に伏せた要素(未提示の問い・人物の返答等)を名指しする。
   ```bash
   # CTA冒頭句の衝突チェック
   grep -h "Full piece\|👇" social/x-thread-*.md | sort | uniq -c | sort -rn
   ```
7. **スレッドで記事の実践パート(問い・手順)を全文そのまま出さない。** CLAUDE.md のカットライン原則
   (本編の核心手前で止める)を Medium への送客にも適用する。問い・手順は半分以下だけ出し、残りをCTAで
   名指しして記事に誘導する。
8. **元記事の見出し(H2)を上から順に1:1でツイート化しない。** 記事で一番強い一節を2/までに前倒しし、
   由来・出典は中盤以降に回す(X は結論先出し・出典後出しが基本)。ビート数をスレッドごとに揃えない。
9. **スレッド横断の定型句リストを保持し、使い回しを避ける**（`docs/article-production-standard.md`
   の EN/JA 定型文リストの social 版）。検出済み: `Read at face value, ...` / `Where this shows up
   at work:`(本体側で既に禁止された定型見出しの再輸入)/ `Two/Three questions worth asking:` /
   `Not [X]. Just [Y].` 締め / フック末尾の `[予告文] 🧵👇`。
   ```bash
   grep -n "Read at face value\|shows up at work\|questions worth asking\|^Not a \|Full piece" social/x-thread-*.md
   ```
10. **em ダッシュは1スレッド4個以下を目安にする。** essay的な密度(ほぼ毎ツイート1個)は「記事です」という
    視覚的な署名になる。同じ強調語(例: sharper)をスレッド内で2回使っていないかも確認する。
11. **誇大表現を避ける**（CLAUDE.md「誇大・神秘化・恐怖訴求をしない」は social にも適用）。
    「the most underrated skill nobody's teaching you」のような煽り文句でフックを作らない。
    フックの強度は誇張ではなく具体物と反転で作る。

## 命名規則

`social/x-thread-<slug>.md`（`<slug>` は元記事の slug と揃える）。
先頭に元記事へのパスと、CTA で使う元記事 URL をメモとして残す。
