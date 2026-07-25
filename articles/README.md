# articles — 無料公開作品

Gumroad 送客とは別に、**Medium / note で無料公開する作品**を管理するディレクトリです。
(Gumroad 送客記事は `handoff_medium_<title>.md` を起点とする別フローで扱います。)

## 棲み分け

| ディレクトリ | プラットフォーム | 言語 | 想定読者 |
|---|---|---|---|
| [`medium/`](medium/) | Medium | 英語 | 西洋のハイパフォーマー/ビジネス層 |
| [`note/`](note/) | note | 日本語 | 日本語読者 |

## ファイル形式

- 1 作品 = 1 Markdown ファイル
- ファイル名: `YYYYMMDD-slug.md`（例: `20260725-quiet-focus.md`）
- 冒頭に front matter を付ける（下記テンプレート）

## front matter テンプレート

新規作成時は [`_template.md`](_template.md) をコピーしてください。

```yaml
---
title: ""            # 記事タイトル
platform: medium     # medium | note
lang: en             # en | ja
status: draft        # draft | review | revising | published
tags: []             # Medium: 最大5タグ / note: ハッシュタグ
created: YYYY-MM-DD
published_url: ""     # 公開後に URL を記入
source: ""           # 既存作品の場合、元原稿の出所メモ（任意）
---
```

## 既存作品のアップロード手順

過去に作成済みの作品は、以下のいずれかで取り込みます。

1. **md / txt / docx などのファイルをこのリポジトリに置く**（`articles/medium/` または `articles/note/`）
2. こちらで front matter を付与し、Markdown に整形して所定の場所へ格納
3. すでに公開済みなら `status: published` と `published_url` を記録

> 一旦どこに置いても構いません。言語や体裁が混在していても、こちらで
> `medium/`（英語）・`note/`（日本語）へ振り分けて整えます。

## ステータス

| status      | 意味       |
|-------------|-----------|
| `draft`     | 執筆中     |
| `review`    | レビュー中 |
| `revising`  | 修正中     |
| `published` | 公開済み   |
