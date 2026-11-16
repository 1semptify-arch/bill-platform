"""Build the printable bill packet (PDF) from the canonical seed data.

Run this whenever the draft changes so the public "printed version"
link always serves the same content the site publishes:

    python build_packet.py

Outputs:
    - bill_packet.html  (print-styled, in this repo's output dir)
    - <app>/app/static/turnbuchalla/bill-packet.pdf
      (served at semptify.org/turnbuchalla/bill-packet.pdf via the
      Render origin — no worker-map entry needed)

PDF rendering uses headless Edge/Chrome (already on the machine — the
platform repo stays stdlib-only; the *tool* may shell out).
"""
import html as _html
import pathlib
import subprocess
import sys
import tempfile

import seed_data as sd

HERE = pathlib.Path(__file__).resolve().parent
# the app's static mount — semptify.org/turnbuchalla/* (Render origin)
APP_STATIC = (HERE.parent / "modules" / "app-semptify-fastapi" /
              "app" / "static" / "turnbuchalla")
HTML_OUT = HERE / "bill_packet.html"
PDF_OUT = APP_STATIC / "bill-packet.pdf"

_BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
]

e = lambda s: _html.escape(str(s or ""))

CSS = """
@page { size: Letter; margin: 0; }
* { box-sizing: border-box; }
body { font-family: Georgia, 'Times New Roman', serif; color:#1a1a1a; margin:0; font-size:11pt; line-height:1.5; }
.page { padding: 0.9in 1in; }
.cover { min-height: 9.5in; display:flex; flex-direction:column; justify-content:center; }
.kicker { font-size:10pt; letter-spacing:.25em; text-transform:uppercase; color:#666; }
h1 { font-size:30pt; font-weight:normal; margin:.3em 0 .2em; line-height:1.15; }
.subtitle { font-size:12.5pt; color:#444; font-style:italic; }
.stage { margin-top:1.6em; font-size:10.5pt; color:#555; border-top:1px solid #999; padding-top:.8em; }
.thesis { margin-top:1.2em; font-size:12pt; line-height:1.6; max-width:34em; }
.meta { margin-top:2em; font-size:9.5pt; color:#777; }
h2 { font-size:17pt; font-weight:normal; margin:0 0 .4em; border-bottom:2px solid #1a1a1a; padding-bottom:.15em; page-break-after:avoid;}
h2 .code { color:#666; font-size:12pt; }
.subtitle2 { font-size:10.5pt; color:#555; font-style:italic; margin-bottom:1em; }
.clause { margin: 0 0 1.1em; page-break-inside:avoid; }
.clause h3 { font-size:12pt; margin:0 0 .15em; }
.clause h3 .cid { color:#666; font-weight:normal; margin-right:.5em; }
.badge { display:inline-block; font-size:7.5pt; letter-spacing:.12em; text-transform:uppercase; border:1px solid #888; border-radius:2px; padding:0 .35em; vertical-align:middle; margin-left:.5em; color:#444;}
.statute { margin:.3em 0; }
.statute .lbl, .plain .lbl, .notes .lbl { font-size:8pt; letter-spacing:.14em; text-transform:uppercase; color:#777; }
.plain { margin:.2em 0 .3em; color:#333; font-style:italic; }
.notes { font-size:9.5pt; color:#444; margin:.2em 0 0; }
.notes div { margin:.1em 0; }
.refs { font-size:8.5pt; color:#888; margin-top:.25em; }
table { width:100%; border-collapse:collapse; font-size:9.5pt; margin-top:.8em; }
th { text-align:left; border-bottom:1.5px solid #1a1a1a; font-size:8.5pt; letter-spacing:.1em; text-transform:uppercase; padding:.3em .4em; }
td { border-bottom:1px solid #ccc; padding:.35em .4em; vertical-align:top; }
.status-verified { color:#1d5c2e; font-weight:bold; }
.status-estimate { color:#8a5a00; }
.glance { display:block; margin:.6em 0 1em; }
.glance .g { margin:.5em 0; page-break-inside:avoid; }
.glance .g b { display:block; font-size:11.5pt; }
.glance .g span { font-size:10pt; color:#444; }
.pb { page-break-before:always; }
.small { font-size:9pt; color:#666; }
"""


def _clause_html(c):
    notes = []
    for k, label in (("renter_note", "Renter"), ("provider_note", "Provider"),
                     ("lawmaker_note", "Lawmaker")):
        if c.get(k):
            notes.append(f'<div><span class="lbl">{label}:</span> {e(c[k])}</div>')
    return f'''<div class="clause">
      <h3><span class="cid">{e(c["id"])}</span>{e(c["heading"])}<span class="badge">{e(c.get("status",""))}</span></h3>
      <div class="statute"><span class="lbl">Statutory draft</span><br>{e(c.get("statute_text"))}</div>
      <div class="plain"><span class="lbl">Plain language</span><br>{e(c.get("plain_text"))}</div>
      {"" if not notes else '<div class="notes">' + "".join(notes) + "</div>"}
      {"" if not c.get("refs") else f'<div class="refs">Sources: {e(", ".join(c["refs"]))}</div>'}
    </div>'''


def render_html():
    out = ['<!doctype html><html><head><meta charset="utf-8">'
           '<title>Minnesota Rent Assurance &amp; Deposit Protection Act — print packet</title>'
           '<style>' + CSS + '</style></head><body>']
    out.append('<div class="page cover">')
    out.append(f'<div class="kicker">{e(sd.BILL_META["jurisdiction"])} &middot; Legislative Draft Packet</div>')
    out.append(f'<h1>{e(sd.BILL_META["short_title"])}</h1>')
    out.append(f'<div class="subtitle">{e(sd.BILL_META["working_name"])} &mdash; amends {e(sd.BILL_META["amends"])}</div>')
    out.append(f'<div class="thesis">{e(sd.BILL_META["thesis"])}</div>')
    out.append(f'<div class="stage"><b>Stage:</b> {e(sd.BILL_META["stage"])} &nbsp;&middot;&nbsp; <b>Updated:</b> {e(sd.BILL_META["updated"])}</div>')
    out.append('<div class="meta">Written in public at semptify.org/bill &middot; printed from the canonical working draft</div>')
    out.append('</div>')

    out.append('<div class="page pb"><h2>The Bill at a Glance</h2><div class="glance">')
    for p in sd.BILL_META["summary_points"]:
        out.append(f'<div class="g"><b>{e(p["label"])} &mdash; {e(p["headline"])}</b><span>{e(p["detail"])} (clause {e(p["clause_ref"])})</span></div>')
    out.append('</div><h2 style="margin-top:1.6em">Where It Stands</h2>'
               '<table><tr><th>Step</th><th>Stage</th><th>Status</th><th>Note</th></tr>')
    for j in sd.JOURNEY_STAGES:
        out.append(f'<tr><td>{j["step"]}</td><td>{e(j["name"])}</td><td>{e(j["state"])}</td><td>{e(j["note"])}</td></tr>')
    out.append('</table></div>')

    for t in sd.TITLES:
        cls = [c for c in sd.CLAUSES if c["title_num"] == t["num"]]
        if not cls:
            continue
        out.append(f'<div class="page pb"><h2><span class="code">{e(t["code"])}</span> &mdash; {e(t["name"])}</h2>')
        out.append(f'<div class="subtitle2">{e(t["subtitle"])}</div>')
        for c in cls:
            out.append(_clause_html(c))
        out.append('</div>')

    out.append('<div class="page pb"><h2>Claims Ledger &mdash; every figure, its source, its status</h2>')
    out.append('<table><tr><th>ID</th><th>Figure</th><th>Claim</th><th>Source</th><th>Status</th><th>Checked</th></tr>')
    for c in sd.CLAIMS_LEDGER:
        st = e(c["status"])
        out.append(f'<tr><td>{e(c["id"])}</td><td><b>{e(c["figure"])}</b></td>'
                   f'<td>{e(c["claim"])}<br><span class="small">{e(c["derivation"])}</span></td>'
                   f'<td>{e(c["source"])}</td><td class="status-{st}">{st}</td><td>{e(c["checked"])}</td></tr>')
    out.append('</table></div>')

    out.append('<div class="page pb"><h2>Locked Decisions</h2>'
               '<table><tr><th>#</th><th>Clause</th><th>Decision</th><th>Why</th></tr>')
    for ld in sd.LOCKED_DECISIONS:
        out.append(f'<tr><td>{ld["num"]}</td><td>{e(ld["clause"])}</td><td>{e(ld["title"])}</td><td>{e(ld["why"])}</td></tr>')
    out.append('</table><p class="small" style="margin-top:2em">Everything in this packet is a '
               'working draft, openly labeled &mdash; "locked" means decided, "modeled"/"estimate" '
               'means still under review. Live version: semptify.org/bill</p></div>')
    out.append('</body></html>')
    return "\n".join(out)


def render_pdf(html_path, pdf_path):
    for b in _BROWSERS:
        if pathlib.Path(b).exists():
            subprocess.run(
                [b, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                 f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                check=True, capture_output=True, timeout=120)
            return
    raise SystemExit("no Edge/Chrome found for headless PDF print")


if __name__ == "__main__":
    HTML_OUT.write_text(render_html(), encoding="utf-8")
    print(f"wrote {HTML_OUT}")
    PDF_OUT.parent.mkdir(parents=True, exist_ok=True)
    render_pdf(HTML_OUT, PDF_OUT)
    print(f"wrote {PDF_OUT}")
