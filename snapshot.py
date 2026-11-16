#!/usr/bin/env python
"""snapshot.py — offline reference copy of the Bill Platform.

Crawls the running local server, saves every page as static HTML into
`reference/`, rewrites internal links to relative .html files so the
copy browses from file:// with no server, and pulls /static/* assets.

    python snapshot.py                # crawls 127.0.0.1:8093
    python snapshot.py --port 18093   # other port

Stdlib only. The snapshot is a *read-only copy* — forms and POSTs don't
work offline, by design (it's for reference, not a second platform).
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import db  # noqa: E402
OUT = HERE / "reference"

PAGES = [
    "/", "/desk", "/bill", "/margin", "/intake", "/requests",
    "/positions", "/claims", "/decisions", "/editions", "/changes",
    "/changes?s=proposed", "/changes?s=incorporated",
    "/changes?s=declined", "/changes?s=retracted",
    "/search", "/track", "/teach", "/campaign", "/packet",
    "/calculator", "/mark", "/sign", "/help", "/legal", "/steward",
]
PAGES += [f"/clause/{r['id']}" for r in db.clauses()]
PAGES += [f"/present?s={i}" for i in range(1, 9)]

STATIC = ["platform.css", "platform.js", "logo.svg", "mn-flag.svg",
          "favicon.png", "logo.png", "logo-512.png"]


def fname(route: str) -> str:
    """Route -> flat local filename."""
    route = route.split("#")[0]
    if route == "/":
        return "index.html"
    path, _, query = route.lstrip("/").partition("?")
    name = path.replace("/", "-") or "index"
    if query:
        for kv in query.split("&"):
            k, _, v = kv.partition("=")
            if k in ("s",) and v:          # changes filter / slide number
                name += f"-{k}{v}"
    return name + ".html"


def rewrite(html: str) -> str:
    """Make internal absolute links relative for file:// browsing."""
    def _link(m):
        href = m.group(1)
        if href.startswith("/static/"):
            return f'href="{href.lstrip("/")}"'
        if href.startswith("/api/") or href.startswith("/mode/"):
            return 'href="#"'
        if href.startswith("/"):
            frag = ""
            if "#" in href:
                href, frag = href.split("#", 1)
                frag = "#" + frag
            if href == "/tv":
                href = "/present?s=1"
            base = href.split("?")[0]
            if base in {"/mark", "/track", "/requests", "/calculator",
                        "/bill", "/changes", "/search"}:
                return f'href="{fname(base)}{frag}"'
            return f'href="{fname(href)}{frag}"'
        return m.group(0)

    html = re.sub(r'href="([^"]+)"', _link, html)
    html = re.sub(r'src="(/static/[^"]+)"',
                  lambda m: f'src="{m.group(1).lstrip("/")}"', html)
    # POST forms can't work offline — point them at a note instead of 404
    html = html.replace('action="/api/', 'action="#offline-')
    return html


def fetch(base: str, route: str) -> bytes | None:
    try:
        with urllib.request.urlopen(base + route, timeout=15) as r:
            if r.status == 200:
                return r.read()
    except Exception as e:
        print(f"  !! {route}: {e}")
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8093)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    base = f"http://{args.host}:{args.port}"

    (OUT / "static").mkdir(parents=True, exist_ok=True)
    ok = fail = 0
    for route in PAGES:
        raw = fetch(base, route)
        if raw is None:
            fail += 1
            continue
        (OUT / fname(route)).write_bytes(rewrite(raw.decode("utf-8")).encode("utf-8"))
        ok += 1
    for a in STATIC:
        raw = fetch(base, f"/static/{a}")
        if raw:
            (OUT / "static" / a).write_bytes(raw)

    (OUT / "README.txt").write_text(
        "Offline reference snapshot of the Bill Platform.\n"
        "Open index.html in a browser — all internal links work locally.\n"
        "Forms don't submit offline (read-only copy, by design).\n"
        "Regenerate anytime: python snapshot.py (needs the server on :8093).\n",
        encoding="utf-8")
    print(f"snapshot: {ok} pages -> {OUT}  ({fail} failed)")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
