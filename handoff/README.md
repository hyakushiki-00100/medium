# handoff — チーム間の引き継ぎ

チームをまたぐ引き継ぎファイルを置く場所です。

## 引き継ぎの向き

| ファイル | 向き | 内容 |
|---|---|---|
| `handoff_medium_<title>.md` | 本体チーム → **この Medium チーム** | ブランド文脈・商品情報・Gumroad リンク・抜粋素材/対象章・推奨アングル・CTA |
| `handoff_note_<title>.md` | この Medium チーム → **NOTE チーム** | note(日本語)公開に向けた素材・アングル・注意点 |

> note 公開作品は別の NOTE チームが担当します。このチームは note 向けの素材が出たら
> [`handoff_note.template.md`](handoff_note.template.md) をコピーして
> `handoff_note_<title>.md` を作成し、NOTE チームへ引き継ぎます。

## note 変換の共通仕様

note で公開できる形に整える際の変換ルール（表→箇条書き・見出しは h2/h3 のみ・
`---`→区切り線・タグは投稿欄で入力・HTML は直貼り不可 等）は
[`../docs/note-conversion-guide.md`](../docs/note-conversion-guide.md) にまとめてある。
引き継ぎ時はこのガイドを共通仕様として参照する。
