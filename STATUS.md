# Bill Platform — Status (2026-11-14)

**What this is:** standalone micro-repo presenting the Minnesota Rent
Assurance & Deposit Protection Act as a living, working document — real
SQLite-backed mechanics, not a mockup. Independent of the Semptify app
and the static mirror (`semptify-bill-mirror`).

**Run it:** `python server.py` → `http://127.0.0.1:8093/` (port 8093,
loopback). Python 3.11 stdlib only — zero dependencies, zero install.
DB: `data/platform.db` (auto-seeds on first run).

**Verified state:** `python selfcheck.py` → **SELFCHECK PASS, 91 checks**
— every route, every write path, steward gating, sanitization, 3 screen
modes, calculator, change ledger, campaign, receipts, rate limit.

---

## Routes

| Route | What |
|---|---|
| `/` | Index: intro, how-it-works, living-document badge, Semptify footer |
| `/desk` | Working desk: spine, objective, pipeline, last event |
| `/bill` | 23 clauses, statute + plain language, audience lenses |
| `/clause/<id>` | Clause page: notes, sources, margin, change history, mailto-legislator |
| `/mark` | Inkwell — public submission (no login), lands dark |
| `/margin` | Public ledger of read-in marks, permalinks `#M-xxxx` |
| `/intake` | Steward-gated dark queue |
| `/changes` | Chronological change ledger: proposed→incorporated/declined/retracted, Was/Now diffs |
| `/requests` | Briefings/amendments/positions/questions pipeline |
| `/positions` | Who-stands-where ledger |
| `/claims` | Figures marked verified/estimate with sources |
| `/decisions` | Locked design decisions |
| `/editions` | Dated editions E-01–E-09 + linked CH records |
| `/calculator` | Live 3-source funding braid, shareable `?rent&units&m1pr` URLs |
| `/present` `/tv` | 8-slide 16:9 TV deck; `?notes=1` shows speaker notes |
| `/search` | One query across the whole record |
| `/teach` | 14-stop guided path (classrooms, tenant meetings) |
| `/track` | Private receipt-code status lookup |
| `/campaign` | 2027 push: plan, one-thing actions, allies ledger |
| `/packet` | Printable testimony packet — marks grouped by clause |
| `/api/state` | Sanitized public JSON (contacts/receipts stripped) |
| `/api/export` | Steward-only full JSON backup incl. dark intake |

## Mechanics that work

- **Marks:** public → dark intake → steward `read_in` (gets M-number,
  optional official answer) | `held` | `crisis_routed` | `retract`
  (stays visible, struck). Edit-kind marks auto-record a CH- change.
- **Changes:** CH-numbers, statuses, edition links, source-mark links,
  chronological log + status pills at `/changes?s=…`.
- **Requests:** R-numbers, new→reviewing→scheduled→incorporated|declined.
- **Receipts:** every submission returns a code → `/track` shows status
  only. Contacts never render publicly; receipts never render at all.
- **Steward:** toggle on loopback or `BILL_STEWARD_CODE` passcode; 403s
  enforced on intake triage, changes, supporters, export.
- **Anti-spam:** honeypot field + 12 posts/5min per IP → 429.
- **Modes:** Auto (default, live viewport follow) · Desktop · TV ·
  Mobile — manual picks pin until Auto is re-chosen.

## Campaign state

`/campaign` allies ledger: **Amy Klobuchar — endorsed**; 14 targets
(HOME Line, HJC, IX, CTUL, LSAP, SMRLS, ISAIAH, JCA, MCH, SEIU, MHA,
MHFA, SFM, Eviction Lab). Stewards advance stages from the page.
Plan: actuarial verify → coalition → testimony via margin → file Jan
2027 → MHFA pilot fallback (IV-1).

## Open items (not blockers)

- Incorporate doesn't yet apply new text to the draft (manual today).
- No multilingual (Spanish/Somali/Hmong plain text is the first).
- Not publicly reachable — loopback only; deploy needs
  `BILL_STEWARD_CODE` + a tunnel/host or snapshot export to the mirror.
- No git remote yet (local repo, 12 commits on `main`).

## Files

`server.py` routes · `db.py` schema+seed+queries · `views.py` all HTML ·
`static/platform.css` one stylesheet, 3 modes · `static/platform.js`
mode-follow + selection toolbar + braid + TV keys · `selfcheck.py` the
harness · `seed/` canon · `CHANGELOG.md` plain-language history ·
`AGENTS.md` repo rules.
