(function () {
  "use strict";

  const monthly = DATA.monthly.map(d => ({ ...d, date: new Date(d.d) }));
  const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const fmt = d3.format(",.0f");
  const fmt1 = d3.format(",.1f");
  const eur = (v) => "€" + fmt(v) + "m";
  const gwh = (v) => fmt(v) + " GWh";
  const eurMwh = (v) => "€" + fmt1(v);

  const tooltip = d3.select("#tooltip");
  function showTip(html, evt) {
    const wrap = document.querySelector(".wrap").getBoundingClientRect();
    tooltip.html(html)
      .style("opacity", 1)
      .style("left", (evt.clientX - wrap.left + 16) + "px")
      .style("top", (evt.clientY - wrap.top - 10 + window.scrollY) + "px");
  }
  function moveTip(evt) {
    const wrap = document.querySelector(".wrap").getBoundingClientRect();
    tooltip.style("left", (evt.clientX - wrap.left + 16) + "px")
           .style("top", (evt.clientY - wrap.top - 10 + window.scrollY) + "px");
  }
  function hideTip() { tooltip.style("opacity", 0); }

  // ---------- KPI row ----------
  (function kpis() {
    const peak = monthly.reduce((a, b) => (b.cost > a.cost ? b : a));
    const latest = monthly[monthly.length - 1];
    const dropPct = Math.round((1 - latest.cost / peak.cost) * 100);
    const tsoTotal = d3.sum(DATA.tso, d => d.gwh);
    const tenneT = DATA.tso.find(d => d.tso === "TenneT DE");
    const tenneTShare = Math.round((tenneT.gwh / tsoTotal) * 100);
    const y2022 = DATA.boxByYear["2022"].median;
    const y2025 = DATA.boxByYear["2025"].median;
    const unitDrop = Math.round((1 - y2025 / y2022) * 100);

    const items = [
      { label: "Peak monthly cost", value: eur(peak.cost), delta: peak.m, deltaClass: "muted" },
      { label: "Latest monthly cost", value: eur(latest.cost), delta: "↓ " + dropPct + "% from peak", deltaClass: "good" },
      { label: "TenneT DE's share of redispatch energy", value: tenneTShare + "%", delta: gwh(tenneT.gwh) + " of " + gwh(tsoTotal), deltaClass: "muted" },
      { label: "Median unit cost, 2022 → 2025", value: eurMwh(y2025) + "/MWh", delta: "↓ " + unitDrop + "% vs. " + eurMwh(y2022), deltaClass: "good" },
    ];
    const row = d3.select("#kpiRow");
    items.forEach(it => {
      const c = row.append("div").attr("class", "kpi");
      c.append("div").attr("class", "label").text(it.label);
      c.append("div").attr("class", "value").text(it.value);
      c.append("div").attr("class", "delta " + it.deltaClass).text(it.delta);
    });
  })();

  // ---------- shared chart shell ----------
  function makeSvg(id, margin) {
    const svg = d3.select("#" + id);
    const vb = svg.attr("viewBox").split(" ").map(Number);
    const width = vb[2], height = vb[3];
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
    return { svg, g, width, height, innerW, innerH };
  }

  function yAxisGrid(g, y, innerW, ticks, formatter) {
    g.append("g").attr("class", "gridlines")
      .selectAll("line")
      .data(y.ticks(ticks))
      .join("line")
      .attr("class", "gridline")
      .attr("x1", 0).attr("x2", innerW)
      .attr("y1", d => y(d)).attr("y2", d => y(d));
    g.append("g").attr("class", "axis")
      .selectAll("text")
      .data(y.ticks(ticks))
      .join("text")
      .attr("x", -10).attr("y", d => y(d))
      .attr("dy", "0.32em").attr("text-anchor", "end")
      .text(d => formatter ? formatter(d) : fmt(d));
  }

  // ================= Chart 1: cost trend (bar + rolling line) =================
  (function chart1() {
    const margin = { top: 40, right: 24, bottom: 34, left: 48 };
    const { g, innerW, innerH } = makeSvg("viz1", margin);
    const x = d3.scaleTime().domain(d3.extent(monthly, d => d.date)).range([0, innerW]);
    const maxCost = d3.max(monthly, d => d.cost);
    const y = d3.scaleLinear().domain([0, maxCost * 1.28]).range([innerH, 0]).nice();

    yAxisGrid(g, y, innerW, 5, v => "€" + fmt(v) + "m");

    g.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(d3.timeYear.every(1)).tickFormat(d3.timeFormat("%Y")).tickSize(0))
      .call(g => g.select(".domain").attr("class", "baseline"));

    const barW = Math.min(14, innerW / monthly.length * 0.62);
    g.append("g").selectAll("rect")
      .data(monthly).join("rect")
      .attr("x", d => x(d.date) - barW / 2)
      .attr("y", d => y(d.cost))
      .attr("width", barW)
      .attr("height", d => innerH - y(d.cost))
      .attr("rx", Math.min(4, barW / 2)).attr("ry", Math.min(4, barW / 2))
      .attr("fill", cssVar("--series-1-soft"))
      .on("mousemove", (evt, d) => {
        showTip(`<strong>${d.m}</strong><div class="row"><span>Monthly cost</span><span>${eur(d.cost)}</span></div>` +
          (d.roll12 ? `<div class="row"><span>12-mo avg</span><span>${eur(d.roll12)}</span></div>` : ""), evt);
      })
      .on("mouseleave", hideTip);

    const line = d3.line().defined(d => d.roll12 != null).x(d => x(d.date)).y(d => y(d.roll12)).curve(d3.curveMonotoneX);
    g.append("path").datum(monthly).attr("d", line)
      .attr("fill", "none").attr("stroke", cssVar("--series-1")).attr("stroke-width", 2);

    g.selectAll("circle.roll")
      .data(monthly.filter(d => d.roll12 != null))
      .join("circle")
      .attr("class", "roll")
      .attr("cx", d => x(d.date)).attr("cy", d => y(d.roll12)).attr("r", 2.4)
      .attr("fill", cssVar("--series-1"))
      .style("opacity", 0)
      .on("mousemove", function (evt, d) {
        d3.select(this).style("opacity", 1);
        showTip(`<strong>${d.m}</strong><div class="row"><span>12-mo avg</span><span>${eur(d.roll12)}</span></div>`, evt);
      })
      .on("mouseleave", function () { d3.select(this).style("opacity", 0); hideTip(); });

    const peak = monthly.reduce((a, b) => (b.cost > a.cost ? b : a));
    const latest = monthly[monthly.length - 1];
    [ [peak, `Peak: ${eur(peak.cost)}`, -8], [latest, `Latest: ${eur(latest.cost)}`, -8] ].forEach(([d, label, dy]) => {
      g.append("text").attr("x", x(d.date)).attr("y", y(d.cost) + dy - 4)
        .attr("text-anchor", d === peak ? "middle" : "end")
        .attr("font-size", 11.5).attr("font-weight", 600)
        .attr("fill", cssVar("--text-secondary")).text(label);
    });

    // data table
    fillTable("table1", ["Month", "Cost (€m)", "12-mo avg (€m)"],
      monthly.map(d => [d.m, fmt1(d.cost), d.roll12 != null ? fmt1(d.roll12) : "—"]));
  })();

  // ================= Chart 2: wind vs volume, indexed =================
  (function chart2() {
    const wv = DATA.windVol;
    const base = wv[0];
    const idx = wv.map(d => ({ m: d.m, vol: d.vol, wind: d.wind, iVol: d.vol / base.vol * 100, iWind: d.wind / base.wind * 100 }));

    const margin = { top: 40, right: 90, bottom: 34, left: 48 };
    const { g, innerW, innerH } = makeSvg("viz2", margin);
    const x = d3.scalePoint().domain(idx.map(d => d.m)).range([0, innerW]);
    const allVals = idx.flatMap(d => [d.iVol, d.iWind]);
    const y = d3.scaleLinear().domain([d3.min(allVals) * 0.9, d3.max(allVals) * 1.08]).range([innerH, 0]).nice();

    yAxisGrid(g, y, innerW, 5, v => fmt(v));
    g.append("text").attr("class", "axis-title").attr("x", -40).attr("y", -22).text("Index (Mar 2025 = 100)");

    g.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickValues(idx.filter((_, i) => i % 2 === 0).map(d => d.m)).tickSize(0))
      .call(g => g.select(".domain").attr("class", "baseline"))
      .selectAll("text").attr("transform", "rotate(-28)").attr("text-anchor", "end").attr("dx", "-0.3em");

    // baseline at 100
    g.append("line").attr("x1", 0).attr("x2", innerW).attr("y1", y(100)).attr("y2", y(100))
      .attr("class", "baseline").attr("stroke-dasharray", "0");
    g.append("text").attr("x", 0).attr("y", y(100) - 6).attr("text-anchor", "start")
      .attr("font-size", 10.5).attr("fill", cssVar("--text-muted")).text("start = 100");

    function drawSeries(key, color, label) {
      const line = d3.line().x(d => x(d.m)).y(d => y(d[key])).curve(d3.curveMonotoneX);
      g.append("path").datum(idx).attr("d", line).attr("fill", "none").attr("stroke", color).attr("stroke-width", 2);
      g.selectAll(`circle.${key}`).data(idx).join("circle").attr("class", key + " dot-ring")
        .attr("cx", d => x(d.m)).attr("cy", d => y(d[key])).attr("r", 4)
        .attr("fill", color)
        .style("stroke", cssVar("--surface-1"))
        .on("mousemove", (evt, d) => showTip(
          `<strong>${d.m}</strong><div class="row"><span>${label}</span><span>${fmt(d[key])}</span></div>` +
          `<div class="row"><span>Actual</span><span>${key === "iVol" ? gwh(d.vol) : fmt(d.wind) + " MW"}</span></div>`, evt))
        .on("mouseleave", hideTip);
      const last = idx[idx.length - 1];
      g.append("text").attr("x", x(last.m) + 8).attr("y", y(last[key])).attr("dy", "0.32em")
        .attr("font-size", 11.5).attr("font-weight", 600).attr("fill", color).text(label);
    }
    drawSeries("iVol", cssVar("--series-1"), "Volume");
    drawSeries("iWind", cssVar("--series-2"), "Wind");

    fillTable("table2", ["Month", "Redispatch volume (GWh)", "Wind generation (avg MW)", "Volume index", "Wind index"],
      idx.map(d => [d.m, fmt1(d.vol), fmt(d.wind), fmt(d.iVol), fmt(d.iWind)]));
  })();

  // ================= Chart 3: unit cost box plot by year =================
  (function chart3() {
    const years = Object.keys(DATA.boxByYear).sort();
    const seqColors = [cssVar("--seq-1"), cssVar("--seq-2"), cssVar("--seq-3"), cssVar("--seq-4"), cssVar("--seq-5")];
    const margin = { top: 30, right: 24, bottom: 30, left: 52 };
    const { g, innerW, innerH } = makeSvg("viz3", margin);
    const x = d3.scaleBand().domain(years).range([0, innerW]).padding(0.42);
    const maxV = d3.max(years, y => DATA.boxByYear[y].max);
    const y = d3.scaleLinear().domain([0, maxV * 1.12]).range([innerH, 0]).nice();

    yAxisGrid(g, y, innerW, 5, v => "€" + fmt(v));
    g.append("text").attr("class", "axis-title").attr("x", -44).attr("y", -14).text("€ / MWh");

    g.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickSize(0))
      .call(g => g.select(".domain").attr("class", "baseline"));

    years.forEach((yr, i) => {
      const b = DATA.boxByYear[yr];
      const color = seqColors[i];
      const cx = x(yr) + x.bandwidth() / 2;
      const boxW = Math.min(46, x.bandwidth() * 0.62);

      g.append("line").attr("x1", cx).attr("x2", cx).attr("y1", y(b.min)).attr("y2", y(b.max))
        .attr("stroke", color).attr("stroke-width", 1.4);
      g.append("line").attr("x1", cx - boxW * 0.22).attr("x2", cx + boxW * 0.22).attr("y1", y(b.min)).attr("y2", y(b.min)).attr("stroke", color).attr("stroke-width", 1.4);
      g.append("line").attr("x1", cx - boxW * 0.22).attr("x2", cx + boxW * 0.22).attr("y1", y(b.max)).attr("y2", y(b.max)).attr("stroke", color).attr("stroke-width", 1.4);

      const boxSel = g.append("rect")
        .attr("x", cx - boxW / 2).attr("y", y(b.q3))
        .attr("width", boxW).attr("height", Math.max(1, y(b.q1) - y(b.q3)))
        .attr("fill", color).attr("opacity", 0.28)
        .attr("stroke", color).attr("stroke-width", 1.4).attr("rx", 3);

      g.append("line").attr("x1", cx - boxW / 2).attr("x2", cx + boxW / 2)
        .attr("y1", y(b.median)).attr("y2", y(b.median)).attr("stroke", color).attr("stroke-width", 2.4);

      // jittered points
      const jitter = d3.randomUniform(-boxW * 0.34, boxW * 0.34);
      const rng = d3.randomLcg(i * 97 + 1);
      const jf = d3.randomUniform.source(rng)(-boxW * 0.34, boxW * 0.34);
      g.selectAll(`circle.pt${i}`).data(b.vals).join("circle").attr("class", `pt${i} dot-ring`)
        .attr("cx", (v, j) => cx + jf())
        .attr("cy", v => y(v)).attr("r", 3)
        .attr("fill", color).style("stroke", cssVar("--surface-1")).attr("fill-opacity", 0.85)
        .on("mousemove", (evt, v) => showTip(`<strong>${yr}</strong><div class="row"><span>Month value</span><span>${eurMwh(v)}/MWh</span></div>`, evt))
        .on("mouseleave", hideTip);

      boxSel.on("mousemove", (evt) => showTip(
        `<strong>${yr}</strong>` +
        `<div class="row"><span>Median</span><span>${eurMwh(b.median)}</span></div>` +
        `<div class="row"><span>Q1–Q3</span><span>${eurMwh(b.q1)}–${eurMwh(b.q3)}</span></div>` +
        `<div class="row"><span>Range</span><span>${eurMwh(b.min)}–${eurMwh(b.max)}</span></div>` +
        `<div class="row"><span>Months</span><span>${b.n}</span></div>`, evt))
        .on("mousemove.move", moveTip)
        .on("mouseleave", hideTip);

      g.append("text").attr("x", cx + boxW / 2 + 6).attr("y", y(b.median)).attr("dy", "0.32em")
        .attr("font-size", 10.5).attr("font-weight", 600).attr("fill", cssVar("--text-secondary"))
        .text("€" + fmt(b.median));
    });

    fillTable("table3", ["Year", "Months", "Min", "Q1", "Median", "Q3", "Max"],
      years.map(yr => { const b = DATA.boxByYear[yr]; return [yr, b.n, eurMwh(b.min), eurMwh(b.q1), eurMwh(b.median), eurMwh(b.q3), eurMwh(b.max)]; }));
  })();

  // ================= Chart 4: TSO horizontal bar =================
  (function chart4() {
    const data = [...DATA.tso].sort((a, b) => b.gwh - a.gwh);
    const margin = { top: 10, right: 90, bottom: 20, left: 100 };
    const { g, innerW, innerH } = makeSvg("viz4", margin);
    const y = d3.scaleBand().domain(data.map(d => d.tso)).range([0, innerH]).padding(0.32);
    const x = d3.scaleLinear().domain([0, d3.max(data, d => d.gwh) * 1.05]).range([0, innerW]);
    const barH = Math.min(24, y.bandwidth());

    g.selectAll("rect").data(data).join("rect")
      .attr("x", 0).attr("y", d => y(d.tso) + (y.bandwidth() - barH) / 2)
      .attr("width", d => x(d.gwh)).attr("height", barH)
      .attr("rx", 4).attr("ry", 4)
      .attr("fill", cssVar("--series-1"))
      .on("mousemove", (evt, d) => showTip(`<strong>${d.tso}</strong><div class="row"><span>Redispatched energy</span><span>${gwh(d.gwh)}</span></div>`, evt))
      .on("mouseleave", hideTip);

    g.selectAll("text.label").data(data).join("text").attr("class", "label")
      .attr("x", -10).attr("y", d => y(d.tso) + y.bandwidth() / 2).attr("dy", "0.32em")
      .attr("text-anchor", "end").attr("font-size", 12.5).attr("fill", cssVar("--text-primary")).text(d => d.tso);

    g.selectAll("text.value").data(data).join("text").attr("class", "value")
      .attr("x", d => x(d.gwh) + 8).attr("y", d => y(d.tso) + y.bandwidth() / 2).attr("dy", "0.32em")
      .attr("font-size", 12).attr("font-weight", 600).attr("fill", cssVar("--text-secondary"))
      .text(d => gwh(d.gwh));

    fillTable("table4", ["TSO", "Redispatched energy (GWh)"], data.map(d => [d.tso, fmt(d.gwh)]));
  })();

  // ================= Chart 5: stacked area conventional/renewable =================
  (function chart5() {
    const margin = { top: 40, right: 24, bottom: 34, left: 52 };
    const { g, innerW, innerH } = makeSvg("viz5", margin);
    const x = d3.scaleTime().domain(d3.extent(monthly, d => d.date)).range([0, innerW]);
    const totals = monthly.map(d => d.volCon + d.volRen);
    const y = d3.scaleLinear().domain([0, d3.max(totals) * 1.14]).range([innerH, 0]).nice();

    yAxisGrid(g, y, innerW, 5, v => fmt(v));
    g.append("text").attr("class", "axis-title").attr("x", -46).attr("y", -22).text("GWh / month");

    g.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(d3.timeYear.every(1)).tickFormat(d3.timeFormat("%Y")).tickSize(0))
      .call(g => g.select(".domain").attr("class", "baseline"));

    const stack = d3.stack().keys(["volCon", "volRen"]);
    const series = stack(monthly);
    const colors = [cssVar("--series-1"), cssVar("--series-3")];
    const labels = { volCon: "Conventional", volRen: "Renewable" };

    const area = d3.area().x((d, i) => x(monthly[i].date)).y0(d => y(d[0])).y1(d => y(d[1])).curve(d3.curveMonotoneX);

    series.forEach((s, i) => {
      g.append("path").datum(s).attr("d", area)
        .attr("fill", colors[i]).attr("fill-opacity", 0.55)
        .attr("stroke", colors[i]).attr("stroke-width", 1.2);
    });

    // separator line between the two bands (surface-colored)
    const sepLine = d3.line().x((d, i) => x(monthly[i].date)).y((d) => y(d[1])).curve(d3.curveMonotoneX);
    g.append("path").datum(series[0]).attr("d", sepLine).attr("fill", "none")
      .attr("stroke", cssVar("--surface-1")).attr("stroke-width", 2);

    // hover: vertical hit area
    const bisect = d3.bisector(d => d.date).left;
    const hoverLine = g.append("line").attr("y1", 0).attr("y2", innerH).attr("stroke", cssVar("--text-muted")).attr("stroke-width", 1).style("opacity", 0);
    g.append("rect").attr("width", innerW).attr("height", innerH).attr("fill", "transparent")
      .on("mousemove", function (evt) {
        const mx = d3.pointer(evt, this)[0];
        const x0 = x.invert(mx);
        const i = Math.min(monthly.length - 1, Math.max(0, bisect(monthly, x0)));
        const d = monthly[i];
        hoverLine.attr("x1", x(d.date)).attr("x2", x(d.date)).style("opacity", 1);
        showTip(`<strong>${d.m}</strong>` +
          `<div class="row"><span>Conventional</span><span>${gwh(d.volCon)}</span></div>` +
          `<div class="row"><span>Renewable</span><span>${gwh(d.volRen)}</span></div>` +
          `<div class="row"><span>Total</span><span>${gwh(d.volCon + d.volRen)}</span></div>`, evt);
      })
      .on("mouseleave", () => { hoverLine.style("opacity", 0); hideTip(); });

    fillTable("table5", ["Month", "Conventional (GWh)", "Renewable (GWh)", "Total (GWh)"],
      monthly.map(d => [d.m, fmt1(d.volCon), fmt1(d.volRen), fmt1(d.volCon + d.volRen)]));
  })();

  // ================= Chart 6: dumbbell reductions/increases =================
  (function chart6() {
    const categories = [
      { key: "reduction", label: "Reductions", color: cssVar("--series-1") },
      { key: "increase", label: "Increases", color: cssVar("--series-2") },
    ];
    const margin = { top: 30, right: 130, bottom: 40, left: 40 };
    const { g, innerW, innerH } = makeSvg("viz6", margin);
    const x = d3.scalePoint().domain(["2022–23 avg", "2025–26 avg"]).range([40, innerW - 40]);
    const allVals = categories.flatMap(c => [DATA.early[c.key], DATA.recent[c.key]]);
    const y = d3.scaleLinear().domain([0, d3.max(allVals) * 1.2]).range([innerH, 0]).nice();

    yAxisGrid(g, y, innerW, 5, v => fmt(v));
    g.append("text").attr("class", "axis-title").attr("x", -20).attr("y", -14).text("GWh / month (avg)");

    g.append("g").attr("class", "axis")
      .attr("transform", `translate(0,${innerH})`)
      .call(d3.axisBottom(x).tickSize(0))
      .call(g => g.select(".domain").attr("class", "baseline"));

    categories.forEach(c => {
      const p0 = { x: x("2022–23 avg"), y: y(DATA.early[c.key]) };
      const p1 = { x: x("2025–26 avg"), y: y(DATA.recent[c.key]) };
      g.append("line").attr("x1", p0.x).attr("y1", p0.y).attr("x2", p1.x).attr("y2", p1.y)
        .attr("stroke", c.color).attr("stroke-width", 2.5);
      [[p0, DATA.early[c.key]], [p1, DATA.recent[c.key]]].forEach(([p, val]) => {
        g.append("circle").attr("cx", p.x).attr("cy", p.y).attr("r", 6)
          .attr("fill", c.color).attr("class", "dot-ring").style("stroke", cssVar("--surface-1"))
          .on("mousemove", (evt) => showTip(`<strong>${c.label}</strong><div class="row"><span>Value</span><span>${gwh(val)}</span></div>`, evt))
          .on("mouseleave", hideTip);
      });
      g.append("text").attr("x", p1.x + 12).attr("y", p1.y).attr("dy", "0.32em")
        .attr("font-size", 12.5).attr("font-weight", 600).attr("fill", c.color)
        .text(`${c.label}: ${fmt(DATA.recent[c.key])}`);
      g.append("text").attr("x", p0.x - 12).attr("y", p0.y).attr("dy", "0.32em")
        .attr("text-anchor", "end")
        .attr("font-size", 11.5).attr("fill", cssVar("--text-secondary")).text(fmt(DATA.early[c.key]));
    });

    fillTable("table6", ["Category", "2022–23 avg (GWh)", "2025–26 avg (GWh)", "Change"],
      categories.map(c => [c.label, fmt1(DATA.early[c.key]), fmt1(DATA.recent[c.key]),
        (DATA.recent[c.key] >= DATA.early[c.key] ? "+" : "") + fmt1(DATA.recent[c.key] - DATA.early[c.key])]));
  })();

  function fillTable(id, headers, rows) {
    const table = d3.select("#" + id);
    table.append("thead").append("tr").selectAll("th").data(headers).join("th").text(d => d);
    const tbody = table.append("tbody");
    rows.forEach(r => {
      tbody.append("tr").selectAll("td").data(r).join("td").text(d => d);
    });
  }
})();
