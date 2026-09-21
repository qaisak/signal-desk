# Signal Desk

A one-person outbound desk. Keep a list of target accounts, pull fresh buying
signals every morning from free sources, rank by "why now", draft the opener,
track status. Built for the Encord Commercial Associate process; works for any
B2B territory.

## Run

Day to day you never touch GitHub:

- **`desk.bat`**: opens the desk at http://localhost:8787 with a local server. "+ add account", "request a brief" and "refresh now" work instantly and push the result to the public page.
- **`run.bat`**: the full pipeline plus push. Registered as a Windows scheduled task, weekdays 08:00 (`schtasks /Query /TN SignalDesk`).
- The public page at https://qaisak.github.io/signal-desk/ and the claude.ai team edition are just what the laptop last pushed.

The GitHub Action is a manual fallback for when the laptop is off.


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

## Adding an account or requesting a brief

From the desk opened with `desk.bat`: **+ add account** adds the row and pulls its signals (about ten seconds), **request a brief** writes the brief and deck (about two minutes). The page reloads itself when done. On the public page those buttons open a pre-filled GitHub issue instead, for teammates without the laptop.

By hand: one row in `accounts.csv`. `query` is the Google News search (quote the name,
add a disambiguator for generic names). `ats_slugs` are guesses at the job
board slug, semicolon separated; the first that answers wins. `paper_query`
blank skips arXiv.

## Two editions, one codebase

| | GitHub Pages | claude.ai artifact |
|---|---|---|
| URL | https://qaisak.github.io/signal-desk/ | private link, shared from its Share menu |
| Pipeline state | this browser only (localStorage) | shared live across the team (claude db), every action attributed |
| Who am I | "you" | your claude.ai identity; owners and the activity feed show real names |
| Deck download | direct | via the downloads capability |
| Refresh | daily bot, or "refresh now" | republish after a run |

The page detects which one it is running in. The header badge says `solo` or `team · live`.

## Working the desk as a team

- **Your day** strip at the top: your overdue and due-today follow-ups.
- **Claim before you call**: set owner, so nobody double-contacts. Tiles show hot-and-unowned accounts.
- **Log a touch**: email sent / call / reply received / note. Status changes set follow-ups automatically (contacted +3d, replied +1d). Everything lands in the team activity feed.
- **Pipeline first** ordering keeps accounts in conversation on top, overdue ones first.
- **Export CSV** for the weekly pipeline review.
- **Daily digest** at `docs/digest.md`; set a `SLACK_WEBHOOK` secret and it posts to a channel every morning.

## State

Status, next-step date, edited opener and notes live in the browser
(localStorage), so they survive rebuilds of the HTML but stay on this machine.
