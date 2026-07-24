# works

制作中・公開済みの作品を管理するディレクトリです。

## 使い方

1. 承認された企画は [`templates/article.md`](../templates/article.md) をコピーして
   [`drafts/`](drafts/) に配置する
2. ファイル名は `YYYYMMDD-slug.md`（例: `20260724-medium-workflow.md`）
3. 作品の状態はファイル冒頭のメタ情報 `status` で管理する

## 状態

| status      | 意味       |
|-------------|-----------|
| `draft`     | 執筆中     |
| `review`    | レビュー中 |
| `revising`  | 修正中     |
| `published` | 公開済み   |

公開済みの作品も履歴として本ディレクトリに残し、`status: published` と
`published_url` を記録します。
