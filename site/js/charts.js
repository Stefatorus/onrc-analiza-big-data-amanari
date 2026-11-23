/* Small dependency-free SVG charts (band + median + comparison line, crosshair tooltip). */
(function (root) {
  "use strict";
  var NS = "http://www.w3.org/2000/svg";
  var MONTHS = ["ian.", "feb.", "mar.", "apr.", "mai", "iun.", "iul.", "aug.", "sept.", "oct.", "nov.", "dec."];

  function el(name, attrs, parent) {
    var e = document.createElementNS(NS, name);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function parse(iso) { var p = iso.split("-"); return Date.UTC(+p[0], +p[1] - 1, +p[2]); }
  function niceStep(max, n) {
    var raw = max / n, mag = Math.pow(10, Math.floor(Math.log10(raw))), r = raw / mag;
    return (r <= 1 ? 1 : r <= 2 ? 2 : r <= 2.5 ? 2.5 : r <= 5 ? 5 : 10) * mag;
  }
  function fin(v, cap) { return isFinite(v) ? v : cap; }

  /*
   * opts: { svg, tip, dates:[iso], q:[[p10,p50,p90]], base:[p50]|null, fmtY(v), fmtTip(i), marker:{date,label}|null,
   *         height, labelMain, labelBase }
   */
  function bandChart(o) {
    var svg = o.svg;
    var W = Math.max(300, Math.round(svg.parentNode.clientWidth || 760));
    var small = W < 520;
    var H = o.height || (small ? 250 : 320);
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("width", W); svg.setAttribute("height", H);
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var m = { l: small ? 40 : 52, r: small ? 12 : 92, t: 12, b: 26 };
    var iw = W - m.l - m.r, ih = H - m.t - m.b;
    var t0 = parse(o.dates[0]), t1 = parse(o.dates[o.dates.length - 1]);
    var x = function (iso) { return m.l + (parse(iso) - t0) / (t1 - t0) * iw; };
    var ymaxData = 0;
    o.q.forEach(function (r) { if (isFinite(r[2])) ymaxData = Math.max(ymaxData, r[2]); else if (isFinite(r[1])) ymaxData = Math.max(ymaxData, r[1]); });
    if (o.base) o.base.forEach(function (v) { if (isFinite(v)) ymaxData = Math.max(ymaxData, v); });
    var step = niceStep(Math.max(ymaxData, o.minMax || 10), small ? 4 : 5);
    var ymax = Math.ceil(Math.max(ymaxData, o.minMax || 10) / step) * step;
    var y = function (v) { return m.t + ih - (Math.min(fin(v, ymax), ymax) / ymax) * ih; };

    // grid + y axis
    var g = el("g", { "class": "grid" }, svg);
    for (var v = 0; v <= ymax + 1e-9; v += step) {
      el("line", { x1: m.l, x2: m.l + iw, y1: y(v), y2: y(v) }, g);
      var t = el("text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end" }, g);
      t.textContent = o.fmtY(v);
    }
    // x ticks: quarters
    var gx = el("g", { "class": "axis" }, svg);
    el("line", { x1: m.l, x2: m.l + iw, y1: m.t + ih, y2: m.t + ih, stroke: "#bdbab2" }, gx);
    var d0 = new Date(t0);
    for (var yy = d0.getUTCFullYear(); yy <= 2028; yy++) {
      for (var mm = 0; mm < 12; mm += small ? 6 : 3) {
        var ms = Date.UTC(yy, mm, 1);
        if (ms < t0 || ms > t1) continue;
        var xx = m.l + (ms - t0) / (t1 - t0) * iw;
        el("line", { x1: xx, x2: xx, y1: m.t + ih, y2: m.t + ih + 4, stroke: "#bdbab2" }, gx);
        var lt = el("text", { x: xx, y: m.t + ih + 17, "text-anchor": "middle" }, gx);
        lt.textContent = mm === 0 ? (MONTHS[0] + " " + yy) : MONTHS[mm];
      }
    }
    // marker (start of measures)
    if (o.marker && parse(o.marker.date) >= t0 && parse(o.marker.date) <= t1) {
      var mx = x(o.marker.date);
      el("line", { x1: mx, x2: mx, y1: m.t, y2: m.t + ih, stroke: "#7a6200", "stroke-width": 1, "stroke-dasharray": "2 3" }, svg);
      var mt = el("text", { x: mx + 4, y: m.t + 10, style: "fill:#7a6200" }, svg);
      mt.textContent = o.marker.label;
    }
    // band
    var top = o.q.map(function (r, i) { return x(o.dates[i]).toFixed(1) + "," + y(r[2]).toFixed(1); });
    var bot = o.q.map(function (r, i) { return x(o.dates[i]).toFixed(1) + "," + y(r[0]).toFixed(1); }).reverse();
    el("path", { d: "M" + top.join("L") + "L" + bot.join("L") + "Z", fill: "rgba(29,94,90,.16)", stroke: "none" }, svg);
    // base line
    function line(vals, attrs) {
      var d = vals.map(function (v, i) { return (i ? "L" : "M") + x(o.dates[i]).toFixed(1) + "," + y(v).toFixed(1); }).join("");
      return el("path", Object.assign({ d: d, fill: "none", "stroke-linejoin": "round", "stroke-linecap": "round" }, attrs), svg);
    }
    if (o.base) line(o.base, { stroke: "#6b7178", "stroke-width": 2, "stroke-dasharray": "5 4" });
    line(o.q.map(function (r) { return r[1]; }), { stroke: "#1d5e5a", "stroke-width": 2.25 });
    // direct labels (desktop)
    if (!small) {
      var last = o.q.length - 1, ly1 = y(o.q[last][1]), ly2 = o.base ? y(o.base[last]) : null;
      if (ly2 !== null && Math.abs(ly1 - ly2) < 14) { if (ly1 <= ly2) { ly1 -= 7; ly2 += 7; } else { ly1 += 7; ly2 -= 7; } }
      var l1 = el("text", { x: m.l + iw + 6, y: ly1 + 4, style: "fill:#1b1d1f;font-weight:500" }, svg); l1.textContent = o.labelMain;
      if (o.base) { var l2 = el("text", { x: m.l + iw + 6, y: ly2 + 4 }, svg); l2.textContent = o.labelBase; }
    }
    // crosshair
    var cross = el("line", { y1: m.t, y2: m.t + ih, stroke: "#1b1d1f", "stroke-width": 1, visibility: "hidden" }, svg);
    var dot = el("circle", { r: 4, fill: "#1d5e5a", stroke: "#fff", "stroke-width": 2, visibility: "hidden" }, svg);
    var hit = el("rect", { x: m.l, y: m.t, width: iw, height: ih, fill: "transparent", tabindex: 0 }, svg);
    var tip = o.tip, idx = -1;
    function show(i) {
      idx = Math.max(0, Math.min(o.dates.length - 1, i));
      var xx = x(o.dates[idx]);
      cross.setAttribute("x1", xx); cross.setAttribute("x2", xx); cross.setAttribute("visibility", "visible");
      dot.setAttribute("cx", xx); dot.setAttribute("cy", y(o.q[idx][1])); dot.setAttribute("visibility", "visible");
      tip.innerHTML = "";
      o.fmtTip(idx, tip);
      tip.style.display = "block";
      var cw = svg.parentNode.clientWidth, tw = tip.offsetWidth;
      var scale = svg.getBoundingClientRect().width / W;
      var left = xx * scale + 12;
      if (left + tw > cw) left = xx * scale - tw - 12;
      tip.style.left = Math.max(0, left) + "px";
      tip.style.top = (svg.offsetTop + m.t * scale + 6) + "px";
    }
    function hide() { cross.setAttribute("visibility", "hidden"); dot.setAttribute("visibility", "hidden"); tip.style.display = "none"; }
    function nearest(evt) {
      var r = svg.getBoundingClientRect(), px = (evt.clientX - r.left) * (W / r.width);
      var t = t0 + (px - m.l) / iw * (t1 - t0), best = 0, bd = Infinity;
      for (var i = 0; i < o.dates.length; i++) { var dd = Math.abs(parse(o.dates[i]) - t); if (dd < bd) { bd = dd; best = i; } }
      return best;
    }
    hit.addEventListener("pointermove", function (e) { show(nearest(e)); });
    hit.addEventListener("pointerdown", function (e) { show(nearest(e)); });
    hit.addEventListener("pointerleave", hide);
    hit.addEventListener("blur", hide);
    hit.addEventListener("focus", function () { show(idx < 0 ? o.dates.length - 1 : idx); });
    hit.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { show(idx - 1); e.preventDefault(); }
      if (e.key === "ArrowRight") { show(idx + 1); e.preventDefault(); }
    });
  }

  root.OnrcCharts = { bandChart: bandChart };
})(window);
