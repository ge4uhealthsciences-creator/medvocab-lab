#!/usr/bin/env python3
"""Store TikTok views read from TikTok Studio so the Hub can show them.

TikTok gives this account no API, so the autopilot opens https://www.tiktok.com/tiktokstudio/content,
saves the page text (get_page_text) to a file and runs:

    python3 scripts/tiktok_views.py page.txt            # parse + upload to status/tiktok-views.json
    python3 scripts/tiktok_views.py page.txt --dry-run  # only print

Each post on that page reads: "<emoji> <term> /<ipa>/ = ..." caption, a date line, the privacy
("Everyone" / "Mọi người"), then views, likes, comments. The result is
{"updated": "<VN time>", "views": {"<term>": views}, "likes": {...}, "comments": {...}};
social-post/post.py puts the views into the Hub's status table.
"""
import base64, datetime as dt, json, re, subprocess, sys, tempfile

REPO = "ge4uhealthsciences-creator/medvocab-lab"
BRANCH = "status"
PATH = "status/tiktok-views.json"
VN = dt.timezone(dt.timedelta(hours=7))
PRIVACY = {"everyone", "mọi người", "friends", "bạn bè", "only you", "chỉ mình bạn", "followers", "người theo dõi"}


def num(s):
    s = s.strip().replace(",", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([KkMm]?)", s)
    if not m:
        return None
    v = float(m.group(1)) * {"": 1, "k": 1e3, "m": 1e6}[m.group(2).lower()]
    return int(round(v))


def parse(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out = {"views": {}, "likes": {}, "comments": {}}
    for i, l in enumerate(lines):
        m = re.match(r"^\W*\s*([A-Za-z][A-Za-z \-']*?)\s+/[^/]+/\s*=", l)
        if not m:
            continue
        term = m.group(1).strip().lower()
        # find the privacy line within the next few lines, then three numbers
        for j in range(i + 1, min(i + 6, len(lines))):
            if lines[j].lower() in PRIVACY:
                nums = [num(x) for x in lines[j + 1:j + 4]]
                if len(nums) == 3 and all(n is not None for n in nums) and term not in out["views"]:
                    out["views"][term], out["likes"][term], out["comments"][term] = nums
                break
    return out


def gh(*a, check=True):
    return subprocess.run(["gh", *a], check=check, capture_output=True, text=True)


def upload(data):
    r = gh("api", f"repos/{REPO}/contents/{PATH}?ref={BRANCH}", check=False)
    sha = json.loads(r.stdout).get("sha") if r.returncode == 0 else None
    old = {}
    if sha:
        try:
            old = json.loads(base64.b64decode(json.loads(r.stdout)["content"]).decode())
        except Exception:
            old = {}
    for k in ("views", "likes", "comments"):  # keep terms not on today's first page
        merged = dict(old.get(k) or {}); merged.update(data[k]); data[k] = merged
    body = {"message": f"TikTok views {data['updated']}", "branch": BRANCH,
            "content": base64.b64encode(json.dumps(data, ensure_ascii=False, indent=1).encode()).decode()}
    if sha:
        body["sha"] = sha
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(body, f); f.close()
    gh("api", "-X", "PUT", f"repos/{REPO}/contents/{PATH}", "--input", f.name)


if __name__ == "__main__":
    text = open(sys.argv[1], encoding="utf-8").read()
    data = parse(text)
    data["updated"] = dt.datetime.now(VN).strftime("%Y-%m-%d %H:%M")
    print(json.dumps(data, ensure_ascii=False))
    if not data["views"]:
        sys.exit("No posts found in the page text (is it the TikTok Studio Posts page?)")
    if "--dry-run" not in sys.argv:
        upload(data)
        print("uploaded", len(data["views"]), "posts")
