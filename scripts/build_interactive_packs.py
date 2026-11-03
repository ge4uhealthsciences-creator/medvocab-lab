#!/usr/bin/env python3
"""Build GE4u interactive learning packs as self-contained offline HTML files.

- Topic packs (data/packs/<id>.json, listed in data/packs/curriculum.json, ~100 terms in groups)
- Starter packs for disciplines that have no topic packs yet (merged vocabulary bank)
Every pack also gets the shared word-parts section (data/word-parts.json).

  python3 scripts/build_interactive_packs.py --out dist/interactive [--only medical-anatomy]
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "social-video"))
import ge4u_video as gv

TEMPLATE = (ROOT / "scripts" / "pack_template.html").read_text(encoding="utf-8")
PARTS = json.loads((ROOT / "data" / "word-parts.json").read_text(encoding="utf-8"))["parts"]
FIELDS = ("term", "ipa", "meaning", "definition", "example")


def validate(pid, terms):
    seen = set()
    for t in terms:
        missing = [f for f in FIELDS if not str(t.get(f, "")).strip()]
        if missing:
            raise ValueError(f"{pid}: {t.get('term')} missing {missing}")
        if not (t["ipa"].startswith("/") and t["ipa"].endswith("/")):
            raise ValueError(f"{pid}: bad IPA for {t['term']}")
        k = t["term"].lower()
        if k in seen:
            raise ValueError(f"{pid}: duplicate term {t['term']}")
        seen.add(k)


def render(pid, title, sub, terms, groups, out):
    validate(pid, terms)
    data = {"id": pid, "terms": terms, "groups": groups, "parts": PARTS}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = TEMPLATE.replace("__TITLE__", title).replace("__SUB__", sub).replace("__DATA__", payload)
    f = out / f"GE4u-{pid}.html"
    f.write_text(html, encoding="utf-8")
    print(f"{f.name}: {len(terms)} terms, {len(groups)} topics, {f.stat().st_size // 1024} KB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist/interactive")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cur = json.loads((ROOT / "data" / "packs" / "curriculum.json").read_text(encoding="utf-8"))
    with_topics = set()
    for d in cur["disciplines"]:
        for lvl in d["levels"]:
            for p in lvl["packs"]:
                if p["status"] != "ready" or (a.only and a.only != p["id"]):
                    continue
                with_topics.add(d["id"])
                src = json.loads((ROOT / "data" / "packs" / f"{p['id']}.json").read_text(encoding="utf-8"))
                terms, groups = [], []
                for gi, g in enumerate(src["groups"]):
                    groups.append({"vi": g["vi"], "en": g["en"]})
                    terms += [dict(zip(FIELDS, row), g=gi) for row in g["terms"]]
                render(p["id"], f"{src['en']} Learning Pack", f"{src['vi']} · {lvl['vi']}", terms, groups, out)
    if a.only:
        return
    bank = gv.load_bank()
    for cid in gv.ORDER:
        if cid in with_topics:
            continue
        vi, en, _, _ = gv.LABEL[cid]
        render(f"{cid}-starter", f"{en} Starter Pack", f"{vi} · Bộ khởi động", [dict(t, g=0) for t in bank[cid]], [], out)


if __name__ == "__main__":
    main()
