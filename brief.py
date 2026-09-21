"""
Write a first-meeting brief for each account flagged brief=yes in accounts.csv.

Not a template. For every flagged account we gather what we actually know
(their site, their open ML/CV job ads, this month's signals, our own notes),
hand it to Claude Opus 5 with the Encord product facts, and ask for an
account-specific point of view: what their pipeline probably looks like,
where it hurts, an ontology for THEIR objects, which case study matches,
and a proof-of-value plan sized to them. Output: data/briefs/<slug>.json,
marked DRAFT until a human reads it.

Run:  python brief.py            # all flagged accounts without a fresh brief
      python brief.py Dexory     # one account, regenerate
Needs ANTHROPIC_API_KEY in the environment or in ../hardlaunch-task/.env.
"""
import csv, json, os, re, sys, html as htmllib
from datetime import date
from pathlib import Path
import requests, anthropic

ROOT = Path(__file__).parent
BRIEFS = ROOT / "data" / "briefs"; BRIEFS.mkdir(parents=True, exist_ok=True)
TODAY = date.today().isoformat()
H = {"User-Agent": "Mozilla/5.0 (signal-desk; personal research tool)"}

# key: env first, then the local .env used for prototypes
if not os.environ.get("ANTHROPIC_API_KEY"):
    envf = ROOT.parent / "hardlaunch-task" / ".env"
    if envf.exists():
        for line in envf.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip().strip('"')

ENCORD_FACTS = """
Encord (London, founded 2020, YC, $110m raised incl. $60m Series C Feb 2026 led by Wellington) is an AI data
development platform for computer vision and physical AI. Four modules:
- Index: register data from the customer's own S3/GCS/Azure (data never moves); automatic embeddings and quality
  metrics per frame (brightness, sharpness, uniqueness); filter, embedding plot, similarity search; build Collections.
- Annotate: labelling for images, native video, 3D point clouds / LIDAR, DICOM/NIfTI medical, audio, text. Ontology
  (objects: box, polygon, polyline, keypoint, bitmask, rotatable box; attributes; frame classifications).
  Workflows (annotate -> review -> complete, sampled review, routing). SAM 3 auto-segmentation, object tracking across
  video, interpolation. Managed labelling workforce available. Export via SDK.
- Active: label validation (find label errors with data/label/model metrics) and model evaluation (import predictions,
  mAP/mAR/F1/PR curves, confusion matrix, slice by class, IoU threshold, and any data metric; metric-to-failure
  correlation tells you which data to label next).
- Agents: run the customer's own model or a foundation model as a workflow stage for pre-labelling and QA.
Security: SOC2 Type II, HIPAA, GDPR; hosted on GCP; data stays in the customer's bucket. Everything scriptable via SDK.
Named customers: Woven by Toyota, Skydio, Synthesia, Philips, Tractable, Automotus, Harvard Medical School / MGH.
Case studies: Automotus (street cameras): +20% mAP, 35% smaller dataset, 33% lower labelling cost after curating with
Encord. Harvard Medical School & MGH: annotation time from days to minutes on medical imaging. Encord's own claim:
60-80% labelling cost reduction on high-complexity use cases with automation + active learning.
Our own proof: on a simulated warehouse-robot stream (public shelf images, 3 passes per rack, 10% degraded frames)
quality gates + CLIP de-duplication + diversity sampling cut frames to label by 61% keeping 95% of racks; YOLOv8n
trained on the curated pick scored 0.48 mAP50 vs 0.43 on a random pick of equal size.
"""

SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["headline", "what_they_build", "inferred_pipeline", "hypotheses", "ontology", "modules", "case_study",
                 "proof_of_value", "discovery_questions", "risks", "opener_email", "confidence"],
    "properties": {
        "headline": {"type": "string", "description": "One sentence, the point of view for this account, no jargon"},
        "what_they_build": {"type": "string", "description": "2-3 sentences, specific to them, what the product does and who pays"},
        "inferred_pipeline": {"type": "array", "items": {"type": "string"}, "description": "4-6 steps: how we think data flows from sensor to model today, flagging guesses"},
        "hypotheses": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["pain", "evidence", "encord_answer"],
                       "properties": {"pain": {"type": "string", "description": "max 35 words"}, "evidence": {"type": "string", "description": "which signal, job ad or site text supports it, max 35 words"}, "encord_answer": {"type": "string", "description": "max 55 words, name the module"}}},
                       "description": "exactly 3, ranked by confidence"},
        "ontology": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["name", "shape", "why"],
                     "properties": {"name": {"type": "string"}, "shape": {"type": "string", "enum": ["bounding box", "polygon", "polyline", "keypoint", "bitmask", "3D cuboid", "frame classification"]}, "why": {"type": "string", "description": "max 20 words"}}},
                     "description": "5-8 label classes for THEIR objects and modalities"},
        "modules": {"type": "array", "items": {"type": "string", "enum": ["Index", "Annotate", "Active", "Agents"]}, "description": "which Encord modules to lead with, in order"},
        "case_study": {"type": "object", "additionalProperties": False, "required": ["name", "why_it_matches", "numbers"],
                       "properties": {"name": {"type": "string"}, "why_it_matches": {"type": "string"}, "numbers": {"type": "string"}}},
        "proof_of_value": {"type": "array", "items": {"type": "string"}, "description": "4-5 steps for a two-week POV on their data, with success metrics"},
        "discovery_questions": {"type": "array", "items": {"type": "string"}, "description": "5 questions for the first call that test the hypotheses"},
        "risks": {"type": "array", "items": {"type": "string"}, "description": "2-4 reasons this deal might not happen (in-house tooling, procurement, data access, competitor)"},
        "opener_email": {"type": "string", "description": "under 90 words, plain, one specific hook from the evidence, one ask, signed Qais"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"], "description": "how sure we are about the pain, given the evidence"},
    },
}


def fetch_text(url, limit=6000):
    try:
        r = requests.get(url, headers=H, timeout=20)
        if r.status_code != 200: return ""
        t = re.sub(r"<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", r.text, flags=re.S | re.I)
        t = re.sub(r"<[^>]+>", " ", t); t = htmllib.unescape(re.sub(r"\s+", " ", t)).strip()
        return t[:limit]
    except requests.RequestException:
        return ""


def context_for(acc, signals):
    site = fetch_text(f"https://{acc['domain']}", 5000)
    jobs = [s for s in signals if s["type"] == "job"][:3]
    job_text = "\n\n".join(f"JOB AD: {j['title']} ({j.get('loc', '')})\n{fetch_text(j['url'], 3500)}" for j in jobs)
    sigs = "\n".join(f"- [{s['type']}] {s.get('date', '')} {s['title']}" for s in signals[:25])
    return f"""ACCOUNT: {acc['name']} ({acc['domain']}), {acc['vertical']}, {acc['hq']}
OUR NOTES: {acc['notes']}
WHAT THEY BUILD (our summary): {acc['blurb']}
DATA WE THINK THEY HAVE (our guess): {acc['data']}
TARGET PERSONA: {acc['persona']}   CONTACT: {acc.get('contact') or 'unknown'}

RECENT SIGNALS:
{sigs or '- none in window'}

WEBSITE TEXT (first 5000 chars):
{site or '(could not fetch)'}

{job_text or 'OPEN ML/CV JOB ADS: none found'}"""


def write_brief(client, acc, signals):
    system = ("You are a senior solutions consultant at Encord preparing a first-meeting brief for a Commercial Associate. "
              "Be specific to this account; if the evidence is thin, say so and lower confidence rather than inventing. "
              "Never claim Encord features not listed. Prefer their vocabulary (from the site and job ads) over ours. "
              "British English. No em dashes anywhere.\n\nENCORD FACTS:\n" + ENCORD_FACTS)
    with client.messages.stream(
        model="claude-opus-5", max_tokens=16000,
        thinking={"type": "adaptive"}, output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
        system=system,
        messages=[{"role": "user", "content": "Write the brief for this account.\n\n" + context_for(acc, signals)}],
    ) as stream:
        resp = stream.get_final_message()
    if resp.stop_reason == "refusal":
        raise RuntimeError(f"refused: {resp.stop_details}")
    text = next(b.text for b in resp.content if b.type == "text")
    brief = json.loads(text)
    brief.update(account=acc["name"], generated=TODAY, status="DRAFT: review before sending",
                 signals_used=len(signals), usage=dict(input=resp.usage.input_tokens, output=resp.usage.output_tokens))
    return brief


def slug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    accounts = list(csv.DictReader(open(ROOT / "accounts.csv", encoding="utf-8")))
    store = json.load(open(ROOT / "data" / "signals.json", encoding="utf-8"))
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("no ANTHROPIC_API_KEY; skipping briefs"); return
    client = anthropic.Anthropic()
    for acc in accounts:
        if only and acc["name"] != only: continue
        if only and acc.get("brief", "").lower() != "yes": continue   # explicit name but not flagged: nothing to do
        if not only and acc.get("brief", "").lower() != "yes": continue
        out = BRIEFS / f"{slug(acc['name'])}.json"
        if not only and out.exists():
            age = (date.today() - date.fromisoformat(json.load(open(out, encoding="utf-8")).get("generated", "2000-01-01"))).days
            if age < 7: print(f"{acc['name']:26s} brief is {age}d old, keeping"); continue
        print(f"{acc['name']:26s} gathering context and writing brief...", flush=True)
        try:
            brief = write_brief(client, acc, store.get(acc["name"], {}).get("signals", []))
        except anthropic.RateLimitError:
            print("  rate limited, try later"); continue
        except anthropic.APIStatusError as e:
            print(f"  API error {e.status_code}: {e.message}"); continue
        except anthropic.APIConnectionError:
            print("  network error"); continue
        json.dump(brief, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        print(f"  -> {out.name}  confidence={brief['confidence']}  tokens in/out {brief['usage']['input']}/{brief['usage']['output']}")


if __name__ == "__main__":
    main()
