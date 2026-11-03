#!/usr/bin/env python3
"""Build the 12 interactive GE4u Learning Packs as self-contained offline HTML files.

Each pack: flashcards with spoken pronunciation (browser speech), drag-and-drop matching,
scored multiple choice, gap fill, searchable word list and saved progress.

  python3 scripts/build_interactive_packs.py --out dist/interactive
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "social-video"))
import ge4u_video as gv

TEMPLATE = (ROOT / "scripts" / "pack_template.html").read_text(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist/interactive")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    bank = gv.load_bank()
    for cid in gv.ORDER:
        vi, en, _, _ = gv.LABEL[cid]
        data = {"id": cid, "terms": bank[cid]}
        payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        html = (TEMPLATE.replace("__TITLE__", f"{en} Learning Pack")
                .replace("__SUB__", f"{vi} · Tiếng Anh chuyên ngành")
                .replace("__DATA__", payload))
        f = out / f"GE4u-{cid}-interactive-pack.html"
        f.write_text(html, encoding="utf-8")
        print(f.name, len(bank[cid]), "terms", f.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
