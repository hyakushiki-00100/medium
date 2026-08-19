"""
カバー画像生成 (雨シリーズのリファレンス画像を参考に再現)
- 禅語シリーズ（JOBS）: 背景 #F7F5F0 / 本文墨色 #2B2B28 / アクセント #2C3E50。
  縦書きの禅語タイトル(大)+「禅語」ラベル(小)。モチーフ無しのプレーン構図。
- 仏教語シリーズ（JOBS_BUDDHIST）: 背景・アクセントカラーを禅語シリーズと変え、
  禅語シリーズには無い「法輪」の背景モチーフを加える（draw_dharma_wheel）。
  サムネイル（中央正方形クロップ）だけでもシリーズの違いが分かることを狙いにしている。
  新シリーズを追加する場合は、この2シリーズと同様に背景色・アクセントカラー・モチーフの
  3点を必ず変えること（docs/article-production-standard.md 参照）。
- 筆致テクスチャ: 輪郭ジッター、擦れ(dry-brush)、にじみ(ink bleed)、太細(pressure taper)
- 4倍スーパーサンプリング -> LANCZOSダウンサンプル
- 字数に応じて字サイズを自動調整するため、縦1列のまま任意の字数に対応
  （長い語もカバーは正式名のまま。表記は削らない。docs/article-production-standard.md 参照）

使い方:
  python3 tools/build_covers.py            # JOBS + JOBS_BUDDHIST 全件を articles/covers/ に生成
  python3 tools/build_covers.py ikkegoyo   # 指定スラッグのみ再生成
  COVER_OUT_DIR=/path python3 tools/build_covers.py   # 出力先を上書き

依存: numpy, scipy, Pillow / フォント: NotoSerifCJK-Black.ttc
"""
import os
import sys
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
FONT_INDEX = 0  # Japanese

BG_COLOR = (247, 245, 240)
INK_COLOR = (43, 43, 40)
ACCENT_COLOR = (44, 62, 80)

SCALE = 4
OUT_W, OUT_H = 1280, 720
SS_W, SS_H = OUT_W * SCALE, OUT_H * SCALE


def jittered_glyph(ch, size, seed, wear=0.0):
    """1文字を高解像度でレンダリングし、輪郭ジッター・擦れ・にじみを加えたRGBA画像を返す。
    wear: 0=ほぼ均一な筆致 / 1=最大限にかすれ・荒れた筆致(列の下方ほど強める用途)"""
    rng = random.Random(seed)
    pad = int(size * 0.35)
    canvas = size + pad * 2
    font = ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)

    base = Image.new("L", (canvas, canvas), 0)
    d = ImageDraw.Draw(base)
    bbox = font.getbbox(ch)
    cx = (canvas - (bbox[2] - bbox[0])) / 2 - bbox[0]
    cy = (canvas - (bbox[3] - bbox[1])) / 2 - bbox[1]
    d.text((cx, cy), ch, font=font, fill=255)

    arr = np.array(base, dtype=np.float32) / 255.0

    # --- 輪郭ジッター: ランダム位置ずらしを複数回合成してエッジを荒らす ---
    jitter_layers = np.zeros_like(arr)
    n_layers = 8
    max_shift = max(1, int(size * (0.014 + 0.02 * wear)))
    for i in range(n_layers):
        dx = rng.randint(-max_shift, max_shift)
        dy = rng.randint(-max_shift, max_shift)
        shifted = np.roll(np.roll(arr, dy, axis=0), dx, axis=1)
        jitter_layers += shifted
    jitter_layers /= n_layers

    # --- 太細(pressure taper): 縦方向グラデーションで上端・下端をわずかに薄く ---
    ys = np.linspace(0, 1, canvas)
    taper = 0.70 + 0.30 * np.sin(np.pi * ys)
    taper = taper[:, None]
    tapered = jitter_layers * taper

    # --- かすれ(dry-brush): ノイズで一部を欠けさせる。wearが高いほど激しく ---
    from scipy.ndimage import gaussian_filter as _gf
    pre_erosion = tapered  # 「一」等、画数の少ない字が複数の掠れ効果の重なりでほぼ消えるのを防ぐ下限に使う
    rng_np = np.random.RandomState(seed)
    speckle = rng_np.rand(canvas, canvas)
    hole_prob = 0.05 + 0.14 * wear
    dry = np.where(speckle < hole_prob, 0.0, 1.0)
    dry = _gf(dry, sigma=0.9 + 1.2 * wear)
    dry_strength = 0.35 + 0.35 * wear
    tapered = tapered * (1 - dry_strength + dry_strength * dry)

    # 大粒の掠れ(筆が紙から離れる瞬間の抜け)を数カ所加える
    coarse = rng_np.rand(max(4, canvas // 40), max(4, canvas // 40))
    coarse_mask = np.array(
        Image.fromarray((coarse * 255).astype(np.uint8)).resize((canvas, canvas), Image.BILINEAR)
    ).astype(np.float32) / 255.0
    coarse_gate = np.where(coarse_mask < 0.10 + 0.10 * wear, 0.35, 1.0)
    tapered = tapered * coarse_gate

    # 掠れ効果の下限: 「一」のような画数の少ない字が、乾筆+大粒掠れの重なりでほぼ消滅しないよう
    # 元の濃さの一定割合は必ず残す(文字が縦書きの列の途中で消えて改行したように見える不具合を防ぐ)
    tapered = np.maximum(tapered, pre_erosion * 0.45)

    ink_alpha = np.clip(tapered, 0, 1)

    # --- にじみ(ink bleed): ぼかした低アルファ層を下敷きにする ---
    bleed = _gf(ink_alpha, sigma=size * (0.025 + 0.02 * wear))
    bleed_alpha = bleed * (0.30 + 0.15 * wear)

    final_alpha = np.clip(ink_alpha + bleed_alpha * (1 - ink_alpha), 0, 1)

    rgba = np.zeros((canvas, canvas, 4), dtype=np.uint8)
    rgba[..., 0] = INK_COLOR[0]
    rgba[..., 1] = INK_COLOR[1]
    rgba[..., 2] = INK_COLOR[2]
    rgba[..., 3] = (final_alpha * 255).astype(np.uint8)

    # インクの縦方向の重心(行)。「一」等ごく少画数の字は本来のemの中心と
    # インクの塊の中心がずれやすく、canvas位置だけを均等割りすると縦書きの列で
    # 字間が不揃いに見える(まるで途中で改行したような空白ができる)。
    # paste_vertical_column側で、この重心を基準に位置合わせする。
    row_mass = final_alpha.sum(axis=1)
    total_mass = row_mass.sum()
    if total_mass > 1e-6:
        centroid_row = float((row_mass * np.arange(canvas)).sum() / total_mass)
    else:
        centroid_row = canvas / 2.0

    img = Image.fromarray(rgba, mode="RGBA")
    img.ink_centroid_row = centroid_row
    return img


def paste_vertical_column(canvas_img, chars, center_x, top_y, char_size, gap_ratio, color, seed_base, wear_curve=False, wear_n=None):
    """縦書きで文字を並べて貼り付ける。wear_curve=Trueなら下に行くほど掠れを強める。
    位置合わせは各字のcanvas位置ではなく、実際のインクの重心を基準に行う。
    「一」のような画数の少ない字はインクの塊がcanvasの幾何中心からずれやすく、
    canvas位置だけを均等割りすると列の途中で字間が不揃いに見えるため。
    wear_n: 掠れの進み方の基準となる字数。省略時はこの列自身の字数(len(chars))を使う。
    複数列で字数が異なる場合、列ごとの字数を基準にすると短い列ほど掠れが速く進んで
    列間で濃さが不揃いに見えるため、全列共通の基準(通常は最長列の字数)を渡すこと。"""
    step = char_size * (1 + gap_ratio)
    n = len(chars)
    wear_ref = wear_n if wear_n is not None else n
    target_centroid_y = top_y + step / 2  # 1字目の理想的なインク重心位置
    for i, ch in enumerate(chars):
        wear = (i / max(1, wear_ref - 1)) * 0.85 if wear_curve else 0.0
        glyph = jittered_glyph(ch, int(char_size), seed_base + i, wear=wear)
        centroid_row = glyph.ink_centroid_row
        if color != INK_COLOR:
            arr = np.array(glyph)
            arr[..., 0] = color[0]
            arr[..., 1] = color[1]
            arr[..., 2] = color[2]
            glyph = Image.fromarray(arr, mode="RGBA")
        gw, gh = glyph.size
        px = int(center_x - gw / 2)
        py = int(round(target_centroid_y - centroid_row))
        canvas_img.alpha_composite(glyph, (px, py))
        target_centroid_y += step
    return target_centroid_y


def add_paper_grain(img, seed=1):
    rng_np = np.random.RandomState(seed)
    arr = np.array(img).astype(np.float32)
    noise = rng_np.normal(0, 3.0, arr.shape[:2])
    for c in range(3):
        arr[..., c] += noise
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def draw_dharma_wheel(canvas, center, radius, color, seed=1, alpha=42, spokes=8):
    """法輪(だるまホイール)のうっすらとした背景モチーフ。仏教語シリーズ専用。
    禅語シリーズには存在しないシルエットのため、サムネイル(中央クロップ)だけでも
    シリーズの違いが一目で分かるようにする。円相(禅画の丸)と混同しないよう、
    二重の輪+ハブ+放射スポークという法輪の構造で描く。"""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    rng = random.Random(seed)
    line_w = max(2, int(radius * 0.018))
    rgba = tuple(color) + (alpha,)

    def wobbly_ellipse(r):
        # 定規で引いたような機械的な円にならないよう、微小に中心をずらして2重に描く
        for _ in range(2):
            jx = rng.uniform(-radius * 0.006, radius * 0.006)
            jy = rng.uniform(-radius * 0.006, radius * 0.006)
            d.ellipse(
                [cx - r + jx, cy - r + jy, cx + r + jx, cy + r + jy],
                outline=rgba, width=line_w,
            )

    outer_r = radius
    inner_r = radius * 0.82
    hub_r = radius * 0.13
    wobbly_ellipse(outer_r)
    wobbly_ellipse(inner_r)
    wobbly_ellipse(hub_r)

    for i in range(spokes):
        angle = 2 * math.pi * i / spokes
        x1 = cx + hub_r * math.cos(angle)
        y1 = cy + hub_r * math.sin(angle)
        x2 = cx + inner_r * math.cos(angle)
        y2 = cy + inner_r * math.sin(angle)
        d.line([x1, y1, x2, y2], fill=rgba, width=line_w)

    layer = layer.filter(ImageFilter.GaussianBlur(radius=radius * 0.006))
    canvas.alpha_composite(layer)


def make_cover(title_chars, label_chars, out_path, seed=42, accent_color=None, bg_color=None, motif=None, columns=None):
    """columns: 長いタイトルを縦2列以上に割りたい場合、右から読む順の文字列リストを渡す
    (例: ["一日不作", "一日不食"])。省略時は title_chars をそのまま1列で表示する(従来どおり)。
    正式名は削らない方針のため、字数が多いときは1列の字サイズを下げるより2列に割るほうを優先する。"""
    accent = accent_color or ACCENT_COLOR
    bg = bg_color or BG_COLOR
    canvas = Image.new("RGBA", (SS_W, SS_H), bg + (255,))

    cols = columns if columns else [title_chars]
    n = max(len(c) for c in cols)  # 列ごとの字数の最大値で字サイズを決める
    margin_ratio = 0.16
    usable_h = SS_H * (1 - margin_ratio * 2)
    gap_ratio = 0.22
    char_size = usable_h / (n + (n - 1) * gap_ratio)
    char_size = min(char_size, SS_H * 0.30)  # 極端に大きくなりすぎないよう上限

    total_h = char_size * n + char_size * gap_ratio * (n - 1)
    top_y = (SS_H - total_h) / 2
    center_x = SS_W * 0.46

    if motif == "dharma_wheel":
        draw_dharma_wheel(canvas, (center_x, SS_H / 2), radius=SS_H * 0.30, color=accent, seed=seed)

    # 縦書きは右から左へ列を進める。1列目(cols[0])がいちばん右。
    n_cols = len(cols)
    col_step = char_size * 1.15  # 列間の間隔
    rightmost_x = center_x + col_step * (n_cols - 1) / 2
    for ci, col_text in enumerate(cols):
        col_center_x = rightmost_x - col_step * ci
        col_top_y = top_y + (n - len(col_text)) * (char_size * (1 + gap_ratio)) / 2  # 字数が少ない列は中央揃え
        paste_vertical_column(canvas, col_text, col_center_x, col_top_y, char_size, gap_ratio, INK_COLOR, seed + ci * 50, wear_curve=True, wear_n=n)

    # ラベル(小・アクセントカラー・タイトルの右上)。シリーズごとに label_chars / accent_color を切り替え可能
    label_size = char_size * 0.30
    label_gap = 0.30
    label_total_h = label_size * len(label_chars) + label_size * label_gap * (len(label_chars) - 1)
    label_top = top_y + char_size * 0.15
    label_center_x = rightmost_x + char_size * 0.95
    paste_vertical_column(canvas, label_chars, label_center_x, label_top, label_size, label_gap, accent, seed + 100)

    # ダウンサンプル
    final = canvas.convert("RGB").resize((OUT_W, OUT_H), Image.LANCZOS)
    final = add_paper_grain(final, seed=seed)

    # 端にインクが到達していないか検査 (numpyピクセル検査)
    # 背景を暗く/暖色にするシリーズが増えるほどこの閾値との余裕は減る
    # （仏教語シリーズの生成り色 #F2E8D4 で輝度マージンは約21）。
    # 新シリーズで背景をさらに暗くする場合は、この余裕を実測で確認すること。
    arr = np.array(final.convert("L"))
    edge = np.concatenate([arr[0, :], arr[-1, :], arr[:, 0], arr[:, -1]])
    assert edge.min() > 200, "インクが画像端に到達しています"

    final.save(out_path, quality=95)
    print("saved:", out_path, final.size)
    return final


def make_thumbnail(cover_img, out_path):
    w, h = cover_img.size
    side = min(w, h)
    left = (w - side) // 2
    top = int(h * 0.06)
    top = min(top, h - side)
    cropped = cover_img.crop((left, top, left + side, top + side))
    thumb = cropped.resize((600, 600), Image.LANCZOS)
    thumb.save(out_path, quality=95)
    print("saved:", out_path, thumb.size)


# slug -> (タイトル, ラベル)。タイトルはカバーも正式名のまま（表記を削らない）。
# 禅語シリーズ専用。禅宗(中国禅・日本の臨済宗/曹洞宗)の言葉のみ、ラベルは「禅語」固定。
JOBS = [
    ("nengemisho", "拈華微笑", "禅語"),
    ("ikkegoyo", "一華開五葉", "禅語"),
    ("kyokasuigetsu", "鏡花水月", "禅語"),
    ("katsu", "喝", "禅語"),
    ("hogejaku", "放下著", "禅語"),
    ("genkan", "玄関", "禅語"),
    ("ichigoichie", "一期一会", "禅語"),
    ("kankyakka", "看脚下", "禅語"),
    ("shujinko", "主人公", "禅語"),
    ("mukudoku", "無功徳", "禅語"),
    ("sekishu", "隻手の声", "禅語"),
    ("byojoshin", "平常心是道", "禅語"),
    ("kyogen", "香厳撃竹", "禅語"),
    ("kissako", "喫茶去", "禅語"),
    ("muichimotsu", "本来無一物", "禅語"),
    ("baishijukuya", "梅子熟也", "禅語"),
    ("masangin", "麻三斤", "禅語"),
    ("fusaku", "一日不作一日不食", "禅語"),
    ("anjin", "安心", "禅語"),
    ("mu", "無", "禅語"),
    ("kanto", "百尺竿頭進一歩", "禅語"),
    ("daichi", "雪峰尽大地", "禅語"),
    ("nichinichi", "日日是好日", "禅語"),
    ("muinoshinnin", "無位真人", "禅語"),
    ("mukanjo", "洞山無寒暑", "禅語"),
    ("bashoan", "婆子焼庵", "禅語"),
    ("suikogyu", "潙山水牯牛", "禅語"),
    ("hifuhiban", "非風非幡", "禅語"),
]

# 8字等、1列では字が小さくなりすぎる/字間が間延びして見えるタイトルは、
# 意味の切れ目(読点の位置等)で縦2列に割る。表記は削らない(正式名のまま)。
COLUMN_SPLITS = {
    "fusaku": ["一日不作", "一日不食"],  # 「一日不作、一日不食」の読点で分割。右列が先に読む側
    "kanto": ["百尺竿頭", "進一歩"],  # 「百尺竿頭・進一歩」の意味の切れ目で分割。右列が先に読む側
}

# 仏教語シリーズ専用。禅宗に限らない仏教の言葉（天台宗・浄土宗 等）。
# 禅語シリーズと混同しないよう、背景色・アクセントカラー・ラベル文言に加えて
# 禅語シリーズには存在しない「法輪」の背景モチーフを入れる。
# サムネイル(中央クロップ)だけでもシリーズの違いが分かることを狙いにしている。
BUDDHIST_BG_COLOR = (242, 232, 212)   # 温かみのある生成り色（禅語シリーズの #F7F5F0 は寒色寄りの白）
BUDDHIST_ACCENT_COLOR = (139, 90, 43)  # 温かみのある琥珀色（禅語シリーズの #2C3E50 と区別）
JOBS_BUDDHIST = [
    ("ichigu", "一隅を照らす", "仏教語"),
]

if __name__ == "__main__":
    out_dir = os.environ.get(
        "COVER_OUT_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "articles", "covers"),
    )
    only = set(sys.argv[1:])  # 指定スラッグのみ。無指定なら全件
    for i, (slug, title, label) in enumerate(JOBS):
        if only and slug not in only:
            continue
        make_cover(title, label, os.path.join(out_dir, f"{slug}.png"), seed=42 + i * 17, columns=COLUMN_SPLITS.get(slug))
    for i, (slug, title, label) in enumerate(JOBS_BUDDHIST):
        if only and slug not in only:
            continue
        make_cover(
            title, label, os.path.join(out_dir, f"{slug}.png"),
            seed=142 + i * 17,
            accent_color=BUDDHIST_ACCENT_COLOR,
            bg_color=BUDDHIST_BG_COLOR,
            motif="dharma_wheel",
        )
