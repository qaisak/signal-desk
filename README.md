# Signal Desk

A one-person outbound desk. Keep a list of target accounts, pull fresh buying
signals every morning from free sources, rank by "why now", draft the opener,
track status. Built for the Encord Commercial Associate process; works for any
B2B territory.

## Run

```bash
python signals.py     # pulls news, jobs, papers, HN for every account (~1 min)
python dashboard.py   # scores, ranks, writes dashboard.html
```

Or double-click `run.bat`. To run it every weekday at 08:00:

```
schtasks /create /tn "SignalDesk" /tr "C:\Users\Qais\signal-desk\run.bat" /sc weekly /d MON,TUE,WED,THU,FRI /st 08:00
```

## Sources (no API keys)

| Signal | Source | Window |
|---|---|---|
| news, funding, launches | Google News RSS, per-account query | 60 days |
| ML / CV job postings | company ATS: Greenhouse, Lever, Ashby, Workable | live |
| papers | arXiv | 12 months |
| Hacker News | Algolia HN API | 6 months |

## Scoring

`score = fit x momentum`. Fit (1 to 5) is your judgement of data volume and
buyability, set once in `accounts.csv`. Momentum (0 to 100) is computed from
signals with recency decay: funding 30, launch 12 (cap 24), ML job 8 (cap 32),
paper 6 (cap 12), HN 3 (cap 6), plain news 2 (cap 10), +5 if anything is new
since the last run.

## Briefs and decks

Set `brief=yes` on an account you have decided to work. The next run gathers
their website, their open ML/CV job ads and the month's signals, and asks
Claude Opus 5 for a first-meeting brief: what they build, how we think their
data flows, three ranked hypotheses with evidence, an ontology for their
objects, the matching case study, a two-week proof of value, discovery
questions and risks. `deck.py` turns it into a 7-slide pptx (questions and
risks go in the speaker notes). Everything is marked DRAFT: read it before it
goes anywhere. Briefs refresh weekly, not daily, to keep API spend low
(roughly 10p each). Needs `ANTHROPIC_API_KEY` locally or as a GitHub secret.

## Adding an account

One row in `accounts.csv`. `query` is the Google News search (quote the name,
add a disambiguator for generic names). `ats_slugs` are guesses at the job
board slug, semicolon separated; the first that answers wins. `paper_query`
blank skips arXiv.

## State

Status, next-step date, edited opener and notes live in the browser
(localStorage), so they survive rebuilds of the HTML but stay on this machine.
