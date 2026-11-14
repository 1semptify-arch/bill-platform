#!/usr/bin/env python
"""server.py — standalone Bill Platform, loopback only on 127.0.0.1:8093.

Routes:

    /                    the desk — spine, pipeline, evidence
    /bill                the draft, read through
    /clause/<id>         one clause + its margin + mark form
    /mark                the Inkwell (mark form; ?c=, ?re=, ?q=)
    /margin              the public ledger of read-in marks
    /intake              triage queue — read in / hold / crisis route
    /requests            requests desk + new-request form
    /positions           who stands where
    /claims              claims ledger
    /decisions           locked decisions
    /editions            change ledger
    /mode/<m>?next=<p>   set screen mode (desk|tv|mobile), redirect
    /static/<file>       platform.css, platform.js

Posts (form-encoded, 303 redirect):
    /api/mark            enter a mark (lands queued — never public)
    /api/mark_action     read_in | held | crisis_routed (+optional answer)
    /api/request         enter a request
    /api/request_status  advance/decline a request
    /api/position        record a position

GET /api/state returns a JSON snapshot for tooling.

Run:  python server.py        (or: python server.py --port 8093)
Stop: Ctrl+C
"""
from __future__ import annotations

import argparse
import mimetypes
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

import db
import views

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
MODES = ("desk", "tv", "mobile")
MAX_POST = 64 * 1024


def _safe_join(root: Path, rel: str) -> Path | None:
    """Resolve rel inside root; refuse escapes and non-files."""
    p = (root / urllib.parse.unquote(rel).lstrip("/")).resolve()
    try:
        p.relative_to(root.resolve())
    except ValueError:
        return None
    return p if p.is_file() else None


class Handler(BaseHTTPRequestHandler):
    server_version = "BillPlatform/1.0"
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
        self._send(b"", 303, extra=[("Location", location)] + (extra or []))

    def _mode(self) -> str:
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("bp_mode="):
                m = part[8:]
                return m if m in MODES else "desk"
        return "desk"

    def _form(self) -> dict[str, list[str]] | None:
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_POST:
            return None
        return urllib.parse.parse_qs(
            self.rfile.read(n).decode("utf-8", "replace"),
            keep_blank_values=True, max_num_fields=64)

    @staticmethod
    def _one(form: dict, key: str, maxlen: int = 8000) -> str:
        return (form.get(key, [""])[0] or "")[:maxlen].strip()

    def log_message(self, fmt, *args):  # quieter, but not silent
        print(f"[bill-platform] {self.address_string()} {fmt % args}")

    # ---------- GET ----------

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path.rstrip("/") or "/"
        q = urllib.parse.parse_qs(url.query)
        mode = self._mode()

        if path == "/api/state":
            import json as _json
            snap = {
                "clauses": [dict(r) for r in db.clauses()],
                "marks": [dict(r) for r in db.marks()],
                "requests": [dict(r) for r in db.requests()],
                "positions": [dict(r) for r in db.positions()],
                "claims": [dict(r) for r in db.claims()],
                "decisions": [dict(r) for r in db.decisions()],
                "journey": [dict(r) for r in db.journey()],
                "editions": [dict(r) for r in db.editions()],
            }
            self._send(_json.dumps(snap).encode(),
                       ctype="application/json; charset=utf-8")
            return

        if path.startswith("/mode/"):
            m = path.split("/", 2)[2]
            if m in MODES:
                nxt = q.get("next", ["/"])[0]
                if not nxt.startswith("/") or nxt.startswith("//"):
                    nxt = "/"
                self._redirect(nxt, extra=[
                    ("Set-Cookie",
                     f"bp_mode={m}; Path=/; SameSite=Strict; Max-Age=31536000")])
            else:
                self._redirect("/")
            return

        if path.startswith("/static/"):
            p = _safe_join(STATIC, path[len("/static/"):])
            if not p:
                self._send(b"not found", 404, "text/plain; charset=utf-8")
                return
            ctype = (mimetypes.guess_type(p.name)[0] or
                     "application/octet-stream")
            self._send(p.read_bytes(), ctype=ctype)
            return

        if path == "/favicon.ico":
            self._send(b"", 204)
            return

        clause_id = q.get("c", [None])[0]
        route = {
            "/": lambda: views.home(mode, path),
            "/bill": lambda: views.bill(mode, path),
            "/margin": lambda: views.margin(mode, path),
            "/intake": lambda: views.intake(mode, path),
            "/requests": lambda: views.requests_desk(clause_id, mode, path),
            "/positions": lambda: views.positions(mode, path),
            "/claims": lambda: views.claims(mode, path),
            "/decisions": lambda: views.decisions(mode, path),
            "/editions": lambda: views.editions(mode, path),
            "/mark": lambda: views.mark_form_page(
                clause_id, q.get("re", [None])[0],
                q.get("q", [None])[0], mode, path),
        }
        if path.startswith("/clause/"):
            cid = urllib.parse.unquote(path[len("/clause/"):])
            body = views.clause_view(cid, mode, path)
            self._send(body if body else views.not_found(mode, path),
                       200 if body else 404)
            return
        self._send(route.get(path, lambda: views.not_found(mode, path))(),
                   200 if path in route else 404)

    do_HEAD = do_GET

    # ---------- POST ----------

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path.rstrip("/") or "/"
        form = self._form()
        if form is None:
            self._send(b"bad request", 400, "text/plain; charset=utf-8")
            return

        if path == "/api/mark":
            body = self._one(form, "body")
            if not body:
                self._send(b"a mark with no mark is nothing", 422,
                           "text/plain; charset=utf-8")
                return
            db.add_mark(self._one(form, "clause_id", 40) or None,
                        self._one(form, "kind", 20), body,
                        self._one(form, "name", 200),
                        self._one(form, "contact", 200),
                        self._one(form, "reply_to", 20) or None,
                        self._one(form, "quote", 400) or None,
                        self._one(form, "proposed") or None)
            self._redirect("/margin?posted=1")
            return

        if path == "/api/mark_action":
            try:
                mid = int(self._one(form, "id", 20))
            except ValueError:
                mid = 0
            db.mark_action(mid, self._one(form, "action", 20),
                           self._one(form, "response"))
            self._redirect("/intake")
            return

        if path == "/api/request":
            summary = self._one(form, "summary", 400)
            if not summary:
                self._send(b"a request needs a summary", 422,
                           "text/plain; charset=utf-8")
                return
            db.add_request(self._one(form, "req_type", 20), summary,
                           self._one(form, "details"),
                           self._one(form, "clause_id", 40) or None,
                           self._one(form, "org_or_role", 300),
                           self._one(form, "contact", 300))
            self._redirect("/requests")
            return

        if path == "/api/request_status":
            try:
                db.request_status(int(self._one(form, "id", 20)),
                                  self._one(form, "status", 20),
                                  self._one(form, "note", 500) or None)
            except ValueError:
                pass
            self._redirect("/requests")
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


def main():
    ap = argparse.ArgumentParser(description="Standalone Bill Platform")
    ap.add_argument("--port", type=int, default=8093)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    db.init()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Bill Platform — http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
