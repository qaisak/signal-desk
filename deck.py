"""
Build a first-meeting deck from a brief (data/briefs/<slug>.json) on a
proper template. Output docs/briefs/<slug>.pptx, footer marked DRAFT.

Customer-facing slides only: the brief's discovery questions and risks are
for Qais, so they go into the speaker notes of the relevant slides.
"""
import json, re, sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = Path(__file__).parent
OUT = ROOT / "docs" / "briefs"; OUT.mkdir(parents=True, exist_ok=True)
NAVY, INK, MUTED, ACC, SOFT, LINE, WHITE = (RGBColor(0x12, 0x14, 0x3a), RGBColor(0x17, 0x1a, 0x33), RGBColor(0x5d, 0x61, 0x80),
                                            RGBColor(0x4f, 0x46, 0xe5), RGBColor(0xee, 0xed, 0xfb), RGBColor(0xdf, 0xe2, 0xee), RGBColor(0xff, 0xff, 0xff))
W, Hh = 13.333, 7.5


def slug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


class Deck:
    def __init__(self):
        self.p = Presentation(); self.p.slide_width, self.p.slide_height = Inches(W), Inches(Hh)
        self.blank = self.p.slide_layouts[6]; self.n = 0

    def rect(self, s, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
        r = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        r.fill.solid(); r.fill.fore_color.rgb = fill; r.line.fill.background(); r.shadow.inherit = False; return r

    def text(self, s, x, y, w, h, t, size=14, bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font="Calibri", bullets=False, space=4):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
        tf.vertical_anchor = anchor; tf.margin_left = tf.margin_right = Emu(0); tf.margin_top = tf.margin_bottom = Emu(0)
        for i, ln in enumerate(t if isinstance(t, list) else [t]):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.alignment = align; para.space_after = Pt(space)
            run = para.add_run(); run.text = ("•  " + ln) if bullets else ln
            run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = color; run.font.name = font
        return tb

    def slide(self, eyebrow, title, notes=None):
        s = self.p.slides.add_slide(self.blank); self.n += 1
        self.rect(s, 0, 0, W, 0.12, ACC)
        self.text(s, 0.7, 0.45, 12, 0.3, eyebrow.upper(), 10, True, ACC)
        self.text(s, 0.7, 0.75, 11.9, 1.0, title, 26, True, INK)
        self.text(s, 0.7, Hh - 0.45, 8, 0.3, "DRAFT for review  ·  Encord  ·  confidential", 9, False, MUTED)
        self.text(s, W - 1.2, Hh - 0.45, 0.5, 0.3, str(self.n), 9, False, MUTED, PP_ALIGN.RIGHT)
        if notes: s.notes_slide.notes_text_frame.text = notes
        return s


def build(b):
    d = Deck(); name = b["account"]
    # 1 cover
    s = d.p.slides.add_slide(d.blank); d.n += 1
    d.rect(s, 0, 0, 4.6, Hh, NAVY); d.rect(s, 4.6, 0, 0.12, Hh, ACC)
    d.text(s, 0.6, 0.6, 3.5, 0.4, "ENCORD", 12, True, WHITE)
    d.text(s, 0.6, Hh - 1.4, 3.5, 1, [f"Prepared {b['generated']}", "Qais Al-Azkawi", "DRAFT for review"], 10, False, RGBColor(0xb9, 0xbc, 0xdc))
    d.text(s, 5.3, 2.0, 7.4, 1.4, f"Encord x {name}", 40, True, INK)
    d.text(s, 5.3, 3.4, 7.4, 2.2, b["headline"], 18, False, MUTED)
    d.text(s, 5.3, Hh - 1.2, 7.4, 0.5, "A first-meeting point of view. Everything here is our reading of public information; the questions are where we want to be corrected.", 10, False, MUTED)

    # 2 what you build / how we think it flows
    s = d.slide("What we understand", f"What {name} builds, and how we think the data flows",
                notes="Discovery questions to test this:\n" + "\n".join("- " + q for q in b["discovery_questions"]))
    d.text(s, 0.7, 1.9, 5.6, 4.5, b["what_they_build"], 14, False, INK, space=8)
    d.text(s, 6.8, 1.9, 5.8, 0.3, "INFERRED PIPELINE (guesses marked)", 10, True, ACC)
    y = 2.3
    for i, step in enumerate(b["inferred_pipeline"][:6]):
        d.rect(s, 6.8, y, 0.42, 0.42, ACC, MSO_SHAPE.OVAL)
        d.text(s, 6.8, y, 0.42, 0.42, str(i + 1), 12, True, WHITE, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        d.text(s, 7.4, y - 0.02, 5.2, 0.7, step, 10.5, False, INK)
        y += 0.72

    # 3 hypotheses
    s = d.slide("Where we think it hurts", "Three hypotheses, ranked by how sure we are",
                notes="Confidence: " + b["confidence"] + "\nRisks:\n" + "\n".join("- " + r for r in b["risks"]))
    cw = 3.85
    for i, h in enumerate(b["hypotheses"][:3]):
        x = 0.7 + i * (cw + 0.25)
        d.rect(s, x, 1.85, cw, 5.05, SOFT)
        d.rect(s, x, 1.9, cw, 0.08, ACC)
        d.text(s, x + 0.25, 2.15, cw - 0.5, 0.3, f"HYPOTHESIS {i + 1}", 10, True, ACC)
        d.text(s, x + 0.25, 2.45, cw - 0.5, 1.4, h["pain"], 12, True, INK)
        d.text(s, x + 0.25, 3.85, cw - 0.5, 0.3, "WHY WE THINK SO", 9, True, MUTED)
        d.text(s, x + 0.25, 4.1, cw - 0.5, 1.0, h["evidence"], 9.5, False, MUTED)
        d.text(s, x + 0.25, 5.1, cw - 0.5, 0.3, "WHAT ENCORD DOES ABOUT IT", 9, True, MUTED)
        d.text(s, x + 0.25, 5.35, cw - 0.5, 1.5, h["encord_answer"], 9.5, False, INK)

    # 4 ontology
    s = d.slide("A starting ontology", f"What we would label for {name}, and how")
    d.text(s, 0.7, 1.85, 12, 0.4, "A proposal to argue with. The shapes matter: they decide what the model can learn and what the labellers spend time on.", 12, False, MUTED)
    rows = b["ontology"][:8]
    tbl = s.shapes.add_table(len(rows) + 1, 3, Inches(0.7), Inches(2.4), Inches(11.9), Inches(0.4 * (len(rows) + 1))).table
    tbl.columns[0].width, tbl.columns[1].width, tbl.columns[2].width = Inches(3.2), Inches(2.0), Inches(6.7)
    for j, hdr in enumerate(["Class", "Shape", "Why this shape"]):
        c = tbl.cell(0, j); c.text = hdr; c.fill.solid(); c.fill.fore_color.rgb = ACC
        for p in c.text_frame.paragraphs:
            for r in p.runs: r.font.size = Pt(11); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = "Calibri"
    for i, o in enumerate(rows, 1):
        for j, v in enumerate([o["name"], o["shape"], o["why"]]):
            c = tbl.cell(i, j); c.text = v; c.fill.solid(); c.fill.fore_color.rgb = WHITE if i % 2 else SOFT
            for p in c.text_frame.paragraphs:
                for r in p.runs: r.font.size = Pt(10.5); r.font.color.rgb = INK; r.font.name = "Calibri"; r.font.bold = (j == 0)

    # 5 where encord fits + case study
    s = d.slide("Where Encord fits", "Lead with " + " then ".join(b["modules"][:2]) + ", the rest follows")
    MOD = {"Index": "Register the data where it already lives. Embeddings and quality metrics on every frame. Find the frames worth labelling; drop the repeats.",
           "Annotate": "Label video, 3D and images with SAM auto-segmentation and tracking. Ontology, review workflow, managed workforce if needed.",
           "Active": "Import predictions. Accuracy by class, site and condition. Find label errors. Know exactly what to label next.",
           "Agents": "Run your own model as a workflow stage to pre-label and QA, so people adjudicate rather than draw."}
    y = 1.9
    for i, m in enumerate(b["modules"]):
        d.rect(s, 0.7, y, 0.1, 0.9, ACC if i < 2 else LINE)
        d.text(s, 0.95, y, 1.4, 0.3, m, 14, True, INK)
        d.text(s, 0.95, y + 0.32, 5.6, 0.7, MOD[m], 10.5, False, MUTED)
        y += 1.1
    cs = b["case_study"]
    d.rect(s, 7.2, 1.9, 5.4, 4.4, SOFT); d.rect(s, 7.2, 1.9, 5.4, 0.08, ACC)
    d.text(s, 7.45, 2.15, 5, 0.3, "CLOSEST CASE STUDY", 10, True, ACC)
    d.text(s, 7.45, 2.45, 5, 0.5, cs["name"], 20, True, INK)
    d.text(s, 7.45, 3.0, 5, 0.9, cs["numbers"], 14, True, ACC)
    d.text(s, 7.45, 3.9, 5, 2.3, cs["why_it_matches"], 11, False, INK)
    d.text(s, 0.7, 6.5, 12, 0.4, "Data stays in your bucket. SOC2 Type II, HIPAA, GDPR. Everything the UI does, the SDK does.", 10, False, MUTED)

    # 6 proof of value
    s = d.slide("Proposed next step", "A two-week proof of value on one site's data")
    steps = b["proof_of_value"][:5]; y = 1.95
    for i, st in enumerate(steps):
        d.rect(s, 0.7, y + 0.05, 0.5, 0.5, ACC, MSO_SHAPE.ROUNDED_RECTANGLE)
        d.text(s, 0.7, y + 0.05, 0.5, 0.5, str(i + 1), 13, True, WHITE, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
        d.text(s, 1.4, y, 11.2, 0.85, st, 11.5, False, INK)
        y += 0.9
    # 7 close
    s = d.slide("Let's test it", "What we'd like to learn from you")
    d.text(s, 0.7, 1.9, 7.2, 4.5, b["discovery_questions"][:5], 14, False, INK, bullets=True, space=10)
    d.rect(s, 8.4, 1.9, 4.2, 2.6, NAVY)
    d.text(s, 8.7, 2.15, 3.7, 0.3, "CONTACT", 10, True, RGBColor(0xb9, 0xbc, 0xdc))
    d.text(s, 8.7, 2.5, 3.7, 1.8, ["Qais Al-Azkawi", "Commercial Associate, Encord", "qaisqas@gmail.com"], 13, False, WHITE, space=6)
    path = OUT / f"{slug(name)}.pptx"; d.p.save(path); return path


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for f in sorted((ROOT / "data" / "briefs").glob("*.json")):
        b = json.load(open(f, encoding="utf-8"))
        if only and b["account"] != only: continue
        print(b["account"], "->", build(b).relative_to(ROOT))
