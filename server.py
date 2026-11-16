#!/usr/bin/env python
"""server.py — standalone Bill Platform, loopback only on 127.0.0.1:8093.

Routes:

    /                    the desk — reading spine, pipeline, evidence
    /bill                the draft, read through (?lens=all|renter|provider|lawmaker&view=both|statute|plain)
    /clause/<id>         one clause + audience impact + refs + margin + mark form
    /calculator          live 3-source funding braid & stress-test calculator
    /present             16:9 TV / Presentation stage deck (?s=1..8)
    /tv                  shortcut into TV mode on /present
    /mark                the Inkwell (mark form; ?c=, ?re=, ?q=, ?kind=)
    /margin              the public ledger of read-in marks
    /intake              steward triage queue — read in / hold / crisis route
    /requests            requests desk + new-request form
    /positions           who stands where
    /claims              verification & claims ledger
    /decisions           8 locked design decisions
    /editions            change ledger (E-01…E-09)
    /steward             steward unlock / passcode screen
    /steward/toggle      1-tap local dev steward toggle (loopback only when no custom env code set)
    /steward/lock        lock steward session
    /mode/<m>?next=<p>   set screen mode (desk|tv|mobile), redirect
    /static/<file>       platform.css, platform.js

JSON / API endpoints:
    GET  /api/state      sanitized JSON snapshot (public marks only unless steward)
    GET  /api/calculate  funding braid JSON (?rent=1300&units=1&m1pr=1)
    POST /api/steward    verify passcode and set steward cookie
    POST /api/mark       enter a mark (lands queued — never public until read_in)
    POST /api/mark_action    steward-only: read_in | held | crisis_routed (+answer)
    POST /api/request        enter a request
    POST /api/request_status steward-only: advance/decline a request
    POST /api/position       record a position

Run:  python server.py        (or: python server.py --port 8093)
Stop: Ctrl+C
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import mimetypes
import os
import sys
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Guard stdout/stderr for pythonw.exe and Windows cp1252 consoles
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
else:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
else:
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import db
import views

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
MODES = ("desk", "tv", "mobile")
MAX_POST = 64 * 1024
DEFAULT_PASSCODE = "mn-steward"

# URL mount point for deployment under a path prefix (e.g. "/bill" when
# served at semptify.org/bill behind the Cloudflare proxy worker).
# Empty = mounted at root (local dev / onrender direct).
MOUNT = os.environ.get("BILL_MOUNT", "").rstrip("/")


def steward_code() -> str:
    return os.environ.get("BILL_STEWARD_CODE", DEFAULT_PASSCODE)


def local_onetap_allowed(host_header: str) -> bool:
    """Allow 1-tap steward unlock on loopback when no custom passcode env var is set."""
    if os.environ.get("BILL_STEWARD_CODE"):
        return False
    host = (host_header or "").split(":", 1)[0].strip().lower()
    return host in {"127.0.0.1", "localhost", "::1", ""}


def make_steward_token() -> str:
    secret = steward_code().encode("utf-8")
    return hmac.new(secret, b"bill-platform-steward-v1", hashlib.sha256).hexdigest()[:32]


def _safe_next(raw: str | None, fallback: str = "/") -> str:
    if not raw or not raw.startswith("/") or raw.startswith("//"):
        return fallback
    return raw


def _safe_join(root: Path, rel: str) -> Path | None:
    """Resolve rel inside root; refuse escapes and non-files."""
    p = (root / urllib.parse.unquote(rel).lstrip("/")).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return None
    return p if p.is_file() else None


class Handler(BaseHTTPRequestHandler):
    server_version = "BillPlatform/1.1"
    protocol_version = "HTTP/1.1"

    # ---------- helpers ----------

    def _send(self, body: bytes, status: int = 200,
              ctype: str = "text/html; charset=utf-8",
              extra: list[tuple[str, str]] | None = None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in extra or []:
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _redirect(self, location: str,
                  extra: list[tuple[str, str]] | None = None):
        if (MOUNT and location.startswith("/")
                and location != MOUNT
                and not location.startswith(MOUNT + "/")):
            location = MOUNT + location
        self._send(b"", 303, extra=[("Location", location)] + (extra or []))

    def _cookies(self) -> dict[str, str]:
        out: dict[str, str] = {}
        raw = self.headers.get("Cookie", "")
        for part in raw.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                out[k.strip()] = v.strip()
        return out

    _RATE: dict[str, list[float]] = {}

    def _rate_ok(self, limit: int = 12, window: float = 300.0) -> bool:
        ip = self.client_address[0]
        now = time.time()
        hits = [t for t in self._RATE.get(ip, []) if now - t < window]
        if len(hits) >= limit:
            self._RATE[ip] = hits
            return False
        hits.append(now)
        self._RATE[ip] = hits
        return True

    def _mode(self) -> str:
        m = self._cookies().get("bp_mode", "auto")
        return m if m in MODES + ("auto",) else "auto"

    def _is_steward(self) -> bool:
        tok = self._cookies().get("bp_steward", "")
        if tok and hmac.compare_digest(tok, make_steward_token()):
            return True
        hdr = (self.headers.get("X-Steward-Code") or "").strip()
        if hdr and hmac.compare_digest(hdr, steward_code()):
            return True
        return False

    def _ctx(self, path: str) -> dict:
        return {
            "mode": self._mode(),
            "path": path,
            "steward": self._is_steward(),
            "onetap": local_onetap_allowed(self.headers.get("Host", "")),
        }

    def _form(self) -> dict[str, list[str]] | None:
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n < 0 or n > MAX_POST:
            return None
        if n == 0:
            return {}
        return urllib.parse.parse_qs(
            self.rfile.read(n).decode("utf-8", "replace"),
            keep_blank_values=True, max_num_fields=64)

    @staticmethod
    def _one(form: dict, key: str, maxlen: int = 8000) -> str:
        return (form.get(key, [""])[0] or "")[:maxlen].strip()

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[bill-platform] {self.address_string()} {fmt % args}\n")

    # ---------- GET ----------

    def _mount_path(self, path: str) -> str | None:
        """Strip the mount prefix; returns the routed path, or None when
        the request landed outside the mount (caller redirects into it)."""
        if not MOUNT:
            return path
        if path == MOUNT:
            return "/"
        if path.startswith(MOUNT + "/"):
            return path[len(MOUNT):]
        return None

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        raw_path = url.path.rstrip("/") or "/"
        path = self._mount_path(raw_path)
        if path is None:
            self._redirect(MOUNT + raw_path)
            return
        q = urllib.parse.parse_qs(url.query)
        ctx = self._ctx(path)

        if path == "/api/export":
            if not self._is_steward():
                self._send(b"steward unlock required for export", 403,
                           "text/plain; charset=utf-8")
                return
            self._send(json.dumps(db.export_state(), default=str).encode("utf-8"),
                       ctype="application/json; charset=utf-8")
            return

        if path == "/api/state":
            steward = ctx["steward"]
            raw_marks = db.marks() if steward else db.marks(status="read_in")
            safe_marks = []
            for r in raw_marks:
                d = dict(r)
                d.pop("contact", None)
                d.pop("receipt", None)
                safe_marks.append(d)
            safe_reqs = []
            for r in db.requests():
                d = dict(r)
                d.pop("contact_info", None)
                d.pop("receipt", None)
                safe_reqs.append(d)
            snap = {
                "clauses": [dict(r) for r in db.clauses()],
                "marks": safe_marks,
                "queued_marks_count": db.queue_count(),
                "requests": safe_reqs,
                "positions": [dict(r) for r in db.positions()],
                "claims": [dict(r) for r in db.claims()],
                "decisions": [dict(r) for r in db.decisions()],
                "journey": [dict(r) for r in db.journey()],
                "editions": [dict(r) for r in db.editions()],
                "changes": [dict(r) for r in db.changes()],
                "steward": steward,
                "default_braid": db.calculate_braid(1300.0, 1, True),
            }
            self._send(json.dumps(snap).encode("utf-8"),
                       ctype="application/json; charset=utf-8")
            return

        if path == "/api/calculate":
            try:
                rent = float(q.get("rent", ["1300"])[0])
                units = int(q.get("units", ["1"])[0])
                m1pr = q.get("m1pr", ["1"])[0] not in ("0", "false", "False", "no")
            except ValueError:
                self._send(b'{"error":"invalid parameters"}', 400,
                           "application/json; charset=utf-8")
                return
            res = db.calculate_braid(rent, units, m1pr)
            self._send(json.dumps(res).encode("utf-8"),
                       ctype="application/json; charset=utf-8")
            return

        if path == "/tv":
            self._redirect("/present?s=1", extra=[
                ("Set-Cookie",
                 "bp_mode=tv; Path=/; SameSite=Strict; Max-Age=31536000")])
            return

        if path.startswith("/mode/"):
            m = path.split("/", 2)[2]
            if m in MODES + ("auto",):
                default_dest = "/present?s=1" if m == "tv" else "/"
                raw_next = q.get("next", [default_dest])[0]
                nxt = _safe_next(raw_next, default_dest)
                # Switching out of TV while sitting on /present returns cleanly to Desk
                if m != "tv" and nxt.startswith("/present") and "keep=1" not in url.query:
                    nxt = "/"
                self._redirect(nxt, extra=[
                    ("Set-Cookie",
                     f"bp_mode={m}; Path=/; SameSite=Strict; Max-Age=31536000")])
            else:
                self._redirect("/")
            return

        if path == "/steward/toggle":
            nxt = _safe_next(q.get("next", ["/"])[0], "/")
            if ctx["steward"]:
                self._redirect(nxt, extra=[
                    ("Set-Cookie", "bp_steward=; Path=/; SameSite=Strict; Max-Age=0")])
                return
            if ctx["onetap"]:
                tok = make_steward_token()
                self._redirect(nxt, extra=[
                    ("Set-Cookie",
                     f"bp_steward={tok}; Path=/; SameSite=Strict; HttpOnly; Max-Age=86400")])
                return
            self._redirect(f"/steward?next={urllib.parse.quote(nxt, safe='')}")
            return

        if path == "/steward/lock":
            nxt = _safe_next(q.get("next", ["/"])[0], "/")
            self._redirect(nxt, extra=[
                ("Set-Cookie", "bp_steward=; Path=/; SameSite=Strict; Max-Age=0")])
            return

        if path.startswith("/static/"):
            p = _safe_join(STATIC, path[len("/static/"):])
            if not p:
                self._send(b"not found", 404, "text/plain; charset=utf-8")
                return
            ctype = (mimetypes.guess_type(p.name)[0] or
                     "application/octet-stream")
            if p.suffix == ".css":
                ctype = "text/css; charset=utf-8"
            elif p.suffix == ".js":
                ctype = "application/javascript; charset=utf-8"
            self._send(p.read_bytes(), ctype=ctype)
            return

        if path == "/favicon.ico":
            self._send(b"", 204)
            return

        clause_id = q.get("c", [None])[0]
        lens = q.get("lens", ["all"])[0]
        view_style = q.get("view", ["both"])[0]
        posted_flag = q.get("posted", [None])[0] == "1"

        if path == "/calculator":
            try:
                rent = float(q.get("rent", ["1300"])[0])
                units = int(q.get("units", ["1"])[0])
                m1pr = q.get("m1pr", ["1"])[0] not in ("0", "false", "no")
            except ValueError:
                rent, units, m1pr = 1300.0, 1, True
            self._send(views.calculator(rent, units, m1pr, ctx))
            return

        if path == "/present":
            try:
                slide = int(q.get("s", ["1"])[0])
            except ValueError:
                slide = 1
            try:
                rent = float(q.get("rent", ["1300"])[0])
            except ValueError:
                rent = 1300.0
            self._send(views.present(slide, clause_id, rent, ctx,
                                     q.get("notes", ["0"])[0] == "1"))
            return

        if path == "/steward":
            nxt = _safe_next(q.get("next", ["/intake"])[0], "/intake")
            err = q.get("err", [None])[0] == "1"
            self._send(views.steward_page(nxt, err, ctx))
            return

        route = {
            "/": lambda: views.index(ctx),
            "/desk": lambda: views.desk(ctx),
            "/bill": lambda: views.bill(lens, view_style, ctx),
            "/margin": lambda: views.margin(posted_flag, ctx),
            "/intake": lambda: views.intake(ctx),
            "/requests": lambda: views.requests_desk(clause_id, ctx),
            "/positions": lambda: views.positions(ctx),
            "/claims": lambda: views.claims(ctx),
            "/decisions": lambda: views.decisions(ctx),
            "/editions": lambda: views.editions(ctx),
            "/changes": lambda: views.changes_page(
                q.get("s", [None])[0], ctx),
            "/search": lambda: views.search_page(q.get("q", [""])[0], ctx),
            "/track": lambda: views.track_page(q.get("code", [""])[0],
                                               q.get("new", [""])[0], ctx),
            "/teach": lambda: views.teach_page(ctx),
            "/campaign": lambda: views.campaign(ctx),
            "/sign": lambda: views.sign_page(ctx),
            "/help": lambda: views.help_page(ctx),
            "/legal": lambda: views.legal_page(ctx),
            "/packet": lambda: views.packet(ctx),
            "/mark": lambda: views.mark_form_page(
                clause_id, q.get("re", [None])[0],
                q.get("q", [None])[0], q.get("kind", [None])[0], ctx),
        }
        if path == "/your-voice":
            self._redirect("/mark")
            return
        if path in ("/bill/live", "/live"):
            self._redirect("/bill")
            return
        slug = (path[len("/bill/"):] if path.startswith("/bill/")
                else path.lstrip("/"))
        if slug in views.CONTENT_PAGES:
            body = views.content_page(slug, ctx)
            self._send(body if body else views.not_found(ctx),
                       200 if body else 404)
            return
        if path.startswith("/clause/"):
            cid = urllib.parse.unquote(path[len("/clause/"):])
            body = views.clause_view(cid, ctx)
            self._send(body if body else views.not_found(ctx),
                       200 if body else 404)
            return
        self._send(route.get(path, lambda: views.not_found(ctx))(),
                   200 if path in route else 404)

    do_HEAD = do_GET

    # ---------- POST ----------

    def do_POST(self):
        raw_path = urllib.parse.urlparse(self.path).path.rstrip("/") or "/"
        path = self._mount_path(raw_path)
        if path is None:
            self._redirect(MOUNT + raw_path)
            return
        form = self._form()
        if form is None:
            self._send(b"bad request", 400, "text/plain; charset=utf-8")
            return

        if path == "/api/steward":
            code = self._one(form, "code", 200)
            nxt = _safe_next(self._one(form, "next", 300), "/intake")
            onetap_ok = (code == "dev-local" and
                         local_onetap_allowed(self.headers.get("Host", "")))
            code_ok = bool(code) and hmac.compare_digest(code, steward_code())
            if onetap_ok or code_ok:
                tok = make_steward_token()
                self._redirect(nxt, extra=[
                    ("Set-Cookie",
                     f"bp_steward={tok}; Path=/; SameSite=Strict; HttpOnly; Max-Age=86400")])
            else:
                self._send(
                    views.steward_page(nxt, True, self._ctx("/steward")),
                    403,
                )
            return

        if path in ("/api/mark", "/api/request", "/api/sign"):
            if form.get("website"):  # honeypot — only bots fill it
                self._redirect("/margin")
                return
            if not self._rate_ok():
                self._send(b"too many submissions - try again in a few minutes",
                           429, "text/plain; charset=utf-8")
                return

        if path == "/api/mark":
            body = self._one(form, "body")
            if not body:
                self._send(b"a mark with no mark is nothing", 422,
                           "text/plain; charset=utf-8")
                return
            rc = db.add_mark(self._one(form, "clause_id", 40) or None,
                             self._one(form, "kind", 20), body,
                             self._one(form, "name", 200),
                             self._one(form, "contact", 200),
                             self._one(form, "reply_to", 20) or None,
                             self._one(form, "quote", 400) or None,
                             self._one(form, "proposed") or None)
            self._redirect(f"/track?code={rc}&new=mark")
            return

        if path == "/api/mark_action":
            if not self._is_steward():
                self._send(b"steward unlock required for intake triage", 403,
                           "text/plain; charset=utf-8")
                return
            try:
                mid = int(self._one(form, "id", 20))
            except ValueError:
                mid = 0
            if self._one(form, "action", 20) == "retract":
                db.mark_retract(mid, self._one(form, "response", 500) or None)
                self._redirect("/margin")
                return
            db.mark_action(mid, self._one(form, "action", 20),
                           self._one(form, "response"),
                           self._one(form, "responder", 80) or None)
            self._redirect("/intake")
            return

        if path == "/api/request":
            summary = self._one(form, "summary", 400)
            if not summary:
                self._send(b"a request needs a summary", 422,
                           "text/plain; charset=utf-8")
                return
            rc = db.add_request(self._one(form, "req_type", 20), summary,
                                self._one(form, "details"),
                                self._one(form, "clause_id", 40) or None,
                                self._one(form, "org_or_role", 300),
                                self._one(form, "contact", 300))
            self._redirect(f"/track?code={rc}&new=request")
            return

        if path == "/api/request_status":
            if not self._is_steward():
                self._send(b"steward unlock required for request triage", 403,
                           "text/plain; charset=utf-8")
                return
            try:
                db.request_status(int(self._one(form, "id", 20)),
                                  self._one(form, "status", 20),
                                  self._one(form, "note", 500) or None)
            except ValueError:
                pass
            self._redirect("/requests")
            return

        if path == "/api/change":
            if not self._is_steward():
                self._send(b"steward unlock required to record a change", 403,
                           "text/plain; charset=utf-8")
                return
            proposed = self._one(form, "proposed_text", 2000)
            if not proposed:
                self._send(b"a change needs proposed wording", 422,
                           "text/plain; charset=utf-8")
                return
            db.add_change(self._one(form, "clause_id", 40) or None,
                          proposed, self._one(form, "quote_text", 2000),
                          self._one(form, "note", 1000))
            self._redirect("/changes")
            return

        if path == "/api/change_status":
            if not self._is_steward():
                self._send(b"steward unlock required for change triage", 403,
                           "text/plain; charset=utf-8")
                return
            try:
                db.change_action(int(self._one(form, "id", 20)),
                                 self._one(form, "action", 20),
                                 self._one(form, "edition", 20) or None,
                                 self._one(form, "new_text", 4000) or None,
                                 self._one(form, "note", 1000) or None)
            except ValueError:
                pass
            self._redirect("/changes")
            return

        if path == "/api/sign":
            name = self._one(form, "name", 200)
            if not name or self._one(form, "consent", 10) != "yes":
                self._send(b"signing needs a name and the publish consent",
                           422, "text/plain; charset=utf-8")
                return
            rc = db.add_signature(name, self._one(form, "org", 200),
                                  self._one(form, "note", 400),
                                  self._one(form, "email", 200))
            self._redirect(f"/track?code={rc}&new=signature")
            return

        if path == "/api/sign_action":
            if not self._is_steward():
                self._send(b"steward unlock required for the signature book",
                           403, "text/plain; charset=utf-8")
                return
            try:
                db.signature_action(int(self._one(form, "id", 20)),
                                    self._one(form, "action", 20))
            except ValueError:
                pass
            self._redirect("/sign")
            return

        if path == "/api/supporter":
            if not self._is_steward():
                self._send(b"steward unlock required for the allies ledger",
                           403, "text/plain; charset=utf-8")
                return
            if self._one(form, "id"):
                try:
                    db.supporter_stage(int(self._one(form, "id", 20)),
                                       self._one(form, "stage", 20),
                                       self._one(form, "note", 500) or None)
                except ValueError:
                    pass
            else:
                db.add_supporter(self._one(form, "name", 200),
                                 self._one(form, "org", 200),
                                 self._one(form, "role", 200),
                                 self._one(form, "stage", 20),
                                 self._one(form, "district", 120),
                                 self._one(form, "note", 500))
            self._redirect("/campaign")
            return

        if path == "/api/position":
            person = self._one(form, "person", 200)
            provision = self._one(form, "provision", 300)
            if person and provision:
                db.add_position(person, provision,
                                self._one(form, "stance", 20),
                                self._one(form, "source", 300))
            self._redirect("/positions")
            return

        self._send(b"not found", 404, "text/plain; charset=utf-8")


H = Handler  # backwards-compatible alias


def main():
    ap = argparse.ArgumentParser(description="Standalone Bill Platform")
    ap.add_argument("--port", type=int,
                    default=int(os.environ.get("PORT", 8093)))
    ap.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    args = ap.parse_args()
    db.init()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Bill Platform — http://{args.host}:{args.port}  (Ctrl+C to stop)")
    sys.stdout.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
