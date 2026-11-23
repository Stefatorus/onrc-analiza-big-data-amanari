/*
 * ONRC queue forecast engine — JavaScript port of analysis/policy_paper_ro/audit_forecast.py
 * (prepare_workload + simulate), with the scenario levers used by audit_oug.py,
 * steelman_and_solutions_engine.py, independent_audit/forecast_grid.py and
 * independent_audit/forecast_caen_compliance.py.
 *
 * Every array component is rebuilt from the exported per-draw parameters and the engine's
 * own date vectors IN THE ENGINE'S ORDER OF OPERATIONS (IEEE-754 float64), so results are
 * bit-identical to numpy (checked by verify_js_vs_py.py).
 *
 * No DOM access: the same file is loaded by the browser (window.OnrcEngine) and by Node
 * (module.exports) for the verification run.
 */
(function (root) {
  "use strict";
  var DAY_MS = 86400000;

  function isoToUTC(iso) {
    var p = iso.split("-");
    return Date.UTC(+p[0], +p[1] - 1, +p[2]);
  }
  function utcToIso(ms) {
    return new Date(ms).toISOString().slice(0, 10);
  }

  /* ---------------------------------------------------------------- model setup */
  function init(inp) {
    var N = inp.n_draws, n = inp.n_dates, L = inp.n_calendar;
    var v = inp.vectors, P = inp.params;
    var start = isoToUTC(inp.start);
    var opening = new Uint8Array(L);
    for (var j = 0; j < L; j++) opening[j] = inp.opening[j];
    // date helpers
    var mondays = [], dateIso = new Array(n);
    var dow0 = (new Date(start).getUTCDay() + 6) % 7; // Monday = 0 (pandas dayofweek)
    for (var i = 0; i < n; i++) {
      dateIso[i] = utcToIso(start + i * DAY_MS);
      if ((dow0 + i) % 7 === 0) mondays.push(i);
    }
    // per-draw scalars, in the engine's expression order
    var ordinary = new Float64Array(N * n);
    var sc = {
      capBase: new Float64Array(N), initial: new Float64Array(N), cw: new Float64Array(N),
      dosare: new Float64Array(N), efortCaen: new Float64Array(N), anafS: new Float64Array(N)
    };
    for (var d = 0; d < N; d++) {
      var flux = P.flux_zilnic_recurent[d], g1 = 1 + P.crestere_anuala_flux[d];
      var dos = P.dosare_caen_suplimentare[d], ec = P.efort_caen[d];
      var pop = P.populatie_capital[d], prop = P.proportie_reducere[d], efc = P.efort_capital[d];
      var earlyS = (pop * prop) * efc;
      var cw = (((pop * (1 - prop)) * P.conformare_ulterioara[d]) * P.depuneri_separate_ulterioare[d]) * efc;
      var def = P.dosare_defensive[d];
      var anafS = (P.cazuri_anaf[d] * P.fractie_anaf_capacitate_comuna[d]) * P.efort_anaf[d];
      var avg = 1 - P.pondere_caen_iesiri[d] * (1 - ec);
      sc.capBase[d] = P.rezolvari_observate_pe_zi[d] * avg;   // times opening[j] per day
      sc.initial[d] = P.stoc_initial[d] * avg;
      sc.cw[d] = cw; sc.dosare[d] = dos; sc.efortCaen[d] = ec; sc.anafS[d] = anafS;
      var o = d * n;
      for (i = 0; i < n; i++) {
        var recurring = ((flux * v.seasonal[i]) * v.recurring_weight[i]) * Math.pow(g1, v.forecast_offset[i]);
        var early = earlyS * v.early_shape[i];
        var defensive = (def * v.defensive_shape[i]) * 0.95;
        var dissolve = anafS * v.anaf_shape[i];
        ordinary[o + i] = ((recurring + early) + defensive) + dissolve;
      }
    }
    var idx = function (iso) { return Math.round((isoToUTC(iso) - start) / DAY_MS); };
    return {
      inp: inp, N: N, n: n, L: L, opening: opening, v: v, sc: sc, ordinary: ordinary,
      start: inp.start, mondays: mondays, dateIso: dateIso, idx: idx,
      keys: { mid2027: idx("2027-06-30"), june2028: n - 1 },
      C: inp.constants
    };
  }

  /* ---------------------------------------------------------------- levers */
  var OUG_VARIANTS = {            // audit_oug.py SCENARIOS: net FTE, units per FTE per workday, Art. III share
    none: [0, 0, 0],
    redus: [5, 20, 0],
    central: [15, 25, 0.25],
    ridicat: [30, 30, 0.5]
  };
  var DEFAULTS = {
    in_pct: 0,          // % change of TOTAL inflow (recurring + waves), as forecast_grid.py
    cap_pct: 0,         // % change of the engine's solving capacity, as forecast_grid.py
    caen: "motor",      // "motor" (engine assumption 140–390k) or share of the 902,243 MJ figure: 0, 0.5, 0.8, 1
    caen_auto: false,   // automatic 1-to-1 CAEN conversion: removes caen_auto_share of the CAEN wave from start
    caen_auto_share: 0.75,
    stagger: false,     // staggered capital filings (engine stagger_shape)
    oug: "none",        // draft OUG delivery variant (audit_oug.py)
    oug_extended: false,// OUG support not ending on 08.01.2028 (packages P3–P5)
    art3: null,         // Art. III share of ANAF dissolution work transferred (null = variant default)
    staff_fte: 0,       // extra net FTE at the (single) solving stage, units_per_fte each, from start + 56 days
    triage: false,      // +2% of mean baseline capacity from start (package P5 "triaj")
    start: "2027-01-04" // start date of all measures
  };
  function withDefaults(s) {
    var o = {};
    for (var k in DEFAULTS) o[k] = (s && s[k] !== undefined) ? s[k] : DEFAULTS[k];
    return o;
  }
  function noMeasures(s) {
    var o = withDefaults(s);
    o.caen_auto = false; o.stagger = false; o.oug = "none"; o.oug_extended = false;
    o.art3 = null; o.staff_fte = 0; o.triage = false;
    return o;
  }
  function hasMeasures(s) {
    var o = withDefaults(s);
    return o.caen_auto || o.stagger || o.oug !== "none" || o.staff_fte > 0 || o.triage ||
      (o.art3 !== null && o.art3 > 0);
  }

  /* Policy day vectors on the full calendar (length L), as in audit_oug.py / steelman engine. */
  function policyVectors(M, s) {
    var L = M.L, open = M.opening, C = M.C;
    var js = M.idx(s.start), jEnd = M.idx(C.oug_end);
    var after = new Float64Array(L), perm = new Float64Array(L), staff = new Float64Array(L), ramp = new Float64Array(L);
    var cnt = 0;
    for (var j = 0; j < L; j++) {
      var a = j >= js;
      after[j] = a ? 1 : 0;
      perm[j] = j >= js + C.art3_lag_days ? 1 : 0;
      staff[j] = j >= js + C.staff_lag_days ? 1 : 0;
      var t = s.oug_extended ? a : (a && j <= jEnd);
      if (t && open[j]) cnt++;
      ramp[j] = t ? (cnt <= C.ramp_workdays ? 0.5 : 1.0) : 0.0;
    }
    return { after: after, perm: perm, staff: staff, ramp: ramp };
  }

  /* ---------------------------------------------------------------- simulate */
  // Lindley recursion S_t = max(0, S_{t-1} + A_t - C_t); a standard file filed at the close of day i
  // is served on the first day k with cumC_k >= cumC_i + S_i + 1 (np.searchsorted, side="left").
  function run(M, settings, opts) {
    var s = withDefaults(settings);
    opts = opts || {};
    var N = M.N, n = M.n, L = M.L, v = M.v, sc = M.sc, open = M.opening, C = M.C;
    var pv = policyVectors(M, s);
    var variant = OUG_VARIANTS[s.oug] || OUG_VARIANTS.none;
    var ougU = variant[0] * variant[1];
    var art3 = s.art3 === null ? variant[2] : s.art3;
    var staffU = s.staff_fte * C.units_per_fte;
    var T = s.triage ? C.triage_units : 0;
    var inMult = 1 + s.in_pct / 100, capMult = 1 + s.cap_pct / 100;
    var auto = s.caen_auto ? s.caen_auto_share : 0;
    var share = s.caen === "motor" ? null : +s.caen;
    var MJ = C.mj_caen_remaining;

    // extra capacity per calendar day (draw-independent)
    var extra = new Float64Array(L);
    for (var j = 0; j < L; j++) extra[j] = ((ougU * pv.ramp[j] + staffU * pv.staff[j]) + T * pv.after[j]) * open[j];

    var W = M.mondays, nw = W.length;
    var keyIdx = [M.keys.mid2027, M.keys.june2028];
    var res = {
      settings: s, N: N,
      waitW: new Float64Array(N * nw), stockW: new Float64Array(N * nw),
      waitKey: [new Float64Array(N), new Float64Array(N)], stockKey: [new Float64Array(N), new Float64Array(N)],
      peak: new Float64Array(N), beyond: 0
    };
    if (opts.full) { res.waitFull = new Float64Array(N * n); res.stockFull = new Float64Array(N * n); }
    var cum = new Float64Array(L), stock = new Float64Array(n), inflow = new Float64Array(n), wait = new Float64Array(n);
    for (var d = 0; d < N; d++) {
      var o = d * n, cb = sc.capBase[d];
      var caenF = share === null ? 1 : (share * MJ) / sc.dosare[d];
      var dos = sc.dosare[d], ec = sc.efortCaen[d], cw = sc.cw[d], anafS = sc.anafS[d];
      for (var i = 0; i < n; i++) {
        var caen = (dos * v.caen_shape[i]) * ec;
        if (share !== null) caen = caen * caenF;
        caen = caen * (1 - auto * pv.after[i]);
        var capital = s.stagger ? cw * v.stagger_shape[i] : cw * v.capital_shape[i];
        var dissolve = anafS * v.anaf_shape[i];
        inflow[i] = ((((M.ordinary[o + i] + caen) + capital) - (art3 * dissolve) * pv.perm[i])) * inMult;
      }
      // capacity and its running sum (np.cumsum is sequential)
      var acc = 0;
      for (j = 0; j < L; j++) {
        acc += (cb * open[j]) * capMult + extra[j];
        cum[j] = acc;
      }
      var prev = sc.initial[d], pk = -Infinity;
      for (i = 0; i < n; i++) {
        var capi = (cb * open[i]) * capMult + extra[i];
        prev = Math.max(0, (prev + inflow[i]) - capi);
        stock[i] = prev;
      }
      for (i = 0; i < n; i++) {
        var target = (cum[i] + stock[i]) + 1;
        var lo = 0, hi = L;              // lower_bound on cum
        while (lo < hi) { var mid = (lo + hi) >>> 1; if (cum[mid] < target) lo = mid + 1; else hi = mid; }
        var w;
        if (lo >= L) { w = Infinity; res.beyond++; } else w = lo - i;
        if (w > pk) pk = w;
        if (opts.full) { res.waitFull[o + i] = w; res.stockFull[o + i] = stock[i]; }
        wait[i] = w;
      }
      for (var k = 0; k < nw; k++) {
        res.waitW[d * nw + k] = wait[W[k]];
        res.stockW[d * nw + k] = stock[W[k]];
      }
      for (k = 0; k < 2; k++) { res.waitKey[k][d] = wait[keyIdx[k]]; res.stockKey[k][d] = stock[keyIdx[k]]; }
      res.peak[d] = pk;
    }
    return res;
  }

  /* ---------------------------------------------------------------- statistics */
  // numpy.quantile(method="linear") incl. its two-sided lerp.
  function quantileSorted(a, q) {
    var n = a.length, vi = (n - 1) * q, lo = Math.floor(vi), hi = Math.min(lo + 1, n - 1), g = vi - lo;
    var x = a[lo], y = a[hi];
    if (!isFinite(x) || !isFinite(y)) return (g === 0 && isFinite(x)) ? x : Infinity; // censored draws
    var diff = y - x;
    return g >= 0.5 ? y - diff * (1 - g) : x + diff * g;
  }
  function quantiles(arr, qs) {
    var a = Float64Array.from(arr).sort();
    return qs.map(function (q) { return quantileSorted(a, q); });
  }
  var Q = [0.1, 0.5, 0.9];
  function column(buf, N, stride, k) {
    var c = new Float64Array(N);
    for (var d = 0; d < N; d++) c[d] = buf[d * stride + k];
    return c;
  }
  function frac(arr, f) { var c = 0; for (var i = 0; i < arr.length; i++) if (f(arr[i])) c++; return c / arr.length; }
  function diffMedian(a, b) { // median of paired differences a - b (same draws); undefined if any draw is censored
    var d = new Float64Array(a.length);
    for (var i = 0; i < a.length; i++) {
      if (!isFinite(a[i]) || !isFinite(b[i])) return NaN;
      d[i] = a[i] - b[i];
    }
    return quantiles(d, [0.5])[0];
  }

  function summarize(M, r, base) {
    var N = r.N, nw = M.mondays.length;
    var weekly = [];
    for (var k = 0; k < nw; k++) {
      var wq = quantiles(column(r.waitW, N, nw, k), Q), sq = quantiles(column(r.stockW, N, nw, k), Q);
      weekly.push({ date: M.dateIso[M.mondays[k]], wait: wq, stock: sq });
    }
    function point(arr, barr) {
      var o = { q: quantiles(arr, Q), le3: frac(arr, function (x) { return x <= 3; }) };
      if (barr) o.gain = diffMedian(barr, arr);
      return o;
    }
    return {
      beyond: r.beyond, weekly: weekly,
      mid2027: point(r.waitKey[0], base && base.waitKey[0]),
      peak: point(r.peak, base && base.peak),
      june2028: point(r.waitKey[1], base && base.waitKey[1]),
      stockJune2028: quantiles(r.stockKey[1], Q),
      stockMid2027: quantiles(r.stockKey[0], Q)
    };
  }

  var api = {
    init: init, run: run, summarize: summarize, quantiles: quantiles, DEFAULTS: DEFAULTS,
    OUG_VARIANTS: OUG_VARIANTS, withDefaults: withDefaults, noMeasures: noMeasures, hasMeasures: hasMeasures
  };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.OnrcEngine = api;
})(typeof window !== "undefined" ? window : this);
