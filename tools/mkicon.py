"""咲耶ジャンプバグのアイコン(apple-touch-icon 180px / favicon 32px)を作る。

    python3 tools/mkicon.py apple-touch-icon.png favicon-32.png

咲耶スクランブル(ピンクの三角形)と同じく、形だけで見せるシンプルなアイコンにする。
  - 暗い四角 + 金の枠
  - 中身は1つのシルエットを、マゼンタで塗りつぶし・金で縁取り・マゼンタの淡い光
使う色は咲耶スクランブルのアイコンと同じ3色(地・金・マゼンタ)だけ。

シルエットは 🚙 型の箱形の車の屋根に ⌐◨-◨ が乗った形。
  - ◨ の黒い半分(瞳)は地の色で抜き、1色でもメガネに見えるようにする
  - タイヤは車体からすき間(くり抜き)で切り離し、車だと一目で分かるようにする
形は180px基準の座標で書き、8倍で描いてから縮める(32pxも同じ形を縮めて作る)。
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent

BG = (0x06, 0x07, 0x0C)       # 地(咲耶スクランブルと同じ)
GOLD = (0xE8, 0xC5, 0x6A)     # 金: 枠と縁取り
FILL = (0xFF, 0x2D, 0x9B)     # マゼンタ: 塗りつぶし
SS = 8                        # スーパーサンプリング


def silhouette(S):
    """塗りつぶす形(白)のマスクと、あとから地の色で抜く穴(◨の瞳)のマスクを返す。
    瞳を形の一部として抜くと、縁取りの金が穴の中まで回り込んで細いすき間にしか
    見えなかったので、縁取りを描いたあとで地の色を上から置いて抜く。座標は180px基準"""
    u = S / 180
    P = lambda pts: [(x * u, y * u) for x, y in pts]
    R = lambda x0, y0, x1, y1: [x0 * u, y0 * u, x1 * u, y1 * u]
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    # 車体(横から見た箱形。右が前)
    d.polygon(P([(26, 124), (26, 90), (36, 76), (110, 76), (128, 94), (152, 98), (158, 108), (158, 124)]), fill=255)
    # ⌐◨-◨ は屋根から少し浮かせて、かけているメガネとして1つの形に見せる
    d.rectangle(R(50, 42, 76, 68), fill=255)      # ◨
    d.rectangle(R(86, 42, 112, 68), fill=255)     # ◨
    d.rectangle(R(76, 51, 86, 58), fill=255)      # -
    d.rectangle(R(30, 47, 50, 54), fill=255)      # ⌐ のつる
    d.rectangle(R(30, 47, 37, 62), fill=255)      # ⌐ の折れ
    # タイヤ: 車体を丸くくり抜いてから、ひとまわり小さいタイヤを置く
    for cx in (58, 128):
        d.ellipse(R(cx - 20, 124 - 20, cx + 20, 124 + 20), fill=0)
    d.rectangle(R(0, 138, 180, 180), fill=0)
    for cx in (58, 128):
        d.ellipse(R(cx - 14, 124 - 14, cx + 14, 124 + 14), fill=255)
    holes = Image.new("L", (S, S), 0)
    h = ImageDraw.Draw(holes)
    # ◨ の黒い半分(瞳)。レンズの内側の右半分
    h.rectangle(R(63, 48, 71, 62), fill=255)
    h.rectangle(R(99, 48, 107, 62), fill=255)
    return m, holes


def icon(size):
    S = size * SS
    u = S / 180
    im = Image.new("RGB", (S, S), BG)

    mask, holes = silhouette(S)
    # 形を r px 太らせる(膨張)。BoxBlur で近くに白がある画素を拾い、しきい値で2値に戻す
    grow = lambda r: mask.filter(ImageFilter.BoxBlur(max(1, round(r * u)))).point(lambda v: 255 if v > 6 else 0)
    outline = grow(3)                                  # 金の縁取りの太さ(180px基準で約3px)
    glow = grow(5).filter(ImageFilter.GaussianBlur(9 * u))

    im.paste(Image.new("RGB", (S, S), FILL), (0, 0), glow.point(lambda v: v * 0.45))
    im.paste(Image.new("RGB", (S, S), GOLD), (0, 0), outline)
    im.paste(Image.new("RGB", (S, S), FILL), (0, 0), mask)
    im.paste(Image.new("RGB", (S, S), BG), (0, 0), holes)

    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, S - 1, S - 1], outline=GOLD, width=round(7 * u))
    return im.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    for size, path in [(180, sys.argv[1]), (32, sys.argv[2])]:
        icon(size).save(ROOT / path, optimize=True)
        print("wrote", path, size)
