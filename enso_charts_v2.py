"""
ENSO Phase vs Weather Scatter Chart Generator  v2
==================================================
Swap cities by changing the three config lines below, then run:
    python3 enso_charts_v2.py

Interactive features
--------------------
- Dual-handle year-range slider  (dims out-of-range dots; updates phase means & n= counts live)
- Phase isolation on click        (click any dot or legend label to spotlight that phase)
- Decade colour toggle            (recolour dots by decade; click dot or legend to isolate a decade)
- PNG export button               (downloads current view at high resolution)
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────
EXCEL_FILE   = "ENSO_Phase_vs_Snowfall_scatter_NYC.xlsx"
CITY_TAB     = "NYC"
CITY_NAME    = "Central Park, NY"
OUTPUT_DIR   = Path(".")
JITTER_SEED  = 42
JITTER_WIDTH = 0.25
# ───────────────────────────────────────────────────────────────────────────

PHASES = [
    (1, "Strong<br>La Niña",   "Strong La Niña",   "#9B59B6"),
    (2, "Moderate<br>La Niña", "Moderate La Niña", "#5B9BD5"),
    (3, "Weak<br>La Niña",     "Weak La Niña",     "#85C1E9"),
    (4, "Neutral",             "Neutral",           "#27AE60"),
    (5, "Weak<br>El Niño",     "Weak El Niño",     "#F4D03F"),
    (6, "Moderate<br>El Niño", "Moderate El Niño", "#E67E22"),
    (7, "Strong<br>El Niño",   "Strong El Niño",   "#E74C3C"),
    (8, "Super<br>El Niño",    "Super El Niño",    "#922B21"),
]

DECADE_COLORS = {
    "1860s": "#FFE119", "1870s": "#FF7F00", "1880s": "#E6194B",
    "1890s": "#C030C0", "1900s": "#4363D8", "1910s": "#42D4F4",
    "1920s": "#3CB44B", "1930s": "#F032E6", "1940s": "#BFEF45",
    "1950s": "#F8A5C2", "1960s": "#469990", "1970s": "#B48EF0",
    "1980s": "#C87F3B", "1990s": "#50C878", "2000s": "#FF6B6B",
    "2010s": "#00CED1", "2020s": "#FFA07A",
}


# ── Data loading ────────────────────────────────────────────────────────────
def load_data(excel_file, city_tab):
    df = pd.read_excel(excel_file, sheet_name=city_tab, header=2)
    df.columns = ["Season", "Temp", "Snowfall", "ENSO_Code"]
    df = df.dropna(subset=["ENSO_Code", "Season", "Temp", "Snowfall"])
    df["ENSO_Code"]  = df["ENSO_Code"].astype(int)
    df["Start_Year"] = df["Season"].astype(str).str[:4].astype(int)
    df["Decade"]     = df["Start_Year"].apply(lambda y: f"{(y // 10) * 10}s")
    return df.reset_index(drop=True)


def add_jitter(df):
    rng = np.random.default_rng(JITTER_SEED)
    phase_to_idx = {code: i for i, (code, *_) in enumerate(PHASES)}
    df = df.copy()
    df["x_pos"] = df["ENSO_Code"].map(phase_to_idx).astype(float)
    for code in df["ENSO_Code"].unique():
        mask = df["ENSO_Code"] == code
        df.loc[mask, "x_pos"] += rng.uniform(-JITTER_WIDTH, JITTER_WIDTH, mask.sum())
    return df


def build_app_data(df):
    phase_map = {code: (lbl_br, lbl, color) for code, lbl_br, lbl, color in PHASES}
    points = [
        {
            "season":       row.Season,
            "temp":         round(float(row.Temp), 1),
            "snowfall":     round(float(row.Snowfall), 1),
            "enso_code":    int(row.ENSO_Code),
            "start_year":   int(row.Start_Year),
            "decade":       row.Decade,
            "x_pos":        round(float(row.x_pos), 4),
            "phase_color":  phase_map[int(row.ENSO_Code)][2],
            "decade_color": DECADE_COLORS.get(row.Decade, "#888"),
        }
        for row in df.itertuples()
    ]
    phases = [
        {"code": code, "label_br": lbl_br, "label": lbl, "color": color, "x_center": i}
        for i, (code, lbl_br, lbl, color) in enumerate(PHASES)
    ]
    present_decades = sorted({p["decade"] for p in points})
    decades = [
        {"label": d, "color": DECADE_COLORS.get(d, "#888")}
        for d in present_decades
    ]
    return {
        "points":    points,
        "phases":    phases,
        "decades":   decades,
        "city_name": CITY_NAME,
        "min_year":  int(df["Start_Year"].min()),
        "max_year":  int(df["Start_Year"].max()),
    }


# ── HTML template ───────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>__CITY_NAME__ — ENSO Weather Charts</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  background: #0d0d0d;
  color: #eee;
  font-family: Arial, sans-serif;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 16px;
  gap: 32px;
  min-height: 100vh;
}

.chart-card {
  background: #161616;
  border: 1px solid #2a2a2a;
  border-radius: 12px;
  padding: 22px 22px 16px;
  width: min(960px, 100%);
}

.chart-title {
  text-align: center;
  font-size: 17px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 3px;
  line-height: 1.3;
}

.chart-subtitle {
  text-align: center;
  font-size: 12px;
  color: #777;
  margin-bottom: 14px;
  min-height: 16px;
}

/* ── Controls ── */
.controls {
  display: flex;
  gap: 14px;
  align-items: flex-end;
  flex-wrap: wrap;
  background: #1e1e1e;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  padding: 13px 16px;
  margin-bottom: 6px;
}

.ctrl-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: #666;
  margin-bottom: 5px;
}

.ctrl-year-display {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: bold;
  color: #ccc;
  margin-bottom: 8px;
}

/* Dual-range slider */
.range-wrap {
  flex: 1;
  min-width: 220px;
}

.dual-slider {
  position: relative;
  height: 22px;
  display: flex;
  align-items: center;
}

.dual-slider .track-bg {
  position: absolute;
  inset: 0;
  margin: auto;
  height: 4px;
  border-radius: 2px;
  background: #3a3a3a;
}

.dual-slider .track-fill {
  position: absolute;
  height: 4px;
  border-radius: 2px;
  background: #5B9BD5;
  pointer-events: none;
  top: 50%;
  transform: translateY(-50%);
}

.dual-slider input[type=range] {
  position: absolute;
  width: 100%;
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
  pointer-events: none;
  outline: none;
  height: 0;
}

.dual-slider input[type=range]::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 18px; height: 18px;
  border-radius: 50%;
  background: #5B9BD5;
  border: 2px solid #fff;
  cursor: ew-resize;
  pointer-events: all;
  box-shadow: 0 1px 4px rgba(0,0,0,.6);
  transition: background .15s;
}
.dual-slider input[type=range]::-webkit-slider-thumb:hover { background: #7ab4e8; }
.dual-slider input[type=range]::-moz-range-thumb {
  width: 18px; height: 18px;
  border-radius: 50%;
  background: #5B9BD5;
  border: 2px solid #fff;
  cursor: ew-resize;
  pointer-events: all;
}

/* Buttons */
.btn-group { display: flex; gap: 8px; align-items: flex-end; flex-shrink: 0; }

.btn {
  padding: 7px 13px;
  border-radius: 6px;
  border: 1px solid #3a3a3a;
  background: #252525;
  color: #ccc;
  font-size: 12px;
  cursor: pointer;
  transition: background .14s, border-color .14s, color .14s;
  white-space: nowrap;
  line-height: 1.4;
}
.btn:hover { background: #333; border-color: #555; color: #fff; }
.btn.active { background: #1e3a60; border-color: #5B9BD5; color: #fff; }

.btn-export {
  border-color: #27AE60;
  color: #27AE60;
  background: #0f1f14;
}
.btn-export:hover { background: #27AE60; color: #fff; border-color: #27AE60; }

/* Legend */
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-top: 10px;
  padding: 10px 14px;
  background: #111;
  border: 1px solid #222;
  border-radius: 6px;
  min-height: 38px;
}

.leg-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #bbb;
  cursor: pointer;
  padding: 3px 7px;
  border-radius: 4px;
  border: 1px solid transparent;
  transition: background .1s, border-color .1s;
  user-select: none;
}
.leg-item:hover { background: #222; border-color: #333; }
.leg-item.isolated { border-color: #5B9BD5; background: #1a2a3a; color: #fff; }
.leg-item.no-click { cursor: default; }
.leg-item.no-click:hover { background: transparent; border-color: transparent; }

.leg-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.leg-diamond { width: 9px; height: 9px; transform: rotate(45deg); flex-shrink: 0; background: #aaa; }
.leg-divider { width: 1px; background: #2a2a2a; align-self: stretch; margin: 0 3px; }

.hint {
  text-align: center;
  font-size: 11px;
  color: #444;
  margin-top: 7px;
}
</style>
</head>
<body>

<div class="chart-card">
  <div class="chart-title" id="title-temp"></div>
  <div class="chart-subtitle" id="sub-temp"></div>
  <div class="controls">
    <div class="range-wrap">
      <div class="ctrl-label">Year Range Filter</div>
      <div class="ctrl-year-display">
        <span id="yr-min-temp"></span>
        <span id="yr-max-temp"></span>
      </div>
      <div class="dual-slider">
        <div class="track-bg"></div>
        <div class="track-fill" id="fill-temp"></div>
        <input type="range" id="rlo-temp">
        <input type="range" id="rhi-temp">
      </div>
    </div>
    <div class="btn-group">
      <button class="btn" id="dbtn-temp"   onclick="toggleDecade('temp')">🎨 Color by Decade</button>
      <button class="btn btn-export"        onclick="exportPNG('temp')">⬇ Export PNG</button>
      <button class="btn"                   onclick="resetAll('temp')">↺ Reset</button>
    </div>
  </div>
  <div id="plt-temp"></div>
  <div class="legend" id="leg-temp"></div>
  <div class="hint">Click any dot or legend label to isolate that phase &nbsp;·&nbsp; Double-click chart to clear</div>
</div>

<div class="chart-card">
  <div class="chart-title" id="title-snow"></div>
  <div class="chart-subtitle" id="sub-snow"></div>
  <div class="controls">
    <div class="range-wrap">
      <div class="ctrl-label">Year Range Filter</div>
      <div class="ctrl-year-display">
        <span id="yr-min-snow"></span>
        <span id="yr-max-snow"></span>
      </div>
      <div class="dual-slider">
        <div class="track-bg"></div>
        <div class="track-fill" id="fill-snow"></div>
        <input type="range" id="rlo-snow">
        <input type="range" id="rhi-snow">
      </div>
    </div>
    <div class="btn-group">
      <button class="btn" id="dbtn-snow"   onclick="toggleDecade('snow')">🎨 Color by Decade</button>
      <button class="btn btn-export"        onclick="exportPNG('snow')">⬇ Export PNG</button>
      <button class="btn"                   onclick="resetAll('snow')">↺ Reset</button>
    </div>
  </div>
  <div id="plt-snow"></div>
  <div class="legend" id="leg-snow"></div>
  <div class="hint">Click any dot or legend label to isolate that phase &nbsp;·&nbsp; Double-click chart to clear</div>
</div>

<script>
const D = __APP_DATA__;

// ── State ───────────────────────────────────────────────────────────────────
const ST = {
  temp: { lo: D.min_year, hi: D.max_year, decade: false, iso: null, iso_decade: null },
  snow: { lo: D.min_year, hi: D.max_year, decade: false, iso: null, iso_decade: null },
};

const N_PHASES = D.phases.length;
const Y_FIELD  = { temp: 'temp', snow: 'snowfall' };
const Y_LABEL  = { temp: 'Temperature (°F)', snow: 'Snowfall (in)' };
const TITLES   = {
  temp: `${D.city_name} — DJF Mean Temperature by ENSO Phase`,
  snow: `${D.city_name} — Seasonal Snowfall by ENSO Phase`,
};

// ── Opacity logic ────────────────────────────────────────────────────────────
function opacity(pt, cid) {
  const s = ST[cid];
  const inR = pt.start_year >= s.lo && pt.start_year <= s.hi;
  // In decade mode, isolation is by decade; otherwise by phase
  const inP = s.decade
    ? (s.iso_decade === null || pt.decade === s.iso_decade)
    : (s.iso        === null || pt.enso_code === s.iso);
  if ( inR &&  inP) return 0.88;
  if ( inR && !inP) return 0.10;
  if (!inR &&  inP) return 0.15;
  return 0.04;
}

function color(pt, cid) {
  return ST[cid].decade ? pt.decade_color : pt.phase_color;
}

// ── Stats helpers ────────────────────────────────────────────────────────────
function filteredPts(cid) {
  const s = ST[cid];
  return D.points.filter(p => p.start_year >= s.lo && p.start_year <= s.hi);
}

function phaseStats(cid) {
  const yf  = Y_FIELD[cid];
  const fps = filteredPts(cid);
  const out = {};
  D.phases.forEach(ph => {
    const vals = fps.filter(p => p.enso_code === ph.code).map(p => p[yf]);
    out[ph.code] = {
      mean:  vals.length ? vals.reduce((a,b)=>a+b,0)/vals.length : null,
      count: vals.length,
    };
  });
  return out;
}

// ── Annotations ─────────────────────────────────────────────────────────────
function makeAnnotations(cid) {
  const stats = phaseStats(cid);
  const ann = D.phases.map(ph => ({
    x: ph.x_center, y: -0.135, xref:'x', yref:'paper',
    text: `n=${stats[ph.code].count}`,
    showarrow: false,
    font: { size: 10, color: '#666' },
  }));
  ann.push(
    { x:1.0, y:-0.185, xref:'x', yref:'paper', text:'<b>LA NIÑA</b>',
      font:{color:'#85C1E9',size:13}, showarrow:false },
    { x:5.5, y:-0.185, xref:'x', yref:'paper', text:'<b>EL NIÑO</b>',
      font:{color:'#E74C3C',size:13}, showarrow:false },
  );
  return ann;
}

// ── Initial chart build ──────────────────────────────────────────────────────
function buildChart(cid) {
  const yf     = Y_FIELD[cid];
  const stats  = phaseStats(cid);
  const traces = [];

  // Dot traces — one per phase
  D.phases.forEach(ph => {
    const pts = D.points.filter(p => p.enso_code === ph.code);
    traces.push({
      type:'scatter', mode:'markers',
      x: pts.map(p => p.x_pos),
      y: pts.map(p => p[yf]),
      marker: {
        color:   pts.map(p => color(p, cid)),
        opacity: pts.map(p => opacity(p, cid)),
        size: 9,
        line: { width:0.5, color:'rgba(0,0,0,.25)' },
      },
      customdata: pts.map(p => [p.season, p[yf], p.decade]),
      hovertemplate: '<b>%{customdata[0]}</b><br>' + Y_LABEL[cid] + ': %{customdata[1]}<extra></extra>',
      showlegend: false,
      _phase: ph.code,
    });
  });

  // Diamond mean traces — one per phase
  D.phases.forEach(ph => {
    const m = stats[ph.code].mean;
    traces.push({
      type:'scatter', mode:'markers',
      x: [ph.x_center],
      y: [m],
      marker: {
        symbol:'diamond', size:16,
        color: ph.color,
        line: { width:2, color:'white' },
        opacity: 1,
      },
      customdata: [[ph.label, m !== null ? m.toFixed(1) : '—']],
      hovertemplate: '<b>%{customdata[0]}</b><br>Phase mean: %{customdata[1]}<extra></extra>',
      showlegend: false,
      _diamond: true,
      _phase: ph.code,
    });
  });

  const layout = {
    paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'#111',
    font: { color:'#ddd', family:'Arial' },
    xaxis: {
      tickmode:'array',
      tickvals: D.phases.map(p=>p.x_center),
      ticktext: D.phases.map(p=>p.label_br),
      tickfont: { size:11, color:'#bbb' },
      showgrid:false, zeroline:false,
      range: [-0.6, N_PHASES-0.4],
    },
    yaxis: {
      title: { text:Y_LABEL[cid], font:{size:13} },
      gridcolor:'rgba(255,255,255,.06)',
      zeroline:false,
    },
    annotations: makeAnnotations(cid),
    hoverlabel: { bgcolor:'#1e1e1e', font:{color:'#fff'}, bordercolor:'#444' },
    margin: { l:65, r:20, t:10, b:110 },
    showlegend: false,
    height: 500,
  };

  Plotly.newPlot(`plt-${cid}`, traces, layout, { responsive:true, displayModeBar:false });

  // Click → isolate phase or decade depending on mode
  document.getElementById(`plt-${cid}`).on('plotly_click', ev => {
    const tr = ev.points[0].data;
    if (tr._diamond) return;
    if (ST[cid].decade) {
      const clickedDecade = ev.points[0].customdata[2];   // season decade stored below
      ST[cid].iso_decade = ST[cid].iso_decade === clickedDecade ? null : clickedDecade;
    } else {
      ST[cid].iso = ST[cid].iso === tr._phase ? null : tr._phase;
    }
    refresh(cid);
  });

  // Double-click → clear isolation
  document.getElementById(`plt-${cid}`).on('plotly_doubleclick', () => {
    ST[cid].iso = null;
    refresh(cid);
    return false;  // prevent Plotly's default zoom-reset
  });
}

// ── Refresh (after any state change) ────────────────────────────────────────
function refresh(cid) {
  const yf    = Y_FIELD[cid];
  const stats = phaseStats(cid);
  const div   = document.getElementById(`plt-${cid}`);

  // Update dot opacities + colours
  const opArr = [], colArr = [];
  D.phases.forEach(ph => {
    const pts = D.points.filter(p => p.enso_code === ph.code);
    opArr.push(pts.map(p => opacity(p, cid)));
    colArr.push(pts.map(p => color(p, cid)));
  });
  Plotly.restyle(div,
    { 'marker.opacity': opArr, 'marker.color': colArr },
    [...Array(N_PHASES).keys()]
  );

  // Update diamond y-values (filtered mean)
  const diamY = D.phases.map(ph => [stats[ph.code].mean]);
  Plotly.restyle(div, { y: diamY },
    D.phases.map((_,i) => i + N_PHASES)
  );

  // Update n= annotations
  Plotly.relayout(div, { annotations: makeAnnotations(cid) });

  updateSubtitle(cid);
  buildLegend(cid);
}

// ── Subtitle ────────────────────────────────────────────────────────────────
function updateSubtitle(cid) {
  const s = ST[cid];
  const n = filteredPts(cid).length;
  const full = s.lo === D.min_year && s.hi === D.max_year;
  const rangeStr = full
    ? `${D.min_year}–${D.max_year + 1}  ·  ${n} seasons`
    : `Filtered ${s.lo}–${s.hi + 1}  ·  ${n} of ${D.points.length} seasons`;
  document.getElementById(`sub-${cid}`).textContent = rangeStr;
}

// ── Legend ───────────────────────────────────────────────────────────────────
function buildLegend(cid) {
  const el = document.getElementById(`leg-${cid}`);
  el.innerHTML = '';

  if (ST[cid].decade) {
    // Decade items — clickable to isolate
    const present = [...new Set(D.points.map(p=>p.decade))].sort();
    present.forEach(d => {
      const dc   = D.decades.find(x=>x.label===d)?.color ?? '#888';
      const item = Object.assign(document.createElement('div'), { className:'leg-item' });
      if (ST[cid].iso_decade === d) item.classList.add('isolated');
      item.innerHTML = `<div class="leg-dot" style="background:${dc}"></div>${d}`;
      item.onclick = () => {
        ST[cid].iso_decade = ST[cid].iso_decade === d ? null : d;
        refresh(cid);
      };
      el.appendChild(item);
    });
  } else {
    // Phase items (clickable to isolate)
    D.phases.forEach(ph => {
      const item = Object.assign(document.createElement('div'), { className:'leg-item' });
      if (ST[cid].iso === ph.code) item.classList.add('isolated');
      item.innerHTML = `<div class="leg-dot" style="background:${ph.color}"></div>${ph.label}`;
      item.onclick = () => {
        ST[cid].iso = ST[cid].iso === ph.code ? null : ph.code;
        refresh(cid);
      };
      el.appendChild(item);
    });
    // Diamond mean key
    const div = Object.assign(document.createElement('div'), { className:'leg-divider' });
    el.appendChild(div);
    const mi = Object.assign(document.createElement('div'), { className:'leg-item no-click' });
    mi.innerHTML = `<div class="leg-diamond"></div>Phase mean`;
    el.appendChild(mi);
  }
}

// ── Dual-range slider ─────────────────────────────────────────────────────────
function initSlider(cid) {
  const rlo  = document.getElementById(`rlo-${cid}`);
  const rhi  = document.getElementById(`rhi-${cid}`);
  const fill = document.getElementById(`fill-${cid}`);
  const lblL = document.getElementById(`yr-min-${cid}`);
  const lblR = document.getElementById(`yr-max-${cid}`);

  [rlo, rhi].forEach(r => {
    r.min = D.min_year; r.max = D.max_year;
  });
  rlo.value = D.min_year;
  rhi.value = D.max_year;

  function sync() {
    let lo = parseInt(rlo.value), hi = parseInt(rhi.value);
    const GAP = 5;
    if (lo > hi - GAP) { lo = hi - GAP; rlo.value = lo; }
    if (hi < lo + GAP) { hi = lo + GAP; rhi.value = hi; }
    const span  = D.max_year - D.min_year;
    const leftP = ((lo - D.min_year) / span) * 100;
    const wP    = ((hi - lo) / span) * 100;
    fill.style.left  = leftP + '%';
    fill.style.width = wP    + '%';
    lblL.textContent = lo;
    lblR.textContent = hi;
    ST[cid].lo = lo;
    ST[cid].hi = hi;
    refresh(cid);
  }

  rlo.addEventListener('input', sync);
  rhi.addEventListener('input', sync);
  sync();
}

// ── Toggle decade mode ────────────────────────────────────────────────────────
function toggleDecade(cid) {
  ST[cid].decade = !ST[cid].decade;
  if (!ST[cid].decade) ST[cid].iso_decade = null;   // clear decade isolation when leaving decade mode
  document.getElementById(`dbtn-${cid}`).classList.toggle('active', ST[cid].decade);
  refresh(cid);
}

// ── Reset ─────────────────────────────────────────────────────────────────────
function resetAll(cid) {
  ST[cid] = { lo:D.min_year, hi:D.max_year, decade:false, iso:null, iso_decade:null };
  document.getElementById(`rlo-${cid}`).value = D.min_year;
  document.getElementById(`rhi-${cid}`).value = D.max_year;
  document.getElementById(`dbtn-${cid}`).classList.remove('active');
  initSlider(cid);   // re-syncs fill bar and labels
  refresh(cid);
}

// ── Export PNG ────────────────────────────────────────────────────────────────
function exportPNG(cid) {
  const s    = ST[cid];
  const city = D.city_name.replace(/[^a-z0-9]/gi,'_');
  const rng  = (s.lo===D.min_year && s.hi===D.max_year) ? '' : `_${s.lo}-${s.hi}`;
  Plotly.downloadImage(`plt-${cid}`, {
    format:'png', width:1600, height:900,
    filename:`ENSO_${cid}_${city}${rng}`,
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  ['temp','snow'].forEach(cid => {
    document.getElementById(`title-${cid}`).textContent = TITLES[cid];
    buildChart(cid);
    initSlider(cid);
    updateSubtitle(cid);
    buildLegend(cid);
  });
});
</script>
</body>
</html>
"""


def main():
    df       = load_data(EXCEL_FILE, CITY_TAB)
    df       = add_jitter(df)
    app_data = build_app_data(df)

    html = HTML.replace("__APP_DATA__", json.dumps(app_data, ensure_ascii=False)) \
               .replace("__CITY_NAME__", CITY_NAME)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUT_DIR / f"ENSO_Charts_{CITY_TAB}.html"
    out.write_text(html, encoding="utf-8")
    print(f"✓  Saved: {out}")

    stats = df.groupby("ENSO_Code")[["Temp","Snowfall"]].agg(["mean","median","count"])
    stats.index = [next(lbl for c,_,lbl,_ in PHASES if c==i) for i in stats.index]
    print("\nPhase summary stats:\n", stats.round(1).to_string())


if __name__ == "__main__":
    main()
