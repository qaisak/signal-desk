"""
Local desk server: serves the dashboard and handles "add account", "request
brief" and "refresh" without GitHub. Runs the pipeline in the background and
pushes the result so the public page updates too.

  python serve.py            # http://localhost:8787, opens the browser
  python serve.py --no-push  # local only
"""
import csv, json, os, re, subprocess, sys, threading, time, webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).parent
PORT = 8787
PUSH = "--no-push" not in sys.argv
STATE = {"running": False, "log": [], "done_at": None}
PY = sys.executable


def log(msg):
    STATE["log"].append(f"{time.strftime('%H:%M:%S')} {msg}"); STATE["log"] = STATE["log"][-40:]; print(msg, flush=True)


def run(cmd):
    log("> " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in (r.stdout or "").strip().splitlines()[-3:]: log("  " + line)
    if r.returncode: log(f"  FAILED ({r.returncode}): {(r.stderr or '').strip()[-300:]}")
    return r.returncode == 0


def pipeline(only=None, message="desk update"):
    if STATE["running"]: log("already running, queued request ignored"); return
    STATE["running"] = True
    try:
        run([PY, "signals.py"] + ([only] if only else []))
        run([PY, "brief.py"] + ([only] if only else []))
        run([PY, "deck.py"])
        run([PY, "dashboard.py"])
        if PUSH:
            run(["git", "add", "-A"]); subprocess.run(["git", "commit", "-qm", message], cwd=ROOT, capture_output=True)
            run(["git", "pull", "-q", "--rebase", "-X", "theirs", "origin", "main"]); run(["git", "push", "-q", "origin", "main"])
        log("done")
    finally:
        STATE["running"] = False; STATE["done_at"] = time.time()


def rows():
    return list(csv.DictReader(open(ROOT / "accounts.csv", encoding="utf-8")))


def save(rs):
    with open(ROOT / "accounts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rs[0].keys())); w.writeheader(); w.writerows(rs)


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(ROOT / "docs"), **k)
    def log_message(self, *a): pass

    def _json(self, code, obj):
        b = json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/api/status"): return self._json(200, STATE)
        if self.path == "/": self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0)); d = json.loads(self.rfile.read(n) or b"{}")
        if self.path == "/api/add":
            rs = rows(); name = d.get("name", "").strip()
            if not name or not d.get("domain"): return self._json(400, {"error": "name and domain required"})
            if any(r["name"].lower() == name.lower() for r in rs): return self._json(409, {"error": f"{name} is already on the list"})
            row = {k: "" for k in rs[0].keys()}
            row.update(name=name, domain=d["domain"].strip(), vertical=d.get("vertical") or "Other", hq=d.get("hq", ""), fit=str(d.get("fit", 3)),
                       ats_slugs=re.sub(r"[^a-z0-9]", "", name.lower()), query=f'"{name}"', paper_query=name, persona=d.get("persona") or "ML Lead",
                       blurb=d.get("blurb", ""), data=d.get("data", ""), verified="no", brief="yes" if d.get("brief") else "no")
            rs.append(row); save(rs)
            threading.Thread(target=pipeline, args=(name, f"add account: {name}"), daemon=True).start()
            return self._json(200, {"ok": True, "msg": f"{name} added; pulling signals" + (" and writing a brief" if row["brief"] == "yes" else "")})
        if self.path == "/api/brief":
            rs = rows(); r = next((x for x in rs if x["name"] == d.get("name")), None)
            if not r: return self._json(404, {"error": "no such account"})
            r["brief"] = "yes"; r["verified"] = "yes"; save(rs)
            threading.Thread(target=pipeline, args=(r["name"], f"brief: {r['name']}"), daemon=True).start()
            return self._json(200, {"ok": True, "msg": f"writing a brief for {r['name']}, about two minutes"})
        if self.path == "/api/refresh":
            threading.Thread(target=pipeline, args=(None, "refresh"), daemon=True).start()
            return self._json(200, {"ok": True, "msg": "refreshing signals, about a minute"})
        return self._json(404, {"error": "unknown"})


if __name__ == "__main__":
    print(f"Signal Desk local server on http://localhost:{PORT}  (push {'on' if PUSH else 'off'}), Ctrl+C to stop")
    threading.Timer(0.8, lambda: webbrowser.open(f"http://localhost:{PORT}/")).start()
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
