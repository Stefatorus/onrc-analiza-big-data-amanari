/* Audit page: renders verification.json, report refs and a live in-browser re-run of the named scenarios. */
(function () {
  "use strict";
  var V = window.ONRC_VERIFY, R = window.ONRC_REFS, I = window.ONRC_INPUTS, E = window.OnrcEngine;
  var $ = function (id) { return document.getElementById(id); };
  var nf = new Intl.NumberFormat("ro-RO"), nf1 = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 1 });
  var nf2 = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
  function esc(s) { return String(s === null || s === undefined ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function d(v) { return v === null || v === undefined ? "—" : !isFinite(v) ? "peste orizont" : nf1.format(Math.round(v * 10) / 10); }
  function dz(v) { return v !== null && v !== undefined && isFinite(v) && v <= 3 ? "≤3" : d(v); }
  function q3(a) { return a ? a.map(dz).join(" / ") : "—"; }
  function okb(b) { return b ? '<span class="ok">✓</span>' : '<span class="fail">✗</span>'; }
  function dmy(iso) { var p = iso.split("-"); return p[2] + "." + p[1] + "." + p[0]; }
  function table(id, head, rows, numCols) {
    numCols = numCols || [];
    var h = "<thead><tr>" + head.map(function (x, i) { return '<th' + (numCols.indexOf(i) >= 0 ? ' class="n"' : "") + ">" + x + "</th>"; }).join("") + "</tr></thead><tbody>";
    h += rows.map(function (r) {
      var cls = r.cls ? ' class="' + r.cls + '"' : ""; var cells = r.cells || r;
      return "<tr" + cls + ">" + cells.map(function (c, i) { return "<td" + (numCols.indexOf(i) >= 0 ? ' class="n"' : "") + ">" + c + "</td>"; }).join("") + "</tr>";
    }).join("");
    $(id).innerHTML = h + "</tbody>";
  }
  var claim = {}; R.claims.forEach(function (c) { claim[c.id] = c; });

  /* ---------------- summary */
  var nClaims = V.claims.rows.length, okClaims = V.claims.rows.filter(function (c) { return c.ok; }).length;
  var nPub = V.published_check.rows.length, okPub = V.published_check.rows.filter(function (c) { return c.ok; }).length;
  var maxStock = Math.max.apply(null, V.results.map(function (r) { return r.max_diff_stock_weekly || 0; }));
  $("summary").innerHTML = "<strong>" + (V.all_ok && V.claims.ok && V.published_check.ok ? "Toate verificările trec." : "Unele verificări nu trec.") +
    "</strong> Motor JS = motor Python pe " + V.n_settings + " de setări (diferență maximă " + d(V.max_abs_diff_days) +
    " zile). Afirmațiile din raport refăcute: " + okClaims + "/" + nClaims + ". Generat la " + esc(V.generated) + ".";
  table("t_summary", ["Verificare", "Rezultat", "Detalii"], [
    ["Motorul din browser față de motorul Python", (V.all_ok ? '<span class="ok">trece</span>' : '<span class="fail">nu trece</span>'),
      V.n_settings + " setări × 2.000 de variante; diferență maximă <strong>" + d(V.max_abs_diff_days) + " zile</strong> (prag 0,5). <a href=\"#verificare\">Tabel</a>"],
    ["Fișierele de rezultate ale raportului, refăcute", (V.published_check.ok ? '<span class="ok">trece</span>' : '<span class="fail">nu trece</span>'),
      okPub + " din " + nPub + " valori publicate refăcute exact din motor (grilă, CAEN, OUG, pachete)."],
    ["Afirmațiile din raport, refăcute în JavaScript", (V.claims.ok ? '<span class="ok">trece</span>' : '<span class="fail">nu trece</span>'),
      okClaims + " din " + nClaims + " valori (C42, C43, C44, C52–C54, C59–C63, C94, C95). <a href=\"#afirmatii\">Tabel</a>"],
    ["Mecanismul cozii pe trecut [C96]", '<span class="badge pass">PASS</span>', "Eroare medie 1,4–2,5 zile, corelație 0,98–0,99, 3 origini. <a href=\"#backtest\">Detalii</a>"],
    ["Prognoza doar cu ce se știa atunci [C97]", '<span class="badge pass">PASS</span>', "Eroare medie 4,8–11,5 zile; subestimează când cererea crește brusc."],
    ["Ritmul de soluționare, în timp real [C70]", '<span class="badge pass">PASS</span>', "Eroare absolută medie ≈5,5% pe 9 ferestre de 4 săptămâni."]
  ]);

  /* ---------------- live check in this browser */
  function live() {
    var M, named = V.results.filter(function (r) { return r.group === "scenarii numite"; }), i = 0, maxd = 0, bad = 0, t0 = performance.now();
    try { M = E.init(I); } catch (e) { $("live_txt").textContent = "Nu am putut porni motorul: " + e; return; }
    function step() {
      if (i >= named.length) {
        $("live_txt").innerHTML = "Motorul a rulat acum în browserul dumneavoastră cele <strong>" + named.length +
          " scenarii numite</strong> (status quo, variantele OUG, Art. III, pachetele P3–P5), cu câte 2.000 de variante, în " +
          Math.round(performance.now() - t0) + " ms. Diferența maximă față de cifrele motorului Python: <strong>" + d(maxd) + " zile</strong>" +
          (bad ? ' <span class="fail">(' + bad + " diferențe)</span>." : ' <span class="ok">✓</span>.');
        return;
      }
      var r = named[i++], run = E.run(M, r.settings), base = E.run(M, E.noMeasures(r.settings)), S = E.summarize(M, run, base);
      [["mid2027", S.mid2027.q], ["peak", S.peak.q], ["june2028", S.june2028.q]].forEach(function (p) {
        p[1].forEach(function (v, k) { var dd = Math.abs(v - r.py[p[0]][k]); if (dd > maxd) maxd = dd; if (dd > 0.5) bad++; });
      });
      var g = Math.abs(S.june2028.gain - r.py.gain_june2028); if (isFinite(g) && g > maxd) maxd = g;
      $("live_txt").textContent = "Rulez scenariul " + i + " din " + named.length + "…";
      setTimeout(step, 0);
    }
    setTimeout(step, 50);
  }

  /* ---------------- parameters */
  var PN = {
    stoc_initial: ["Stocul la start (18.11.2026), în dosare", "derivat: stocul MJ la 06.11 + intrări − ieșiri BERC"],
    flux_zilnic_recurent: ["Cereri recurente pe zi lucrătoare", "estimat din noiembrie 2026, fără valul rezidual"],
    crestere_anuala_flux: ["Creșterea anuală a fluxului", "ipoteză"],
    pondere_caen_iesiri: ["Ponderea CAEN în soluționări", "măsurat pe eșantion de buletine [C50] + interval"],
    dosare_caen_suplimentare: ["Valul CAEN suplimentar, ian.–apr. 2027", "ipoteză (nota MJ: 902.243 încă așteptate)"],
    efort_caen: ["Munca unui dosar CAEN față de unul standard", "ipoteză"],
    populatie_capital: ["Firme care trebuie să majoreze capitalul", "nota MJ + bilanțuri MF"],
    proportie_reducere: ["Cota care depune devreme, cu reducere", "ipoteză"],
    conformare_ulterioara: ["Conformarea ulterioară", "ipoteză"],
    depuneri_separate_ulterioare: ["Cota depunerilor separate", "ipoteză"],
    efort_capital: ["Munca unui dosar de capital", "ipoteză"],
    dosare_defensive: ["Depuneri defensive (fiscal)", "ipoteză"],
    cazuri_anaf: ["Cazuri de dizolvare ANAF", "nota MJ (422.093 de entități) + ipoteză"],
    fractie_anaf_capacitate_comuna: ["Cota ANAF care folosește aceeași capacitate", "ipoteză"],
    efort_anaf: ["Munca unui dosar ANAF", "ipoteză"],
    rezolvari_observate_pe_zi: ["Soluționări pe zi lucrătoare", "măsurat: BERC, 2–17.11.2026 (−10% … +8%)"]
  };
  function fmtP(v) { return Math.abs(v) < 2 ? nf2.format(v) : nf.format(Math.round(v)); }
  table("t_params", ["Parametru", "Minim", "Cel mai probabil", "Maxim", "Natura"], I.param_names.map(function (k) {
    var b = I.bounds[k]; return [esc(PN[k] ? PN[k][0] : k) + ' <span class="muted mono small">' + k + "</span>", fmtP(b.low), fmtP(b.mode), fmtP(b.high), esc(PN[k] ? PN[k][1] : "")];
  }), [1, 2, 3]);

  table("t_levers", ["Pârghie", "Cum intră în motor", "Sursa formulei"], [
    ["Cereri noi ±%", "toate intrările × (1 + x%), de la 19.11.2026", "forecast_grid.py [C63]"],
    ["Capacitate ±%", "capacitatea motorului × (1 + y%)", "forecast_grid.py [C63]"],
    ["Valul CAEN 0/50/80/100%", "valul variantei × (pondere × 902.243 / valul variantei); aceeași formă în timp și aceeași muncă pe dosar", "forecast_caen_compliance.py [C94]"],
    ["Conversie CAEN 1-la-1", "valul CAEN × (1 − 0,75) de la data de start", "forecast_caen_compliance.py [C95], pachetele P4/P5"],
    ["Proiectul de OUG", "+ posturi × dosare/zi × rampă (0,5 în primele 20 de zile lucrătoare), până la 08.01.2028, doar în zilele lucrătoare; − cota Art. III × munca de dizolvare ANAF, de la start + 15 zile. Livrare slabă 5×20 și 0%; centrală 15×25 și 25%; bună 30×30 și 50%", "audit_oug.py [C43, C44, C61]"],
    ["OUG prelungit", "rampa nu se mai oprește la 08.01.2028", "steelman_and_solutions_engine.py (P3–P5)"],
    ["Personal suplimentar", "+ posturi × 25 de dosare pe zi lucrătoare, de la start + 56 de zile (P3: +375 de la 01.03.2027)", "steelman_and_solutions_engine.py (P3) [C52]"],
    ["Eșalonarea capitalului", "valul de capital pe forma eșalonată a motorului (stagger_shape)", "audit_forecast.py, audit_oug.py, P4/P5 [C53]"],
    ["Triaj", "+ 0,02 × capacitatea medie a motorului (" + nf.format(Math.round(I.constants.triage_units)) + " pe zi), de la data de start", "steelman_and_solutions_engine.py (P5) [C54]"],
    ["Data de start", "mută toate pragurile de mai sus; implicit 04.01.2027, ca în raport", "audit_oug.py / P3–P5"]
  ].map(function (r) { return [esc(r[0]), esc(r[1]), '<span class="mono small">' + esc(r[2]) + "</span>"]; }));

  /* ---------------- backtest */
  var O = R.backtest_queue.origini, keys = Object.keys(O);
  table("t_bt", ["Origine", "Stoc la origine", "Zile evaluate", "Mecanism: eroare medie", "deplasare", "corelație", "Prognoză: capacitate / intrări presupuse", "eroare medie", "deplasare"],
    keys.map(function (k) {
      var o = O[k]; return [dmy(k), nf.format(o.stoc_initial), o.zile_evaluate, d(o.mecanism.mae), d(o.mecanism.bias), nf.format(o.mecanism.corelatie),
        nf.format(o.prognoza.capacitate_presupusa) + " / " + nf.format(o.prognoza.intrari_presupuse), d(o.prognoza.mae), d(o.prognoza.bias)];
    }), [1, 2, 3, 4, 5, 7, 8]);
  var cur = keys[1];
  function btChart() {
    var o = O[cur], rows = o.saptamanal, svg = $("svg_bt"), NS = "http://www.w3.org/2000/svg";
    $("bt_title").textContent = "Așteptarea pe săptămâna depunerii, de la originea " + dmy(cur);
    var W = Math.max(300, Math.round(svg.parentNode.clientWidth || 760)), H = W < 520 ? 220 : 250, m = { l: 40, r: 12, t: 10, b: 26 };
    svg.setAttribute("viewBox", "0 0 " + W + " " + H); svg.setAttribute("width", W); svg.setAttribute("height", H);
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    function el(n, a) { var e = document.createElementNS(NS, n); for (var k in a) e.setAttribute(k, a[k]); svg.appendChild(e); return e; }
    var ymax = 0, ymin = 0; rows.forEach(function (r) { ymax = Math.max(ymax, r.observat, r.mecanism, r.prognoza); ymin = Math.min(ymin, r.observat, r.mecanism, r.prognoza); });
    ymax = Math.ceil(ymax / 5) * 5 + 5; ymin = ymin < 0 ? -Math.ceil(-ymin / 5) * 5 : 0;
    var iw = W - m.l - m.r, ih = H - m.t - m.b, n = rows.length;
    var x = function (i) { return m.l + (n === 1 ? iw / 2 : i / (n - 1) * iw); }, y = function (v) { return m.t + ih - (v - ymin) / (ymax - ymin) * ih; };
    for (var v = ymin; v <= ymax; v += ymax - ymin > 30 ? 10 : 5) {
      el("line", { x1: m.l, x2: m.l + iw, y1: y(v), y2: y(v), stroke: "#e3e0d8" });
      el("text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end" }).textContent = v;
    }
    var stepL = Math.ceil(n / (W < 520 ? 4 : 8));
    rows.forEach(function (r, i) { if (i % stepL === 0) el("text", { x: x(i), y: m.t + ih + 17, "text-anchor": "middle" }).textContent = dmy(r.sapt).slice(0, 5); });
    [["observat", "#1b1d1f", ""], ["mecanism", "#1d5e5a", ""], ["prognoza", "#6b7178", "5 4"]].forEach(function (s) {
      el("path", { d: rows.map(function (r, i) { return (i ? "L" : "M") + x(i).toFixed(1) + "," + y(r[s[0]]).toFixed(1); }).join(""),
        fill: "none", stroke: s[1], "stroke-width": 2, "stroke-dasharray": s[2], "stroke-linejoin": "round" });
      rows.forEach(function (r, i) {
        var c = el("circle", { cx: x(i), cy: y(r[s[0]]), r: 3, fill: s[1] });
        var t = document.createElementNS(NS, "title"); t.textContent = dmy(r.sapt) + " · " + s[0] + ": " + d(r[s[0]]) + " zile"; c.appendChild(t);
      });
    });
  }
  $("bt_origin").innerHTML = keys.map(function (k) { return '<button type="button" data-v="' + k + '" aria-pressed="' + (k === cur) + '">' + dmy(k) + "</button>"; }).join("");
  $("bt_origin").addEventListener("click", function (e) {
    var v = e.target.dataset && e.target.dataset.v; if (!v) return; cur = v;
    Array.prototype.forEach.call($("bt_origin").querySelectorAll("button"), function (b) { b.setAttribute("aria-pressed", String(b.dataset.v === cur)); });
    btChart();
  });
  btChart();
  var rt; window.addEventListener("resize", function () { clearTimeout(rt); rt = setTimeout(btChart, 120); });

  var cap = R.backtest_capacity.filter(function (r) { return r.model === "ultimele_12_zile"; });
  var mape = cap.reduce(function (s, r) { return s + Math.abs(100 * (r.predicted_per_day / r.observed_per_day - 1)); }, 0) / cap.length;
  var rowsCap = cap.map(function (r) {
    return [dmy(r.test_start) + " – " + dmy(r.test_end), r.test_workdays, nf.format(Math.round(r.predicted_per_day)), nf.format(Math.round(r.observed_per_day)),
      (r.error_percent > 0 ? "+" : "") + nf1.format(r.error_percent) + "%"];
  });
  rowsCap.push({ cls: "sum", cells: ["Eroare absolută medie (față de valoarea observată)", "", "", "", nf1.format(mape) + "%"] });
  table("t_cap", ["Fereastra de test", "Zile lucrătoare", "Prognozat / zi", "Observat / zi", "Observat față de prognoză"], rowsCap, [1, 2, 3, 4]);

  /* ---------------- verification */
  var weeks = (V.results.filter(function (r) { return r.weekly; })[0] || { weekly: { dates: [] } }).weekly.dates.length;
  $("sz").textContent = nf.format(I.n_draws) + " de variante × " + I.param_names.length + " parametri, plus " + Object.keys(I.vectors).length + " vectori zilnici; sub 1 MB";
  $("vA").innerHTML = okPub + " din " + nPub + " valori " + (V.published_check.ok ? '<span class="ok">✓ identice</span>' : '<span class="fail">✗</span>');
  $("vB").innerHTML = (V.reference_equals_published.ok ? '<span class="ok">✓ aceleași așteptări în toate cele ' + V.reference_equals_published.rows.length + " cazuri</span>" : '<span class="fail">✗</span>');
  $("vCn").textContent = V.n_settings; $("vCw").textContent = weeks;
  $("vC").innerHTML = "diferența maximă a fost <strong>" + d(V.max_abs_diff_days) + " zile</strong> " + (V.all_ok ? '<span class="ok">✓</span>' : '<span class="fail">✗</span>');
  table("t_verify", ["Setare", "Python: 30.06.2027 · vârf (mediane)", "Python: 30.06.2028 p10 / p50 / p90", "JS: 30.06.2028 p10 / p50 / p90", "Câștig median (Py / JS)", "Diferență max., zile", "Rezultat"],
    V.results.map(function (r) {
      var cz = function (a) { return a ? a.map(function (v) { return v === null ? "peste orizont" : dz(v); }).join(" / ") : "—"; };
      if (r.beyond_py) return [esc(r.name) + '<br><span class="muted small">' + nf.format(r.censored_cells_py) + " zile×variante peste orizont (JS: " + nf.format(r.censored_cells_js) + ")</span>",
        cz([r.py.mid2027[1]]) + " · " + cz([r.py.peak[1]]), cz(r.py.june2028), cz(r.js.june2028), "—", d(r.max_diff_days), okb(r.ok)];
      var hasG = r.py.gain_june2028 !== undefined && r.py.gain_june2028 !== null && r.settings && Object.keys(r.settings).some(function (k) { return ["oug", "caen_auto", "stagger", "staff_fte", "triage", "art3", "oug_extended"].indexOf(k) >= 0; });
      return [esc(r.name), dz(r.py.mid2027[1]) + " · " + dz(r.py.peak[1]), q3(r.py.june2028), q3(r.js.june2028),
        hasG ? d(r.py.gain_june2028) + " / " + d(r.js.gain_june2028) : "—", d(r.max_diff_days), okb(r.ok)];
    }), [5]);
  $("v_note").textContent = "Stocul diferă între Python și JavaScript cu cel mult " + maxStock.toExponential(1) +
    " dosare, din rotunjiri în ultima zecimală (de exemplu, la ridicarea la putere). Așteptările nu sunt afectate. Node " + V.node + ", numpy " + V.numpy + ", Python " + V.python + ".";

  /* ---------------- claims */
  function cval(v) { return v.map(function (x) { return x <= 3 ? "≤3" : nf1.format(Math.round(x * 10) / 10); }).join(" / "); }
  table("t_claims", ["Afirmație", "Ce", "Valoare în registru", "Stare", "Motorul JS", "Se potrivește"], V.claims.rows.map(function (c) {
    var st = c.registry_status === "PASS" ? '<span class="badge pass">PASS</span>' : '<span class="badge w">' + esc(c.registry_status) + "</span>";
    var jsv = c.what.indexOf("stoc") === 0 ? "≈" + nf.format(c.js_value[0]) : c.what.indexOf("câștig") >= 0 ? d(c.js_value[0]) : cval(c.js_value);
    return ['<span class="mono">' + c.claim + "</span>", esc(c.what), esc(c.registry_value), st, jsv, c.ok ? '<span class="ok">✓</span>' : '<span class="fail">✗</span>'];
  }));
  table("t_reserves", ["Afirmație", "Stare", "Ce spune", "Rezerva obligatorie", "Amprenta datelor"], R.claims.map(function (c) {
    return ['<span class="mono">' + c.id + "</span>", c.status === "PASS" ? '<span class="badge pass">PASS</span>' : '<span class="badge w">' + esc(c.status) + "</span>",
      esc(c.public_ro), esc(c.rezerva_obligatorie), '<span class="mono small">' + esc((c.data_sha256 || "").slice(0, 12)) + "…</span>"];
  }));

  /* ---------------- reproduction hashes */
  $("se_ok").innerHTML = Object.values(V.side_effect_csvs_identical).every(Boolean) ? '<span class="ok">✓ identice</span>' : '<span class="fail">diferite</span>';
  var sha = [["analysis/policy_paper_ro/audit_forecast.py (motorul)", V.engine_sha256], ["site/data/engine_inputs.json (intrările exportate)", V.engine_inputs_sha256],
    ["site/js/engine.js (motorul din browser, la verificare)", V.engine_js_sha256]];
  Object.keys(I.input_sha256).forEach(function (k) { sha.push([k, I.input_sha256[k]]); });
  Object.keys(R.file_sha256).forEach(function (k) { sha.push([k, R.file_sha256[k]]); });
  table("t_sha", ["Fișier", "SHA-256"], sha.map(function (r) { return ['<span class="mono small">' + esc(r[0]) + "</span>", '<span class="mono small" style="word-break:break-all">' + esc(r[1]) + "</span>"]; }));
  var mj = "https://www.just.ro/wp-content/uploads/2026/11/NF-OUG-pentru-instituirea-unor-masuri-privind-activitatea-de-inregistrare-in-registrului-comertului-si-pentru-completarea-Legii-nr.-265-2022.docx";
  $("mj_link").setAttribute("href", mj);

  live();
  document.documentElement.setAttribute("data-ready", "1");
})();
