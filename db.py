#!/usr/bin/env python
"""db.py — SQLite layer for the standalone Bill Platform.

One file, one connection per call. The database is a runtime artifact
(`data/platform.db`, gitignored) seeded on first open from `seed_data.py`
(the curated campaign seed: clauses, claims ledger, locked decisions,
journey stages, seed marks/requests) plus `seed/editions.json` (the
canonical editions register).

Model (mirrors COMMUNITY_BOARD_DESIGN_2026-11-06, adapted to SQLite):
- marks land QUEUED (intake) — never public by construction.
- read-in assigns a public number (M-0001…) and flips status to read_in;
  only read-in marks render on the Margin board and clause margins.
- held stays dark; crisis_routed stays dark and is counted, not shown.
- contact/steward fields never render publicly.
- requests are the inbound desk: briefing / amendment / position /
  question, pipeline new → reviewing → scheduled | incorporated | declined.

Python 3.11, stdlib only.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import seed_data

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "data" / "platform.db"
SEED_DIR = HERE / "seed"

MARK_STATUSES = ("queued", "read_in", "held", "crisis_routed")
REQ_STATUSES = ("new", "reviewing", "scheduled", "incorporated", "declined")
REQ_TYPES = ("briefing", "amendment", "position", "question", "other")
STANCES = ("support", "oppose", "conditional", "neutral", "watching")
CLAIM_STATUSES = ("verified", "estimate", "checking")

SCHEMA = """
CREATE TABLE IF NOT EXISTS titles (
    num     INTEGER PRIMARY KEY,
    code    TEXT NOT NULL,
    name    TEXT NOT NULL,
    subtitle TEXT
);
CREATE TABLE IF NOT EXISTS clauses (
    id            TEXT PRIMARY KEY,
    ord           INTEGER NOT NULL,
    title_num     INTEGER NOT NULL REFERENCES titles(num),
    heading       TEXT NOT NULL,
    status        TEXT NOT NULL,
    statute_text  TEXT NOT NULL,
    plain_text    TEXT,
    renter_note   TEXT,
    provider_note TEXT,
    lawmaker_note TEXT,
    audiences     TEXT,
    refs          TEXT
);
CREATE TABLE IF NOT EXISTS claims (
    id         TEXT PRIMARY KEY,
    figure     TEXT NOT NULL,
    claim      TEXT NOT NULL,
    source     TEXT,
    status     TEXT NOT NULL,
    checked    TEXT,
    derivation TEXT
);
CREATE TABLE IF NOT EXISTS decisions (
    num    INTEGER PRIMARY KEY,
    clause TEXT,
    title  TEXT NOT NULL,
    why    TEXT
);
CREATE TABLE IF NOT EXISTS journey (
    step  INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    state TEXT NOT NULL,
    note  TEXT
);
CREATE TABLE IF NOT EXISTS editions (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    edition TEXT NOT NULL UNIQUE,
    date    TEXT NOT NULL,
    clause  TEXT NOT NULL,
    change  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS marks (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    public_no      TEXT UNIQUE,            -- M-0001, issued at read-in only
    clause_id      TEXT REFERENCES clauses(id),
    kind           TEXT NOT NULL DEFAULT 'comment',
    quote_text     TEXT,
    proposed_text  TEXT,
    body           TEXT NOT NULL,
    author_label   TEXT,
    contact        TEXT,                   -- intake-only, never rendered
    reply_to       TEXT,
    status         TEXT NOT NULL DEFAULT 'queued'
                   CHECK (status IN ('queued','read_in','held','crisis_routed')),
    response_body  TEXT,                   -- drafter's public answer
    responder_role TEXT,
    source         TEXT NOT NULL DEFAULT 'platform',
    created_at     TEXT NOT NULL,
    read_in_at     TEXT
);
CREATE TABLE IF NOT EXISTS requests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    public_no    TEXT UNIQUE,              -- R-0001
    req_type     TEXT NOT NULL DEFAULT 'other',
    clause_id    TEXT REFERENCES clauses(id),
    org_or_role  TEXT,
    contact_info TEXT,                     -- steward-only, never rendered
    summary      TEXT NOT NULL,
    details      TEXT,
    stance       TEXT NOT NULL DEFAULT 'neutral',
    status       TEXT NOT NULL DEFAULT 'new'
                 CHECK (status IN ('new','reviewing','scheduled',
                                   'incorporated','declined')),
    steward_note TEXT,
    is_public    INTEGER NOT NULL DEFAULT 1,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS positions (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    person    TEXT NOT NULL,
    provision TEXT NOT NULL,
    stance    TEXT NOT NULL,
    noted_at  TEXT NOT NULL,
    source    TEXT
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


@contextmanager
def connect(path: Path | None = None):
    db_path = path or DB_PATH
    db_path.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()


def _next_no(con, table: str, prefix: str) -> str:
    row = con.execute(
        f"SELECT public_no FROM {table} WHERE public_no IS NOT NULL"
        f" ORDER BY CAST(SUBSTR(public_no,3) AS INTEGER) DESC LIMIT 1"
    ).fetchone()
    nxt = (int(row["public_no"][2:]) + 1) if row else 1
    return f"{prefix}-{nxt:04d}"


def _seed(con: sqlite3.Connection) -> None:
    con.executemany(
        "INSERT OR IGNORE INTO titles (num, code, name, subtitle)"
        " VALUES (?,?,?,?)",
        [(t["num"], t["code"], t["name"], t["subtitle"])
         for t in seed_data.TITLES])
    con.executemany(
        "INSERT OR IGNORE INTO clauses (id, ord, title_num, heading, status,"
        " statute_text, plain_text, renter_note, provider_note,"
        " lawmaker_note, audiences, refs) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(c["id"], i, c["title_num"], c["heading"], c["status"],
          c["statute_text"], c.get("plain_text"), c.get("renter_note"),
          c.get("provider_note"), c.get("lawmaker_note"),
          ",".join(c.get("audiences") or ["renter", "provider", "lawmaker"]),
          ",".join(c.get("refs") or []))
         for i, c in enumerate(seed_data.CLAUSES)])
    con.executemany(
        "INSERT OR IGNORE INTO claims (id, figure, claim, source, status,"
        " checked, derivation) VALUES (?,?,?,?,?,?,?)",
        [(c["id"], c["figure"], c["claim"], c.get("source"), c["status"],
          c.get("checked"), c.get("derivation"))
         for c in seed_data.CLAIMS_LEDGER])
    con.executemany(
        "INSERT OR IGNORE INTO decisions (num, clause, title, why)"
        " VALUES (?,?,?,?)",
        [(d["num"], d["clause"], d["title"], d["why"])
         for d in seed_data.LOCKED_DECISIONS])
    con.executemany(
        "INSERT OR IGNORE INTO journey (step, name, state, note)"
        " VALUES (?,?,?,?)",
        [(j["step"], j["name"], j["state"], j["note"])
         for j in seed_data.JOURNEY_STAGES])
    # marks: published → read_in with its number; queued → dark intake.
    for m in seed_data.SEED_MARKS:
        published = m["status"] == "published"
        con.execute(
            "INSERT OR IGNORE INTO marks (public_no, clause_id, kind,"
            " quote_text, proposed_text, body, author_label, reply_to,"
            " status, response_body, responder_role, source, created_at,"
            " read_in_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (m["id"] if published else None, m["clause_id"] or None,
             m["kind"], m.get("quote_text") or None,
             m.get("proposed_text") or None, m["body"],
             m.get("author_label") or None, m.get("reply_to") or None,
             "read_in" if published else "queued",
             m.get("response_body") or None,
             m.get("responder_role") or None, "seed",
             m.get("created_at") or utc_now(),
             m.get("created_at") if published else None))
    for r in seed_data.SEED_REQUESTS:
        con.execute(
            "INSERT OR IGNORE INTO requests (public_no, req_type, clause_id,"
            " org_or_role, contact_info, summary, details, stance, status,"
            " steward_note, is_public, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (r["id"], r["req_type"], r.get("clause_id") or None,
             r.get("org_or_role") or None, r.get("contact_info") or None,
             r["summary"], r.get("details") or None,
             r.get("stance") or "neutral", r["status"],
             r.get("steward_note") or None, int(r.get("is_public", 1)),
             r.get("created_at") or utc_now(),
             r.get("created_at") or utc_now()))
    # R-0003 (a position-type request) says it was recorded on the ledger —
    # seed the matching positions row so the record agrees with itself.
    con.execute(
        "INSERT OR IGNORE INTO positions (person, provision, stance,"
        " noted_at, source) VALUES (?,?,?,?,?)",
        ("Minnesota Tenant-Landlord Mediation Coalition (Demo Record)",
         "Title I custodial escrow + independent adjudication",
         "watching", "2026-11-14 09:05 UTC",
         "Recorded via request R-0003 — monitoring Title II actuarial split"))
    editions_seed = json.loads(
        (SEED_DIR / "editions.json").read_text(encoding="utf-8"))
    con.executemany(
        "INSERT OR IGNORE INTO editions (edition, date, clause, change)"
        " VALUES (?,?,?,?)",
        [(e["edition"], e["date"], e["clause"], e["change"])
         for e in editions_seed["editions"]])


def init(path: Path | None = None) -> None:
    with connect(path) as con:
        con.executescript(SCHEMA)
        cols = {r["name"] for r in con.execute("PRAGMA table_info(clauses)").fetchall()}
        if "audiences" not in cols:
            con.execute("ALTER TABLE clauses ADD COLUMN audiences TEXT")
            for c in seed_data.CLAUSES:
                con.execute(
                    "UPDATE clauses SET audiences = ? WHERE id = ?",
                    (",".join(c.get("audiences") or ["renter", "provider", "lawmaker"]), c["id"]),
                )
        have = con.execute("SELECT COUNT(*) AS n FROM clauses").fetchone()["n"]
        if not have:
            _seed(con)


# ---------- reads ----------

def meta() -> dict:
    return seed_data.BILL_META


def titles() -> list[sqlite3.Row]:
    with connect() as con:
        return con.execute("SELECT * FROM titles ORDER BY num").fetchall()


def clauses() -> list[sqlite3.Row]:
    with connect() as con:
        return con.execute("SELECT * FROM clauses ORDER BY ord").fetchall()


def clause(cid: str) -> sqlite3.Row | None:
    with connect() as con:
        return con.execute(
            "SELECT * FROM clauses WHERE id = ?", (cid,)).fetchone()


def clause_neighbors(cid: str) -> tuple[str | None, str | None]:
    allc = clauses()
    for i, c in enumerate(allc):
        if c["id"] == cid:
            prev_id = allc[i - 1]["id"] if i else None
            next_id = allc[i + 1]["id"] if i + 1 < len(allc) else None
            return prev_id, next_id
    return None, None


def journey() -> list[sqlite3.Row]:
    with connect() as con:
        return con.execute("SELECT * FROM journey ORDER BY step").fetchall()


def journey_current() -> sqlite3.Row | None:
    with connect() as con:
        return con.execute(
            "SELECT * FROM journey WHERE state = 'current'").fetchone()


def claims(status: str | None = None) -> list[sqlite3.Row]:
    q, args = "SELECT * FROM claims", []
    if status:
        q += " WHERE status = ?"
        args.append(status)
    q += " ORDER BY id"
    with connect() as con:
        return con.execute(q, args).fetchall()


def claim(cid: str) -> sqlite3.Row | None:
    with connect() as con:
        return con.execute(
            "SELECT * FROM claims WHERE id = ?", (cid,)).fetchone()


def decisions() -> list[sqlite3.Row]:
    with connect() as con:
        return con.execute("SELECT * FROM decisions ORDER BY num").fetchall()


def margin_counts() -> dict[str, int]:
    """read-in marks per clause — the margin badges."""
    with connect() as con:
        rows = con.execute(
            "SELECT clause_id, COUNT(*) AS n FROM marks"
            " WHERE status = 'read_in' AND clause_id IS NOT NULL"
            " GROUP BY clause_id").fetchall()
    return {r["clause_id"]: r["n"] for r in rows}


def marks(status: str | None = None,
          clause_id: str | None = None) -> list[sqlite3.Row]:
    q, args = "SELECT * FROM marks WHERE 1=1", []
    if status:
        q += " AND status = ?"
        args.append(status)
    if clause_id:
        q += " AND clause_id = ?"
        args.append(clause_id)
    q += " ORDER BY id"
    with connect() as con:
        return con.execute(q, args).fetchall()


def queue_count() -> int:
    with connect() as con:
        return con.execute(
            "SELECT COUNT(*) AS n FROM marks WHERE status = 'queued'"
        ).fetchone()["n"]


def requests(status: str | None = None) -> list[sqlite3.Row]:
    q, args = "SELECT * FROM requests WHERE is_public = 1", []
    if status:
        q += " AND status = ?"
        args.append(status)
    q += (" ORDER BY CASE status WHEN 'new' THEN 0 WHEN 'reviewing' THEN 1"
          " WHEN 'scheduled' THEN 2 WHEN 'incorporated' THEN 3 ELSE 4 END, id")
    with connect() as con:
        return con.execute(q, args).fetchall()


def open_request_count() -> int:
    with connect() as con:
        return con.execute(
            "SELECT COUNT(*) AS n FROM requests WHERE status IN"
            " ('new','reviewing','scheduled')").fetchone()["n"]


def positions() -> list[sqlite3.Row]:
    with connect() as con:
        return con.execute("SELECT * FROM positions ORDER BY id").fetchall()


def editions() -> list[sqlite3.Row]:
    with connect() as con:
        return con.execute(
            "SELECT * FROM editions ORDER BY CAST(SUBSTR(edition,3) AS INTEGER)"
        ).fetchall()


def last_event() -> sqlite3.Row | None:
    """Newest thing that happened anywhere — feeds 'where it stands'."""
    with connect() as con:
        return con.execute(
            "SELECT what, happened_at FROM ("
            "  SELECT 'mark ' || COALESCE(public_no,'(intake #'||id||')')"
            "       || ' — ' || status AS what,"
            "       COALESCE(read_in_at, created_at) AS happened_at FROM marks"
            "  UNION ALL"
            "  SELECT 'request ' || public_no || ' — ' || status, updated_at"
            "       FROM requests"
            "  UNION ALL"
            "  SELECT 'position: ' || person, noted_at FROM positions"
            "  UNION ALL"
            "  SELECT 'edition ' || edition, date FROM editions"
            ") ORDER BY happened_at DESC LIMIT 1").fetchone()


# ---------- writes ----------

def add_mark(clause_id: str | None, kind: str, body: str,
             name: str | None, contact: str | None,
             reply_to: str | None, quote: str | None,
             proposed: str | None) -> int:
    if kind not in ("question", "edit", "comment"):
        kind = "comment"
    with connect() as con:
        cur = con.execute(
            "INSERT INTO marks (clause_id, kind, quote_text, proposed_text,"
            " body, author_label, contact, reply_to, status, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,'queued',?)",
            (clause_id or None, kind, (quote or "").strip() or None,
             (proposed or "").strip() or None, body.strip(),
             (name or "").strip() or None,
             (contact or "").strip() or None, reply_to or None, utc_now()))
        return cur.lastrowid


def mark_action(mark_id: int, action: str,
                response: str | None = None,
                responder: str | None = None) -> str | None:
    """queued -> read_in (issues public number) | held | crisis_routed.
    A response entered at read-in is the drafter answering in the open."""
    if action not in MARK_STATUSES or action == "queued":
        return None
    with connect() as con:
        public_no = None
        if action == "read_in":
            public_no = _next_no(con, "marks", "M")
        resp = (response or "").strip() or None
        con.execute(
            "UPDATE marks SET status = ?, read_in_at = ?, public_no ="
            " COALESCE(public_no, ?), response_body = COALESCE(?,"
            " response_body), responder_role = COALESCE(?, responder_role)"
            " WHERE id = ?",
            (action, utc_now(), public_no, resp,
             (responder or "").strip() or ("Drafting Table" if resp else None),
             mark_id))
    return public_no


def add_request(req_type: str, summary: str, details: str | None,
                clause_id: str | None, org_or_role: str | None,
                contact: str | None) -> str:
    if req_type not in REQ_TYPES:
        req_type = "other"
    with connect() as con:
        public_no = _next_no(con, "requests", "R")
        con.execute(
            "INSERT INTO requests (public_no, req_type, clause_id,"
            " org_or_role, contact_info, summary, details, status,"
            " created_at, updated_at) VALUES (?,?,?,?,?,?,?,'new',?,?)",
            (public_no, req_type, clause_id or None,
             (org_or_role or "").strip() or None,
             (contact or "").strip() or None, summary.strip(),
             (details or "").strip() or None, utc_now(), utc_now()))
    return public_no


def request_status(req_id: int, status: str,
                   note: str | None = None) -> bool:
    if status not in REQ_STATUSES:
        return False
    with connect() as con:
        cur = con.execute(
            "UPDATE requests SET status = ?,"
            " steward_note = COALESCE(?, steward_note), updated_at = ?"
            " WHERE id = ?",
            (status, (note or "").strip() or None, utc_now(), req_id))
        return cur.rowcount > 0


def add_position(person: str, provision: str, stance: str,
                 source: str | None) -> int:
    if stance not in STANCES:
        stance = "watching"
    with connect() as con:
        cur = con.execute(
            "INSERT INTO positions (person, provision, stance, noted_at,"
            " source) VALUES (?,?,?,?,?)",
            (person.strip(), provision.strip(), stance, utc_now(),
             (source or "").strip() or None))
        return cur.lastrowid


def calculate_braid(monthly_rent: float = 1300.0, units: int = 1,
                    m1pr_eligible: bool = True) -> dict:
    """Three-source funding braid & stress-test math (2026-10-23 audit)."""
    rent = max(400.0, min(10000.0, float(monthly_rent)))
    u = max(1, min(500000, int(units)))
    float_mo = round((rent * 0.03) / 12.0, 2)
    base_total_mo = round(rent * (15.33 / 1300.0), 2)
    rem = max(0.0, base_total_mo - float_mo)
    renter_mo = round(rem / 2.0, 2)
    landlord_mo = round(base_total_mo - float_mo - renter_mo, 2)

    fraud_mo = round(rent * (21.23 / 1300.0), 2)
    recession_mo = round(rent * (30.00 / 1300.0), 2)
    tenant_interest_yr = round(rent * 0.01, 2)
    landlord_yr_total = round(landlord_mo * 12.0 * u, 2)
    eviction_benchmark = 6500.0
    unit_years_per_eviction = round(eviction_benchmark / max(1.0, landlord_mo * 12.0), 1)

    return {
        "monthly_rent": round(rent, 2),
        "units": u,
        "m1pr_eligible": bool(m1pr_eligible),
        "deposit_float_mo": float_mo,
        "renter_share_mo": renter_mo,
        "landlord_match_mo": landlord_mo,
        "total_pool_mo": base_total_mo,
        "renter_out_of_pocket_mo": 0.0 if m1pr_eligible else renter_mo,
        "tenant_1pct_interest_yr": tenant_interest_yr,
        "landlord_annual_total": landlord_yr_total,
        "total_pool_annual": round(base_total_mo * 12.0 * u, 2),
        "eviction_cost_benchmark": eviction_benchmark,
        "unit_years_per_eviction": unit_years_per_eviction,
        "stress_base_mo": base_total_mo,
        "stress_fraud_mo": fraud_mo,
        "stress_recession_mo": recession_mo,
    }

