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
DATA = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
page = r"""<title>Signal Desk</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{--bg:#f4f5f9;--surface:#fff;--ink:#171a33;--muted:#5d6180;--line:#dfe2ee;--accent:#4f46e5;--soft:#e8e6fb;--hot:#c2410c;--warm:#b45309;--ok:#0f8a5f;--mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;--body:"IBM Plex Sans",system-ui,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f1124;--surface:#171a32;--ink:#eceefc;--muted:#9fa4c8;--line:#2a2e50;--accent:#8b83ff;--soft:#26265a;--hot:#fb923c;--warm:#fbbf24;--ok:#3ecf8e}}
:root[data-theme=dark]{--bg:#0f1124;--surface:#171a32;--ink:#eceefc;--muted:#9fa4c8;--line:#2a2e50;--accent:#8b83ff;--soft:#26265a;--hot:#fb923c;--warm:#fbbf24;--ok:#3ecf8e}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 var(--body);padding-block:20px 60px;padding-inline:clamp(16px,3vw,32px)}
.wrap{max-width:1200px;margin:0 auto}header{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px 16px;margin-bottom:14px}
h1{font-size:22px;margin:0}.meta{font:12px var(--mono);color:var(--muted)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 12px}.tile b{display:block;font:500 22px var(--mono);color:var(--accent)}.tile span{font-size:12px;color:var(--muted)}
.bar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
input[type=search],select{font:13px var(--body);padding:6px 9px;border:1px solid var(--line);border-radius:6px;background:var(--surface);color:var(--ink)}
.grid{display:grid;grid-template-columns:minmax(0,1fr);gap:14px}@media(min-width:900px){.grid{grid-template-columns:minmax(0,7fr) minmax(0,5fr)}}
table{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--line);border-radius:8px;overflow:hidden}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}th{font:500 11px var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
tr[data-i]{cursor:pointer}tr[data-i]:hover,tr.sel{background:var(--soft)}
.num{font:500 13px var(--mono);font-variant-numeric:tabular-nums}.why{font-size:12.5px;color:var(--muted);max-width:52ch}
.chip{display:inline-block;font:500 10.5px var(--mono);padding:1px 7px;border-radius:999px;background:var(--soft);color:var(--accent);margin-right:4px}
.chip.hot{background:var(--hot);color:#fff}.chip.new{background:var(--ok);color:#fff}
.stat{font:500 11px var(--mono);padding:2px 7px;border-radius:5px;border:1px solid var(--line);background:transparent;color:var(--ink)}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px;position:sticky;top:12px;max-height:calc(100vh - 30px);overflow:auto}
.panel h2{margin:0 0 2px;font-size:18px}.panel .sub{font:12px var(--mono);color:var(--muted);margin-bottom:10px}
.sig{padding:7px 0;border-top:1px solid var(--line);font-size:13px}.sig a{color:var(--ink);text-decoration:none}.sig a:hover{text-decoration:underline}.sig .d{font:11px var(--mono);color:var(--muted)}
textarea{width:100%;min-height:150px;font:12.5px var(--mono);border:1px solid var(--line);border-radius:6px;padding:8px;background:var(--bg);color:var(--ink);resize:vertical}
button{font:500 12px var(--mono);background:var(--accent);color:#fff;border:0;border-radius:6px;padding:6px 10px;cursor:pointer}button.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:8px 0}label{font-size:12px;color:var(--muted)}
.tbl{overflow-x:auto}
.btn{display:inline-block;font:500 11px var(--mono);background:var(--accent);color:#fff;border-radius:6px;padding:4px 9px;text-decoration:none;white-space:nowrap}.lock{font:500 11px var(--mono);color:var(--muted);border:1px dashed var(--line);border-radius:6px;padding:3px 8px;cursor:help;white-space:nowrap}
</style>
<div class="wrap">
<header><h1>Signal Desk</h1><div class="meta">data pulled __DATE__ · auto-refresh weekdays 07:00 UTC · score = fit × momentum &nbsp;<a class="btn" href="https://github.com/qaisak/signal-desk/actions/workflows/refresh.yml" target="_blank" rel="noopener" title="Opens GitHub. Click 'Run workflow', wait about two minutes, then reload this page.">refresh now ↗</a></div></header>
<div class="tiles" id="tiles"></div>
<div class="bar"><input id="q" type="search" placeholder="filter accounts"><select id="vert"><option value="">all verticals</option></select><select id="st"><option value="">any status</option><option>untouched</option><option>contacted</option><option>replied</option><option>meeting</option><option>parked</option></select><label><input id="onlynew" type="checkbox"> new signals only</label><label><input id="pipefirst" type="checkbox" checked> pipeline first</label></div>
<div class="grid"><div class="tbl"><table><thead><tr><th>#</th><th>Account</th><th>Fit</th><th>Mom.</th><th>Score</th><th>Why now</th><th>Lead with</th><th>Brief</th><th>Status</th></tr></thead><tbody id="tb"></tbody></table></div><aside class="panel" id="panel"><div class="sub">select an account</div></aside></div>
</div>
<script>
const ROWS=__DATA__;
const KEY='signal-desk-state';let state={};try{state=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(state))}catch(e){}};
const st=n=>(state[n]||{}).status||'untouched';
const esc=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let sel=null;
function tiles(){const hot=ROWS.filter(r=>r.momentum>=50).length,nw=ROWS.reduce((a,r)=>a+r.new,0),jobs=ROWS.reduce((a,r)=>a+r.pts.job/8,0)|0,cont=ROWS.filter(r=>['contacted','replied','meeting'].includes(st(r.name))).length;
document.getElementById('tiles').innerHTML=[[ROWS.length,'accounts'],[hot,'hot (momentum ≥ 50)'],[nw,'new signals today'],[jobs,'open ML / CV roles'],[cont,'in conversation']].map(([b,s])=>`<div class="tile"><b>${b}</b><span>${s}</span></div>`).join('')}
function render(){const q=document.getElementById('q').value.toLowerCase(),v=document.getElementById('vert').value,s=document.getElementById('st').value,on=document.getElementById('onlynew').checked,pf=document.getElementById('pipefirst').checked;
const PRI={meeting:0,replied:1,contacted:2,untouched:3,parked:4};
const ordered=pf?[...ROWS].sort((a,b)=>(PRI[st(a.name)]-PRI[st(b.name)])||(b.total-a.total)):ROWS;
document.getElementById('tb').innerHTML=ordered.filter(r=>(!q||(r.name+r.vertical+r.why).toLowerCase().includes(q))&&(!v||r.vertical===v)&&(!s||st(r.name)===s)&&(!on||r.new>0)).map((r,i)=>`<tr data-i="${r.name}" class="${sel===r.name?'sel':''}"><td class="num">${i+1}</td><td><b>${esc(r.name)}</b> <span class="why">· ${esc(r.hq)}</span><div class="why" style="margin-top:2px">${esc(r.blurb)}</div><div class="why" style="margin-top:2px;color:var(--accent)">${esc(r.data)}</div></td><td class="num">${r.fit}</td><td class="num">${r.momentum}${r.momentum>=50?' <span class="chip hot">hot</span>':''}${r.new?` <span class="chip new">+${r.new}</span>`:''}</td><td class="num">${r.total}</td><td class="why">${esc(r.why)}</td><td class="why"><b>${esc(r.product)}</b></td><td>${r.brief?`<a class="btn" href="${r.brief.deck}" download onclick="event.stopPropagation()">brief deck ↓</a><div class="why" style="margin-top:4px">${r.brief.confidence} confidence · ${r.brief.generated}</div>`:`<span class="lock" title="${esc(r.deck_lock)}">no brief</span>`}</td><td><span class="stat">${st(r.name)}</span></td></tr>`).join('');
document.querySelectorAll('tr[data-i]').forEach(tr=>tr.onclick=()=>{sel=tr.dataset.i;render();panel()})}
function panel(){const r=ROWS.find(x=>x.name===sel);if(!r)return;const s=state[r.name]||{};
document.getElementById('panel').innerHTML=`<h2>${esc(r.name)}</h2><div class="sub">${esc(r.vertical)} · ${esc(r.hq)} · <a href="https://${r.domain}" target="_blank">${r.domain}</a></div>
<div class="row"><label>status</label><select id="pst">${['untouched','contacted','replied','meeting','parked'].map(o=>`<option ${st(r.name)===o?'selected':''}>${o}</option>`).join('')}</select><label>next step</label><input id="pnext" type="date" value="${s.next||''}"></div>
<div class="row">${Object.entries(r.pts).filter(([k,v])=>v>0).map(([k,v])=>`<span class="chip">${k} +${v}</span>`).join('')}</div>
<p style="font-size:13px;margin:6px 0"><b>Why now:</b> ${esc(r.why)}<br><span class="why">${esc(r.notes)}</span></p>
<p style="font-size:13px;margin:6px 0"><b>Lead with:</b> ${esc(r.product)}<br><span class="why">${esc(r.angle)}</span></p>
${r.brief?`<div style="background:var(--soft);border-radius:8px;padding:10px 12px;margin:8px 0"><div style="font:500 11px var(--mono);letter-spacing:.06em;color:var(--accent)">FIRST-MEETING BRIEF · ${r.brief.confidence.toUpperCase()} CONFIDENCE · ${r.brief.generated} · DRAFT</div><p style="margin:6px 0;font-size:13.5px"><b>${esc(r.brief.headline)}</b></p><div class="why">Lead with ${r.brief.modules.join(' → ')}</div><div style="margin-top:6px;font-size:12.5px">${r.brief.hypotheses.map((h,i)=>`<div style="margin:3px 0"><b>H${i+1}</b> ${esc(h)}</div>`).join('')}</div><div class="row" style="margin-top:8px"><a class="btn" href="${r.brief.deck}" download>download brief deck (pptx)</a><span class="why">7 slides, questions and risks in speaker notes</span></div></div>`:`<div class="row"><label>brief</label><span class="why">${esc(r.deck_lock)}</span></div>`}
<div class="row"><label>target persona</label><span class="stat">${esc(r.persona)}</span></div>
<div class="row"><label>contact</label><input id="pcontact" type="text" placeholder="name, title, LinkedIn URL" value="${esc(s.contact||r.contact||'')}" style="flex:1;font:12.5px var(--mono);padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--ink)"></div>
<div class="row"><b style="font-size:12px">Opener</b><button id="copy">copy</button></div><textarea id="op">${esc(s.opener||r.opener)}</textarea>
${r.brief?`<div class="row"><b style="font-size:12px">Questions for the first call</b></div><ol style="margin:0 0 6px 18px;padding:0;font-size:12.5px">${r.brief.questions.map(q=>`<li style="margin:2px 0">${esc(q)}</li>`).join('')}</ol><div class="row"><b style="font-size:12px">Why it might not happen</b></div><ul style="margin:0 0 6px 18px;padding:0;font-size:12.5px;color:var(--muted)">${r.brief.risks.map(q=>`<li style="margin:2px 0">${esc(q)}</li>`).join('')}</ul>`:''}<div class="row"><b style="font-size:12px">Notes</b></div><textarea id="notes" style="min-height:70px" placeholder="who you spoke to, what they said">${esc(s.notes||'')}</textarea>
<div style="margin-top:10px;font:500 11px var(--mono);letter-spacing:.06em;color:var(--muted)">SIGNALS (${r.signals.length})</div>
${r.signals.map(x=>`<div class="sig"><span class="chip">${x.type}</span> <a href="${x.url}" target="_blank" rel="noopener">${esc(x.title)}</a><div class="d">${x.date||''}${x.loc?' · '+esc(x.loc):''}${x.first_seen===ROWS.today?' · new':''}</div></div>`).join('')||'<div class="sig">nothing in the window</div>'}`;
const upd=()=>{state[r.name]={status:document.getElementById('pst').value,next:document.getElementById('pnext').value,opener:document.getElementById('op').value,notes:document.getElementById('notes').value,contact:document.getElementById('pcontact').value};save();tiles();render()};
['pst','pnext','op','notes','pcontact'].forEach(id=>document.getElementById(id).addEventListener('change',upd));
document.getElementById('copy').onclick=()=>{navigator.clipboard&&navigator.clipboard.writeText(document.getElementById('op').value);document.getElementById('copy').textContent='copied';setTimeout(()=>document.getElementById('copy').textContent='copy',1200)}}
document.getElementById('vert').innerHTML+=[...new Set(ROWS.map(r=>r.vertical))].sort().map(v=>`<option>${v}</option>`).join('');
['q','vert','st','onlynew','pipefirst'].forEach(id=>document.getElementById(id).addEventListener('input',render));
tiles();render();if(ROWS.length){sel=ROWS[0].name;render();panel()}
</script>"""
page = page.replace("__DATA__", DATA).replace("__DATE__", TODAY.isoformat())
(ROOT / "dashboard.html").write_text(page, encoding="utf-8")   # fragment: the claude.ai artifact wraps it
(ROOT / "docs").mkdir(exist_ok=True)
standalone = (              # standalone: GitHub Pages and local double-click
    '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + page + "</html>")
(ROOT / "docs" / "index.html").write_text(standalone, encoding="utf-8")
(ROOT / "index.html").write_text(standalone.replace('href="briefs/', 'href="docs/briefs/'), encoding="utf-8")   # repo root, for Pages set to /
print(f"ranked {len(rows)} accounts -> dashboard.html")
for r in rows[:8]:
    print(f"  {r['total']:4d}  {r['name']:26s} fit {r['fit']}  mom {r['momentum']:3d}  {r['why'][:70]}")
