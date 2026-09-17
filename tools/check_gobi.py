#!/usr/bin/env python3
"""note(JA)記事の語尾の単調さを検出する。

敬体で統一している都合上、地の文が「〜です。」「〜ます。」で揃いやすく、
同じ語尾が3つ以上続くと音読したときに一本調子になる。
`docs/note-conversion-guide.md` の「推敲パス」で使う。

使い方:
    python3 tools/check_gobi.py                      # articles/note/*-ja.md を全件
    python3 tools/check_gobi.py articles/note/x.md   # 個別
    python3 tools/check_gobi.py --min 4              # 4連続以上だけ出す

判定から除外するもの:
  - 見出し行(## 〜)。見出しを挟めば読者は切れ目を感じるため、連続を分断する。
  - 「〜」『〜』で閉じる会話文。原典の問答をそのまま引いている箇所は動かせない。
  - 脚注・出典(区切り線 ────────── より後ろ)と front matter。
"""
import argparse
import glob
import re
import sys

# 長い語尾から先に判定する(「ました」が「ます」に吸われないように)
ENDINGS = ["ました", "ません", "でした", "でしょう", "ください", "のです", "ます", "です"]

SEP = "──────────"


def body_of(path):
    text = open(path, encoding="utf-8").read()
    if "-->" not in text:
        return ""
    body = text.split("-->")[1].split(SEP)[0]
    return re.sub(r"【タイトル案】.*?\n", "", body)


def classify(sentence):
    core = sentence[:-1]
    if core.endswith("」") or core.endswith("』"):
        return None  # 会話文はそのまま
    for ending in ENDINGS:
        if core.endswith(ending):
            return ending
    return None


def sequence(body):
    """(語尾, 文) の並びを返す。見出しの位置には None を挟んで連続を分断する。"""
    items = []
    for line in body.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            items.append(None)
            continue
        for sentence in re.split(r"(?<=。)", line):
            sentence = sentence.strip()
            if sentence.endswith("。"):
                items.append((classify(sentence), sentence))
    return items


def runs(items, minimum):
    found, current = [], []
    for item in items:
        if item is None or item[0] is None:
            if len(current) >= minimum:
                found.append(current)
            current = []
            continue
        if current and current[-1][0] == item[0]:
            current.append(item)
        else:
            if len(current) >= minimum:
                found.append(current)
            current = [item]
    if len(current) >= minimum:
        found.append(current)
    return found


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--min", type=int, default=3, help="何連続から報告するか(既定3)")
    args = parser.parse_args()

    paths = args.paths or sorted(glob.glob("articles/note/*-ja.md"))
    flagged = 0
    for path in paths:
        found = runs(sequence(body_of(path)), args.min)
        if not found:
            continue
        flagged += 1
        print(f"{path}: {len(found)}箇所 (最長{max(len(r) for r in found)}連続)")
        for run in found:
            for ending, sentence in run:
                print(f"    [{ending}] {sentence}")
            print()
    print(f"--- {flagged}/{len(paths)} 本で{args.min}連続以上")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
