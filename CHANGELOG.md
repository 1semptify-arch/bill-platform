# Changelog — Bill Platform

Plain-language record of every change, newest first. Each entry links to
its git commit for the technical detail.

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
