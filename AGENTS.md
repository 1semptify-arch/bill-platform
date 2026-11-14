# Bill Platform — agent rules

Standalone minimalist working platform for the MN Rent Assurance &
Deposit Protection Act. Small on purpose — keep it that way.

## Non-negotiables

- **Python 3.11, stdlib only.** No FastAPI, no Jinja, no pip — this repo
  must run with nothing installed. (House rule: zero-cost, runs anywhere.)
- **Loopback only.** Bind `127.0.0.1`, port **8093** (PORTS.md). This is a
  case-side working desk; the public face is the static mirror
  (`semptify-bill-mirror` / bill.semptify.org) — a separate system.
- **Intake is dark.** Marks never render publicly until `read_in`. Contact
  fields never render anywhere. Do not add a path that skips the gate.
- **Canon lives upstream.** `seed_data.py` is the curated campaign seed
  (clauses + plain language + audience notes, claims ledger, locked
  decisions, journey, seed marks/requests) — edit it, not generated
  output. `seed/clauses.json` comes from
  `modules/app-semptify-fastapi/app/static/turnbuchalla/` via
  `seed/extract_clauses.py` — regenerate it, never hand-edit it.
  `seed/editions.json` mirrors the case-side register.
- **UI contract** (Brad, 2026-10-21): reading spine on the desk page,
  17–19px body, color = state only, sentences not chips, no cards with
  borders beyond hairlines, max 2 emoji per page (currently 0 — keep 0).
- **Crisis routing is a requirement, not a feature.** The mark form's
  HOME Line line and the `crisis_routed` status stay.

## Verify

```powershell
python -m py_compile server.py db.py views.py selfcheck.py seed/extract_clauses.py
python selfcheck.py     # must end with SELFCHECK PASS
```

## Layout

- `server.py` — HTTP routes + POST handlers (+ mode cookie).
- `db.py` — schema, seed-on-first-open, all reads/writes.
- `views.py` — all HTML rendering incl. the context-aware toolbar.
- `static/platform.css` — one stylesheet, three modes (`mode-desk|tv|mobile`).
- `static/platform.js` — mode guess, selection-aware toolbar, TV keys.
- `seed_data.py` — curated campaign seed (consumed by `db.init`).
- `seed/` — clause + edition seed data + the canon extractor.
- `data/platform.db` — runtime artifact, gitignored.
