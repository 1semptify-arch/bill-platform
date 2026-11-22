# Build State — bill platform + public mirror

What's live, what's pending. Updated when state changes — not a changelog
(see OPERATIONS_LOG.md for that).

## Live now (verified 2026-11-10)

- `semptify.org/bill` microsite — self-contained, Cloudflare Worker
  (`bill-mirror`), ~5min page cache. **All 11 routes live:** home, bill,
  live, research, what-the-bill-changes, your-voice, history, providers,
  brief, classroom, press, myths.
- Worker URL map complete: 6 `/bill/*` routes + `brain.js` added
  2026-11-10 (worker.js now versioned in this repo — see README).
- Previously-404 assets fixed same pass: `doc-page.jpeg` (paper texture —
  was broken on every interior page), `loon.png`, `mn-flag.png`,
  `semptify-live-001-cover.jpg`.
- `brain.js` live — tools-rail anchors, rail board widget, live badge,
  30s polling all active in prod.
- Board pipeline verified end-to-end: POST `/api/voice-post` → Neon →
  `awaiting_review` increments; GET `/api/voice-posts` public.
  Moderation lane: `/admin/public-voice` (app admin).
- App-origin redirects: `semptify-jsam.onrender.com/bill*` → 301 to
  `semptify.org/bill*` (verified 2026-11-10).
- **Publish contract moved into this repo (2026-11-14):** case-side
  `publish_bill.py` now writes `site-src/partials/bill_draft.html` (verbatim
  sanitized working file) + `site-src/partials/bill_statute.html` (clean
  reading copy — the act-name→notes-tail split the retired app-side
  `bill_statute_view()` used to derive at render time, now cut at
  publish). `build.py` slots them into `live.html` via
  `{{BILL_DRAFT}}`/`{{BILL_STATUTE}}`; empty/missing statute partial
  falls back to the draft, missing draft falls back to an honest note.
  /bill/live now shows the clean statute first with the verbatim
  working file in a `<details>` fold. `data/bill_claims_public.json`
  is still written app-repo-side (ledger + history-page canon path).
- Dark mode, anonymous APIs — verified 2026-11-05 audit; markup confirmed
  unchanged since.

## Pending / known gaps

- **Voice review queue** — 4 posts awaiting moderation at
  `/admin/public-voice`, including one `probe-do-not-post` test row
  (decline it). Public board shows "Nothing posted yet" until first
  publish — decide whether to seed.
- ~~Retire the 5 app bill templates~~ — done 2026-11-13 (app repo
  `bb30653e`/`bb577294`, local-only until pushed).
- **Retire legacy `home.html`** — the Worker's `/` origin-down fallback
  (timeout >8s or origin 5xx → `mirror('home.html')`; documented in
  README + worker.js 2026-11-14). All its assets are worker-mirrored so
  it renders with the origin fully down — retirement removes that
  resilience and needs a worker.js edit + redeploy. Decision is Brad's.
- **Dead scene-gen artifacts at root** — `gen-flux-4.png` +
  `mask-buck.png` (FLUX base + inpaint mask, commit e13a49e): not in
  the worker map, unreferenced — they 404 if requested. Delete or
  keep for a future scene pass. (`cherry.jpg` retired earlier.)
- **`bill-scene-alt1.jpg` + `bill-scene-ai.jpg` FAIL scene-authenticity**
  (audit 2026-11-14, task-950071e5): alt1's deer stands mid-lake IN the
  water; ai's deer wades with legs in the water and its campfire burns
  beside the cabin at porch level — both violate Brad's scene rules
  (deer on dry land at water's edge; fire only in a stone ring on the
  beach). Both stay in the worker ASSETS map (fetchable but unreferenced
  by any page); do NOT use them in the planned rotation until
  regenerated or replaced — scene-owner call pending Brad. alt2 and
  aurora pass.
- **`bill.semptify.org` scene-img 404 (dormant)** — that host serves
  Turnbuchalla only; `/static/img/bill-scene-*.jpg` 404s there.
  Nothing on the host references them today — only fires if
  `bill_hub` is ever served on that host. Fix = mirror-asset copy or
  worker map entries on the bill host (dashboard access).
- **Unpushed commits** — this repo accumulates local commits that
  `git push` denial leaves on disk; prod reads GitHub master, so an
  unpushed commit = invisible change. Brad pushes on review.
- **Neon/DB**: pool retune shipped (#332) — compute suspends after
  ~5 idle min. Watch first-week CU-hours vs the ~20/mo burn.
- **Parallel-session commits** — ssot sync + ops-log commits from a
  concurrent agent session were unpushed at time of worker deploy;
  pushed together with this state update.

## Last verified

- 2026-11-14 — `/bill/live` preview (127.0.0.1:8791): clean statute view
  renders (act name, I-1…IV-5 clause heads, status note), working-file
  `<details>` fold opens with verbatim shorthand intact, zero console
  messages. Publish run: `publish_bill.py --allow-pending` wrote both
  partials + refreshed claims JSON (12 rows, 5 flagged).
- 2026-11-10 — all 11 routes 200, brain.js + previously-404 images 200,
  content-types correct, AI binding preserved, POST→DB write path proven
  (awaiting_review 3→4 on probe).


## Platform state (absorbed from STATUS.md, 2026-11-16)

- Interactive platform live locally `:8093`; Render deploy prepared
  (`render.yaml` free tier + `litestream.yml` SQLite→R2). Repo public:
  `github.com/1semptify-arch/bill-platform`.
- Working boards: margin, intake (dark→steward), requests, positions,
  claims, decisions, editions, changes (chronological CH- ledger),
  signatures (/sign, consent-gated S-numbers), campaign + allies,
  teach, packet, search, track/receipts, help, legal.
- 3 screen modes + auto-detect + smart toolbars. Steward one-tap is
  loopback-only; prod needs BILL_STEWARD_CODE.
- 100+ selfchecks green.

## Consolidation state (2026-11-16)

- **One repo:** `1semptify-arch/bill-platform` = static mirror build
  (site-src→site) + interactive platform (server/db/views→Render).
  Old mirror repo archived.
- **served:** semptify.org/bill* via bill-mirror Worker → site/ on
  GitHub main (~5min cache). platform.semptify.org → Render, pending
  dashboard setup (env: BILL_STEWARD_CODE + 4 R2 vars).
- **SSOT:** canonical bill text still upstream in app-semptify turnbuchalla;
  both renderers derive from it (sync gate + extract_clauses.py).
- Selfcheck green incl. content routes.

## Live state (2026-11-16)

- **LIVE:** `https://bill-platform-5873.onrender.com` (Render free,
  oregon, auto-deploys on push to main).
- **Branded:** `platform.semptify.org` — proxy worker + route deployed;
  pending one proxied DNS record (CNAME platform → bill-platform-5873.onrender.com).
- **Persistence:** ACTIVE — Litestream replicating to R2 (verified 2026-11-17).
  (R2 API token = dashboard-only creation). Bucket ready: bill-platform-db.

## Public address (2026-11-16)

- **semptify.org/bill IS the platform now** — proxy worker routes the
  bill URL space to the Render app (mounted at /bill). One UI with
  smart nav/toolbars across reading + mechanics.
- Old mirror content = same site-src fragments rendered in platform
  chrome; static site/ build remains as archive/rollback (worker
  dormant but deployed — re-point routes to roll back).
- Render: BILL_MOUNT=/bill + BILL_STEWARD_CODE set; R2 litestream
  dormant pending dashboard-created API token.

## Serving split (2026-11-16)

- **Reads:** site/bill/ snapshot via GitHub raw + CF edge cache (300s).
  Snapshot pages: /bill/, desk, bill reader, clause/*, content pages,
  teach, calculator, help, legal, present slides.
- **Live:** margin, requests, changes, campaign, sign, positions,
  decisions, editions, claims, intake, track, search, packet, mark,
  steward, mode, api — all proxy to Render.
- **Render hours:** ~0 while idle (sleeps; only live-path traffic wakes).
  Shared free-tier budget with Semptify/septify-pi is safe.
- **Republish reads:** python snapshot.py --deploy && git push.

## Current state (2026-11-18)

- **Public intake bug fixed + deployed:** honeypot check read key
  presence, not value — every real browser mark/request/signature was
  silently discarded since 356cde0. Fixed cb6ade5, pushed, selfcheck
  PASS (honeypot coverage now exercised end-to-end).
- **Load tested:** tools/bill_stress.py (master repo) — ~7.4k local
  requests, zero 5xx/locks; 40/40 prod 200s p50 ~300-700ms. listen
  backlog widened 5->128 (7cdf653); GH Actions keepalive pings Render
  inside daytime windows (8da4d8c) — cold starts should be rare.
- **/bill/precedents live** — private-failure + public-model record,
  12-slide interactive PDF deck in app-crm/docs (36 live links).
- **Campaign layer in app-crm (master repo):** 35-contact verified
  roster seed, 7-day plan, outreach drafts, contacts/agenda docs.
- **Pending:** Gmail MCP drafts (server down — texts saved in
  app-crm/docs/OUTREACH_DRAFTS.md); bill@semptify.org send-as + DMARC
  p=none record; verify prod /bill/mark accepts a real submission;
  selfcheck POST helper now sends website= (done 2026-11-18 pass).
- **Known noise:** untracked .cursor/ + .playwright-mcp/ dirs —
  tool artifacts, gitignored 2026-11-18, do not commit.

## Current state (2026-11-21)

- **Architecture changed 2026-11-19 (other sessions):** bill platform is
  now EMBEDDED inside the Semptify FastAPI app — semptify.org/bill →
  CF edge worker → semptify-jsam → middleware → in-container bill
  server. Persistence: Litestream→R2 with rolled creds on Semptify env.
  bill-5873 left running but ephemeral/unsuspended (nothing routes to it).
  See OPERATIONS_LOG.md 2026-11-19 entry for the full cutover record.
- **Prod intake VERIFIED end-to-end 2026-11-21:** POST
  semptify.org/bill/api/mark with empty honeypot (browser-identical) →
  303 /bill/track?code=baefda29 — accepted through the whole chain
  (CF → FastAPI → embedded server → R2 SQLite). Filled honeypot →
  /margin (bot path intact). Receipt page renders "queued".
  Test mark is dark intake, safe for stewards to discard.
- **Selfcheck PASS** on current tree (includes empty-honeypot coverage
  on all 3 public intake posts).
- **Pending (Brad, dashboard):** suspend bill-5873 for tidiness;
  verify Litestream replication stays healthy on Semptify env.
- **Untracked:** _C_DRIVE_COORDINATION.md — cross-session C:-cleanup
  contract file, intentionally not committed.
