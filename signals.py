"""
Pull fresh buying signals for every account in accounts.csv.

Sources (all free, no keys):
  news   Google News RSS, last 60 days
  jobs   the company's own ATS board (Greenhouse / Lever / Ashby / Workable), CV & ML roles only
  papers arXiv, last 12 months, company name in title/abstract
  hn     Hacker News stories mentioning the company

Everything is written to data/signals.json with a first_seen date per item,
so the dashboard can show "new since yesterday".
"""
import csv, json, re, time, html
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
import requests, feedparser

ROOT = Path(__file__).parent
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
STORE = DATA / "signals.json"
H = {"User-Agent": "Mozilla/5.0 (signal-desk; personal research tool)"}
NOW = datetime.now(timezone.utc)
TODAY = NOW.date().isoformat()

ML_ROLE = re.compile(r"computer vision|perception|machine learning|\bML\b|deep learning|annotation|labell?ing|data engineer|autonomy|robotics software|AI engineer|research scientist|data scientist|MLOps|training data", re.I)
FUNDING = re.compile(r"\braises?\b|\braised\b|\bfunding\b|\bseries [a-e]\b|\binvestment\b|\bvaluation\b|\bunicorn\b|[$£€]\d+(\.\d+)?\s?(m|bn|million|billion)\b", re.I)
LAUNCH = re.compile(r"launch|unveil|announce|introduc|new robot|next-gen|partnership|deploy|contract|rollout", re.I)


def get(url, **kw):
    try:
        r = requests.get(url, headers=H, timeout=20, **kw)
        return r if r.status_code == 200 else None
    except requests.RequestException:
        return None


# ---------------------------------------------------------------- sources
def news(query):
    r = get(f"https://news.google.com/rss/search?q={quote(query)}&hl=en-GB&gl=GB&ceid=GB:en")
    if not r: return []
    out = []
    for e in feedparser.parse(r.text).entries[:40]:
        try: d = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
        except Exception: continue
        if NOW - d > timedelta(days=60): continue
        title = html.unescape(e.title)
        kind = "funding" if FUNDING.search(title) else ("launch" if LAUNCH.search(title) else "news")
        out.append(dict(type=kind, title=title, url=e.link, date=d.date().isoformat(),
                        source=getattr(e, "source", {}).get("title", "")))
    return out


def jobs(slugs):
    out = []
    for slug in [s for s in slugs.split(";") if s]:
        # Greenhouse
        r = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        if r:
            for j in r.json().get("jobs", []):
                out.append(dict(title=j["title"], url=j["absolute_url"], loc=j.get("location", {}).get("name", ""), ats="greenhouse"))
            if out: return _ml_only(out)
        # Lever
        r = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        if r and isinstance(r.json(), list):
            for j in r.json():
                out.append(dict(title=j["text"], url=j["hostedUrl"], loc=j.get("categories", {}).get("location", ""), ats="lever"))
            if out: return _ml_only(out)
        # Ashby
        r = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        if r:
            for j in r.json().get("jobs", []):
                out.append(dict(title=j["title"], url=j["jobUrl"], loc=j.get("location", ""), ats="ashby"))
            if out: return _ml_only(out)
        # Workable
        r = get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}")
        if r:
            for j in r.json().get("jobs", []):
                out.append(dict(title=j["title"], url=j["url"], loc=j.get("city", ""), ats="workable"))
            if out: return _ml_only(out)
    return []


def _ml_only(js):
    seen, out = set(), []
    for j in js:
        if ML_ROLE.search(j["title"]) and j["url"] not in seen:
            seen.add(j["url"]); out.append(dict(type="job", **j))
    return out


def papers(query):
    if not query: return []
    r = get(f"http://export.arxiv.org/api/query?search_query=all:{quote(query)}&max_results=10&sortBy=submittedDate&sortOrder=descending")
    if not r: return []
    out = []
    for e in feedparser.parse(r.text).entries:
        d = datetime(*e.published_parsed[:6], tzinfo=timezone.utc)
        if NOW - d > timedelta(days=365): continue
        out.append(dict(type="paper", title=e.title.replace("\n", " "), url=e.link, date=d.date().isoformat()))
    return out


def hn(query):
    r = get(f"https://hn.algolia.com/api/v1/search?query={quote(query)}&tags=story&numericFilters=created_at_i>{int((NOW - timedelta(days=180)).timestamp())}")
    if not r: return []
    return [dict(type="hn", title=h["title"], url=h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                 date=h["created_at"][:10], points=h.get("points", 0)) for h in r.json().get("hits", [])[:5] if h.get("title")]


# ---------------------------------------------------------------- run
def main():
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else None          # python signals.py "Name" pulls one account and merges
    prev = json.load(open(STORE, encoding="utf-8")) if STORE.exists() else {}
    accounts = list(csv.DictReader(open(ROOT / "accounts.csv", encoding="utf-8")))
    store = dict(prev) if only else {}
    for a in accounts:
        if only and a["name"] != only: continue
        n = a["name"]; print(f"{n:28s}", end="", flush=True)
        items = news(a["query"]) + jobs(a["ats_slugs"]) + papers(a["paper_query"]) + hn(a["paper_query"] or n)
        old = {i["url"]: i for i in prev.get(n, {}).get("signals", [])}
        for i in items:
            i["first_seen"] = old.get(i["url"], {}).get("first_seen", TODAY)
        store[n] = dict(**a, signals=items, fetched=TODAY)
        c = {t: sum(1 for i in items if i["type"] == t) for t in ["funding", "launch", "news", "job", "paper", "hn"]}
        print("  " + "  ".join(f"{k}:{v}" for k, v in c.items() if v))
        time.sleep(1.2)   # be polite to the RSS endpoint
    json.dump(store, open(STORE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\nwrote {STORE}")


if __name__ == "__main__":
    main()
