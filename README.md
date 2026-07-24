# medium 出品作品製作チーム

Medium（[medium.com](https://medium.com)）に公開する作品（記事・シリーズ）を、チームで
企画・執筆・レビュー・公開まで一貫して回すためのワークスペースです。

このリポジトリは「作品を作る場所」であると同時に、チームの運営ルール・制作フロー・
テンプレートを一元管理する場所です。新しくジョインしたメンバーは、まず本 README と
[`docs/`](docs/) を読めば動き出せるようにしています。

## 目的

- **品質を揃える** — 誰が書いても一定水準の作品になるよう、テンプレートとチェックリストを共有する
- **フローを見える化する** — 企画から公開までの状態を [`works/`](works/) 配下で追跡する
- **属人化を避ける** — 役割・意思決定・公開手順をドキュメントとして残す

## ディレクトリ構成

```
.
├── README.md              # このファイル
├── docs/                  # チーム運営・制作フローのドキュメント
│   ├── workflow.md        # 企画〜公開までの制作フロー
│   ├── roles.md           # 役割分担
│   ├── style-guide.md     # 表記・トーンのスタイルガイド
│   └── publishing-checklist.md  # 公開前チェックリスト
├── templates/             # 各種テンプレート
│   ├── article.md         # 記事テンプレート
│   └── proposal.md        # 企画書テンプレート
└── works/                 # 制作中・公開済みの作品
    ├── README.md          # works の使い方と状態管理ルール
    └── drafts/            # 執筆中の下書き
```

## クイックスタート

1. 新しい作品を始めるときは [`templates/proposal.md`](templates/proposal.md) をコピーして企画を起こす
2. 承認されたら [`templates/article.md`](templates/article.md) をコピーして [`works/drafts/`](works/drafts/) に置き、執筆を始める
3. 執筆が終わったら [`docs/publishing-checklist.md`](docs/publishing-checklist.md) に沿ってレビュー・公開する

## 制作フロー（概要）

```
企画 → 承認 → 執筆 → レビュー → 修正 → 公開 → 振り返り
```

各ステップの詳細は [`docs/workflow.md`](docs/workflow.md) を参照してください。
