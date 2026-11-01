#!/usr/bin/env python3
"""우주 카드뉴스 렌더러 v1
사용: python3 render_cards.py spec.json out_dir
spec.json 형식:
{
  "series": "우주" | "미스터리" | "만약에",
  "accent": "#FFD54A",              # 포인트 색 (기본 별빛 노랑)
  "signature": "@stellawhisper42",
  "seed": 7,                         # 배경 별 배치
  "slides": [
    {"role":"cover", "kicker":"아무도 모르는 이야기", "title1":"만약 달이", "title2":"사라진다면?",
     "accent_word":"사라진다면?", "visual":"moon", "layout":"bottom"|"center"|"left"},
    {"role":"body", "tag":"01", "label":"1분 뒤", "big":"38만 km",
     "title":"밤하늘이 어두워진다", "desc":"달빛이 사라지고 별이 더 또렷해져요", "visual":"earth"},
    {"role":"end", "question":"너라면 무엇이 가장 그리울까?", "summary":"달은 생각보다 많은 걸 지키고 있어요",
     "cta":"우주 좋아하는 친구 태그하기 🔭"}   # cta 생략 시 "댓글로 알려주세요 💬"
  ]
}
visual: moon, earth, planet, ringed, sun, blackhole, nebula, galaxy, comet, stars, signal, ocean, pyramid, question
"""
import json, sys, random, html, os
from pathlib import Path
from playwright.sync_api import sync_playwright

W, H = 1080, 1350
NAVY = "#0B1430"
FONT = "'Noto Sans CJK KR','Noto Sans KR',sans-serif"


def stars(seed, n=140):
    r = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = r.uniform(0, W), r.uniform(0, H)
        s = r.choice([1, 1, 1, 1.5, 2, 2.5])
        o = r.uniform(0.35, 1)
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{s}" fill="#fff" opacity="{o:.2f}"/>')
    return f'<svg class="stars" width="{W}" height="{H}">{"".join(out)}</svg>'


def visual_svg(kind, size, accent, seed=1):
    r = random.Random(seed)
    c = size / 2
    d = {
        "moon": f'''<defs><radialGradient id="m" cx="35%" cy="35%"><stop offset="0" stop-color="#f4f1e8"/><stop offset=".7" stop-color="#b9b5aa"/><stop offset="1" stop-color="#6d6a63"/></radialGradient></defs>
            <circle cx="{c}" cy="{c}" r="{c*.8}" fill="url(#m)"/>''' + "".join(
            f'<circle cx="{c+r.uniform(-.5,.5)*c:.0f}" cy="{c+r.uniform(-.5,.5)*c:.0f}" r="{r.uniform(.04,.12)*c:.0f}" fill="#8f8b82" opacity=".55"/>' for _ in range(9)),
        "earth": f'''<defs><radialGradient id="e" cx="35%" cy="35%"><stop offset="0" stop-color="#6fc3ff"/><stop offset=".75" stop-color="#1f5fae"/><stop offset="1" stop-color="#0b2552"/></radialGradient></defs>
            <circle cx="{c}" cy="{c}" r="{c*.8}" fill="url(#e)"/>
            <path d="M{c*.55} {c*.6} q{c*.3} {-c*.2} {c*.5} {c*.1} t{c*.3} {c*.4} q{-c*.3} {c*.2} {-c*.5} {-c*.05}z" fill="#3fa36b" opacity=".85"/>
            <path d="M{c*1.1} {c*1.2} q{c*.25} {c*.05} {c*.35} {c*.3} q{-c*.2} {c*.2} {-c*.4} {-c*.05}z" fill="#3fa36b" opacity=".85"/>
            <circle cx="{c}" cy="{c}" r="{c*.84}" fill="none" stroke="#9fd8ff" stroke-width="{c*.04}" opacity=".35"/>''',
        "planet": f'''<defs><radialGradient id="p" cx="35%" cy="35%"><stop offset="0" stop-color="#ffcf9a"/><stop offset=".7" stop-color="#c8643a"/><stop offset="1" stop-color="#5a2412"/></radialGradient></defs>
            <circle cx="{c}" cy="{c}" r="{c*.75}" fill="url(#p)"/>''',
        "ringed": f'''<defs><radialGradient id="s" cx="35%" cy="35%"><stop offset="0" stop-color="#fff0c9"/><stop offset=".7" stop-color="#d1a65e"/><stop offset="1" stop-color="#6b4a1c"/></radialGradient></defs>
            <ellipse cx="{c}" cy="{c}" rx="{c*.98}" ry="{c*.26}" fill="none" stroke="#e8d3a2" stroke-width="{c*.08}" opacity=".7" transform="rotate(-18 {c} {c})"/>
            <circle cx="{c}" cy="{c}" r="{c*.55}" fill="url(#s)"/>
            <path d="M{c-c*.95} {c+c*.15} A{c*.98} {c*.26} -18 0 0 {c+c*.95} {c-c*.45}" fill="none" stroke="#e8d3a2" stroke-width="{c*.08}" opacity=".8" transform="rotate(0 {c} {c})"/>''',
        "sun": f'''<defs><radialGradient id="u"><stop offset="0" stop-color="#fffbe0"/><stop offset=".45" stop-color="#ffc53d"/><stop offset=".7" stop-color="#ff7a1a"/><stop offset="1" stop-color="#ff7a1a" stop-opacity="0"/></radialGradient></defs>
            <circle cx="{c}" cy="{c}" r="{c}" fill="url(#u)"/>''',
        "blackhole": f'''<defs><radialGradient id="b"><stop offset=".32" stop-color="#000"/><stop offset=".36" stop-color="#ffd27a"/><stop offset=".5" stop-color="#ff7b2e" stop-opacity=".8"/><stop offset=".8" stop-color="#7a1fa2" stop-opacity=".25"/><stop offset="1" stop-color="#000" stop-opacity="0"/></radialGradient></defs>
            <circle cx="{c}" cy="{c}" r="{c}" fill="url(#b)"/>
            <ellipse cx="{c}" cy="{c}" rx="{c*.95}" ry="{c*.14}" fill="none" stroke="#ffcf7a" stroke-width="{c*.05}" opacity=".75"/>
            <circle cx="{c}" cy="{c}" r="{c*.3}" fill="#000"/>''',
        "nebula": "".join(
            f'<circle cx="{c+r.uniform(-.5,.5)*c:.0f}" cy="{c+r.uniform(-.5,.5)*c:.0f}" r="{r.uniform(.3,.6)*c:.0f}" fill="{r.choice(["#c03fff","#3f8cff","#ff4f9a","#3fffd2"])}" opacity=".22" filter="url(#bl)"/>' for _ in range(9)),
        "galaxy": "".join(
            f'<ellipse cx="{c}" cy="{c}" rx="{c*(.15+i*.09)}" ry="{c*(.05+i*.03)}" fill="none" stroke="#cdb8ff" stroke-width="3" opacity="{.7-i*.07:.2f}" transform="rotate({i*14} {c} {c})"/>' for i in range(9))
            + f'<circle cx="{c}" cy="{c}" r="{c*.12}" fill="#fff6d6"/>',
        "comet": f'''<defs><linearGradient id="t" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9fe8ff" stop-opacity="0"/><stop offset="1" stop-color="#e9fbff"/></linearGradient></defs>
            <path d="M{c*.1} {c*.2} L{c*1.45} {c*1.4} L{c*1.3} {c*1.55}z" fill="url(#t)"/>
            <circle cx="{c*1.42}" cy="{c*1.5}" r="{c*.1}" fill="#fff"/>''',
        "stars": "".join(
            f'<circle cx="{r.uniform(0,size):.0f}" cy="{r.uniform(0,size):.0f}" r="{r.choice([2,3,4,6])}" fill="#fff" opacity="{r.uniform(.4,1):.2f}"/>' for _ in range(40)),
        "signal": "".join(
            f'<circle cx="{c}" cy="{c*1.6}" r="{c*(.25+i*.22)}" fill="none" stroke="{accent}" stroke-width="5" opacity="{.9-i*.15:.2f}" stroke-dasharray="{c*.8} {c*.4}" transform="rotate(200 {c} {c*1.6})"/>' for i in range(5))
            + f'<rect x="{c-6}" y="{c*1.3}" width="12" height="{c*.6}" fill="#cfd8ff"/>',
        "ocean": f'''<rect x="0" y="{c}" width="{size}" height="{c}" fill="#123b6b"/>''' + "".join(
            f'<path d="M0 {c+i*c*.18} q{size/8} -16 {size/4} 0 t{size/4} 0 t{size/4} 0 t{size/4} 0" fill="none" stroke="#5fb6ff" stroke-width="4" opacity="{.8-i*.12:.2f}"/>' for i in range(6))
            + f'<path d="M{c*.6} {c*.95} l{c*.4} {-c*.7} l{c*.4} {c*.7}z" fill="none" stroke="{accent}" stroke-width="6" stroke-dasharray="14 10"/>',
        "pyramid": f'''<path d="M{c*.2} {c*1.6} L{c} {c*.35} L{c*1.8} {c*1.6}z" fill="#c99a52"/><path d="M{c} {c*.35} L{c*1.8} {c*1.6} L{c*1.15} {c*1.6}z" fill="#8a6230"/>''',
        "question": f'<text x="{c}" y="{c*1.35}" text-anchor="middle" font-size="{c*1.3}" font-weight="900" fill="{accent}" font-family="Noto Sans CJK KR">?</text>',
    }
    body = d.get(kind, d["stars"])
    return f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}"><defs><filter id="bl"><feGaussianBlur stdDeviation="{size*.06:.0f}"/></filter></defs>{body}</svg>'


def esc(s):
    return html.escape(s or "")


def accentize(text, word, accent):
    t = esc(text)
    if word and esc(word) in t:
        t = t.replace(esc(word), f'<span style="color:{accent}">{esc(word)}</span>', 1)
    return t


CSS = f"""
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{W}px;height:{H}px;font-family:{FONT};color:#fff;overflow:hidden;position:relative;background:{NAVY};word-break:keep-all}}
.stars{{position:absolute;inset:0}}
.glow{{position:absolute;inset:0}}
.sig{{position:absolute;right:52px;bottom:44px;font-size:26px;font-weight:700;opacity:.75;letter-spacing:.5px}}
.series{{position:absolute;left:56px;top:52px;font-size:26px;font-weight:700;padding:8px 20px;border:2px solid rgba(255,255,255,.6);border-radius:40px}}
"""


def page(inner, seed, glow):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="glow" style="background:{glow}"></div>{stars(seed)}{inner}</body></html>"""


def cover(s, spec, i):
    a = spec["accent"]
    layout = s.get("layout", "bottom")
    vis = visual_svg(s.get("visual", "moon"), 900, a, spec["seed"] + i)
    t2 = accentize(s.get("title2", ""), s.get("accent_word") or s.get("title2"), a)
    t1 = accentize(s.get("title1", ""), s.get("accent_word"), a)
    if layout == "center":
        vispos = "left:90px;top:60px;opacity:.35"
        text = f'<div style="position:absolute;left:0;right:0;top:470px;text-align:center">'
    elif layout == "left":
        vispos = "left:380px;top:60px"
        text = f'<div style="position:absolute;left:64px;right:64px;bottom:200px">'
    else:
        vispos = "left:90px;top:40px"
        text = f'<div style="position:absolute;left:64px;right:64px;bottom:170px">'
    inner = f"""
<div style="position:absolute;{vispos}">{vis}</div>
<div style="position:absolute;left:0;right:0;bottom:0;height:{H*0.45:.0f}px;background:linear-gradient(to bottom,rgba(5,9,25,0),rgba(5,9,25,.92) 45%)"></div>
<div class="series">{esc(spec['series'])}</div>
{text}
  <div style="font-size:38px;font-weight:700;opacity:.85;margin-bottom:22px">{esc(s.get('kicker',''))}</div>
  <div style="font-size:104px;font-weight:900;line-height:1.18;letter-spacing:-2px">{t1}<br>{t2}</div>
</div>
<div class="sig">{esc(spec['signature'])}</div>"""
    return page(inner, spec["seed"] + i, "radial-gradient(circle at 50% 30%,#2a3a7a 0,#0B1430 60%)")


def body(s, spec, i):
    a = spec["accent"]
    series = spec["series"]
    vis = visual_svg(s.get("visual", "stars"), 560, a, spec["seed"] + i)
    tag = esc(s.get("tag", f"{i:02d}"))
    extra = ""
    if series == "미스터리":
        tagbox = f'<div style="font-size:30px;font-weight:800;padding:10px 22px;background:{a};color:#111;border-radius:6px">FILE No.{tag}</div>'
        if s.get("stamp", True):
            extra = f'<div style="position:absolute;right:120px;top:600px;transform:rotate(-14deg);border:7px solid #ff4b4b;color:#ff4b4b;font-size:56px;font-weight:900;padding:6px 26px;border-radius:10px;opacity:.9">{esc(s.get("stamp_text","미해결"))}</div>'
    else:
        tagbox = f'<div style="font-size:34px;font-weight:900;width:84px;height:84px;border-radius:50%;background:{a};color:#111;display:flex;align-items:center;justify-content:center">{tag}</div>'
    label = s.get("label")
    labelhtml = f'<div style="font-size:40px;font-weight:800;color:{a};margin-left:22px">{esc(label)}</div>' if label else ""
    big = s.get("big")
    bightml = f'<div style="position:absolute;left:0;right:0;top:250px;text-align:center;font-size:120px;font-weight:900;color:{a};text-shadow:0 6px 30px rgba(0,0,0,.6)">{esc(big)}</div>' if big else ""
    inner = f"""
<div style="position:absolute;left:64px;top:64px;display:flex;align-items:center">{tagbox}{labelhtml}</div>
<div style="position:absolute;left:100px;top:190px;width:880px;height:620px;border-radius:36px;background:rgba(255,255,255,.06);border:2px solid rgba(255,255,255,.14);overflow:hidden;display:flex;align-items:center;justify-content:center">{vis}</div>
{bightml}{extra}
<div style="position:absolute;left:72px;right:72px;top:880px">
  <div style="font-size:66px;font-weight:900;line-height:1.25;letter-spacing:-1px">{accentize(s.get('title',''), s.get('accent_word'), a)}</div>
  <div style="font-size:38px;font-weight:500;line-height:1.5;opacity:.85;margin-top:26px">{esc(s.get('desc',''))}</div>
</div>
<div class="sig">{esc(spec['signature'])}</div>"""
    return page(inner, spec["seed"] + i, f"linear-gradient(180deg,#0E1A40,{NAVY})")


def end(s, spec, i):
    a = spec["accent"]
    inner = f"""
<div style="position:absolute;left:0;right:0;top:330px;text-align:center">{visual_svg('question',260,a)}</div>
<div style="position:absolute;left:80px;right:80px;top:640px;text-align:center">
  <div style="font-size:76px;font-weight:900;line-height:1.3;letter-spacing:-1px">{accentize(s.get('question',''), s.get('accent_word'), a)}</div>
  <div style="font-size:38px;font-weight:500;opacity:.85;margin-top:40px;line-height:1.5">{esc(s.get('summary',''))}</div>
  <div style="font-size:34px;font-weight:700;margin-top:60px;color:{a}">{esc(s.get('cta','댓글로 알려주세요 💬'))}</div>
</div>
<div class="sig">{esc(spec['signature'])}</div>"""
    return page(inner, spec["seed"] + i, "radial-gradient(circle at 50% 40%,#23306b 0,#0B1430 65%)")


def main(spec_path, out_dir):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    spec.setdefault("accent", "#FFD54A")
    spec.setdefault("signature", "@stellawhisper42")
    spec.setdefault("seed", 7)
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    fn = {"cover": cover, "body": body, "end": end}
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        for i, s in enumerate(spec["slides"], 1):
            pg.set_content(fn[s["role"]](s, spec, i), wait_until="load")
            pg.wait_for_timeout(150)
            f = out / f"{i:02d}.png"
            pg.screenshot(path=str(f), type="png")
            paths.append(str(f))
        b.close()
    print("\n".join(paths))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
