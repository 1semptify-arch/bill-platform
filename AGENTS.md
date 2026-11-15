# Bill Platform — agent rules

Standalone minimalist working platform for the MN Rent Assurance &
Deposit Protection Act. Small on purpose — keep it that way.

## Non-negotiables

- **Python 3.11, stdlib only.** No FastAPI, no Jinja, no pip — this repo
  must run with nothing installed. (House rule: zero-cost, runs anywhere.)
- **Loopback for local dev; Render for public.** Local dev binds
  `127.0.0.1`, port **8093** (`PORTS.md`). Public deploy runs on Render
  free tier (`render.yaml` blueprint): `PORT`/`HOST` env-driven, SQLite
  persisted to Cloudflare R2 via Litestream (`litestream.yml`). Prod
  MUST set `BILL_STEWARD_CODE` — one-tap steward unlock auto-disables
  off-loopback. Independent micro-repo, decoupled from Semptify's
  `ssot.css` / `sync_assets.py` constraints while keeping the canonical
  bill substance intact.
- **Intake is dark & Steward-gated.** Marks never render publicly until
  `read_in`. Queued intake bodies and triage mutations (`/api/mark_action`,
  `/api/request_status`) require Steward mode (`1-tap` on loopback when
  `BILL_STEWARD_CODE` is unset; passcode-gated via `BILL_STEWARD_CODE`
  when set). Contact fields never render anywhere.
- **UI contract**: warm monochrome palette, 17–19px desk/mobile body,
  23px+ TV stage scale, color = state only, 1px hairline borders, zero emoji.
- **Crisis routing stays.** The mark form's HOME Line (`612-728-5767`) notice
  and the `crisis_routed` triage path stay.

## Verify

```powershell
python -m py_compile server.py db.py views.py seed_data.py selfcheck.py seed/extract_clauses.py
python selfcheck.py     # must end with SELFCHECK PASS
```

## Layout

- `server.py` — HTTP routes, Steward cookie/passcode gate, `/api/calculate`, POST handlers.
- `db.py` — SQLite schema, seed-on-first-open, `calculate_braid()`, all reads/writes.
- `seed_data.py` — canonical 23 clauses (statute + plain language + audience notes), 12 claims, 8 locked decisions, 6 journey steps, seed marks/requests.
- `views.py` — HTML rendering across all routes, 8-slide `/present` TV deck, Context-Aware Smart Toolbar, desktop rail, and mobile bottom bar.
- `static/platform.css` — one stylesheet, three distinct screen layouts (`mode-desk`, `mode-tv`, `mode-mobile`).
- `static/platform.js` — Brain layer: viewport mode suggest, multi-clause selection toolbar, live 60fps funding-braid math, TV slide keys (`←`/`→`/`Space`/`1`–`8`/`F`/`Esc`).
- `seed/` — canonical editions register + upstream clause extractor.
- `data/platform.db` — runtime SQLite database, gitignored.
