#!/usr/bin/env python3
"""GE4u daily short-video pipeline (views & reach phase).

Builds 3 vertical videos per day (SLOTS): TikTok 1, Instagram/Facebook Reels 1, YouTube Shorts 1
(owner cut this to 1/platform/day on 6 Nov 2026 to conserve Claude usage; see AUTOPILOT.md).
Half are ~30 s clinical case quizzes taken from the GE4u English Ward game (data/game/cases.json,
refresh with `node scripts/export_game_cases.js`), half are word videos; disciplines rotate daily.

  python3 social-video/ge4u_video.py plan   --date 2026-11-04 --out out/
  python3 social-video/ge4u_video.py render --plan out/plan.json

Rendering needs ffmpeg, Pillow and the sherpa-onnx Kokoro TTS (see setup_tts.sh).
"""
import argparse, datetime as dt, hashlib, json, math, os, shutil, subprocess, sys, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
VN = dt.timezone(dt.timedelta(hours=7))
EPOCH = dt.date(2026, 11, 3)  # day 0 of the video rotation
W, H, FPS = 1080, 1920, 30

ORDER = ["dentistry", "medical", "pharmacy", "nursing", "midwifery", "social-work",
         "pharmaceutical-chemistry", "pharmaceutical-technology", "traditional-medicine",
         "public-health", "psychology", "nutrition"]
LABEL = {
    "dentistry": ("Răng Hàm Mặt", "Dental English", "🦷", "DentalEnglish"),
    "medical": ("Y khoa", "Medical English", "🩺", "MedicalEnglish"),
    "pharmacy": ("Dược học", "Pharmacy English", "💊", "PharmacyEnglish"),
    "nursing": ("Điều dưỡng", "Nursing English", "🩹", "NursingEnglish"),
    "midwifery": ("Hộ sinh", "Midwifery English", "🤰", "MidwiferyEnglish"),
    "social-work": ("Công tác xã hội", "Social Work English", "🤝", "SocialWorkEnglish"),
    "pharmaceutical-chemistry": ("Hóa dược", "Pharma Chemistry English", "⚗️", "PharmaChemistry"),
    "pharmaceutical-technology": ("Bào chế", "Pharma Technology English", "🏭", "PharmaTech"),
    "traditional-medicine": ("Y học cổ truyền", "Traditional Medicine English", "🌿", "TraditionalMedicine"),
    "public-health": ("Y tế công cộng", "Public Health English", "🌍", "PublicHealthEnglish"),
    "psychology": ("Tâm lý học", "Psychology English", "🧠", "PsychologyEnglish"),
    "nutrition": ("Dinh dưỡng", "Nutrition English", "🥗", "NutritionEnglish"),
}
COLOR = {  # background top, background bottom, accent
    "dentistry": ("#0b3a5b", "#06182a", "#5ee0ff"), "medical": ("#5b0b1e", "#22060c", "#ff7a8a"),
    "pharmacy": ("#2b0b5b", "#10062a", "#b98cff"), "nursing": ("#0b5b48", "#062a21", "#5effc5"),
    "midwifery": ("#5b0b4a", "#2a0622", "#ff8ae0"), "social-work": ("#5b3a0b", "#2a1a06", "#ffc35e"),
    "pharmaceutical-chemistry": ("#0b4a5b", "#06222a", "#5effff"), "pharmaceutical-technology": ("#3a3f4a", "#15181e", "#9ecbff"),
    "traditional-medicine": ("#2f5b0b", "#152a06", "#c5ff5e"), "public-health": ("#0b225b", "#060f2a", "#7aa8ff"),
    "psychology": ("#4a0b5b", "#20062a", "#e08aff"), "nutrition": ("#5b4a0b", "#2a2206", "#ffe35e"),
}
PLATFORMS = ["tiktok", "instagram", "youtube"]
FORMAT = {"tiktok": "pronounce", "instagram": "quiz", "youtube": "three_terms"}
# Four slots per platform per day, staggered so platforms never publish at the same minute.
# 12 slots per platform per day (all 12 disciplines on every platform), staggered by platform.
# Hours follow Metricool's best-time-to-post data for Asia/Ho_Chi_Minh (checked 3 Nov 2026):
# TikTok peaks 10h/12h/18h, Instagram 9–12h and 17–18h, YouTube 14–17h. Weak hours (before 8h, after 20h) dropped.
HOURS = {"tiktok": [8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20],
         "instagram": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
         "youtube": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]}
MINUTE = {"tiktok": 10, "instagram": 30, "youtube": 50}
TIMES = {p: [f"{h:02d}:{MINUTE[p]:02d}" for h in HOURS[p]] for p in MINUTE}
# Native Threads posts: Threads uses only the FIRST hashtag as the post's topic tag, so each post ends with one
# searched topic. Noon post uses the broad Vietnamese learner topic, evening post the discipline topic.
THREADS_TIMES = ["11:45"]  # 1 bài/nền tảng/ngày (chủ sở hữu quyết định 12/11/2026)
THREADS_TOPIC = {"medical": "medstudent", "dentistry": "dentalstudent", "pharmacy": "pharmacy", "nursing": "nursing",
                 "midwifery": "midwifery", "public-health": "publichealth", "psychology": "psychology",
                 "nutrition": "nutrition", "social-work": "socialwork", "traditional-medicine": "traditionalmedicine",
                 "pharmaceutical-chemistry": "chemistry", "pharmaceutical-technology": "pharmacy"}
THREADS_LIMIT = 480
HOOKS = {  # rotated daily; variant id is logged for hook experiments
    "pronounce": [("challenge", "Bạn đọc đúng từ này trong 3 giây không?"),
                  ("mistake", "Nhiều người đọc sai từ này 👀"),
                  ("curiosity", "Từ này trong {vi} nghĩa là gì?")],
    "quiz": [("question", "Chỉ 1 đáp án đúng. Bạn chọn gì?"),
             ("timer", "3 giây. Chọn nhanh!"),
             ("dare", "Sinh viên {vi} có trả lời được không?")],
    "three_terms": [("speed", "3 từ {en} trong 30 giây"),
                    ("list", "3 từ bạn sẽ gặp khi học {vi}"),
                    ("test", "Bạn biết mấy từ trong 3 từ này?")],
}
# Quality over volume (owner approved the marketing plan, 5 Nov 2026): 12 videos a day instead of 36.
# TikTok, YouTube and Meta all reduce reach for mass-produced look-alike videos, so each platform gets a
# few slots, half of them a longer clinical "case" quiz drawn from the English Ward game.
SLOTS = {"tiktok": [("18:10", "rotate")],
         "instagram": [("17:30", "rotate")],
         "youtube": [("14:50", "rotate")]}
ROTATE_FMT = {"tiktok": "quiz", "instagram": "quiz", "youtube": "three_terms"}  # for disciplines without game cases
CASE_DISC = {"dent": "dentistry", "ob": "midwifery"}  # every other department is shown as Medical English
DEPT_VI = {"er": "Cấp cứu", "card": "Tim mạch", "ped": "Nhi", "dent": "Răng Hàm Mặt", "eye": "Mắt", "derm": "Da liễu",
           "ortho": "Chấn thương chỉnh hình", "ent": "Tai Mũi Họng", "im": "Nội", "ob": "Sản", "neuro": "Thần kinh",
           "gi": "Tiêu hoá", "resp": "Hô hấp", "endo": "Nội tiết", "surg": "Ngoại"}
GAME_LINE = "🎮 Chơi trọn ca này trong game GE4u English Ward (chơi thử miễn phí, không cần tài khoản): link ở bio GE4u."
# Combined phase (owner decision, 3 Nov 2026): one video per platform per day carries a soft CTA.
CTA_LINE = "📚 Bộ học liệu {en} đầy đủ (PDF in được, có bài tập + đáp án): link ở bio GE4u."
VOICES = {"tiktok": 1, "instagram": 3, "youtube": 6}  # kokoro v0.19: af_bella, af_sarah, am_michael


# ---------------------------------------------------------------- content
def load_bank():
    bank = {k: [] for k in ORDER}
    seen = set()  # global: a term belongs to one discipline only, so no two disciplines make the same video

    def add(cid, row):
        term = row[0].strip()
        if term.lower() in seen or not all(str(x).strip() for x in row[:5]):
            return
        seen.add(term.lower())
        bank[cid].append({"term": term, "ipa": row[1], "meaning": row[2], "definition": row[3], "example": row[4]})

    for ch in json.loads((DATA / "ge4u-channel-samples.json").read_text(encoding="utf-8"))["channels"]:
        if ch["id"] in bank:
            for t in ch.get("terms", []):
                add(ch["id"], t)
    dental = json.loads((DATA / "dental-english-pack.json").read_text(encoding="utf-8"))
    for topic in dental.get("topics", []):
        for w in topic.get("words", []):
            add("dentistry", [w["term"], w.get("ipa", ""), w["meaning"], w["definition"], w["example"]])
    extra = json.loads((DATA / "social-video-bank.json").read_text(encoding="utf-8"))["channels"]
    for cid, rows in extra.items():
        for r in rows:
            add(cid, r)
    for cid, items in bank.items():
        if len(items) < 6:
            raise ValueError(f"{cid}: need at least 6 terms, have {len(items)}")
    return bank


def pick(seq, n, start):
    return [seq[(start + i) % len(seq)] for i in range(n)]


FMTS = ["pronounce", "quiz", "three_terms"]
FOLLOW = {"tiktok": "Follow", "instagram": "Follow", "youtube": "Subscribe"}
# Discovery tags per platform (3–6 is the useful range; the brand tag stays last).
PLATFORM_TAGS = {"tiktok": "#hoctienganh #sinhvien #LearnOnTikTok #xuhuong",
                 "instagram": "#hoctienganh #sinhvien #Reels",
                 "youtube": "#hoctienganh #Shorts"}


def load_cases():
    return json.loads((DATA / "game" / "cases.json").read_text(encoding="utf-8"))


def build_case(day, k, platform, slot, time, cases, cid_want=None):
    """A clinical case quiz from the game: the patient's own words, vitals, three diagnoses, the answer and why."""
    if cid_want:
        cases = [x for x in cases if CASE_DISC.get(x["dept"], "medical") == cid_want] or cases
    c = cases[(day * 6 + k) % len(cases)]
    cid = CASE_DISC.get(c["dept"], "medical")
    vi, en, emoji, tag = LABEL[cid]
    opts = list(c["options"])
    rot = (day + k) % 3
    opts = opts[rot:] + opts[:rot]
    answer = "ABC"[[o["ok"] for o in opts].index(True)]
    dept = DEPT_VI.get(c["dept"], "")
    sfx = " #Shorts" if platform == "youtube" else ""
    title = f"Bệnh nhân nói: \"{c['says']}\" Bạn chẩn đoán gì?"
    if len(title + sfx) > 100:
        title = f"{c['cc']}: bạn chẩn đoán gì? ({en})"
    item = {"discipline": cid, "discipline_vi": vi, "discipline_en": en, "platform": platform, "format": "case",
            "hook_variant": "case", "hook": f"{c['who']} · {dept}", "slot": slot, "time": time,
            "voice": VOICES[platform], "terms": [], "case": {**c, "options": opts, "answer": answer, "dept_vi": dept},
            "title": (title + sfx)[:100], "cta": True,
            "primary_metric": "average watch time, comments with A/B/C, game trial starts"}
    item["caption"] = (f"🚑 {c['who']} vào khoa {dept}: \"{c['says']}\"\n({c['cc']})\n\n"
                       f"Hỏi bệnh, khám và xét nghiệm xong, chẩn đoán đúng là gì?\n"
                       + "\n".join(f"{'ABC'[i]}) {o['vi']}" for i, o in enumerate(opts)) +
                       f"\n\nComment A, B hoặc C 👇 Đáp án ở cuối video.\n{GAME_LINE}\n\n"
                       f"#{tag} #TiengAnhYKhoa {PLATFORM_TAGS[platform]} #GE4u")
    return item


def build_item(day, cid, platform, slot, bank, fmt=None, time=None):
    vi, en, emoji, tag = LABEL[cid]
    terms = bank[cid]
    n = len(terms)
    # After each full pass through a discipline's terms, every platform moves to the next format,
    # so the same (platform, format, term) video does not come back for about 3 x n days.
    cycle = day // n if day >= 0 else 0
    fmt = fmt or FMTS[(FMTS.index(FORMAT[platform]) + cycle) % 3]
    follow, ptag = FOLLOW[platform], PLATFORM_TAGS[platform]
    salt = int(hashlib.sha1(f"{cid}{platform}".encode()).hexdigest(), 16) % n
    # Each discipline uses 5 consecutive terms per day: TikTok 1, Instagram 1, YouTube 3 — no overlap across platforms.
    step = next(k for k in range(5, 5 + n) if math.gcd(k, n) == 1)  # coprime step: full cycle before any repeat
    base = (day * step) % n
    hook_id, hook = HOOKS[fmt][(day + slot) % len(HOOKS[fmt])]
    hook = hook.format(vi=vi, en=en)
    item = {"discipline": cid, "discipline_vi": vi, "discipline_en": en, "platform": platform,
            "format": fmt, "hook_variant": hook_id, "hook": hook, "slot": slot,
            "time": time or TIMES[platform][slot], "voice": VOICES[platform]}
    if fmt == "pronounce":
        t = terms[base % n]
        item["terms"] = [t]
        item["caption"] = (f"{emoji} {t['term']} {t['ipa']}\n= {t['meaning']}\n\n"
                           f"Nghe 2 lần rồi đọc theo. Bạn đọc đúng ngay lần đầu không? 👇\n"
                           f"{follow} GE4u để học 1 từ {en} mỗi ngày.\n\n"
                           f"#{tag} {ptag} #GE4u")
        item["title"] = f"{t['term']} — {en}" + (" #Shorts" if platform == "youtube" else "")
        item["primary_metric"] = "average watch time, full-video-watched rate"
    elif fmt == "quiz":
        start = (base + 1) % n
        t = terms[start]
        pool = [x for x in terms if x["term"] != t["term"]]
        distractors = pick(pool, 2, (day * 3 + salt) % len(pool))
        opts = [t] + distractors
        rot = (day + slot) % 3
        opts = opts[rot:] + opts[:rot]
        letters = "ABC"
        answer = letters[[o["term"] for o in opts].index(t["term"])]
        item["terms"] = [t]
        item["quiz"] = {"question": t["definition"], "options": [o["term"] for o in opts], "answer": answer}
        item["caption"] = (f"{emoji} {en} quiz: \"{t['definition']}\"\n"
                           f"A) {opts[0]['term']}  B) {opts[1]['term']}  C) {opts[2]['term']}\n\n"
                           f"Comment A, B hoặc C trước khi xem đáp án 👇 Gửi cho bạn học cùng ngành để thử thách!\n\n"
                           f"#{tag} {ptag} #GE4u")
        item["title"] = f"{en} quiz: {t['term'][0].upper()}…?" + (" #Shorts" if platform == "youtube" else "")
        item["primary_metric"] = "non-follower reach, shares"
    else:
        trio = pick(terms, 3, (base + 2) % n)
        item["terms"] = trio
        sfx = " #Shorts" if platform == "youtube" else ""
        full = f"3 {en} words in 30 seconds: {', '.join(x['term'] for x in trio)}{sfx}"
        item["title"] = full if len(full) <= 100 else f"3 {en} words in 30 seconds{sfx}"
        item["caption"] = ("\n".join(f"• {x['term']} {x['ipa']} = {x['meaning']}" for x in trio) +
                           f"\n\nBạn đã biết mấy từ? Comment số 0–3 👇 {follow} GE4u để học {en} miễn phí mỗi ngày.\n\n"
                           f"#{tag} {ptag} #GE4u")
        item["primary_metric"] = "views, average view duration"
    return item


def dedupe_tags(text):
    head, sep, tags = text.rpartition("\n\n")
    if not sep or not tags.startswith("#"):
        return text
    seen, keep = set(), []
    for t in tags.split():
        if t.lower() not in seen:
            seen.add(t.lower()); keep.append(t)
    return head + sep + " ".join(keep)


def _items(day, bank, cases):
    """The day's 12 videos (SLOTS): case quizzes from the game plus word videos, disciplines rotating daily."""
    items, k, w = [], 0, 0
    for pi, platform in enumerate(PLATFORMS):
        for slot, (time, fmt) in enumerate(SLOTS[platform]):
            if fmt == "rotate":
                # Owner (12 Nov 2026): one post a day per platform, rotating through all 12 disciplines.
                # Each platform is 4 disciplines apart, so every discipline reaches every platform every 12 days.
                cid = ORDER[(day + 4 * pi) % 12]
                if cid in CASE_DISC.values() or cid == "medical":
                    it = build_case(day, k, platform, slot, time, cases, cid_want=cid); k += 1
                else:
                    it = build_item(day, cid, platform, slot, bank, fmt=ROTATE_FMT[platform], time=time)
            elif fmt == "case":
                it = build_case(day, k, platform, slot, time, cases); k += 1
            else:
                cid = ORDER[(day * 5 + w + 4 * pi) % 12]; w += 1
                it = build_item(day, cid, platform, slot, bank, fmt=fmt, time=time)
            items.append(it)
    return items


def make_plan(date):
    """12 items a day (see SLOTS); every discipline still comes round every few days."""
    bank, cases = load_bank(), load_cases()
    day = (date - EPOCH).days
    items = []
    for it in _items(day, bank, cases):
        it["caption"] = dedupe_tags(it["caption"])
        it["id"] = f"{date.isoformat()}-{it['platform']}-{it['slot']:02d}-{it['discipline']}"
        it["date"] = date.isoformat()
        items.append(it)
    items.sort(key=lambda x: (x["time"], x["platform"]))
    return {"date": date.isoformat(), "timezone": "Asia/Ho_Chi_Minh", "phase": "quality: 12 videos, half clinical cases",
            "rotation_day": day, "items": items, "threads": make_threads(items, day)}


def _day_items(day, bank):
    return _items(day, bank, load_cases())


def _threads_pick(items, day, avoid=frozenset()):
    picks, used = [], set()
    for want in ("quiz", "three_terms"):
        cands = [i for i in items if i["format"] == want and not i.get("cta") and i["discipline"] not in used]
        if not cands:
            continue
        order = cands[day % len(cands):] + cands[:day % len(cands)]
        it = next((c for c in order if tuple(t["term"] for t in c["terms"]) not in avoid), order[0])
        used.add(it["discipline"])
        picks.append(it)
    return picks


def make_threads(items, day):
    """Two native Threads text posts a day (a quiz and a 3-word list) from today's videos, one topic tag each.
    Terms used on Threads in the previous 30 days are skipped so Threads never repeats within a month."""
    bank = load_bank()
    avoid = {tuple(t["term"] for t in it["terms"]) for d in range(day - 30, day) for it in _threads_pick(_day_items(d, bank), d)}
    out = []
    for it, time, topic in zip(_threads_pick(items, day, avoid), THREADS_TIMES, (None, "discipline")):
        body = it["caption"].rpartition("\n\n")[0]  # drop the hashtag line
        body = body.replace("Subscribe GE4u", "Follow GE4u").replace(" Gửi cho bạn học cùng ngành để thử thách!", "")
        tag = "tienganh" if topic is None else THREADS_TOPIC[it["discipline"]]
        text = body.strip() + "\n\n#" + tag
        if len(text) > THREADS_LIMIT:
            raise ValueError(f"threads post too long ({len(text)}): {it['id']}")
        out.append({"id": it["id"].replace(it["platform"], "threads", 1), "time": time, "discipline": it["discipline"],
                    "format": it["format"], "topic": tag, "text": text})
    return out


# ---------------------------------------------------------------- rendering
FONT_DIRS = ["/usr/share/fonts/opentype/inter", "/usr/share/fonts/truetype/inter", str(ROOT / "social-video" / "fonts")]


def font(weight, size):
    from PIL import ImageFont
    names = {"black": ["Inter-Black.otf", "Inter-ExtraBold.otf"], "bold": ["Inter-Bold.otf"],
             "semi": ["Inter-SemiBold.otf", "Inter-Medium.otf"], "reg": ["Inter-Regular.otf"],
             "ipa": []}
    for d in FONT_DIRS:
        for nme in names.get(weight, []):
            p = Path(d) / nme
            if p.exists():
                return ImageFont.truetype(str(p), size)
    dj = "DejaVuSans-Bold.ttf" if weight in ("black", "bold", "semi") else "DejaVuSans.ttf"
    for d in ["/usr/share/fonts/truetype/dejavu"]:
        if (Path(d) / dj).exists():
            return ImageFont.truetype(str(Path(d) / dj), size)
    raise FileNotFoundError("No usable font found")


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def clean(text):
    return "".join(ch for ch in text if ord(ch) < 0x2600 and ch != "\ufe0f").strip()


def wrap(draw, text, fnt, maxw):
    text = clean(text)
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self, cid):
        from PIL import Image, ImageDraw
        top, bot, acc = COLOR[cid]
        a, b = hexrgb(top), hexrgb(bot)
        self.img = Image.new("RGB", (W, H))
        px = self.img.load()
        for y in range(H):
            f = y / (H - 1)
            c = tuple(int(a[i] * (1 - f) + b[i] * f) for i in range(3))
            for x in range(W):
                px[x, y] = c
        self.d = ImageDraw.Draw(self.img)
        self.acc = hexrgb(acc)
        self.cid = cid

    def header(self):
        vi, en, _, _ = LABEL[self.cid]
        f = font("black", 52)
        gw = self.d.textlength("GE4u", font=f)
        self.d.rounded_rectangle((70, 150, 70 + gw + 52, 234), 20, fill=self.acc)
        self.d.text((96, 160), "GE4u", font=f, fill=(10, 10, 20))
        sub = font("semi", 42)
        self.d.text((70 + gw + 84, 168), clean(f"{vi} · {en}"), font=sub, fill=(235, 235, 245))

    def block(self, text, y, size, weight="black", color=(255, 255, 255), maxw=920, spacing=1.18, center=True):
        f = font(weight, size)
        for line in wrap(self.d, text, f, maxw):
            w = self.d.textlength(line, font=f)
            x = (W - w) / 2 if center else 80
            self.d.text((x, y), line, font=f, fill=color)
            y += int(size * spacing)
        return y

    def pill(self, text, y, size=60, fill=None, fg=(10, 10, 20)):
        f = font("bold", size)
        text = clean(text)
        while self.d.textlength(text, font=f) > W - 200 and size > 40:
            size -= 6; f = font("bold", size)
        w = self.d.textlength(text, font=f)
        x = (W - w) / 2
        self.d.rounded_rectangle((x - 40, y - 18, x + w + 40, y + size + 26), 30, fill=fill or self.acc)
        self.d.text((x, y), text, font=f, fill=fg)
        return y + size + 60

    def save(self, path):
        self.img.save(path)


def scenes_for(item):
    """Return scenes: dict(draw=callable(canvas), say=str|None, min=seconds, beep=bool).
    Text stays inside y 300-1450 (clear of platform UI at top and bottom)."""
    sc = []
    t = item["terms"]
    fmt = item["format"]
    if fmt == "pronounce":
        x = t[0]
        sc.append(dict(min=2.2, say=None, draw=lambda c: (c.header(), c.block(item["hook"], 520, 116),
                                                          c.pill(x["term"], 1060, 120))))
        for n in ["3", "2", "1"]:
            sc.append(dict(min=0.8, say=None, beep=True, draw=lambda c, n=n: (
                c.header(), c.block("Thử đọc trước...", 440, 64, "semi"), c.pill(x["term"], 600, 120),
                c.block(n, 880, 380, color=c.acc))))
        sc.append(dict(min=2.0, say=f"{x['term']}. ... {x['term']}.", draw=lambda c: (
            c.header(), c.block("Nghe và đọc theo", 480, 64, "semi"), c.pill(x["term"], 640, 120),
            c.block(x["ipa"], 900, 84, "ipa", color=c.acc))))
        sc.append(dict(min=2.5, say=x["definition"], draw=lambda c: (
            c.header(), c.block(x["term"], 420, 96), c.block(x["ipa"], 560, 64, "ipa", color=c.acc),
            c.block("= " + x["meaning"], 740, 96, "bold", color=c.acc), c.block(x["definition"], 1000, 66, "semi"))))
        sc.append(dict(min=2.5, say=x["example"], draw=lambda c: (
            c.header(), c.block("Ví dụ · Example", 560, 60, "semi", color=c.acc),
            c.block(f"“{x['example']}”", 700, 84, "bold"))))
        sc.append(dict(min=2.0, say=x["term"], draw=lambda c: (
            c.header(), c.block("Đến lượt bạn đọc!", 560, 80, "bold"), c.pill(x["term"], 780, 120),
            c.block("Follow GE4u", 1130, 64, "bold", color=c.acc), c.block("1 từ chuyên ngành mỗi ngày", 1220, 52, "semi"))))
    elif fmt == "quiz":
        q = item["quiz"]
        def opts(c, reveal=False, y=820):
            for i, o in enumerate(q["options"]):
                L = "ABC"[i]
                good = reveal and L == q["answer"]
                fill = c.acc if good else ((70, 70, 85) if reveal else (255, 255, 255))
                fg = (10, 10, 20) if not reveal or good else (190, 190, 200)
                c.d.rounded_rectangle((90, y, W - 90, y + 170), 36, fill=fill)
                size = 70
                f = font("bold", size)
                txt = f"{L}   {o}"
                while c.d.textlength(txt, font=f) > W - 280 and size > 40:
                    size -= 4; f = font("bold", size)
                c.d.text((150, y + (170 - size) / 2 - 6), txt, font=f, fill=fg)
                y += 205
        sc.append(dict(min=2.0, say=None, draw=lambda c: (c.header(), c.block(item["hook"], 640, 120))))
        sc.append(dict(min=3.0, say=q["question"], draw=lambda c: (
            c.header(), c.block("Thuật ngữ nào có nghĩa là:", 330, 54, "semi", color=c.acc),
            c.block(q["question"], 420, 70, "bold"), opts(c))))
        for n in ["3", "2", "1"]:
            sc.append(dict(min=0.8, say=None, beep=True, draw=lambda c, n=n: (
                c.header(), c.block(n, 300, 200, color=c.acc), c.block(q["question"], 540, 56, "bold"), opts(c))))
        x = item["terms"][0]
        sc.append(dict(min=2.5, say=f"The answer is {q['answer']}. {x['term']}.", draw=lambda c: (
            c.header(), c.block(f"Đáp án: {q['answer']}", 360, 110, color=c.acc), c.block(q["question"], 530, 56, "semi"),
            opts(c, True))))
        sc.append(dict(min=2.5, say=x["example"], draw=lambda c: (
            c.header(), c.pill(x["term"], 420, 110), c.block(x["ipa"], 620, 70, "ipa", color=c.acc),
            c.block("= " + x["meaning"], 760, 90, "bold"), c.block(f"“{x['example']}”", 1000, 64, "semi"),
            c.block("Bạn chọn đúng không? Comment A/B/C", 1330, 50, "semi", color=c.acc))))
    else:
        sc.append(dict(min=2.0, say=None, draw=lambda c: (c.header(), c.block(item["hook"], 560, 120),
                                                          c.block("1 · 2 · 3", 1100, 110, color=c.acc))))
        for i, x in enumerate(t):
            sc.append(dict(min=2.0, say=f"{x['term']}. {x['term']}.", draw=lambda c, i=i, x=x: (
                c.header(), c.block(f"{i + 1}/3", 420, 80, "bold", color=c.acc), c.pill(x["term"], 600, 116),
                c.block(x["ipa"], 860, 80, "ipa", color=c.acc), c.block("= " + x["meaning"], 1020, 92, "bold"))))
            sc.append(dict(min=2.0, say=x["definition"], draw=lambda c, i=i, x=x: (
                c.header(), c.block(f"{i + 1}/3 · {x['term']}", 440, 72, "bold", color=c.acc),
                c.block("= " + x["meaning"], 580, 84, "bold"), c.block(x["definition"], 820, 72, "semi"))))
        sc.append(dict(min=2.0, say=None, draw=lambda c: (
            c.header(), c.block("Bạn biết mấy từ?", 600, 116), c.block("Comment 0 – 3", 900, 90, "bold", color=c.acc),
            c.block("Subscribe để học miễn phí mỗi ngày", 1120, 56, "semi"))))
    if fmt == "case":
        return case_scenes(item)
    if item.get("cta"):
        sc[-1] = dict(min=2.6, say=None, draw=lambda c: (
            c.header(), c.block("Muốn học trọn bộ?", 560, 96),
            c.block(f"{item['discipline_en']} Learning Pack", 740, 70, "bold", color=c.acc),
            c.block("PDF in được · bài tập · đáp án", 960, 56, "semi"),
            c.pill("Link ở bio GE4u", 1140, 80)))
    return sc


PATIENT_VOICE = {"m": 6, "f": 3}  # kokoro v0.19: am_michael, af_sarah


def _sex(who):
    w = who.lower()
    return "f" if any(x in w for x in ("ms.", "mrs.", "miss", "bà ", "cô ", "chị ", "bé gái", "girl")) else "m"


def case_scenes(item):
    c = item["case"]
    opts, ans = c["options"], c["answer"]
    good = next(o for o in opts if o["ok"])
    pv = PATIENT_VOICE[_sex(c["who"])]
    def boxes(cv, reveal=False, y=760):
        from PIL import ImageFont  # noqa: F401  (fonts come from font())
        for i, o in enumerate(opts):
            L = "ABC"[i]
            hit = reveal and o["ok"]
            fill = cv.acc if hit else ((70, 70, 85) if reveal else (255, 255, 255))
            fg = (10, 10, 20) if not reveal or hit else (190, 190, 200)
            size = 56
            f = font("bold", size)
            lines = wrap(cv.d, f"{L}  {o['vi']}", f, W - 300)
            while len(lines) > 2 and size > 42:
                size -= 6; f = font("bold", size); lines = wrap(cv.d, f"{L}  {o['vi']}", f, W - 300)
            lead = int(size * 1.18)
            hgt = 70 + lead * len(lines)
            cv.d.rounded_rectangle((90, y, W - 90, y + hgt), 36, fill=fill)
            yy = y + 35
            for ln in lines:
                cv.d.text((140, yy), ln, font=f, fill=fg); yy += lead
            y += hgt + 30
        return y
    vit = c.get("vit") or {}
    vtxt = " · ".join(x for x in [f"Mạch {vit['hr']}" if vit.get("hr") else "", f"HA {vit['bp']}" if vit.get("bp") else "",
                                  f"SpO₂ {vit['sp']}%" if vit.get("sp") else "", f"{vit['t']}°C" if vit.get("t") else ""] if x)
    sc = [dict(min=2.2, say=None, draw=lambda cv: (cv.header(), cv.block("Bạn là bác sĩ trực", 430, 70, "semi", color=cv.acc),
                                                     cv.block(f"{c['who']} vào khoa {c['dept_vi']}", 560, 84),
                                                     cv.block(c["cc"], 820, 62, "semi"))),
          dict(min=2.5, say=c["says"], voice=pv, draw=lambda cv: (
              cv.header(), cv.block("Bệnh nhân nói:", 400, 60, "semi", color=cv.acc),
              cv.block(f"“{c['says']}”", 520, 74, "bold"),
              cv.block(vtxt, 1250, 52, "semi", color=cv.acc) if vtxt else None)),
          dict(min=3.2, say=None, draw=lambda cv: (
              cv.header(), cv.block("Hỏi bệnh, khám, xét nghiệm xong.", 380, 54, "semi"),
              cv.block("Chẩn đoán đúng là gì?", 470, 76), boxes(cv)))]
    for n in ["3", "2", "1"]:
        sc.append(dict(min=0.8, say=None, beep=True, draw=lambda cv, n=n: (
            cv.header(), cv.block(n, 330, 200, color=cv.acc), boxes(cv))))
    sc.append(dict(min=2.6, say=None, draw=lambda cv: (cv.header(), cv.block(f"Đáp án: {ans}", 360, 110, color=cv.acc),
                                                       boxes(cv, True))))
    whys = [o for o in opts if not o["ok"] and o["why"]]
    if whys:
        sc.append(dict(min=3.2, say=None, draw=lambda cv: (cv.header(), cv.block("Vì sao không phải:", 380, 62, "bold", color=cv.acc),
                       [cv.block(f"{o['vi']}: {o['why']}", 520 + 330 * i, 50, "semi") for i, o in enumerate(whys[:2])])))
    sc.append(dict(min=2.5, say=good["en"], draw=lambda cv: (
        cv.header(), cv.block("Bác sĩ nói với bệnh nhân:", 420, 60, "semi", color=cv.acc),
        cv.block(f"“{good['en']}”", 560, 74, "bold"))))
    sc.append(dict(min=2.6, say=None, draw=lambda cv: (
        cv.header(), cv.block("Chơi trọn ca này", 560, 96), cv.block("GE4u English Ward", 720, 80, "bold", color=cv.acc),
        cv.block("Game tiếng Anh y khoa · chơi thử miễn phí", 900, 52, "semi"), cv.pill("Link ở bio GE4u", 1100, 80))))
    return sc


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr[-800:]}")
    return r


def tts(text, sid, out):
    tdir = Path(os.environ.get("GE4U_TTS_DIR") or os.path.expanduser("~/ge4u-tts"))
    binp = next(tdir.glob("sherpa-onnx-*/bin/sherpa-onnx-offline-tts"))
    m = tdir / "kokoro-en-v0_19"
    run([str(binp), f"--kokoro-model={m}/model.onnx", f"--kokoro-voices={m}/voices.bin",
         f"--kokoro-tokens={m}/tokens.txt", f"--kokoro-data-dir={m}/espeak-ng-data", "--num-threads=4",
         f"--sid={sid}", "--kokoro-length-scale=1.08", f"--output-filename={out}", text])
    with wave.open(str(out)) as w:
        return w.getnframes() / w.getframerate()


def render_item(item, outdir, work):
    outdir, work = Path(outdir).resolve(), Path(work).resolve()
    work.mkdir(parents=True, exist_ok=True)
    scenes = scenes_for(item)
    parts, audio_parts, total = [], [], 0.0
    for i, s in enumerate(scenes):
        c = Canvas(item["discipline"])
        s["draw"](c)
        png = work / f"s{i}.png"
        c.save(png)
        dur = s["min"]
        wav = None
        if s.get("say"):
            wav = work / f"s{i}.wav"
            dur = max(dur, tts(s["say"], s.get("voice", item["voice"]), wav) + 0.45)
        dur = round(dur * FPS) / FPS
        seg = work / f"s{i}.mp4"
        tmp = work / f"s{i}.tmp.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(png), "-vf",
             f"format=yuv420p,loop=-1:1,trim=duration={dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), str(tmp)])
        tmp.rename(seg)
        parts.append(seg)
        # audio for this scene: speech (if any) padded with silence, or a tick for countdown
        aseg = work / f"a{i}.wav"
        if wav:
            run(["ffmpeg", "-y", "-v", "error", "-i", str(wav), "-af", f"adelay=150|150,apad=whole_dur={dur:.3f}",
                 "-ar", "24000", "-ac", "1", str(aseg)])
        elif s.get("beep"):
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=880:duration=0.12",
                 "-af", f"volume=0.25,apad=whole_dur={dur:.3f}", "-ar", "24000", "-ac", "1", str(aseg)])
        else:
            run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
                 "-t", f"{dur:.3f}", str(aseg)])
        audio_parts.append(aseg)
        total += dur
    lst = work / "v.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    alst = work / "a.txt"
    alst.write_text("".join(f"file '{p}'\n" for p in audio_parts))
    silent = work / "video.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
    voice = work / "voice.wav"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(alst), "-c", "copy", str(voice)])
    final = outdir / f"{item['id']}.mp4"
    tmp = outdir / f"{item['id']}.tmp.mp4"
    # progress bar across the bottom keeps motion on screen; placed above platform UI safe zone
    acc = COLOR[item["discipline"]][2].lstrip("#")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-i", str(voice), "-f", "lavfi", "-i",
         f"color=c=0x{acc}:s={W}x12:r={FPS}",
         "-filter_complex", f"[0:v][2:v]overlay=x='-W+W*t/{total:.3f}':y=262:shortest=1[v]",
         "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart",
         "-t", f"{total:.3f}", str(tmp)])
    tmp.rename(final)
    item["file"] = final.name
    item["duration_s"] = round(total, 2)
    shutil.rmtree(work, ignore_errors=True)
    return final


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan"); p.add_argument("--date"); p.add_argument("--out", default="out")
    r = sub.add_parser("render"); r.add_argument("--plan", required=True); r.add_argument("--only", default="")
    a = ap.parse_args()
    if a.cmd == "plan":
        date = dt.date.fromisoformat(a.date) if a.date else dt.datetime.now(VN).date()
        plan = make_plan(date)
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        mix = {}
        for it in plan["items"]:
            mix.setdefault(it["platform"], []).append(it["discipline"])
        print(json.dumps(mix, ensure_ascii=False))
    else:
        planp = Path(a.plan)
        plan = json.loads(planp.read_text(encoding="utf-8"))
        outdir = planp.parent
        for it in plan["items"]:
            if a.only and a.only not in it["id"]:
                continue
            for attempt in (1, 2):
                try:
                    f = render_item(it, outdir, outdir / ".work" / it["id"])
                    break
                except Exception as e:  # one retry per video; a second failure stops the run
                    print(f"render failed ({attempt}/2) for {it['id']}: {e}", file=sys.stderr)
                    shutil.rmtree(outdir / ".work" / it["id"], ignore_errors=True)
                    if attempt == 2:
                        raise
            print(f"rendered {f.name} {it['duration_s']}s")
        planp.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
