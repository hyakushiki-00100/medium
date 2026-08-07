"""
禅語シリーズ カバー画像生成 (雨シリーズのリファレンス画像を参考に再現)
- 背景 #F7F5F0 / 本文墨色 #2B2B28 / アクセント #2C3E50
- 縦書きの禅語タイトル(大)+「禅語」ラベル(小)
- 筆致テクスチャ: 輪郭ジッター、擦れ(dry-brush)、にじみ(ink bleed)、太細(pressure taper)
- 4倍スーパーサンプリング -> LANCZOSダウンサンプル
- 字数に応じて字サイズを自動調整するため、縦1列のまま任意の字数に対応
  （長い禅語はカバーも正式名のまま。表記は削らない。docs/article-production-standard.md 参照）

使い方:
  python3 tools/build_covers.py            # jobs 全件を articles/covers/ に生成
  python3 tools/build_covers.py ikkegoyo   # 指定スラッグのみ再生成
  COVER_OUT_DIR=/path python3 tools/build_covers.py   # 出力先を上書き

依存: numpy, scipy, Pillow / フォント: NotoSerifCJK-Black.ttc
"""
import os
import sys
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

    return Image.fromarray(rgba, mode="RGBA")


def paste_vertical_column(canvas_img, chars, center_x, top_y, char_size, gap_ratio, color, seed_base, wear_curve=False):
    """縦書きで文字を並べて貼り付ける。wear_curve=Trueなら下に行くほど掠れを強める"""
    y = top_y
    step = char_size * (1 + gap_ratio)
    n = len(chars)
    for i, ch in enumerate(chars):
        wear = (i / max(1, n - 1)) * 0.85 if wear_curve else 0.0
        glyph = jittered_glyph(ch, int(char_size), seed_base + i, wear=wear)
        if color != INK_COLOR:
            arr = np.array(glyph)
            arr[..., 0] = color[0]
            arr[..., 1] = color[1]
            arr[..., 2] = color[2]
            glyph = Image.fromarray(arr, mode="RGBA")
        gw, gh = glyph.size
        px = int(center_x - gw / 2)
        py = int(y)
        canvas_img.alpha_composite(glyph, (px, py))
        y += step
    return y


def add_paper_grain(img, seed=1):
    rng_np = np.random.RandomState(seed)
    arr = np.array(img).astype(np.float32)
    noise = rng_np.normal(0, 3.0, arr.shape[:2])
    for c in range(3):
        arr[..., c] += noise
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def make_cover(title_chars, label_chars, out_path, seed=42, accent_color=None):
    accent = accent_color or ACCENT_COLOR
    canvas = Image.new("RGBA", (SS_W, SS_H), BG_COLOR + (255,))

    n = len(title_chars)
    margin_ratio = 0.16
    usable_h = SS_H * (1 - margin_ratio * 2)
    gap_ratio = 0.22
    char_size = usable_h / (n + (n - 1) * gap_ratio)
    char_size = min(char_size, SS_H * 0.30)  # 極端に大きくなりすぎないよう上限

    total_h = char_size * n + char_size * gap_ratio * (n - 1)
    top_y = (SS_H - total_h) / 2
    center_x = SS_W * 0.46

    paste_vertical_column(canvas, title_chars, center_x, top_y, char_size, gap_ratio, INK_COLOR, seed, wear_curve=True)

    # ラベル(小・アクセントカラー・タイトルの右上)。シリーズごとに label_chars / accent_color を切り替え可能
    label_size = char_size * 0.30
    label_gap = 0.30
    label_total_h = label_size * len(label_chars) + label_size * label_gap * (len(label_chars) - 1)
    label_top = top_y + char_size * 0.15
    label_center_x = center_x + char_size * 0.95
    paste_vertical_column(canvas, label_chars, label_center_x, label_top, label_size, label_gap, accent, seed + 100)

    # ダウンサンプル
    final = canvas.convert("RGB").resize((OUT_W, OUT_H), Image.LANCZOS)
    final = add_paper_grain(final, seed=seed)

    # 端にインクが到達していないか検査 (numpyピクセル検査)
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
]

# 仏教語シリーズ専用。禅宗に限らない仏教の言葉（天台宗・浄土宗 等）。
# 禅語シリーズと混同しないよう、ラベル文言とアクセントカラーを変える。
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
        make_cover(title, label, os.path.join(out_dir, f"{slug}.png"), seed=42 + i * 17)
    for i, (slug, title, label) in enumerate(JOBS_BUDDHIST):
        if only and slug not in only:
            continue
        make_cover(title, label, os.path.join(out_dir, f"{slug}.png"), seed=142 + i * 17, accent_color=BUDDHIST_ACCENT_COLOR)
