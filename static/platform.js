/* Bill Platform client — smart-toolbar assist, mode detect, TV keys.
   Progressive enhancement only: every action also works without JS. */
(function () {
  "use strict";

  /* 1. Mode auto-detect — only when the user has never picked one.
     Narrow viewport suggests mobile; very wide suggests TV. */
  try {
    if (!document.cookie.match(/(?:^|;\s*)bp_mode=/) &&
        !window.__BP_MODE_GUESSED) {
      var w = window.innerWidth;
      var guess = w <= 700 ? "mobile" : (w >= 1700 ? "tv" : null);
      if (guess) {
        document.body.classList.remove("mode-desk");
        document.body.classList.add("mode-" + guess);
      }
    }
  } catch (e) { /* never break the page */ }

  /* 2. Selection-aware toolbar — select bill text, get "Mark selection". */
  var toolbar = document.querySelector(".toolbar");
  var clauseEl = document.querySelector("[data-clause]");
  if (toolbar && clauseEl) {
    var selBtn = null;
    document.addEventListener("selectionchange", function () {
      var sel = window.getSelection();
      var txt = sel ? sel.toString().trim() : "";
      if (txt.length > 3 && clauseEl.contains(sel.anchorNode)) {
        var cid = clauseEl.getAttribute("data-clause");
        if (!selBtn) {
          selBtn = document.createElement("a");
          selBtn.className = "tb-select";
          toolbar.appendChild(selBtn);
        }
        selBtn.textContent = "Mark selection";
        selBtn.href = "/mark?c=" + encodeURIComponent(cid) +
                      "&q=" + encodeURIComponent(txt.slice(0, 300));
        var host = clauseEl;
        host.classList.add("sel");
      } else if (selBtn && !txt) {
        selBtn.remove();
        selBtn = null;
        var marked = document.querySelector(".clause.sel");
        if (marked) marked.classList.remove("sel");
      }
    });
  }

  /* 3. TV keyboard — ←/→ walk the clause neighbours; t = back to desk. */
  if (document.body.classList.contains("mode-tv")) {
    document.addEventListener("keydown", function (e) {
      var links = document.querySelectorAll(".pnav a");
      if (e.key === "ArrowLeft" && links[0]) links[0].click();
      if (e.key === "ArrowRight" && links[1]) links[1].click();
      if (e.key === "t" || e.key === "T") {
        window.location.href = "/mode/desk?next=" +
          encodeURIComponent(location.pathname);
      }
    });
  }

  /* 4. Mark-form clause deep-link — /mark?c=… already preselects; this
     keeps the pick visible in long lists. */
  var sel = document.querySelector('select[name="clause_id"] option[selected]');
  if (sel && sel.scrollIntoView) {
    try { sel.scrollIntoView({ block: "nearest" }); } catch (e) {}
  }
})();
