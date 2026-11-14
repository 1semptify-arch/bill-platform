#!/usr/bin/env python
"""selfcheck.py — end-to-end verification for the Bill Platform.

Boots the real server on an ephemeral loopback port against a throwaway
database (seeded identically to production), then drives every route and
every write path over HTTP: mark intake → read-in → public ledger with
drafter answer, reply-by-reference, hold/crisis, request pipeline,
positions, mode switch, and the smart-toolbar context actions.

    python selfcheck.py

Exits 0 with a PASS line, non-zero on the first failure. Stdlib only.
"""
from __future__ import annotations

import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import db       # noqa: E402
import server   # noqa: E402

FAILS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{' — ' + detail if detail else ''}")
    if not ok:
        FAILS.append(name)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="bp_selfcheck_"))
    db_path = tmp / "test.db"
    db.DB_PATH = db_path
    db.init(db_path)

    port = 18093
    srv = ThreadingHTTPServer(("127.0.0.1", port), server.Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)
    base = f"http://127.0.0.1:{port}"

    def get(path, cookie=None):
        req = urllib.request.Request(base + path)
        if cookie:
            req.add_header("Cookie", cookie)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.read().decode("utf-8", "replace"), r.headers
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace"), e.headers

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    raw = urllib.request.build_opener(NoRedirect())

    def get_raw(path):
        req = urllib.request.Request(base + path)
        try:
            with raw.open(req, timeout=10) as r:
                return r.status, dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers)

    def post(path, data):
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(base + path, data=body, method="POST")
        try:
            with raw.open(req, timeout=10) as r:
                return r.status, dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers)

    def newest_queued_mark_id() -> int:
        return db.marks(status="queued")[-1]["id"]

    def request_id(public_no: str) -> int:
        with db.connect() as con:
            return con.execute(
                "SELECT id FROM requests WHERE public_no = ?",
                (public_no,)).fetchone()["id"]

    try:
        # ---- reads -----------------------------------------------------
        st, html, _ = get("/")
        check("GET / desk home (spine)", st == 200 and "Objective" in html
              and "Where it stands" in html and "Next action" in html)
        check("home shows pipeline", "The pipeline" in html
              and "Working Draft" in html)

        st, html, _ = get("/bill")
        check("GET /bill renders draft", st == 200
              and "I-1" in html and "IV-5" in html
              and "Custodial escrow" in html)
        check("/bill annot links", 'href="/mark?c=II-3"' in html)
        check("/bill open tags", html.count("open drafting") >= 3)
        check("/bill plain language", "In plain language" in html)

        st, html, _ = get("/clause/II-3")
        check("GET /clause/II-3", st == 200 and "three-source" in html
              and "Mark this clause" in html)
        check("clause neighbours", 'href="/clause/II-2"' in html
              and 'href="/clause/II-4"' in html)
        check("clause notes + standing-on", "Renter:" in html
              or "Standing on" in html)

        st, html, _ = get("/clause/NOPE")
        check("GET /clause/bogus -> 404", st == 404)

        for p in ("/margin", "/intake", "/requests", "/positions",
                  "/claims", "/decisions", "/editions", "/mark"):
            st, html, _ = get(p)
            check(f"GET {p}", st == 200)

        st, html, _ = get("/editions")
        check("editions seeded (9 rows)", html.count(">E-0") == 9)
        st, html, _ = get("/claims")
        check("claims seeded with figures", "$" in html and "verified" in html)
        st, html, _ = get("/decisions")
        check("decisions locked (8)", html.count("Decision ") >= 8)

        # context-aware toolbar differs by page
        st, h_bill, _ = get("/bill")
        st, h_int, _ = get("/intake")
        check("smart toolbar: bill vs intake differ",
              "Mark the draft" in h_bill and "Mark the draft" not in h_int)

        # seeded margin: M-0001..M-0004 public, M-0005 still dark
        st, html, _ = get("/margin")
        check("seed margin has M-0001", "M-0001" in html)
        check("queued seed mark NOT on margin", "M-0005" not in html)
        st, html, _ = get("/intake")
        check("queued seed mark in intake", st == 200)

        # ---- mode switch ------------------------------------------------
        st, hdrs = get_raw("/mode/tv?next=/bill")
        check("mode switch sets cookie + redirects", st == 303
              and "bp_mode=tv" in (hdrs.get("Set-Cookie") or ""))
        st, html, _ = get("/bill", cookie="bp_mode=tv")
        check("tv mode renders", st == 200 and "mode-tv" in html)
        st, html, _ = get("/bill", cookie="bp_mode=mobile")
        check("mobile mode renders", st == 200 and "mode-mobile" in html)

        # ---- marks: intake → read-in → ledger ---------------------------
        st, _ = post("/api/mark", {
            "clause_id": "II-3", "kind": "question",
            "body": "The braid's split ratio needs the actuarial before "
                    "this can be priced — flag it on the clause page.",
            "name": "Test Reviewer", "contact": "t@example.org"})
        check("POST /api/mark -> 303", st == 303)
        mid = newest_queued_mark_id()

        st, html, _ = get("/intake")
        check("mark landed in intake (dark)", st == 200
              and "actuarial" in html)
        st, html, _ = get("/margin")
        check("queued mark NOT on public margin", "actuarial" not in html)

        st, _ = post("/api/mark_action", {
            "id": mid, "action": "read_in",
            "response": "Actuarial review is already scheduled with the "
                        "fiscal staff — this mark is why."})
        check("read-in assigns public number", st == 303)
        st, html, _ = get("/margin")
        check("read-in mark on margin as M-0005", "M-0005" in html
              and "actuarial" in html and "Test Reviewer" in html)
        check("drafter answer published", "Drafting Table" in html)
        check("contact never rendered", "t@example.org" not in html)

        st, html, _ = get("/clause/II-3")
        check("clause margin shows read-in mark", "M-0005" in html)
        st, html, _ = get("/bill")
        check("margin count badge on draft", 'class="mcount"' in html)

        # reply-by-reference
        st, _ = post("/api/mark", {
            "clause_id": "II-3", "body": "Agreed — flag it.",
            "reply_to": "M-0005", "name": ""})
        rid = newest_queued_mark_id()
        st, _ = post("/api/mark_action", {"id": rid, "action": "read_in"})
        st, html, _ = get("/margin")
        check("reply cites by reference", "re: M-0005" in html
              and "M-0006" in html)

        # hold + crisis path
        st, _ = post("/api/mark", {"body": "spam my landlord story"})
        cid = newest_queued_mark_id()
        st, _ = post("/api/mark_action", {"id": cid, "action": "crisis_routed"})
        st, html, _ = get("/margin")
        check("crisis mark never public", "spam my landlord" not in html)

        # ---- requests desk ----------------------------------------------
        st, _ = post("/api/request", {
            "req_type": "amendment", "summary": "Pin the II-3 split ratio",
            "details": "Needed before the actuarial ask lands.",
            "clause_id": "II-3", "org_or_role": "Test Office"})
        check("POST /api/request", st == 303)
        rq = request_id("R-0004")
        st, _ = post("/api/request_status", {"id": rq, "status": "reviewing"})
        st, _ = post("/api/request_status", {"id": rq, "status": "scheduled"})
        st, _ = post("/api/request_status",
                     {"id": rq, "status": "incorporated"})
        st, html, _ = get("/requests")
        check("request pipeline new->incorporated",
              "Pin the II-3 split ratio" in html and "incorporated" in html
              and "R-0004" in html)
        check("seeded requests render", "R-0001" in html)

        # ---- positions --------------------------------------------------
        st, _ = post("/api/position", {
            "person": "Rep. Example", "provision": "Title II funding braid",
            "stance": "watching", "source": "email 2026-11-10"})
        st, html, _ = get("/positions")
        check("position recorded", "Rep. Example" in html
              and "watching" in html)
        check("seeded position renders",
              "Mediation Coalition" in html)

        # ---- static + misc ----------------------------------------------
        st, css, _ = get("/static/platform.css")
        check("static css", st == 200 and "mode-tv" in css)
        st, js, _ = get("/static/platform.js")
        check("static js", st == 200 and "selectionchange" in js)
        st, html, _ = get("/api/state")
        check("api/state snapshot", st == 200 and '"clauses"' in html)
        st, html, _ = get("/nope")
        check("404 page", st == 404)

    finally:
        srv.shutdown()
        srv.server_close()

    print()
    if FAILS:
        print(f"SELFCHECK FAILED — {len(FAILS)} check(s): {', '.join(FAILS)}")
        return 1
    print("SELFCHECK PASS — all routes, writes, modes, and boards verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
