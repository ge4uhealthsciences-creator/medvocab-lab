#!/usr/bin/env python3
"""Build the 12 GE4u Learning Pack PDFs (vocabulary, 3 practice sets, answer key, 7-day review plan).

  python3 scripts/build_packs.py --out dist/packs
"""
import argparse, random, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "social-video"))
import ge4u_video as gv  # reuses the merged vocabulary bank and labels

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

DJ = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", DJ + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", DJ + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVI", DJ + "DejaVuSans-Oblique.ttf"))
from reportlab.lib.fonts import addMapping
addMapping("DV", 0, 0, "DV"); addMapping("DV", 1, 0, "DVB"); addMapping("DV", 0, 1, "DVI"); addMapping("DV", 1, 1, "DVB")

INK = colors.HexColor("#15334b")
TEAL = colors.HexColor("#087e83")
SOFT = colors.HexColor("#e8f4f4")
LINE = colors.HexColor("#c9d6dd")

S = {
    "title": ParagraphStyle("t", fontName="DVB", fontSize=26, leading=32, textColor=INK, spaceAfter=6),
    "sub": ParagraphStyle("s", fontName="DV", fontSize=13, leading=18, textColor=TEAL, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="DVB", fontSize=16, leading=21, textColor=INK, spaceBefore=4, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DVB", fontSize=12, leading=16, textColor=TEAL, spaceBefore=6, spaceAfter=4),
    "body": ParagraphStyle("b", fontName="DV", fontSize=10, leading=14.5, textColor=colors.black),
    "small": ParagraphStyle("sm", fontName="DV", fontSize=8.6, leading=11.5, textColor=colors.HexColor("#333333")),
    "cell": ParagraphStyle("c", fontName="DV", fontSize=8.6, leading=11),
    "cellb": ParagraphStyle("cb", fontName="DVB", fontSize=9, leading=11.5, textColor=INK),
    "note": ParagraphStyle("n", fontName="DVI", fontSize=8.6, leading=11.5, textColor=colors.HexColor("#555555")),
}


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def footer(label):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("DV", 7.5)
        canvas.setFillColor(colors.HexColor("#666666"))
        canvas.drawString(18 * mm, 10 * mm, f"GE4u Health Sciences · {label} · Dành cho người học đã đăng ký, vui lòng không chia sẻ lại.")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
        canvas.restoreState()
    return draw


def table(data, widths, header=True, zebra=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
          ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), INK), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white)]
    if zebra:
        for r in range(1 if header else 0, len(data)):
            if r % 2 == 0:
                st.append(("BACKGROUND", (0, r), (-1, r), SOFT))
    t.setStyle(TableStyle(st))
    return t


def hcell(t):
    return Paragraph(f'<font color="white"><b>{esc(t)}</b></font>', S["cell"])


def build(cid, terms, out):
    vi, en, _, _ = gv.LABEL[cid]
    rnd = random.Random(f"ge4u-{cid}")
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=16 * mm, bottomMargin=18 * mm,
                            title=f"GE4u {en} Learning Pack", author="GE4u Health Sciences")
    W = A4[0] - 36 * mm
    st = []

    # Cover
    st += [Spacer(1, 30 * mm), Paragraph("GE4u Health Sciences", S["sub"]),
           Paragraph(f"{esc(en)}<br/>Learning Pack", S["title"]),
           Paragraph(f"{esc(vi)} · Tiếng Anh chuyên ngành", S["sub"]), Spacer(1, 8 * mm)]
    contents = [
        ["Phần", "Nội dung"],
        ["1", f"Bảng {len(terms)} thuật ngữ cốt lõi: IPA, nghĩa tiếng Việt, định nghĩa tiếng Anh, câu ví dụ"],
        ["2", "Luyện tập A: Nối thuật ngữ với nghĩa tiếng Việt (10 câu)"],
        ["3", "Luyện tập B: Trắc nghiệm định nghĩa (10 câu)"],
        ["4", "Luyện tập C: Điền từ vào câu (8 câu)"],
        ["5", "Đáp án đầy đủ"],
        ["6", "Lộ trình ôn tập 7 ngày (lặp lại ngắt quãng)"],
    ]
    st.append(table([[hcell(a), hcell(b)] if i == 0 else [Paragraph(a, S["cell"]), Paragraph(esc(b), S["cell"])]
                     for i, (a, b) in enumerate(contents)], [16 * mm, W - 16 * mm]))
    st += [Spacer(1, 8 * mm), Paragraph(
        "Cách dùng: đọc to từng thuật ngữ theo IPA, che cột nghĩa để tự kiểm tra, làm 3 phần luyện tập rồi mới xem đáp án. "
        "Đánh dấu từ sai để ôn lại theo lộ trình 7 ngày ở cuối tài liệu.", S["body"]),
        Spacer(1, 4 * mm), Paragraph(
        "Tài liệu phục vụ học tiếng Anh chuyên ngành; không thay thế hướng dẫn chuyên môn, phác đồ hay tài liệu lâm sàng đã được phê duyệt.",
        S["note"]), PageBreak()]

    # 1. Vocabulary
    st.append(Paragraph(f"1. Bảng thuật ngữ — {esc(en)}", S["h1"]))
    rows = [[hcell("#"), hcell("Term / IPA"), hcell("Nghĩa"), hcell("Definition"), hcell("Example")]]
    for i, t in enumerate(terms, 1):
        rows.append([Paragraph(str(i), S["cell"]),
                     Paragraph(f"<b>{esc(t['term'])}</b><br/>{esc(t['ipa'])}", S["cell"]),
                     Paragraph(esc(t["meaning"]), S["cell"]),
                     Paragraph(esc(t["definition"]), S["cell"]),
                     Paragraph(f"<i>{esc(t['example'])}</i>", S["cell"])])
    st += [table(rows, [8 * mm, 38 * mm, 32 * mm, 46 * mm, W - 124 * mm]), PageBreak()]

    # 2. Matching
    pick = rnd.sample(terms, min(10, len(terms)))
    meanings = [t["meaning"] for t in pick]
    shuffled = meanings[:]
    rnd.shuffle(shuffled)
    letters = "ABCDEFGHIJ"
    st.append(Paragraph("2. Luyện tập A — Nối thuật ngữ với nghĩa", S["h1"]))
    st.append(Paragraph("Ghi chữ cái của nghĩa đúng vào ô trống.", S["body"]))
    st.append(Spacer(1, 3 * mm))
    mrows = [[hcell("Thuật ngữ"), hcell(""), hcell("Nghĩa")]]
    for i, t in enumerate(pick):
        mrows.append([Paragraph(f"{i + 1}. {esc(t['term'])}", S["cell"]), Paragraph("____", S["cell"]),
                      Paragraph(f"{letters[i]}. {esc(shuffled[i])}", S["cell"])])
    st.append(table(mrows, [62 * mm, 16 * mm, W - 78 * mm]))
    key_a = [f"{i + 1}-{letters[shuffled.index(m)]}" for i, m in enumerate(meanings)]

    # 3. Definition MCQ
    st.append(Spacer(1, 8 * mm))
    st.append(Paragraph("3. Luyện tập B — Trắc nghiệm định nghĩa", S["h1"]))
    qpick = rnd.sample(terms, min(10, len(terms)))
    key_b = []
    for i, t in enumerate(qpick, 1):
        others = rnd.sample([x for x in terms if x["term"] != t["term"]], 2)
        opts = [t["term"], others[0]["term"], others[1]["term"]]
        rnd.shuffle(opts)
        ans = "ABC"[opts.index(t["term"])]
        key_b.append(f"{i}-{ans}")
        st.append(KeepTogether([Paragraph(f"<b>{i}.</b> {esc(t['definition'])}", S["body"]),
                                Paragraph("&nbsp;&nbsp;&nbsp;" + "&nbsp;&nbsp;&nbsp;&nbsp;".join(
                                    f"{'ABC'[k]}) {esc(o)}" for k, o in enumerate(opts)), S["body"]),
                                Spacer(1, 2.5 * mm)]))
    st.append(PageBreak())

    # 4. Gap fill
    st.append(Paragraph("4. Luyện tập C — Điền từ vào câu", S["h1"]))
    gaps = []
    for t in rnd.sample(terms, len(terms)):
        pat = re.compile(re.escape(t["term"]), re.I)
        if pat.search(t["example"]):
            gaps.append((t, pat.sub("__________", t["example"], count=1)))
        if len(gaps) == 8:
            break
    bank = [g[0]["term"] for g in gaps]
    rnd.shuffle(bank)
    st.append(Paragraph("Từ gợi ý: " + " · ".join(f"<b>{esc(b)}</b>" for b in bank), S["body"]))
    st.append(Spacer(1, 3 * mm))
    for i, (t, s) in enumerate(gaps, 1):
        st.append(Paragraph(f"{i}. {esc(s)}", S["body"]))
        st.append(Spacer(1, 2.5 * mm))
    key_c = [f"{i}. {t['term']}" for i, (t, _) in enumerate(gaps, 1)]

    # 5. Answer key
    st.append(Spacer(1, 8 * mm))
    st.append(Paragraph("5. Đáp án", S["h1"]))
    st.append(Paragraph("<b>Luyện tập A:</b> " + " · ".join(key_a), S["body"]))
    st.append(Paragraph("<b>Luyện tập B:</b> " + " · ".join(key_b), S["body"]))
    st.append(Paragraph("<b>Luyện tập C:</b> " + " · ".join(esc(k) for k in key_c), S["body"]))
    st.append(PageBreak())

    # 6. 7-day plan
    st.append(Paragraph("6. Lộ trình ôn tập 7 ngày", S["h1"]))
    n = len(terms)
    third = (n + 2) // 3
    groups = [terms[:third], terms[third:2 * third], terms[2 * third:]]
    g = lambda k: f"từ {sum(len(x) for x in groups[:k]) + 1}–{sum(len(x) for x in groups[:k + 1])}"
    plan = [["Ngày", "Việc cần làm (15–20 phút)"],
            ["1", f"Học {g(0)}: đọc to theo IPA 3 lần, che nghĩa tự kiểm tra."],
            ["2", f"Học {g(1)}. Ôn nhanh {g(0)}."],
            ["3", f"Học {g(2)}. Làm Luyện tập A, đánh dấu từ sai."],
            ["4", "Ôn toàn bộ từ đã đánh dấu. Làm Luyện tập B."],
            ["5", "Làm Luyện tập C. Tự đặt 1 câu mới cho mỗi từ sai."],
            ["6", "Che cột tiếng Anh, nhìn nghĩa tiếng Việt và nói lại thuật ngữ."],
            ["7", "Làm lại cả 3 phần luyện tập không xem bảng từ; mục tiêu đúng ≥ 90%."]]
    st.append(table([[hcell(a), hcell(b)] if i == 0 else [Paragraph(a, S["cell"]), Paragraph(esc(b), S["cell"])]
                     for i, (a, b) in enumerate(plan)], [16 * mm, W - 16 * mm]))
    st += [Spacer(1, 6 * mm), Paragraph(
        "Học thêm mỗi ngày miễn phí: bài học hằng ngày trên website GE4u và các video ngắn trên TikTok, Instagram, YouTube, Facebook @GE4u.",
        S["small"])]

    doc.build(st, onFirstPage=footer(en), onLaterPages=footer(en))
    return {"terms": len(terms), "matching": len(pick), "mcq": len(qpick), "gaps": len(gaps)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="dist/packs")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    bank = gv.load_bank()
    for cid in gv.ORDER:
        f = out / f"GE4u-{cid}-learning-pack.pdf"
        info = build(cid, bank[cid], f)
        print(f.name, info)


if __name__ == "__main__":
    main()
