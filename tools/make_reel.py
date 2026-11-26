#!/usr/bin/env python3
"""카드 폴더(01.jpg…)를 인스타 릴스용 세로 영상 reel.mp4 로 만든다.
사용: python3 tools/make_reel.py cards/<폴더> [초/장=3.0]
- 1080×1920(9:16), 30fps, H.264 + 무음 AAC(업로드 호환용)
- 카드(4:5)는 90%로 줄여 위쪽에 배치 → 아래 릴스 UI(캡션·버튼)에 서명·크레딧이 가리지 않음
- 배경은 같은 카드를 흐리고 어둡게 채움, 장 사이 0.4초 페이드
- 표지(01)는 0.5초 더 길게. 릴스 표지 이미지는 cover.jpg(1080×1920)로 함께 저장
"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

W, H = 1080, 1920
SCALE = 0.9
TOP = 250          # 위 여백(상단 UI 피함)
FADE = 0.4


def frame(card_path, out_path):
    card = Image.open(card_path).convert("RGB")
    bg = card.resize((W, int(card.height * W / card.width * 1.45)))
    bg = bg.crop((0, (bg.height - H) // 2, W, (bg.height - H) // 2 + H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(40))).enhance(0.35)
    cw, ch = int(card.width * SCALE), int(card.height * SCALE)
    bg.paste(card.resize((cw, ch), Image.LANCZOS), ((W - cw) // 2, TOP))
    bg.save(out_path, "JPEG", quality=94)


def main(folder, per=3.0):
    d = Path(folder)
    cards = sorted(p for p in d.glob("[0-9][0-9].jpg"))
    if not cards:
        sys.exit(f"no cards in {d}")
    tmp = Path(tempfile.mkdtemp())
    frames = []
    for c in cards:
        f = tmp / c.name
        frame(c, f)
        frames.append(f)
    frame(cards[0], d / "cover.jpg")
    durs = [per + 0.5] + [per] * (len(frames) - 1)
    args = []
    for f, t in zip(frames, durs):
        args += ["-loop", "1", "-t", f"{t + FADE:.2f}", "-i", str(f)]
    n = len(frames)
    args += ["-f", "lavfi", "-t", f"{sum(durs) + FADE:.2f}", "-i", "anullsrc=r=44100:cl=stereo"]
    chain, prev, off = [], "[0:v]", 0.0
    for i in range(1, n):
        off += durs[i - 1]
        out = f"[v{i}]"
        chain.append(f"{prev}[{i}:v]xfade=transition=fade:duration={FADE}:offset={off:.2f}{out}")
        prev = out
    chain.append(f"{prev}format=yuv420p,fps=30[vout]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *args, "-filter_complex", ";".join(chain),
           "-map", "[vout]", "-map", f"{n}:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "96k", "-shortest", "-movflags", "+faststart", str(d / "reel.mp4")]
    subprocess.run(cmd, check=True)
    print(d / "reel.mp4")


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 3.0)
