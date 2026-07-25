# articles — 無料公開作品

Gumroad 送客とは別に、**Medium で無料公開する作品**を管理するディレクトリです。
(Gumroad 送客記事は `handoff_medium_<title>.md` を起点とする別フローで扱います。)

## 担当範囲

| 対象 | 担当 | 場所 |
|---|---|---|
| **Medium(英語)の無料作品** | このチームが執筆・管理 | [`medium/`](medium/) |
| **note(日本語)の作品** | 公開は別の **NOTE チーム** | 制作済みの控えは [`note/`](note/) にアーカイブ |

> note 公開作業は NOTE チームが別に担当します（引き継ぎは [`../handoff/`](../handoff/)）。
> note 向けの素材・アングルが出たら `handoff/handoff_note_<title>.md` を作って引き継ぎます。
> 制作済みの note 作品の**控え**は [`note/`](note/) にアーカイブとして保持します（公開フローそのものではありません）。

## ファイル形式（Medium 作品）

- 1 作品 = 1 Markdown ファイル
- ファイル名: `YYYYMMDD-slug.md`（例: `20260725-quiet-focus.md`）
- 冒頭に front matter を付ける（[`_template.md`](_template.md) をコピー）

```yaml
---
title: ""            # 記事タイトル
platform: medium
lang: en
status: draft        # draft | review | revising | published
tags: []             # 最大 5 タグ
created: YYYY-MM-DD
published_url: ""     # 公開後に URL を記入
source: ""           # 既存作品の場合、元原稿の出所メモ（任意）
---
```

## 既存作品のアップロード手順（Medium）

過去に作成済みの Medium 作品は、以下で取り込みます。

1. **md / txt / docx などのファイルを [`medium/`](medium/) に置く**
2. こちらで front matter を付与し、Markdown に整形
3. すでに公開済みなら `status: published` と `published_url` を記録

## ステータス

| status      | 意味       |
|-------------|-----------|
| `draft`     | 執筆中     |
| `review`    | レビュー中 |
| `revising`  | 修正中     |
| `published` | 公開済み   |

## タグ管理

Medium 記事ごとの確定タグは [`tag-tracker.md`](tag-tracker.md) に記録する
（1 つ目最重要・固定ペア＋可変、フォロワー数は編集画面で最終確認）。

## カバー画像

各記事のカバー画像（PNG）は [`covers/`](covers/) に slug 名で格納する（日英・note/Medium で共用）。

## 制作標準

ボリューム目安・記事の構成の型・史実性の扱い・カバー画像仕様は
[`../docs/article-production-standard.md`](../docs/article-production-standard.md) にまとめてある。
