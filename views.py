#!/usr/bin/env python
"""views.py — HTML rendering for the standalone Bill Platform.

Server-rendered, stdlib only. Three distinct screen modes share one clean
semantic engine:

    mode-desk    2-column desktop workspace (sticky index rail + reading spine)
    mode-tv      16:9 presentation stage (/present 8-slide deck + room scale)
    mode-mobile  thumb-zone bottom navigation bar + single-column touch layout

Style law (Brad's UI contract + minimalist-ui): 17–19px body text on desk/mobile,
24–44px on TV, warm monochrome palette, color = state only, bold = names and
actions, sentences not chips, hairline 1px borders only, zero emoji.
"""
from __future__ import annotations

import html
import os
import re
import urllib.parse
from pathlib import Path

import db

HERE = Path(__file__).resolve().parent

BRAND = "Turnbuchalla"
SUB = "MN Rent Assurance & Deposit Protection Act — working platform"

# URL mount point (mirrors server.MOUNT) — all generated links get the
# prefix when the app is deployed under a path, e.g. semptify.org/bill.
MOUNT = os.environ.get("BILL_MOUNT", "").rstrip("/")

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
    "target": "target", "contacted": "contacted", "talks": "in talks",
    "endorsed": "endorsed", "retracted": "retracted", "proposed": "proposed",
    "published": "published",
}
REQ_NEXT = {"new": "reviewing", "reviewing": "scheduled",
            "scheduled": "incorporated"}
KIND_WORDS = {"question": "question", "edit": "proposed edit",
              "comment": "comment"}


def esc(v) -> str:
    return html.escape("" if v is None else str(v), quote=True)


def _mode_links(current: str, path: str) -> str:
    out = []
    specs = (
        ("auto", "Auto"),
        ("desk", "Desktop"),
        ("tv", "TV / Present"),
        ("mobile", "Mobile / Tablet"),
    )
    for m, label in specs:
        cls = "mode-link on" if m == current else "mode-link"
        dest = "/present?s=1" if (m == "tv" and path == "/") else path
        href = f"/mode/{m}?next={urllib.parse.quote(dest, safe='')}"
        out.append(f'<a class="{cls}" href="{href}">{label}</a>')
    return "".join(out)


def _steward_control(ctx: dict) -> str:
    nxt = urllib.parse.quote(ctx["path"], safe="")
    if ctx["steward"]:
        return (f'<a class="steward-pill on" href="/steward/lock?next={nxt}" '
                f'title="Click to lock Steward triage">Steward: On</a>')
    href = f"/steward/toggle?next={nxt}" if ctx.get("onetap") else f"/steward?next={nxt}"
    return (f'<a class="steward-pill" href="{href}" '
            f'title="Unlock Steward triage controls">Steward: Off</a>')


def toolbar(actions: list[tuple[str, str, str]], label: str = "Context actions") -> str:
    """actions: [(label, href, kind)] — kind in ('primary', 'link', 'pill', 'pill-on')."""
    items = "".join(
        f'<a class="tb-{k}" href="{esc(h)}">{esc(t)}</a>' for t, h, k in actions)
    return (f'<nav class="toolbar" aria-label="{esc(label)}">'
            f'<div class="tb-items">{items}</div>'
            f'<div class="tb-selection" id="tbSelection" hidden></div>'
            f'</nav>')


def _desk_rail(ctx: dict, sublinks: list[tuple[str, str]] | None = None) -> str:
    path = ctx["path"]
    n_q = db.queue_count()
    n_req = db.open_request_count()
    nav_items = [
        ("/", "Home"),
        ("/desk", "Desk"),
        ("/bill", "The Bill (23)"),
        ("/calculator", "Funding Braid"),
        ("/margin", "Public Margin"),
        ("/requests", f"Requests ({n_req})"),
        ("/changes", "Changes"),
        ("/search", "Search"),
        ("/teach", "Teach"),
        ("/track", "Track"),
        ("/campaign", "Campaign"),
        ("/sign", "Sign the Bill"),
        ("/positions", "Positions"),
        ("/claims", "Claims Ledger"),
        ("/decisions", "Locked Decisions"),
        ("/editions", "Editions"),
        ("/intake", f"Intake Queue ({n_q})"),
        ("/tv", "TV Briefing Deck"),
        ("—", "Public pages"),
        ("/bill/research", "Numbers & Sources"),
        ("/bill/precedents", "Where Others Tried"),
        ("/bill/history", "History"),
        ("/bill/providers", "For Providers"),
        ("/bill/brief", "The Brief"),
        ("/bill/classroom", "Classroom"),
        ("/bill/press", "Press"),
        ("/bill/myths", "Myths"),
        ("/what-the-bill-changes", "What Changes"),
    ]
    links = []
    for href, label in nav_items:
        if href == "—":
            links.append(f'<li class="rail-sep">{esc(label)}</li>')
            continue
        active = ((path == href) or
                  (href == "/bill" and path.startswith("/clause/")) or
                  (href.startswith("/bill/") and path == href))
        cls = ' class="rail-on"' if active else ""
        links.append(f'<li><a href="{href}"{cls}>{esc(label)}</a></li>')

    sub_html = ""
    if sublinks:
        s_items = "".join(
            f'<li><a href="{esc(h)}">{esc(lbl)}</a></li>' for lbl, h in sublinks)
        sub_html = f'<p class="rail-head">On this screen</p><ul class="rail-sub">{s_items}</ul>'

    return (f'<aside class="desk-rail" aria-label="Workspace navigation">'
            f'<p class="rail-head">Platform</p>'
            f'<ul class="rail-nav">{"".join(links)}</ul>'
            f'{sub_html}'
            f'</aside>')


def _mobile_bottom_nav(ctx: dict) -> str:
    path = ctx["path"]
    tabs = [
        ("/", "Home", '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9h10M7 13h6"/>'),
        ("/bill", "Bill", '<path d="M6 3h9l5 5v13H6z"/><path d="M14 3v6h6M9 13h6M9 17h6"/>'),
        ("/calculator", "Braid", '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 12h2M14 12h2M8 16h2M14 16h2"/>'),
        ("/margin", "Margin", '<path d="M4 5h16v11H8l-4 4z"/>'),
        ("/requests", "Requests", '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>'),
    ]
    out = []
    for href, label, svg_inner in tabs:
        on = (path == href) or (href == "/bill" and path.startswith("/clause/"))
        cls = "mnav-item on" if on else "mnav-item"
        out.append(
            f'<a class="{cls}" href="{href}">'
            f'<svg viewBox="0 0 24 24" width="20" height="20" fill="none" '
            f'stroke="currentColor" stroke-width="1.75" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{svg_inner}</svg>'
            f'<span>{label}</span></a>'
        )
    return f'<nav class="mobile-bar" aria-label="Mobile navigation">{"".join(out)}</nav>'


def page(title: str, body: str, ctx: dict,
         actions: list[tuple[str, str, str]],
         toolbar_label: str = "Context actions",
         sublinks: list[tuple[str, str]] | None = None,
         is_stage: bool = False) -> bytes:
    mode = ctx["mode"]
    path = ctx["path"]
    stage_cls = " is-stage" if is_stage else ""
    rail = "" if is_stage else _desk_rail(ctx, sublinks)
    doc = f"""<!DOCTYPE html>
<html lang="en" data-mount="{MOUNT}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {BRAND}</title>
<meta name="description" content="{esc(SUB)} — a working draft presented in the open: statute text, plain language, the funding math, and the public record of every mark and change.">
<meta property="og:title" content="{esc(title)} — {BRAND}">
<meta property="og:description" content="{esc(SUB)} — working draft, public ledger, living document.">
<meta property="og:type" content="website">
<meta property="og:image" content="/static/logo-512.png">
<link rel="icon" type="image/png" href="/static/favicon.png">
<link rel="stylesheet" href="/static/platform.css">
</head>
<body class="mode-{'desk' if mode == 'auto' else esc(mode)}{stage_cls}"{' data-mode-auto="1"' if mode == 'auto' else ''} data-steward="{'1' if ctx['steward'] else '0'}">
<a class="skip" href="#main-content">Skip to content</a>
<div class="viewport-shell">
<header class="topbar">
  <a class="brand" href="/"><img class="brand-logo" src="/static/logo.svg" alt=""><span>{BRAND}<small>{esc(SUB)}</small></span></a>
  <div class="topbar-right">
    <div class="modes" role="group" aria-label="Screen mode">{_mode_links(mode, path)}</div>
    {_steward_control(ctx)}
  </div>
</header>
{toolbar(actions, toolbar_label)}
<div class="workspace">
  {rail}
  <main class="page" id="main-content">
  {body}
  </main>
</div>
<footer class="foot">
  <p class="foot-brand"><img class="foot-logo" src="/static/logo.svg" alt=""><img class="foot-flag" src="/static/mn-flag.svg" alt="Minnesota state flag"><b>Presented by <a href="https://semptify.org">Semptify</a></b>
  — housing rights, written in public. A Semptify project.</p>
  <p>Working draft — nothing here is filed law. Marks land in intake and
  are read into the ledger by a person, never automatically.
  <a href="/help">Need help now?</a></p>
  <p class="foot-thanks">With gratitude to the men and women who serve —
  and have served — in the Armed Forces of the United States.</p>
  <p class="foot-nav"><a href="/">Home</a> · <a href="/desk">Desk</a> ·
  <a href="/bill">The bill</a> · <a href="/calculator">Funding braid</a> ·
  <a href="/margin">The margin</a> · <a href="/intake">Intake</a> ·
  <a href="/requests">Requests</a> · <a href="/positions">Positions</a> ·
  <a href="/claims">Claims</a> · <a href="/decisions">Decisions</a> ·
  <a href="/editions">Editions</a> · <a href="/changes">Changes</a> ·
  <a href="/stewards">Stewards</a> ·
  <a href="/search">Search</a> · <a href="/teach">Teach</a> ·
  <a href="/track">Track</a> · <a href="/campaign">Campaign</a> · <a href="/sign">Sign</a> · <a href="/tv">TV Present</a> ·
  <a href="/help">Help</a> · <a href="/legal">Legal</a> ·
  <a href="https://semptify.org">semptify.org</a></p>
</footer>
{_mobile_bottom_nav(ctx)}
</div>
<script src="/static/platform.js"></script>
</body>
</html>"""
    if MOUNT:
        doc = (doc
               .replace('href="/', f'href="{MOUNT}/')
               .replace('action="/', f'action="{MOUNT}/')
               .replace('src="/', f'src="{MOUNT}/')
               .replace('content="/', f'content="{MOUNT}/'))
    return doc.encode("utf-8")


def _status(status: str) -> str:
    return (f'<span class="st st-{esc(status)}">'
            f'{esc(STATUS_WORDS.get(status, status))}</span>')


_CLAUSE_IDS: set | None = None


def _clause_label(cid) -> str:
    global _CLAUSE_IDS
    if not cid:
        return '<span class="clref gen">general</span>'
    if _CLAUSE_IDS is None:
        _CLAUSE_IDS = {r["id"] for r in db.clauses()}
    if cid in _CLAUSE_IDS:
        return f'<b class="clref"><a href="/clause/{esc(cid)}">{esc(cid)}</a></b>'
    return f'<span class="clref gen">{esc(cid)}</span>'


def _reline(m) -> str:
    return f' · re: <a href="/margin#{esc(m["reply_to"])}">{esc(m["reply_to"])}</a>' if m["reply_to"] else ""


def _mark_html(m, show_answer_link: bool = True, steward: bool = False) -> str:
    quote = (f'<blockquote class="quote">“{esc(m["quote_text"])}”</blockquote>'
             if m["quote_text"] else "")
    proposed = (f'<p class="proposed"><b>Proposed wording:</b> '
                f'{esc(m["proposed_text"])}</p>'
                if m["proposed_text"] else "")
    response = (f'<p class="response"><b>{esc(m["responder_role"] or "Drafting Table")}:</b> '
                f'{esc(m["response_body"])}</p>'
                if m["response_body"] else "")
    answer = (f'<p class="mact"><a href="/mark?re={esc(m["public_no"])}'
              f'{"&c=" + esc(m["clause_id"]) if m["clause_id"] else ""}">'
              f'answer by reference</a></p>' if show_answer_link else "")
    kind = KIND_WORDS.get(m["kind"], "comment")
    if m["redacted_at"]:
        author = ' · <span class="quiet">name withheld by stewards</span>'
    elif m["change_id"]:
        author = ' · a contributor'
    else:
        author = (f' · {esc(m["author_label"])}' if m["author_label"]
                  else " · unsigned")
    edited = (f' <span class="quiet">(edited by stewards'
              f'{(" — " + esc(m["edit_note"])) if m["edit_note"] else ""})'
              f'</span>' if m["edited_at"] else "")
    no = m["public_no"] or "#" + str(m["id"])
    plink = (f' <a class="plink" href="/margin#{esc(m["public_no"])}" '
             f'title="Link to this mark">#</a>' if m["public_no"] else "")
    if m["retracted_at"]:
        retract = (f'{_status("retracted")} <span class="quiet">'
                   f'{esc(m["retracted_at"])}'
                   f'{(" — " + esc(m["retract_note"])) if m["retract_note"] else ""}</span>')
        return (f'<article class="mark retracted" id="{esc(no)}">'
                f'<p class="mno"><b>{esc(no)}</b>{plink} {retract}</p>'
                f'<p><del>{esc(m["body"])}</del></p></article>')
    mod_form = ""
    if steward and m["public_no"]:
        mod_form = f'''
  <form method="post" action="/api/mark_action" class="stack mact">
    <input type="hidden" name="id" value="{m["id"]}">
    <input type="hidden" name="back" value="/margin">
    <input name="note" placeholder="Moderation note (public on redact/edit)" maxlength="500">
    <input name="new_body" placeholder="Replacement text (Edit only)">
    <button name="action" value="retract" class="ghost">Retract</button>
    <button name="action" value="redact" class="ghost">Redact name</button>
    <button name="action" value="edit" class="ghost">Edit text</button>
  </form>'''
    return (f'<article class="mark" id="{esc(no)}">'
            f'<p class="mno"><b>{esc(no)}</b>{plink}'
            f' · {esc(m["read_in_at"] or m["created_at"])} · {kind} · '
            f'{_clause_label(m["clause_id"])}{author}{_reline(m)}</p>'
            f'{quote}{proposed}<p>{esc(m["body"])}{edited}</p>{response}{answer}'
            f'{mod_form}</article>')


def _mark_form(cid: str | None, re_no: str | None,
               quote: str | None = None,
               kind_sel: str | None = None) -> str:
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
             f'<i>“{esc(quote[:180])}”</i></p>') if quote else ""
    k_opts = []
    for k_val, k_lbl in (("comment", "Comment"), ("question", "Question"), ("edit", "Proposed edit")):
        sel = " selected" if k_val == kind_sel else ""
        k_opts.append(f'<option value="{k_val}"{sel}>{k_lbl}</option>')
    return f"""
<form method="post" action="/api/mark" class="stack">
  {reline}{qline}
  <div class="row">
    <label>Clause<select name="clause_id">{''.join(options)}</select></label>
    <label>Kind<select name="kind">{''.join(k_opts)}</select></label>
  </div>
  <label>Your mark<textarea name="body" rows="4" required
    placeholder="Write it plainly — a suggestion, a concern, a correction, a question."></textarea></label>
  <label>Proposed wording <span class="quiet">(optional — for clause edits)</span>
    <textarea name="proposed" rows="2"
      placeholder="The exact statutory or plain words you propose."></textarea></label>
  <div class="row">
    <label>Name or role <span class="quiet">(optional — sign it and it stands publicly)</span>
      <input name="name" autocomplete="name" placeholder="e.g. St. Paul Renter, Rural Provider"></label>
    <label>Contact <span class="quiet">(optional — never shown publicly)</span>
      <input name="contact" autocomplete="off"></label>
      <input name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
  </div>
  <p class="crisis">If this is about your own housing right now —
  <b>HOME Line 612-728-5767</b> first · <a href="/help">more help lines</a>.
  This desk is for the draft.</p>
  <button class="btn" type="submit">Enter the mark</button>
</form>"""


# ---------- pages ----------

def index(ctx: dict) -> bytes:
    meta = db.meta()
    n_clauses = len(db.clauses())
    counts = db.margin_counts()
    n_marks = sum(counts.values())
    n_eds = len(db.editions())
    n_req = db.open_request_count()
    body = f"""
<section class="index-hero">
  <p class="stage-kicker"><img class="mn-flag" src="/static/mn-flag.svg"
    alt="Minnesota state flag"> Presented by <a href="https://semptify.org">Semptify</a> · {esc(meta['jurisdiction'])}</p>
  <h1>{esc(meta['short_title'])}</h1>
  <p class="lede">{esc(meta['thesis'])}</p>
  <p class="live-badge">{_status('current')} <b>Living document</b> — last
  publish {esc(meta['updated'])} · {n_eds} editions on the record ·
  <a href="/editions">see the change ledger</a></p>
  <p class="hero-acts"><a class="btn" href="/bill">Read the draft</a>
    <a class="btn ghost" href="/tv">TV briefing deck</a>
    <a class="btn ghost" href="/calculator">Funding calculator</a></p>
</section>

<section>
  <h2>Introduction — what this is</h2>
  <p>This platform presents a real, working bill — the Minnesota Rent
  Assurance &amp; Deposit Protection Act — the way a bill should be shown
  to the public: the full statutory text in {n_clauses} clauses, the plain
  English beside it, the math behind it, and the record of every mark,
  request, and change it has ever taken.</p>
  <p>It is <b>living</b>, not a PDF. The draft updates as it is written,
  every change lands on the <a href="/editions">Editions ledger</a>, and
  every figure is marked <a href="/claims">verified or estimate</a>. Nothing
  here is filed law — but nothing here is hidden either.</p>
</section>

<section>
  <h2 id="how-it-works">How it works</h2>
  <ol class="how-steps">
    <li><b>Read it your way.</b> The draft at <a href="/bill">/bill</a>
    carries statute text and plain language side by side, with audience
    lenses for renters, housing providers, and lawmakers. Three screen
    modes — <b>Desktop</b>, <b>TV / Present</b>, and <b>Mobile / Tablet</b> —
    fit whatever screen you're on.</li>
    <li><b>Mark the draft.</b> Any clause takes a mark — a question, a
    comment, or a proposed edit with your own wording — through the
    <a href="/mark">Inkwell</a>. Highlight text on a clause and the toolbar
    offers to quote it directly.</li>
    <li><b>Marks get read in by a person.</b> Nothing posts automatically.
    Marks land in a dark <a href="/intake">intake queue</a>; a steward
    reads each in (it gets its public M-number), holds it, or crisis-routes
    it — someone in housing trouble is pointed at help, not published.</li>
    <li><b>The ledger answers in the open.</b> Read-in marks live on the
    <a href="/margin">Margin</a> — numbered, dated, attached to their
    clause, answered by the drafting table, and replyable by reference
    (<i>re: M-0001</i>). {n_marks} on the record so far.</li>
    <li><b>Requests get worked, not lost.</b> Briefings, amendments,
    positions, and asks go through the <a href="/requests">Requests
    desk</a>: new → reviewing → scheduled → incorporated. {n_req} active.</li>
    <li><b>The math is checkable.</b> The <a href="/calculator">funding
    braid calculator</a> runs the live three-source model — deposit float,
    M1PR advance, landlord match — against any rent, portfolio size, and
    stress scenario.</li>
  </ol>
</section>

<section>
  <h2>Presented by Semptify</h2>
  <p>Semptify builds housing-rights tools in the open — the bill, this
  platform, and the guides and record tools at
  <a href="https://semptify.org">semptify.org</a>. No advertising, no
  tracking, no accounts here — the record is the interface.</p>
</section>"""
    return page("Home", body, ctx, [
        ("Read the draft", "/bill", "primary"),
        ("How it works", "#how-it-works" , "link"),
        ("Funding braid", "/calculator", "link"),
        ("semptify.org", "https://semptify.org", "link"),
    ], "Front page", sublinks=[
        ("Introduction", "#"), ("How it works", "#"), ("Semptify", "https://semptify.org"),
    ])


def desk(ctx: dict) -> bytes:
    meta = db.meta()
    ev = db.last_event()
    cur = db.journey_current()
    n_queued = db.queue_count()
    n_open = db.open_request_count()
    counts = db.margin_counts()
    n_marks = sum(counts.values())
    n_clauses = len(db.clauses())
    braid = db.calculate_braid(1300.0, 1, True)

    if ev:
        stands = f"Last event: {esc(ev['what'])} — {esc(ev['happened_at'])}."
    else:
        stands = "Nothing has happened yet — the platform is freshly seeded."
    if cur:
        stands += (f" The campaign sits at <b>{esc(cur['name'])}</b> — "
                   f"{esc(cur['note'])}.")

    if n_queued and ctx["steward"]:
        nxt = (f'<a class="next" href="/intake">Triage the intake queue '
               f'({n_queued} waiting)</a>')
    elif n_open and ctx["steward"]:
        nxt = (f'<a class="next" href="/requests">Work the requests desk '
               f'({n_open} open)</a>')
    else:
        nxt = ('<a class="next" href="/bill">Read the 23-clause draft</a> '
               'or <a class="next" href="/tv">launch the 8-slide TV briefing</a>.')

    journey = "".join(
        f'<li class="j-{esc(j["state"])}"><b>{j["step"]}. '
        f'{esc(j["name"])}</b> {_status(j["state"])}'
        f'<br><span class="quiet">{esc(j["note"])}</span></li>'
        for j in db.journey())

    pillars = "".join(
        f'<div class="bento-item">'
        f'<p class="mno"><b>{esc(p["label"])}</b> · {_clause_label(p["clause_ref"])}</p>'
        f'<p><b>{esc(p["headline"])}</b></p>'
        f'<p class="quiet">{esc(p["detail"])}</p>'
        f'</div>'
        for p in meta["summary_points"])

    body = f"""
<section class="spine">
  <p class="spine-line"><span class="spine-tag">Objective</span>
    {esc(meta['thesis'])}</p>
  <p class="spine-line"><span class="spine-tag">Where it stands</span>
    {stands} The draft holds <b>{n_clauses} clauses</b> across five titles;
    <b>{n_marks}</b> marks are on the public ledger and <b>{n_queued}</b>
    wait in dark intake.</p>
  <p class="spine-line"><span class="spine-tag">Next action</span>{nxt}</p>
</section>

<section>
  <h2>Core mechanics at a glance</h2>
  <div class="bento-grid">{pillars}</div>
  <p class="pillar-calc">Base funding braid at $1,300/mo rent:
    <b>${braid['deposit_float_mo']:.2f}</b> deposit float +
    <b>${braid['renter_share_mo']:.2f}</b> M1PR monthly advance +
    <b>${braid['landlord_match_mo']:.2f}</b> landlord match =
    <b>${braid['total_pool_mo']:.2f}/mo</b> (~1.18% of rent).
    <a href="/calculator">Test any rent or building size →</a></p>
</section>

<section>
  <h2>The pipeline</h2>
  <ol class="journey">{journey}</ol>
</section>

<section class="evidence">
  <h2>Evidence &amp; working boards</h2>
  <ul class="ev">
    <li><a href="/bill">The draft</a> — all 23 clauses, audience lenses, plain-English layer, margins open.</li>
    <li><a href="/calculator">Funding braid calculator</a> — test monthly rent, units, M1PR credit, and stress shocks.</li>
    <li><a href="/margin">The margin</a> — public docket of read-in marks and drafter answers.</li>
    <li><a href="/requests">Requests desk</a> — briefings, amendments, positions, and asks ({n_open} active).</li>
    <li><a href="/positions">Positions</a> — who stands where, dated.</li>
    <li><a href="/claims">Claims ledger</a> — every public figure, verified or labeled estimate.</li>
    <li><a href="/decisions">Locked decisions</a> — the eight non-negotiable safeguards.</li>
    <li><a href="/editions">Editions</a> — dated change ledger (E-01 through E-09).</li>
    <li><a href="/tv">TV / Presentation stage</a> — 8-slide 16:9 briefing deck for rooms and screenshares.</li>
  </ul>
</section>"""
    acts = [
        ("The bill", "/bill", "primary"),
        ("Funding calculator", "/calculator", "link"),
        ("The margin", "/margin", "link"),
        ("Requests", "/requests", "link"),
        ("Present (TV)", "/tv", "link"),
    ]
    if ctx["steward"] and n_queued:
        acts.append((f"Triage intake ({n_queued})", "/intake", "pill-on"))
    return page("Desk", body, ctx, acts, "Desk actions")


def bill(lens: str, view_style: str, ctx: dict) -> bytes:
    if lens not in ("all", "renter", "provider", "lawmaker"):
        lens = "all"
    if view_style not in ("both", "statute", "plain"):
        view_style = "both"

    titles = {t["num"]: t for t in db.titles()}
    counts = db.margin_counts()
    parts = []
    sublinks = []
    last_title = None
    shown = 0

    for c in db.clauses():
        aud_list = [a.strip() for a in (c["audiences"] or "renter,provider,lawmaker").split(",") if a.strip()]
        if lens != "all" and lens not in aud_list:
            continue
        shown += 1
        if c["title_num"] != last_title:
            last_title = c["title_num"]
            t = titles[last_title]
            tid = f"title-{last_title}"
            sublinks.append((f"{t['code']}: {t['name']}", f"#{tid}"))
            parts.append(
                f'<h2 class="title-head" id="{tid}">{esc(t["code"])} — '
                f'{esc(t["name"])}</h2>'
                f'<p class="title-note">{esc(t["subtitle"])}</p>')
        n = counts.get(c["id"], 0)
        badge = (f'<a class="mcount" href="/clause/{esc(c["id"])}#margin">'
                 f'({n})</a>') if n else ''
        tag = _status(c["status"])

        statute_html = (f'<p class="statute-copy">{esc(c["statute_text"])}</p>'
                        if view_style in ("both", "statute") else "")
        plain_html = (f'<p class="plain"><b>In plain language:</b> '
                      f'{esc(c["plain_text"])}</p>'
                      if (c["plain_text"] and view_style in ("both", "plain")) else "")

        lens_note = ""
        if lens == "renter" and c["renter_note"]:
            lens_note = f'<p class="lens-callout"><b>For renters:</b> {esc(c["renter_note"])}</p>'
        elif lens == "provider" and c["provider_note"]:
            lens_note = f'<p class="lens-callout"><b>For housing providers:</b> {esc(c["provider_note"])}</p>'
        elif lens == "lawmaker" and c["lawmaker_note"]:
            lens_note = f'<p class="lens-callout"><b>For lawmakers &amp; staff:</b> {esc(c["lawmaker_note"])}</p>'

        parts.append(f"""
<section class="clause" id="c-{esc(c['id'])}" data-clause="{esc(c['id'])}">
  <header class="chead">
    <a class="secnum" href="/clause/{esc(c['id'])}">{esc(c['id'])}</a>
    <h3><a class="chead-link" href="/clause/{esc(c['id'])}">{esc(c['heading'])}</a> {tag}</h3>
    <a class="annot" href="/mark?c={esc(c['id'])}" aria-label="Mark {esc(c['id'])}" title="Add a mark to {esc(c['id'])}">+</a>
    {badge}
  </header>
  <div class="cbody">{statute_html}{plain_html}{lens_note}</div>
</section>""")

    lens_bar = []
    for k, lbl in (("all", "All clauses"), ("renter", "Renter lens"),
                   ("provider", "Provider lens"), ("lawmaker", "Lawmaker lens")):
        kind = "pill-on" if lens == k else "pill"
        lens_bar.append((lbl, f"/bill?lens={k}&view={view_style}", kind))

    next_view = {"both": ("Plain only", "plain"),
                 "plain": ("Statute only", "statute"),
                 "statute": ("Statute + Plain", "both")}[view_style]

    body = f"""
<header class="mast">
  <h1>The draft, read through</h1>
  <p class="lede">Showing <b>{shown}</b> clause(s). Select any phrase to
  quote or propose an edit directly from the smart toolbar above; tap
  <b>+</b> to mark a clause, or click a clause code to inspect its sources
  and margin.</p>
</header>
{''.join(parts)}"""

    actions = [
        ("Mark the draft", "/mark", "primary"),
        *lens_bar,
        (next_view[0], f"/bill?lens={lens}&view={next_view[1]}", "link"),
        ("Calculator", "/calculator", "link"),
        ("Present", "/tv", "link"),
    ]
    return page("The Bill", body, ctx, actions, "Draft reader tools", sublinks=sublinks)


def clause_view(cid: str, ctx: dict) -> bytes | None:
    c = db.clause(cid)
    if not c:
        return None
    prev_id, next_id = db.clause_neighbors(cid)
    rows = db.marks(status="read_in", clause_id=cid)
    margin_html = "".join(_mark_html(m) for m in rows) or (
        '<p class="quiet">No marks read in on this clause yet.</p>')
    nav = []
    if prev_id:
        nav.append(f'<a class="pnav-btn" href="/clause/{esc(prev_id)}">← {esc(prev_id)}</a>')
    else:
        nav.append('<span></span>')
    if next_id:
        nav.append(f'<a class="pnav-btn" href="/clause/{esc(next_id)}">{esc(next_id)} →</a>')

    notes = []
    for label, field in (("Renter", "renter_note"),
                         ("Housing provider", "provider_note"),
                         ("Lawmaker & staff", "lawmaker_note")):
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
            refs.append(f'<li><a href="/claims#{esc(cl["id"])}"><b>{esc(cl["figure"])}</b></a> — '
                        f'{esc(cl["claim"])} {_status(cl["status"])} '
                        f'<span class="quiet">({esc(cl["source"] or "internal derivation")})</span></li>')
    refs_html = (f'<section class="refs"><h2>Standing on</h2>'
                 f'<ul class="ev">{"".join(refs)}</ul></section>' if refs else "")

    ch_rows = db.changes(clause_id=cid)
    hist_html = ""
    if ch_rows:
        items = "".join(
            f'<li><a href="/changes"><b>{esc(ch["public_no"])}</b></a> '
            f'{_status(ch["status"])} <span class="quiet">'
            f'{esc(ch["resolved_at"] or ch["created_at"])}</span>'
            + (f' — {esc(ch["proposed_text"])}' if ch["proposed_text"] else "")
            + "</li>" for ch in ch_rows)
        hist_html = (f'<section class="refs"><h2>Change history ({len(ch_rows)})</h2>'
                     f'<ul class="ev">{items}</ul></section>')

    plain = (f'<p class="plain"><b>In plain language:</b> '
             f'{esc(c["plain_text"])}</p>') if c["plain_text"] else ""

    body = f"""
<header class="mast">
  <p class="crumbs"><a href="/bill">The draft</a> / {_clause_label(cid)}</p>
  <h1>{esc(c['id'])} — {esc(c['heading'])} {_status(c['status'])}</h1>
</header>
<div class="clause-focus" data-clause="{esc(c['id'])}">
  <div class="cbody"><p class="statute-copy">{esc(c['statute_text'])}</p>{plain}</div>
</div>
{notes_html}
<nav class="pnav" aria-label="Adjacent clauses">{' '.join(nav)}</nav>
{refs_html}
{hist_html}
<section id="margin" class="margin-block">
  <h2>The margin on {esc(cid)} ({len(rows)})</h2>
  {margin_html}
</section>
<section class="markform" id="mark-clause">
  <h2>Mark this clause</h2>
  {_mark_form(cid, None)}
</section>"""

    leg_mail = ("mailto:?subject=" + urllib.parse.quote(
        f"MN Rent Assurance & Deposit Protection Act — {c['id']} {c['heading']}")
        + "&body=" + urllib.parse.quote(
        f"Please read {c['id']} ({c['heading']}) of the working draft.\n\n"
        f"{c['plain_text']}\n\nI'm asking you to carry this bill in 2027."))
    actions = [
        (f"Mark {cid}", f"/mark?c={cid}", "primary"),
        ("Send to a legislator", leg_mail, "link"),
        (f"Propose edit on {cid}", f"/mark?c={cid}&kind=edit", "link"),
        (f"Request on {cid}", f"/requests?c={cid}#new", "link"),
    ]
    if prev_id:
        actions.append((f"← {prev_id}", f"/clause/{prev_id}", "pill"))
    if next_id:
        actions.append((f"{next_id} →", f"/clause/{next_id}", "pill"))
    actions.append(("All clauses", "/bill", "link"))
    return page(f"Clause {cid}", body, ctx, actions, f"Clause {cid} tools")


def calculator(rent: float, units: int, m1pr: bool, ctx: dict) -> bytes:
    res = db.calculate_braid(rent, units, m1pr)
    m1pr_checked = " checked" if m1pr else ""
    oop_label = (
        "$0.00 / mo new out-of-pocket (covered via monthly M1PR tax-credit advance)"
        if res["m1pr_eligible"]
        else f"${res['renter_out_of_pocket_mo']:.2f} / mo direct disclosed pool line (household above $77,570 M1PR cap)"
    )
    body = f"""
<header class="mast">
  <h1>Three-source funding braid &amp; stress test</h1>
  <p class="lede">Test any Minnesota monthly rent, portfolio unit count, and
  M1PR eligibility against the 2026-10-23 math audit (<a href="/clause/II-3">Clause II-3</a>).
  Figures marked <b>estimate</b> carry transparent derivations awaiting formal actuarial review.</p>
</header>

<form method="get" action="/calculator" class="calc-form" id="braidForm">
  <div class="calc-controls">
    <label>Monthly rent ($/unit)
      <div class="calc-slider-row">
        <input type="range" min="600" max="3500" step="25" value="{int(res['monthly_rent'])}" id="rentRange" aria-label="Monthly rent slider">
        <input type="number" name="rent" id="rentInput" min="400" max="10000" step="25" value="{int(res['monthly_rent'])}">
      </div>
    </label>
    <label>Units in lease / portfolio
      <input type="number" name="units" id="unitsInput" min="1" max="500000" step="1" value="{res['units']}">
    </label>
    <label class="calc-check">
      <input type="checkbox" name="m1pr" value="1" id="m1prInput"{m1pr_checked}>
      <span>Tenant eligible for MN Renter's Credit (M1PR — income up to $77,570)</span>
    </label>
    <noscript><button class="btn" type="submit">Calculate</button></noscript>
  </div>
</form>

<section class="bento-grid calc-grid" aria-live="polite">
  <div class="bento-item">
    <p class="mno">Leg 1 · Escrowed Deposit Float (3% net)</p>
    <p class="big-num" id="valFloat">${res['deposit_float_mo']:.2f}<span>/unit/mo</span></p>
    <p class="quiet">4% Treasury yield on 1-month escrowed deposit minus the tenant's
    statutory 1% interest floor (<span id="valTenantInt">${res['tenant_1pct_interest_yr']:.2f}/yr</span> kept by renter).</p>
  </div>
  <div class="bento-item">
    <p class="mno">Leg 2 · Renter Share (M1PR Advance)</p>
    <p class="big-num" id="valRenter">${res['renter_share_mo']:.2f}<span>/unit/mo</span></p>
    <p class="quiet" id="valOop">{esc(oop_label)}</p>
  </div>
  <div class="bento-item">
    <p class="mno">Leg 3 · Landlord Matched Share</p>
    <p class="big-num" id="valLandlord">${res['landlord_match_mo']:.2f}<span>/unit/mo</span></p>
    <p class="quiet">Community-rated base + bounded experience band; clean years earn a mutual no-claim dividend.</p>
  </div>
  <div class="bento-item highlight">
    <p class="mno">Combined Assurance Pool (~1.18% of rent)</p>
    <p class="big-num" id="valTotal">${res['total_pool_mo']:.2f}<span>/unit/mo</span></p>
    <p class="quiet">Annual landlord match across <b id="valUnits">{res['units']}</b> unit(s):
    <b id="valLandlordYr">${res['landlord_annual_total']:,.2f}/yr</b> vs. <b>$5,600–$7,400</b> cost of a single eviction
    (<b id="valUnitYears">{res['unit_years_per_eviction']}</b> unit-years of match = 1 avoided eviction).</p>
  </div>
</section>

<section>
  <h2>Actuarial stress scenarios (per unit / month)</h2>
  <div class="stress-table">
    <div class="stress-row">
      <span><b>Base case</b> (~1.18% of rent · ~$106M statewide claims)</span>
      <b id="stBase">${res['stress_base_mo']:.2f} / mo</b>
    </div>
    <div class="stress-row">
      <span><b>Fraud / moral-hazard stress</b> (+30% claims shock · ~1.63% of rent)</span>
      <b id="stFraud">${res['stress_fraud_mo']:.2f} / mo</b>
    </div>
    <div class="stress-row">
      <span><b>Recession shock</b> (6% statewide lease default · ~2.31% of rent)</span>
      <b id="stRecession">${res['stress_recession_mo']:.2f} / mo</b>
    </div>
  </div>
</section>"""

    actions = [
        ("Clause II-3 (Braid)", "/clause/II-3", "primary"),
        ("$1,000 rent", "/calculator?rent=1000&units=1&m1pr=1", "pill" if int(rent) != 1000 else "pill-on"),
        ("$1,300 base", "/calculator?rent=1300&units=1&m1pr=1", "pill" if int(rent) != 1300 else "pill-on"),
        ("$1,650 metro", "/calculator?rent=1650&units=1&m1pr=1", "pill" if int(rent) != 1650 else "pill-on"),
        ("20-unit owner", "/calculator?rent=1450&units=20&m1pr=1", "pill" if units != 20 else "pill-on"),
        ("Claims ledger", "/claims", "link"),
    ]
    return page("Funding Braid Calculator", body, ctx, actions, "Calculator presets")


PRESENT_NOTES = {
    1: "Open with the single-sentence ask, then the two honesty badges: every figure is labeled verified or estimate, and nothing here is filed law yet.",
    2: "Anchor the problem in their numbers: filings and provider loss are verified; surety-debt framing is what the bill replaces.",
    3: "Title I is the self-funding core — deposits never touch the landlord, adjudication is neutral, and the 1% tenant floor is preserved.",
    4: "Drive the slider live. Base case $15.33/mo at $1,300 rent ≈ 1.18%; ask the room what number breaks it, then show fraud and recession legs.",
    5: "Title II is the assurance engine — hardship triggers are UI-standard verified events, coverage is bounded 2–6 months.",
    6: "Titles III–IV: belongings coverage plus governance — home agency, public registry, symmetric penalties, scheduled review.",
    7: "Q&A slide — pull up any clause code (P-1 … IV-5) and read the statute + plain text straight off the record.",
    8: "Close on the record, not the pitch: marks, requests, positions, and the change ledger are all public — that's the accountability story.",
}


def present(slide: int, clause_id: str | None, rent: float, ctx: dict,
            notes: bool = False) -> bytes:
    """Dedicated 8-slide 16:9 TV / Presentation briefing deck."""
    total_slides = 8
    s = max(1, min(total_slides, slide))
    meta = db.meta()
    braid = db.calculate_braid(rent, 1, True)
    all_clauses = db.clauses()
    counts = db.margin_counts()
    n_marks = sum(counts.values())
    n_reqs = db.open_request_count()

    if s == 1:
        stage_body = f"""
<p class="stage-kicker">Briefing Deck · Slide 1 of {total_slides} · {esc(meta['jurisdiction'])}</p>
<h1 class="stage-title">{esc(meta['short_title'])}</h1>
<p class="stage-thesis">{esc(meta['thesis'])}</p>
<div class="stage-metrics">
  <div><b>{len(all_clauses)}</b><span>Statutory clauses across Titles I–IV</span></div>
  <div><b>1.18%</b><span>Modeled base cost ($15.33/mo at $1,300 rent)</span></div>
  <div><b>0</b><span>Subrogation or clawback debt against tenants</span></div>
  <div><b>{n_marks}</b><span>Public docket marks read into the open record</span></div>
</div>"""
    elif s == 2:
        stage_body = f"""
<p class="stage-kicker">Slide 2 of {total_slides} · Empirical Problem Statement</p>
<h1 class="stage-title">Why the current deposit &amp; eviction cycle fails both sides</h1>
<div class="stage-grid2">
  <div class="stage-box">
    <p class="stage-big">23,282 – 25,847</p>
    <p><b>Annual Minnesota eviction filings</b> (MN Judicial Branch, 2023–2024).
    <b>44.6%</b> of filings concentrate in repeat/serial filings (Eviction Lab).</p>
  </div>
  <div class="stage-box">
    <p class="stage-big">$5,600 – $7,400</p>
    <p><b>Direct provider loss per completed eviction</b> (turnover, arrears, court &amp; vacancy —
    Harris County i4J benchmark).</p>
  </div>
  <div class="stage-box">
    <p class="stage-big">$9 Billion</p>
    <p><b>U.S. rental &amp; surety debt</b> flagged by CFPB: private “zero-deposit” bonds charge fees
    and still pursue renters through collection.</p>
  </div>
  <div class="stage-box">
    <p class="stage-big">Since 2007</p>
    <p><b>UK Tenancy Deposit Protection</b> has proven custodial escrow + free neutral adjudication
    works at national scale off pooled interest float.</p>
  </div>
</div>"""
    elif s == 3:
        stage_body = f"""
<p class="stage-kicker">Slide 3 of {total_slides} · Title I — Amends Minn. Stat. § 504B.178</p>
<h1 class="stage-title">Custodial Deposit Escrow &amp; Neutral Adjudication</h1>
<div class="stage-grid2">
  <div class="stage-box">
    <h3>I-1 · Neutral custody for the tenancy</h3>
    <p>Every security deposit enters bonded escrow at lease signing. Landlords never hold, commingle,
    or unilaterally deduct from deposits.</p>
  </div>
  <div class="stage-box">
    <h3>I-2 &amp; I-3 · Independent referee + free renter lane</h3>
    <p>Move-out claims are decided on photo/document evidence by an administrative adjudicator — neither
    the landlord nor the carrier decides.</p>
  </div>
  <div class="stage-box">
    <h3>I-5 · Statutory 1% + clean-year dividend</h3>
    <p>Tenants keep their guaranteed 1% annual interest plus a mutual surplus dividend after claims-free years.</p>
  </div>
  <div class="stage-box">
    <h3>I-8 · Self-funded via ~3% net float (~$23.4M/yr)</h3>
    <p>4% Treasury yield less 1% tenant interest yields ~$39/unit/yr (~$3.25/mo) to fund escrow and adjudication.</p>
  </div>
</div>"""
    elif s == 4:
        stage_body = f"""
<p class="stage-kicker">Slide 4 of {total_slides} · Title II — Three-Source Funding Braid</p>
<h1 class="stage-title">How Rent Assurance Is Paid For (Live Model)</h1>
<form method="get" action="/present" class="stage-calc-bar" id="braidForm">
  <input type="hidden" name="s" value="4">
  <label>Monthly rent:
    <input type="range" min="700" max="3000" step="50" value="{int(braid['monthly_rent'])}" id="rentRange">
    <input type="number" name="rent" id="rentInput" value="{int(braid['monthly_rent'])}" step="50" min="400" max="10000">
  </label>
  <input type="hidden" id="unitsInput" value="1">
  <input type="checkbox" id="m1prInput" checked hidden>
</form>
<div class="stage-metrics">
  <div><b id="valFloat">${braid['deposit_float_mo']:.2f}/mo</b><span>1. Custodial deposit float (3% net)</span></div>
  <div><b id="valRenter">${braid['renter_share_mo']:.2f}/mo</b><span>2. MN Renter's Credit monthly advance ($0 new OOP up to $77.5K income)</span></div>
  <div><b id="valLandlord">${braid['landlord_match_mo']:.2f}/mo</b><span>3. Landlord matched share (earns clean-book dividend)</span></div>
  <div><b id="valTotal">${braid['total_pool_mo']:.2f}/mo</b><span>Combined pool (~1.18% of rent · zero subrogation)</span></div>
</div>"""
    elif s == 5:
        d_cards = "".join(
            f'<div class="stage-box compact"><b>{d["num"]}. {esc(d["title"])}</b>'
            f'<p class="quiet">{esc(d["why"])} ({esc(d["clause"])})</p></div>'
            for d in db.decisions()
        )
        stage_body = f"""
<p class="stage-kicker">Slide 5 of {total_slides} · Fairness Axiom &amp; Structural Locks</p>
<h1 class="stage-title">Eight Non-Negotiable Safeguards</h1>
<div class="stage-grid4">{d_cards}</div>"""
    elif s == 6:
        stage_body = f"""
<p class="stage-kicker">Slide 6 of {total_slides} · Fiscal Discipline &amp; Rollout Sequence</p>
<h1 class="stage-title">Stress-Tested Numbers &amp; MHFA Pilot Path</h1>
<div class="stage-grid2">
  <div class="stage-box">
    <h3>Three modeled loss regimes (at $1,300 rent)</h3>
    <p><b>Base case (1.18%):</b> $15.33 / unit / mo (~$106M claims)</p>
    <p><b>+30% Fraud / hazard shock (1.63%):</b> $21.23 / unit / mo</p>
    <p><b>6% Recession default shock (2.31%):</b> $30.00 / unit / mo</p>
    <p class="quiet">Normal years build ~$4M/yr in dedicated reserves.</p>
  </div>
  <div class="stage-box">
    <h3>Clause II-6 &amp; IV-4 · Prove it first, sunset if it misses</h3>
    <p><b>Step 1:</b> MHFA operates Title II as a pilot on LIHTC subsidized properties using existing compliance rails.</p>
    <p><b>Step 2:</b> Audited pilot loss data forms the official fiscal note for statewide rollout.</p>
    <p><b>Step 3:</b> Mandatory Year-3 committee audit + hard 5-year statutory sunset.</p>
  </div>
</div>"""
    elif s == 7:
        foc = db.clause(clause_id or "I-4") or all_clauses[0]
        pills = "".join(
            f'<a class="stage-cpill{" on" if c["id"] == foc["id"] else ""}" '
            f'href="/present?s=7&c={esc(c["id"])}">{esc(c["id"])}</a>'
            for c in all_clauses
        )
        stage_body = f"""
<p class="stage-kicker">Slide 7 of {total_slides} · Live Clause Q&amp;A Browser</p>
<div class="stage-cpills">{pills}</div>
<div class="stage-box" style="margin-top:18px">
  <h2>{esc(foc['id'])} — {esc(foc['heading'])} {_status(foc['status'])}</h2>
  <p style="margin:12px 0">{esc(foc['statute_text'])}</p>
  <p class="plain"><b>In plain language:</b> {esc(foc['plain_text'] or '')}</p>
</div>"""
    else:
        recent_marks = db.marks(status="read_in")[-3:]
        m_list = "".join(
            f'<div class="stage-box compact">'
            f'<p class="mno"><b>{esc(m["public_no"])}</b> on <b>{esc(m["clause_id"] or "general")}</b> · {esc(m["author_label"] or ("a contributor" if m["change_id"] else "unsigned"))}</p>'
            f'<p>{esc(m["body"])}</p>'
            f'{"<p class=quiet><b>Answer:</b> " + esc(m["response_body"]) + "</p>" if m["response_body"] else ""}'
            f'</div>'
            for m in reversed(recent_marks)
        )
        stage_body = f"""
<p class="stage-kicker">Slide 8 of {total_slides} · Live Public Docket &amp; Next Steps</p>
<h1 class="stage-title">Open Ledger: {n_marks} Marks Read In · {n_reqs} Active Requests</h1>
<div class="stage-grid3">{m_list}</div>
<p class="stage-cta">Add a clause mark at <b>/mark</b> · Request a briefing or amendment at <b>/requests</b> · Inspect every source at <b>/claims</b>.</p>"""

    prev_s = max(1, s - 1)
    next_s = min(total_slides, s + 1)
    dots = [(f"{i}", f"/present?s={i}", "pill-on" if i == s else "pill")
            for i in range(1, total_slides + 1)]

    body = f"""
<article class="stage-slide" data-slide="{s}" data-total="{total_slides}">
  {stage_body}
  {f'<p class="speaker-notes"><b>Notes:</b> {esc(PRESENT_NOTES.get(s, ""))}</p>' if notes and PRESENT_NOTES.get(s) else ""}
  <nav class="stage-foot pnav" aria-label="Slide controls">
    <a class="pnav-btn" id="prevSlide" href="/present?s={prev_s}{"&notes=1" if notes else ""}">{'← Previous' if s > 1 else 'Start'}</a>
    <span class="quiet">Use ← / → arrow keys, 1–8, F for fullscreen, or Esc for Desk</span>
    <a class="pnav-btn" id="nextSlide" href="/present?s={next_s}{"&notes=1" if notes else ""}">{'Next slide →' if s < total_slides else 'Done'}</a>
  </nav>
</article>"""

    actions = [
        ("← Prev", f"/present?s={prev_s}", "link"),
        *dots,
        ("Next →", f"/present?s={next_s}{'&notes=1' if notes else ''}", "primary"),
        ("Notes off" if notes else "Speaker notes",
         f"/present?s={s}{'' if notes else '&notes=1'}", "link"),
        ("Exit to Desk", "/mode/desk?next=/", "link"),
    ]
    ctx_tv = dict(ctx)
    ctx_tv["mode"] = "tv"
    return page(f"Presentation ({s}/{total_slides})", body, ctx_tv, actions,
                "Stage controls", is_stage=True)


def mark_form_page(cid: str | None, re_no: str | None, quote: str | None,
                   kind_sel: str | None, ctx: dict) -> bytes:
    body = f"""
<header class="mast"><h1>The Inkwell</h1>
<p class="lede">Every mark is numbered, dated, and attached to a clause.
It lands in dark intake first — a steward reads it in, and only then does it
stand on the public ledger.</p></header>
<section class="markform">{_mark_form(cid, re_no, quote, kind_sel)}</section>"""
    return page("The Inkwell", body, ctx, [
        ("The draft", "/bill", "link"),
        ("The margin", "/margin", "link"),
        ("Requests", "/requests", "link"),
    ], "Inkwell actions")


def margin(posted: bool, ctx: dict) -> bytes:
    rows = db.marks(status="read_in")
    banner = (
        '<div class="notice-ok" role="status"><b>Received into intake.</b> '
        'Your mark stays dark until a steward reads it into the public ledger '
        'and assigns its M-number.</div>'
        if posted else ""
    )
    items = "".join(_mark_html(m, steward=ctx["steward"]) for m in rows) or (
        '<p class="quiet">The ledger is empty. Marks enter through the '
        'Inkwell and are read in from the intake queue.</p>')
    n = db.queue_count()
    body = f"""
{banner}
<header class="mast"><h1>The margin</h1>
<p class="lede">The public ledger — every mark read in, numbered and
dated, attached to its clause. Answers cite earlier marks by reference
(<i>re: M-0001</i>). The record does not erase; it amends in the open.</p></header>
{items}"""
    acts = [
        ("New mark", "/mark", "primary"),
        (f"Intake queue ({n})", "/intake", "pill-on" if (ctx["steward"] and n) else "link"),
        ("The draft", "/bill", "link"),
    ]
    return page("The Margin", body, ctx, acts, "Margin docket tools")


def intake(ctx: dict) -> bytes:
    n_queued = db.queue_count()
    held = db.marks(status="held")
    crisis = db.marks(status="crisis_routed")

    if not ctx["steward"]:
        nxt = urllib.parse.quote("/intake", safe="")
        unlock_href = f"/steward/toggle?next={nxt}" if ctx.get("onetap") else f"/steward?next={nxt}"
        body = f"""
<header class="mast"><h1>Intake queue (dark gate)</h1>
<p class="lede">Unscreened marks never display publicly — protecting against
accidental personal details, spam, and housing emergencies hitting a comment box.</p></header>
<section class="gate-box">
  <p><b>{n_queued}</b> mark(s) currently wait for steward read-in ·
  Held: {len(held)} · Crisis-routed: {len(crisis)}.</p>
  <p class="quiet">Unlock Steward mode to review queued items, write official
  Drafting Table answers, read marks into the public Margin, or crisis-route.</p>
  <p><a class="btn" href="{unlock_href}" style="display:inline-block;text-decoration:none">Unlock Steward triage</a></p>
</section>"""
        return page("Intake (Locked)", body, ctx, [
            ("Unlock Steward", unlock_href, "primary"),
            ("Public margin", "/margin", "link"),
            ("The draft", "/bill", "link"),
        ], "Intake gate")

    rows = db.marks(status="queued")
    items = "".join(f"""
<article class="mark intake">
  <p class="mno"><b>Intake #{m['id']}</b> · {esc(m['created_at'])} ·
    {KIND_WORDS.get(m['kind'], 'comment')} · {_clause_label(m['clause_id'])}
    {" · re: proposed change" if m["change_id"] else ""}
    {" · " + esc(m["author_label"]) if m["author_label"] else " · unsigned"}</p>
  {'<blockquote class="quote">“' + esc(m["quote_text"]) + '”</blockquote>' if m["quote_text"] else ""}
  {'<p class="proposed"><b>Proposed:</b> ' + esc(m["proposed_text"]) + '</p>' if m["proposed_text"] else ""}
  <p>{esc(m['body'])}</p>
  <form method="post" action="/api/mark_action" class="stack">
    <input type="hidden" name="id" value="{m['id']}">
    <input type="hidden" name="back" value="/intake">
    <div class="row">
      <label>Answer in the open <span class="quiet">(optional — publishes alongside mark)</span>
        <input name="response" placeholder="The drafting table's public answer."></label>
      <label>Responder role
        <input name="responder" value="Drafting Table"></label>
    </div>
    <div class="row">
      <label>Moderation note <span class="quiet">(public reason on redact/edit)</span>
        <input name="note" maxlength="500"></label>
      <label>Replacement text <span class="quiet">(Edit only)</span>
        <input name="new_body"></label>
    </div>
    <div class="acts">
      <button name="action" value="read_in" class="btn">Read in (assign M-number)</button>
      <button name="action" value="redact" class="btn ghost">Redact name/contact</button>
      <button name="action" value="edit" class="btn ghost">Edit text</button>
      <button name="action" value="held" class="btn ghost">Hold</button>
      <button name="action" value="crisis_routed" class="btn ghost">Crisis route</button>
    </div>
  </form>
</article>""" for m in rows) or (
        '<p class="quiet">The queue is empty — nothing waits for read-in.</p>')

    body = f"""
<header class="mast"><h1>Intake queue (Steward active)</h1>
<p class="lede">What lands here is dark until you read it in.
<b>Read in</b> assigns its permanent M-number. <b>Hold</b> sets it aside.
<b>Crisis route</b> counts it and keeps it off the public ledger.</p></header>
{items}
<p class="quiet">Held: {len(held)} · Crisis-routed: {len(crisis)}</p>"""
    return page("Intake", body, ctx, [
        ("Public margin", "/margin", "primary"),
        ("Requests desk", "/requests", "link"),
        ("Lock Steward", "/steward/lock?next=/intake", "pill"),
    ], "Steward triage tools")


def steward_page(nxt: str, err: bool, ctx: dict) -> bytes:
    err_html = ('<p class="notice-err" role="alert">Passcode did not match. '
                'Check BILL_STEWARD_CODE (default local code: <code>mn-steward</code>).</p>'
                if err else "")
    onetap = (
        f'<p class="quiet">Running locally on loopback: you can also use '
        f'<a href="/steward/toggle?next={urllib.parse.quote(nxt, safe="")}">1-tap local unlock</a>.</p>'
        if ctx.get("onetap") else ""
    )
    body = f"""
<header class="mast"><h1>Steward unlock</h1>
<p class="lede">Public readers browse, calculate, post marks, and file
requests with zero login. Steward mode unlocks intake read-in, official
answers, and request status updates.</p></header>
{err_html}
<form method="post" action="/api/steward" class="stack" style="max-width:26rem">
  <input type="hidden" name="next" value="{esc(nxt)}">
  <label>Steward passcode or personal steward code
    <input type="password" name="code" required autofocus placeholder="Passcode or your st- code"></label>
  <button class="btn" type="submit">Unlock Steward mode</button>
</form>
{onetap}"""
    return page("Steward Unlock", body, ctx, [
        ("Back", nxt, "link"),
        ("Desk", "/", "link"),
    ], "Steward authentication")


def requests_desk(clause_id: str | None, ctx: dict) -> bytes:
    rows = db.requests()

    def row(r):
        nxt = REQ_NEXT.get(r["status"])
        acts_html = ""
        if ctx["steward"]:
            acts = []
            if nxt:
                acts.append(
                    f'<button name="status" value="{nxt}" class="btn">'
                    f'Mark {STATUS_WORDS[nxt]}</button>')
            if r["status"] not in ("incorporated", "declined"):
                acts.append('<button name="status" value="declined" '
                            'class="btn ghost">Decline</button>')
            if acts:
                acts_html = (
                    f'<form method="post" action="/api/request_status" class="acts">'
                    f'<input type="hidden" name="id" value="{r["id"]}">'
                    f'<input name="note" placeholder="Optional steward note" class="inline-note">'
                    f'{"".join(acts)}</form>'
                )
        note = (f'<p class="quiet"><b>Steward note:</b> {esc(r["steward_note"])}</p>'
                if r["steward_note"] else "")
        org = f' · {esc(r["org_or_role"])}' if r["org_or_role"] else ""
        return f"""
<article class="req" id="{esc(r['public_no'])}">
  <p class="mno"><b>{esc(r['public_no'])}</b> · {esc(r['req_type'])} ·
    {_status(r['status'])} · {_status(r['stance'])}{org} ·
    {_clause_label(r['clause_id'])}</p>
  <p><b>{esc(r['summary'])}</b>
    {' — ' + esc(r['details']) if r['details'] else ''}</p>
  {note}
  {acts_html}
</article>"""

    items = "".join(row(r) for r in rows) or (
        '<p class="quiet">No requests yet — the desk is clear.</p>')
    options = ['<option value="">— whole bill / no specific clause —</option>'] + [
        f'<option value="{esc(c["id"])}"'
        f'{" selected" if c["id"] == clause_id else ""}>'
        f'{esc(c["id"])} — {esc(c["heading"])}</option>'
        for c in db.clauses()]
    steward_hint = (
        "" if ctx["steward"]
        else '<p class="quiet">Status updates require Steward mode (top right).</p>'
    )
    body = f"""
<header class="mast"><h1>Requests desk</h1>
<p class="lede">Briefings, statutory amendments, organizational positions, and
questions — tracked openly through <b>new → reviewing → scheduled →
incorporated</b>. Contact info stays private to stewards.</p>
{steward_hint}</header>
<section id="new" class="markform">
  <h2>Submit a request</h2>
  <form method="post" action="/api/request" class="stack">
    <div class="row">
      <label>Type<select name="req_type">
        <option value="briefing">Briefing / fiscal walkthrough</option>
        <option value="amendment">Statutory amendment</option>
        <option value="position">Organization position</option>
        <option value="question">Technical question</option>
        <option value="other">Other</option>
      </select></label>
      <label>Clause<select name="clause_id">{''.join(options)}</select></label>
    </div>
    <label>Who is asking<input name="org_or_role"
      placeholder="Office, organization, or role (e.g. Housing Committee Staff, 12-unit Owner)"></label>
    <label>One-line summary<input name="summary" required
      placeholder="One clear sentence — what is being requested?"></label>
    <label>Detail &amp; reasoning<textarea name="details" rows="3"
      placeholder="Optional — background, source citation, or timing window."></textarea></label>
    <label>Contact <span class="quiet">(steward-only — never rendered on the site)</span>
      <input name="contact" autocomplete="off" placeholder="Email or phone for scheduling"></label>
      <input name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
    <button class="btn" type="submit">Submit request</button>
  </form>
</section>
<section>
  <h2>Open &amp; historical requests ({len(rows)})</h2>
  {items}
</section>"""
    return page("Requests", body, ctx, [
        ("Submit request", "/requests#new", "primary"),
        ("Positions", "/positions", "link"),
        ("The draft", "/bill", "link"),
    ], "Requests desk tools")


def positions(ctx: dict) -> bytes:
    rows = db.positions()
    items = "".join(f"""
<article class="mark">
  <p class="mno"><b>{esc(p['person'])}</b> · {_status(p['stance'])} ·
    {esc(p['noted_at'])}{' · ' + esc(p['source']) if p['source'] else ''}</p>
  <p>{esc(p['provision'])}</p>
</article>""" for p in rows) or (
        '<p class="quiet">No positions recorded yet.</p>')
    body = f"""
<header class="mast"><h1>Who stands where</h1>
<p class="lede">Organization or office × provision × stance, dated and sourced.</p></header>
<section id="add" class="markform">
  <h2>Record a position</h2>
  <form method="post" action="/api/position" class="stack">
    <div class="row">
      <label>Who<input name="person" required
        placeholder="Organization, coalition, or office"></label>
      <label>Stance<select name="stance">
        <option value="support">Supports</option>
        <option value="oppose">Opposes</option>
        <option value="conditional">Conditional</option>
        <option value="neutral">Neutral</option>
        <option value="watching">Watching</option>
      </select></label>
    </div>
    <label>On what provision<input name="provision" required
      placeholder="e.g. Title I custodial escrow, Title II funding braid, or whole draft"></label>
    <label>Public source<input name="source"
      placeholder="Optional — letter, testimony, meeting date"></label>
    <button class="btn" type="submit">Record position</button>
  </form>
</section>
{items}"""
    return page("Positions", body, ctx, [
        ("Add position", "/positions#add", "primary"),
        ("Requests", "/requests", "link"),
        ("The draft", "/bill", "link"),
    ], "Positions ledger tools")


def claims(ctx: dict) -> bytes:
    rows = db.claims()
    items = "".join(f"""
<article class="mark" id="{esc(c['id'])}">
  <p class="mno"><b>{esc(c['id'])} · {esc(c['figure'])}</b> · {_status(c['status'])}
    {' · checked ' + esc(c['checked']) if c['checked'] else ''}</p>
  <p>{esc(c['claim'])}</p>
  <p class="quiet">{esc(c['source'] or 'internal derivation')}
    {' — ' + esc(c['derivation']) if c['derivation'] else ''}</p>
</article>""" for c in rows)
    body = f"""
<header class="mast"><h1>Claims &amp; verification ledger</h1>
<p class="lede">Every figure the platform cites, with its check status.
<b>Verified</b> means checked against a named statutory, court, or agency source.
<b>Estimate</b> means derived openly and awaiting formal actuarial sign-off.</p></header>
{items}"""
    return page("Claims", body, ctx, [
        ("Funding calculator", "/calculator", "primary"),
        ("The draft", "/bill", "link"),
        ("Locked decisions", "/decisions", "link"),
    ], "Verification tools")


def decisions(ctx: dict) -> bytes:
    items = "".join(f"""
<article class="mark">
  <p class="mno"><b>Decision {d['num']}</b> · {_clause_label(d['clause'])} ·
    <span class="st st-locked">locked</span></p>
  <p><b>{esc(d['title'])}</b>{' — ' + esc(d['why']) if d['why'] else ''}</p>
</article>""" for d in db.decisions())
    body = f"""
<header class="mast"><h1>Locked decisions</h1>
<p class="lede">The eight architectural safeguards that hold the draft together —
locked in public so any change must happen openly on the record.</p></header>
{items}"""
    return page("Decisions", body, ctx, [
        ("The draft", "/bill", "primary"),
        ("Claims", "/claims", "link"),
        ("Editions", "/editions", "link"),
    ], "Decision record tools")


def editions(ctx: dict) -> bytes:
    rows = db.editions()
    def _linked(e):
        chs = db.changes(edition=e["edition"])
        if not chs:
            return ""
        lis = "".join(
            f'<li><a href="/changes"><b>{esc(c["public_no"])}</b></a> '
            f'{_status(c["status"])} — {esc(c["proposed_text"] or c["note"] or "")}</li>'
            for c in chs)
        return f'<ul class="ev">{lis}</ul>'
    items = "".join(
        f'<article class="mark"><p class="mno"><b>{esc(e["edition"])}</b> · '
        f'{esc(e["date"])} · '
        f'{_clause_label(e["clause"]) if e["clause"] != "—" else "—"}</p>'
        f"<p>{esc(e['change'])}</p>{_linked(e)}</article>" for e in reversed(rows))
    body = f"""
<header class="mast"><h1>Editions</h1>
<p class="lede">The dated change ledger (E-01 through E-09), newest first.</p></header>
{items}"""
    return page("Editions", body, ctx, [
        ("The draft", "/bill", "primary"),
        ("The margin", "/margin", "link"),
        ("Decisions", "/decisions", "link"),
    ], "Change history tools")


def stewards_page(issued: str | None, ctx: dict) -> bytes:
    rows = db.stewards(active_only=True)
    retired = [] if not ctx["steward"] else db.stewards(active_only=False)
    retired = [r for r in retired if not r["active"]]
    cards = "".join(
        f'<article class="mark"><p class="mno"><b>{esc(r["name"])}</b>'
        + (f' · {esc(r["role"])}' if r["role"] else "")
        + f' · <span class="quiet">since {esc(r["added_at"])}</span></p>'
        + (f'<p>{esc(r["note"])}</p>' if r["note"] else "")
        + (f'<form method="post" action="/api/steward_roster" class="stack">'
           f'<input type="hidden" name="id" value="{r["id"]}">'
           f'<button name="roster_action" value="retire" class="ghost">'
           f'Retire from roster</button></form>' if ctx["steward"] else "")
        + '</article>' for r in rows)
    add_form = ""
    if ctx["steward"]:
        add_form = f"""
<details class="stack"><summary><b>Add a steward</b></summary>
<form method="post" action="/api/steward_roster" class="stack">
  <input type="hidden" name="roster_action" value="add">
  <div class="row"><input name="name" required placeholder="Name — published here with their consent" maxlength="120">
  <input name="role" placeholder="Role (e.g. intake, resolutions)" maxlength="120"></div>
  <input name="note" placeholder="Note (how chosen, scope)" maxlength="400">
  <div class="row"><button>Add to the committee</button></div>
</form></details>"""
        if retired:
            add_form += ('<p class="quiet"><b>Retired:</b> ' + ", ".join(
                f'{esc(r["name"])} ({esc(r["retired_at"] or "")}) '
                f'<form method="post" action="/api/steward_roster" '
                f'style="display:inline"><input type="hidden" name="id" '
                f'value="{r["id"]}"><button name="roster_action" '
                f'value="restore" class="ghost">restore</button></form>'
                for r in retired) + '</p>')
    issued_banner = ""
    if issued and ctx["steward"]:
        issued_banner = (
            '<div class="notice-ok" role="status"><b>Steward code issued.</b> '
            'Pass it to them now — it unlocks steward mode at '
            '<a href="/steward">/steward</a> and is shown only once: '
            f'<code>{esc(issued)}</code>. Retiring them from the roster '
            'revokes it.</div>')
    body = f"""
<header class="mast"><h1>The stewards</h1>
<p class="lede">The people who read intake into the public record, moderate
the boards, and resolve proposed changes to the bill's wording. <b>Only
steward names publish on this platform, and only with consent.</b>
While the platform gets rolling, stewards are chosen by the bill's authors —
the goal is a standing committee that owns resolutions together. Retired
stewards stay in the record, not erased.</p></header>
{issued_banner}
{add_form}
{cards or '<p class="quiet">The committee is forming — no stewards named yet.</p>'}"""
    return page("Stewards", body, ctx, [
        ("The draft", "/bill", "primary"),
        ("Changes", "/changes", "link"),
        ("The margin", "/margin", "link"),
        ("Requests", "/requests", "link"),
    ], "Stewards")


def _change_html(ch: dict, steward: bool = False,
                 sname: str | None = None) -> str:
    src = (f' · re: <b>{esc(ch["mark_no"])}</b>' if ch["mark_no"] else "")
    ed = (f' · edition <b>{esc(ch["edition"])}</b>' if ch["edition"] else "")
    by = (f' · resolved by <b>{esc(ch["resolved_by"])}</b>'
          if ch["resolved_by"] else "")
    diff = ""
    if ch["status"] == "incorporated" and (ch["old_text"] or ch["new_text"]):
        diff = ('<div class="ch-diff">'
                + (f'<p class="ch-old"><b>Was:</b> {esc(ch["old_text"])}</p>'
                   if ch["old_text"] else "")
                + (f'<p class="ch-new"><b>Now:</b> {esc(ch["new_text"])}</p>'
                   if ch["new_text"] else "") + '</div>')
    window = ""
    if ch["status"] == "proposed" and ch["closes_at"]:
        window = (f'<p class="quiet">Discussion open until '
                  f'<b>{esc(ch["closes_at"])}</b>.</p>')
    thread = ""
    if ch["status"] == "proposed":
        marks = db.marks_for_change(ch["id"])
        if marks:
            thread = ('<div class="ch-thread">'
                      + "".join(
                          f'<p class="mark-body">{esc(m["body"])}</p>'
                          f'<p class="quiet">a contributor · '
                          f'{esc(m["created_at"])}'
                          + (f' <span class="quiet">(edited by stewards'
                             + (f' — {esc(m["edit_note"])}' if m["edit_note"] else "")
                             + ')</span>' if m["edited_at"] else "")
                          + '</p>' for m in marks)
                      + '</div>')
        open_now = db.change_is_open(ch["id"])
        if open_now:
            thread += f"""
  <details class="stack"><summary><b>Weigh in on this proposal</b></summary>
  <form method="post" action="/api/mark" class="stack">
    <input type="hidden" name="change_id" value="{ch['id']}">
    <textarea name="body" rows="3" required
              placeholder="Support, concern, or alternative wording"></textarea>
    <div class="row"><input name="name" placeholder="Name (stewards only — never published here)" maxlength="120">
    <input name="contact" placeholder="Contact (steward-only, optional)" maxlength="120"></div>
    <p class="quiet">Names on change discussions never publish — only steward
    names appear on this record, with their consent.</p>
    <div class="row"><button>Send to the stewards</button></div>
  </form></details>"""
    acts = ""
    if steward and ch["status"] == "proposed":
        acts = f"""
  <form method="post" action="/api/change_status" class="stack">
    <input type="hidden" name="id" value="{ch['id']}">
    <div class="row"><input name="edition" placeholder="Edition ref (e.g. E-10)" maxlength="20">
    <input name="resolved_by" value="{esc(sname or '')}" placeholder="Your name (published — blank stays unnamed)" maxlength="120"></div>
    <input name="note" placeholder="Public reason — required, it is the record" maxlength="500" required>
    <textarea name="new_text" rows="2" placeholder="Statute text as incorporated (optional)"></textarea>
    <div class="row"><button name="action" value="incorporated">Incorporate</button>
    <button name="action" value="declined" class="ghost">Decline</button></div>
  </form>"""
    elif steward and ch["status"] == "incorporated":
        acts = f"""
  <form method="post" action="/api/change_status" class="stack">
    <input type="hidden" name="id" value="{ch['id']}">
    <div class="row"><input name="note" placeholder="Retraction note" maxlength="500">
    <button name="action" value="retracted" class="ghost">Retract</button></div>
  </form>"""
    return f"""
<article class="mark">
  <p class="mno"><b>{esc(ch['public_no'])}</b> {_status(ch['status'])} ·
    {_clause_label(ch['clause_id']) if ch['clause_id'] else 'whole draft'}{src}{ed} ·
    <span class="quiet">{esc(ch['resolved_at'] or ch['created_at'])}</span>{by}</p>
  {window}
  {thread}
  {'<blockquote class="quote">“' + esc(ch["quote_text"]) + '”</blockquote>' if ch["quote_text"] else ""}
  {'<p class="proposed"><b>Proposed:</b> ' + esc(ch["proposed_text"]) + '</p>' if ch["proposed_text"] else ""}
  {diff}
  {'<p class="quiet">' + esc(ch["note"]) + '</p>' if ch["note"] else ""}
  {acts}
</article>"""


def changes_page(status_filter: str | None, ctx: dict) -> bytes:
    status_filter = status_filter if status_filter in db.CHANGE_STATUSES else None
    rows = db.changes(status=status_filter)
    counts = db.change_counts()
    pills = ['<a class="tb-pill%s" href="/changes">All (%d)</a>'
             % ("-on" if not status_filter else "", sum(counts.values()))]
    for s in db.CHANGE_STATUSES:
        pills.append('<a class="tb-pill%s" href="/changes?s=%s">%s (%d)</a>'
                     % ("-on" if s == status_filter else "", s,
                        s.capitalize(), counts.get(s, 0)))
    pills_html = '<p class="tb-items" style="margin:4px 0 14px">' + "".join(pills) + "</p>"
    open_n = counts.get("proposed", 0)
    record_form = ""
    if ctx["steward"]:
        opts = "".join(
            f'<option value="{esc(c["id"])}">{esc(c["id"])} — {esc(c["heading"])}</option>'
            for c in db.clauses())
        record_form = f"""
<details class="stack"><summary><b>Record a proposed change</b> (steward)</summary>
<form method="post" action="/api/change" class="stack">
  <div class="row"><select name="clause_id"><option value="">— whole draft —</option>{opts}</select></div>
  <input name="quote_text" placeholder="Passage it targets (optional)">
  <textarea name="proposed_text" rows="3" required
            placeholder="Proposed wording"></textarea>
  <input name="note" placeholder="Source / note (e.g. R-0003, briefing)">
  <input name="closes_at" placeholder="Discussion open until (YYYY-MM-DD, optional)" maxlength="10">
  <div class="row"><button>Record CH</button></div>
</form></details>"""
    body = f"""
<header class="mast"><h1>Changes</h1>
<p class="lede">Every proposed and incorporated change on the record —
<b>{open_n}</b> open proposal(s), {counts.get("incorporated", 0)} incorporated,
{counts.get("declined", 0)} declined, {counts.get("retracted", 0)} retracted.
Open proposals take discussion marks below each card; when a steward resolves
one, the public reason is required and only steward names appear — with their
consent. The <a href="/stewards">steward roster</a> names who holds that
authority. Nothing is deleted, only resolved.
<b>Newest activity first.</b></p></header>
{pills_html}
{record_form}
{"".join(_change_html(ch, ctx["steward"],
                      ctx["steward_row"]["name"]
                      if ctx["steward_row"] else None)
         for ch in rows) or
 '<p class="quiet">No changes recorded yet.</p>'}"""
    return page("Changes", body, ctx, [
        ("The draft", "/bill", "primary"),
        ("The margin", "/margin", "link"),
        ("Editions", "/editions", "link"),
        ("Requests", "/requests", "link"),
    ], "Change ledger tools")


def search_page(term: str, ctx: dict) -> bytes:
    term = (term or "").strip()
    out = ""
    total = 0
    if term:
        res = db.search(term)
        total = sum(len(v) for v in res.values())
        groups = (
            ("Clauses", res["clauses"], lambda r:
             f'<a href="/clause/{esc(r["id"])}"><b>{esc(r["id"])}</b> — {esc(r["heading"])}</a> {_status(r["status"])}'),
            ("Margin", res["marks"], lambda r:
             f'<a href="/margin#{esc(r["public_no"])}"><b>{esc(r["public_no"])}</b></a> '
             f'{_clause_label(r["clause_id"])} — {esc((r["body"] or "")[:140])}'),
            ("Changes", res["changes"], lambda r:
             f'<a href="/changes"><b>{esc(r["public_no"])}</b></a> {_status(r["status"])} '
             f'{_clause_label(r["clause_id"])} — {esc((r["proposed_text"] or "")[:140])}'),
            ("Requests", res["requests"], lambda r:
             f'<a href="/requests"><b>{esc(r["public_no"])}</b></a> {_status(r["status"])} '
             f'— {esc(r["summary"][:140])}'),
            ("Editions", res["editions"], lambda r:
             f'<a href="/editions"><b>{esc(r["edition"])}</b></a> {esc(r["date"])} '
             f'— {esc(r["change"][:140])}'),
            ("Decisions", res["decisions"], lambda r:
             f'<a href="/decisions"><b>D-{r["num"]:02d}</b></a> — {esc(r["title"])}'),
            ("Signatures", res["signatures"], lambda r:
             f'<a href="/sign"><b>{esc(r["public_no"] or "S—")}</b></a> '
             f'— {esc(r["name"])}'
             f'{", " + esc(r["org_or_town"]) if r["org_or_town"] else ""}'),
        )
        for name, rows, render in groups:
            if rows:
                lis = "".join(f"<li>{render(r)}</li>" for r in rows)
                out += f'<section><h2>{name} ({len(rows)})</h2><ul class="ev">{lis}</ul></section>'
        if not total:
            out = '<p class="quiet">Nothing on the record matches that.</p>'
    body = f"""
<header class="mast"><h1>Search the record</h1>
<p class="lede">Clauses, margin marks, changes, requests, editions, and
locked decisions — one query.</p></header>
<form method="get" action="/search" class="stack">
  <input type="search" name="q" value="{esc(term)}" autofocus
         placeholder="Search the whole platform…" aria-label="Search">
  <div class="row"><button>Search</button></div>
</form>
{f'<p class="quiet">{total} result(s) for “{esc(term)}”.</p>' if term else ""}
{out}"""
    return page("Search", body, ctx, [
        ("The draft", "/bill", "primary"),
        ("The margin", "/margin", "link"),
        ("Changes", "/changes", "link"),
    ], "Search")


def track_page(code: str, new: str, ctx: dict) -> bytes:
    rec = db.by_receipt(code)
    banner = ""
    if new and code:
        kind = {"mark": "mark", "request": "request",
                "signature": "signature"}.get(new, "submission")
        banner = (f'<div class="notice-ok" role="status"><b>Received into intake.</b> '
                  f'Your private receipt code is <b class="rc">{esc(code)}</b> — '
                  f'save it. It is the only way to check your {kind}\'s '
                  f'status; it is never shown publicly.</div>')
    found = ""
    if code and rec:
        if rec["type"] == "mark":
            state = ("retracted" if rec["retracted_at"] else rec["status"])
            pub = (f' — public as <b>{esc(rec["public_no"])}</b> on the '
                   f'<a href="/margin#{esc(rec["public_no"])}">Margin</a>'
                   if rec["public_no"] else " — still in dark intake")
            found = (f'<article class="mark"><p class="mno"><b>Mark</b> '
                     f'{_status(state)}{_clause_label(rec["clause_id"]) if rec["clause_id"] else ""}</p>'
                     f'<p>{pub} · submitted {esc(rec["created_at"])}</p></article>')
        elif rec["type"] == "signature":
            pub = (f' — published as <b>{esc(rec["public_no"])}</b> in the '
                   f'<a href="/sign">signature book</a>'
                   if rec["public_no"] else " — awaiting steward publish")
            found = (f'<article class="mark"><p class="mno"><b>Signature</b> '
                     f'{_status(rec["status"])}</p>'
                     f'<p>{pub} · signed {esc(rec["created_at"])}</p></article>')
        else:
            found = (f'<article class="mark"><p class="mno"><b>Request</b> '
                     f'{_status(rec["status"])} · <b>{esc(rec["public_no"])}</b></p>'
                     f'<p>Type: {esc(rec["req_type"])} · updated {esc(rec["updated_at"])}</p></article>')
    elif code:
        found = '<p class="quiet">No record under that code.</p>'
    body = f"""
<header class="mast"><h1>Track a submission</h1>
<p class="lede">Marks and requests give you a private receipt code at
submission. Enter it to see the status — nothing else is exposed.</p></header>
{banner}
<form method="get" action="/track" class="stack">
  <input name="code" value="{esc(code)}" placeholder="Receipt code"
         aria-label="Receipt code">
  <div class="row"><button>Check status</button></div>
</form>
{found}"""
    return page("Track", body, ctx, [
        ("Mark the draft", "/mark", "primary"),
        ("Requests", "/requests", "link"),
        ("The margin", "/margin", "link"),
    ], "Track a submission")


TEACH_STOPS = [
    ("Why this bill exists", "P-1", "Open question: who holds your deposit today — and who decides when there's a fight?"),
    ("The words of the bill", "D-1", "Why does coverage attach to the lease, not a city license?"),
    ("Where the deposit goes", "I-1", "What actually changes at lease signing?"),
    ("Who decides disputes", "I-2", "Why can't the landlord — or the insurer — decide claims?"),
    ("When you're the one owed", "I-3", "What does a free counter-claim lane change for renters?"),
    ("A paid claim is final", "I-4", "Why does no-subrogation matter more than the payout?"),
    ("Rewards for clean years", "I-5", "Who earns the dividend, and where does the surplus come from?"),
    ("Checking the record", "I-6", "What could you look up about a building before you sign?"),
    ("Emergency rent coverage", "II-1", "Which hardships trigger the fund — and which don't?"),
    ("No debt cliff", "II-2", "What happens to a family the month after coverage ends?"),
    ("Who pays what", "II-3", "Trace the three funding legs — then test your own rent on the calculator."),
    ("Your belongings", "III-1", "What does belongings coverage add beyond the deposit?"),
    ("Who runs it", "IV-1", "Why a home agency instead of bolting it onto an existing one?"),
    ("Staying honest", "IV-5", "How does the public registry keep the system accountable?"),
]


def teach_page(ctx: dict) -> bytes:
    stops = []
    for i, (title, cid, prompt) in enumerate(TEACH_STOPS, 1):
        c = db.clause(cid)
        if not c:
            continue
        stops.append(f"""
<article class="mark teach-stop">
  <p class="mno"><b>Stop {i:02d}</b> · {_clause_label(cid)}</p>
  <h3><a href="/clause/{esc(cid)}">{esc(title)}</a></h3>
  <p class="plain"><b>Plain language:</b> {esc(c["plain_text"] or "")}</p>
  <p class="teach-prompt"><b>Talk about:</b> {esc(prompt)}</p>
</article>""")
    body = f"""
<header class="mast"><h1>Teach the bill</h1>
<p class="lede">A guided path through the draft for classrooms, tenant
meetings, and kitchen-table briefings — {len(stops)} stops, plain language
first, each with a discussion prompt. Pair with the
<a href="/tv">TV briefing deck</a> or have students follow along in
<a href="/bill?view=plain&lens=renter">plain-language view</a>.</p></header>
{"".join(stops)}"""
    return page("Teach", body, ctx, [
        ("Student view (plain)", "/bill?view=plain&lens=renter", "primary"),
        ("TV briefing deck", "/tv", "link"),
        ("Calculator", "/calculator", "link"),
        ("The margin", "/margin", "link"),
    ], "Teacher / student tools")


def _supporter_row(s, steward: bool) -> str:
    org = f'<span class="quiet">{esc(s["org"] or "")}</span>' if s["org"] else ""
    dist = f' · {esc(s["district"])}' if s["district"] else ""
    note = f'<p class="quiet">{esc(s["note"])}</p>' if s["note"] else ""
    move = ""
    if steward:
        nxt = {"target": "contacted", "contacted": "talks",
               "talks": "endorsed", "endorsed": "endorsed"}[s["stage"]]
        move = (f'<form method="post" action="/api/supporter" class="stack mact">'
                f'<input type="hidden" name="id" value="{s["id"]}">'
                f'<input name="note" placeholder="Note (optional)" maxlength="300">'
                f'<button name="stage" value="{nxt}" class="ghost">Move to {nxt}</button></form>'
                if s["stage"] != "endorsed" else "")
    return (f'<article class="mark"><p class="mno"><b>{esc(s["name"])}</b> '
            f'{_status(s["stage"])}{dist}</p>'
            f'<p>{esc(s["role"] or "")} {org}</p>{note}{move}</article>')


def campaign(ctx: dict) -> bytes:
    steps = db.journey()
    lane = "".join(
        f'<li><b>{esc(s["name"])}</b> {_status(s["state"])}'
        + (f' <span class="quiet">— {esc(s["note"])}</span>' if s["note"] else "")
        + "</li>" for s in steps)
    counts = db.supporter_counts()
    sup = db.supporters()
    groups = {}
    for s in sup:
        groups.setdefault(s["stage"], []).append(s)
    allies = ""
    for st, label in (("endorsed", "Endorsed"), ("talks", "In talks"),
                      ("contacted", "Contacted"), ("target", "Targets")):
        rows = groups.get(st, [])
        if rows:
            allies += (f'<h2>{label} ({len(rows)})</h2>'
                       + "".join(_supporter_row(s, ctx["steward"]) for s in rows))
    add_form = ""
    if ctx["steward"]:
        add_form = """
<details class="stack"><summary><b>Add an ally</b> (steward)</summary>
<form method="post" action="/api/supporter" class="stack">
  <div class="row"><input name="name" required placeholder="Name">
    <input name="org" placeholder="Organization"></div>
  <div class="row"><input name="role" placeholder="Role">
    <input name="district" placeholder="District / scope"></div>
  <div class="row"><select name="stage"><option value="target">target</option>
    <option value="contacted">contacted</option><option value="talks">talks</option>
    <option value="endorsed">endorsed</option></select>
    <input name="note" placeholder="Note"></div>
  <div class="row"><button>Add</button></div>
</form></details>"""
    mailto = ("mailto:?subject=" + urllib.parse.quote("MN Rent Assurance & Deposit Protection Act — read the working draft")
              + "&body=" + urllib.parse.quote(
                  "The working draft of the Minnesota Rent Assurance & Deposit "
                  "Protection Act — deposits in bonded custody, neutral "
                  "adjudication, hardship rent assurance, no subrogation.\n\n"
                  "Worth 20 minutes. I'm asking you to carry it in the 2027 "
                  "session."))
    body = f"""
<header class="mast"><h1>Carry the bill — 2027</h1>
<p class="lede">The campaign: get this draft actuarially verified, sponsored,
heard, and passed in the 2027 Minnesota session. <b>{counts.get("endorsed", 0)}</b>
endorsed · {counts.get("talks", 0)} in talks · {counts.get("contacted", 0)} contacted
· {counts.get("target", 0)} targets on the list.</p></header>

<section><h2>Where it stands</h2><ul class="how-steps">{lane}</ul></section>

<section><h2>The 2027 plan</h2>
<ol class="how-steps">
  <li><b>Verify the math.</b> Every <a href="/claims">estimate</a> needs
  actuarial sign-off — the credibility gate everything else compounds on.</li>
  <li><b>Build the coalition.</b> The targets below become contacted, then
  talks, then endorsed — tracked in the open.</li>
  <li><b>Collect testimony.</b> Marks on the <a href="/margin">Margin</a>
  become the <a href="/packet">testimony packet</a> committees actually read.</li>
  <li><b>File in January.</b> Revisor draft, chief authors in both chambers,
  housing committee hearings.</li>
  <li><b>Fallback is built in.</b> Title IV-1 already allows an MHFA pilot on
  LIHTC properties — fund the pilot if the full bill stalls.</li>
</ol></section>

<section><h2>Do one thing</h2>
<ul class="ev">
  <li><a href="/sign"><b>Sign the bill</b></a> — the voluntary signature
  book; your name publishes only when a steward reads it in.</li>
  <li><a href="/mark"><b>Mark the draft</b></a> — your name never publishes
  without read-in; your words can reach a hearing.</li>
  <li><a href="/requests"><b>Request a briefing or take a position</b></a> —
  orgs get worked through the requests desk.</li>
  <li><a href="{mailto}"><b>Send the draft to your legislator</b></a> —
  opens your mail with the ask pre-written.</li>
  <li><a href="/teach"><b>Teach it</b></a> — 14-stop guided path for
  meetings and classrooms.</li>
  <li><a href="/packet"><b>Print the testimony packet</b></a> — every
  read-in mark, grouped by clause.</li>
</ul></section>

<section><h2>The allies ledger</h2>
{add_form}
{allies or '<p class="quiet">The ledger is being built.</p>'}
</section>"""
    return page("Campaign", body, ctx, [
        ("Send to a legislator", mailto, "primary"),
        ("Mark the draft", "/mark", "link"),
        ("Testimony packet", "/packet", "link"),
        ("Teach it", "/teach", "link"),
    ], "Campaign tools")


def sign_page(ctx: dict) -> bytes:
    """The voluntary signature book — like a visitor's book at a town
    hall. Signing is opt-in, lands dark, and only the consented fields
    (name, org/town, note) publish when a steward reads it in. The
    optional email never renders — it is the OAuth-storage seam."""
    published = db.signatures(status="published")
    pending = db.signatures(status="queued") if ctx["steward"] else []
    rows = []
    for s in published:
        who = f'<b>{esc(s["name"])}</b>'
        if s["org_or_town"]:
            who += f' <span class="quiet">— {esc(s["org_or_town"])}</span>'
        line = f'<p class="quiet">{esc(s["note"])}</p>' if s["note"] else ""
        rows.append(f'<li>{who} <span class="quiet">· {esc(s["public_no"] or "")}'
                    f' · {esc((s["published_at"] or s["created_at"])[:10])}'
                    f'</span>{line}</li>')
    book = (f'<ul class="ev">{"".join(rows)}</ul>' if rows else
            '<p class="quiet">The book is open — the first names publish '
            'here once a steward reads them in.</p>')
    pend = ""
    if ctx["steward"] and pending:
        items = []
        for s in pending:
            items.append(f"""
<li><b>{esc(s["name"])}</b>{(", " + esc(s["org_or_town"])) if s["org_or_town"] else ""}
  <span class="quiet">· {esc(s["created_at"][:10])}</span>
  {f'<br><span class="quiet">{esc(s["note"])}</span>' if s["note"] else ""}
  <form method="post" action="/api/sign_action" class="acts">
    <input type="hidden" name="id" value="{s["id"]}">
    <button class="btn" name="action" value="published">Publish</button>
    <button class="btn ghost" name="action" value="held">Hold</button>
  </form></li>""")
        pend = (f'<section><h2>Awaiting publish ({len(pending)})</h2>'
                f'<ul class="ev">{"".join(items)}</ul></section>')
    body = f"""
<header class="mast"><h1>Sign the bill</h1>
<p class="lede">A voluntary signature book — like the visitor's book at a
town hall. Signing says: <i>I stand behind the Minnesota Rent Assurance
&amp; Deposit Protection Act.</i> Nothing is required but your name; it
publishes only after a steward reads it in. The book can be printed and
carried to a hearing.</p></header>
<section><h2>Add your name</h2>
<form method="post" action="/api/sign" class="stack">
  <label>Your name <input name="name" required autocomplete="name"
    placeholder="As you want it published — e.g. A. Renter, St. Paul"></label>
  <div class="row">
    <label>Org or town <span class="quiet">(optional — published)</span>
      <input name="org" placeholder="e.g. Frogtown, HOME Line"></label>
    <label>Email <span class="quiet">(optional — never published)</span>
      <input name="email" type="email" autocomplete="email"></label>
  </div>
  <label>A line for the record <span class="quiet">(optional — published)</span>
    <input name="note" maxlength="200"
      placeholder="e.g. My deposit should be working for me, not sitting in someone's drawer."></label>
  <input name="website" class="hp" tabindex="-1" autocomplete="off" aria-hidden="true">
  <label class="consent"><input type="checkbox" name="consent" value="yes"
    required> Publish my name — I understand my name, org/town, and line
    will appear publicly when a steward reads this in. Email is never
    published.</label>
  <button class="btn" type="submit">Sign the book</button>
</form></section>
<section><h2>The book ({len(published)})</h2>{book}</section>
{pend}"""
    return page("Sign the Bill", body, ctx, [
        ("Mark the draft", "/mark", "primary"),
        ("Campaign", "/campaign", "link"),
        ("The margin", "/margin", "link"),
    ], "Sign the bill")


def help_page(ctx: dict) -> bytes:
    """Public help directory — crisis lines and free public services.
    Official channels only; no advertising, no endorsements. Numbers
    verified against official listings as of Nov 2026 — re-verify on the
    service's official site before relying on any line."""
    body = """
<header class="mast"><h1>Help lines</h1>
<p class="lede">If the bill questions brought up something heavier — you're
not alone, and these are free, public help lines. Every entry is an
official public channel. Nothing here is an advertisement and nobody
paid to be listed.</p></header>

<section><h2>Right now</h2>
<ul class="ev">
  <li><b>Emergency — 911</b></li>
  <li><b>Suicide &amp; Crisis Lifeline — call or text 988</b>
  · 24/7, free, confidential. Veterans press 1.</li>
  <li><b>Crisis Text Line — text HOME to 741741</b></li>
  <li><b>Poison Control — 1-800-222-1222</b></li>
</ul></section>

<section><h2>Housing</h2>
<ul class="ev">
  <li><b>HOME Line — 612-728-5767</b> · free legal help for Minnesota
  renters — deposits, evictions, repairs, notices.</li>
  <li><b>United Way 211 — dial 2-1-1</b> · statewide referrals for
  shelter, rent help, utilities, food.</li>
  <li><b>Minnesota Food HelpLine — 1-888-711-1151</b> · food shelves and
  SNAP help.</li>
</ul></section>

<section><h2>Mental health &amp; addiction</h2>
<ul class="ev">
  <li><b>SAMHSA National Helpline — 1-800-662-4357</b> · 24/7 free,
  confidential treatment referral for substance use and mental health.</li>
  <li><b>Alcoholics Anonymous</b> · local meetings — aa.org</li>
  <li><b>Narcotics Anonymous</b> · local meetings — na.org</li>
  <li><b>Al-Anon</b> · for family &amp; friends of drinkers — al-anon.org</li>
  <li><b>Minnesota Problem Gambling Helpline — 1-800-333-4673</b>
  (1-800-333-HOPE) · free, confidential, 24/7.</li>
  <li><b>Gamblers Anonymous</b> · local meetings — gamblersanonymous.org</li>
  <li><b>Debtors Anonymous</b> · local meetings — debtorsanonymous.org</li>
</ul></section>

<section><h2>Safety &amp; legal</h2>
<ul class="ev">
  <li><b>MN Day One Crisis Line — 1-866-223-1111</b> · domestic violence
  help, statewide, 24/7.</li>
  <li><b>National Domestic Violence Hotline — 1-800-799-7233</b></li>
  <li><b>LawHelpMN.org</b> · free legal-aid directory for Minnesota.</li>
</ul></section>

<section><h2>A note</h2>
<p>These are public services run by their own organizations — listing a
line is information, not an endorsement, and Semptify receives nothing
for it. Phone numbers change; the service's official site is the
authority. This page is information only, not advice.</p>
<p>If you came here about the bill itself, the desk is at
<a href="/mark">/mark</a> — and your mark stays private until a steward
reads it in.</p></section>"""
    return page("Help lines", body, ctx, [
        ("Mark the draft", "/mark", "primary"),
        ("Home", "/", "link"),
        ("Legal", "/legal", "link"),
    ], "Help")


def legal_page(ctx: dict) -> bytes:
    body = """
<header class="mast"><h1>Legal</h1>
<p class="lede">The fine print, kept readable — privacy, terms, and
license for this platform. The bill is a <b>working draft</b>: nothing
here is filed law, and nothing here is legal advice.</p></header>

<section id="privacy"><h2>Privacy</h2>
<p><b>What we store.</b> Only what you choose to submit: the text of marks
and requests, and — if you opt in — a name, contact, or email. Signing
the <a href="/sign">signature book</a> stores what you typed; your name,
org/town, and line publish only after a steward reads them in. Email and
contact fields are never rendered publicly.</p>
<p><b>Receipts.</b> Each submission returns a private code for status
checks. It reveals status only — never your contact or full text.</p>
<p><b>Cookies.</b> Two functional cookies, no tracking: <code>bp_mode</code>
(your screen-mode choice) and <code>bp_steward</code> (steward session).
No analytics, no ads, no third-party trackers — there is nothing to
opt out of.</p>
<p><b>Rate limiting.</b> Submission counts are kept per IP in memory only;
nothing is written to the database about your IP.</p>
<p><b>Where it lives.</b> Records sit in a database on the hosting service
and replicate to project cloud storage for backup. Stewards can export
the full record for safekeeping. To ask for a correction or removal,
leave a steward note through <a href="/requests">Requests</a>.</p>
</section>

<section id="terms"><h2>Terms</h2>
<ul class="ev">
  <li>This platform presents a <b>draft bill</b> for public reading,
  comment, and campaign coordination. It is not enacted law and confers
  no rights or obligations.</li>
  <li>Submissions are reviewed by people before anything publishes. The
  stewards may hold, decline, or retract material — the record of that
  decision stays visible.</li>
  <li>Don't submit other people's personal information. Yours is your
  choice; theirs is not.</li>
  <li>No abusive, deceptive, or commercial content. This space carries
  no advertising and promotes no product or service.</li>
  <li>Nothing here is legal advice. If you have a live housing problem,
  the <a href="/help">help lines</a> are the right door.</li>
</ul></section>

<section id="license"><h2>License</h2>
<p><b>Content.</b> The bill text, plain-language explanations, and page
content are dedicated to the <b>public domain (CC0 1.0)</b> — take them,
use them, carry them. A bill belongs to the public.</p>
<p><b>Code.</b> The platform source is released under the
<b>MIT License</b>.</p>
<p><b>Marks and signatures.</b> By submitting, you agree your words (and
for signatures, the name you consent to publish) may be read into the
public record. Retraction stays on the record rather than erasing it —
that's what makes the ledger honest.</p>
</section>"""
    return page("Legal", body, ctx, [
        ("Help lines", "/help", "primary"),
        ("Sign the bill", "/sign", "link"),
        ("Home", "/", "link"),
    ], "Legal")


# ---------- mirror content pages (one source, two UIs) ----------
# site-src/pages/*.html is the SAME source the static mirror builds
# from — the platform renders it inside platform chrome, the Worker
# serves it inside northstar chrome. Edit the fragment once; both
# faces change.

CONTENT_PAGES = {
    "research": "The numbers & sources",
    "precedents": "Where others tried",
    "history": "Bill history",
    "providers": "For housing providers",
    "brief": "The brief",
    "classroom": "Classroom",
    "press": "Press",
    "myths": "Myths & straight answers",
    "what-the-bill-changes": "What the bill changes",
}

# Mirror-space links → platform-space routes
_LINK_MAP = {
    "/bill/live": "/bill",
    "/your-voice": "/mark",
    "/contact": "/requests",
    "/donate": "/campaign",
}

_HISTORY_NOTE = (
    '<p class="quiet">The live change record is the platform ledger — '
    'see <a href="/editions">Editions</a> and '
    '<a href="/changes">Changes</a>. The published commit history is '
    'mirrored on the static site build.</p>')


def content_page(slug: str, ctx: dict) -> bytes | None:
    """Serve a mirror page fragment inside platform chrome."""
    p = HERE / "site-src" / "pages" / f"{slug}.html"
    if not p.is_file():
        return None
    text = p.read_text(encoding="utf-8")
    m = re.match(r"\s*<!--(.*?)-->", text, re.S)
    meta, body = {}, text
    if m:
        for line in m.group(1).strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = text[m.end():].strip()
    body = body.replace("{{BILL_HISTORY}}", _HISTORY_NOTE)
    body = body.replace("{{BILL_DRAFT}}", "").replace("{{BILL_STATUTE}}", "")
    for old, new in _LINK_MAP.items():
        body = body.replace(f'href="{old}"', f'href="{new}"')
    title = CONTENT_PAGES.get(slug, meta.get("title", slug).replace("&amp;", "&"))
    return page(title, body, ctx, [
        ("The draft", "/bill", "primary"),
        ("Mark it", "/mark", "link"),
        ("Home", "/", "link"),
    ], meta.get("desc", "").replace("&amp;", "&"))


def packet(ctx: dict) -> bytes:
    """Printable testimony packet — read-in marks grouped by clause."""
    rows = db.marks(status="read_in")
    n_ret = sum(1 for r in rows if r["retracted_at"])
    live = [r for r in rows if not r["retracted_at"]]
    by_clause: dict[str, list] = {}
    for m in live:
        by_clause.setdefault(m["clause_id"] or "general", []).append(m)
    blocks = []
    for c in db.clauses():
        marks = by_clause.pop(c["id"], [])
        if not marks:
            continue
        entries = "".join(
            f'<article class="mark"><p class="mno"><b>{esc(m["public_no"])}</b> · '
            f'{esc(m["read_in_at"] or m["created_at"])} · '
            f'{KIND_WORDS.get(m["kind"], "comment")}</p>'
            f'<p>{esc(m["body"])}</p>'
            + (f'<p class="response"><b>{esc(m["responder_role"] or "Drafting Table")}:</b> '
               f'{esc(m["response_body"])}</p>' if m["response_body"] else "")
            + "</article>" for m in marks)
        blocks.append(f'<h2 class="title-head">{esc(c["id"])} — {esc(c["heading"])}'
                      f' <span class="quiet">({len(marks)})</span></h2>{entries}')
    general = by_clause.pop("general", [])
    if general:
        entries = "".join(
            f'<article class="mark"><p class="mno"><b>{esc(m["public_no"])}</b> · '
            f'{esc(m["read_in_at"] or m["created_at"])}</p><p>{esc(m["body"])}</p></article>'
            for m in general)
        blocks.append(f'<h2 class="title-head">General marks ({len(general)})</h2>{entries}')
    body = f"""
<header class="mast"><h1>Testimony packet</h1>
<p class="lede">{len(live)} read-in marks grouped by clause
{f' · {n_ret} retracted (kept on record)' if n_ret else ""}.
Print or save as PDF — this is what goes in a committee folder.</p></header>
{"".join(blocks) or '<p class="quiet">No marks read in yet.</p>'}"""
    return page("Testimony Packet", body, ctx, [
        ("Mark the draft", "/mark", "primary"),
        ("The margin", "/margin", "link"),
        ("Campaign", "/campaign", "link"),
    ], "Testimony packet")


def not_found(ctx: dict) -> bytes:
    body = ('<header class="mast"><h1>Not found</h1>'
            '<p class="lede">That route is not part of this platform.</p></header>')
    return page("Not found", body, ctx, [("Desk", "/", "primary")])
