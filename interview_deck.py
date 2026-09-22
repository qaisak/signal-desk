"""Six slides: what Qais built since the Jumpstart intro. Links are live hyperlinks."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from deck import Deck, INK, MUTED, ACC, SOFT, LINE, WHITE, NAVY, W, Hh
from pptx.util import Inches, Pt
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

ROOT = Path(__file__).parent
DESK = "https://country-renewable-sells-pic.trycloudflare.com"
PAGES = "https://qaisak.github.io/signal-desk/"
REPO = "https://github.com/qaisak/signal-desk"
FUNNEL = ROOT.parent / "encord-dexory" / "outputs" / "fig_funnel.png"
UMAP = ROOT.parent / "encord-dexory" / "outputs" / "fig_umap.png"
brief = json.load(open(ROOT / "data" / "briefs" / "dexory.json", encoding="utf-8"))

d = Deck()

def link(slide, x, y, w, h, label, url, size=13):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    r = tf.paragraphs[0].add_run(); r.text = label; r.font.size = Pt(size); r.font.bold = True; r.font.name = "Calibri"; r.font.color.rgb = ACC
    r.hyperlink.address = url; return tb

# 1 cover
s = d.p.slides.add_slide(d.blank); d.n += 1
d.rect(s, 0, 0, 4.6, Hh, NAVY); d.rect(s, 4.6, 0, 0.12, Hh, ACC)
d.text(s, 0.6, 0.6, 3.5, 0.4, "QAIS AL-AZKAWI", 12, True, WHITE)
d.text(s, 0.6, Hh - 1.2, 3.5, 0.8, ["Commercial Associate (UK)", "September 2026"], 10, False, RGBColor(0xb9, 0xbc, 0xdc))
d.text(s, 5.3, 2.0, 7.4, 1.4, "What I built since our intro", 40, True, INK)
d.text(s, 5.3, 3.5, 7.4, 1.6, "Two things: a proof that Encord's curation story holds on a real target's kind of data, and the desk I'd use to work the UK physical-AI territory.", 18, False, MUTED)
link(s, 5.3, 5.4, 7.4, 0.4, "Open Signal Desk (live)  →  " + DESK, DESK, 13)
link(s, 5.3, 5.8, 7.4, 0.4, "Public copy  →  " + PAGES, PAGES, 11)

# 2 the account
s = d.slide("Part one: a target and a proof", "Dexory: warehouse robots that scan the same racking every day")
d.text(s, 0.7, 1.9, 5.8, 3, ["• Autonomous robots scan aisles daily; operators get live inventory and damage alerts",
                               "• $165m Series C (Oct 2025 + Mar 2026)",
                               "• Storage Health launched Feb 2026: damaged stock, leaning pallets. New classes, no labels yet",
                               "• Their data engineer ad: modelling perception accuracy per site against customer SLAs"], 14, False, INK, space=8)
d.rect(s, 7.0, 1.9, 5.6, 4.4, SOFT); d.rect(s, 7.0, 1.9, 5.6, 0.08, ACC)
d.text(s, 7.25, 2.15, 5.1, 0.3, "THE PROBLEM, IN ONE LINE", 10, True, ACC)
d.text(s, 7.25, 2.5, 5.1, 1.6, "Every frame is nearly yesterday's frame. Labelling all of it burns budget, and the rare damaged pallet gets lost in the pile.", 16, True, INK)
d.text(s, 7.25, 4.3, 5.1, 1.8, "Same shape as Automotus (fixed street cameras, same scenes): they solved it by curating, not by labelling more. +20% mAP, 35% smaller dataset, 33% lower labelling cost.", 12, False, MUTED)

# 3 what I did
s = d.slide("What I did", "Rebuilt the Encord curation approach on a proxy of their data")
steps = [("Proxy stream", "450 public shelf photos, 3 robot passes each with camera shift and exposure drift, 10% blurred or dark. 1,350 frames, ground truth logged."),
         ("Quality gates", "Exposure and blur (variance of Laplacian). Classical CV, milliseconds per frame."),
         ("De-duplication", "CLIP embeddings; drop anything above 0.965 cosine similarity to a frame already kept."),
         ("Diversity", "Farthest-point sampling so the kept set spans the distribution instead of the common racks."),
         ("Fair test", "YOLOv8n trained on 150 curated frames vs 150 random, judged on 80 held-out racks.")]
y = 1.9
for i, (t, body) in enumerate(steps):
    d.rect(s, 0.7, y, 0.42, 0.42, ACC, MSO_SHAPE.OVAL); d.text(s, 0.7, y, 0.42, 0.42, str(i + 1), 12, True, WHITE, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
    d.text(s, 1.3, y - 0.02, 1.6, 0.4, t, 13, True, INK); d.text(s, 2.9, y - 0.02, 4.0, 0.9, body, 10.5, False, MUTED); y += 0.95
if FUNNEL.exists(): s.shapes.add_picture(str(FUNNEL), Inches(7.2), Inches(1.9), width=Inches(5.5))
d.text(s, 7.2, 4.95, 5.5, 0.4, "Curation funnel on the proxy stream", 10, False, MUTED)

# 4 result
s = d.slide("Result", "Label 61% less, keep 95% of racks, get a better model")
for i, (big, small) in enumerate([("61%", "fewer frames to label\n1,350 → 532"), ("95%", "of racks still represented\n427 of 450"), ("0.48 vs 0.43", "mAP50, curated vs random\nsame budget, held-out racks"), ("71% / 81%", "degraded-frame recall / precision\nscored against ground truth")]):
    x = 0.7 + i * 3.1
    d.rect(s, x, 1.9, 2.9, 2.3, SOFT); d.rect(s, x, 1.9, 2.9, 0.08, ACC)
    d.text(s, x + 0.2, 2.15, 2.5, 0.8, big, 30, True, ACC); d.text(s, x + 0.2, 3.05, 2.5, 1.1, small, 11, False, INK)
d.text(s, 0.7, 4.5, 12, 0.4, "SO WHAT", 10, True, ACC)
d.text(s, 0.7, 4.8, 12, 1.4, "The pitch to Dexory is not 'label more'. It is 'label a third less and prove per-site accuracy', which is the number their own job ad says they have promised customers. Honest caveats: re-passes were simulated so real de-dup will be lower; the model test is directional, not a benchmark.", 14, False, INK)
d.text(s, 0.7, 6.3, 12, 0.4, "Brief and 7-slide deck for Dexory written from their site, job ads and this month's signals. Confidence: medium, because the pain is inferred, not stated.", 11, False, MUTED)

# 5 signal desk
s = d.slide("Part two: the desk I'd work from", "Signal Desk: the account-watching part of the job, automated")
d.text(s, 0.7, 1.9, 6.0, 4.4, ["• 21 UK physical-AI and medical accounts, scored fit × momentum",
                               "• Signals every morning, no API keys: news, their own job boards (Greenhouse, Lever, Ashby, Workable), arXiv, Hacker News",
                               "• Why-now line and draft opener per account; lead-with module (Index, Annotate, Active, Agents)",
                               "• Team layer: claim before you call, log every touch, follow-ups set automatically, morning digest",
                               "• Request a brief: reads their site and job ads, writes a first-meeting point of view and deck in two minutes",
                               "• Python, Claude Opus 5 for briefs, no frameworks. A working prototype, not a product"], 13, False, INK, space=7)
d.rect(s, 7.2, 1.9, 5.4, 4.4, SOFT); d.rect(s, 7.2, 1.9, 5.4, 0.08, ACC)
d.text(s, 7.45, 2.15, 5, 0.3, "OPEN IT", 10, True, ACC)
link(s, 7.45, 2.5, 5, 0.5, "Live desk (team mode)  →", DESK, 20)
d.text(s, 7.45, 3.05, 5, 0.6, DESK, 10, False, MUTED)
d.text(s, 7.45, 3.6, 5, 0.4, "sign in with your name · password: encord-desk-2026", 11, True, INK)
link(s, 7.45, 4.3, 5, 0.4, "Public read-only copy  →", PAGES, 14)
d.text(s, 7.45, 4.65, 5, 0.4, PAGES, 10, False, MUTED)
link(s, 7.45, 5.3, 5, 0.4, "Code on GitHub  →", REPO, 14)
d.text(s, 7.45, 5.65, 5, 0.4, REPO, 10, False, MUTED)

# 6 what I'd do with it
s = d.slide("What I'd do in the first month", "Work the list, learn the product, fix the facts")
d.text(s, 0.7, 1.9, 6.0, 4.5, ["1. Learn the product hands-on and shadow every call I can",
                               "2. Work the top of the list with the team's messaging, not mine: Dexory, Oxa, Humanoid, Proximie",
                               "3. Three questions on every first call: what fraction of frames reach a labeller, who reviews edge cases, who owns the budget",
                               "4. After each call, correct the account's facts so the next brief is smarter",
                               "5. Report weekly: conversations, meetings, what the market is saying"], 14, False, INK, space=9)
d.rect(s, 7.2, 1.9, 5.4, 3.2, SOFT); d.rect(s, 7.2, 1.9, 5.4, 0.08, ACC)
d.text(s, 7.45, 2.15, 5, 0.3, "WHAT I WANT TO LEARN FROM YOU", 10, True, ACC)
d.text(s, 7.45, 2.5, 5, 2.5, ["• What does a good week look like for a CA?", "• Which vertical is the push post Series C?", "• What separated the CAs who progressed fastest?"], 13, False, INK, space=8)
d.text(s, 7.45, 5.4, 5, 0.6, "Qais Al-Azkawi · qaisqas@gmail.com", 13, True, INK)

for sl in d.p.slides:
    for sh in sl.shapes:
        if sh.has_text_frame and sh.text_frame.text.startswith("DRAFT for review"):
            for r in sh.text_frame.paragraphs[0].runs: r.text = "Qais Al-Azkawi  ·  Encord Commercial Associate  ·  what I built since our intro"
out = ROOT.parent / "OneDrive" / "Career" / "Encord-Interview-What-I-Built.pptx"
d.p.save(out); print(out)
