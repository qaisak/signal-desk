"""
Score every account on "why now", rank, draft an opener, and render
dashboard.html (self-contained, works offline, state kept in the browser).

Score = fit (1-5, static, from accounts.csv)  x  momentum (0-100, from signals)

Momentum points, with recency decay (full value <14d, half <30d, quarter <60d):
  funding headline        30 (max one)
  launch / partnership    12 each, cap 24
  CV / ML job posting     8 each, cap 32
  arXiv paper             6 each, cap 12
  HN story                3 each, cap 6
  plain news              2 each, cap 10
  new since last run      +5 bonus if any signal first_seen today
"""
import json, html, re
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent
import csv
store = json.load(open(ROOT / "data" / "signals.json", encoding="utf-8"))
# account fields always come from the current accounts.csv, signals from the last pull
for a in csv.DictReader(open(ROOT / "accounts.csv", encoding="utf-8")):
    store.setdefault(a["name"], dict(signals=[], fetched="")).update(a)
TODAY = date.today()
W = dict(funding=(30, 30), launch=(12, 24), job=(8, 32), paper=(6, 12), hn=(3, 6), news=(2, 10))


def decay(d):
    if not d: return 1.0
    age = (TODAY - date.fromisoformat(d)).days
    return 1.0 if age < 14 else 0.5 if age < 30 else 0.25


def score(acc):
    pts = {k: 0.0 for k in W}
    for s in acc["signals"]:
        w, cap = W.get(s["type"], (0, 0))
        pts[s["type"]] = min(cap, pts[s["type"]] + w * decay(s.get("date")))
    momentum = min(100, sum(pts.values()) + (5 if any(s["first_seen"] == TODAY.isoformat() for s in acc["signals"]) else 0))
    return round(momentum), pts


def why_now(acc):
    top = []
    for t in ("funding", "launch"):
        c = sorted([s for s in acc["signals"] if s["type"] == t], key=lambda s: s.get("date", ""), reverse=True)
        if c: top = c[:1]; break
    jobs = [s for s in acc["signals"] if s["type"] == "job"]
    parts = []
    if top: parts.append(f"{top[0]['title'].split(' - ')[0]} ({top[0]['date']})")
    if jobs: parts.append(f"hiring {len(jobs)} ML/CV role{'s' if len(jobs) > 1 else ''}: {jobs[0]['title']}")
    papers = [s for s in acc["signals"] if s["type"] == "paper"]
    if papers and not parts: parts.append(f"published: {papers[0]['title'][:70]}")
    return "; ".join(parts) or "quiet: nurture"


MEDICAL = {"Surgical robotics", "Surgical video", "Medical imaging", "Digital pathology"}
VIDEO_3D = {"Warehouse robotics", "Industrial autonomy", "Humanoid robotics", "Autonomous driving", "Drones", "Drone inspection", "Defence AI", "Teleoperation", "Robot navigation"}

def product(acc, pts):
    """Which Encord module leads the conversation, and the one-line angle."""
    v = acc["vertical"]; jobs = pts["job"] > 0; funded = pts["funding"] > 0
    if v in MEDICAL:
        return ("Annotate (DICOM / video) + Active", "Expert review workflows for clinicians, DICOM and surgical video native, label QA before regulatory submission")
    if v == "Autonomous driving":
        return ("Active (model evaluation)", "They have labelling covered in-house; sell evaluation: slice model failures by scene metric, find what to label next")
    if v in VIDEO_3D and (jobs or funded):
        return ("Index (curation) then Annotate", "Fleet data is mostly re-passes; curate first, then label with SAM and tracking on video / point clouds")
    if v in VIDEO_3D:
        return ("Annotate (video / 3D)", "Native video and point-cloud labelling with tracking; start with a labelling pilot")
    if v == "Agri robotics":
        return ("Annotate + Agents", "Fine-grained grading labels in messy lighting; agent pre-labelling with their own model cuts human time")
    if v == "Lab automation":
        return ("Annotate (images) + Agents", "Bench-camera QC and plate imaging; small team, so pre-labelling agents matter more than curation")
    return ("Index + Annotate", "Standard land: curate, label, evaluate")


def opener(acc, why):
    hook = why.split(";")[0] if why != "quiet: nurture" else f"your work on {acc['vertical'].lower()}"
    return (f"Hi [name],\n\nSaw {hook}. Teams at that stage usually hit the same wall: far more frames than anyone can label, "
            f"and most of them near-duplicates.\n\nEncord's curation layer picks the frames worth labelling before a human touches them. "
            f"On a camera-fleet customer it cut the dataset 35% and lifted mAP 20%.\n\nWorth 20 minutes to see if it applies to {acc['name']}?\n\nQais")


rows = []
for name, acc in store.items():
    m, pts = score(acc)
    why = why_now(acc)
    prod, angle = product(acc, pts)
    rows.append(dict(name=name, brief_flag=acc.get("brief", "no"), verified=acc.get("verified", "no"), blurb=acc.get("blurb", ""), data=acc.get("data", ""), persona=acc.get("persona", ""), contact=acc.get("contact", ""), product=prod, angle=angle, domain=acc["domain"], vertical=acc["vertical"], hq=acc["hq"], fit=int(acc["fit"]),
                     momentum=m, total=int(acc["fit"]) * m, pts={k: round(v) for k, v in pts.items()},
                     why=why, opener=opener(acc, why), notes=acc["notes"],
                     new=sum(1 for s in acc["signals"] if s["first_seen"] == TODAY.isoformat()),
                     signals=sorted(acc["signals"], key=lambda s: s.get("date", ""), reverse=True)))
rows.sort(key=lambda r: -r["total"])
import re as _re
def _slug(n): return _re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")
for r in rows:
    bf = ROOT / "data" / "briefs" / f"{_slug(r['name'])}.json"
    if bf.exists() and (ROOT / "docs" / "briefs" / f"{_slug(r['name'])}.pptx").exists():
        b = json.load(open(bf, encoding="utf-8"))
        r["brief"] = dict(headline=b["headline"], confidence=b["confidence"], generated=b["generated"], hypotheses=[h["pain"] for h in b["hypotheses"]],
                          questions=b["discovery_questions"], risks=b["risks"], email=b["opener_email"], modules=b["modules"], deck=f"briefs/{_slug(r['name'])}.pptx")
        r["opener"] = b["opener_email"]
        r["deck_lock"] = ""
    else:
        r["brief"] = None
        r["deck_lock"] = ("brief flagged; it is written on the next run (needs the API key)" if r.get("brief_flag", "").lower() == "yes"
                          else "set brief=yes in accounts.csv once you have decided to work this account; a reasoned brief and deck are generated on the next run")
json.dump(rows, open(ROOT / "data" / "ranked.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)

# ------------------------------------------------------------------ html
import base64
DATA = json.dumps(rows, ensure_ascii=False).replace("</", "<" + chr(92) + "/")
files = {}
for r in rows:
    if r.get("brief"):
        pp = ROOT / "docs" / "briefs" / f"{_slug(r['name'])}.pptx"
        if pp.exists() and pp.stat().st_size < 400_000:
            files[_slug(r["name"])] = base64.b64encode(pp.read_bytes()).decode()
FILES = json.dumps(files)
page = (ROOT / "template.html").read_text(encoding="utf-8").replace("__DATA__", DATA).replace("__FILES__", FILES).replace("__DATE__", TODAY.isoformat())
(ROOT / "dashboard.html").write_text(page, encoding="utf-8")   # fragment: the claude.ai artifact wraps it
standalone = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">' + page + "</html>")
(ROOT / "docs").mkdir(exist_ok=True)
(ROOT / "docs" / "index.html").write_text(standalone, encoding="utf-8")
(ROOT / "index.html").write_text(standalone.replace('"deck":"briefs/', '"deck":"docs/briefs/'), encoding="utf-8")   # repo root, for Pages set to /

# ------------------------------------------------------------------ daily digest (markdown + optional Slack)
NL = chr(10)
hot = [r for r in rows if r["momentum"] >= 50][:6]
new_sig = [(r, [s for s in r["signals"] if s["first_seen"] == TODAY.isoformat()]) for r in rows]
new_sig = [(r, n) for r, n in new_sig if n]
md = [f"# Signal Desk digest, {TODAY.isoformat()}", ""]
md += ["## Hot accounts"] + [f"- **{r['name']}** ({r['total']}): {r['why']}" for r in hot] + [""]
if new_sig:
    md += ["## New signals since yesterday"]
    for r, n in new_sig[:10]:
        md += [f"- **{r['name']}**: " + "; ".join(f"[{s['type']}] {s['title'][:80]}" for s in n[:3])]
    md += [""]
briefed = [r for r in rows if r.get("brief")]
if briefed:
    md += ["## Briefs ready"] + [f"- {r['name']} ({r['brief']['confidence']} confidence, {r['brief']['generated']})" for r in briefed] + [""]
md += ["Open the desk: https://qaisak.github.io/signal-desk/"]
(ROOT / "docs" / "digest.md").write_text(NL.join(md), encoding="utf-8")
import os, requests
if os.environ.get("SLACK_WEBHOOK"):
    txt = f"*Signal Desk, {TODAY.isoformat()}*" + NL + NL.join(f"• *{r['name']}* ({r['total']}): {r['why'][:120]}" for r in hot)
    if new_sig: txt += NL + NL + "*New signals:* " + ", ".join(r["name"] for r, _ in new_sig[:8])
    txt += NL + "<https://qaisak.github.io/signal-desk/|open the desk>"
    try: requests.post(os.environ["SLACK_WEBHOOK"], json={"text": txt}, timeout=15)
    except requests.RequestException: pass
print(f"ranked {len(rows)} accounts -> dashboard.html, docs/index.html, index.html, docs/digest.md ({len(files)} decks embedded)")
for r in rows[:8]:
    print(f"  {r['total']:4d}  {r['name']:26s} fit {r['fit']}  mom {r['momentum']:3d}  {r['why'][:70]}")
