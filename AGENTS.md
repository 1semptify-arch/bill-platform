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

- **Data rules are this repo's own — deliberate scope.** This platform
  DOES collect contributor data: marks carry an optional name and a
  never-rendered contact field, submissions inform whether proposed
  changes to the bill's wording get approved (that workflow is still
  being designed), and signatures are a separate opt-in page. Bounds:
  collected contact fields never render publicly, everything is dark
  until a steward reads it in, signature publication requires explicit
  consent, full backup is steward-gated. The app-side "no user PII
  ever" standard does not govern this repo — do not "fix" it to that
  posture; the micro-repo exists so these rules could be scoped
  independently.
- **Intake is dark & Steward-gated.** Marks never render publicly until
  `read_in`. Queued intake bodies and triage mutations (`/api/mark_action`,
  `/api/request_status`) require Steward mode (`1-tap` on loopback when
  `BILL_STEWARD_CODE` is unset; passcode-gated via `BILL_STEWARD_CODE`
  when set). Contact fields never render anywhere.
- **Moderation mechanics exist — use them per MODERATION.md.** Stewards
  can `redact` (clears name+contact columns — gone, not hidden),
  `edit` (replaces body for ads/hate/spam; original kept in
  `body_original` steward-side, edit reason shown publicly), `held`,
  `retract` (visible strike-through), `crisis_routed`. **Never edit or
  decline a mark because it criticizes the bill** — substance is
  protected; only conduct (PII, ads, hate, spam, threats) is moderated.
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


## The public mirror (site-src -> site -> Worker)

- Edit `site-src/pages/*.html` + `site-src/partials/*` — never `site/*.html`
  directly. Output files are the served contract: `python build.py`, then
  commit `site/` with the source change (the Cloudflare Worker pulls
  `site/` from GitHub, ~5-min cache).
- `build.py` runs `sync_assets.py --check` first — vendored app assets
  must match `../modules/app-semptify-fastapi` or the build fails.
- `worker.js` PAGES/ASSETS maps are the public URL contract — a new
  public page needs a map entry + worker redeploy.
- Same fragments, two UIs: `/bill/<page>` routes serve `site-src/pages`
  inside platform chrome (`views.content_page`). Public-side rules apply
  to mirror content: no advertising, no third-party promotion, no PII.
