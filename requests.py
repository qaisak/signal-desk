"""
Handle a request raised as a GitHub issue from the dashboard.

  title "add account: <Name>"   body has "key: value" lines -> new row in accounts.csv
  title "brief: <Name>"         -> brief=yes on that row (and verified=yes)
  title "park: <Name>"          -> brief=no

Run by .github/workflows/requests.yml with ISSUE_TITLE / ISSUE_BODY set.
Prints a one-line result for the bot to post back on the issue.
"""
import csv, os, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
title = os.environ.get("ISSUE_TITLE", "").strip()
body = os.environ.get("ISSUE_BODY", "")
rows = list(csv.DictReader(open(ROOT / "accounts.csv", encoding="utf-8")))
fields = list(rows[0].keys())


def save():
    with open(ROOT / "accounts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def find(name):
    return next((r for r in rows if r["name"].lower() == name.lower()), None)


def kv(body):
    out = {}
    for line in body.splitlines():
        m = re.match(r"\s*\**([a-z_ ]+)\**\s*:\s*(.+)", line, re.I)
        if m: out[m.group(1).strip().lower().replace(" ", "_")] = m.group(2).strip()
    return out


m = re.match(r"(add account|brief|park)\s*:\s*(.+)", title, re.I)
if not m:
    print("ignored: title must start with 'add account:', 'brief:' or 'park:'"); sys.exit(0)
kind, name = m.group(1).lower(), m.group(2).strip()

if kind == "add account":
    if find(name):
        print(f"{name} is already on the list"); sys.exit(0)
    d = kv(body)
    row = {k: "" for k in fields}
    row.update(name=name, domain=d.get("domain", ""), vertical=d.get("vertical", "Other"), hq=d.get("hq", ""),
               fit=d.get("fit", "3") if d.get("fit", "3").isdigit() else "3", ats_slugs=d.get("ats_slugs") or re.sub(r"[^a-z0-9]", "", name.lower()),
               notes=d.get("notes", ""), query=d.get("query") or f'"{name}"', paper_query=d.get("paper_query", name),
               persona=d.get("persona", "ML Lead"), blurb=d.get("blurb", d.get("what_they_build", "")), data=d.get("data", d.get("data_we_can_help_with", "")),
               verified="no", brief="yes" if d.get("brief", "").lower().startswith("y") else "no")
    rows.append(row); save()
    print(f"added {name} ({row['vertical']}, fit {row['fit']}). Signals will be pulled on this run" + (" and a brief written." if row["brief"] == "yes" else "."))
elif kind == "brief":
    r = find(name)
    if not r: print(f"no account called {name}; add it first"); sys.exit(0)
    r["brief"] = "yes"; r["verified"] = "yes"; save()
    print(f"brief requested for {name}. It is being written now; allow three minutes, then reload the desk.")
else:
    r = find(name)
    if not r: print(f"no account called {name}"); sys.exit(0)
    r["brief"] = "no"; save()
    print(f"{name} parked: no further briefs.")
