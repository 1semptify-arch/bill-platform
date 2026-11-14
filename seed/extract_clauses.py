#!/usr/bin/env python
"""Extract clause seed data from the canonical Turnbuchalla read-through.

Reads the generated `index.html` (built by build_platform.py from
BILL_LIVE.md — the marker-locked BILLDOC section) and emits
`seed/clauses.json` for the standalone Bill Platform.

Usage:
    python seed/extract_clauses.py [path-to-index.html]

Default input is the in-repo canon at
modules/app-semptify-fastapi/app/static/turnbuchalla/index.html.

The output is committed: the platform is standalone at runtime and never
reaches back into the module tree. Re-run this only when the canon moves.
Stdlib only.
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
CANON = REPO / "modules" / "app-semptify-fastapi" / "app" / "static" / "turnbuchalla" / "index.html"
OUT = HERE / "clauses.json"

# Drafting decisions the canon itself calls open (index.html lede line).
OPEN_CLAUSES = {"I-9", "IV-2", "IV-4"}


class BillDocParser(HTMLParser):
    """Pull title heads + clause sections out of the BILLDOC block."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_doc = False
        self.titles = []          # [(title_id, heading)]
        self.clauses = []         # [{id, title, heading, body, locked, open}]
        self._tag_stack = []
        self._cur_title = ""
        self._title_ord = 0
        self._in_title_head = False
        self._title_buf = []
        self._in_section = False
        self._clause = None
        self._in_h3 = False
        self._buf = []
        self._in_annot = False

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "")
        if tag == "p" and "title-head" in cls:
            self._in_title_head = True
            self._title_buf = []
        elif tag == "div" and "doc" in cls.split():
            self.in_doc = True
        elif tag == "section" and self.in_doc:
            self._in_section = True
            self._clause = {"id": None, "title": self._cur_title,
                            "heading": "", "body": [], "locked": False}
        elif self._in_section and tag == "span" and "secnum" in cls:
            self._buf = []
        elif self._in_section and tag == "h3":
            self._in_h3 = True
            self._buf = []
        elif self._in_section and tag in ("p", "li"):
            self._buf = []
            if tag == "p" and "dnote" in cls.split():
                self._clause["locked"] = True
            self._tag_stack.append(tag)
        elif self._in_section and tag == "a" and "annot" in cls:
            self._in_annot = True

    def handle_endtag(self, tag):
        if self._in_title_head and tag == "p":
            self._in_title_head = False
            text = " ".join("".join(self._title_buf).split())
            self._title_ord += 1
            self._cur_title = f"T{self._title_ord}"
            self.titles.append((self._cur_title, text))
            return
        if self._in_section:
            if tag == "span" and self._clause["id"] is None:
                cid = "".join(self._buf).strip()
                if cid:
                    self._clause["id"] = cid
            elif tag == "h3":
                self._in_h3 = False
                self._clause["heading"] = " ".join("".join(self._buf).split())
            elif tag in ("p", "li") and self._tag_stack:
                self._tag_stack.pop()
                text = " ".join("".join(self._buf).split())
                if text:
                    self._clause["body"].append(text)
            elif tag == "a":
                self._in_annot = False
            elif tag == "section":
                self._in_section = False
                if self._clause and self._clause["id"]:
                    body = "\n".join(self._clause["body"])
                    if re.search(r"locked", body, re.I):
                        self._clause["locked"] = True
                    self._clause["body"] = body
                    self._clause["open"] = self._clause["id"] in OPEN_CLAUSES
                    self.clauses.append(self._clause)
                self._clause = None
        if tag == "div" and self.in_doc and not self._in_section:
            # a .doc container ended; sections end before this fires
            pass

    def handle_data(self, data):
        if self._in_annot:
            return
        if self._in_title_head:
            self._title_buf.append(data)
        elif self._in_h3 or (self._in_section and (self._tag_stack or self._clause["id"] is None)):
            self._buf.append(data)


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else CANON
    if not src.exists():
        print(f"error: canon not found: {src}", file=sys.stderr)
        return 2
    html = src.read_text(encoding="utf-8")
    m = re.search(r"<!--\s*BILLDOC:START.*?-->(.*?)<!--\s*BILLDOC:END\s*-->",
                  html, re.S)
    if not m:
        print("error: BILLDOC markers not found in canon", file=sys.stderr)
        return 2
    p = BillDocParser()
    p.feed(m.group(1))
    if not p.clauses:
        print("error: no clauses extracted — canon format changed?", file=sys.stderr)
        return 2
    payload = {
        "source": str(src),
        "note": ("Generated by seed/extract_clauses.py from the marker-locked "
                 "BILLDOC block of the canonical Turnbuchalla read-through. "
                 "Canon lives in modules/app-semptify-fastapi/app/static/"
                 "turnbuchalla — regenerated, never hand-edited here."),
        "titles": [{"id": t, "heading": h} for t, h in p.titles],
        "clauses": [
            {"id": c["id"], "ord": i, "title": c["title"],
             "heading": c["heading"], "body": c["body"],
             "locked": c["locked"], "open": c["open"]}
            for i, c in enumerate(p.clauses)
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {OUT} — {len(p.titles)} titles, {len(p.clauses)} clauses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
