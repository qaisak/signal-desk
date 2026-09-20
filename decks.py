"""
Generate a short outreach deck (.pptx) per account, but only when a human has
set verified=yes in accounts.csv AND there is a fresh strong signal. Writes to
docs/decks/<slug>.pptx and records the gate result in data/decks.json so the
dashboard can show a button or a lock with the reason.
"""
import json, re
from datetime import date
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

ROOT = Path(__file__).parent
OUT = ROOT / "docs" / "decks"; OUT.mkdir(parents=True, exist_ok=True)
rows = json.load(open(ROOT / "data" / "ranked.json", encoding="utf-8"))
TODAY = date.today().isoformat()

INK, MUTED, ACCENT, LINE = RGBColor(0x17, 0x1a, 0x33), RGBColor(0x5d, 0x61, 0x80), RGBColor(0x4f, 0x46, 0xe5), RGBColor(0xdf, 0xe2, 0xee)
MODULE = {
    "Index": "Index: connect your storage, get embeddings and quality metrics on every frame, filter to the frames worth labelling",
    "Annotate": "Annotate: video, 3D and DICOM native labelling with SAM auto-segmentation, tracking and review workflows",
    "Active": "Active: import model predictions, slice failures by scene and data metric, decide what to label next",
    "Agents": "Agents: run your own model or a foundation model as a workflow stage to pre-label and QA",
}


def slug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


def gate(r):
    if r.get("verified", "").lower() != "yes":
        return False, "set verified=yes in accounts.csv once product, problem and fit are confirmed"
    strong = [s for s in r["signals"] if s["type"] in ("funding", "launch", "job")]
    if not strong:
        return False, "verified, but no fresh funding, launch or ML hiring signal to anchor the deck"
    if not (r.get("blurb") and r.get("data")):
        return False, "verified, but blurb or data line is empty"
    return True, ""


def text(slide, x, y, w, h, s, size=18, bold=False, color=INK, align=PP_ALIGN.LEFT):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    lines = s if isinstance(s, list) else [s]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ln; p.alignment = align; p.space_after = Pt(6)
        for run in p.runs: run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = color; run.font.name = "Calibri"
    return tb


def rule(slide, y):
    ln = slide.shapes.add_shape(1, Inches(0.6), Inches(y), Inches(12.1), Emu(12700)); ln.fill.solid(); ln.fill.fore_color.rgb = LINE; ln.line.fill.background()


def header(slide, eyebrow, title):
    text(slide, 0.6, 0.35, 12, 0.4, eyebrow.upper(), 11, True, ACCENT)
    text(slide, 0.6, 0.7, 12, 1.0, title, 30, True)
    rule(slide, 1.65)


def build(r):
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    strong = sorted([s for s in r["signals"] if s["type"] in ("funding", "launch", "job")], key=lambda s: s.get("date", ""), reverse=True)
    modules = [m for m in MODULE if m in r["product"]]

    # 1 title
    s = prs.slides.add_slide(blank)
    text(s, 0.6, 2.4, 12, 1.2, f"Encord x {r['name']}", 44, True)
    text(s, 0.6, 3.5, 12, 0.8, r["data"].split(";")[0], 20, False, MUTED)
    text(s, 0.6, 6.5, 12, 0.5, f"Prepared {TODAY} · Qais Al-Azkawi, Encord", 12, False, MUTED)

    # 2 what we understand
    s = prs.slides.add_slide(blank); header(s, "What we understand about you", r["blurb"])
    text(s, 0.6, 1.9, 6, 0.4, "Recent signals", 14, True, ACCENT)
    text(s, 0.6, 2.3, 6.2, 4, [f"• {x['title'].split(' - ')[0][:90]}  ({x.get('date') or 'open role'})" for x in strong[:6]], 14)
    text(s, 7.2, 1.9, 5.5, 0.4, "Who we think owns this", 14, True, ACCENT)
    text(s, 7.2, 2.3, 5.5, 2, [r["persona"], r.get("contact") or "(contact to confirm)"], 14, False, MUTED)

    # 3 the data problem
    s = prs.slides.add_slide(blank); header(s, "The data problem", "More frames than anyone should label")
    text(s, 0.6, 1.9, 12, 1.2, r["data"], 20)
    text(s, 0.6, 3.4, 12, 3, ["• Most of the stream is near-duplicate: the same scene seen again", "• Labelling everything spends budget on redundancy and still misses the rare cases", "• New model classes need fresh labels fast, with expert review where it matters", "• Nobody can tell which labelled data actually moved the model"], 16, False, MUTED)

    # 4 how Encord helps
    s = prs.slides.add_slide(blank); header(s, "Where Encord fits", f"Lead with {r['product']}")
    text(s, 0.6, 1.9, 12, 1, r["angle"], 18)
    text(s, 0.6, 3.1, 12, 3.5, [f"• {MODULE[m]}" for m in modules] or ["• " + MODULE["Index"], "• " + MODULE["Annotate"]], 15, False, MUTED)
    text(s, 0.6, 6.3, 12, 0.6, "Data stays in your bucket. SOC2 Type II, HIPAA, GDPR. SDK for everything the UI does.", 12, False, MUTED)

    # 5 proof
    s = prs.slides.add_slide(blank); header(s, "Proof", "Label less, get a better model")
    for i, (big, small) in enumerate([("20%", "mAP uplift, Automotus street cameras"), ("35%", "smaller dataset to annotate"), ("33%", "lower labelling cost"), ("61%", "fewer frames on a warehouse-robot proxy stream, 95% rack coverage kept")]):
        text(s, 0.6 + i * 3.1, 2.0, 2.9, 1, big, 40, True, ACCENT); text(s, 0.6 + i * 3.1, 3.0, 2.9, 1.5, small, 13, False, MUTED)
    text(s, 0.6, 5.2, 12, 1, "Automotus: Encord customer story. Proxy stream: public shelf imagery with simulated robot re-passes, curated with quality gates, CLIP de-duplication and diversity sampling; YOLOv8n trained on the curated pick beat a random pick 0.48 vs 0.43 mAP50 at equal budget.", 11, False, MUTED)

    # 6 next step
    s = prs.slides.add_slide(blank); header(s, "Proposed next step", "Two-week proof of value on one site's data")
    text(s, 0.6, 1.9, 12, 4, ["1. You share one week of raw data from one site (stays in your storage)", "2. We run curation and load the kept frames into Encord with your ontology", "3. Your team labels a sample with assisted tools; we measure frames saved, coverage and time to first model", "4. Success criteria agreed before we start"], 17)
    text(s, 0.6, 6.2, 12, 0.8, "Qais Al-Azkawi · qaisqas@gmail.com", 14, True)
    path = OUT / f"{slug(r['name'])}.pptx"; prs.save(path); return path


status = {}
for r in rows:
    ok, why = gate(r)
    if ok:
        p = build(r); status[r["name"]] = dict(ok=True, path=f"decks/{p.name}", built=TODAY)
    else:
        status[r["name"]] = dict(ok=False, reason=why)
json.dump(status, open(ROOT / "data" / "decks.json", "w", encoding="utf-8"), indent=1)
print(f"decks built: {sum(1 for v in status.values() if v['ok'])} / {len(status)}")
for n, v in status.items():
    if v["ok"]: print("  ", n, "->", v["path"])
