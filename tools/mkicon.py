"""咲耶ジャンプバグのアイコン(apple-touch-icon 180px / favicon 32px)を作る。

    python3 tools/mkicon.py apple-touch-icon.png favicon-32.png

咲耶スクランブル(ピンクの三角形)と同じく、形だけで見せるシンプルなアイコンにする。
  - 暗い四角 + 金の枠
  - 中身は1つのシルエットを、マゼンタで塗りつぶし・金で縁取り・マゼンタの淡い光
使う色は咲耶スクランブルのアイコンと同じ3色(地・金・マゼンタ)だけ。

形は「跳ね上がる⌐◨-◨カー」。屋根に ⌐◨-◨ を乗せた🚙型の車が機首を上げて跳び、
後ろに金の点で跳ねた軌跡を描く。横向きの車を水平に置いただけでは咲耶Nounラリー
(ピンクのセダン)と見分けがつかなかったので、「跳ねている」ことで区別する。
  - ◨ の黒い半分(瞳)は地の色で抜き、1色でもメガネに見えるようにする
  - タイヤは車体からすき間で切り離し、車だと一目で分かるようにする
形は180px基準の座標で書き、8倍で描いてから縮める(32pxも同じ形を縮めて作る)。
"""
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent

BG = (0x06, 0x07, 0x0C)       # 地(咲耶スクランブルと同じ)
GOLD = (0xE8, 0xC5, 0x6A)     # 金: 枠と縁取り
FILL = (0xFF, 0x2D, 0x9B)     # マゼンタ: 塗りつぶし
SS = 8                        # スーパーサンプリング


TILT = math.radians(-20)      # 機首上げの角度
PIVOT = (100, 84)             # 回転の中心(180px基準)
OFFSET = (-6, 8)              # 傾けたあとに枠の中央へ寄せる量


def rot(pts):
    c, s_ = math.cos(TILT), math.sin(TILT)
    cx, cy = PIVOT
    ox, oy = OFFSET
    return [(cx + (x - cx) * c - (y - cy) * s_ + ox, cy + (x - cx) * s_ + (y - cy) * c + oy) for x, y in pts]


def silhouette(S):
    """塗り(形)・抜き(◨の瞳)・金の点(軌跡)の3枚のマスクを返す。座標は180px基準。
    瞳を形の一部として抜くと縁取りの金が穴に回り込み細いすき間にしか見えないので、
    縁取りを描いたあとで地の色を上から置いて抜く"""
    u = S / 180
    m = Image.new("L", (S, S), 0)
    holes = Image.new("L", (S, S), 0)
    dots = Image.new("L", (S, S), 0)
    d, h, g = ImageDraw.Draw(m), ImageDraw.Draw(holes), ImageDraw.Draw(dots)
    poly = lambda draw, pts, v=255: draw.polygon([(x * u, y * u) for x, y in rot(pts)], fill=v)
    box = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    # 車体(横から見た箱形。右が前)
    poly(d, [(50, 102), (50, 76), (59, 64), (118, 64), (133, 79), (153, 82), (158, 92), (158, 102)])
    # ⌐◨-◨ を屋根から少し浮かせて乗せる
    poly(d, box(68, 38, 92, 60))          # ◨
    poly(d, box(100, 38, 124, 60))        # ◨
    poly(d, box(92, 45, 100, 52))         # -
    poly(d, box(52, 42, 68, 49))          # ⌐ のつる
    poly(d, box(52, 42, 59, 56))          # ⌐ の折れ
    poly(h, box(80, 44, 87, 55))          # 瞳
    poly(h, box(112, 44, 119, 55))
    # タイヤ: 車体を丸くくり抜いてから、ひとまわり小さいタイヤを置く
    wheels = rot([(74, 103), (136, 103)])
    for x, y in wheels:
        d.ellipse([(x - 18) * u, (y - 18) * u, (x + 18) * u, (y + 18) * u], fill=0)
    for x, y in wheels:
        d.ellipse([(x - 13) * u, (y - 13) * u, (x + 13) * u, (y + 13) * u], fill=255)

    # 跳ねた軌跡: 地面から後ろのタイヤへ向かう点の列と、踏み切った地面
    for i in range(4):
        t = i / 4
        x = 24 + t * 40
        y = 152 - math.sin(t * math.pi * 0.55) * 40
        r = 3.6 + t * 1.2
        g.ellipse([(x - r) * u, (y - r) * u, (x + r) * u, (y + r) * u], fill=255)
    g.rectangle([14 * u, 155 * u, 58 * u, 159 * u], fill=255)
    return m, holes, dots


def icon(size):
    S = size * SS
    u = S / 180
    im = Image.new("RGB", (S, S), BG)

    mask, holes, dots = silhouette(S)
    # 形を r px 太らせる(膨張)。BoxBlur で近くに白がある画素を拾い、しきい値で2値に戻す
    grow = lambda r: mask.filter(ImageFilter.BoxBlur(max(1, round(r * u)))).point(lambda v: 255 if v > 6 else 0)
    outline = grow(3)                                  # 金の縁取りの太さ(180px基準で約3px)
    glow = grow(5).filter(ImageFilter.GaussianBlur(9 * u))

    im.paste(Image.new("RGB", (S, S), FILL), (0, 0), glow.point(lambda v: v * 0.45))
    im.paste(Image.new("RGB", (S, S), GOLD), (0, 0), outline)
    im.paste(Image.new("RGB", (S, S), FILL), (0, 0), mask)
    im.paste(Image.new("RGB", (S, S), BG), (0, 0), holes)
    im.paste(Image.new("RGB", (S, S), GOLD), (0, 0), dots)

    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, S - 1], outline=GOLD, width=round(7 * u))
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    for size, path in [(180, sys.argv[1]), (32, sys.argv[2])]:
        icon(size).save(ROOT / path, optimize=True)
        print("wrote", path, size)
