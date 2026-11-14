#!/usr/bin/env python
"""views.py — HTML rendering for the standalone Bill Platform.

Server-rendered, stdlib only. Every page shares one frame:

    brand + mode switcher        (always)
    context-aware smart toolbar  (actions for what you're looking at)
    reading spine                (objective / where it stands / next action
                                  where the page carries a spine)

Modes: desk (default), tv (presentation), mobile. Mode rides a cookie set
via /mode/<name>?next=<path>; platform.js auto-suggests on first visit.

Style law (Brad's UI contract + minimalist-ui skill): 17–19px body text,
single column, muted warm palette, color = state only, bold = names and
actions, sentences not chips, hairline borders only, no emoji.
"""
from __future__ import annotations

import html
import urllib.parse

import db

BRAND = "Turnbuchalla"
SUB = "MN Rent Assurance & Deposit Protection Act — working platform"

STATUS_WORDS = {
    "queued": "queued for read-in", "read_in": "read in", "held": "held",
    "crisis_routed": "crisis-routed",
    "new": "new", "reviewing": "reviewing", "scheduled": "scheduled",
    "incorporated": "incorporated", "declined": "declined",
    "support": "supports", "oppose": "opposes", "conditional": "conditional",
    "neutral": "neutral", "watching": "watching",
    "verified": "verified", "estimate": "estimate", "checking": "checking",
    "done": "done", "current": "current", "next": "next",
    "upcoming": "upcoming", "locked": "locked", "modeled": "modeled",
    "open": "open drafting",
}
REQ_NEXT = {"new": "reviewing", "reviewing": "scheduled",
            "scheduled": "incorporated"}
KIND_WORDS = {"question": "question", "edit": "proposed edit",
              "comment": "comment"}


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def _mode_links(current: str, path: str) -> str:
    out = []
    for m, label in (("desk", "Desk"), ("tv", "TV"), ("mobile", "Mobile")):
        cls = "mode-link on" if m == current else "mode-link"
        href = f"/mode/{m}?next={urllib.parse.quote(path, safe='')}"
        out.append(f'<a class="{cls}" href="{href}">{label}</a>')
    return "".join(out)


def toolbar(actions: list[tuple[str, str, str]]) -> str:
    """actions: [(label, href, kind)] — kind 'primary' or 'link'."""
    items = "".join(
        f'<a class="tb-{k}" href="{esc(h)}">{esc(t)}</a>' for t, h, k in actions)
    return f'<nav class="toolbar" aria-label="Context actions">{items}</nav>'


def page(title: str, body: str, mode: str, path: str,
         actions: list[tuple[str, str, str]]) -> bytes:
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {BRAND}</title>
<link rel="stylesheet" href="/static/platform.css">
</head>
<body class="mode-{esc(mode)}">
<header class="topbar">
  <a class="brand" href="/">{BRAND}<small>{esc(SUB)}</small></a>
  <div class="modes" role="group" aria-label="Screen mode">{_mode_links(mode, path)}</div>
</header>
{toolbar(actions)}
<main class="page">
{body}
</main>
<footer class="foot">
  <p>Working draft — nothing here is filed law. Marks land in intake and
  are read into the ledger by a person, never automatically.</p>
  <p class="foot-nav"><a href="/">Desk</a> · <a href="/bill">The bill</a> ·
  <a href="/margin">The margin</a> · <a href="/intake">Intake</a> ·
  <a href="/requests">Requests</a> · <a href="/positions">Positions</a> ·
  <a href="/claims">Claims</a> · <a href="/decisions">Decisions</a> ·
  <a href="/editions">Editions</a></p>
</footer>
<script src="/static/platform.js"></script>
</body>
</html>"""
    return doc.encode("utf-8")


def _status(status: str) -> str:
    return (f'<span class="st st-{esc(status)}">'
            f'{esc(STATUS_WORDS.get(status, status))}</span>')


def _clause_label(cid) -> str:
    return (f'<b class="clref"><a href="/clause/{esc(cid)}">{esc(cid)}</a></b>'
            if cid else '<span class="clref gen">general</span>')


def _reline(m) -> str:
    return f' · re: {esc(m["reply_to"])}' if m["reply_to"] else ""


def _mark_html(m, show_answer_link: bool = True) -> str:
    quote = (f'<blockquote class="quote">“{esc(m["quote_text"])}”</blockquote>'
             if m["quote_text"] else "")
    proposed = (f'<p class="proposed"><b>Proposed:</b> '
                f'{esc(m["proposed_text"])}</p>'
                if m["proposed_text"] else "")
    response = (f'<p class="response"><b>{esc(m["responder_role"] or "Drafting Table")}:</b> '
                f'{esc(m["response_body"])}</p>'
                if m["response_body"] else "")
    answer = (f'<p class="mact"><a href="/mark?re={esc(m["public_no"])}'
              f'{"&c=" + esc(m["clause_id"]) if m["clause_id"] else ""}">'
              f'answer by reference</a></p>' if show_answer_link else "")
    kind = KIND_WORDS.get(m["kind"], "comment")
    author = f' · {esc(m["author_label"])}' if m["author_label"] else " · unsigned"
    return (f'<article class="mark" id="{esc(m["public_no"] or m["id"])}">'
            f'<p class="mno"><b>{esc(m["public_no"] or "#" + str(m["id"]))}</b>'
            f' · {esc(m["read_in_at"] or m["created_at"])} · {kind} · '
            f'{_clause_label(m["clause_id"])}{author}{_reline(m)}</p>'
            f'{quote}{proposed}<p>{esc(m["body"])}</p>{response}{answer}'
            f'</article>')


def _mark_form(cid: str | None, re_no: str | None,
               quote: str | None = None) -> str:
    options = ['<option value="">— general, no clause —</option>']
    for c in db.clauses():
        sel = ' selected' if c["id"] == cid else ""
        options.append(
            f'<option value="{esc(c["id"])}"{sel}>{esc(c["id"])} — '
            f'{esc(c["heading"])}</option>')
    reline = (f'<p class="reline">Answering mark <b>{esc(re_no)}</b> by '
              f'reference.</p>'
              f'<input type="hidden" name="reply_to" value="{esc(re_no)}">'
              ) if re_no else ""
    qline = (f'<input type="hidden" name="quote" value="{esc(quote[:400])}">'
             f'<p class="reline">Marking the selection: '
             f'<i>{esc(quote[:140])}</i></p>') if quote else ""
    return f"""
<form method="post" action="/api/mark" class="stack">
  {reline}{qline}
  <div class="row">
    <label>Clause<select name="clause_id">{''.join(options)}</select></label>
    <label>Kind<select name="kind">
      <option value="comment">Comment</option>
      <option value="question">Question</option>
      <option value="edit">Proposed edit</option>
    </select></label>
  </div>
  <label>Your mark<textarea name="body" rows="5" required
    placeholder="Write it plainly — a suggestion, a concern, a correction, a question."></textarea></label>
  <label>Proposed wording <span class="quiet">(optional — for edits)</span>
    <textarea name="proposed" rows="2"
      placeholder="The exact words you'd put in."></textarea></label>
  <div class="row">
    <label>Name <span class="quiet">(optional — sign it and it stands publicly)</span>
      <input name="name" autocomplete="name"></label>
    <label>Contact <span class="quiet">(optional — never shown)</span>
      <input name="contact" autocomplete="off"></label>
  </div>
  <p class="crisis">If this is about your own housing right now —
  <b>HOME Line 612-728-5767</b> first. This desk is for the draft.</p>
  <button class="btn" type="submit">Enter the mark</button>
</form>"""


# ---------- pages ----------

def home(mode: str, path: str) -> bytes:
    meta = db.meta()
    ev = db.last_event()
    cur = db.journey_current()
    n_queued = db.queue_count()
    n_open = db.open_request_count()
    counts = db.margin_counts()
    n_marks = sum(counts.values())
    n_clauses = len(db.clauses())

    if ev:
        stands = f"Last event: {esc(ev['what'])} — {esc(ev['happened_at'])}."
    else:
        stands = "Nothing has happened yet — the platform is freshly seeded."
    if cur:
        stands += (f" The campaign sits at <b>{esc(cur['name'])}</b> — "
                   f"{esc(cur['note'])}.")

    if n_queued:
        nxt = (f'<a class="next" href="/intake">Triage the intake queue '
               f'({n_queued} waiting)</a>')
    elif n_open:
        nxt = (f'<a class="next" href="/requests">Work the requests desk '
               f'({n_open} open)</a>')
    else:
        nxt = '<a class="next" href="/bill">Read the draft</a>'

    journey = "".join(
        f'<li class="j-{esc(j["state"])}"><b>{j["step"]}. '
        f'{esc(j["name"])}</b> {_status(j["state"])}'
        f'<br><span class="quiet">{esc(j["note"])}</span></li>'
        for j in db.journey())

    pillars = "".join(
        f'<p class="pillar"><b>{esc(p["label"])}</b> — '
        f'{esc(p["headline"])}</p>'
        for p in meta["summary_points"])

    body = f"""
<section class="spine">
  <p class="spine-line"><span class="spine-tag">Objective</span>
    {esc(meta['thesis'])}</p>
  <p class="spine-line"><span class="spine-tag">Where it stands</span>
    {stands} The draft holds <b>{n_clauses} clauses</b> across five titles;
    <b>{n_marks}</b> marks are on the public ledger and <b>{n_queued}</b>
    wait in intake.</p>
  <p class="spine-line"><span class="spine-tag">Next action</span>{nxt}</p>
</section>
<section>
  <h2>The pipeline</h2>
  <ol class="journey">{journey}</ol>
</section>
<section>
  <h2>What the bill does</h2>
  {pillars}
</section>
<section class="evidence">
  <h2>Evidence</h2>
  <ul class="ev">
    <li><a href="/bill">The draft</a> — every clause, margins open.</li>
    <li><a href="/margin">The margin</a> — marks read into the ledger.</li>
    <li><a href="/intake">Intake queue</a> — what waits for read-in.</li>
    <li><a href="/requests">Requests desk</a> — briefings, amendments, asks.</li>
    <li><a href="/positions">Positions</a> — who stands where.</li>
    <li><a href="/claims">Claims ledger</a> — every public figure, checked.</li>
    <li><a href="/decisions">Locked decisions</a> — the eight that hold.</li>
    <li><a href="/editions">Editions</a> — how the draft got here.</li>
  </ul>
</section>"""
    return page("Desk", body, mode, path, [
        ("The bill", "/bill", "primary"),
        ("The margin", "/margin", "link"),
        ("Requests", "/requests", "link"),
    ])


def bill(mode: str, path: str) -> bytes:
    titles = {t["num"]: t for t in db.titles()}
    counts = db.margin_counts()
    parts = []
    last_title = None
    for c in db.clauses():
        if c["title_num"] != last_title:
            last_title = c["title_num"]
            t = titles[last_title]
            parts.append(
                f'<h2 class="title-head">{esc(t["code"])} — '
                f'{esc(t["name"])}</h2>'
                f'<p class="title-note">{esc(t["subtitle"])}</p>')
        n = counts.get(c["id"], 0)
        badge = (f'<a class="mcount" href="/clause/{esc(c["id"])}#margin">'
                 f'({n})</a>') if n else ''
        tag = _status(c["status"])
        plain = (f'<p class="plain"><b>In plain language:</b> '
                 f'{esc(c["plain_text"])}</p>') if c["plain_text"] else ""
        parts.append(f"""
<section class="clause" id="c-{esc(c['id'])}" data-clause="{esc(c['id'])}">
  <header class="chead">
    <span class="secnum">{esc(c['id'])}</span>
    <h3>{esc(c['heading'])} {tag}</h3>
    <a class="annot" href="/mark?c={esc(c['id'])}" aria-label="Mark {esc(c['id'])}">+</a>
    {badge}
  </header>
  <div class="cbody"><p>{esc(c['statute_text'])}</p>{plain}</div>
</section>""")
    body = f"""
<header class="mast">
  <h1>The draft, read through</h1>
  <p class="lede">Every clause. The <b>+</b> opens a mark on that clause;
  the count shows marks already read in. Open drafting questions stand in
  the open — nothing is hidden.</p>
</header>
{''.join(parts)}"""
    return page("The Bill", body, mode, path, [
        ("Mark the draft", "/mark", "primary"),
        ("The margin", "/margin", "link"),
        ("Claims", "/claims", "link"),
        ("Present", "/mode/tv?next=/bill", "link"),
    ])


def clause_view(cid: str, mode: str, path: str) -> bytes | None:
    c = db.clause(cid)
    if not c:
        return None
    prev_id, next_id = db.clause_neighbors(cid)
    rows = db.marks(status="read_in", clause_id=cid)
    margin = "".join(_mark_html(m) for m in rows) or (
        '<p class="quiet">No marks read in on this clause yet.</p>')
    nav = []
    if prev_id:
        nav.append(f'<a href="/clause/{esc(prev_id)}">← {esc(prev_id)}</a>')
    if next_id:
        nav.append(f'<a href="/clause/{esc(next_id)}">{esc(next_id)} →</a>')

    notes = []
    for label, field in (("Renter", "renter_note"),
                         ("Housing provider", "provider_note"),
                         ("Lawmaker", "lawmaker_note")):
        if c[field]:
            notes.append(f'<li><b>{label}:</b> {esc(c[field])}</li>')
    notes_html = (f'<ul class="notes">{"".join(notes)}</ul>' if notes else "")

    refs = []
    for rid in (c["refs"] or "").split(","):
        rid = rid.strip()
        if not rid:
            continue
        cl = db.claim(rid)
        if cl:
            refs.append(f'<li><b>{esc(cl["figure"])}</b> — {esc(cl["claim"])} '
                        f'{_status(cl["status"])} '
                        f'<span class="quiet">({esc(cl["source"] or "internal derivation")})</span></li>')
    refs_html = (f'<section class="refs"><h2>Standing on</h2>'
                 f'<ul class="ev">{"".join(refs)}</ul></section>' if refs else "")

    plain = (f'<p class="plain"><b>In plain language:</b> '
             f'{esc(c["plain_text"])}</p>') if c["plain_text"] else ""

    body = f"""
<header class="mast">
  <p class="crumbs"><a href="/bill">The draft</a> / {_clause_label(cid)}</p>
  <h1>{esc(c['id'])} — {esc(c['heading'])} {_status(c['status'])}</h1>
</header>
<div class="clause-focus" data-clause="{esc(c['id'])}">
  <div class="cbody"><p>{esc(c['statute_text'])}</p>{plain}</div>
</div>
{notes_html}
<nav class="pnav">{' '.join(nav)}</nav>
{refs_html}
<section id="margin" class="margin-block">
  <h2>The margin on {esc(cid)}</h2>
  {margin}
</section>
<section class="markform">
  <h2>Mark this clause</h2>
  {_mark_form(cid, None)}
</section>"""
    return page(f"{cid}", body, mode, path, [
        (f"Mark {cid}", f"/mark?c={cid}", "primary"),
        (f"Request on {cid}", f"/requests?c={cid}#new", "link"),
        ("The margin", "/margin", "link"),
        ("The draft", "/bill", "link"),
    ])


def mark_form_page(cid: str | None, re_no: str | None, quote: str | None,
                   mode: str, path: str) -> bytes:
    body = f"""
<header class="mast"><h1>The Inkwell</h1>
<p class="lede">Every mark is numbered, dated, and attached to a clause.
It lands in intake first — a person reads it in, and only then does it
stand on the public ledger.</p></header>
<section class="markform">{_mark_form(cid, re_no, quote)}</section>"""
    return page("The Inkwell", body, mode, path, [
        ("The draft", "/bill", "link"),
        ("The margin", "/margin", "link"),
        ("Intake queue", "/intake", "link"),
    ])


def margin(mode: str, path: str) -> bytes:
    rows = db.marks(status="read_in")
    items = "".join(_mark_html(m) for m in rows) or (
        '<p class="quiet">The ledger is empty. Marks enter through the '
        'Inkwell and are read in from the intake queue.</p>')
    n = db.queue_count()
    body = f"""
<header class="mast"><h1>The margin</h1>
<p class="lede">The public ledger — every mark read in, numbered and
dated, attached to its clause. The record does not erase; it amends in
the open.</p></header>
{items}"""
    return page("The Margin", body, mode, path, [
        ("New mark", "/mark", "primary"),
        (f"Intake queue ({n})", "/intake", "link"),
        ("The draft", "/bill", "link"),
    ])


def intake(mode: str, path: str) -> bytes:
    rows = db.marks(status="queued")
    items = "".join(f"""
<article class="mark intake">
  <p class="mno"><b>#{m['id']}</b> · {esc(m['created_at'])} ·
    {KIND_WORDS.get(m['kind'], 'comment')} · {_clause_label(m['clause_id'])}
    {" · " + esc(m["author_label"]) if m["author_label"] else " · unsigned"}</p>
  {'<blockquote class="quote">“' + esc(m["quote_text"]) + '”</blockquote>' if m["quote_text"] else ""}
  {'<p class="proposed"><b>Proposed:</b> ' + esc(m["proposed_text"]) + '</p>' if m["proposed_text"] else ""}
  <p>{esc(m['body'])}</p>
  <form method="post" action="/api/mark_action" class="stack">
    <input type="hidden" name="id" value="{m['id']}">
    <label>Answer in the open <span class="quiet">(optional — enters the record with the mark)</span>
      <input name="response" placeholder="The drafting table's public answer."></label>
    <div class="acts">
      <button name="action" value="read_in" class="btn">Read in</button>
      <button name="action" value="held" class="btn ghost">Hold</button>
      <button name="action" value="crisis_routed" class="btn ghost">Crisis route</button>
    </div>
  </form>
</article>""" for m in rows) or (
        '<p class="quiet">The queue is empty — nothing waits for read-in.</p>')
    held = db.marks(status="held")
    crisis = db.marks(status="crisis_routed")
    body = f"""
<header class="mast"><h1>Intake queue</h1>
<p class="lede">What lands here is dark until a person reads it in.
<b>Read in</b> gives it a public number — answer in the open and the
answer enters the record beside it. <b>Hold</b> sets it aside.
<b>Crisis route</b> counts it and keeps it off the ledger — someone in
trouble gets pointed at help, not published.</p></header>
{items}
<p class="quiet">Held: {len(held)} · Crisis-routed: {len(crisis)}</p>"""
    return page("Intake", body, mode, path, [
        ("The margin", "/margin", "primary"),
        ("Requests", "/requests", "link"),
        ("The draft", "/bill", "link"),
    ])


def requests_desk(clause_id: str | None, mode: str, path: str) -> bytes:
    rows = db.requests()
    def row(r):
        nxt = REQ_NEXT.get(r["status"])
        acts = []
        if nxt:
            acts.append(
                f'<button name="status" value="{nxt}" class="btn">'
                f'Mark {STATUS_WORDS[nxt]}</button>')
        if r["status"] not in ("incorporated", "declined"):
            acts.append('<button name="status" value="declined" '
                        'class="btn ghost">Decline</button>')
        note = (f'<p class="quiet">steward: {esc(r["steward_note"])}</p>'
                if r["steward_note"] else "")
        org = f' · {esc(r["org_or_role"])}' if r["org_or_role"] else ""
        return f"""
<article class="req">
  <p class="mno"><b>{esc(r['public_no'])}</b> · {esc(r['req_type'])} ·
    {_status(r['status'])} · {_status(r['stance'])}{org} ·
    {_clause_label(r['clause_id'])}</p>
  <p><b>{esc(r['summary'])}</b>
    {' — ' + esc(r['details']) if r['details'] else ''}</p>
  {note}
  <form method="post" action="/api/request_status" class="acts">
    <input type="hidden" name="id" value="{r['id']}">{''.join(acts)}
  </form>
</article>"""
    items = "".join(row(r) for r in rows) or (
        '<p class="quiet">No requests yet — the desk is clear.</p>')
    options = ['<option value="">— no clause —</option>'] + [
        f'<option value="{esc(c["id"])}"'
        f'{" selected" if c["id"] == clause_id else ""}>'
        f'{esc(c["id"])} — {esc(c["heading"])}</option>'
        for c in db.clauses()]
    body = f"""
<header class="mast"><h1>Requests desk</h1>
<p class="lede">What people ask of the draft — briefings, amendments,
positions, questions — one pipeline: <b>new → reviewing → scheduled →
incorporated</b>. Declined is a verdict, not a graveyard: it stays on
the record.</p></header>
<section id="new" class="markform">
  <h2>New request</h2>
  <form method="post" action="/api/request" class="stack">
    <div class="row">
      <label>Type<select name="req_type">
        <option value="briefing">Briefing / walkthrough</option>
        <option value="amendment">Amendment</option>
        <option value="position">Position</option>
        <option value="question">Question</option>
        <option value="other">Other</option>
      </select></label>
      <label>Clause<select name="clause_id">{''.join(options)}</select></label>
    </div>
    <label>Who is asking<input name="org_or_role"
      placeholder="Office, organization, or role"></label>
    <label>The ask<input name="summary" required
      placeholder="One sentence — what is being asked?"></label>
    <label>Detail<textarea name="details" rows="3"
      placeholder="Optional — the reasoning, the source, the deadline."></textarea></label>
    <label>Contact <span class="quiet">(steward-only — never shown)</span>
      <input name="contact" autocomplete="off"></label>
    <button class="btn" type="submit">Enter the request</button>
  </form>
</section>
{items}"""
    return page("Requests", body, mode, path, [
        ("New request", "/requests#new", "primary"),
        ("The draft", "/bill", "link"),
        ("Intake queue", "/intake", "link"),
    ])


def positions(mode: str, path: str) -> bytes:
    rows = db.positions()
    items = "".join(f"""
<article class="mark">
  <p class="mno"><b>{esc(p['person'])}</b> · {_status(p['stance'])} ·
    {esc(p['noted_at'])}{' · ' + esc(p['source']) if p['source'] else ''}</p>
  <p>{esc(p['provision'])}</p>
</article>""" for p in rows) or (
        '<p class="quiet">No positions recorded yet. Silence is a position '
        'too — after the window, it is recorded as such.</p>')
    body = f"""
<header class="mast"><h1>Who stands where</h1>
<p class="lede">Person × provision × stance, dated. Every send and every
answer lands here; refusing to engage is itself a position once the
window closes.</p></header>
<section id="add" class="markform">
  <h2>Record a position</h2>
  <form method="post" action="/api/position" class="stack">
    <div class="row">
      <label>Who<input name="person" required
        placeholder="Name or office"></label>
      <label>Stance<select name="stance">
        <option value="support">Supports</option>
        <option value="oppose">Opposes</option>
        <option value="conditional">Conditional</option>
        <option value="neutral">Neutral</option>
        <option value="watching">Watching</option>
      </select></label>
    </div>
    <label>On what<input name="provision" required
      placeholder="e.g. Title II funding braid, or the whole draft"></label>
    <label>Source<input name="source"
      placeholder="Optional — email, meeting, call (dated)"></label>
    <button class="btn" type="submit">Record</button>
  </form>
</section>
{items}"""
    return page("Positions", body, mode, path, [
        ("Add position", "/positions#add", "primary"),
        ("The draft", "/bill", "link"),
        ("Requests", "/requests", "link"),
    ])


def claims(mode: str, path: str) -> bytes:
    rows = db.claims()
    items = "".join(f"""
<article class="mark">
  <p class="mno"><b>{esc(c['figure'])}</b> · {_status(c['status'])}
    {' · checked ' + esc(c['checked']) if c['checked'] else ''}</p>
  <p>{esc(c['claim'])}</p>
  <p class="quiet">{esc(c['source'] or 'internal derivation')}
    {' — ' + esc(c['derivation']) if c['derivation'] else ''}</p>
</article>""" for c in rows)
    body = f"""
<header class="mast"><h1>Claims ledger</h1>
<p class="lede">Every figure the campaign says out loud, with its status.
<b>Verified</b> means checked against a named source. <b>Estimate</b>
means derived, derivation shown, awaiting review. Nothing unverified
ships as fact.</p></header>
{items}"""
    return page("Claims", body, mode, path, [
        ("The draft", "/bill", "primary"),
        ("Decisions", "/decisions", "link"),
        ("Editions", "/editions", "link"),
    ])


def decisions(mode: str, path: str) -> bytes:
    items = "".join(f"""
<article class="mark">
  <p class="mno"><b>Decision {d['num']}</b> · {_clause_label(d['clause'])} ·
    <span class="st st-locked">locked</span></p>
  <p><b>{esc(d['title'])}</b>{' — ' + esc(d['why']) if d['why'] else ''}</p>
</article>""" for d in db.decisions())
    body = f"""
<header class="mast"><h1>Locked decisions</h1>
<p class="lede">The design calls that hold the draft up — locked, never
relitigated quietly. A change here goes through the record like
everything else.</p></header>
{items}"""
    return page("Decisions", body, mode, path, [
        ("The draft", "/bill", "primary"),
        ("Claims", "/claims", "link"),
        ("The margin", "/margin", "link"),
    ])


def editions(mode: str, path: str) -> bytes:
    rows = db.editions()
    items = "".join(
        f'<article class="mark"><p class="mno"><b>{esc(e["edition"])}</b> · '
        f'{esc(e["date"])} · '
        f'{_clause_label(e["clause"]) if e["clause"] != "—" else "—"}</p>'
        f"<p>{esc(e['change'])}</p></article>" for e in reversed(rows))
    body = f"""
<header class="mast"><h1>Editions</h1>
<p class="lede">The change ledger — how the draft got here, newest first.
The record does not erase; it amends in the open.</p></header>
{items}"""
    return page("Editions", body, mode, path, [
        ("The draft", "/bill", "primary"),
        ("The margin", "/margin", "link"),
        ("Positions", "/positions", "link"),
    ])


def not_found(mode: str, path: str) -> bytes:
    body = '<header class="mast"><h1>Not found</h1>' \
           '<p class="lede">That page is not part of this desk.</p></header>'
    return page("Not found", body, mode, path,
                [("Desk", "/", "primary")])
