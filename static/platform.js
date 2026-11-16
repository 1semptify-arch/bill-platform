/* Bill Platform Brain — UI/logic layer:
   1. First-visit viewport mode suggestion (mobile vs desktop vs TV)
   2. Multi-clause Selection Detection -> Context-Aware Smart Toolbar actions
   3. Live 3-source Funding Braid & stress-test reactivity
   4. TV / Presentation keyboard & remote navigation (←/→/Space/1-8/F/Esc) */
(function () {
  "use strict";

  /* URL mount prefix (e.g. "/bill" at semptify.org/bill) — empty at root. */
  var M = document.documentElement.getAttribute("data-mount") || "";

  /* 1. Auto screen mode — follows the viewport live while bp_mode=auto
     (default). Picking Desktop / TV / Mobile pins that mode; "Auto"
     returns control to the viewport. */
  try {
    var mqMobile = window.matchMedia("(max-width: 720px)");
    var mqTV = window.matchMedia("(min-width: 1820px)");
    function applyAutoMode() {
      var b = document.body;
      if (!b.hasAttribute("data-mode-auto") || b.classList.contains("is-stage")) return;
      var m = mqMobile.matches ? "mobile" : (mqTV.matches ? "tv" : "desk");
      b.classList.remove("mode-desk", "mode-tv", "mode-mobile");
      b.classList.add("mode-" + m);
    }
    applyAutoMode();
    if (mqMobile.addEventListener) {
      mqMobile.addEventListener("change", applyAutoMode);
      mqTV.addEventListener("change", applyAutoMode);
    } else {
      window.addEventListener("resize", applyAutoMode);
    }
  } catch (e) {}

  /* 2. Multi-clause Selection Detection -> Context-Aware Smart Toolbar */
  var selSlot = document.getElementById("tbSelection");
  function clearSelectionUI() {
    if (selSlot) {
      selSlot.innerHTML = "";
      selSlot.hidden = true;
    }
    document.querySelectorAll(".clause.sel, .clause-focus.sel").forEach(function (el) {
      el.classList.remove("sel");
    });
  }

  function findClauseContainer(node) {
    if (!node) return null;
    var el = node.nodeType === 1 ? node : node.parentElement;
    return el && el.closest ? el.closest("[data-clause]") : null;
  }

  if (selSlot) {
    document.addEventListener("selectionchange", function () {
      var sel = window.getSelection();
      var txt = sel ? sel.toString().trim() : "";
      var host = sel && sel.anchorNode ? findClauseContainer(sel.anchorNode) : null;
      if (txt.length > 3 && host) {
        var cid = host.getAttribute("data-clause");
        clearSelectionUI();
        host.classList.add("sel");
        var base = "/mark?c=" + encodeURIComponent(cid) +
                   "&q=" + encodeURIComponent(txt.slice(0, 300));
        selSlot.innerHTML =
          '<a class="tb-select" href="' + base + '">Mark selection (' + cid + ')</a>' +
          '<a class="tb-select" href="' + base + '&kind=edit">Propose edit (' + cid + ')</a>';
        selSlot.hidden = false;
      } else if (!txt) {
        clearSelectionUI();
      }
    });
  }

  /* 3. Live 3-Source Funding Braid Calculator (works on /calculator and TV Slide 4) */
  var rentRange = document.getElementById("rentRange");
  var rentInput = document.getElementById("rentInput");
  var unitsInput = document.getElementById("unitsInput");
  var m1prInput = document.getElementById("m1prInput");

  function fmtMoney(v) {
    return "$" + Number(v).toFixed(2);
  }

  function recomputeBraid() {
    if (!rentInput) return;
    var rent = Math.max(400, Math.min(10000, parseFloat(rentInput.value) || 1300));
    var units = unitsInput ? Math.max(1, Math.min(500000, parseInt(unitsInput.value, 10) || 1)) : 1;
    var m1pr = m1prInput ? !!m1prInput.checked : true;

    var floatMo = Math.round(((rent * 0.03) / 12) * 100) / 100;
    var baseTotal = Math.round((rent * (15.33 / 1300)) * 100) / 100;
    var rem = Math.max(0, baseTotal - floatMo);
    var renterMo = Math.round((rem / 2) * 100) / 100;
    var landlordMo = Math.round((baseTotal - floatMo - renterMo) * 100) / 100;
    var fraudMo = Math.round((rent * (21.23 / 1300)) * 100) / 100;
    var recMo = Math.round((rent * (30.0 / 1300)) * 100) / 100;
    var tenantIntYr = Math.round((rent * 0.01) * 100) / 100;
    var landlordYr = Math.round((landlordMo * 12 * units) * 100) / 100;
    var unitYears = (6500 / Math.max(1, landlordMo * 12)).toFixed(1);

    var setHtml = function (id, html) {
      var el = document.getElementById(id);
      if (el) el.innerHTML = html;
    };
    var isStage = document.body.classList.contains("is-stage");
    setHtml("valFloat", fmtMoney(floatMo) + (isStage ? "/mo" : "<span>/unit/mo</span>"));
    setHtml("valRenter", fmtMoney(renterMo) + (isStage ? "/mo" : "<span>/unit/mo</span>"));
    setHtml("valLandlord", fmtMoney(landlordMo) + (isStage ? "/mo" : "<span>/unit/mo</span>"));
    setHtml("valTotal", fmtMoney(baseTotal) + (isStage ? "/mo" : "<span>/unit/mo</span>"));
    setHtml("valTenantInt", fmtMoney(tenantIntYr) + "/yr");
    setHtml("valUnits", String(units));
    setHtml("valLandlordYr", "$" + landlordYr.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + "/yr");
    setHtml("valUnitYears", unitYears);
    setHtml("stBase", fmtMoney(baseTotal) + " / mo");
    setHtml("stFraud", fmtMoney(fraudMo) + " / mo");
    setHtml("stRecession", fmtMoney(recMo) + " / mo");

    var oopEl = document.getElementById("valOop");
    if (oopEl) {
      oopEl.textContent = m1pr
        ? "$0.00 / mo new out-of-pocket (covered via monthly M1PR tax-credit advance)"
        : fmtMoney(renterMo) + " / mo direct disclosed pool line (household above $77,570 M1PR cap)";
    }
  }

  function syncBraidUrl() {
    try {
      if (!rentInput || !window.history || !history.replaceState) return;
      var p = new URLSearchParams();
      p.set("rent", rentInput.value);
      if (unitsInput) p.set("units", unitsInput.value);
      if (m1prInput && !m1prInput.checked) p.set("m1pr", "0");
      history.replaceState(null, "", location.pathname + "?" + p.toString());
    } catch (e) {}
  }

  if (rentRange && rentInput) {
    rentRange.addEventListener("input", function () {
      rentInput.value = rentRange.value;
      recomputeBraid(); syncBraidUrl();
    });
    rentInput.addEventListener("input", function () {
      rentRange.value = rentInput.value;
      recomputeBraid(); syncBraidUrl();
    });
  }
  if (unitsInput) unitsInput.addEventListener("input", function () { recomputeBraid(); syncBraidUrl(); });
  if (m1prInput) m1prInput.addEventListener("change", function () { recomputeBraid(); syncBraidUrl(); });

  /* 4. TV / Presentation keyboard & remote D-pad controls */
  if (document.body.classList.contains("mode-tv") || document.body.classList.contains("is-stage")) {
    document.addEventListener("keydown", function (e) {
      var tag = (e.target && e.target.tagName) || "";
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      var prev = document.getElementById("prevSlide") || document.querySelector(".pnav a:first-child");
      var next = document.getElementById("nextSlide") || document.querySelector(".pnav a:last-child");

      if (e.key === "ArrowLeft" && prev) {
        e.preventDefault();
        prev.click();
      } else if ((e.key === "ArrowRight" || e.key === " ") && next) {
        e.preventDefault();
        next.click();
      } else if (e.key >= "1" && e.key <= "8" && document.body.classList.contains("is-stage")) {
        window.location.href = M + "/present?s=" + e.key;
      } else if (e.key === "f" || e.key === "F") {
        if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
          document.documentElement.requestFullscreen().catch(function () {});
        } else if (document.exitFullscreen) {
          document.exitFullscreen().catch(function () {});
        }
      } else if (e.key === "Escape" || e.key === "t" || e.key === "T") {
        window.location.href = M + "/mode/desk?next=" + encodeURIComponent(M + "/");
      }
    });
  }
})();
