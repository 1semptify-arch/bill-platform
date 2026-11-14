# Bill Platform — standalone minimalist micro-repo

Self-contained local platform for presenting and working the **Minnesota
Rent Assurance & Deposit Protection Act** (Turnbuchalla). Built in pure
Python 3.11 standard library + SQLite (`data/platform.db`) with zero
external runtime dependencies and zero coupling to the Semptify app's CSS
or build gates.

```powershell
python server.py          # -> http://127.0.0.1:8093/
python selfcheck.py       # -> end-to-end verification suite
```

Port **8093** is registered in `C:\master-repo\PORTS.md`.

## Surfaces & Working Mechanics

| Route | Purpose |
|---|---|
| `/` — Desk | Reading spine (`Objective` -> `Where it stands` -> `Next action`), 3 core mechanics summary, 6-step legislative pipeline, and evidence index. |
| `/bill` | Full 23-clause statutory draft across Preamble + Titles I–IV, with **Audience Lenses** (`All`, `Renter`, `Provider`, `Lawmaker`), **Plain-English / Statute** view toggle, `+` clause marks, and `(n)` live margin counts. |
| `/clause/<id>` | Focused clause view: statutory text, plain-language meaning, audience notes, linked claims/sources, prev/next neighbours, and clause margin. |
| `/calculator` | Interactive **Three-Source Funding Braid & Stress-Test** (`Deposit Float` + `M1PR Advance` + `Landlord Match` vs. eviction cost, plus Base / `+30%` Fraud / `6%` Recession stress scenarios). |
| `/present` (`/tv`) | Dedicated **8-slide 16:9 TV / Presentation Stage** for committee briefings, screenshares, and living-room TVs (`←`/`→`/`Space`, `1`–`8`, `F` fullscreen, `Esc` exit), including a live interactive funding slider on Slide 4 and live clause browser on Slide 7. |
| `/mark` | The Inkwell — public submission form for comments, questions, and proposed clause edits (zero login; lands in dark intake). |
| `/margin` | Public docket ledger — numbered (`M-0001`…), dated marks read into the record, with official Drafting Table answers and citation replies (`re: M-0001`). |
| `/intake` | **Steward-gated** triage queue: `Read in` (assigns M-number + optional public answer), `Hold`, or `Crisis route` (keeps personal emergencies off the public board; HOME Line `612-728-5767` displayed on form). |
| `/requests` | Working Requests Desk (`briefing`, `amendment`, `position`, `question`) tracked through `new -> reviewing -> scheduled -> incorporated | declined`. |
| `/positions` | Public ledger of organizational and office stances (`person x provision x stance`, dated). |
| `/claims` | Verification ledger (`C-01`…`C-12`) separating `verified` statutory/agency figures from `estimate` derivations awaiting actuarial review. |
| `/decisions` | The 8 locked non-negotiable safeguards (`No subrogation`, `Independent adjudication`, `Symmetric fraud penalties`, `5-year sunset`, etc.). |
| `/editions` | Dated change history (`E-01` through `E-09`). |

## Three Distinct Screen Modes

Switchable at any time in the top bar (persisted via `bp_mode` cookie) and
auto-suggested on first visit by viewport width:

1. **Desktop (`mode-desk`)** — 2-column minimalist workspace with a sticky
   left architectural index rail (`220px`), sticky Context-Aware Smart
   Toolbar, and crisp editorial reading spine (`18px` base).
2. **TV / Presentation (`mode-tv` + `/present`)** — Full-bleed widescreen
   16:9 briefing stage (`23px`–`44px` room-legible scale, side rail hidden,
   keyboard/remote D-pad navigation).
3. **Mobile / Tablet (`mode-mobile`)** — Fixed thumb-zone 5-tab bottom
   navigation bar (`Desk`, `Bill`, `Braid`, `Margin`, `Requests`), single-column
   touch targets, and centered `480px` device preview when toggled on desktop.

## Context-Aware Smart Toolbar & Steward Gate

- **Route-aware tools**: The sticky toolbar swaps its primary and secondary
  controls for each surface (Audience Lenses & view toggles on `/bill`,
  rent presets on `/calculator`, slide dots on `/present`, triage tools on
  `/intake`).
- **Selection detection**: Highlighting text inside *any* clause (`P-1`…`IV-5`)
  on `/bill` or `/clause/<id>` dynamically surfaces **`Mark selection (<ID>)`**
  and **`Propose edit (<ID>)`** in the Smart Toolbar, pre-filling the exact
  clause and quoted passage.
- **Steward toggle + passcode**: Public readers browse, calculate, post marks,
  and submit requests with zero login. Unlocking **Steward mode** (`1-tap`
  on loopback `127.0.0.1` in local dev, or gated by `BILL_STEWARD_CODE` via
  `/steward` when deployed) enables intake read-in, official answers, and
  request status transitions.
