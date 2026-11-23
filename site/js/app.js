/* Estimator UI: reads controls, runs OnrcEngine (2,000 draws) and draws tiles and charts. */
(function () {
  "use strict";
  var E = window.OnrcEngine, C = window.OnrcCharts, VS = window.ONRC_VERIFY_SUMMARY;
  var $ = function (id) { return document.getElementById(id); };
  var nf = new Intl.NumberFormat("ro-RO");
  var nf1 = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 1 });

  var t0 = performance.now();
  var M = E.init(window.ONRC_INPUTS);
  var initMs = performance.now() - t0;

  // Mondays offered by the start-date slider: 23.11.2026 + 7k days
  var START0 = Date.UTC(2026, 10, 23);
  function startIso(k) { return new Date(START0 + k * 7 * 86400000).toISOString().slice(0, 10); }
  function startIdx(iso) { var p = iso.split("-"); return Math.round((Date.UTC(+p[0], +p[1] - 1, +p[2]) - START0) / (7 * 86400000)); }

  var PRESETS = [
    { id: "sq", label: "Fără măsuri", s: {}, note: "Status quo din raport [C42, C59, C60]" },
    { id: "oug", label: "Proiectul de OUG", s: { oug: "central" }, note: "Varianta centrală [C43]" },
    { id: "p3", label: "Pachet P3", s: { oug: "central", oug_extended: true, art3: 0.30, staff_fte: 15 }, note: "OUG extins + 40% din posturile vacante finanțate [C52]" },
    { id: "p4", label: "Pachet P4", s: { caen_auto: true, stagger: true }, note: "Conversie CAEN + eșalonare [C53]" },
    { id: "p5", label: "Pachet P5", s: { oug: "central", oug_extended: true, art3: 0.30, caen_auto: true, stagger: true, triage: true }, note: "Pachetul minim realist [C54]" },
    { id: "c80", label: "Val CAEN 80%", s: { caen: 0.8 }, note: "80% din 902.243 de cereri CAEN [C94]" },
    { id: "c80a", label: "CAEN 80% + conversie", s: { caen: 0.8, caen_auto: true }, note: "[C95]" }
  ];
  var OUG_HINT = {
    none: "Fără proiect.",
    redus: "5 posturi nete × 20 de dosare pe zi, fără transfer prin Art. III.",
    central: "15 posturi nete × 25 de dosare pe zi (375 pe zi), plus transferul a 25% din munca de dizolvare ANAF (Art. III). Expiră la 08.01.2028.",
    ridicat: "30 de posturi nete × 30 de dosare pe zi (900 pe zi), plus transferul a 50% din munca de dizolvare ANAF."
  };

  var state = E.withDefaults({});

  /* ---------------------------------------------------------------- formatting */
  function rhe(v) { // round half to even (Python round), as the report rounds 102.5 -> 102
    var f = Math.floor(v), d = v - f;
    if (Math.abs(d - 0.5) < 1e-9) return f % 2 === 0 ? f : f + 1;
    return Math.round(v);
  }
  function zile(n) {
    if (n === 1) return "1 zi";
    var r = n % 100;
    return nf.format(n) + ((r === 0 && n > 0) || r >= 20 ? " de zile" : " zile");
  }
  function dayVal(v) {
    if (!isFinite(v)) return { big: "peste", unit: "orizontul de calcul", txt: "peste orizont" };
    if (v <= 3) return { big: "≤3", unit: "zile", txt: "≤3 zile" };
    var n = rhe(v), z = zile(n);
    return { big: nf.format(n), unit: z.slice(nf.format(n).length + 1), txt: z };
  }
  function rangeTxt(q) {
    var lo = !isFinite(q[0]) ? "peste orizont" : q[0] <= 3 ? "≤3" : nf.format(rhe(q[0]));
    var hi = !isFinite(q[2]) ? "peste orizont" : q[2] <= 3 ? "≤3 zile" : zile(rhe(q[2]));
    return "interval 80%: " + lo + " – " + hi;
  }
  function months(v) { return isFinite(v) && v > 3 ? "≈ " + nf1.format(v / 30.44) + " luni" : ""; }
  function dmy(iso) { var p = iso.split("-"); return p[2] + "." + p[1] + "." + p[0]; }

  /* ---------------------------------------------------------------- controls */
  function setSeg(id, val) {
    Array.prototype.forEach.call($(id).querySelectorAll("button"), function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.v === String(val)));
    });
  }
  function syncControls() {
    $("in_pct").value = state.in_pct; $("cap_pct").value = state.cap_pct;
    $("in_pct_v").textContent = (state.in_pct > 0 ? "+" : state.in_pct < 0 ? "−" : "") + Math.abs(state.in_pct) + "%";
    $("cap_pct_v").textContent = (state.cap_pct > 0 ? "+" : state.cap_pct < 0 ? "−" : "") + Math.abs(state.cap_pct) + "%";
    setSeg("caen", state.caen === "motor" ? "motor" : String(+state.caen));
    setSeg("oug", state.oug);
    $("oug_hint").textContent = state.oug_extended ? OUG_HINT[state.oug].replace(" Expiră la 08.01.2028.", " Prelungit după 08.01.2028.") : OUG_HINT[state.oug];
    $("oug_extended").checked = !!state.oug_extended;
    $("oug_extended").disabled = state.oug === "none";
    $("caen_auto").checked = !!state.caen_auto;
    $("stagger").checked = !!state.stagger;
    $("triage").checked = !!state.triage;
    $("staff_fte").value = state.staff_fte;
    $("staff_fte_v").textContent = state.staff_fte ? "+" + state.staff_fte + " posturi (" + nf.format(state.staff_fte * 25) + " dosare/zi)" : "0";
    $("start").value = startIdx(state.start);
    $("start_v").textContent = dmy(state.start);
    $("art3").value = state.art3 === null ? "" : String(state.art3);
    var cur = JSON.stringify(state);
    Array.prototype.forEach.call($("presets").querySelectorAll("button"), function (b) {
      var p = PRESETS.filter(function (x) { return x.id === b.dataset.id; })[0];
      b.setAttribute("aria-pressed", String(JSON.stringify(E.withDefaults(p.s)) === cur));
    });
  }
  function bind() {
    PRESETS.forEach(function (p) {
      var b = document.createElement("button");
      b.type = "button"; b.dataset.id = p.id; b.textContent = p.label; b.title = p.note;
      b.addEventListener("click", function () { state = E.withDefaults(p.s); changed(); });
      $("presets").appendChild(b);
    });
    $("in_pct").addEventListener("input", function (e) { state.in_pct = +e.target.value; changed(); });
    $("cap_pct").addEventListener("input", function (e) { state.cap_pct = +e.target.value; changed(); });
    $("staff_fte").addEventListener("input", function (e) { state.staff_fte = +e.target.value; changed(); });
    $("start").addEventListener("input", function (e) { state.start = startIso(+e.target.value); changed(); });
    ["oug_extended", "caen_auto", "stagger", "triage"].forEach(function (id) {
      $(id).addEventListener("change", function (e) { state[id] = e.target.checked; changed(); });
    });
    $("art3").addEventListener("change", function (e) { state.art3 = e.target.value === "" ? null : +e.target.value; changed(); });
    $("caen").addEventListener("click", function (e) {
      var v = e.target.dataset && e.target.dataset.v; if (!v) return;
      state.caen = v === "motor" ? "motor" : +v; changed();
    });
    $("oug").addEventListener("click", function (e) {
      var v = e.target.dataset && e.target.dataset.v; if (!v) return;
      state.oug = v; if (v === "none") state.oug_extended = false; changed();
    });
    $("reset").addEventListener("click", function () { state = E.withDefaults({}); changed(); });
    var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(draw, 120); });
  }

  /* ---------------------------------------------------------------- URL hash (shareable settings) */
  var KEYS = { in_pct: "cereri", cap_pct: "capacitate", caen: "caen", caen_auto: "conversie", stagger: "esalonare",
    oug: "oug", oug_extended: "prelungit", art3: "art3", staff_fte: "personal", triage: "triaj", start: "start" };
  function toHash() {
    var d = E.withDefaults({}), parts = [];
    for (var k in KEYS) if (state[k] !== d[k]) parts.push(KEYS[k] + "=" + (typeof state[k] === "boolean" ? (state[k] ? 1 : 0) : state[k]));
    var h = parts.length ? "#" + parts.join("&") : " ";
    try { if (location.hash !== h) history.replaceState(null, "", h === " " ? location.pathname + location.search : h); } catch (e) { /* sandboxed or file:// edge cases */ }
  }
  function fromHash() {
    var s = {}, h = location.hash.replace(/^#/, "");
    if (!h) return;
    h.split("&").forEach(function (kv) {
      var p = kv.split("="), key = null;
      for (var k in KEYS) if (KEYS[k] === p[0]) key = k;
      if (!key || p.length < 2) return;
      var v = decodeURIComponent(p[1]);
      if (["caen_auto", "stagger", "oug_extended", "triage"].indexOf(key) >= 0) s[key] = v === "1";
      else if (key === "caen") s[key] = v === "motor" ? "motor" : +v;
      else if (key === "oug") s[key] = E.OUG_VARIANTS[v] ? v : "none";
      else if (key === "start") s[key] = /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : "2027-01-04";
      else if (key === "art3") s[key] = v === "null" ? null : +v;
      else s[key] = +v;
    });
    state = E.withDefaults(s);
  }

  /* ---------------------------------------------------------------- compute + render */
  var baseCache = {}, last = null, pending = false;
  function baseKey(s) { return [s.in_pct, s.cap_pct, s.caen].join("|"); }
  function compute() {
    var t = performance.now();
    var r = E.run(M, state);
    var measures = E.hasMeasures(state), b;
    if (measures) {
      var key = baseKey(state);
      b = baseCache[key] || (baseCache[key] = E.run(M, E.noMeasures(state)));
      if (Object.keys(baseCache).length > 12) baseCache = {};
    }
    var S = E.summarize(M, r, measures ? b : null);
    var SB = measures ? E.summarize(M, b, null) : null;
    last = { S: S, SB: SB, measures: measures, ms: performance.now() - t, beyond: r.beyond + (measures ? b.beyond : 0) };
    draw();
  }
  function changed() {
    syncControls(); toHash();
    if (pending) return;
    pending = true;
    setTimeout(function () { pending = false; compute(); }, 0);
  }

  function tile(kicker, p, def, extra) {
    var d = dayVal(p.q[1]);
    var h = '<div class="tile"><div class="kicker">' + kicker + '</div>' +
      '<div class="big">' + d.big + ' <small>' + d.unit + '</small></div>' +
      '<div class="rng">' + rangeTxt(p.q) + (months(p.q[1]) ? " · mediana " + months(p.q[1]) : "") + '</div>';
    if (p.gain !== undefined && isFinite(p.gain)) {
      var g = rhe(p.gain);
      h += '<div class="gain">' + (g > 0 ? "<b>cu " + zile(g) + " mai puțin</b> decât fără măsuri"
        : g < 0 ? "<b>cu " + zile(-g) + " mai mult</b> decât fără măsuri" : "practic la fel ca fără măsuri") + '</div>';
    }
    if (extra) h += '<div class="def">' + extra + '</div>';
    h += '<div class="def">' + def + '</div></div>';
    return h;
  }

  function draw() {
    if (!last) return;
    var S = last.S, SB = last.SB;
    $("tiles").innerHTML =
      tile("Dosar depus la 30.06.2027", S.mid2027, "Mijlocul lui 2027, ca în raport [C59].") +
      tile("Vârful așteptării", S.peak, "Cea mai lungă așteptare din fiecare variantă, nov. 2026–iun. 2028 [C60].") +
      tile("Dosar depus la 30.06.2028", S.june2028, "Ultima zi a orizontului [C42].",
        "Stoc la 30.06.2028: ≈ " + nf.format(Math.round(S.stockJune2028[1] / 1000) * 1000) + " dosare-echivalent");
    $("mini").innerHTML = [["30.06.2027", S.mid2027], ["vârf", S.peak], ["30.06.2028", S.june2028]].map(function (x) {
      return "<div>" + x[0] + "<b>" + dayVal(x[1].q[1]).txt + "</b></div>"; }).join("");
    $("warn").innerHTML = last.beyond > 0
      ? '<p class="warn">În unele variante, un dosar depus înainte de iunie 2028 nu ar fi soluționat nici până în iunie 2030, finalul calendarului de calcul. Valorile marcate „peste orizont” sunt doar limite de jos; motorul Python oprește calculul în acest caz.</p>' : "";
    var dates = S.weekly.map(function (w) { return w.date; });
    var marker = last.measures ? { date: state.start, label: "start măsuri " + dmy(state.start) } : null;
    var lw = '<span><i></i>' + (last.measures ? "Cu măsurile alese, mediană" : "Mediană") + '</span><span><i class="band"></i>80% dintre variante</span>' +
      (last.measures ? '<span><i class="base"></i>Fără măsuri, aceleași ipoteze</span>' : "");
    $("legend_wait").innerHTML = lw; $("legend_stock").innerHTML = lw;
    C.bandChart({
      svg: $("svg_wait"), tip: $("tip_wait"), dates: dates, minMax: 30,
      q: S.weekly.map(function (w) { return w.wait; }),
      base: SB ? SB.weekly.map(function (w) { return w.wait[1]; }) : null,
      fmtY: function (v) { return nf.format(v); }, marker: marker,
      labelMain: last.measures ? "cu măsuri" : "mediană", labelBase: "fără măsuri",
      fmtTip: function (i, tip) { tipRows(tip, "Depus luni " + dmy(dates[i]), S.weekly[i].wait, SB && SB.weekly[i].wait[1], dayTxt); }
    });
    C.bandChart({
      svg: $("svg_stock"), tip: $("tip_stock"), dates: dates, height: window.innerWidth < 600 ? 210 : 240, minMax: 1000,
      q: S.weekly.map(function (w) { return w.stock; }),
      base: SB ? SB.weekly.map(function (w) { return w.stock[1]; }) : null,
      fmtY: function (v) { return v >= 1000 ? nf.format(v / 1000) + " mii" : nf.format(v); }, marker: marker,
      labelMain: last.measures ? "cu măsuri" : "mediană", labelBase: "fără măsuri",
      fmtTip: function (i, tip) { tipRows(tip, "Luni " + dmy(dates[i]), S.weekly[i].stock, SB && SB.weekly[i].stock[1], stockTxt); }
    });
    $("status").textContent = "2.000 de variante, calculate în browser în " + Math.round(last.ms) + " ms (pregătire " + Math.round(initMs) +
      " ms)." + (VS ? " Verificat față de motorul Python pe " + VS.n_settings + " de setări: diferență maximă " + nf1.format(VS.max_abs_diff_days) + " zile." : "");
  }
  function dayTxt(v) { return dayVal(v).txt; }
  function stockTxt(v) { return nf.format(Math.round(v / 100) * 100); }
  function tipRows(tip, title, q, base, fmt) {
    var h = document.createElement("div"); h.style.fontWeight = "600"; h.textContent = title; tip.appendChild(h);
    function row(cls, label, val) {
      var d = document.createElement("div"), k = document.createElement("span"), b = document.createElement("b");
      if (cls !== null) { k.className = "k" + (cls ? " " + cls : ""); d.appendChild(k); }
      b.textContent = val; d.appendChild(b); d.appendChild(document.createTextNode(" " + label)); tip.appendChild(d);
    }
    row("", last.measures ? "cu măsuri (mediană)" : "mediană", fmt(q[1]));
    row(null, "interval 80%", fmt(q[0]) + " – " + fmt(q[2]));
    if (base !== null && base !== undefined) row("base", "fără măsuri", fmt(base));
  }

  fromHash();
  bind();
  // mobile: show the sticky summary only while the controls are on screen
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (en) { $("mini").classList.toggle("on", en[0].isIntersecting); }, { threshold: 0.05 }).observe($("controls"));
  }
  syncControls();
  compute();
  document.documentElement.setAttribute("data-ready", "1");
})();
