#!/usr/bin/env python3
"""Create a deterministic daily micro-lesson rotating across all 12 GE4u disciplines."""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANNELS_PATH = ROOT / "data" / "ge4u-channel-samples.json"
DENTAL_PATH = ROOT / "data" / "dental-english-pack.json"
OUT_PATH = ROOT / "data" / "daily-lesson.json"

# GitHub Actions runs at 23:00 UTC, which is 06:00 in Vietnam (UTC+7).
TODAY = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).date()
ORDER = [
    "dentistry", "medical", "pharmacy", "nursing", "midwifery", "social-work",
    "pharmaceutical-chemistry", "pharmaceutical-technology", "traditional-medicine",
    "public-health", "psychology", "nutrition",
]

def load_channels():
    sample_data = json.loads(CHANNELS_PATH.read_text(encoding="utf-8"))
    channels = {item["id"]: item for item in sample_data["channels"]}
    dental = json.loads(DENTAL_PATH.read_text(encoding="utf-8"))
    dental_words = []
    for topic in dental.get("topics", []):
        dental_words.extend(topic.get("words", []))
    dental_channel = {
        "id": "dentistry",
        "vi": "Răng Hàm Mặt",
        "name": "Dental English",
        "desc": "Dental vocabulary, examination, instruments and patient communication.",
        "terms": [[w["term"], w.get("ipa", ""), w["meaning"], w["definition"], w["example"]]
                  for w in dental_words],
        "quiz": [
            {"q": q["q"], "opts": q["options"], "a": q["answer"], "why": q["explanation"]}
            for q in dental.get("quiz", [])
        ],
    }
    channels["dentistry"] = dental_channel
    return channels

def build():
    channels = load_channels()
    missing = sorted(set(ORDER) - set(channels))
    if missing:
        raise ValueError(f"Missing channel data: {missing}")
    # Use day number for a stable daily rotation; each 12-day cycle covers all disciplines.
    channel_id = ORDER[(TODAY.toordinal() - 1) % len(ORDER)]
    channel = channels[channel_id]
    terms = channel.get("terms", [])
    quiz_items = channel.get("quiz", [])
    if len(terms) < 3 or not quiz_items:
        raise ValueError(f"Insufficient learning data for {channel_id}")
    start = ((TODAY.toordinal() - 1) // len(ORDER)) % len(terms)
    chosen = [terms[(start + i) % len(terms)] for i in range(3)]
    q = quiz_items[((TODAY.toordinal() - 1) // len(ORDER)) % len(quiz_items)]
    options = q.get("opts", [])
    if len(options) != 3 or q.get("a") not in options:
        raise ValueError(f"Invalid quiz in {channel_id}")
    return {
        "date": TODAY.isoformat(),
        "channel_id": channel_id,
        "discipline": channel["name"],
        "topic": f"{channel['vi']} · {channel['name']}",
        "title": f"GE4u Daily Practice: {channel['name']}",
        "objective": f"Review three core terms and practise one knowledge check in {channel['name']}.",
        "vocabulary": [
            {"term": w[0], "ipa": w[1], "meaning": w[2], "definition": w[3], "example": w[4]}
            for w in chosen
        ],
        "quiz": {"question": q["q"], "options": options, "answer": q["a"], "explanation": q["why"]},
        "source_mode": "curated-channel-data",
    }

if __name__ == "__main__":
    lesson = build()
    OUT_PATH.write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {lesson['date']} lesson for {lesson['channel_id']} ({lesson['source_mode']})")
