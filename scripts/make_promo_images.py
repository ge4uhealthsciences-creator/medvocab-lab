#!/usr/bin/env python3
"""Render GE4u promo images (1080x1350, 4:5 for Facebook feed) from marketing/promo-images.json.

Usage: python3 scripts/make_promo_images.py [--only ID] [--out marketing/promo-images]
Each spec: id, theme (a discipline key from social-video COLOR), kicker, headline,
optional card {title?, lines[]}, bullets[], chips[], steps[], cta.
"""
import argparse, json, pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
W, H = 1080, 1350
THEMES = {
    "medical": ("#5b0b1e", "#22060c", "#ff7a8a"), "dentistry": ("#0b3a5b", "#06182a", "#5ee0ff"),
    "pharmacy": ("#2b0b5b", "#10062a", "#b98cff"), "nursing": ("#0b5b48", "#062a21", "#5effc5"),
    "public-health": ("#0b225b", "#060f2a", "#7aa8ff"), "traditional-medicine": ("#2f5b0b", "#152a06", "#c5ff5e"),
    "social-work": ("#5b3a0b", "#2a1a06", "#ffc35e"), "psychology": ("#4a0b5b", "#20062a", "#e08aff"),
    "nutrition": ("#5b4a0b", "#2a2206", "#ffe35e"), "brand": ("#0f2f4f", "#071526", "#5ee0ff"),
}
FD = "/usr/share/fonts/opentype/inter/"


def font(weight, size):
    name = {"black": "Inter-Black.otf", "bold": "Inter-Bold.otf", "semi": "Inter-SemiBold.otf", "med": "Inter-Medium.otf", "reg": "Inter-Regular.otf"}[weight]
    for p in (FD + name, "/usr/share/fonts/truetype/inter/" + name.replace(".otf", ".ttf")):
        if pathlib.Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if weight in ("black", "bold", "semi") else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)


def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def render(spec, out):
    top, bot, acc = (hexrgb(c) for c in THEMES[spec.get("theme", "brand")])
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        for x in range(W): px[x, y] = c
    d = ImageDraw.Draw(img, "RGBA")
    # soft decorative circles
    d.ellipse((W - 420, -180, W + 180, 420), fill=acc + (34,))
    d.ellipse((-220, H - 380, 260, H + 100), fill=acc + (22,))
    M = 84
    # brand row
    d.rounded_rectangle((M, 78, M + 150, 138), 14, fill=acc + (255,))
    d.text((M + 75, 108), "GE4u", font=font("black", 34), fill=bot, anchor="mm")
    d.text((M + 172, 108), spec.get("kicker", "Medical English"), font=font("semi", 30), fill=(255, 255, 255, 215), anchor="lm")
    ipa = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)

    def body(y, draw):
        hf = font("black", spec.get("headline_size", 80))
        for ln in wrap(d, spec["headline"], hf, W - 2 * M):
            if draw: d.text((M, y), ln, font=hf, fill=(255, 255, 255))
            y += int(hf.size * 1.14)
        y += 36
        card = spec.get("card")
        if card:
            lines = card["lines"]
            tf, lf = font("bold", 64), font("semi", 44)
            ch = 60 + (88 if card.get("title") else 0) + 70 * len(lines) + 16
            if draw:
                d.rounded_rectangle((M, y, W - M, y + ch), 34, fill=(255, 255, 255, 240))
                d.rounded_rectangle((M, y, M + 16, y + ch), 8, fill=acc + (255,))
            cy = y + 42
            if card.get("title"):
                if draw: d.text((M + 52, cy), card["title"], font=tf, fill=bot)
                cy += 88
            for ln in lines:
                hl = ln.startswith("!"); t = ln.lstrip("!")
                f = ipa if t.startswith("/") else (font("bold", 44) if hl else lf)
                if draw: d.text((M + 52, cy), t, font=f, fill=(200, 30, 60) if hl else (40, 48, 60))
                cy += 70
            y += ch + 44
        chips = spec.get("chips", [])
        if chips:
            cf, cx = font("semi", 38), M
            for c in chips:
                w = d.textlength(c, font=cf) + 52
                if cx + w > W - M: cx = M; y += 82
                if draw:
                    d.rounded_rectangle((cx, y, cx + w, y + 64), 32, outline=acc + (255,), width=3, fill=acc + (40,))
                    d.text((cx + w / 2, y + 32), c, font=cf, fill=(255, 255, 255), anchor="mm")
                cx += w + 14
            y += 108
        for i, st in enumerate(spec.get("steps", []), 1):
            if draw:
                d.ellipse((M, y, M + 68, y + 68), fill=acc + (255,))
                d.text((M + 34, y + 34), str(i), font=font("black", 36), fill=bot, anchor="mm")
                d.text((M + 94, y + 34), st, font=font("semi", 44), fill=(255, 255, 255), anchor="lm")
            y += 92
        if spec.get("steps"): y += 16
        bf = font("semi", 44)
        for b in spec.get("bullets", []):
            if draw: d.ellipse((M, y + 16, M + 24, y + 40), fill=acc + (255,))
            for ln in wrap(d, b, bf, W - 2 * M - 50):
                if draw: d.text((M + 50, y), ln, font=bf, fill=(255, 255, 255, 235))
                y += 58
            y += 14
        return y

    top_y, bottom_y = 190, H - 230
    h = body(0, False)
    body(top_y + max(0, (bottom_y - top_y - h) // 2), True)
    # footer price + cta
    fy = H - 200
    d.rounded_rectangle((M, fy, M + 360, fy + 104), 52, fill=acc + (255,))
    d.text((M + 180, fy + 52), "99.000đ/bộ", font=font("black", 46), fill=bot, anchor="mm")
    d.text((M + 392, fy + 34), spec.get("cta", "Học tương tác trên điện thoại"), font=font("semi", 32), fill=(255, 255, 255), anchor="lm")
    d.text((M + 392, fy + 76), "Link đặt mua trong bài viết", font=font("reg", 30), fill=(255, 255, 255, 190), anchor="lm")
    img.save(out, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(ROOT / "marketing" / "promo-images.json"))
    ap.add_argument("--out", default=str(ROOT / "marketing" / "promo-images"))
    ap.add_argument("--only")
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for s in json.loads(pathlib.Path(a.spec).read_text())["images"]:
        if a.only and s["id"] != a.only: continue
        render(s, out / f"{s['id']}.png"); print(out / f"{s['id']}.png")


if __name__ == "__main__":
    main()
