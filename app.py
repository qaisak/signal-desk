"""
Signal Desk server. One process, no framework, runs anywhere Python runs.

  python app.py                 local, http://localhost:8787, no password
  DESK_PASSWORD=... python app.py   team mode: one shared password, names on every action

Shared pipeline state lives in data/pipeline.json. If GITHUB_TOKEN is set the
server commits and pushes every change (debounced), so the repo is the database:
a restart or redeploy loses nothing, and the public GitHub Pages copy stays in step.

Env:  PORT (default 8787)   DESK_PASSWORD (optional gate)   GITHUB_TOKEN (optional, enables push)
      ANTHROPIC_API_KEY (briefs)   GIT_REMOTE (default origin URL)
"""
import csv, json, os, re, subprocess, sys, threading, time, hashlib
from http import cookies
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs

ROOT = Path(__file__).parent
DATA = ROOT / "data"; DATA.mkdir(exist_ok=True)
PIPE = DATA / "pipeline.json"
PORT = int(os.environ.get("PORT", 8787))
PASSWORD = os.environ.get("DESK_PASSWORD", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
PY = sys.executable
LOCK = threading.Lock()
STATE = {"running": False, "log": [], "done_at": None, "pushed_at": None}
COOKIE_NAME = "desk"


def log(msg):
    STATE["log"].append(f"{time.strftime('%H:%M:%S')} {msg}"); STATE["log"] = STATE["log"][-60:]; print(msg, flush=True)


def sh(cmd, quiet=False):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not quiet:
        for line in (r.stdout or "").strip().splitlines()[-3:]: log("  " + line)
        if r.returncode: log(f"  FAILED ({r.returncode}): {(r.stderr or '').strip()[-300:]}")
    return r.returncode == 0


# ---------------------------------------------------------------- git persistence
def git_setup():
    if TOKEN:
        url = os.environ.get("GIT_REMOTE") or subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        url = re.sub(r"https://[^@]*@", "https://", url)
        sh(["git", "remote", "set-url", "origin", url.replace("https://", f"https://x-access-token:{TOKEN}@")], quiet=True)
    sh(["git", "config", "user.name", "signal-desk"], quiet=True); sh(["git", "config", "user.email", "desk@users.noreply.github.com"], quiet=True)
    sh(["git", "pull", "-q", "--rebase", "-X", "theirs", "origin", "main"], quiet=True)


_push_timer = None
def push_soon(message, delay=20):
    """Commit and push after a quiet period, so a burst of edits is one commit."""
    global _push_timer
    if _push_timer: _push_timer.cancel()
    _push_timer = threading.Timer(delay, push_now, args=(message,)); _push_timer.daemon = True; _push_timer.start()


def push_now(message):
    with LOCK:
        sh(["git", "add", "-A"], quiet=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0: return
        sh(["git", "commit", "-qm", message], quiet=True)
        if TOKEN or "--push" in sys.argv:
            ok = sh(["git", "pull", "-q", "--rebase", "-X", "theirs", "origin", "main"], quiet=True) and sh(["git", "push", "-q", "origin", "main"], quiet=True)
            STATE["pushed_at"] = time.time() if ok else STATE["pushed_at"]
            log("pushed" if ok else "push failed")


# ---------------------------------------------------------------- pipeline
def pipeline(only=None, message="desk update"):
    if STATE["running"]: log("busy, try again in a minute"); return
    STATE["running"] = True
    try:
        log(f"> signals {only or 'all'}"); sh([PY, "signals.py"] + ([only] if only else []))
        log(f"> brief {only or 'flagged'}"); sh([PY, "brief.py"] + ([only] if only else []))
        log("> decks"); sh([PY, "deck.py"])
        log("> dashboard"); sh([PY, "dashboard.py"])
        push_now(message); log("done")
    finally:
        STATE["running"] = False; STATE["done_at"] = time.time()


# ---------------------------------------------------------------- accounts + shared state
def rows(): return list(csv.DictReader(open(ROOT / "accounts.csv", encoding="utf-8")))
def save_rows(rs):
    with open(ROOT / "accounts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0].keys())); w.writeheader(); w.writerows(rs)
def load_pipe(): return json.load(open(PIPE, encoding="utf-8")) if PIPE.exists() else {}
def save_pipe(p): json.dump(p, open(PIPE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)


def slug(n): return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(ROOT / "docs"), **k)
    def log_message(self, *a): pass

    # -- helpers
    def _json(self, code, obj, extra=None):
        b = json.dumps(obj, ensure_ascii=False).encode(); self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers(); self.wfile.write(b)
    def _cookie(self, name):
        c = cookies.SimpleCookie(self.headers.get("Cookie", "")); return c[name].value if name in c else ""
    def _authed(self):
        if not PASSWORD: return True
        return self._cookie(COOKIE_NAME) == hashlib.sha256(PASSWORD.encode()).hexdigest()[:32]
    def _who(self):
        return (self._cookie("who") or self.headers.get("X-Who") or "someone")[:40]
    def _body(self):
        n = int(self.headers.get("Content-Length", 0)); return json.loads(self.rfile.read(n) or b"{}")

    # -- routes
    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/login": return self._login_page()
        if p == "/healthz": return self._json(200, {"ok": True})
        if not self._authed(): self.send_response(302); self.send_header("Location", "/login"); self.end_headers(); return
        if p == "/api/status": return self._json(200, STATE)
        if p == "/api/state": return self._json(200, load_pipe())
        if p == "/api/me": return self._json(200, {"who": self._who(), "hosted": True, "password": bool(PASSWORD)})
        if p == "/": self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/login":
            n = int(self.headers.get("Content-Length", 0)); form = parse_qs(self.rfile.read(n).decode())
            pw, who = form.get("password", [""])[0], form.get("who", ["someone"])[0].strip()[:40]
            if PASSWORD and pw != PASSWORD: return self._login_page("wrong password")
            self.send_response(302); self.send_header("Location", "/")
            self.send_header("Set-Cookie", f"{COOKIE_NAME}={hashlib.sha256(PASSWORD.encode()).hexdigest()[:32]}; Path=/; Max-Age=31536000; SameSite=Lax; HttpOnly")
            self.send_header("Set-Cookie", f"who={who}; Path=/; Max-Age=31536000; SameSite=Lax"); self.end_headers(); return
        if not self._authed(): return self._json(401, {"error": "sign in first"})
        d = self._body(); who = self._who()
        if p.startswith("/api/state/"):
            sl = p.rsplit("/", 1)[1]; pipe = load_pipe(); cur = pipe.get(sl, {"log": []})
            patch = {k: v for k, v in d.items() if k in ("status", "owner", "next", "contact", "opener")}
            entries = d.get("log_add") or []
            newlog = [dict(t=e.get("t") or time.strftime("%Y-%m-%dT%H:%M:%S"), who=who, kind=e.get("kind", "note"), text=(e.get("text") or "")[:400]) for e in entries][:5]
            cur.update(patch); cur["log"] = (newlog + cur.get("log", []))[:40]; cur["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S"); cur["by"] = who
            pipe[sl] = cur; save_pipe(pipe); push_soon(f"pipeline: {sl} by {who}")
            return self._json(200, cur)
        if p == "/api/add":
            rs = rows(); name = (d.get("name") or "").strip()
            if not name or not d.get("domain"): return self._json(400, {"error": "name and domain required"})
            if any(r["name"].lower() == name.lower() for r in rs): return self._json(409, {"error": f"{name} is already on the list"})
            row = {k: "" for k in rs[0].keys()}
            row.update(name=name, domain=d["domain"].strip(), vertical=d.get("vertical") or "Other", hq=d.get("hq", ""), fit=str(d.get("fit", 3)),
                       ats_slugs=re.sub(r"[^a-z0-9]", "", name.lower()), query=f'"{name}"', paper_query=name, persona=d.get("persona") or "ML Lead",
                       blurb=d.get("blurb", ""), data=d.get("data", ""), verified="no", brief="yes" if d.get("brief") else "no", notes=f"added by {who}")
            rs.append(row); save_rows(rs)
            threading.Thread(target=pipeline, args=(name, f"add account: {name} ({who})"), daemon=True).start()
            return self._json(200, {"ok": True, "msg": f"{name} added; pulling signals" + (" and writing a brief" if row["brief"] == "yes" else "")})
        if p == "/api/brief":
            rs = rows(); r = next((x for x in rs if x["name"] == d.get("name")), None)
            if not r: return self._json(404, {"error": "no such account"})
            r["brief"] = "yes"; r["verified"] = "yes"; save_rows(rs)
            threading.Thread(target=pipeline, args=(r["name"], f"brief: {r['name']} ({who})"), daemon=True).start()
            return self._json(200, {"ok": True, "msg": f"writing a brief for {r['name']}, about two minutes"})
        if p == "/api/refresh":
            threading.Thread(target=pipeline, args=(None, f"refresh ({who})"), daemon=True).start()
            return self._json(200, {"ok": True, "msg": "refreshing every account, about four minutes"})
        return self._json(404, {"error": "unknown"})

    def _login_page(self, err=""):
        html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Signal Desk</title>
<style>body{{font:15px system-ui,sans-serif;background:#f4f5f9;color:#171a33;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}form{{background:#fff;border:1px solid #dfe2ee;border-radius:10px;padding:24px;width:min(360px,90vw)}}input{{width:100%;box-sizing:border-box;font:15px system-ui;padding:9px 10px;border:1px solid #dfe2ee;border-radius:6px;margin:6px 0 12px}}button{{font:600 14px ui-monospace,monospace;background:#4f46e5;color:#fff;border:0;border-radius:6px;padding:9px 14px;cursor:pointer}}h1{{font-size:20px;margin:0 0 4px}}p{{color:#5d6180;margin:0 0 14px;font-size:13px}}.e{{color:#c2410c;font-size:13px}}</style></head>
<body><form method="post" action="/login"><h1>Signal Desk</h1><p>Outbound desk for UK physical AI. Your name goes on everything you do.</p>
<label>Your name<input name="who" required placeholder="e.g. Qais" autofocus></label>{'<label>Team password<input name="password" type="password" required></label>' if PASSWORD else ''}
<button>open the desk</button> <span class="e">{err}</span></form></body></html>"""
        b = html.encode(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


def sync_loop():
    """Every 10 minutes pull whatever the daily GitHub refresh pushed (signals, rebuilt page)."""
    while True:
        time.sleep(600)
        if STATE["running"]: continue
        with LOCK:
            sh(["git", "pull", "-q", "--rebase", "-X", "theirs", "origin", "main"], quiet=True)


if __name__ == "__main__":
    git_setup()
    threading.Thread(target=sync_loop, daemon=True).start()
    if not (ROOT / "docs" / "index.html").exists(): sh([PY, "dashboard.py"])
    print(f"Signal Desk on http://0.0.0.0:{PORT}  password={'on' if PASSWORD else 'off'}  push={'on' if TOKEN else 'off'}", flush=True)
    if "--open" in sys.argv:
        import webbrowser; threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}/")).start()
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
