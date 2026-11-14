# Bill Platform — standalone minimalist micro-repo

A self-contained local working platform for the **Minnesota Rent
Assurance & Deposit Protection Act** (Turnbuchalla). One Python file
serves the whole thing; SQLite holds the boards. No dependencies, no
accounts, no network calls — loopback only.

```powershell
python server.py          # → http://127.0.0.1:8093/
python selfcheck.py       # → full route + write-path verification
```

Port **8093** is registered in `C:\master-repo\PORTS.md`.

## What it is

| Surface | What it does |
|---|---|
| `/` — Desk | Reading spine: objective → where it stands → next action → evidence; campaign pipeline (journey stages) and bill pillars. |
| `/bill` | The whole draft, five titles, 23 clauses — statute text plus a plain-language line each. `+` opens a mark; `(n)` shows read-in marks per clause. |
| `/clause/<id>` | Clause focus: text, plain language, audience notes (renter / provider / lawmaker), the claims it stands on, its margin, prev/next. |
| `/mark` | The Inkwell — marks land in **intake**, never public by construction. Kinds: comment / question / proposed edit. |
| `/intake` | Triage queue: read in (issues M-0001…, optional drafter answer published with it), hold, or crisis-route. |
| `/margin` | The public ledger — read-in marks only, numbered and dated, answers cite by reference (`re: M-0001`). |
| `/requests` | Requests desk — briefings/amendments/positions/questions through `new → reviewing → scheduled → incorporated` (or declined, on the record). |
| `/positions` | Who stands where — person × provision × stance, dated. |
| `/claims` | Claims ledger — every figure the campaign says out loud, verified or derivation shown. |
| `/decisions` | Locked decisions — the eight design calls that hold the draft up. |
| `/editions` | The change ledger (seeded E-01…E-09 from the canonical register). |
| `/api/state` | JSON snapshot of every board (for tooling). |

## Three screen modes

`?mode` links in the top bar switch and persist via cookie:

- **Desk** — default working density.
- **TV** — presentation scale (~26px base), `←`/`→` walk clause
  neighbours on a clause page, `T` returns to desk.
- **Mobile** — stacked single column, large touch targets.

The client also *suggests* a mode on first visit (narrow → mobile, very
wide → TV) until you pick one yourself.

## Context-aware smart toolbar

The bar under the brand changes with what you're looking at: the bill
offers *Mark the draft / The margin / Claims / Present*; a clause offers
*Mark \<id\> / Request on \<id\>* plus its margin and the draft; the
margin and intake offer each other's counts; the requests desk and
positions offer their add-forms. Selecting bill text in the browser adds
a **Mark selection** action that prefills clause + quote.

## The board model (SQLite)

Marks follow the docket model from
`COMMUNITY_BOARD_DESIGN_2026-11-06.md`: intake is **dark** — a person
reads each mark in, which is when it gets its public number; an answer
typed at read-in enters the record beside the mark ("Drafting Table").
Held stays dark; crisis-routed stays dark and is counted. Contact info
is stored intake-only and never rendered.

## Canon

`seed_data.py` is the curated campaign seed — bill meta, journey
stages, five titles, 23 clauses (statute text + plain language +
audience notes + claim refs), claims ledger, locked decisions, seed
marks and requests. `seed/clauses.json` is the extraction snapshot from
the marker-locked BILLDOC block of the canonical read-through at
`modules/app-semptify-fastapi/app/static/turnbuchalla/index.html`
(regenerate with `python seed/extract_clauses.py`). Editions seed comes
from the case-side `registers/editions.jsonl`. Canon stays upstream —
this platform is a working surface, not a second source of truth.
