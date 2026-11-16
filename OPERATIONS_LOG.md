# Operations Log — bill platform + public mirror

Dated record of site-affecting operations. Newest first. Format:
`YYYY-MM-DD — what changed — where verified`.

## 2026-11-16

- **CONSOLIDATION — one repo, one SSOT.** semptify-bill-mirror merged
  into bill-platform: `src/` → `site-src/`, generated pages → `site/`
  (byte-identical output verified), build.py/sync_assets.py/worker.js
  retargeted, worker BASE → bill-platform/main/site/. Platform serves
  the same fragments in its own chrome at `/bill/<page>` — one source,
  two UIs. Docs unified: README/AGENTS/BUILD_GUIDE/BUILD_STATE/
  OPERATIONS_LOG; STATUS.md folded into BUILD_STATE, CHANGELOG.md
  folded in below.
- windows-mcp + stale E: mirror cleanup (separate system work same day).

## Platform history (folded from CHANGELOG.md, newest first)

## 2026-11-14

### `344cdaa` — Screen size is now automatic
The site detects your screen live: phone-width gets the mobile layout,
TV-width gets the presentation stage, everything in between gets the
desktop workspace. Resizing the window switches instantly — no reload.
A new "Auto" chip leads the mode switcher; picking Desktop / TV / Mobile
still pins that mode manually until you choose Auto again.

### `0a0cc01` — Bigger logo, honest footer
Logo doubled (topbar 68px, footer 40px). Removed the "nonprofit" wording
— the org isn't filed yet, so the footer now reads "A Semptify project."

### `245f3e3` — Official lockup logo
The Mini Aussie now sits over the word "Semptify" in Vikings purple with
a snow-white edge — matching his jersey. This is the canonical logo
(`static/logo-master.png`); every other size derives from it.

### `fa54d9e` — Logo ready for Google + browser tab
Exported a square 512×512 transparent logo for Google uploads (copy in
`Downloads`). Added the favicon so the dog shows in the browser tab on
every page. Saved the full-res cleaned master for future sizes.

### `561163d` — Mascot arrives
The Mini Aussie sketch got its white background removed (interior fur
kept), was cropped, wrapped as `logo.svg`, and wired into the topbar
(34px) and footer (20px).

### `8073172` — Front door built
`/` became a real index page: Introduction, How It Works (the 6-step
mark→intake→read-in→margin flow), and a Living Document badge linked to
the Editions ledger. The old reading spine moved to `/desk`. Every page
gained a "Presented by Semptify" footer with a semptify.org link.

### `16cdbf3` — Full working mechanics suite
- Interactive 3-source Funding Braid calculator (`/calculator` + API):
  deposit float + M1PR advance + landlord match, fraud/recession stress.
- Steward toggle + passcode gate protecting dark intake and request triage.
- Dedicated 8-slide 16:9 TV briefing deck (`/present`) with keyboard and
  remote-style navigation, live rent slider on slide 4, and clause pull-up
  on slide 7.
- Desktop two-column workspace rail, audience lenses (renter / provider /
  lawmaker), select-text-to-mark smart toolbar, and mobile thumb-zone
  bottom navigation.

### `94dfce3` — First light
Standalone micro-repo created: Python 3.11 stdlib server + SQLite, no
dependencies. 23 bill clauses seeded with statute + plain language, the
claims ledger, locked decisions, editions, public marks with dark intake
→ steward read-in → numbered public margin, requests pipeline, positions,
and three screen modes. End-to-end `selfcheck.py` harness.

### Next — Change ledger: every proposed and incorporated change on record
New `/changes` page — a permanent ledger where every edit-kind mark read
into the Margin automatically lands as a numbered proposed change
(CH-0001…). Stewards can also record proposals from the requests/briefing
lane, then incorporate them (with edition ref + before/after statute
diff), decline, or retract — nothing is deleted, only resolved. Each
clause page now shows its own change history. Fixed `_next_no` to support
multi-letter prefixes (CH-).

### Next — v1.1 coverage pass + Teach page
Full gap sweep: mark permalinks (/margin#M-0001), visible retract for
read-in marks, private receipt codes + /track status lookup, /search
across the whole record, shareable calculator URLs, honeypot + rate
limit on public posts, og/description meta, print stylesheet, skip-link,
steward /api/export backup, speaker notes on the TV deck (?notes=1),
and /teach — a 14-stop guided path through the bill with plain language
and discussion prompts for classrooms and tenant meetings.

### Next — The campaign: /campaign + /packet + legislator mailto
Campaign hub for carrying the bill to 2027: journey lane, the 5-step
plan, one-thing actions (mark / request / mail-to-legislator / teach /
print packet), and the allies ledger — supporters tracked through
target → contacted → talks → endorsed, steward-managed. Seeded with
Amy Klobuchar (endorsed) plus 14 coalition targets (HOME Line, HJC, IX,
CTUL, legal aid, faith orgs, MHA, MHFA, SFM, Eviction Lab). /packet is
the printable testimony packet — read-in marks grouped by clause. Clause
pages gained a "Send to a legislator" mailto action.

## 2026-11-14 (deploy prep)

### Remote deploy path — GitHub → Render → Cloudflare + R2
The platform no longer has to live on Brad's machine. Repo pushed to
GitHub (`1semptify-arch/bill-platform`, private); `render.yaml`
blueprint deploys it as a Render **free-tier** web service. The SQLite
ledger persists via **Litestream → Cloudflare R2** (the storage
Semptify already uses): every write streams to R2 in near-real-time and
the DB auto-restores on boot — no paid disk needed. `PORT`/`HOST` and
`PLATFORM_DB` are now env-driven. Cloudflare's role stays front-door
only (DNS + TLS at platform.semptify.org). `AGENTS.md` updated:
loopback is now the local-dev rule, not the only mode.

### The signature book — `/sign`
A voluntary endorsement list, like the visitor's book at a town hall.
Anyone can sign their name to the bill — it lands dark (queued) with a
private receipt, and only publishes when a steward reads it in, with an
S-number. Only name, org/town, and the optional line ever render; the
consent checkbox is required, and the optional email never publishes —
that field is the seam where OAuth storage plugs in later. Stewards get
an "Awaiting publish" queue on the page with Publish/Hold. Wired into
nav, footer, search, receipts, export, and the campaign's do-one-thing.

### Help lines, legal pages, and the Minnesota flag
`/help` is a public help directory — 911, 988, Crisis Text Line, HOME
Line, 211, SAMHSA, AA/NA/Al-Anon, the MN gambling helpline, Gamblers
Anonymous, Debtors Anonymous, Day One, LawHelpMN. Official public
channels only; no advertising, no endorsements, nobody paid to be
listed. `/legal` carries the privacy policy (what's stored, receipts,
the two functional cookies, in-memory rate limiting, R2 backups),
terms (draft not law, steward review, no PII-of-others, no ads, not
legal advice), and the license (content CC0 public domain, code MIT).
The 2024 Minnesota flag sits in the index hero kicker and the footer
next to the Semptify lockup. Footer links to Help and Legal sitewide;
the mark form's crisis line now links to the help page.



## 2026-11-14

- **`home.html` role audited + documented** (swe-2, task-baa88882):
  the legacy "Semptify Live" cover is NOT dead weight — worker.js
  serves it as the `/` origin-down fallback (>8s timeout or 5xx from
  the app origin), and every asset it needs (ssot.css, cover image)
  is worker-mirrored so it renders with the origin fully down. Not in
  `src/pages/`, not built by `build.py` — root-authored legacy page.
  Documented the contract in README + a worker.js comment + corrected
  the BUILD_STATE pending item. Retirement remains Brad's call
  (removal path recorded in README); a `bill.html` fallback is the
  likely replacement if retired.

- **Research ledger statuses refreshed to canon** (swe-2, task
  task-71e5f6fc): every row showed "checking" — stale since the
  10/23 verification pass. Statuses now mirror the canon vocabulary
  (`references.html` Quotable Shelf): 1% deposit interest →
  **verified** (Minn. Stat. §504B.178 subd. 2, checked 10/23·11/2);
  the 11 internal-model figures → **estimate** (derivation shown,
  math audit passed 10/23, awaits actuarial review). Added a
  "what the statuses mean" line to the explainer box.
  `data/bill_claims_public.json` in the app repo updated in lockstep
  (same status fields; `published:true` on the verified row only).
  Verified live: all 11 routes + 12 mapped images 200 on
  semptify.org. Flags: `gen-flux-4.png`/`mask-buck.png` are dead
  scene-gen artifacts (404, unreferenced); `bill.semptify.org`
  scene-img 404 is dormant (host references no scene assets);
  worker.js map is complete — dashboard edits remain Brad's lane.

## 2026-11-10

- **ssot.css sync + history regen** (swe-2, task
  plan-20261110-bill-mirror-run-sync-assets-py-ssot-css--efd9):
  drift check flagged root `ssot.css` stale vs app
  `static/css/ssot-design-system.css` — upstream added the
  `body.shell--dc-alt` A/B Document-Center layout block (flipped
  rail geometry). `sync_assets.py` synced the verbatim copy;
  vendored `src/bill.css` sections and all other tracked assets
  were already in lockstep. `build.py` regenerated all 11 root
  pages; only real diff = `history.html` picking up 3 new rows
  (canon 037fc2f9 + 73fb7648, site e79f555). Verified: preview on
  :8791 — `/bill/history` 200 with new rows rendered,
  `/ssot.css` 200 serving `shell--dc-alt`, IronBee console clean;
  py_compile PASS on build.py / sync_assets.py / preview_server.py;
  pytest test_ssot_architecture.py 7/8 — the one FAIL is
  pre-existing and unrelated (executive_admin/router.py:401 raw
  RedirectResponse; app-repo issue, logged as intake-eb3daf41,
  not touched). Committed 06d5b95. NOT pushed — `git push` is
  denied for headless runs.

- **Worker URL-map gap verified in prod — 6 routes serving wrong
  content** (swe-2, task
  plan-20261110-add-6-bill-routes-static-js-brain-js-to--e6ea):
  live probe of all 13 contract paths. The 5 original routes +
  `/static/js/law-linker.js` are worker-served and correct
  (`/bill` body = GitHub master `bill.html` + CF beacon injection
  — worker pulls current master, files need no push). The six new
  `/bill/*` routes are NOT in the map — they fall through to the
  Render origin and return **HTTP 200 with the app's "Setting Up
  Your Storage" onboarding page** (worse than a 404 — silent
  wrong content). `/static/js/brain.js` 404s via the origin and
  is edge-cached up to 4h. Fix = add the 7 map entries in the
  dashboard worker; exact entries + verification protocol in
  `master-repo/handoffs/2026-11-10-bill-worker-url-map.md`.
  BLOCKED: no headless path to edit the worker — cloudflare MCP
  OAuth grant lacks workers scopes, no API token on this machine,
  dashboard-only source. Needs Brad: dashboard edit, an API
  token, or MCP re-auth.

- **Worker URL-map gap FIXED — all 11 routes + brain.js + 4 images
  live** (devin interactive session, Brad-authorized wrangler OAuth):
  unblocked the headless agent's blocker — `npx wrangler login` → OAuth
  token → `PUT /workers/scripts/bill-mirror/content`. Added the 6
  `PAGES` routes, 5 `ASSETS` entries (`brain.js`, `doc-page.jpeg`,
  `loon.png`, `mn-flag.png`, `semptify-live-001-cover.jpg`), `jpeg`
  content-type. Verified: 11/11 routes 200, assets 200, AI binding
  preserved. **Silent breakage also fixed:** `doc-page.jpeg` paper
  texture, `loon.png`, `mn-flag.png` were 404ing in prod — interior
  pages had no paper texture until this deploy. POST
  `/api/voice-post` → Neon write path proven live (awaiting_review
  3→4); disclosure — probe left a `probe-do-not-post` row in the
  review queue, decline at `/admin/public-voice`. `worker.js` now
  committed to repo (was dashboard-only — the fragility that caused
  this). Docs updated: README + BUILD_GUIDE + BUILD_STATE.

## 2026-11-07

- **"Page at first light" background pass + scene-layering fix** (swe-2,
  task plan-20261106-bill-pages-new-background-design-pass-wh-e453):
  root cause of the "flat empty page" — `.paper-scene` was
  `position:fixed;inset:0;z-index:0`, which paints ABOVE all
  non-positioned content, so the whole liquid frame (header, bill nav,
  tools + options rails) rendered under the parchment and only `main`
  (z-index:1) was visible. pointer-events:none hid it from hit-testing,
  which is why DOM/computed checks looked fine. Scene now sits at
  z-index:-1 — the frame has never visibly rendered until now.
  New interior backdrop: real laid-paper texture (doc-page.jpeg,
  regenerated — the vendored file was an ice-fisherman photo, used as
  card texture on every interior page AND offered on /bill/press as
  "the paper texture") + dawn band rising at the top edge + lamp pool
  + cool water shade + loon woodcut watermark (multiply blend,
  bottom-right) + deckle edge vignette + 80s lamp-glow breathe (off
  under prefers-reduced-motion). Cover /bill: dropped the winter-snow
  cherry photo (season clash, covered the kicker), loon now blends via
  multiply (was a floating white box), flag stays, scene gets the same
  deckle edge vignette. Verified: all 11 routes + 4 scene assets 200,
  IronBee shots at 1440px + 375px, console clean, reduced-motion gate
  confirmed live. NOT pushed — awaiting Brad's visual check.
  Flagged: cherry.jpg now unreferenced (31KB dead asset — delete or
  keep for reuse); at ≤1100px body drops to display:block so rails
  stack in DOM order (tools before main) — pre-existing shell
  behavior, not touched.

- **Verification re-run post-4dbf38d/d7d4f70** (swe-2, same task —
  dispatcher re-spawn): fresh pass on current HEAD. py_compile PASS
  (3.11.9): build.py, sync_assets.py, preview_server.py; brain.js
  `node --check` PASS. build.py clean — drift gate + 11 pages; only
  diff = history.html picking up 2 new canon commits (e3612507,
  9c6061d1), regenerated + committed as usual. pytest
  test_ssot_architecture.py 8/8 PASS (68s, --no-cov; the earlier
  coverage-gate error is an artifact of running one file, not a test
  failure). guardrail_engine 9/9 PASS (86.4s). Manual: preview :8791 —
  19 route/asset probes all 200 (11 pages, brain.js, law-linker.js,
  5 images, /api/voice-posts proxy); IronBee runtime trace on
  /bill/live: every request repo-local /static/* or Google Fonts except
  the voice-posts data seam (200 via proxy), console zero messages,
  ARIA shows all four rails + live-board status text.
- **Verification resubmit pass** (swe-2, same task — desk bounce asked
  for populated verification fields): re-ran everything independently.
  py_compile PASS (3.11.9): build.py, sync_assets.py, preview_server.py.
  build.py clean — drift gate + 11 pages, zero diff vs committed root.
  pytest tests/test_ssot_architecture.py 8/8 PASS (45.32s, venv311).
  guardrail_engine 9/9 PASS (34.34s). Manual: preview_server :8791 —
  16 route/asset probes all 200; IronBee runtime trace on /bill +
  /your-voice: 130 requests all 200, every request repo-local /static/*
  or Google Fonts except the /api/voice-posts data seam (200 via proxy);
  console clean both pages. **Found + fixed:** home.html (tracked legacy
  Semptify Live cover, still served at /home.html) referenced
  /static/img/semptify-live-001-cover.jpg which was never vendored —
  404. Added to sync_assets VERBATIM_FILES and synced; now 200.
  home.html itself is a legacy non-bill page — retire decision logged
  to the queue for Brad.

- **Microsite self-containment audit + worker-map doc fix** (swe-2,
  task plan-20261105-make-bill-section-a-self-contained-micro-06d7):
  verified the site is fully self-contained — `python build.py` clean
  (drift gate + 11 pages, zero diff vs committed root), runtime trace
  on preview:8791 shows only repo-local `/static/*` + Google Fonts +
  the `/api/voice-posts` data seam (200, proxied). No app-shell
  dependency anywhere. Fixed a doc gap: `/static/js/brain.js` was not
  in the README Worker-map contract or the BUILD_STATE deploy
  prerequisite — without a worker entry it would 404 in prod and kill
  the tools/options rails. Added `.gitignore` (`__pycache__/`, `*.log`,
  `nul*`).

- **Static-asset sync automated** (swe-2): new `sync_assets.py` syncs all
  app-sourced copies (root css/js/img + the vendored ssot sections inside
  `src/bill.css`) from `../modules/app-semptify-fastapi`, with `--check`
  mode reporting drift. `build.py` runs the check before every build —
  stale assets now fail loudly instead of shipping silently (root cause
  of the northstar dark-pin / ssot fill-fix drift). Synced `ssot.css`
  (was missing the dark-mode paper-text-on-primary-fill rules).
- **Six new bill-wing spaces built** (swe-2, architecture draft §5):
  history (public version history — build.py now merges `git log` from
  this repo + the app repo's bill canon into a dated table with GitHub
  commit links), providers, lawmakers' brief, classroom kit, press room,
  myths & facts. New links added to rail_top, nav_deck, rail_tools, and
  cover panels. preview_server.py aliases added for the six routes;
  port 8791 registered in PORTS.md. Verified via build + local preview.
  NOT pushed — deploy needs the six `/bill/*` routes added to the
  Cloudflare Worker URL map first (dashboard-only source).

## 2026-11-05

- **DB pool retune shipped** — `NullPool` on `render_balanced` (#332) +
  SSOT redirect fix (#333), deploy `dep-dbmadglbedkc73bmlb6g`.
  Verified: Neon compute `ep-cold-surf` went idle/suspended 16:05Z after
  ~5.5 min quiet — first time it ever could. CU-hour burn closed.
- **Bill 301s verified on origin** — all five `/bill*` paths redirect to
  semptify.org (PR #330, carried in same deploy).
- **Decision engine live** — desk at 127.0.0.1:8600/desk; orchestrator +
  review pages retired to redirects (consolidation pass).

## 2026-11-04 → 2026-11-05 (earlier)

- Public-site audit fixes — dark-mode collisions on /bill/research,
  non-200 assets, live-draft sanitization (strikethrough, no filenames,
  no user name), anonymous API behavior (PR #326).
- Dead CSS System 3 removed — PR #329 merged.
- Module-registry workflow fixed to PR-flow — PR #328 merged.
- `render_balanced` profile deployed — embeddings + registry kept,
  Positronic Brain/Mesh/monitoring off.

## Standing notes

- Cloudflare worker cache ~5 min — "pushed but not live" is usually cache.
- App origin bill paths MUST stay 301 — a 200 there means the stale twin
  is back.
- Neon free plan: suspend is fixed 5 min, not configurable — app-side
  connection behavior is the only lever.

## 2026-11-06

- **Desk scene replaces lake on interior pages** (swe-2, Brad's spec):
  sitter's-POV oak desk — worn front edge, haphazard written-on parchment
  stack left, fresh sheet front-center, ink bottle, quill resting right,
  half-burnt candlestick back-left. Animations: candle-flame flicker +
  halo/light pulse, quill lifts and writes left→right laying a visible
  ink line that fades, dust motes. Quill write disabled ≤700px (would
  smudge behind the content column); all motion off under
  prefers-reduced-motion. Lamplit parchment pool added behind .shell-main
  for heading contrast. Cover (/bill deck) keeps the lake scene.
  Built via build.py; verified locally at 1280px + 375px, console clean.
  NOT yet pushed — awaiting Brad's visual check.
- **Parchment liquid layout replaces desk scene** (swe-2, Brad's spec):
  flat warm parchment backdrop; true-liquid frame = low-profile Semptify
  bar (header) + bill nav top rail + tools rail left + options/board rail
  right + main + footer. brain.js (root) = logic layer: auto 'On this
  page' tool anchors, board polling /api/voice-posts every 30s into rail
  + full list on /your-voice, live badge, rail status text. Board =
  existing anonymous voice-posts API (bulletin board, not chat).
  Desk scene retired to git history (9353a37). preview_server.py now
  proxies /api/* to semptify.org. Verified: grid geometry + computed
  styles at 1280px via IronBee, structure snapshot clean. NOT pushed —
  awaiting Brad's visual check.
- **MN manuscript theme applied** — lake-dawn scene (mn-lake-sunrise.jpg)
  + MN flag + loon + cherry branch + ink-bottle/quill SVG on all bill
  pages; interior pages' cards now parchment (doc-page.jpeg texture);
  UnifrakturMaguntia blackletter + Pinyon Script calligraphy added to
  head.html. New assets at repo root: mn-flag.png, loon.png, cherry.jpg,
  doc-page.jpeg. Built via build.py; verified locally — all assets 200,
  fonts load. NOT yet pushed — awaiting Brad's visual check.
# Operations Log — bill platform + public mirror

Dated record of site-affecting operations. Newest first. Format:
`YYYY-MM-DD — what changed — where verified`.

## 2026-11-16

- **CONSOLIDATION — one repo, one SSOT.** semptify-bill-mirror merged
  into bill-platform: `src/` → `site-src/`, generated pages → `site/`
  (byte-identical output verified), build.py/sync_assets.py/worker.js
  retargeted, worker BASE → bill-platform/main/site/. Platform serves
  the same fragments in its own chrome at `/bill/<page>` — one source,
  two UIs. Docs unified: README/AGENTS/BUILD_GUIDE/BUILD_STATE/
  OPERATIONS_LOG; STATUS.md folded into BUILD_STATE, CHANGELOG.md
  folded in below.
- windows-mcp + stale E: mirror cleanup (separate system work same day).

## Platform history (folded from CHANGELOG.md, newest first)

## 2026-11-14

### `344cdaa` — Screen size is now automatic
The site detects your screen live: phone-width gets the mobile layout,
TV-width gets the presentation stage, everything in between gets the
desktop workspace. Resizing the window switches instantly — no reload.
A new "Auto" chip leads the mode switcher; picking Desktop / TV / Mobile
still pins that mode manually until you choose Auto again.

### `0a0cc01` — Bigger logo, honest footer
Logo doubled (topbar 68px, footer 40px). Removed the "nonprofit" wording
— the org isn't filed yet, so the footer now reads "A Semptify project."

### `245f3e3` — Official lockup logo
The Mini Aussie now sits over the word "Semptify" in Vikings purple with
a snow-white edge — matching his jersey. This is the canonical logo
(`static/logo-master.png`); every other size derives from it.

### `fa54d9e` — Logo ready for Google + browser tab
Exported a square 512×512 transparent logo for Google uploads (copy in
`Downloads`). Added the favicon so the dog shows in the browser tab on
every page. Saved the full-res cleaned master for future sizes.

### `561163d` — Mascot arrives
The Mini Aussie sketch got its white background removed (interior fur
kept), was cropped, wrapped as `logo.svg`, and wired into the topbar
(34px) and footer (20px).

### `8073172` — Front door built
`/` became a real index page: Introduction, How It Works (the 6-step
mark→intake→read-in→margin flow), and a Living Document badge linked to
the Editions ledger. The old reading spine moved to `/desk`. Every page
gained a "Presented by Semptify" footer with a semptify.org link.

### `16cdbf3` — Full working mechanics suite
- Interactive 3-source Funding Braid calculator (`/calculator` + API):
  deposit float + M1PR advance + landlord match, fraud/recession stress.
- Steward toggle + passcode gate protecting dark intake and request triage.
- Dedicated 8-slide 16:9 TV briefing deck (`/present`) with keyboard and
  remote-style navigation, live rent slider on slide 4, and clause pull-up
  on slide 7.
- Desktop two-column workspace rail, audience lenses (renter / provider /
  lawmaker), select-text-to-mark smart toolbar, and mobile thumb-zone
  bottom navigation.

### `94dfce3` — First light
Standalone micro-repo created: Python 3.11 stdlib server + SQLite, no
dependencies. 23 bill clauses seeded with statute + plain language, the
claims ledger, locked decisions, editions, public marks with dark intake
→ steward read-in → numbered public margin, requests pipeline, positions,
and three screen modes. End-to-end `selfcheck.py` harness.

### Next — Change ledger: every proposed and incorporated change on record
New `/changes` page — a permanent ledger where every edit-kind mark read
into the Margin automatically lands as a numbered proposed change
(CH-0001…). Stewards can also record proposals from the requests/briefing
lane, then incorporate them (with edition ref + before/after statute
diff), decline, or retract — nothing is deleted, only resolved. Each
clause page now shows its own change history. Fixed `_next_no` to support
multi-letter prefixes (CH-).

### Next — v1.1 coverage pass + Teach page
Full gap sweep: mark permalinks (/margin#M-0001), visible retract for
read-in marks, private receipt codes + /track status lookup, /search
across the whole record, shareable calculator URLs, honeypot + rate
limit on public posts, og/description meta, print stylesheet, skip-link,
steward /api/export backup, speaker notes on the TV deck (?notes=1),
and /teach — a 14-stop guided path through the bill with plain language
and discussion prompts for classrooms and tenant meetings.

### Next — The campaign: /campaign + /packet + legislator mailto
Campaign hub for carrying the bill to 2027: journey lane, the 5-step
plan, one-thing actions (mark / request / mail-to-legislator / teach /
print packet), and the allies ledger — supporters tracked through
target → contacted → talks → endorsed, steward-managed. Seeded with
Amy Klobuchar (endorsed) plus 14 coalition targets (HOME Line, HJC, IX,
CTUL, legal aid, faith orgs, MHA, MHFA, SFM, Eviction Lab). /packet is
the printable testimony packet — read-in marks grouped by clause. Clause
pages gained a "Send to a legislator" mailto action.

## 2026-11-14 (deploy prep)

### Remote deploy path — GitHub → Render → Cloudflare + R2
The platform no longer has to live on Brad's machine. Repo pushed to
GitHub (`1semptify-arch/bill-platform`, private); `render.yaml`
blueprint deploys it as a Render **free-tier** web service. The SQLite
ledger persists via **Litestream → Cloudflare R2** (the storage
Semptify already uses): every write streams to R2 in near-real-time and
the DB auto-restores on boot — no paid disk needed. `PORT`/`HOST` and
`PLATFORM_DB` are now env-driven. Cloudflare's role stays front-door
only (DNS + TLS at platform.semptify.org). `AGENTS.md` updated:
loopback is now the local-dev rule, not the only mode.

### The signature book — `/sign`
A voluntary endorsement list, like the visitor's book at a town hall.
Anyone can sign their name to the bill — it lands dark (queued) with a
private receipt, and only publishes when a steward reads it in, with an
S-number. Only name, org/town, and the optional line ever render; the
consent checkbox is required, and the optional email never publishes —
that field is the seam where OAuth storage plugs in later. Stewards get
an "Awaiting publish" queue on the page with Publish/Hold. Wired into
nav, footer, search, receipts, export, and the campaign's do-one-thing.

### Help lines, legal pages, and the Minnesota flag
`/help` is a public help directory — 911, 988, Crisis Text Line, HOME
Line, 211, SAMHSA, AA/NA/Al-Anon, the MN gambling helpline, Gamblers
Anonymous, Debtors Anonymous, Day One, LawHelpMN. Official public
channels only; no advertising, no endorsements, nobody paid to be
listed. `/legal` carries the privacy policy (what's stored, receipts,
the two functional cookies, in-memory rate limiting, R2 backups),
terms (draft not law, steward review, no PII-of-others, no ads, not
legal advice), and the license (content CC0 public domain, code MIT).
The 2024 Minnesota flag sits in the index hero kicker and the footer
next to the Semptify lockup. Footer links to Help and Legal sitewide;
the mark form's crisis line now links to the help page.



## 2026-11-14

- **`home.html` role audited + documented** (swe-2, task-baa88882):
  the legacy "Semptify Live" cover is NOT dead weight — worker.js
  serves it as the `/` origin-down fallback (>8s timeout or 5xx from
  the app origin), and every asset it needs (ssot.css, cover image)
  is worker-mirrored so it renders with the origin fully down. Not in
  `src/pages/`, not built by `build.py` — root-authored legacy page.
  Documented the contract in README + a worker.js comment + corrected
  the BUILD_STATE pending item. Retirement remains Brad's call
  (removal path recorded in README); a `bill.html` fallback is the
  likely replacement if retired.

- **Research ledger statuses refreshed to canon** (swe-2, task
  task-71e5f6fc): every row showed "checking" — stale since the
  10/23 verification pass. Statuses now mirror the canon vocabulary
  (`references.html` Quotable Shelf): 1% deposit interest →
  **verified** (Minn. Stat. §504B.178 subd. 2, checked 10/23·11/2);
  the 11 internal-model figures → **estimate** (derivation shown,
  math audit passed 10/23, awaits actuarial review). Added a
  "what the statuses mean" line to the explainer box.
  `data/bill_claims_public.json` in the app repo updated in lockstep
  (same status fields; `published:true` on the verified row only).
  Verified live: all 11 routes + 12 mapped images 200 on
  semptify.org. Flags: `gen-flux-4.png`/`mask-buck.png` are dead
  scene-gen artifacts (404, unreferenced); `bill.semptify.org`
  scene-img 404 is dormant (host references no scene assets);
  worker.js map is complete — dashboard edits remain Brad's lane.

## 2026-11-10

- **ssot.css sync + history regen** (swe-2, task
  plan-20261110-bill-mirror-run-sync-assets-py-ssot-css--efd9):
  drift check flagged root `ssot.css` stale vs app
  `static/css/ssot-design-system.css` — upstream added the
  `body.shell--dc-alt` A/B Document-Center layout block (flipped
  rail geometry). `sync_assets.py` synced the verbatim copy;
  vendored `src/bill.css` sections and all other tracked assets
  were already in lockstep. `build.py` regenerated all 11 root
  pages; only real diff = `history.html` picking up 3 new rows
  (canon 037fc2f9 + 73fb7648, site e79f555). Verified: preview on
  :8791 — `/bill/history` 200 with new rows rendered,
  `/ssot.css` 200 serving `shell--dc-alt`, IronBee console clean;
  py_compile PASS on build.py / sync_assets.py / preview_server.py;
  pytest test_ssot_architecture.py 7/8 — the one FAIL is
  pre-existing and unrelated (executive_admin/router.py:401 raw
  RedirectResponse; app-repo issue, logged as intake-eb3daf41,
  not touched). Committed 06d5b95. NOT pushed — `git push` is
  denied for headless runs.

- **Worker URL-map gap verified in prod — 6 routes serving wrong
  content** (swe-2, task
  plan-20261110-add-6-bill-routes-static-js-brain-js-to--e6ea):
  live probe of all 13 contract paths. The 5 original routes +
  `/static/js/law-linker.js` are worker-served and correct
  (`/bill` body = GitHub master `bill.html` + CF beacon injection
  — worker pulls current master, files need no push). The six new
  `/bill/*` routes are NOT in the map — they fall through to the
  Render origin and return **HTTP 200 with the app's "Setting Up
  Your Storage" onboarding page** (worse than a 404 — silent
  wrong content). `/static/js/brain.js` 404s via the origin and
  is edge-cached up to 4h. Fix = add the 7 map entries in the
  dashboard worker; exact entries + verification protocol in
  `master-repo/handoffs/2026-11-10-bill-worker-url-map.md`.
  BLOCKED: no headless path to edit the worker — cloudflare MCP
  OAuth grant lacks workers scopes, no API token on this machine,
  dashboard-only source. Needs Brad: dashboard edit, an API
  token, or MCP re-auth.

- **Worker URL-map gap FIXED — all 11 routes + brain.js + 4 images
  live** (devin interactive session, Brad-authorized wrangler OAuth):
  unblocked the headless agent's blocker — `npx wrangler login` → OAuth
  token → `PUT /workers/scripts/bill-mirror/content`. Added the 6
  `PAGES` routes, 5 `ASSETS` entries (`brain.js`, `doc-page.jpeg`,
  `loon.png`, `mn-flag.png`, `semptify-live-001-cover.jpg`), `jpeg`
  content-type. Verified: 11/11 routes 200, assets 200, AI binding
  preserved. **Silent breakage also fixed:** `doc-page.jpeg` paper
  texture, `loon.png`, `mn-flag.png` were 404ing in prod — interior
  pages had no paper texture until this deploy. POST
  `/api/voice-post` → Neon write path proven live (awaiting_review
  3→4); disclosure — probe left a `probe-do-not-post` row in the
  review queue, decline at `/admin/public-voice`. `worker.js` now
  committed to repo (was dashboard-only — the fragility that caused
  this). Docs updated: README + BUILD_GUIDE + BUILD_STATE.

## 2026-11-07

- **"Page at first light" background pass + scene-layering fix** (swe-2,
  task plan-20261106-bill-pages-new-background-design-pass-wh-e453):
  root cause of the "flat empty page" — `.paper-scene` was
  `position:fixed;inset:0;z-index:0`, which paints ABOVE all
  non-positioned content, so the whole liquid frame (header, bill nav,
  tools + options rails) rendered under the parchment and only `main`
  (z-index:1) was visible. pointer-events:none hid it from hit-testing,
  which is why DOM/computed checks looked fine. Scene now sits at
  z-index:-1 — the frame has never visibly rendered until now.
  New interior backdrop: real laid-paper texture (doc-page.jpeg,
  regenerated — the vendored file was an ice-fisherman photo, used as
  card texture on every interior page AND offered on /bill/press as
  "the paper texture") + dawn band rising at the top edge + lamp pool
  + cool water shade + loon woodcut watermark (multiply blend,
  bottom-right) + deckle edge vignette + 80s lamp-glow breathe (off
  under prefers-reduced-motion). Cover /bill: dropped the winter-snow
  cherry photo (season clash, covered the kicker), loon now blends via
  multiply (was a floating white box), flag stays, scene gets the same
  deckle edge vignette. Verified: all 11 routes + 4 scene assets 200,
  IronBee shots at 1440px + 375px, console clean, reduced-motion gate
  confirmed live. NOT pushed — awaiting Brad's visual check.
  Flagged: cherry.jpg now unreferenced (31KB dead asset — delete or
  keep for reuse); at ≤1100px body drops to display:block so rails
  stack in DOM order (tools before main) — pre-existing shell
  behavior, not touched.

- **Verification re-run post-4dbf38d/d7d4f70** (swe-2, same task —
  dispatcher re-spawn): fresh pass on current HEAD. py_compile PASS
  (3.11.9): build.py, sync_assets.py, preview_server.py; brain.js
  `node --check` PASS. build.py clean — drift gate + 11 pages; only
  diff = history.html picking up 2 new canon commits (e3612507,
  9c6061d1), regenerated + committed as usual. pytest
  test_ssot_architecture.py 8/8 PASS (68s, --no-cov; the earlier
  coverage-gate error is an artifact of running one file, not a test
  failure). guardrail_engine 9/9 PASS (86.4s). Manual: preview :8791 —
  19 route/asset probes all 200 (11 pages, brain.js, law-linker.js,
  5 images, /api/voice-posts proxy); IronBee runtime trace on
  /bill/live: every request repo-local /static/* or Google Fonts except
  the voice-posts data seam (200 via proxy), console zero messages,
  ARIA shows all four rails + live-board status text.
- **Verification resubmit pass** (swe-2, same task — desk bounce asked
  for populated verification fields): re-ran everything independently.
  py_compile PASS (3.11.9): build.py, sync_assets.py, preview_server.py.
  build.py clean — drift gate + 11 pages, zero diff vs committed root.
  pytest tests/test_ssot_architecture.py 8/8 PASS (45.32s, venv311).
  guardrail_engine 9/9 PASS (34.34s). Manual: preview_server :8791 —
  16 route/asset probes all 200; IronBee runtime trace on /bill +
  /your-voice: 130 requests all 200, every request repo-local /static/*
  or Google Fonts except the /api/voice-posts data seam (200 via proxy);
  console clean both pages. **Found + fixed:** home.html (tracked legacy
  Semptify Live cover, still served at /home.html) referenced
  /static/img/semptify-live-001-cover.jpg which was never vendored —
  404. Added to sync_assets VERBATIM_FILES and synced; now 200.
  home.html itself is a legacy non-bill page — retire decision logged
  to the queue for Brad.

- **Microsite self-containment audit + worker-map doc fix** (swe-2,
  task plan-20261105-make-bill-section-a-self-contained-micro-06d7):
  verified the site is fully self-contained — `python build.py` clean
  (drift gate + 11 pages, zero diff vs committed root), runtime trace
  on preview:8791 shows only repo-local `/static/*` + Google Fonts +
  the `/api/voice-posts` data seam (200, proxied). No app-shell
  dependency anywhere. Fixed a doc gap: `/static/js/brain.js` was not
  in the README Worker-map contract or the BUILD_STATE deploy
  prerequisite — without a worker entry it would 404 in prod and kill
  the tools/options rails. Added `.gitignore` (`__pycache__/`, `*.log`,
  `nul*`).

- **Static-asset sync automated** (swe-2): new `sync_assets.py` syncs all
  app-sourced copies (root css/js/img + the vendored ssot sections inside
  `src/bill.css`) from `../modules/app-semptify-fastapi`, with `--check`
  mode reporting drift. `build.py` runs the check before every build —
  stale assets now fail loudly instead of shipping silently (root cause
  of the northstar dark-pin / ssot fill-fix drift). Synced `ssot.css`
  (was missing the dark-mode paper-text-on-primary-fill rules).
- **Six new bill-wing spaces built** (swe-2, architecture draft §5):
  history (public version history — build.py now merges `git log` from
  this repo + the app repo's bill canon into a dated table with GitHub
  commit links), providers, lawmakers' brief, classroom kit, press room,
  myths & facts. New links added to rail_top, nav_deck, rail_tools, and
  cover panels. preview_server.py aliases added for the six routes;
  port 8791 registered in PORTS.md. Verified via build + local preview.
  NOT pushed — deploy needs the six `/bill/*` routes added to the
  Cloudflare Worker URL map first (dashboard-only source).

## 2026-11-05

- **DB pool retune shipped** — `NullPool` on `render_balanced` (#332) +
  SSOT redirect fix (#333), deploy `dep-dbmadglbedkc73bmlb6g`.
  Verified: Neon compute `ep-cold-surf` went idle/suspended 16:05Z after
  ~5.5 min quiet — first time it ever could. CU-hour burn closed.
- **Bill 301s verified on origin** — all five `/bill*` paths redirect to
  semptify.org (PR #330, carried in same deploy).
- **Decision engine live** — desk at 127.0.0.1:8600/desk; orchestrator +
  review pages retired to redirects (consolidation pass).

## 2026-11-04 → 2026-11-05 (earlier)

- Public-site audit fixes — dark-mode collisions on /bill/research,
  non-200 assets, live-draft sanitization (strikethrough, no filenames,
  no user name), anonymous API behavior (PR #326).
- Dead CSS System 3 removed — PR #329 merged.
- Module-registry workflow fixed to PR-flow — PR #328 merged.
- `render_balanced` profile deployed — embeddings + registry kept,
  Positronic Brain/Mesh/monitoring off.

## Standing notes

- Cloudflare worker cache ~5 min — "pushed but not live" is usually cache.
- App origin bill paths MUST stay 301 — a 200 there means the stale twin
  is back.
- Neon free plan: suspend is fixed 5 min, not configurable — app-side
  connection behavior is the only lever.

## 2026-11-06

- **Desk scene replaces lake on interior pages** (swe-2, Brad's spec):
  sitter's-POV oak desk — worn front edge, haphazard written-on parchment
  stack left, fresh sheet front-center, ink bottle, quill resting right,
  half-burnt candlestick back-left. Animations: candle-flame flicker +
  halo/light pulse, quill lifts and writes left→right laying a visible
  ink line that fades, dust motes. Quill write disabled ≤700px (would
  smudge behind the content column); all motion off under
  prefers-reduced-motion. Lamplit parchment pool added behind .shell-main
  for heading contrast. Cover (/bill deck) keeps the lake scene.
  Built via build.py; verified locally at 1280px + 375px, console clean.
  NOT yet pushed — awaiting Brad's visual check.
- **Parchment liquid layout replaces desk scene** (swe-2, Brad's spec):
  flat warm parchment backdrop; true-liquid frame = low-profile Semptify
  bar (header) + bill nav top rail + tools rail left + options/board rail
  right + main + footer. brain.js (root) = logic layer: auto 'On this
  page' tool anchors, board polling /api/voice-posts every 30s into rail
  + full list on /your-voice, live badge, rail status text. Board =
  existing anonymous voice-posts API (bulletin board, not chat).
  Desk scene retired to git history (9353a37). preview_server.py now
  proxies /api/* to semptify.org. Verified: grid geometry + computed
  styles at 1280px via IronBee, structure snapshot clean. NOT pushed —
  awaiting Brad's visual check.
- **MN manuscript theme applied** — lake-dawn scene (mn-lake-sunrise.jpg)
  + MN flag + loon + cherry branch + ink-bottle/quill SVG on all bill
  pages; interior pages' cards now parchment (doc-page.jpeg texture);
  UnifrakturMaguntia blackletter + Pinyon Script calligraphy added to
  head.html. New assets at repo root: mn-flag.png, loon.png, cherry.jpg,
  doc-page.jpeg. Built via build.py; verified locally — all assets 200,
  fonts load. NOT yet pushed — awaiting Brad's visual check.

## 2026-11-16 — Consolidation shipped

- **Mirror merged into bill-platform.** `src/` → `site-src/`, generated
  output → `site/`. build.py + sync_assets.py retargeted; all 11 static
  pages byte-identical to the old mirror build (verified research, myths,
  what-the-bill-changes).
- **One UI.** Same `site-src/pages/*.html` fragments now also render
  inside platform chrome (rail + smart toolbar) at their production
  paths — /bill/research, /bill/myths, /what-the-bill-changes,
  /your-voice, etc. One source file, two renderers.
- **bill-mirror Worker redeployed** (v18821483) — BASE now
  `raw.githubusercontent.com/1semptify-arch/bill-platform/main/site/`.
  Verified live: semptify.org/bill, /bill/research, /your-voice all 200.
- **Old repo retired.** semptify-bill-mirror: pointer README pushed,
  repo archived (public, read-only).
- **bill-platform made public** (required for Worker raw fetches).
  GitHub briefly flagged repo "disabled" during the visibility flip —
  transient, cleared on retry. Push 3cc8fe9 confirmed.
- Selfcheck: SELFCHECK PASS — all routes, 3 modes, toolbars, steward
  gates, boards, and the new content routes.

## 2026-11-16 — Platform deployed to Render

- **Render:** blueprint `exs-dbtoq03l550s738t84g0` → service
  `bill-platform-5873` (srv-dbtoq1lckfvc7392b8v0, free, oregon).
  Deploy LIVE on commit 08fb321 — serves at
  `https://bill-platform-5873.onrender.com`. autoSync on push to main.
- **Steward:** BILL_STEWARD_CODE set at approve time — remote steward
  mutations verified 403 without passcode. Code delivered to Brad in
  session (not stored in repo).
- **R2:** bucket `bill-platform-db` created via wrangler. Litestream is
  conditional in startCommand — app boots ephemeral until
  LITESTREAM_* creds are set (R2 API tokens are dashboard-only to create).
- **Branded URL:** `edge/` proxy worker `bill-platform-proxy` deployed
  with route `platform.semptify.org/*` → onrender origin. Route needs
  one proxied DNS record (platform CNAME → bill-platform-5873.onrender.com)
  — DNS write scope unavailable via API; single dashboard step.
- Live checks: /, /margin, /api/state 200; steward POST w/o auth 403.

## 2026-11-16 — Platform mounted at semptify.org/bill (one URL, one UI)

- **BILL_MOUNT=/bill** — platform generates /bill-prefixed links
  (views.MOUNT postprocess in page(), server strips prefix on route,
  redirects re-prefix). platform.js reads data-mount.
- **Routes repointed:** semptify.org/bill* + /your-voice* +
  /what-the-bill-changes* (+www) → bill-platform-proxy worker →
  Render origin. bill-mirror keeps /, /static/*, /gen-image*
  (main Semptify site untouched).
- **proxy.js** remaps the two non-/bill paths into the mount; keep-warm
  cron */14min keeps Render free tier awake (~720 of 750 free hrs).
- **platform.semptify.org** custom domain also live (same proxy).
- Content slugs registered bare AND under /bill/ — serves mounted and
  unmounted. /bill/live → reader redirect.
- Verified live: /bill/, /bill/margin, /bill/sign, /bill/research,
  /bill/brief, /bill/myths, /bill/history, /bill/desk all 200;
  /bill/live 303→reader. data-mount + prefixed links confirmed.
- Selfcheck +7 mounted-mode checks (subprocess instance, BILL_MOUNT set).
