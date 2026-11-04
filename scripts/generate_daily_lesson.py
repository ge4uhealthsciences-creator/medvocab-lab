#!/usr/bin/env python3
"""Generate a daily Medical English micro-lesson, with a curated no-cost fallback."""
import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "daily-lesson.json"
TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()

BANK = [
    {
        "topic": "Respiratory system",
        "title": "Gas exchange and oxygenation",
        "objective": "Distinguish common terms used to describe breathing and gas exchange.",
        "vocabulary": [
            {"term": "dyspnea", "ipa": "/dɪspˈniːə/", "meaning": "khó thở", "definition": "Subjective difficulty or discomfort in breathing.", "example": "The patient reported dyspnea on exertion."},
            {"term": "hypoxemia", "ipa": "/ˌhaɪpɒkˈsiːmiə/", "meaning": "giảm oxy máu", "definition": "An abnormally low level of oxygen in arterial blood.", "example": "The team monitored the patient for hypoxemia."},
            {"term": "respiratory rate", "ipa": "/rɪˈspɪrətri reɪt/", "meaning": "tần số thở", "definition": "The number of breaths taken per minute.", "example": "The nurse recorded the respiratory rate."}
        ],
        "quiz": {"question": "Which term means an abnormally low level of oxygen in arterial blood?", "options": ["Dyspnea", "Hypoxemia", "Respiratory rate"], "answer": "Hypoxemia", "explanation": "Hypoxemia refers to low oxygen in arterial blood."}
    },
    {
        "topic": "Cardiovascular system",
        "title": "Blood pressure terminology",
        "objective": "Review core vocabulary used when discussing blood pressure.",
        "vocabulary": [
            {"term": "hypertension", "ipa": "/ˌhaɪpəˈtenʃən/", "meaning": "tăng huyết áp", "definition": "Persistently elevated arterial blood pressure.", "example": "Hypertension is an important cardiovascular risk factor."},
            {"term": "systolic pressure", "ipa": "/sɪˈstɒlɪk ˈpreʃə/", "meaning": "huyết áp tâm thu", "definition": "Arterial pressure during ventricular contraction.", "example": "Systolic pressure is the upper number in a blood pressure reading."},
            {"term": "diastolic pressure", "ipa": "/ˌdaɪəˈstɒlɪk ˈpreʃə/", "meaning": "huyết áp tâm trương", "definition": "Arterial pressure during ventricular relaxation.", "example": "Diastolic pressure is the lower number in a blood pressure reading."}
        ],
        "quiz": {"question": "When is systolic pressure measured?", "options": ["During ventricular contraction", "During ventricular relaxation", "Only during sleep"], "answer": "During ventricular contraction", "explanation": "Systolic pressure corresponds to ventricular contraction."}
    },
    {
        "topic": "Medication safety",
        "title": "Adverse effects and precautions",
        "objective": "Differentiate common medication-safety terms in patient counselling.",
        "vocabulary": [
            {"term": "adverse drug reaction", "ipa": "/ˈædvɜːs drʌɡ riˈækʃən/", "meaning": "phản ứng có hại của thuốc", "definition": "A harmful and unintended response to a medicine used at normal doses.", "example": "Report a suspected adverse drug reaction to a healthcare professional."},
            {"term": "contraindication", "ipa": "/ˌkɒntrəˌɪndɪˈkeɪʃən/", "meaning": "chống chỉ định", "definition": "A condition or factor that makes a particular treatment inadvisable.", "example": "A documented allergy may be a contraindication to a medicine."},
            {"term": "dosage", "ipa": "/ˈdəʊsɪdʒ/", "meaning": "liều dùng", "definition": "The amount and schedule of a medicine to be taken.", "example": "Follow the prescribed dosage instructions."}
        ],
        "quiz": {"question": "What is a contraindication?", "options": ["A reason a treatment should not be used", "The brand name of a medicine", "The time a pharmacy opens"], "answer": "A reason a treatment should not be used", "explanation": "A contraindication is a reason to avoid a particular treatment."}
    }
]

def fallback():
    item = json.loads(json.dumps(BANK[dt.date.today().toordinal() % len(BANK)]))
    item.update(date=TODAY, source_mode="curated-fallback")
    return item

if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lesson = fallback()  # curated lesson bank only (no third-party AI API)
    OUT.write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} for {TODAY}; mode={lesson['source_mode']}")
