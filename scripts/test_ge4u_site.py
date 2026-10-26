#!/usr/bin/env python3
"""Fast regression checks for the public GE4u learning pages."""
from pathlib import Path
import json
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
required = [
    "ge4u-health-sciences.html",
    "ge4u-case-practice.html",
    "ge4u-case-deep-practice.html",
    "ge4u-channel.html",
    "ge4u-dental-english.html",
    "data/ge4u-channel-samples.json",
]
missing = [p for p in required if not (ROOT / p).is_file()]
if missing:
    raise SystemExit("FAIL: missing required files: " + ", ".join(missing))

hub = (ROOT / "ge4u-health-sciences.html").read_text(encoding="utf-8")
deep = (ROOT / "ge4u-case-deep-practice.html").read_text(encoding="utf-8")
case_script_match = re.search(r"<script>(.*?)</script>", deep, re.S)
if not case_script_match:
    raise SystemExit("FAIL: deep practice page has no inline script")
js = case_script_match.group(1)

expected = [
    "dentistry", "medical", "pharmacy", "nursing", "midwifery",
    "social-work", "pharmaceutical-chemistry", "pharmaceutical-technology",
    "traditional-medicine", "public-health", "psychology", "nutrition",
]
found = re.findall(r'^"([^"]+)":\{name:', js, re.M)
if found != expected:
    raise SystemExit(f"FAIL: case IDs differ. Found {found}")
for channel in expected:
    start = js.find(f'"{channel}":{{name:')
    next_start = js.find('\n"', start + 2)
    chunk = js[start: next_start if next_start != -1 else len(js)]
    if len(re.findall(r'\{speaker:', chunk)) != 3:
        raise SystemExit(f"FAIL: {channel} should contain exactly 3 turns")

if "ge4u-case-deep-practice.html" not in hub:
    raise SystemExit("FAIL: hub does not link to deep practice page")
if "window.print()" not in js:
    raise SystemExit("FAIL: print/PDF action not found")
if "function finish()" not in js or "function choose(" not in js:
    raise SystemExit("FAIL: core case interaction functions missing")

try:
    with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8") as f:
        f.write(js)
        f.flush()
        subprocess.run(["node", "--check", f.name], check=True, capture_output=True, text=True)
except FileNotFoundError:
    raise SystemExit("FAIL: Node.js unavailable; cannot validate JavaScript syntax")
except subprocess.CalledProcessError as exc:
    raise SystemExit("FAIL: JavaScript syntax error:\n" + exc.stderr)

with (ROOT / "data/ge4u-channel-samples.json").open(encoding="utf-8") as f:
    data = json.load(f)
channels = data.get("channels", [])
if len(channels) != 11:
    raise SystemExit(f"FAIL: expected 11 non-dental channel samples, found {len(channels)}")
if len({c.get("id") for c in channels}) != len(channels):
    raise SystemExit("FAIL: duplicate channel IDs in sample data")

expected_sample_ids = {
    "medical", "pharmacy", "nursing", "midwifery", "social-work",
    "pharmaceutical-chemistry", "pharmaceutical-technology",
    "traditional-medicine", "public-health", "psychology", "nutrition",
}
if {c.get("id") for c in channels} != expected_sample_ids:
    raise SystemExit("FAIL: the 11 non-dental sample channels do not match the expected 12-discipline architecture")
for channel in channels:
    if len(channel.get("terms", [])) < 3:
        raise SystemExit(f"FAIL: {channel.get('id')} needs at least 3 terms")
    quiz = channel.get("quiz", [])
    if len(quiz) != 5:
        raise SystemExit(f"FAIL: {channel.get('id')} should have 5 channel-specific quiz items")
    for item in quiz:
        if len(item.get("opts", [])) != 3 or item.get("a") not in item.get("opts", []):
            raise SystemExit(f"FAIL: invalid quiz answer/options for {channel.get('id')}")
        if "reason for using a medicine" in item.get("q", "").lower() and channel.get("id") != "pharmacy":
            raise SystemExit(f"FAIL: generic pharmacy quiz leaked into {channel.get('id')}")

dental_path = ROOT / "data/dental-english-pack.json"
with dental_path.open(encoding="utf-8") as f:
    dental = json.load(f)
if not dental.get("topics") or not dental.get("quiz"):
    raise SystemExit("FAIL: dental source data is missing topics or quiz items")

daily_path = ROOT / "data/daily-lesson.json"
if not daily_path.is_file():
    raise SystemExit("FAIL: daily lesson was not generated")
with daily_path.open(encoding="utf-8") as f:
    daily = json.load(f)
if daily.get("channel_id") not in {"dentistry"} | expected_sample_ids:
    raise SystemExit(f"FAIL: daily lesson has unknown channel_id: {daily.get('channel_id')}")
if len(daily.get("vocabulary", [])) != 3:
    raise SystemExit("FAIL: daily lesson must contain exactly 3 vocabulary items")
if len(daily.get("quiz", {}).get("options", [])) != 3 or daily.get("quiz", {}).get("answer") not in daily.get("quiz", {}).get("options", []):
    raise SystemExit("FAIL: daily lesson quiz is invalid")

print("PASS: required public pages and data files exist")
print("PASS: 12 case scenarios each contain 3 turns")
print("PASS: deep-practice JavaScript syntax and core interactions")
print("PASS: hub links to deep practice and print/PDF action exists")
print("PASS: 11 channel sample datasets and quizzes are valid")
print("PASS: daily lesson is generated from one of all 12 disciplines")
