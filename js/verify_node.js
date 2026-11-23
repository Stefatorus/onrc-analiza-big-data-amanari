// Node runner for verify_js_vs_py.py: loads the SAME js/engine.js the site uses.
// usage: node js/verify_node.js data/engine_inputs.json settings.json out.json
"use strict";
const fs = require("fs");
const E = require("./engine.js");
const [inpPath, setPath, outPath] = process.argv.slice(2);
const inp = JSON.parse(fs.readFileSync(inpPath, "utf8"));
const t0 = Date.now();
const M = E.init(inp);
const tInit = Date.now() - t0;
const cases = setPath ? JSON.parse(fs.readFileSync(setPath, "utf8")) : [{ name: "default", settings: {} }];
const fin = (x) => (isFinite(x) ? x : null);
const arr = (a) => Array.from(a, fin);
const out = { init_ms: tInit, cases: [] };
for (const c of cases) {
  const t1 = Date.now();
  const r = E.run(M, c.settings);
  const base = E.run(M, E.noMeasures(c.settings));
  const ms = Date.now() - t1;
  const S = E.summarize(M, r, base);
  out.cases.push({
    name: c.name, ms, beyond: r.beyond,
    weekly_dates: S.weekly.map((w) => w.date),
    wait_weekly: S.weekly.map((w) => arr(w.wait)), stock_weekly: S.weekly.map((w) => arr(w.stock)),
    mid2027: arr(S.mid2027.q), peak: arr(S.peak.q), june2028: arr(S.june2028.q),
    gain_june2028: fin(S.june2028.gain), gain_mid2027: fin(S.mid2027.gain), gain_peak: fin(S.peak.gain),
    le3_june2028: S.june2028.le3, stock_june2028: arr(S.stockJune2028), stock_mid2027: arr(S.stockMid2027),
  });
}
fs.writeFileSync(outPath || "/dev/stdout", JSON.stringify(out));
