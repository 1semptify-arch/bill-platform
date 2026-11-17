#!/usr/bin/env python
"""selfcheck.py — end-to-end verification for the Bill Platform.

Boots the real server on an ephemeral loopback port against a throwaway
database (seeded identically to production), then drives every route,
screen mode, calculator endpoint, steward security gate, and write path
over HTTP:
  - Desk reading spine + 2-column desktop rail
  - Bill reader + Audience Lens + Plain/Statute toggle
  - Live 3-source Funding Braid calculator + /api/calculate math check
  - Dedicated 8-slide 16:9 TV / Presentation Stage (/present + /tv)
  - Mobile / Tablet mode + thumb-zone bottom navigation bar
  - Steward gate: dark intake when locked (403 on triage POSTs), 1-tap &
    passcode unlock, read-in -> M-number + drafter answer, citation reply,
    crisis routing, request pipeline, positions, and PII redaction.

    python selfcheck.py

Exits 0 with SELFCHECK PASS, non-zero on any failure. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
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

    def get_raw(path, cookie=None):
        req = urllib.request.Request(base + path)
        if cookie:
            req.add_header("Cookie", cookie)
        try:
            with raw.open(req, timeout=10) as r:
                return r.status, dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers)

    def post(path, data, cookie=None):
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(base + path, data=body, method="POST")
        if cookie:
            req.add_header("Cookie", cookie)
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
        # ---- 1. Desk & core reads --------------------------------------
        st, html, _ = get("/")
        check("GET / index: introduction + how-it-works", st == 200
              and "Introduction" in html and "How it works" in html)
        check("index: living document badge + semptify link",
              "Living document" in html and "semptify.org" in html
              and "Presented by" in html)

        st, html, _ = get("/desk")
        check("GET /desk (spine)", st == 200 and "Objective" in html
              and "Where it stands" in html and "Next action" in html)
        check("desk shows pipeline + rail", "The pipeline" in html
              and "desk-rail" in html and "Working Draft" in html)

        st, html, _ = get("/bill")
        check("GET /bill renders 23 clauses", st == 200
              and "I-1" in html and "IV-5" in html
              and "Custodial escrow" in html)
        check("/bill annot links", 'href="/mark?c=II-3"' in html)
        check("/bill open tags", html.count("open drafting") >= 3)
        check("/bill plain language", "In plain language" in html)

        st, html_lens, _ = get("/bill?lens=lawmaker&view=plain")
        check("/bill lawmaker lens + plain view", st == 200
              and "For lawmakers" in html_lens
              and "statute-copy" not in html_lens)

        st, html, _ = get("/clause/II-3")
        check("GET /clause/II-3", st == 200 and "Three-source" in html
              and "Mark this clause" in html)
        check("clause neighbours", 'href="/clause/II-2"' in html
              and 'href="/clause/II-4"' in html)
        check("clause notes + standing-on", "Renter:" in html
              and "Standing on" in html)

        st, html, _ = get("/clause/NOPE")
        check("GET /clause/bogus -> 404", st == 404)

        for p in ("/calculator", "/present", "/margin", "/intake",
                  "/requests", "/positions", "/claims", "/decisions",
                  "/editions", "/mark", "/steward"):
            st, html, _ = get(p)
            check(f"GET {p}", st == 200)

        st, html, _ = get("/editions")
        check("editions seeded (9 rows)", html.count(">E-0") == 9)
        st, html, _ = get("/claims")
        check("claims seeded with figures", "$15.33/mo" in html and "verified" in html)
        st, html, _ = get("/decisions")
        check("decisions locked (8)", html.count("Decision ") >= 8)

        # ---- 2. Funding Braid Calculator & API math --------------------
        st, calc_json, _ = get("/api/calculate?rent=1300&units=10&m1pr=1")
        calc = json.loads(calc_json)
        check("calculator base math ($1,300)", st == 200
              and calc["deposit_float_mo"] == 3.25
              and calc["total_pool_mo"] == 15.33
              and calc["stress_fraud_mo"] == 21.23
              and calc["stress_recession_mo"] == 30.0
              and calc["renter_out_of_pocket_mo"] == 0.0)

        st, calc_over, _ = get("/api/calculate?rent=2600&units=1&m1pr=0")
        calc2 = json.loads(calc_over)
        check("calculator scales with rent & over-cap M1PR", st == 200
              and calc2["deposit_float_mo"] == 6.50
              and calc2["total_pool_mo"] == 30.66
              and calc2["renter_out_of_pocket_mo"] > 0)

        # ---- 3. Context-Aware Smart Toolbar & 3 Screen Modes -----------
        st, h_bill, _ = get("/bill")
        st, h_calc, _ = get("/calculator")
        check("smart toolbar swaps actions per context",
              "Mark the draft" in h_bill and "Renter lens" in h_bill
              and "Mark the draft" not in h_calc and "$1,300 base" in h_calc)

        st, hdrs = get_raw("/tv")
        check("/tv sets bp_mode=tv & opens /present?s=1", st == 303
              and "bp_mode=tv" in (hdrs.get("Set-Cookie") or "")
              and hdrs.get("Location") == "/present?s=1")

        for s_num in (1, 4, 7, 8):
            st, s_html, _ = get(f"/present?s={s_num}", cookie="bp_mode=tv")
            check(f"TV presentation slide {s_num}/8", st == 200
                  and "stage-slide" in s_html and f"Slide {s_num} of 8" in s_html)

        st, m_html, _ = get("/bill", cookie="bp_mode=mobile")
        check("Mobile mode renders thumb-zone bottom bar", st == 200
              and "mode-mobile" in m_html and 'class="mobile-bar"' in m_html)

        st, a_html, _ = get("/bill")  # no cookie -> auto default
        check("Auto mode default: body flagged for JS viewport follow",
              st == 200 and 'data-mode-auto="1"' in a_html)
        st, hdrs = get_raw("/mode/auto?next=/bill")
        check("/mode/auto sets bp_mode=auto", st == 303
              and "bp_mode=auto" in (hdrs.get("Set-Cookie") or ""))

        # ---- 4. Steward Gate + Dark Intake -> Read-In -> Public Margin -
        st, html, _ = get("/margin")
        check("seed margin has M-0001..M-0004", "M-0001" in html and "M-0004" in html)
        check("queued seed mark NOT on margin", "Appellate Practitioner" not in html)

        # Submit new mark publicly (zero login required)
        st, _ = post("/api/mark", {
            "clause_id": "II-3", "kind": "question",
            "body": "The braid's split ratio needs the actuarial before "
                    "this can be priced — flag it on the clause page.",
            "name": "Test Reviewer", "contact": "t@example.org"})
        check("POST /api/mark (public, zero login) -> 303", st == 303)
        mid = newest_queued_mark_id()

        # Without steward cookie, intake keeps queued text dark & blocks triage POSTs
        st, locked_int, _ = get("/intake")
        check("locked /intake hides raw queued mark body",
              st == 200 and "Unlock Steward" in locked_int
              and "actuarial before this can be priced" not in locked_int)

        st, _ = post("/api/mark_action", {"id": mid, "action": "read_in"})
        check("unauthenticated POST /api/mark_action -> 403", st == 403)
        st, _ = post("/api/request_status", {"id": 1, "status": "reviewing"})
        check("unauthenticated POST /api/request_status -> 403", st == 403)
        st, _ = post("/api/steward", {"code": "wrong-passcode"})
        check("wrong steward passcode -> 403", st == 403)

        # Unlock Steward via passcode (and verify 1-tap loopback toggle)
        st, st_hdrs = post("/api/steward", {"code": "mn-steward", "next": "/intake"})
        steward_cookie = (st_hdrs.get("Set-Cookie") or "").split(";", 1)[0]
        check("valid steward passcode sets bp_steward cookie",
              st == 303 and steward_cookie.startswith("bp_steward="))

        st, t_hdrs = get_raw("/steward/toggle?next=/intake")
        check("loopback 1-tap /steward/toggle sets cookie",
              st == 303 and "bp_steward=" in (t_hdrs.get("Set-Cookie") or ""))

        st, open_int, _ = get("/intake", cookie=steward_cookie)
        check("unlocked /intake reveals queued mark for triage",
              st == 200 and "actuarial before this can be priced" in open_int)

        st, html, _ = get("/margin")
        check("queued mark still NOT on public margin",
              "actuarial before this can be priced" not in html)

        # Steward reads in mark with an official answer
        st, _ = post("/api/mark_action", {
            "id": mid, "action": "read_in",
            "response": "Actuarial review is scheduled with fiscal staff.",
            "responder": "Drafting Table",
        }, cookie=steward_cookie)
        check("steward read-in assigns M-number", st == 303)

        st, html, _ = get("/margin")
        check("read-in mark on public margin as M-0005", "M-0005" in html
              and "actuarial before this can be priced" in html
              and "Test Reviewer" in html)
        check("drafter answer published", "Actuarial review is scheduled" in html)
        check("contact never rendered on margin", "t@example.org" not in html)

        st, html, _ = get("/clause/II-3")
        check("clause margin shows read-in mark", "M-0005" in html)
        st, html, _ = get("/bill")
        check("margin count badge on draft", 'class="mcount"' in html)

        # Reply-by-reference
        st, _ = post("/api/mark", {
            "clause_id": "II-3", "body": "Agreed — flag it.",
            "reply_to": "M-0005", "name": ""})
        rid = newest_queued_mark_id()
        st, _ = post("/api/mark_action", {"id": rid, "action": "read_in"},
                     cookie=steward_cookie)
        st, html, _ = get("/margin")
        check("reply cites by reference", "M-0005" in html and "M-0006" in html)

        # ---- 4c. Moderation: redact PII, edit abuse, protect criticism --
        st, _ = post("/api/mark", {
            "clause_id": "II-3",
            "body": "This bill is wrong on the math, full stop. Call me.",
            "name": "Jane Critic", "contact": "jane@example.org"})
        mod_id = newest_queued_mark_id()
        st, _ = post("/api/mark_action", {"id": mod_id, "action": "read_in"},
                     cookie=steward_cookie)
        st, html, _ = get("/margin")
        check("critical mark publishes with name", "Jane Critic" in html
              and "wrong on the math" in html)

        st, _ = post("/api/mark_action", {"id": mod_id, "action": "redact"})
        check("unauthenticated redact -> 403", st == 403)

        st, _ = post("/api/mark_action", {
            "id": mod_id, "action": "redact", "back": "/margin"},
            cookie=steward_cookie)
        check("steward redact -> redirect", st == 303)
        st, html, _ = get("/margin")
        check("redacted mark shows 'name withheld'",
              "name withheld by stewards" in html
              and "Jane Critic" not in html
              and "wrong on the math" in html)
        st, html, _ = get("/intake", cookie=steward_cookie)
        check("redacted contact gone steward-side too",
              "jane@example.org" not in html)

        st, _ = post("/api/mark_action", {
            "id": mod_id, "action": "edit", "back": "/margin",
            "new_body": "This bill is wrong on the math, full stop.",
            "note": "contact info stripped"}, cookie=steward_cookie)
        st, html, _ = get("/margin")
        check("edited mark shows steward edit + public reason",
              "edited by stewards" in html
              and "contact info stripped" in html
              and "Call me" not in html)
        st, st_data, _ = get("/api/state")
        check("edited body in public state; original stays steward-side",
              "Call me" not in st_data and "edited by stewards" not in st_data)

        # Criticism of substance is protected — a harsh mark publishes intact
        st, _ = post("/api/mark", {
            "body": "This clause is a scam and the drafters know it."})
        crit_id = newest_queued_mark_id()
        st, _ = post("/api/mark_action", {"id": crit_id, "action": "read_in"},
                     cookie=steward_cookie)
        st, html, _ = get("/margin")
        check("harsh criticism publishes unedited",
              "a scam and the drafters know it" in html)

        # Crisis routing keeps personal emergency off public ledger
        st, _ = post("/api/mark", {"body": "emergency eviction tomorrow help"})
        cid = newest_queued_mark_id()
        st, _ = post("/api/mark_action", {"id": cid, "action": "crisis_routed"},
                     cookie=steward_cookie)
        st, html, _ = get("/margin")
        check("crisis-routed mark never public",
              "emergency eviction tomorrow" not in html)

        # ---- 4b. Change ledger: edit marks auto-record, steward resolves -
        st, _ = post("/api/mark", {
            "clause_id": "I-4", "kind": "edit",
            "quote": "not recoverable from the tenant",
            "proposed": "not recoverable from the tenant or any successor",
            "body": "Close the assignee loophole in no-subrogation."})
        eid = newest_queued_mark_id()
        st, _ = post("/api/mark_action", {"id": eid, "action": "read_in"},
                     cookie=steward_cookie)
        st, html, _ = get("/changes")
        check("read-in edit mark auto-records CH-0001 proposed", st == 200
              and "CH-0001" in html and "proposed" in html
              and "not recoverable from the tenant or any successor" in html)

        st, html, _ = get("/clause/I-4")
        check("clause page shows change history", "CH-0001" in html
              and "Change history" in html)

        st, _ = post("/api/change_status", {"id": 1, "action": "incorporated"})
        check("unauthenticated POST /api/change_status -> 403", st == 403)

        st, _ = post("/api/change_status", {
            "id": 1, "action": "incorporated", "edition": "E-10"},
            cookie=steward_cookie)
        check("resolve without public reason -> 422", st == 422)

        pst, _ = post("/api/change_status", {
            "id": 1, "action": "incorporated", "edition": "E-10",
            "note": "Closes the assignee loophole; discussion record clean.",
            "resolved_by": "Steward A. Test",
            "new_text": "A claim paid from the pool or escrow is final and is"
                        " not recoverable from the tenant or any successor."},
            cookie=steward_cookie)
        st, html, _ = get("/changes")
        check("steward incorporates change w/ edition + diff", pst == 303
              and "E-10" in html and "incorporated" in html
              and "any successor" in html)
        check("diff keeps old text visible", "Was:" in html and "Now:" in html)
        check("consent-named steward on the record",
              "resolved by <b>Steward A. Test</b>" in html)

        st, _ = post("/api/change", {
            "clause_id": "II-1", "proposed_text": "Extend coverage term to 9 months",
            "note": "From R-0001 briefing"}, cookie=steward_cookie)
        st, html, _ = get("/changes")
        check("steward manual change record -> CH-0002", "CH-0002" in html
              and "Extend coverage term" in html)

        # ---- 4c. Open-window discussion on a proposal ------------------
        # Named contributor weighs in on CH-0002 (id=2) — name stays
        # steward-side; only steward names publish on this record.
        st, _ = post("/api/mark", {
            "change_id": "2", "body": "Nine months is too long — six keeps "
            "the pool funded.", "name": "Secret Squirrel",
            "contact": "sq@example.org"})
        check("discussion mark on open proposal -> 303", st == 303)
        did = newest_queued_mark_id()
        st, _ = post("/api/mark_action", {"id": did, "action": "read_in"},
                     cookie=steward_cookie)
        st, html, _ = get("/changes")
        check("discussion mark publishes on the change card", st == 200
              and "Nine months is too long" in html)
        check("contributor name withheld on change record",
              "a contributor" in html and "Secret Squirrel" not in html)
        st, html, _ = get("/margin")
        check("name withheld in margin too",
              "a contributor" in html and "Secret Squirrel" not in html)
        st, body, _ = get("/api/state")
        check("/api/state strips discussion author",
              "Secret Squirrel" not in body)

        # Closed window rejects new discussion marks.
        st, _ = post("/api/change", {
            "clause_id": "I-1", "proposed_text": "Reword the header",
            "closes_at": "2000-01-01"}, cookie=steward_cookie)
        st, _ = post("/api/mark", {"change_id": "3", "body": "too late"})
        check("mark on closed-window proposal -> 422", st == 422)

        # ---- 4d. Steward roster — the committee -----------------------
        st, _ = post("/api/steward_roster",
                     {"roster_action": "add", "name": "Test Steward"})
        check("unauthenticated roster add -> 403", st == 403)
        st, _ = post("/api/steward_roster",
                     {"roster_action": "add", "name": "Test Steward",
                      "role": "resolutions"}, cookie=steward_cookie)
        st, html, _ = get("/stewards")
        check("steward added to public roster", st == 200
              and "Test Steward" in html and "resolutions" in html)
        # ---- 4e. Per-steward codes ------------------------------------
        st, hdrs = post("/api/steward_roster",
                        {"roster_action": "add", "name": "Coded Steward"},
                        cookie=steward_cookie)
        loc = hdrs.get("Location", "")
        m_code = re.search(r"issued=(st-\w+)", loc)
        code = m_code.group(1) if m_code else ""
        check("roster add issues a one-time code", st == 303
              and code.startswith("st-"))
        st, html, _ = get("/stewards?issued=" + code,
                          cookie=steward_cookie)
        check("issued code shown once on roster page", code in html)

        # personal code unlocks steward mode bound to that steward
        st, hdrs = post("/api/steward", {"code": code, "next": "/changes"})
        scode = (hdrs.get("Set-Cookie") or "")
        check("personal code unlock -> session cookie", st == 303
              and "sw" in scode and "bp_steward" in scode)
        pers_cookie = scode.split(";")[0].split("=", 1)[1]
        st, html, _ = get("/changes", cookie="bp_steward=" + pers_cookie)
        check("resolution form prefills steward name",
              'value="Coded Steward"' in html)

        # retiring revokes the code
        st, _ = post("/api/steward_roster",
                     {"roster_action": "retire", "id": "2"},
                     cookie=steward_cookie)
        st, _ = post("/api/steward", {"code": code, "next": "/changes"})
        check("retired steward code rejected", st == 403)

        st, _ = post("/api/steward_roster",
                     {"roster_action": "retire", "id": "1"},
                     cookie=steward_cookie)
        st, html, _ = get("/stewards")
        check("retired steward leaves public roster",
              "Test Steward" not in html)

        # ---- 5. Requests Desk + Steward Status Pipeline ----------------
        st, _ = post("/api/request", {
            "req_type": "amendment", "summary": "Pin the II-3 split ratio",
            "details": "Needed before the actuarial ask lands.",
            "clause_id": "II-3", "org_or_role": "Test Office",
            "contact": "private-req@example.org"})
        check("POST /api/request (public) -> 303", st == 303)
        rq = request_id("R-0004")
        st, _ = post("/api/request_status",
                     {"id": rq, "status": "reviewing", "note": "Scoped"},
                     cookie=steward_cookie)
        st, _ = post("/api/request_status", {"id": rq, "status": "scheduled"},
                     cookie=steward_cookie)
        st, _ = post("/api/request_status", {"id": rq, "status": "incorporated"},
                     cookie=steward_cookie)
        st, html, _ = get("/requests")
        check("request pipeline new->incorporated",
              "Pin the II-3 split ratio" in html and "incorporated" in html
              and "R-0004" in html and "Scoped" in html)
        check("request contact never rendered", "private-req@example.org" not in html)

        # ---- 6. Positions + Static + Sanitized State Snapshot ----------
        st, _ = post("/api/position", {
            "person": "Rep. Example", "provision": "Title II funding braid",
            "stance": "watching", "source": "email 2026-11-10"})
        st, html, _ = get("/positions")
        check("position recorded", "Rep. Example" in html and "watching" in html)

        # ---- 6. v1.1 coverage: permalinks, retract, receipts, search,
        #    shareable calculator, honeypot+rate, meta, export, teach ----
        st, html, _ = get("/margin")
        check("margin marks have permalink anchors + links",
              'id="M-0005"' in html and 'href="/margin#M-0005"' in html)

        # receipt -> /track round trip
        st, hdrs = post("/api/mark", {"clause_id": "I-1",
                        "body": "receipt test mark"})
        loc = hdrs.get("Location", "")
        check("mark POST redirects to /track with receipt code",
              st == 303 and loc.startswith("/track?code="))
        code = urllib.parse.parse_qs(
            urllib.parse.urlparse(loc).query)["code"][0]
        st, html, _ = get(loc)
        check("track page shows private receipt + intake status",
              st == 200 and code in html and "dark intake" in html)
        check("track exposes status only, not contact/body",
              "receipt test mark" not in html)

        # steward retract keeps the record visible, struck through
        mid2 = newest_queued_mark_id()
        post("/api/mark_action", {"id": mid2, "action": "read_in"},
             cookie=steward_cookie)
        st, _ = post("/api/mark_action", {
            "id": mid2, "action": "retract",
            "response": "withdrawn at submitter's request"},
            cookie=steward_cookie)
        st, html, _ = get("/margin")
        check("retracted mark stays visible, struck through",
              st == 303 or "retracted" in html)

        st, html, _ = get("/search?q=subrogation")
        check("search finds clause + margin + change hits", st == 200
              and "I-4" in html and "result(s)" in html)

        st, html, _ = get("/calculator?rent=2000&units=48&m1pr=0")
        check("calculator honors shareable URL params", st == 200
              and 'value="2000"' in html and 'value="48"' in html)

        st, html, _ = get("/")
        check("og/description meta + skip link present", st == 200
              and 'property="og:title"' in html and 'class="skip"' in html)

        st, html, _ = get("/teach")
        check("teach page renders guided stops with prompts", st == 200
              and "Talk about" in html and "Stop 01" in html)

        st, html, _ = get("/present?s=4&notes=1", cookie="bp_mode=tv")
        check("speaker notes render with ?notes=1", st == 200
              and "speaker-notes" in html and "slider" in html)

        st, _ = post("/api/mark", {"body": "bot spam", "website": "x"})
        check("honeypot silently drops bot submissions", st == 303
              and db.marks(status="queued")[-1]["body"] != "bot spam")

        st, _ = get_raw("/api/export")
        check("/api/export locked without steward", st == 403)
        st, hdrs = get_raw("/api/export", cookie=steward_cookie)
        check("/api/export serves full backup to steward", st == 200)

        # ---- 7. Campaign: allies ledger + testimony packet + mailto ----
        st, html, _ = get("/campaign")
        check("campaign hub renders journey + allies", st == 200
              and "Carry the bill" in html and "Amy Klobuchar" in html
              and "endorsed" in html and "mailto:" in html)
        st, _ = post("/api/supporter", {"name": "X", "stage": "endorsed"})
        check("unauthenticated POST /api/supporter -> 403", st == 403)
        st, _ = post("/api/supporter", {
            "name": "Test Ally", "org": "Test Org", "stage": "contacted"},
            cookie=steward_cookie)
        st, html, _ = get("/campaign")
        check("steward adds ally to ledger", "Test Ally" in html)
        st, _ = post("/api/supporter", {"id": 2, "stage": "contacted"},
                     cookie=steward_cookie)
        st, html, _ = get("/packet")
        check("testimony packet groups read-in marks by clause",
              st == 200 and "Testimony packet" in html
              and "M-0005" in html and "I-4" in html)
        st, html, _ = get("/clause/I-4")
        check("clause has send-to-legislator mailto", "mailto:" in html
              and "carry this bill" in urllib.parse.unquote(html))

        # signature book: voluntary, dark until steward publishes
        st, _ = post("/api/sign", {"name": "No Consent Person"})
        check("signature requires name + consent", st == 422)
        st, hdrs = post("/api/sign", {
            "name": "Dena C.", "org": "Frogtown",
            "note": "Deposits should protect renters.",
            "email": "dena@example.org", "consent": "yes"})
        check("signature POST redirects to /track with receipt", st == 303
              and "/track?code=" in (hdrs.get("Location") or ""))
        sig_rc = urllib.parse.parse_qs(urllib.parse.urlparse(
            hdrs.get("Location", "")).query)["code"][0]
        st, html, _ = get("/sign")
        check("queued signature stays dark publicly", st == 200
              and "Dena C." not in html and "The book" in html)
        st, exp, _ = get("/api/export", cookie=steward_cookie)
        sig_id = json.loads(exp)["signatures"][-1]["id"]
        st, _ = post("/api/sign_action",
                     {"id": sig_id, "action": "published"})
        check("unauthenticated POST /api/sign_action -> 403", st == 403)
        st, _ = post("/api/sign_action",
                     {"id": sig_id, "action": "published"},
                     cookie=steward_cookie)
        st, html, _ = get("/sign")
        check("steward publishes signature, email stays hidden", st == 200
              and "Dena C." in html and "Frogtown" in html
              and "S-0001" in html and "dena@example.org" not in html)
        st, html, _ = get(f"/track?code={sig_rc}")
        check("receipt shows published signature", st == 200
              and "S-0001" in html)

        # help + legal pages and the MN flag
        st, html, _ = get("/help")
        check("help page lists crisis + public help lines", st == 200
              and "988" in html and "612-728-5767" in html
              and "1-800-333-4673" in html and "aa.org" in html
              and "debtorsanonymous.org" in html)
        st, html, _ = get("/legal")
        check("legal page covers privacy + terms + license", st == 200
              and "Privacy" in html and "Terms" in html
              and "CC0" in html and "MIT License" in html
              and "bp_mode" in html)
        st, html, _ = get("/")
        check("MN flag on hero + footer links", st == 200
              and "mn-flag.svg" in html and "/help" in html
              and "/legal" in html)
        st, flag, _ = get("/static/mn-flag.svg")
        check("MN flag asset serves", st == 200 and "<svg" in flag)

        # consolidated mirror content — same source, platform chrome
        for slug in ("research", "history", "providers", "brief",
                     "classroom", "press", "myths"):
            st, html, _ = get(f"/bill/{slug}")
            check(f"content page /bill/{slug} serves in platform chrome",
                  st == 200 and "rail" in html)
        st, html, _ = get("/what-the-bill-changes")
        check("what-the-bill-changes serves", st == 200)
        st2, hdrs2, _ = get("/your-voice")
        check("your-voice redirects to platform mark", st2 in (200, 303))
        st3, hdrs3, _ = get("/bill/live")
        check("bill/live redirects to platform bill", st3 in (200, 303))
        st, html, _ = get("/bill/history")
        check("history page links live ledger", st == 200
              and "/editions" in html and "/changes" in html)

        # rate limit: flood /api/mark — 12th+ within 5 min must 429
        flood = [post("/api/mark", {"body": f"flood {i}"})[0]
                 for i in range(14)]
        check("rate limit returns 429 after burst", 429 in flood)

        st, css, _ = get("/static/platform.css")
        check("static css", st == 200 and "stage-slide" in css and "mobile-bar" in css)
        st, js, _ = get("/static/platform.js")
        check("static js", st == 200 and "recomputeBraid" in js and "selectionchange" in js)

        st, snap_pub, _ = get("/api/state")
        pub_data = json.loads(snap_pub)
        check("/api/state hides queued marks & contacts publicly",
              st == 200
              and all(m["status"] == "read_in" for m in pub_data["marks"])
              and "t@example.org" not in snap_pub
              and "private-req@example.org" not in snap_pub)

        st, html, _ = get("/nope")
        check("404 page", st == 404)

        # ---- 8. Mount mode (BILL_MOUNT=/bill — semptify.org/bill) -----
        env = {**os.environ, "BILL_MOUNT": "/bill",
               "PLATFORM_DB": str(tmp / "mount.db")}
        proc = subprocess.Popen(
            [sys.executable, "server.py", "--port", "18094"],
            cwd=HERE, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(40):
                try:
                    urllib.request.urlopen(
                        "http://127.0.0.1:18094/bill/", timeout=1)
                    break
                except Exception:
                    time.sleep(0.25)
            mbase = "http://127.0.0.1:18094"

            def mget(p):
                req = urllib.request.Request(mbase + p)
                try:
                    with urllib.request.urlopen(req, timeout=10) as r:
                        return r.status, r.read().decode("utf-8", "replace")
                except urllib.error.HTTPError as e:
                    return e.code, e.read().decode("utf-8", "replace")

            def mraw(p):
                req = urllib.request.Request(mbase + p)
                try:
                    with raw.open(req, timeout=10) as r:
                        return r.status, dict(r.headers)
                except urllib.error.HTTPError as e:
                    return e.code, dict(e.headers)

            st, hdrs = mraw("/")
            check("mounted / redirects to /bill/", st == 303
                  and hdrs.get("Location") == "/bill/")
            st, hdrs = mraw("/margin")
            check("unmounted path redirects into mount", st == 303
                  and hdrs.get("Location") == "/bill/margin")
            st, html = mget("/bill/")
            check("mounted home serves with prefixed links", st == 200
                  and 'href="/bill/margin"' in html
                  and 'href="/bill/sign"' in html
                  and 'href="/margin"' not in html
                  and 'data-mount="/bill"' in html)
            st, html = mget("/bill/api/state")
            check("mounted api serves", st == 200 and "clauses" in html)
            st, html = mget("/bill/research")
            check("mounted content page /bill/research serves", st == 200
                  and "rail" in html)
            st, html = mget("/bill/bill")
            check("mounted reader /bill/bill serves clauses", st == 200
                  and "I-1" in html)
            st, hdrs = mraw("/bill/steward/toggle")
            check("mounted steward toggle redirects in mount", st == 303
                  and (hdrs.get("Location") or "").startswith("/bill"))
        finally:
            proc.terminate()
            proc.wait(timeout=10)

    finally:
        srv.shutdown()
        srv.server_close()

    print()
    if FAILS:
        print(f"SELFCHECK FAILED — {len(FAILS)} check(s): {', '.join(FAILS)}")
        return 1
    print("SELFCHECK PASS — all routes, 3 screen modes, smart toolbars, calculator, steward gates, and boards verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
