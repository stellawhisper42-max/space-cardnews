#!/usr/bin/env python3
"""cards/render_queue.txt 에 적힌 폴더를 렌더 → 01.jpg… (JPEG q92), PNG 삭제.
사진(photo)이 아직 assets/img 에 없으면 그 폴더는 건너뛰고 큐에 남긴다."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image
q = Path("cards/render_queue.txt")
if not q.exists():
    sys.exit(0)
left = []
for name in [l.strip() for l in q.read_text().splitlines() if l.strip() and not l.startswith("#")]:
    d = Path("cards") / name
    spec = json.loads((d / "spec.json").read_text(encoding="utf-8"))
    missing = [s["photo"] for s in spec["slides"] if s.get("photo") and not Path(s["photo"]).exists()]
    if missing:
        print("SKIP", name, "missing:", missing); left.append(name); continue
    for old in list(d.glob("*.jpg")) + list(d.glob("*.png")):
        old.unlink()
    out = subprocess.run([sys.executable, "render_cards.py", str(d / "spec.json"), str(d)],
                         check=True, capture_output=True, text=True).stdout.split()
    for i, p in enumerate(sorted(out), 1):
        Image.open(p).convert("RGB").save(d / f"{i:02d}.jpg", "JPEG", quality=92)
        if not p.endswith(f"{i:02d}.jpg"):
            Path(p).unlink(missing_ok=True)
    print("RENDERED", name)
q.write_text("".join(f"{n}\n" for n in left))
