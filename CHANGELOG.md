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
