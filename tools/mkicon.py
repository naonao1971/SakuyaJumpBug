"""咲耶ジャンプバグのアイコン(apple-touch-icon 180px / favicon 32px)を作る。

    python3 tools/mkicon.py apple-touch-icon.png favicon-32.png

姉妹作(咲耶スクランブル=ピンクの機体、咲耶Nounラリー=ピンクのラリーカー)と並べて
姉妹作だと分かるよう、「暗い四角+金の枠」はそろえ、中身だけこの作品の車にする。

車はゲーム中のドット絵(index.html の CAR_SPRITE / CAR_COLORS / WHEEL_FRAMES)を
そのまま読んで描く。ゲームで車を描き直せば、このスクリプトを流し直すだけで追従する。
ラリーカー(横向きのなめらかなセダン)と見分けやすいよう、
  - ドット絵のまま拡大する(ぼかさない)
  - 屋根に ⌐◨-◨、鉢巻をなびかせる
  - 車を宙に浮かせ、下に影を落として「跳ねている」ことを見せる
32px は 180px を縮めると潰れるので、1ドット=1pxで別に描く。
"""
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "index.html").read_text(encoding="utf-8")


def js_block(name):
    m = re.search(r"const %s = (\[|\{)(.*?)(\]|\});" % name, src, re.S)
    if not m:
        raise SystemExit(f"{name} が index.html に見つからない")
    return m.group(2)


SPRITE = re.findall(r'"([^"]+)"', js_block("CAR_SPRITE"))
COLORS = {k: v for k, v in re.findall(r'(\w):\s*"(#[0-9A-Fa-f]{6})"', js_block("CAR_COLORS"))}
WHEEL = re.findall(r'"([^"]+)"', js_block("WHEEL_FRAMES"))[:6]      # 1コマ目
WHEEL_COLS = [int(v) for v in re.findall(r"\d+", js_block("WHEEL_COLS"))]

BG = "#06070C"       # --bg
GOLD = "#E8C56A"     # --gold 枠
MAGENTA = "#FF2D9B"  # --magenta 鉢巻
SHADOW = "#2A1F3D"


def car_grid():
    """車体+タイヤ+鉢巻を1枚のドット配列にする(ゲームの描画と同じ重ね順)"""
    g = [list(r) for r in SPRITE]
    for wc in WHEEL_COLS:
        for y, row in enumerate(WHEEL):
            for x, ch in enumerate(row):
                if ch != ".":
                    g[13 + y][wc + x] = ch
    # 鉢巻: ⌐ のつるの先(4列目・1行目)から後ろへ
    for x, y in [(3, 1), (2, 1), (2, 2), (1, 2), (0, 2), (0, 3)]:
        if g[y][x] == ".":
            g[y][x] = "M"
    return g


def paint(g, grid, ox, oy, px):
    colors = dict(COLORS, M=MAGENTA)
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            col = colors.get(ch)
            if col:
                g.rectangle([ox + x * px, oy + y * px, ox + (x + 1) * px - 1, oy + (y + 1) * px - 1], fill=col)


def icon(size):
    im = Image.new("RGB", (size, size), BG)
    g = ImageDraw.Draw(im)
    grid = car_grid()
    gw, gh = len(grid[0]), len(grid)
    if size >= 64:
        bw = round(size * 7 / 180)
        g.rectangle([0, 0, size - 1, size - 1], outline=GOLD, width=bw)
        px = 5                                   # 30ドット×5 = 150px
        ox = (size - gw * px) // 2
        oy = 30                                  # 宙に浮かせる
        ground = 156
        # 影(地面に落ちる。車が浮いているほど小さく見せる)
        g.ellipse([ox + 30, ground - 5, ox + gw * px - 30, ground + 5], fill=SHADOW)
        # 跳ねた勢いの線(タイヤの下)
        for wc in WHEEL_COLS:
            cx = ox + (wc + 3) * px
            for i, w in enumerate((18, 12)):
                y = oy + gh * px + 6 + i * 7
                g.rectangle([cx - w // 2, y, cx + w // 2, y + 2], fill=GOLD)
        paint(g, grid, ox, oy, px)
    else:
        g.rectangle([0, 0, size - 1, size - 1], outline=GOLD, width=1)
        ox = (size - gw) // 2
        oy = 4
        g.rectangle([ox + 6, size - 5, ox + gw - 6, size - 4], fill=SHADOW)
        paint(g, grid, ox, oy, 1)
    return im


if __name__ == "__main__":
    for size, path in [(180, sys.argv[1]), (32, sys.argv[2])]:
        icon(size).save(ROOT / path, optimize=True)
        print("wrote", path, size)
