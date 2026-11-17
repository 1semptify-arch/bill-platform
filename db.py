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
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

import seed_data

HERE = Path(__file__).resolve().parent
import os

DB_PATH = Path(os.environ.get("PLATFORM_DB", str(HERE / "data" / "platform.db")))
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
    read_in_at     TEXT,
    receipt        TEXT,                   -- submitter's status-lookup code
    retracted_at   TEXT,                   -- public correction, never deleted
    retract_note   TEXT,
    redacted_at    TEXT,                   -- name/contact removed by stewards
    redact_note    TEXT,
    edited_at      TEXT,                   -- body replaced by stewards
    edit_note      TEXT,                   -- public reason ("advertising removed")
    body_original  TEXT,                   -- pre-edit body, steward-only record
    change_id      INTEGER REFERENCES changes(id)
                                           -- mark weighs in on proposal CH-XXXX
                                           -- (author_label never renders on these)
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
    receipt      TEXT,
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
CREATE TABLE IF NOT EXISTS supporters (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    name      TEXT NOT NULL,
    org       TEXT,
    role      TEXT,
    stage     TEXT NOT NULL DEFAULT 'target'
              CHECK (stage IN ('target','contacted','talks','endorsed')),
    district  TEXT,
    note      TEXT,
    noted_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS signatures (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    public_no    TEXT UNIQUE,            -- S-0001, issued at publish only
    name         TEXT NOT NULL,          -- consented to publish
    org_or_town  TEXT,                   -- consented to publish
    note         TEXT,                   -- optional public line
    email        TEXT,                   -- private; OAuth-storage seam later
    status       TEXT NOT NULL DEFAULT 'queued'
                 CHECK (status IN ('queued','published','held')),
    receipt      TEXT,                   -- signer's status-lookup code
    created_at   TEXT NOT NULL,
    published_at TEXT
);
CREATE TABLE IF NOT EXISTS changes (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    public_no     TEXT UNIQUE,            -- CH-0001
    clause_id     TEXT REFERENCES clauses(id),
    source_mark   INTEGER REFERENCES marks(id),
    edition       TEXT,                   -- edition that incorporated it (E-10…)
    quote_text    TEXT,                   -- statute passage the change targets
    proposed_text TEXT,                   -- proposed wording
    old_text      TEXT,                   -- statute text before (snapshot)
    new_text      TEXT,                   -- statute text after
    note          TEXT,
    closes_at     TEXT,                    -- discussion window end (YYYY-MM-DD)
    resolved_by   TEXT,                    -- steward name, published w/ consent
    status        TEXT NOT NULL DEFAULT 'proposed'
                  CHECK (status IN ('proposed','incorporated','declined',
                                    'retracted')),
    created_at    TEXT NOT NULL,
    resolved_at   TEXT
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
        f"SELECT public_no FROM {table} WHERE public_no LIKE '{prefix}-%'"
        f" ORDER BY CAST(SUBSTR(public_no,{len(prefix) + 2}) AS INTEGER)"
        " DESC LIMIT 1"
    ).fetchone()
    nxt = (int(row["public_no"][len(prefix) + 1:]) + 1) if row else 1
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
        # Migrate older DBs forward — CHECK constraints can't be altered,
        # so retract uses a timestamp column, not a status value.
        for table, cols in {"marks": ["receipt TEXT", "retracted_at TEXT",
                                      "retract_note TEXT", "redacted_at TEXT",
                                      "redact_note TEXT", "edited_at TEXT",
                                      "edit_note TEXT", "body_original TEXT",
                                      "change_id INTEGER REFERENCES changes(id)"],
                            "requests": ["receipt TEXT"],
                            "changes": ["closes_at TEXT",
                                        "resolved_by TEXT"]}.items():
            have_cols = {r["name"] for r in con.execute(
                f"PRAGMA table_info({table})").fetchall()}
            for col in cols:
                if col.split()[0] not in have_cols:
                    con.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
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
        _seed_supporters(con)


def _seed_supporters(con) -> None:
    if con.execute("SELECT COUNT(*) AS n FROM supporters").fetchone()["n"]:
        return
    con.executemany(
        "INSERT INTO supporters (name, org, role, stage, district, note,"
        " noted_at) VALUES (?,?,?,?,?,?,?)",
        [
            ("Amy Klobuchar", "U.S. Senate (MN)", "U.S. Senator",
             "target", "MN statewide",
             "Outreach suggestion — federal visibility ally; the bill itself is state-level.",
             utc_now()),
            ("HOME Line", "HOME Line", "Tenant hotline & advocacy",
             "target", "Statewide", "Already the platform's crisis-routing partner.", utc_now()),
            ("Housing Justice Center", "Housing Justice Center", "Policy & litigation",
             "target", "Statewide", "Deposit-protection policy expertise.", utc_now()),
            ("Inquilinxs Unidxs", "Inquilinxs Unidxs (IX)", "Renter organizing",
             "target", "Minneapolis", None, utc_now()),
            ("CTUL", "CTUL", "Worker center",
             "target", "Twin Cities", None, utc_now()),
            ("Legal Services Advocacy Project", "LSAP / Mid-MN Legal Aid",
             "Legal aid", "target", "Statewide",
             "Sees deposit disputes daily.", utc_now()),
            ("SMRLS", "Southern MN Regional Legal Services", "Legal aid",
             "target", "Southern MN", None, utc_now()),
            ("ISAIAH / Faith in Minnesota", "ISAIAH", "Faith organizing",
             "target", "Metro + St. Cloud", None, utc_now()),
            ("Jewish Community Action", "JCA", "Faith organizing",
             "target", "Metro", None, utc_now()),
            ("MN Coalition for the Homeless", "MCH", "Anti-poverty coalition",
             "target", "Statewide", None, utc_now()),
            ("SEIU Minnesota", "SEIU", "Labor", "target", "Statewide", None, utc_now()),
            ("Minnesota Multi Housing Assoc.", "MHA", "Provider association",
             "target", "Statewide",
             "Persuasion target — bill pays providers during hardship and ends surety-fee competition.", utc_now()),
            ("MHFA", "MN Housing Finance Agency", "Pilot home agency",
             "target", "Statewide",
             "Named in Title IV-1 as the pilot administrator.", utc_now()),
            ("SFM Mutual", "SFM Mutual Insurance", "Mutual precedent",
             "target", "Bloomington",
             "Mutual-dividend model precedent for the claims-free dividend.", utc_now()),
            ("Eviction Lab", "Eviction Lab (Princeton)", "Research",
             "target", "National",
             "Serial-filing data already cited in the claims ledger.", utc_now()),
        ])


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


def supporters(stage: str | None = None) -> list[sqlite3.Row]:
    q, args = "SELECT * FROM supporters WHERE 1=1", []
    if stage:
        q += " AND stage = ?"; args.append(stage)
    q += (" ORDER BY CASE stage WHEN 'endorsed' THEN 0 WHEN 'talks' THEN 1"
          " WHEN 'contacted' THEN 2 ELSE 3 END, org, name")
    with connect() as con:
        return con.execute(q, args).fetchall()


def supporter_counts() -> dict[str, int]:
    with connect() as con:
        return {r["stage"]: r["n"] for r in con.execute(
            "SELECT stage, COUNT(*) AS n FROM supporters GROUP BY stage")}


def add_supporter(name: str, org: str | None, role: str | None,
                  stage: str, district: str | None,
                  note: str | None) -> None:
    if stage not in ("target", "contacted", "talks", "endorsed"):
        stage = "target"
    with connect() as con:
        con.execute(
            "INSERT INTO supporters (name, org, role, stage, district, note,"
            " noted_at) VALUES (?,?,?,?,?,?,?)",
            (name.strip(), (org or "").strip() or None,
             (role or "").strip() or None, stage,
             (district or "").strip() or None,
             (note or "").strip() or None, utc_now()))


def supporter_stage(supporter_id: int, stage: str,
                    note: str | None = None) -> bool:
    if stage not in ("target", "contacted", "talks", "endorsed"):
        return False
    with connect() as con:
        n = (note or "").strip() or None
        cur = con.execute(
            "UPDATE supporters SET stage = ?,"
            " note = CASE WHEN ? IS NULL THEN note"
            "           ELSE COALESCE(note,'') || ' ' || ? END"
            " WHERE id = ?",
            (stage, n, n, supporter_id))
        return cur.rowcount > 0


def add_signature(name: str, org_or_town: str | None, note: str | None,
                  email: str | None) -> str:
    """A voluntary signature lands dark ('queued'). Email is private —
    the OAuth-storage seam when that keystone ships."""
    receipt = secrets.token_hex(4)
    with connect() as con:
        con.execute(
            "INSERT INTO signatures (name, org_or_town, note, email, status,"
            " receipt, created_at) VALUES (?,?,?,?,'queued',?,?)",
            (name.strip(), (org_or_town or "").strip() or None,
             (note or "").strip() or None, (email or "").strip() or None,
             receipt, utc_now()))
    return receipt


def signatures(status: str | None = None) -> list[sqlite3.Row]:
    with connect() as con:
        if status:
            return con.execute(
                "SELECT id, public_no, name, org_or_town, note, status,"
                " created_at, published_at FROM signatures WHERE status = ?"
                " ORDER BY published_at DESC, id DESC", (status,)).fetchall()
        return con.execute(
            "SELECT id, public_no, name, org_or_town, note, status,"
            " created_at, published_at FROM signatures"
            " ORDER BY CASE status WHEN 'queued' THEN 0 ELSE 1 END,"
            " id DESC").fetchall()


def sign_pending_count() -> int:
    with connect() as con:
        return con.execute(
            "SELECT COUNT(*) FROM signatures WHERE status='queued'"
        ).fetchone()[0]


def signature_action(sig_id: int, action: str) -> str | None:
    """queued|held -> published (issues S-number) | held."""
    if action not in ("published", "held"):
        return None
    with connect() as con:
        public_no = _next_no(con, "signatures", "S") \
            if action == "published" else None
        con.execute(
            "UPDATE signatures SET status = ?,"
            " public_no = COALESCE(public_no, ?),"
            " published_at = CASE WHEN ? = 'published'"
            " THEN COALESCE(published_at, ?) ELSE published_at END"
            " WHERE id = ?",
            (action, public_no, action, utc_now(), sig_id))
        return public_no


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
            "  SELECT 'change ' || public_no || ' — ' || status,"
            "       COALESCE(resolved_at, created_at) FROM changes"
            "  UNION ALL"
            "  SELECT 'edition ' || edition, date FROM editions"
            ") ORDER BY happened_at DESC LIMIT 1").fetchone()


# ---------- writes ----------

def add_mark(clause_id: str | None, kind: str, body: str,
             name: str | None, contact: str | None,
             reply_to: str | None, quote: str | None,
             proposed: str | None,
             change_id: int | None = None) -> int:
    if kind not in ("question", "edit", "comment"):
        kind = "comment"
    receipt = secrets.token_hex(4)
    with connect() as con:
        con.execute(
            "INSERT INTO marks (clause_id, kind, quote_text, proposed_text,"
            " body, author_label, contact, reply_to, status, created_at,"
            " receipt, change_id) VALUES (?,?,?,?,?,?,?,?,'queued',?,?,?)",
            (clause_id or None, kind, (quote or "").strip() or None,
             (proposed or "").strip() or None, body.strip(),
             (name or "").strip() or None,
             (contact or "").strip() or None, reply_to or None, utc_now(),
             receipt, change_id))
    return receipt


def mark_retract(mark_id: int, note: str | None = None) -> bool:
    """Visibly retract a read-in mark — the record stays, struck through."""
    with connect() as con:
        cur = con.execute(
            "UPDATE marks SET retracted_at = ?, retract_note = ?"
            " WHERE id = ? AND status = 'read_in' AND retracted_at IS NULL",
            (utc_now(), (note or "").strip() or None, mark_id))
        return cur.rowcount > 0


def mark_redact(mark_id: int, note: str | None = None) -> str | None:
    """Remove name + contact from a mark — the columns are cleared, not
    hidden (redaction means gone). The mark itself stays, per MODERATION.md:
    strip the details, publish the rest. Returns the mark's status."""
    with connect() as con:
        row = con.execute("SELECT status FROM marks WHERE id = ?",
                          (mark_id,)).fetchone()
        if not row:
            return None
        con.execute(
            "UPDATE marks SET author_label = NULL, contact = NULL,"
            " redacted_at = ?, redact_note = ? WHERE id = ?",
            (utc_now(), (note or "").strip() or None, mark_id))
        return row["status"]


def mark_edit(mark_id: int, new_body: str, note: str | None = None) -> str | None:
    """Replace a mark's body (advertising, hate, etc. per MODERATION.md —
    never for criticizing the bill). Original moves to body_original for
    steward-side accountability; the edit is noted publicly. Returns the
    mark's status."""
    new_body = (new_body or "").strip()
    if not new_body:
        return None
    with connect() as con:
        row = con.execute("SELECT status FROM marks WHERE id = ?",
                          (mark_id,)).fetchone()
        if not row:
            return None
        con.execute(
            "UPDATE marks SET body_original = COALESCE(body_original, body),"
            " body = ?, edited_at = ?, edit_note = ? WHERE id = ?",
            (new_body, utc_now(), (note or "").strip() or None, mark_id))
        return row["status"]


def by_receipt(code: str) -> dict | None:
    """Submitter status lookup — status only, never contact or raw body."""
    code = (code or "").strip()
    if not code:
        return None
    with connect() as con:
        r = con.execute(
            "SELECT public_no, status, clause_id, kind, created_at,"
            " read_in_at, retracted_at FROM marks WHERE receipt = ?",
            (code,)).fetchone()
        if r:
            d = dict(r); d["type"] = "mark"; return d
        r = con.execute(
            "SELECT public_no, req_type, status, clause_id, created_at,"
            " updated_at FROM requests WHERE receipt = ?",
            (code,)).fetchone()
        if r:
            d = dict(r); d["type"] = "request"; return d
        r = con.execute(
            "SELECT public_no, status, created_at, published_at"
            " FROM signatures WHERE receipt = ?",
            (code,)).fetchone()
        if r:
            d = dict(r); d["type"] = "signature"; return d
    return None


def search(term: str) -> dict:
    like = f"%{term}%"
    with connect() as con:
        return {
            "clauses": con.execute(
                "SELECT id, heading, status FROM clauses WHERE id LIKE ?"
                " OR heading LIKE ? OR statute_text LIKE ? OR plain_text LIKE ?"
                " ORDER BY ord", (like,) * 4).fetchall(),
            "marks": con.execute(
                "SELECT public_no, clause_id, kind, body FROM marks"
                " WHERE status = 'read_in' AND retracted_at IS NULL AND"
                " (public_no LIKE ? OR body LIKE ? OR quote_text LIKE ?"
                " OR response_body LIKE ?) ORDER BY public_no",
                (like,) * 4).fetchall(),
            "changes": con.execute(
                "SELECT public_no, clause_id, status, proposed_text FROM changes"
                " WHERE public_no LIKE ? OR proposed_text LIKE ?"
                " OR note LIKE ? OR edition LIKE ?"
                " ORDER BY created_at DESC", (like,) * 4).fetchall(),
            "requests": con.execute(
                "SELECT public_no, req_type, summary, status FROM requests"
                " WHERE is_public = 1 AND (public_no LIKE ? OR summary LIKE ?"
                " OR details LIKE ?) ORDER BY updated_at DESC",
                (like,) * 3).fetchall(),
            "editions": con.execute(
                "SELECT edition, date, clause, change FROM editions WHERE"
                " edition LIKE ? OR clause LIKE ? OR change LIKE ?",
                (like,) * 3).fetchall(),
            "decisions": con.execute(
                "SELECT num, clause, title FROM decisions WHERE title LIKE ?"
                " OR why LIKE ? OR clause LIKE ?", (like,) * 3).fetchall(),
            "signatures": con.execute(
                "SELECT public_no, name, org_or_town FROM signatures"
                " WHERE status = 'published' AND (public_no LIKE ?"
                " OR name LIKE ? OR org_or_town LIKE ?)"
                " ORDER BY published_at DESC", (like,) * 3).fetchall(),
        }


def export_state() -> dict:
    """Full backup for a steward — includes intake and contact fields,
    which is why this only serves behind the steward gate."""
    tables = ("titles", "clauses", "claims", "decisions", "journey",
              "editions", "marks", "changes", "requests", "positions",
              "supporters", "signatures")
    with connect() as con:
        return {"meta": meta(),
                **{t: [dict(r) for r in con.execute(
                    f"SELECT * FROM {t} ORDER BY rowid")] for t in tables}}


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
        if action == "read_in":
            # Edit-kind marks carry proposed wording — record them on the
            # public change ledger automatically so no proposal is lost.
            row = con.execute(
                "SELECT kind, clause_id, quote_text, proposed_text, body"
                " FROM marks WHERE id = ?", (mark_id,)).fetchone()
            if row and row["kind"] == "edit" and (
                    row["proposed_text"] or row["quote_text"]):
                ch_no = _next_no(con, "changes", "CH")
                con.execute(
                    "INSERT INTO changes (public_no, clause_id, source_mark,"
                    " quote_text, proposed_text, note, status, created_at)"
                    " VALUES (?,?,?,?,?,?,'proposed',?)",
                    (ch_no, row["clause_id"], mark_id, row["quote_text"],
                     row["proposed_text"], row["body"], utc_now()))
    return public_no


# ---------- change ledger ----------

CHANGE_STATUSES = ("proposed", "incorporated", "declined", "retracted")


def changes(status: str | None = None, clause_id: str | None = None,
            since: str | None = None,
            edition: str | None = None) -> list[sqlite3.Row]:
    q, args = ("SELECT c.*, m.public_no AS mark_no FROM changes c"
               " LEFT JOIN marks m ON m.id = c.source_mark WHERE 1=1"), []
    if status:
        q += " AND c.status = ?"; args.append(status)
    if clause_id:
        q += " AND c.clause_id = ?"; args.append(clause_id)
    if edition:
        q += " AND c.edition = ?"; args.append(edition)
    if since:
        q += (" AND COALESCE(c.resolved_at, c.created_at) >= ?")
        args.append(since)
    q += (" ORDER BY COALESCE(c.resolved_at, c.created_at) DESC, c.id DESC")
    with connect() as con:
        return con.execute(q, args).fetchall()


def change_counts() -> dict[str, int]:
    with connect() as con:
        return {r["status"]: r["n"] for r in con.execute(
            "SELECT status, COUNT(*) AS n FROM changes GROUP BY status")}


def add_change(clause_id: str | None, proposed_text: str, quote: str | None,
               closes_at: str | None = None,
               note: str | None = None) -> str:
    """Steward-recorded proposed change (requests lane, briefings, etc.)."""
    with connect() as con:
        ch_no = _next_no(con, "changes", "CH")
        con.execute(
            "INSERT INTO changes (public_no, clause_id, quote_text,"
            " proposed_text, note, closes_at, status, created_at)"
            " VALUES (?,?,?,?,?,?,'proposed',?)",
            (ch_no, clause_id or None, (quote or "").strip() or None,
             proposed_text.strip(), (note or "").strip() or None,
             (closes_at or "").strip() or None, utc_now()))
    return ch_no


def change_action(change_id: int, action: str, edition: str | None = None,
                  new_text: str | None = None, note: str | None = None,
                  resolved_by: str | None = None) -> bool:
    """proposed -> incorporated (records old/new text + edition) |
    declined | retracted."""
    if action not in ("incorporated", "declined", "retracted"):
        return False
    with connect() as con:
        row = con.execute(
            "SELECT clause_id FROM changes WHERE id = ?", (change_id,)
        ).fetchone()
        if not row:
            return False
        old = None
        if action == "incorporated" and row["clause_id"]:
            old = con.execute(
                "SELECT statute_text FROM clauses WHERE id = ?",
                (row["clause_id"],)).fetchone()
            old = old["statute_text"] if old else None
        n = (note or "").strip() or None
        con.execute(
            "UPDATE changes SET status = ?, resolved_at = ?,"
            " edition = COALESCE(?, edition),"
            " old_text = COALESCE(old_text, ?),"
            " new_text = COALESCE(?, new_text),"
            " resolved_by = COALESCE(?, resolved_by),"
            " note = CASE WHEN ? IS NULL THEN note"
            "           ELSE COALESCE(note,'') || ' ' || ? END"
            " WHERE id = ?",
            (action, utc_now(), (edition or "").strip() or None, old,
             (new_text or "").strip() or None,
             (resolved_by or "").strip() or None, n, n, change_id))
    return True


def change_is_open(change_id: int) -> bool:
    """True when the proposal exists, is still 'proposed', and its
    discussion window hasn't passed (closes_at is a YYYY-MM-DD date)."""
    with connect() as con:
        row = con.execute(
            "SELECT status, closes_at FROM changes WHERE id = ?",
            (change_id,)).fetchone()
    if not row or row["status"] != "proposed":
        return False
    return not (row["closes_at"] and
                row["closes_at"] < date.today().isoformat())


def marks_for_change(change_id: int) -> list[sqlite3.Row]:
    """Read-in discussion marks on a proposal — public thread."""
    with connect() as con:
        return con.execute(
            "SELECT * FROM marks WHERE change_id = ? AND status = 'read_in'"
            " ORDER BY created_at", (change_id,)).fetchall()


def add_request(req_type: str, summary: str, details: str | None,
                clause_id: str | None, org_or_role: str | None,
                contact: str | None) -> str:
    if req_type not in REQ_TYPES:
        req_type = "other"
    receipt = secrets.token_hex(4)
    with connect() as con:
        public_no = _next_no(con, "requests", "R")
        con.execute(
            "INSERT INTO requests (public_no, req_type, clause_id,"
            " org_or_role, contact_info, summary, details, status, receipt,"
            " created_at, updated_at) VALUES (?,?,?,?,?,?,?,'new',?,?,?)",
            (public_no, req_type, clause_id or None,
             (org_or_role or "").strip() or None,
             (contact or "").strip() or None, summary.strip(),
             (details or "").strip() or None, receipt, utc_now(), utc_now()))
    return receipt


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

