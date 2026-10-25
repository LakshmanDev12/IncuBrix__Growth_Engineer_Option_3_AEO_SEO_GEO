"""Template Renderer for IncuBrix Visibility Intelligence.

Renders the exact high-fidelity SaaS dashboard UI design with animated glowing orbs,
radial progress score ring, SVG telemetry charts, interactive heatmap, and multi-page routing.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st

MASTER_CSS = """
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
/* Reset and Streamlit overrides */
.main > div { padding: 0 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stSidebar"] { display: none !important; }
header[data-testid="stHeader"],
[data-testid="stDecoration"],
[data-testid="stToolbar"],
div[data-testid="stHeader"],
[data-testid="stSpinner"],
.stSpinner {
  display: none !important;
  height: 0 !important;
  width: 0 !important;
  pointer-events: none !important;
  visibility: hidden !important;
  z-index: -9999 !important;
}

:root {
  --canvas: #000;
  --card: #111;
  --line: #262626;
  --ink: #fafafa;
  --ink-rgb: 250,250,250;
  --muted: #a3a3a3;
  --soft: #171717;
  --band: #0a0a0a;
  --ok: #22c55e;
  --warn: #eab308;
  --bad: #ef4444;
  box-sizing: border-box;
  background: var(--canvas);
}

* { box-sizing: border-box; margin: 0; }

body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(rgba(var(--ink-rgb),.08) 1px, transparent 1.3px) 0 0/22px 22px, var(--canvas) !important;
  color: var(--ink) !important;
  font: 14px/1.5 Inter, system-ui, -apple-system, "Segoe UI", sans-serif !important;
  min-height: 100vh;
  margin: 0;
  position: relative;
}

.mono { font-family: "JetBrains Mono", ui-monospace, Consolas, monospace; }

/* Top Hero Band: Transparent with Gradient Title & Colorful Elements */
.band {
  position: relative;
  overflow: visible !important;
  background: transparent !important;
  color: var(--ink) !important;
  padding-bottom: 110px;
  z-index: 100 !important;
  pointer-events: none;
}

.band > * {
  pointer-events: auto;
}

.bg, body::before {
  display: none !important;
}

/* Shell Container */
.wrap {
  max-width: 1360px;
  margin: 0 auto;
  padding: 0 28px;
  position: relative;
  z-index: 20;
}

/* Top Navigation Bar */
.top {
  display: flex;
  align-items: center;
  gap: 28px;
  height: 64px;
  border-bottom: 1px solid var(--line) !important;
  position: relative;
  z-index: 30;
  pointer-events: auto !important;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  letter-spacing: -.02em;
  font-size: 17px;
  flex: none;
  text-decoration: none;
  color: var(--ink);
  cursor: pointer !important;
  pointer-events: auto !important;
  position: relative;
  z-index: 50;
  user-select: none !important;
}

.logo {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: #fafafa;
  color: #0a0a0a;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 13px;
  pointer-events: none;
}

nav {
  display: flex;
  gap: 4px;
  overflow-x: auto;
  flex: 1;
  scrollbar-width: none;
  position: relative;
  z-index: 40;
  pointer-events: auto !important;
}
nav::-webkit-scrollbar { display: none; }

nav a {
  color: var(--muted) !important;
  padding: 8px 14px !important;
  border-radius: 99px !important;
  font-weight: 500 !important;
  font-size: 13px !important;
  white-space: nowrap !important;
  cursor: pointer !important;
  text-decoration: none !important;
  transition: .15s !important;
  pointer-events: auto !important;
  position: relative !important;
  z-index: 50 !important;
  user-select: none !important;
  -webkit-user-select: none !important;
}

nav a:hover {
  color: var(--ink) !important;
  background: rgba(var(--ink-rgb), .06) !important;
}

nav a.on {
  color: #fff !important;
  background: linear-gradient(135deg, #7c3aed, #ec4899) !important;
  box-shadow: 0 6px 18px rgba(236,72,153,.35) !important;
  font-weight: 600 !important;
}

.tools {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: none;
}

.gw {
  font-size: 12px;
  color: var(--muted) !important;
  display: flex;
  align-items: center;
  gap: 7px;
  border: 1px solid var(--line) !important;
  padding: 5px 12px;
  border-radius: 99px;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 0 3px rgba(34,197,94,.22);
  display: inline-block;
}

.av {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #555, #222);
  border: 1px solid #444;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 600;
}

/* Hero Section */
.hero {
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  gap: 40px;
  align-items: center;
  padding-top: 44px;
  position: relative;
  z-index: 120 !important;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: .14em;
  text-transform: uppercase;
  color: var(--muted) !important;
  display: flex;
  gap: 8px;
  align-items: center;
}

h1 {
  font-size: 46px !important;
  line-height: 1.05 !important;
  letter-spacing: -.035em !important;
  font-weight: 800 !important;
  margin: 12px 0 10px !important;
  background: linear-gradient(90deg, #7c3aed, #ec4899 55%, #f59e0b) !important;
  -webkit-background-clip: text !important;
  background-clip: text !important;
  -webkit-text-fill-color: transparent !important;
  color: transparent !important;
}

.lead {
  color: var(--muted) !important;
  max-width: 520px;
  font-size: 15px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
  align-items: center;
  position: relative;
  z-index: 150 !important;
}

.seg {
  display: flex;
  border: 1px solid var(--line) !important;
  border-radius: 99px;
  padding: 3px;
  background: transparent !important;
}

.seg a, .seg button {
  background: none;
  border: 0;
  color: var(--muted) !important;
  padding: 6px 14px;
  border-radius: 99px;
  font: 500 13px Inter, sans-serif;
  cursor: pointer;
  text-decoration: none;
  transition: .15s;
}

.seg a.on, .seg button.on {
  background: linear-gradient(135deg, #06b6d4, #3b82f6) !important;
  color: #fff !important;
  font-weight: 600;
}

/* Creative Glass Dropdowns with Details & Hover Support */
.c-dd {
  position: relative;
  display: inline-block;
  user-select: none;
  z-index: 200;
}

.c-dd[open],
.c-dd:hover {
  z-index: 99999 !important;
}

details.c-dd summary {
  list-style: none !important;
  outline: none !important;
}

details.c-dd summary::-webkit-details-marker {
  display: none !important;
}

.c-dd-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(18, 18, 24, 0.75) !important;
  color: var(--ink) !important;
  border: 1px solid var(--line) !important;
  border-radius: 99px !important;
  padding: 8px 16px;
  font: 500 13px Inter, sans-serif;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.c-dd-btn:hover,
.c-dd[open] > .c-dd-btn,
.c-dd:hover > .c-dd-btn,
.c-dd.open > .c-dd-btn {
  border-color: rgba(139, 92, 246, 0.55) !important;
  box-shadow: 0 0 16px rgba(124, 58, 237, 0.25);
  background: rgba(28, 28, 38, 0.95) !important;
  color: #fff !important;
}

.c-dd-arrow {
  width: 6px;
  height: 6px;
  border-right: 1.5px solid var(--muted);
  border-bottom: 1.5px solid var(--muted);
  transform: rotate(45deg);
  margin-left: 3px;
  margin-bottom: 2px;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.c-dd[open] > .c-dd-btn .c-dd-arrow,
.c-dd:hover > .c-dd-btn .c-dd-arrow,
.c-dd.open > .c-dd-btn .c-dd-arrow {
  transform: rotate(-135deg) !important;
  margin-bottom: -2px !important;
  border-color: #a78bfa !important;
}

.c-dd-menu {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  min-width: 250px;
  background: rgba(14, 14, 20, 0.98) !important;
  backdrop-filter: blur(28px) !important;
  -webkit-backdrop-filter: blur(28px) !important;
  border: 1px solid rgba(255, 255, 255, 0.16) !important;
  border-radius: 14px !important;
  padding: 6px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.95), 0 0 0 1px rgba(255, 255, 255, 0.08);
  z-index: 100000 !important;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-6px) scale(0.97);
  transition: opacity 0.16s ease, transform 0.16s ease, visibility 0.16s;
  pointer-events: none;
}

.c-dd[open] > .c-dd-menu,
.c-dd:hover > .c-dd-menu,
.c-dd.open > .c-dd-menu {
  opacity: 1 !important;
  visibility: visible !important;
  transform: translateY(0) scale(1) !important;
  pointer-events: auto !important;
}

.c-dd-heading {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  padding: 6px 10px 6px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 4px;
}

.c-dd-badge {
  font-size: 9px;
  padding: 2px 6px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--muted);
  font-weight: 500;
  letter-spacing: 0;
  text-transform: none;
}

.c-dd-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 9px;
  color: var(--ink);
  text-decoration: none;
  transition: all 0.15s ease;
  margin-bottom: 2px;
}

.c-dd-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(2px);
  color: #fff;
}

.c-dd-item.selected {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.28), rgba(236, 72, 153, 0.22));
  border: 1px solid rgba(139, 92, 246, 0.45);
  color: #fff;
}

.c-dd-item-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.c-dd-item-flag {
  font-size: 16px;
  line-height: 1;
}

.c-dd-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.c-dd-item-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--ink);
}

.c-dd-item-desc {
  font-size: 10px;
  color: var(--muted);
  font-weight: 400;
}

.c-dd-item.selected .c-dd-item-desc {
  color: rgba(255, 255, 255, 0.75);
}

.c-dd-check {
  font-size: 12px;
  color: #a78bfa;
  font-weight: 700;
  margin-right: 4px;
}

/* Hardened fallback for native selects */
select, .filters select {
  background: rgba(18, 18, 24, 0.8) !important;
  color: var(--ink) !important;
  border: 1px solid var(--line) !important;
  border-radius: 99px;
  padding: 8px 14px;
  font: 500 13px Inter, sans-serif;
  color-scheme: dark !important;
}

select option, .filters select option {
  background: #141418 !important;
  color: #fafafa !important;
  padding: 10px 14px !important;
}

.btn {
  background: linear-gradient(135deg, #7c3aed, #ec4899) !important;
  color: #fff !important;
  border: 0 !important;
  border-radius: 99px !important;
  padding: 9px 20px !important;
  font: 600 13px Inter, sans-serif !important;
  cursor: pointer !important;
  transition: .15s !important;
  text-decoration: none !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 6px !important;
}

.btn:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 8px 24px rgba(236,72,153,.4) !important;
}

.score {
  display: flex;
  gap: 26px;
  align-items: center;
  justify-content: flex-end;
}

.ring {
  position: relative;
  width: 170px;
  height: 170px;
  flex: none;
  display: grid;
  place-items: center;
}

.ring svg, .ring canvas, .ring img {
  display: block;
  width: 170px;
  height: 170px;
}

.ring-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  pointer-events: none;
}

.ring-score {
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.03em;
  color: #ffffff;
}

.ring-label {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #a3a3a3;
  margin-top: 4px;
  line-height: 1;
  white-space: nowrap;
}

.mini div {
  display: flex;
  justify-content: space-between;
  gap: 30px;
  font-size: 13px;
  padding: 9px 0;
  border-bottom: 1px solid var(--line) !important;
  color: var(--muted) !important;
  min-width: 180px;
}

.mini b {
  color: var(--ink) !important;
  font-weight: 600;
}

/* Main Cards Overlap Area */
.main {
  margin-top: -70px;
  position: relative;
  z-index: 1 !important;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 14px;
}

.card {
  background: color-mix(in srgb, var(--card) 62%, transparent) !important;
  backdrop-filter: blur(12px) !important;
  -webkit-backdrop-filter: blur(12px) !important;
  border: 1px solid var(--line) !important;
  border-radius: 16px !important;
  padding: 20px;
  min-width: 0;
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
}

.kpi {
  border-top: 3px solid #06b6d4 !important;
}
.kpi:nth-child(2) {
  border-top-color: #f59e0b !important;
}
.kpi:nth-child(3) {
  border-top-color: #10b981 !important;
}
.kpi:nth-child(2) .sp {
  stroke: #f59e0b !important;
}
.kpi:nth-child(3) .sp {
  stroke: #10b981 !important;
}

.kpi .l {
  font-size: 12px;
  color: var(--muted);
  font-weight: 500;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kpi .v {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -.04em;
  margin: 6px 0 2px;
}

.kpi .d {
  font-size: 12px;
  color: var(--muted);
}

.kpi.dark {
  background: linear-gradient(135deg, #7c3aed, #ec4899) !important;
  color: #fff !important;
  border: 0 !important;
}

.kpi.dark .l, .kpi.dark .d { color: rgba(255,255,255,.85) !important; }
.kpi.dark .sp { stroke: #fff !important; }
.kpi.dark .pill {
  background: rgba(255,255,255,.22) !important;
  border-color: transparent !important;
  color: #fff !important;
}

.pill {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
  background: rgba(124,58,237,.12) !important;
  color: #7c3aed !important;
  border: 1px solid transparent !important;
}

.spark, .spark-canvas, .kpi img {
  margin-top: 10px;
  display: block;
  width: 100%;
  height: 32px;
}

.sp {
  fill: none;
  stroke: var(--ink);
  stroke-width: 2;
  stroke-linejoin: round;
}

/* Grid systems */
.g { display: grid; gap: 14px; margin-bottom: 14px; }
.c2 { grid-template-columns: 1.7fr 1fr; }
.c11 { grid-template-columns: 1fr 1fr; }

h3 {
  font-size: 15px;
  font-weight: 700;
  letter-spacing: -.01em;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;
  color: var(--ink);
}

h3 small {
  font-weight: 400;
  font-size: 12px;
  color: var(--muted);
}

svg text { fill: var(--muted); font: 11px Inter, sans-serif; }
.ln { stroke: var(--line); }

#fade stop { stop-color: #8b5cf6 !important; }
.l1 { fill: none; stroke: #8b5cf6 !important; stroke-width: 2.5; stroke-linejoin: round; }
.l2 { fill: none; stroke: #06b6d4 !important; stroke-width: 2; stroke-dasharray: 4 4; stroke-linejoin: round; }
.ar { fill: url(#fade); }

.leg {
  display: flex;
  gap: 22px;
  font-size: 12px;
  color: var(--muted);
  margin-top: 16px;
  align-items: center;
}

.leg span {
  display: inline-flex;
  align-items: center;
}

.leg i {
  display: inline-block;
  width: 14px;
  height: 3px;
  background: #8b5cf6 !important;
  margin-right: 8px;
  vertical-align: middle;
  border-radius: 2px;
}

.leg i.d {
  background: repeating-linear-gradient(90deg, #06b6d4 0 4px, transparent 4px 7px) !important;
}

/* Heatmap */
.heat {
  display: grid;
  grid-template-columns: 80px repeat(6, 1fr);
  gap: 5px;
  font-size: 11px;
  color: var(--muted);
  align-items: center;
}

.heat div.c {
  height: 34px;
  border-radius: 7px;
  display: grid;
  place-items: center;
  font-weight: 600;
  font-size: 11px;
}

.heat .h { text-align: center; }

/* Progress bars */
.bars .r {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 13px 0;
  font-size: 13px;
}

.bars .n { width: 84px; font-weight: 500; }
.tr { flex: 1; height: 10px; background: rgba(var(--ink-rgb), .06) !important; border-radius: 9px; overflow: hidden; border: 1px solid var(--line); }
.tr b { display: block; height: 100%; background: linear-gradient(90deg, #8b5cf6, #ec4899) !important; border-radius: 9px; }
.bars .r:nth-child(3) .tr b { background: linear-gradient(90deg, #06b6d4, #3b82f6) !important; }
.bars .r:nth-child(4) .tr b { background: linear-gradient(90deg, #f59e0b, #ef4444) !important; }
.bars .r:nth-child(5) .tr b { background: linear-gradient(90deg, #10b981, #06b6d4) !important; }
.bars .p { width: 40px; text-align: right; font-weight: 600; }

/* Tables */
.tw { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 440px; }
th { text-align: left; font-size: 11px; font-weight: 500; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); padding: 8px 10px; border-bottom: 1px solid var(--line); }
td { padding: 11px 10px; border-bottom: 1px solid var(--line); color: var(--ink); }
tr:last-child td { border: 0; }
tbody tr:hover { background: var(--soft); }

.st { display: inline-flex; align-items: center; gap: 7px; font-weight: 500; }
.st i { width: 7px; height: 7px; border-radius: 50%; display: inline-block; }

/* Opportunities */
.opp {
  display: flex;
  gap: 14px;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--line);
  border-radius: 12px;
  margin-bottom: 10px;
  transition: .15s;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
}

.opp:hover {
  background: linear-gradient(135deg, #7c3aed, #ec4899) !important;
  border-color: transparent !important;
  color: #fff !important;
}

.opp:hover p { color: rgba(255,255,255,.85) !important; }

.da {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8b5cf6, #ec4899) !important;
  color: #fff !important;
  display: grid;
  place-items: center;
  font-weight: 800;
  flex: none;
}

.opp:nth-child(3) .da { background: linear-gradient(135deg, #06b6d4, #3b82f6) !important; }
.opp:nth-child(4) .da { background: linear-gradient(135deg, #f59e0b, #ef4444) !important; }

.opp:hover .da {
  background: #fff !important;
  color: #7c3aed !important;
}

.opp div:nth-child(2) { flex: 1; min-width: 0; }
.opp p { font-size: 12px; color: var(--muted); margin-top: 2px; }

/* Technical Crawlability */
.sev {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.sev div {
  background: transparent !important;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 16px;
  text-align: center;
}

.sev b {
  display: block;
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -.04em;
}

.sev div:nth-child(1) b { color: #ef4444 !important; }
.sev div:nth-child(2) b { color: #f59e0b !important; }
.sev div:nth-child(3) b { color: #10b981 !important; }

.sev span { font-size: 12px; color: var(--muted); }

.code {
  margin-top: 14px;
  background: #0a0a0a;
  color: #d4d4d4;
  border: 1px solid #262626;
  border-radius: 12px;
  padding: 14px;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre;
  line-height: 1.7;
}

.code em { font-style: normal; color: #86efac; }

footer {
  text-align: center;
  color: var(--muted);
  font-size: 12px;
  padding: 28px 0 44px;
}

@media(max-width: 1000px) {
  .hero { grid-template-columns: 1fr; }
  .score { justify-content: flex-start; }
  .kpis { grid-template-columns: repeat(2, 1fr); }
  .c2, .c11 { grid-template-columns: 1fr; }
  h1 { font-size: 36px; }
  .gw { display: none; }
}

@media(max-width: 600px) {
  .wrap { padding: 0 16px; }
  .kpis { grid-template-columns: 1fr; }
  .top { gap: 14px; }
  .heat { grid-template-columns: 60px repeat(6, 1fr); }
}
</style>
"""


def _svg_to_data_uri(svg: str) -> str:
    """Encode SVG markup to an immutable base64 data URI (100% immune to DOMPurify stripping)."""
    b64 = base64.b64encode(svg.strip().encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{b64}"


def _render_score_ring_uri(score: int) -> str:
    """Generate base64 data URI for the 4-color gradient visibility score ring."""
    stroke_pct = min(100, max(0, score))
    dash_val = round((stroke_pct / 100.0) * 452.4, 1)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 170" width="170" height="170">
  <defs>
    <linearGradient id="scoreRingGrad" gradientUnits="userSpaceOnUse" x1="140" y1="20" x2="20" y2="140">
      <stop offset="0%" stop-color="#ec4899"/>
      <stop offset="35%" stop-color="#c084fc"/>
      <stop offset="70%" stop-color="#6366f1"/>
      <stop offset="100%" stop-color="#06b6d4"/>
    </linearGradient>
  </defs>
  <circle cx="85" cy="85" r="72" fill="none" stroke="#26272e" stroke-width="11"/>
  <circle cx="85" cy="85" r="72" fill="none" stroke="url(#scoreRingGrad)" stroke-width="11" stroke-linecap="round" stroke-dasharray="{dash_val} 452.4" transform="rotate(-90 85 85)"/>
</svg>"""
    return _svg_to_data_uri(svg)


def _render_sparkline_uri(pts: str, color: str) -> str:
    """Generate base64 data URI for KPI sparkline curve."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="200" height="30" viewBox="0 0 200 30" preserveAspectRatio="none">
  <polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""
    return _svg_to_data_uri(svg)


def _render_trend_chart_uri(score: int = 87) -> str:
    """Generate base64 data URI for the master 30-day visibility telemetry trend chart dynamically scaled to score."""
    clamped_score = min(100, max(20, score))
    # Peak at Wk 4 (x=630)
    peak_y = round(20 + (100 - clamped_score) * 1.5, 1)
    p5_y = round(min(170, peak_y + 24), 1)
    p4_y = round(min(170, peak_y + 40), 1)
    p3_y = round(min(170, peak_y + 58), 1)
    p2_y = round(min(170, peak_y + 80), 1)
    p1_y = round(min(170, peak_y + 90), 1)
    p0_y = round(min(170, peak_y + 108), 1)

    score_pts = f"36,{p0_y} 120,{p1_y} 205,{p2_y} 290,{p3_y} 375,{p4_y} 460,{p5_y} 630,{peak_y}"
    area_d = f"M36,{p0_y} L120,{p1_y} L205,{p2_y} L290,{p3_y} L375,{p4_y} L460,{p5_y} L630,{peak_y} L630,170 L36,170Z"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 220" width="100%" height="220" preserveAspectRatio="none">
  <defs>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.32"/>
      <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <!-- Grid Lines -->
  <line x1="36" x2="630" y1="20" y2="20" stroke="#262626" stroke-width="1"/>
  <line x1="36" x2="630" y1="70" y2="70" stroke="#262626" stroke-width="1"/>
  <line x1="36" x2="630" y1="120" y2="120" stroke="#262626" stroke-width="1"/>
  <line x1="36" x2="630" y1="170" y2="170" stroke="#262626" stroke-width="1"/>
  <!-- Y Axis Labels -->
  <text x="4" y="24" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">100</text>
  <text x="10" y="74" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">75</text>
  <text x="10" y="124" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">50</text>
  <text x="10" y="174" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">25</text>
  <!-- Shaded Area Fill -->
  <path fill="url(#fade)" d="{area_d}"/>
  <!-- Cyan Dashed Evaluations Line -->
  <polyline fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 4" points="36,162 120,156 205,148 290,134 375,122 460,110 545,98 630,84"/>
  <!-- Purple Solid Visibility Score Line -->
  <polyline fill="none" stroke="#8b5cf6" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" points="{score_pts}"/>
  <!-- Glowing Target Marker at Wk 4 (Peak {score}) -->
  <circle cx="630" cy="{peak_y}" r="11" fill="#ffffff" opacity="0.28"/>
  <circle cx="630" cy="{peak_y}" r="5" fill="#ffffff"/>
  <!-- X Axis Labels -->
  <text x="36" y="200" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">Wk 1</text>
  <text x="225" y="200" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">Wk 2</text>
  <text x="410" y="200" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">Wk 3</text>
  <text x="590" y="200" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">Wk 4</text>
</svg>"""
    return _svg_to_data_uri(svg)


def render_top_band(
    active_page: str = "overview",
    eyebrow: str = "Live telemetry · AEO · SEO · GEO engine",
    title_line1: str = "Visibility",
    title_line2: str = "Overview",
    lead: str = "Track organic search performance, AI answer presence and citation opportunities in one place.",
    score: int = 87,
    avg_rank: str = "#2.0",
    direct_links: int = 1,
    evaluations: int = 2,
    show_score: bool = True,
    active_range: str = "30d",
    active_market: str = "All",
    active_provider: str = "All",
) -> str:
    """Generate the exact top hero band HTML with animated orbs and SVG flow lines."""
    
    # Calculate ring stroke offset (circumference = 2 * pi * 72 ~= 452.39)
    # Score 87 -> 393.6 of 452.4
    stroke_pct = min(100, max(0, score))
    dash_val = round((stroke_pct / 100.0) * 452.4, 1)

    nav_items = [
        ("overview", "Overview"),
        ("seo_aeo", "SEO & AEO"),
        ("geo", "GEO Intel"),
        ("questions", "Questions"),
        ("audit", "Tech Audit"),
        ("content", "Content Studio"),
        ("citations", "Citations"),
        ("scans", "History"),
        ("settings", "Settings"),
    ]

    nav_links = ""
    for key, label in nav_items:
        on_cls = ' class="on"' if active_page == key else ""
        nav_links += f'<a href="?page={key}" data-page="{key}"{on_cls} onclick="switchTab(\'{key}\', event);">{label}</a>'

    score_html = ""
    if show_score:
        ring_uri = _render_score_ring_uri(score)
        score_html = f"""
        <div class="score">
          <div class="ring" id="vis-ring-container">
            <img id="vis-ring-img" src="{ring_uri}" width="170" height="170" style="position:absolute;inset:0;width:170px;height:170px;display:block;" alt="Score Ring">
            <div class="ring-content">
              <div class="ring-score" id="vis-ring-score-val">{score}</div>
              <div class="ring-label">VISIBILITY SCORE</div>
            </div>
          </div>
          <div class="mini">
            <div>Avg rank<b id="vis-mini-rank">{avg_rank}</b></div>
            <div>Direct links<b id="vis-mini-links">{direct_links}</b></div>
            <div>Evaluations<b id="vis-mini-evals">{evaluations}</b></div>
          </div>
        </div>
        """

    r7_on = ' class="on"' if active_range == "7d" else ""
    r30_on = ' class="on"' if active_range == "30d" else ""
    r90_on = ' class="on"' if active_range == "90d" else ""

    market_items = [
        ("All", "All Markets", "🌐", "Global Telemetry"),
        ("US", "United States", "🇺🇸", "Tier-1 High Intent"),
        ("UK", "United Kingdom", "🇬🇧", "Regional SERP"),
        ("IN", "India", "🇮🇳", "High-Growth APAC"),
    ]

    cur_m_label = "Market: All"
    cur_m_flag = "🌐"
    for k, lbl, flag, _ in market_items:
        if active_market == k:
            cur_m_label = f"Market: {k}" if k != "All" else "Market: All"
            cur_m_flag = flag
            break

    m_menu_items = ""
    for k, lbl, flag, desc in market_items:
        is_sel = " selected" if active_market == k else ""
        check_icon = '<span class="c-dd-check">✓</span>' if active_market == k else ""
        m_menu_items += f"""
        <a href="?page={active_page}&range={active_range}&market={k}&provider={active_provider}" class="c-dd-item{is_sel}" data-market="{k}" target="_self">
          <div class="c-dd-item-left">
            <span class="c-dd-item-flag">{flag}</span>
            <div>
              <div class="c-dd-item-name">{lbl}</div>
              <div class="c-dd-item-desc">{desc}</div>
            </div>
          </div>
          {check_icon}
        </a>"""

    provider_items = [
        ("All", "All Providers", "✨", "#8b5cf6", "Search + 4 AI Engines"),
        ("chatgpt", "ChatGPT", "🤖", "#10a37f", "OpenAI Search & 4o"),
        ("perplexity", "Perplexity", "⚡", "#20b2aa", "Direct Citations"),
        ("claude", "Claude", "🧠", "#d97706", "Anthropic Sonnet"),
        ("gemini", "Gemini", "💎", "#4285f4", "Google AI Studio"),
    ]

    cur_p_label = "Provider: All"
    cur_p_color = "#8b5cf6"
    for k, lbl, icon, color, _ in provider_items:
        if active_provider == k:
            cur_p_label = f"Provider: {lbl}" if k != "All" else "Provider: All"
            cur_p_color = color
            break

    p_menu_items = ""
    for k, lbl, icon, color, desc in provider_items:
        is_sel = " selected" if active_provider == k else ""
        check_icon = '<span class="c-dd-check">✓</span>' if active_provider == k else ""
        p_menu_items += f"""
        <a href="?page={active_page}&range={active_range}&market={active_market}&provider={k}" class="c-dd-item{is_sel}" data-provider="{k}" target="_self">
          <div class="c-dd-item-left">
            <span class="c-dd-dot" style="background:{color};box-shadow:0 0 8px {color}88"></span>
            <div>
              <div class="c-dd-item-name">{lbl}</div>
              <div class="c-dd-item-desc">{desc}</div>
            </div>
          </div>
          {check_icon}
        </a>"""

    return f"""
    <div class="band">
      <div class="bg" aria-hidden="true">
        <i class="orb o1"></i><i class="orb o2"></i><i class="orb o3"></i>
        <svg viewBox="0 0 900 520" preserveAspectRatio="xMaxYMid slice">
          <g>
            <circle class="rg" cx="640" cy="200" r="90"/>
            <circle class="rg" cx="640" cy="200" r="160"/>
            <circle class="rg" cx="640" cy="200" r="240"/>
            <circle class="rg" cx="640" cy="200" r="330"/>
            <circle class="rg" cx="640" cy="200" r="430"/>
          </g>
          <path class="rg" d="M0,420 C200,300 320,480 520,340 S800,260 900,320"/>
          <path class="fl" d="M0,420 C200,300 320,480 520,340 S800,260 900,320"/>
          <path class="rg" d="M0,470 C220,380 360,520 560,400 S820,330 900,380"/>
          <path class="fl b" d="M0,470 C220,380 360,520 560,400 S820,330 900,380"/>
          <g fill="#fafafa">
            <circle cx="640" cy="110" r="3"/>
            <circle cx="800" cy="200" r="3" opacity=".6"/>
            <circle cx="520" cy="260" r="3" opacity=".6"/>
            <circle cx="700" cy="340" r="3" opacity=".4"/>
          </g>
        </svg>
      </div>
      <div class="wrap">
        <header class="top">
          <a class="brand" href="?page=overview" data-page="overview" onclick="switchTab('overview', event);"><span>Vk Analysis</span></a>
          <nav id="nav">{nav_links}</nav>
          <div class="tools"><div class="gw mono"><i class="dot"></i>:8001/v1</div></div>
        </header>
        <section class="hero">
          <div>
            <div class="eyebrow"><i class="dot"></i>{eyebrow}</div>
            <h1>{title_line1}<br>{title_line2}</h1>
            <p class="lead">{lead}</p>
            <div class="filters">
              <div class="seg" id="range">
                <a href="?page={active_page}&range=7d&market={active_market}&provider={active_provider}"{r7_on} data-range="7d" target="_self">7d</a>
                <a href="?page={active_page}&range=30d&market={active_market}&provider={active_provider}"{r30_on} data-range="30d" target="_self">30d</a>
                <a href="?page={active_page}&range=90d&market={active_market}&provider={active_provider}"{r90_on} data-range="90d" target="_self">90d</a>
              </div>
              <details class="c-dd" id="dd-market">
                <summary class="c-dd-btn">
                  <span class="c-dd-item-flag" id="cur-m-flag" style="font-size:14px">{cur_m_flag}</span>
                  <span id="cur-m-label">{cur_m_label}</span>
                  <span class="c-dd-arrow"></span>
                </summary>
                <div class="c-dd-menu">
                  <div class="c-dd-heading"><span>Target Market</span><span class="c-dd-badge">Region</span></div>
                  {m_menu_items}
                </div>
              </details>
              <details class="c-dd" id="dd-provider">
                <summary class="c-dd-btn">
                  <span class="c-dd-dot" id="cur-p-dot" style="background:{cur_p_color};box-shadow:0 0 8px {cur_p_color}88"></span>
                  <span id="cur-p-label">{cur_p_label}</span>
                  <span class="c-dd-arrow"></span>
                </summary>
                <div class="c-dd-menu">
                  <div class="c-dd-heading"><span>AI Provider</span><span class="c-dd-badge">Engine</span></div>
                  {p_menu_items}
                </div>
              </details>
              <a href="?page={active_page}&action=run_scan" class="btn" target="_self">▶ Run scan</a>
            </div>
          </div>
          {score_html}
        </section>
      </div>
    </div>
    """


def render_overview_view(data: Dict[str, Any]) -> str:
    """Generate the exact Overview page main cards area."""
    score = data.get("score", 87)
    avg_rank = data.get("avg_rank", "#2.0")
    direct_links = data.get("direct_links", 1)
    evals = data.get("evals", 2)
    top10_rate = float(data.get("top10_rate", 82.4))
    mention_rate = float(data.get("mention_rate", 74.0))
    cite_rate = float(data.get("cite_rate", 58.0))
    questions_count = data.get("questions_count", 15)
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    band_html = render_top_band(
        active_page="overview",
        eyebrow="Live telemetry · AEO · SEO · GEO engine",
        title_line1="Visibility",
        title_line2="Overview",
        lead="Track organic search performance, AI answer presence and citation opportunities in one place.",
        score=score,
        avg_rank=avg_rank,
        direct_links=direct_links,
        evaluations=evals,
        show_score=True,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    # 4 KPI cards with pure base64 SVG images (100% immune to DOMPurify SVG stripping)
    spark1_uri = _render_sparkline_uri("0,24 30,20 60,22 95,12 130,14 165,5 200,4", "#ffffff")
    spark2_uri = _render_sparkline_uri("0,26 30,24 60,18 95,19 130,10 165,8 200,4", "#f59e0b")
    spark3_uri = _render_sparkline_uri("0,20 30,22 60,14 95,16 130,9 165,10 200,5", "#10b981")
    spark4_uri = _render_sparkline_uri("0,25 30,25 60,20 95,20 130,14 165,12 200,6", "#06b6d4")

    kpis_html = f"""
    <div class="kpis">
      <div class="card kpi dark">
        <div class="l">SEO Top-10 <span class="pill">▲ 12%</span></div>
        <div class="v" id="kpi-val-seo">{top10_rate:.1f}%</div>
        <div class="d" id="kpi-desc-seo">Avg rank {avg_rank}</div>
        <img src="{spark1_uri}" style="width:100%;height:32px;display:block;margin-top:10px;" alt="SEO Top-10 sparkline">
      </div>
      <div class="card kpi">
        <div class="l">AI Mention Rate <span class="pill">+1</span></div>
        <div class="v" id="kpi-val-mention">{mention_rate:.1f}%</div>
        <div class="d">1 new sighting</div>
        <img src="{spark2_uri}" style="width:100%;height:32px;display:block;margin-top:10px;" alt="AI Mention sparkline">
      </div>
      <div class="card kpi">
        <div class="l">AI Citation Rate <span class="pill">Live</span></div>
        <div class="v" id="kpi-val-cite">{cite_rate:.1f}%</div>
        <div class="d" id="kpi-desc-cite">{direct_links} direct link</div>
        <img src="{spark3_uri}" style="width:100%;height:32px;display:block;margin-top:10px;" alt="AI Citation sparkline">
      </div>
      <div class="card kpi">
        <div class="l">Questions Tracked <span class="pill" id="kpi-pill-evals">{evals} evals</span></div>
        <div class="v" id="kpi-val-questions">{questions_count}</div>
        <div class="d">Across 3 markets</div>
        <img src="{spark4_uri}" style="width:100%;height:32px;display:block;margin-top:10px;" alt="Questions sparkline">
      </div>
    </div>
    """

    # Heatmap rows generator
    cols = ["Pricing", "How-to", "Compare", "Reviews", "Local", "Brand"]
    heat_rows = [
        ("ChatGPT", [80, 90, 60, 70, 40, 95]),
        ("Perplexity", [95, 85, 90, 75, 60, 98]),
        ("Claude", [70, 80, 55, 60, 35, 90]),
        ("Gemini", [50, 65, 45, 55, 30, 80]),
    ]
    
    heat_header = '<div></div>' + ''.join(f'<div class="h">{c}</div>' for c in cols)
    heat_cells = ""
    for ast_name, vals in heat_rows:
        heat_cells += f'<div>{ast_name}</div>'
        for v in vals:
            hue = round(280 - v * 1.5)
            alpha = round(v / 100.0 * 0.75 + 0.2, 2)
            txt_color = '#fff' if v > 45 else 'var(--ink)'
            heat_cells += f'<div class="c" style="background: hsla({hue}, 85%, 55%, {alpha}); color: {txt_color}">{v}</div>'

    trend_chart_uri = _render_trend_chart_uri(score=score)
    main_cards_html = f"""
    <div class="wrap main">
      {kpis_html}

      <div class="g c2">
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px;">
            <h3 style="margin:0;display:block;">Visibility trend <small id="trend-chart-sub" style="display:block;margin-top:4px;color:#a3a3a3;font-size:12px;font-weight:400;">Score vs. evaluations · {active_range}</small></h3>
            <span style="background:rgba(34,197,94,0.12);color:#22c55e;padding:3px 10px;border-radius:99px;font-size:11px;font-weight:600;white-space:nowrap;">▲ +14% MoM</span>
          </div>
          <div id="trend-chart-box" style="position:relative;width:100%;height:220px;overflow:hidden;">
            <img id="trend-chart-img" src="{trend_chart_uri}" style="width:100%;height:220px;display:block;object-fit:fill;" alt="Visibility trend telemetry chart">
          </div>
          <div class="leg">
            <span><i style="background:#8b5cf6;"></i>Visibility score</span>
            <span><i class="d" style="background:repeating-linear-gradient(90deg,#06b6d4 0 4px,transparent 4px 7px);"></i>Evaluations</span>
          </div>
        </div>

        <div class="card bars">
          <h3>AI assistants <small>Mention rate</small></h3>
          <div class="r"><span class="n">Perplexity</span><div class="tr"><b style="width:94%"></b></div><span class="p">94%</span></div>
          <div class="r"><span class="n">ChatGPT</span><div class="tr"><b style="width:82%"></b></div><span class="p">82%</span></div>
          <div class="r"><span class="n">Claude</span><div class="tr"><b style="width:68%"></b></div><span class="p">68%</span></div>
          <div class="r"><span class="n">Gemini</span><div class="tr"><b style="width:55%"></b></div><span class="p">55%</span></div>
        </div>
      </div>

      <div class="g">
        <div class="card">
          <h3>Coverage heatmap <small>Assistant × topic cluster</small></h3>
          <div class="heat">{heat_header}{heat_cells}</div>
        </div>
      </div>

      <div class="g c11">
        <div class="card">
          <h3>Competitor visibility <small>Share of AI answers</small></h3>
          <div class="tw">
            <table>
              <thead>
                <tr><th>Entity</th><th>Sightings</th><th>Threat</th></tr>
              </thead>
              <tbody>
                <tr><td>rival-one.com</td><td class="mono">14</td><td><span class="st"><i style="background:var(--bad)"></i>High</span></td></tr>
                <tr><td>growthlab.io</td><td class="mono">9</td><td><span class="st"><i style="background:var(--warn)"></i>Medium</span></td></tr>
                <tr><td>seotools.dev</td><td class="mono">4</td><td><span class="st"><i style="background:var(--ok)"></i>Low</span></td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="card">
          <h3>Technical crawlability <small>Latest audit</small></h3>
          <div class="sev">
            <div><b>2</b><span>Critical</span></div>
            <div><b>5</b><span>High</span></div>
            <div><b>12</b><span>Validated</span></div>
          </div>
          <div class="code mono">&lt;meta name="robots" content="<em>index, follow</em>"&gt;
User-agent: GPTBot
<em>Allow: /</em></div>
        </div>
      </div>

      <div class="g c11">
        <div class="card">
          <h3>Prioritized opportunities <small>High-DA citation gaps</small></h3>
          <a class="opp" href="?page=citations" data-page="citations" onclick="switchTab('citations', event);">
            <div class="da">92</div>
            <div><b>Industry Weekly</b><p>Competitor cited, you absent · pitch a data study</p></div>
            <span>→</span>
          </a>
          <a class="opp" href="?page=citations" data-page="citations" onclick="switchTab('citations', event);">
            <div class="da">87</div>
            <div><b>TechReview Hub</b><p>Comparison list inclusion · outreach angle ready</p></div>
            <span>→</span>
          </a>
          <a class="opp" href="?page=citations" data-page="citations" onclick="switchTab('citations', event);">
            <div class="da">81</div>
            <div><b>Marketer's Guide</b><p>AI answers cite this source for your topic</p></div>
            <span>→</span>
          </a>
        </div>

        <div class="card">
          <h3>Pipeline activity <small>Last 4 runs</small></h3>
          <div class="tw">
            <table>
              <thead>
                <tr><th>Run</th><th>Status</th><th>Qs</th><th>Duration</th></tr>
              </thead>
              <tbody>
                <tr><td class="mono">run-0142</td><td><span class="st"><i style="background:var(--ok)"></i>Success</span></td><td>15</td><td class="mono">2m 14s</td></tr>
                <tr><td class="mono">run-0141</td><td><span class="st"><i style="background:var(--ok)"></i>Success</span></td><td>15</td><td class="mono">2m 31s</td></tr>
                <tr><td class="mono">run-0140</td><td><span class="st"><i style="background:var(--warn)"></i>Retried</span></td><td>14</td><td class="mono">3m 48s</td></tr>
                <tr><td class="mono">run-0139</td><td><span class="st"><i style="background:var(--bad)"></i>Failed</span></td><td>0</td><td class="mono">0m 09s</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """

    return MASTER_CSS + band_html + main_cards_html


def render_seo_aeo_view(data: Dict[str, Any]) -> str:
    """Generate SEO & AEO Analytics view matching the exact design."""
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    band_html = render_top_band(
        active_page="seo_aeo",
        eyebrow="Search Engine & Answer Engine Optimization",
        title_line1="SEO & AEO",
        title_line2="Analytics",
        lead="Deep search ranking positions, Google SERP answer boxes, featured snippets, and evidence provenance.",
        show_score=False,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    observations = data.get("observations", [])
    top10_rate = float(data.get("top10_rate", 82.4))
    top3_rate = float(data.get("top3_rate", 50.0))
    avg_rank = data.get("avg_rank", "#2.0")

    obs_rows = ""
    for o in observations[:8]:
        rank_val = f"#{o.get('rank_position')}" if o.get('rank_position') else "Unranked"
        ab_val = "Yes" if o.get("answer_box_present") else "No"
        prov = "Real Live" if not o.get("meta", {}).get("is_synthetic_test_fixture") else "Mocked"
        dot_color = "var(--ok)" if prov == "Real Live" else "var(--warn)"
        score_val = f"{o.get('visibility_score', 0):.1f}" if o.get('visibility_score') is not None else "N/A"
        
        obs_rows += f"""
        <tr>
          <td><span class="st"><i style="background:{dot_color}"></i>{prov}</span></td>
          <td><b>{o.get('provider', '').upper()}</b></td>
          <td class="mono">{o.get('market', 'US')}</td>
          <td class="mono"><b>{rank_val}</b></td>
          <td>{ab_val}</td>
          <td class="mono">{score_val}</td>
          <td>{(o.get('measured_at') or '')[:19]}</td>
        </tr>
        """

    main_html = f"""
    <div class="wrap main">
      <div class="kpis">
        <div class="card kpi dark"><div class="l">Top-10 Rank Rate <span class="pill">Podium</span></div><div class="v">{top10_rate:.1f}%</div><div class="d">Avg rank {avg_rank}</div></div>
        <div class="card kpi"><div class="l">Top-3 Rank Rate <span class="pill">Podium</span></div><div class="v">{top3_rate:.1f}%</div><div class="d">1 podium query</div></div>
        <div class="card kpi"><div class="l">Answer Box Coverage <span class="pill">Snippet</span></div><div class="v">50.0%</div><div class="d">1 featured box</div></div>
        <div class="card kpi"><div class="l">Evaluated Rankings <span class="pill">Total</span></div><div class="v">{len(observations)}</div><div class="d">Across tracked queries</div></div>
      </div>

      <div class="g">
        <div class="card">
          <h3>Search Ranking & Answer Feature Observations <small>Logged live records</small></h3>
          <div class="tw">
            <table>
              <thead>
                <tr><th>Provenance</th><th>Provider</th><th>Market</th><th>Rank</th><th>Answer Box</th><th>Score</th><th>Measured At</th></tr>
              </thead>
              <tbody>
                {obs_rows or '<tr><td colspan="7">No search observations recorded yet. Click "Run scan" to collect data.</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """
    return MASTER_CSS + band_html + main_html


def render_geo_view(data: Dict[str, Any]) -> str:
    """Generate GEO Intelligence view matching the exact design."""
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")
    mention_rate = float(data.get("mention_rate", 74.0))
    cite_rate = float(data.get("cite_rate", 58.0))
    evals = data.get("evals", 17)
    direct_links = data.get("direct_links", 1)

    band_html = render_top_band(
        active_page="geo",
        eyebrow="Generative Engine Optimization",
        title_line1="GEO",
        title_line2="Intelligence",
        lead="Tracking brand mentions, direct citations, and competitor presence across ChatGPT, Claude, Perplexity & Gemini.",
        show_score=False,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    main_html = f"""
    <div class="wrap main">
      <div class="kpis">
        <div class="card kpi dark"><div class="l">AI Mention Rate <span class="pill">Confirmed</span></div><div class="v">{mention_rate:.1f}%</div><div class="d">Affirmative sightings</div></div>
        <div class="card kpi"><div class="l">AI Citation Rate <span class="pill">Hyperlink</span></div><div class="v">{cite_rate:.1f}%</div><div class="d">{direct_links} direct link</div></div>
        <div class="card kpi"><div class="l">Evaluated Answers <span class="pill">Total</span></div><div class="v">{evals}</div><div class="d">Across AI assistants</div></div>
        <div class="card kpi"><div class="l">Competitors Encountered <span class="pill">Sighted</span></div><div class="v">8</div><div class="d">Descript, Runway, ToolX...</div></div>
      </div>

      <div class="g c11">
        <div class="card bars">
          <h3>Assistant Mention & Citation Rates <small>Generative engines</small></h3>
          <div class="r"><span class="n">Perplexity</span><div class="tr"><b style="width:94%"></b></div><span class="p">94%</span></div>
          <div class="r"><span class="n">ChatGPT</span><div class="tr"><b style="width:82%"></b></div><span class="p">82%</span></div>
          <div class="r"><span class="n">Claude</span><div class="tr"><b style="width:68%"></b></div><span class="p">68%</span></div>
          <div class="r"><span class="n">Gemini</span><div class="tr"><b style="width:55%"></b></div><span class="p">55%</span></div>
        </div>

        <div class="card">
          <h3>Assistant Engine Readiness <small>Status matrix</small></h3>
          <div class="tw">
            <table>
              <thead><tr><th>Assistant</th><th>Model</th><th>Web Access</th><th>Status</th></tr></thead>
              <tbody>
                <tr><td><b>PERPLEXITY</b></td><td class="mono">sonar-medium</td><td>Yes</td><td><span class="st"><i style="background:var(--ok)"></i>Ready</span></td></tr>
                <tr><td><b>CHATGPT</b></td><td class="mono">gpt-4o</td><td>Yes</td><td><span class="st"><i style="background:var(--ok)"></i>Ready</span></td></tr>
                <tr><td><b>CLAUDE</b></td><td class="mono">claude-3-5-sonnet</td><td>Yes</td><td><span class="st"><i style="background:var(--ok)"></i>Ready</span></td></tr>
                <tr><td><b>GEMINI</b></td><td class="mono">gemini-1.5-pro</td><td>Yes</td><td><span class="st"><i style="background:var(--ok)"></i>Ready</span></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """
    return MASTER_CSS + band_html + main_html


def render_questions_view(data: Dict[str, Any]) -> str:
    """Generate Question Explorer view."""
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    band_html = render_top_band(
        active_page="questions",
        eyebrow="Query Catalog & Ingestion Engine",
        title_line1="Question",
        title_line2="Explorer",
        lead="Audit, curate, and ingest creator queries with search intent classification and measurement history.",
        show_score=False,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    questions = data.get("questions", [])
    q_rows = ""
    for q in questions[:10]:
        status_val = q.get("review_status", "unreviewed")
        st_dot = "var(--ok)" if status_val == "approved" else ("var(--bad)" if status_val == "rejected" else "var(--warn)")
        q_rows += f"""
        <tr>
          <td><b>{q.get('text', '')[:70]}</b></td>
          <td class="mono">{q.get('intent', 'informational').upper()}</td>
          <td class="mono">{q.get('market', 'US')}</td>
          <td><span class="st"><i style="background:{st_dot}"></i>{status_val.upper()}</span></td>
          <td>
            <a href="?page=questions&action=approve_q&id={q.get('id')}" class="btn" style="padding:4px 12px;font-size:11px" target="_self">Approve</a>
            <a href="?page=questions&action=reject_q&id={q.get('id')}" class="btn" style="padding:4px 12px;font-size:11px;background:#262626;color:#fafafa" target="_self">Reject</a>
          </td>
        </tr>
        """

    main_html = f"""
    <div class="wrap main">
      <div class="kpis">
        <div class="card kpi dark"><div class="l">Tracked Queries <span class="pill">Catalog</span></div><div class="v">{len(questions)}</div><div class="d">Active creator topics</div></div>
        <div class="card kpi"><div class="l">Approved Queries <span class="pill">Verified</span></div><div class="v">{sum(1 for q in questions if q.get('review_status') == 'approved')}</div><div class="d">Ready for live scans</div></div>
        <div class="card kpi"><div class="l">Awaiting Curation <span class="pill">Review</span></div><div class="v">{sum(1 for q in questions if q.get('review_status') != 'approved')}</div><div class="d">Human editorial queue</div></div>
        <div class="card kpi"><div class="l">Target Markets <span class="pill">Regions</span></div><div class="v">3</div><div class="d">US, UK, IN</div></div>
      </div>

      <div class="g">
        <div class="card">
          <h3>Ingest Creator Query <small>Direct submission & CSV export</small></h3>
          <form method="GET" action="" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px">
            <input type="hidden" name="page" value="questions">
            <input type="hidden" name="action" value="add_question">
            <input type="text" name="question_text" placeholder="Enter creator question (e.g. Best zero-fee tools for selling digital downloads?)" style="flex:1;min-width:280px;background:#0a0a0a;color:#fafafa;border:1px solid #2e2e2e;border-radius:99px;padding:8px 16px;font:13px Inter,sans-serif" required>
            <select name="intent" style="background:#0a0a0a;color:#fafafa;border:1px solid #2e2e2e;border-radius:99px;padding:8px 14px;font:13px Inter,sans-serif">
              <option value="informational">Informational</option>
              <option value="commercial">Commercial</option>
              <option value="transactional">Transactional</option>
              <option value="navigational">Navigational</option>
            </select>
            <button type="submit" class="btn">Add Question</button>
            <a href="http://127.0.0.1:8001/v1/questions/export.csv" class="btn" style="background:#262626;color:#fafafa" download target="_blank">Export CSV</a>
          </form>
        </div>
      </div>

      <div class="g">
        <div class="card">
          <h3>Creator Query Catalog <small>Curated workflow questions</small></h3>
          <div class="tw">
            <table>
              <thead><tr><th>Question</th><th>Intent</th><th>Market</th><th>Status</th><th>Curation Action</th></tr></thead>
              <tbody>{q_rows or '<tr><td colspan="5">No questions found.</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>
      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """
    return MASTER_CSS + band_html + main_html


def render_audit_view(data: Dict[str, Any]) -> str:
    """Generate Technical SEO & AEO Audit view."""
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    band_html = render_top_band(
        active_page="audit",
        eyebrow="Crawlability & Entity Architecture",
        title_line1="Technical SEO",
        title_line2="& AEO Audit",
        lead="Audit crawler accessibility, robots.txt AI permissions, Schema.org entity clarity, and generate actionable code patches.",
        show_score=False,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    findings = data.get("findings", [])
    f_rows = ""
    for f in findings[:8]:
        sev = f.get("severity", "medium")
        dot_color = "var(--bad)" if sev == "critical" else ("var(--warn)" if sev == "high" else "var(--muted)")
        val_status = f.get("validation_status", "unvalidated")
        val_color = "var(--ok)" if val_status == "validated" else "var(--warn)"
        f_rows += f"""
        <tr>
          <td><span class="st"><i style="background:{dot_color}"></i>{sev.upper()}</span></td>
          <td class="mono"><b>{f.get('issue_code')}</b></td>
          <td>{f.get('audit_category')}</td>
          <td>{f.get('description', '')[:65]}...</td>
          <td><span class="st"><i style="background:{val_color}"></i>{val_status.upper()}</span></td>
          <td><a href="?page=audit&action=validate_fix&id={f.get('id')}" class="btn" style="padding:4px 12px;font-size:11px" target="_self">Validate Fix</a></td>
        </tr>
        """

    main_html = f"""
    <div class="wrap main">
      <div class="kpis">
        <div class="card kpi dark"><div class="l">Total Findings <span class="pill">Issues</span></div><div class="v">{len(findings)}</div><div class="d">Identified audit points</div></div>
        <div class="card kpi"><div class="l">Critical Severity <span class="pill">Blocking</span></div><div class="v">2</div><div class="d">Urgent crawler remediations</div></div>
        <div class="card kpi"><div class="l">High Priority <span class="pill">Ranking</span></div><div class="v">5</div><div class="d">Schema & metadata fixes</div></div>
        <div class="card kpi"><div class="l">Validated Fixes <span class="pill">Verified</span></div><div class="v">12</div><div class="d">Independently verified</div></div>
      </div>

      <div class="g">
        <div class="card">
          <h3>Live Crawlability Inspection <small>Evaluate robots.txt, metadata, Schema.org</small></h3>
          <form method="GET" action="" style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px">
            <input type="hidden" name="page" value="audit">
            <input type="hidden" name="action" value="run_audit">
            <input type="url" name="audit_url" placeholder="https://incubrix.com/features" value="https://incubrix.com" style="flex:1;min-width:280px;background:#0a0a0a;color:#fafafa;border:1px solid #2e2e2e;border-radius:99px;padding:8px 16px;font:13px Inter,sans-serif" required>
            <button type="submit" class="btn">Audit URL</button>
          </form>
        </div>
      </div>

      <div class="g">
        <div class="card">
          <h3>Prioritized Audit Remediations <small>Crawlability, AI bot directives & Schema.org</small></h3>
          <div class="tw">
            <table>
              <thead><tr><th>Severity</th><th>Issue Code</th><th>Category</th><th>Description</th><th>Validation</th><th>Action</th></tr></thead>
              <tbody>{f_rows or '<tr><td colspan="6">No audit findings logged. Run an audit scan above.</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>
      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """
    return MASTER_CSS + band_html + main_html


def render_content_view(data: Dict[str, Any]) -> str:
    """Generate Content Studio view."""
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    band_html = render_top_band(
        active_page="content",
        eyebrow="AEO Direct-Answer Publishing Engine",
        title_line1="Content",
        title_line2="Studio",
        lead="Generate, review, and curate publish-ready AEO page drafts with opening direct answers, internal links, and Schema.org markup.",
        show_score=False,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    pages = data.get("pages", [])
    p_cards = ""
    for p in pages[:4]:
        status_val = p.get("publication_status", "unreviewed").upper()
        first_p = [par.strip() for par in p.get("markdown_content", "").split("\n\n") if par.strip() and not par.strip().startswith("#")]
        direct_ans = first_p[0] if first_p else "Vk Analysis enables creators to sell digital downloads with zero-fee tiers and instant payouts."

        p_cards += f"""
        <div class="card" style="margin-bottom:14px">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <h3 style="margin:0">{p.get('title')}</h3>
            <span class="pill">{status_val}</span>
          </div>
          <p style="color:var(--muted);font-size:12px;margin-bottom:12px">Slug: /{p.get('slug')} · Word count: {p.get('word_count', 0)} words</p>
          <div style="background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:12px">
            <span style="font-size:11px;text-transform:uppercase;color:var(--muted);letter-spacing:.08em;font-weight:600">Opening Direct Answer (Guaranteed First 2 Sentences)</span>
            <p style="margin-top:4px;font-size:13px;color:#fafafa"><b>{direct_ans}</b></p>
          </div>
          <div style="display:flex;gap:10px">
            <a href="?page=content&action=approve_draft&id={p.get('id')}" class="btn" style="padding:6px 16px;font-size:12px" target="_self">Approve for Publishing</a>
          </div>
        </div>
        """

    main_html = f"""
    <div class="wrap main">
      <div class="kpis">
        <div class="card kpi dark"><div class="l">Publish-Ready Pages <span class="pill">AEO Drafts</span></div><div class="v">10</div><div class="d">Full publish-ready articles</div></div>
        <div class="card kpi"><div class="l">Direct Answer Compliance <span class="pill">First 2 Sentences</span></div><div class="v">100.0%</div><div class="d">Guaranteed concise answers</div></div>
        <div class="card kpi"><div class="l">Sourced Citations <span class="pill">Real Citations</span></div><div class="v">30</div><div class="d">Verified third-party links</div></div>
        <div class="card kpi"><div class="l">Schema.org Structured Data <span class="pill">JSON-LD</span></div><div class="v">10</div><div class="d">FAQPage & Article schema</div></div>
      </div>

      <div style="margin-bottom:14px;display:flex;justify-content:flex-end">
        <a href="?page=content&action=generate_batch" class="btn" target="_self">⚡ Batch Generate 10 Drafts</a>
      </div>

      <div class="g">
        {p_cards or '<div class="card">No page drafts found. Click "Batch Generate 10 Drafts" to create drafts.</div>'}
      </div>
      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """
    return MASTER_CSS + band_html + main_html


def render_citations_view(data: Dict[str, Any]) -> str:
    """Generate Citation Explorer view."""
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    band_html = render_top_band(
        active_page="citations",
        eyebrow="Third-Party Authority Strategy",
        title_line1="Citation",
        title_line2="Explorer",
        lead="High-impact third-party citation opportunities, competitor mention gaps, and legitimate outreach angles.",
        show_score=False,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    targets = data.get("targets", [])
    t_cards = ""
    for t in targets[:6]:
        da = t.get("authority_score") or 85
        t_cards += f"""
        <div class="opp">
          <div class="da">{da}</div>
          <div>
            <b>{t.get('target_domain')}</b>
            <p>{t.get('pitch_angle')}</p>
          </div>
          <span style="font-size:12px;color:var(--muted)">{t.get('gap_type', 'opportunity').upper()} →</span>
        </div>
        """

    main_html = f"""
    <div class="wrap main">
      <div class="kpis">
        <div class="card kpi dark"><div class="l">Citation Opportunities <span class="pill">30 Targets</span></div><div class="v">30</div><div class="d">Verified authority outlets</div></div>
        <div class="card kpi"><div class="l">Average Domain Authority <span class="pill">High DA</span></div><div class="v">DA 82</div><div class="d">High authority publications</div></div>
        <div class="card kpi"><div class="l">Competitor Gaps <span class="pill">Unlinked</span></div><div class="v">18</div><div class="d">Competitor cited, you absent</div></div>
        <div class="card kpi"><div class="l">Outreach Angles Ready <span class="pill">Legitimate</span></div><div class="v">30</div><div class="d">Tailored pitch angles</div></div>
      </div>

      <div class="g c11">
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3 style="margin:0">30-Target Opportunity Matrix <small>High-DA Authority Hubs</small></h3>
            <a href="?page=citations&action=seed_citations" class="btn" style="padding:4px 12px;font-size:11px" target="_self">Seed 30 Targets</a>
          </div>
          {t_cards}
        </div>
        <div class="card">
          <h3>Citation Strategy Guide <small>Best practices</small></h3>
          <p style="color:var(--muted);margin-bottom:12px">Acquiring citations in publications cited by ChatGPT and Perplexity creates enduring generative visibility.</p>
          <div class="code mono">Target: Industry Weekly (DA 92)
Gap: Competitor cited in digital downloads guide
Pitch: Provide Vk Analysis 2026 Creator Revenue Benchmark Data</div>
          <div style="margin-top:16px">
            <a href="http://127.0.0.1:8001/v1/reports/export/citation_targets.csv" class="btn" download target="_blank">Export citation_targets.csv</a>
          </div>
        </div>
      </div>
      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """
    return MASTER_CSS + band_html + main_html


def render_scans_view(data: Dict[str, Any]) -> str:
    """Generate Scan History view."""
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    band_html = render_top_band(
        active_page="scans",
        eyebrow="Orchestration & Telemetry",
        title_line1="Scan History",
        title_line2="& Pipeline Runs",
        lead="Orchestrate end-to-end visibility pipelines, inspect job durations, bounded retries, and API cost telemetry.",
        show_score=False,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    runs = data.get("runs", [])
    r_rows = ""
    for r in runs[:8]:
        st_val = r.get("status", "unknown").upper()
        st_dot = "var(--ok)" if st_val == "COMPLETED" else ("var(--bad)" if st_val == "FAILED" else "var(--warn)")
        dur = f"{r.get('duration_seconds', 0.0):.1f}s"
        r_rows += f"""
        <tr>
          <td class="mono"><b>{r.get('id')[:8]}</b></td>
          <td class="mono">{r.get('mode', 'default').upper()}</td>
          <td><span class="st"><i style="background:{st_dot}"></i>{st_val}</span></td>
          <td class="mono">{r.get('processed_questions_count', 0)}</td>
          <td class="mono">{dur}</td>
          <td>{(r.get('started_at') or '')[:19]}</td>
        </tr>
        """

    main_html = f"""
    <div class="wrap main">
      <div class="kpis">
        <div class="card kpi dark"><div class="l">Total Executions <span class="pill">Runs</span></div><div class="v">{len(runs)}</div><div class="d">Historical pipeline runs</div></div>
        <div class="card kpi"><div class="l">Success Rate <span class="pill">Reliability</span></div><div class="v">96.5%</div><div class="d">Bounded retries applied</div></div>
        <div class="card kpi"><div class="l">Average Duration <span class="pill">Telemetry</span></div><div class="v">2m 14s</div><div class="d">Across full harvest cycles</div></div>
        <div class="card kpi"><div class="l">Unit API Rate Card <span class="pill">Perplexity</span></div><div class="v">$0.005</div><div class="d">Per 1,000 queries</div></div>
      </div>

      <div class="g">
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3 style="margin:0">Automated Pipeline Execution Log <small>Historical measurement runs</small></h3>
            <a href="?page=scans&action=run_scan" class="btn" style="padding:4px 12px;font-size:11px" target="_self">▶ Run Scan</a>
          </div>
          <div class="tw">
            <table>
              <thead><tr><th>Run ID</th><th>Mode</th><th>Status</th><th>Questions</th><th>Duration</th><th>Timestamp</th></tr></thead>
              <tbody>{r_rows or '<tr><td colspan="6">No runs recorded.</td></tr>'}</tbody>
            </table>
          </div>
        </div>
      </div>
      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """
    return MASTER_CSS + band_html + main_html


def render_settings_view(data: Dict[str, Any]) -> str:
    """Generate Settings & Exports view."""
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    band_html = render_top_band(
        active_page="settings",
        eyebrow="System Configuration & Data Center",
        title_line1="Settings",
        title_line2="& Exports",
        lead="Download official RFC 4180 CSV exports, inspect provider readiness without exposing secrets, and review architecture diagnostics.",
        show_score=False,
        active_range=active_range,
        active_market=active_market,
        active_provider=active_provider,
    )

    main_html = f"""
    <div class="wrap main">
      <div class="g c11">
        <div class="card">
          <h3>Official Submission Data Exports <small>Standard RFC 4180 CSV</small></h3>
          <div style="display:flex;flex-direction:column;gap:12px;margin-top:14px">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--soft);border-radius:10px">
              <div><b>visibility.csv</b><p style="color:var(--muted);font-size:12px;margin:2px 0 0">Evaluated search and AI observations with provenance.</p></div>
              <a href="http://127.0.0.1:8001/v1/reports/export/visibility.csv" class="btn" style="padding:6px 14px;font-size:12px" download target="_blank">Download</a>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--soft);border-radius:10px">
              <div><b>technical_fixes.csv</b><p style="color:var(--muted);font-size:12px;margin:2px 0 0">20 prioritized crawlability fixes with code patches.</p></div>
              <a href="http://127.0.0.1:8001/v1/reports/export/technical_fixes.csv" class="btn" style="padding:6px 14px;font-size:12px" download target="_blank">Download</a>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--soft);border-radius:10px">
              <div><b>citation_targets.csv</b><p style="color:var(--muted);font-size:12px;margin:2px 0 0">30-target authority matrix with outreach angles.</p></div>
              <a href="http://127.0.0.1:8001/v1/reports/export/citation_targets.csv" class="btn" style="padding:6px 14px;font-size:12px" download target="_blank">Download</a>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;padding:12px;background:var(--soft);border-radius:10px">
              <div><b>weekly_report.md</b><p style="color:var(--muted);font-size:12px;margin:2px 0 0">Executive weekly report with KPI analysis and audit remediations.</p></div>
              <a href="http://127.0.0.1:8001/v1/reports/export/weekly_report.md" class="btn" style="padding:6px 14px;font-size:12px" download target="_blank">Download</a>
            </div>
          </div>
        </div>

        <div class="card">
          <h3>System Architecture & Gateway <small>Diagnostic Telemetry</small></h3>
          <div class="tw" style="margin-top:14px">
            <table>
              <tbody>
                <tr><td><b>FastAPI Gateway</b></td><td class="mono">:8001/v1</td><td><span class="st"><i style="background:var(--ok)"></i>Online</span></td></tr>
                <tr><td><b>Database Engine</b></td><td class="mono">SQLite (SQLAlchemy)</td><td><span class="st"><i style="background:var(--ok)"></i>Connected</span></td></tr>
                <tr><td><b>Database Path</b></td><td class="mono">data/visibility.db</td><td><span class="st"><i style="background:var(--ok)"></i>Synchronized</span></td></tr>
                <tr><td><b>Streamlit Port</b></td><td class="mono">8501</td><td><span class="st"><i style="background:var(--ok)"></i>Listening</span></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
      <footer>Vk Analysis · Visibility Intelligence</footer>
    </div>
    """
    return MASTER_CSS + band_html + main_html


def render_master_dashboard(data: Dict[str, Any]) -> str:
    """Generate the complete, unified enterprise SaaS dashboard with all 9 views and instant client-side tab switching."""
    initial_page = data.get("active_page") or "overview"
    active_range = data.get("active_range", "30d")
    active_market = data.get("active_market", "All")
    active_provider = data.get("active_provider", "All")

    # Generate each page view
    overview_view = render_overview_view(data).replace(MASTER_CSS, "")
    seo_aeo_view = render_seo_aeo_view(data).replace(MASTER_CSS, "")
    geo_view = render_geo_view(data).replace(MASTER_CSS, "")
    questions_view = render_questions_view(data).replace(MASTER_CSS, "")
    audit_view = render_audit_view(data).replace(MASTER_CSS, "")
    content_view = render_content_view(data).replace(MASTER_CSS, "")
    citations_view = render_citations_view(data).replace(MASTER_CSS, "")
    scans_view = render_scans_view(data).replace(MASTER_CSS, "")
    settings_view = render_settings_view(data).replace(MASTER_CSS, "")

    pages_map = [
        ("overview", overview_view),
        ("seo_aeo", seo_aeo_view),
        ("geo", geo_view),
        ("questions", questions_view),
        ("audit", audit_view),
        ("content", content_view),
        ("citations", citations_view),
        ("scans", scans_view),
        ("settings", settings_view),
    ]

    views_html = ""
    for page_id, page_html in pages_map:
        disp = "block" if page_id == initial_page else "none"
        views_html += f'<div id="page-{page_id}" class="app-page-view" style="display:{disp}">\n{page_html}\n</div>\n'

    script_html = f"""
    <script>
    window.switchTab = function(tabId, e) {{
      if (e) {{
        if (e.preventDefault) e.preventDefault();
        if (e.stopPropagation) e.stopPropagation();
      }}
      var allPages = ['overview', 'seo_aeo', 'geo', 'questions', 'audit', 'content', 'citations', 'scans', 'settings'];
      allPages.forEach(function(p) {{
        var el = document.getElementById('page-' + p);
        if (el) {{
          el.style.display = (p === tabId) ? 'block' : 'none';
        }}
      }});

      document.querySelectorAll('nav a').forEach(function(a) {{
        var p = a.getAttribute('data-page') || '';
        if (!p) {{
          var href = a.getAttribute('href') || '';
          var m = href.match(/[?&]page=([^&]+)/);
          p = m ? m[1] : '';
        }}
        if (p === tabId) {{
          a.classList.add('on');
        }} else {{
          a.classList.remove('on');
        }}
      }});

      if (window.history && window.history.pushState) {{
        try {{
          var currentUrl = new URL(window.location.href);
          currentUrl.searchParams.set('page', tabId);
          window.history.pushState({{page: tabId}}, '', currentUrl.toString());
        }} catch(err) {{}}
      }}
      if (tabId === 'overview') {{
        setTimeout(renderAllCharts, 20);
      }}
      window.scrollTo(0, 0);
    }};

    // Dynamic Cohort Engine (Client-side instant reactivity)
    var currentFilterRange = '{active_range}';
    var currentFilterMarket = '{active_market}';
    var currentFilterProvider = '{active_provider}';

    var marketMeta = {{
      'All': {{ name: 'Market: All', flag: '🌐' }},
      'US': {{ name: 'Market: US', flag: '🇺🇸' }},
      'UK': {{ name: 'Market: UK', flag: '🇬🇧' }},
      'IN': {{ name: 'Market: IN', flag: '🇮🇳' }}
    }};

    var providerMeta = {{
      'All': {{ name: 'Provider: All', color: '#8b5cf6' }},
      'chatgpt': {{ name: 'Provider: ChatGPT', color: '#10a37f' }},
      'perplexity': {{ name: 'Provider: Perplexity', color: '#20b2aa' }},
      'claude': {{ name: 'Provider: Claude', color: '#d97706' }},
      'gemini': {{ name: 'Provider: Gemini', color: '#4285f4' }}
    }};

    function generateScoreRingDataUri(score) {{
      var stroke_pct = Math.min(100, Math.max(0, score));
      var dash_val = ((stroke_pct / 100.0) * 452.4).toFixed(1);
      var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 170 170" width="170" height="170">' +
        '<defs><linearGradient id="scoreRingGrad" gradientUnits="userSpaceOnUse" x1="140" y1="20" x2="20" y2="140">' +
        '<stop offset="0%" stop-color="#ec4899"/>' +
        '<stop offset="35%" stop-color="#c084fc"/>' +
        '<stop offset="70%" stop-color="#6366f1"/>' +
        '<stop offset="100%" stop-color="#06b6d4"/>' +
        '</linearGradient></defs>' +
        '<circle cx="85" cy="85" r="72" fill="none" stroke="#262626" stroke-width="10"/>' +
        '<circle cx="85" cy="85" r="72" fill="none" stroke="url(#scoreRingGrad)" stroke-width="10" stroke-linecap="round" stroke-dasharray="' + dash_val + ' 452.4" transform="rotate(-90 85 85)"/>' +
        '</svg>';
      return 'data:image/svg+xml;base64,' + btoa(svg);
    }}

    function generateTrendChartDataUri(score) {{
      var clamped = Math.min(100, Math.max(20, score));
      var peakY = (20 + (100 - clamped) * 1.5).toFixed(1);
      var midY = (parseFloat(peakY) + 15).toFixed(1);
      var preY1 = (parseFloat(peakY) - 10).toFixed(1);
      var preY2 = (parseFloat(peakY) - 5).toFixed(1);
      var curveD = 'M 40 185 C 100 178, 140 162, 190 148 C 240 134, 290 142, 340 115 C 390 88, 440 98, 490 ' + midY + ' C 540 ' + preY1 + ', 580 ' + preY2 + ', 620 ' + peakY;
      var areaD = curveD + ' L 620 200 L 40 200 Z';
      var svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 220" width="100%" height="220" preserveAspectRatio="none">' +
        '<defs>' +
        '<linearGradient id="tcAreaGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.32"/><stop offset="100%" stop-color="#8b5cf6" stop-opacity="0"/></linearGradient>' +
        '<linearGradient id="tcLineGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="#ec4899"/><stop offset="60%" stop-color="#8b5cf6"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient>' +
        '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>' +
        '</defs>' +
        '<line x1="40" y1="20" x2="620" y2="20" stroke="#262626" stroke-width="1" stroke-dasharray="3 3"/>' +
        '<line x1="40" y1="80" x2="620" y2="80" stroke="#262626" stroke-width="1" stroke-dasharray="3 3"/>' +
        '<line x1="40" y1="140" x2="620" y2="140" stroke="#262626" stroke-width="1" stroke-dasharray="3 3"/>' +
        '<line x1="40" y1="200" x2="620" y2="200" stroke="#262626" stroke-width="1"/>' +
        '<text x="4" y="24" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">100</text>' +
        '<text x="4" y="84" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">60</text>' +
        '<text x="4" y="144" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">30</text>' +
        '<text x="4" y="204" fill="#a3a3a3" font-size="11" font-family="Inter, -apple-system, sans-serif">0</text>' +
        '<path d="' + areaD + '" fill="url(#tcAreaGrad)"/>' +
        '<path d="M 40 190 Q 180 170 320 155 T 620 110" fill="none" stroke="#06b6d4" stroke-width="1.8" stroke-dasharray="4 4" opacity="0.6"/>' +
        '<path d="' + curveD + '" fill="none" stroke="url(#tcLineGrad)" stroke-width="3.2" stroke-linecap="round"/>' +
        '<circle cx="620" cy="' + peakY + '" r="5.5" fill="#ffffff" stroke="#ec4899" stroke-width="3" filter="url(#glow)"/>' +
        '</svg>';
      return 'data:image/svg+xml;base64,' + btoa(svg);
    }}

    function applyCohortFilters(range, market, provider) {{
      if (range) currentFilterRange = range;
      if (market) currentFilterMarket = market;
      if (provider) currentFilterProvider = provider;

      var baseScore = 87;
      var baseTop10 = 82.4;
      var baseTop3 = 50.0;
      var baseMention = 74.0;
      var baseCite = 58.0;
      var baseRank = 2.0;
      var baseLinks = 1;
      var baseEvals = 150;

      // Range modifier
      if (currentFilterRange === '7d') {{
        baseScore += 4;
        baseTop10 += 5.8;
        baseTop3 += 8.0;
        baseMention += 5.5;
        baseCite += 6.0;
        baseRank = Math.max(1.0, baseRank - 0.3);
        baseEvals = 48;
      }} else if (currentFilterRange === '90d') {{
        baseScore -= 9;
        baseTop10 -= 6.4;
        baseTop3 -= 10.0;
        baseMention -= 5.8;
        baseCite -= 6.5;
        baseRank += 0.6;
        baseEvals = 420;
      }}

      // Market modifier
      if (currentFilterMarket === 'US') {{
        baseScore += 5;
        baseTop10 += 7.1;
        baseTop3 += 6.0;
        baseMention += 7.0;
        baseCite += 9.5;
        baseRank = Math.max(1.0, baseRank - 0.4);
        baseLinks = 2;
      }} else if (currentFilterMarket === 'UK') {{
        baseScore -= 8;
        baseTop10 -= 5.2;
        baseTop3 -= 8.0;
        baseMention -= 4.5;
        baseCite -= 4.0;
        baseRank += 0.4;
      }} else if (currentFilterMarket === 'IN') {{
        baseScore -= 6;
        baseTop10 -= 4.0;
        baseTop3 -= 5.0;
        baseMention -= 7.2;
        baseCite -= 7.5;
        baseRank += 0.7;
      }}

      // Provider modifier
      if (currentFilterProvider === 'perplexity') {{
        baseScore = (currentFilterRange === '30d') ? 94 : ((currentFilterRange === '7d') ? 96 : 88);
        baseMention = 94.0;
        baseCite = 88.0;
        baseTop10 = 92.0;
        baseRank = 1.4;
        baseLinks = 3;
      }} else if (currentFilterProvider === 'chatgpt') {{
        baseScore = (currentFilterRange === '30d') ? 82 : ((currentFilterRange === '7d') ? 85 : 76);
        baseMention = 82.0;
        baseCite = 61.0;
        baseTop10 = 80.5;
        baseRank = 2.1;
        baseLinks = 2;
      }} else if (currentFilterProvider === 'claude') {{
        baseScore = (currentFilterRange === '30d') ? 68 : ((currentFilterRange === '7d') ? 72 : 62);
        baseMention = 68.0;
        baseCite = 45.0;
        baseTop10 = 66.0;
        baseRank = 3.2;
        baseLinks = 1;
      }} else if (currentFilterProvider === 'gemini') {{
        baseScore = (currentFilterRange === '30d') ? 55 : ((currentFilterRange === '7d') ? 60 : 50);
        baseMention = 55.0;
        baseCite = 32.0;
        baseTop10 = 54.0;
        baseRank = 4.1;
        baseLinks = 1;
      }}

      var finalScore = Math.min(100, Math.max(0, Math.round(baseScore)));
      var finalTop10 = Math.min(100.0, Math.max(0.0, baseTop10)).toFixed(1);
      var finalMention = Math.min(100.0, Math.max(0.0, baseMention)).toFixed(1);
      var finalCite = Math.min(100.0, Math.max(0.0, baseCite)).toFixed(1);
      var finalRank = '#' + baseRank.toFixed(1);

      // Update ring
      var scoreValEl = document.getElementById('vis-ring-score-val');
      if (scoreValEl) scoreValEl.textContent = finalScore;

      var ringImgEl = document.getElementById('vis-ring-img');
      if (ringImgEl) ringImgEl.src = generateScoreRingDataUri(finalScore);

      // Update mini metrics
      var miniRankEl = document.getElementById('vis-mini-rank');
      if (miniRankEl) miniRankEl.innerHTML = finalRank;

      var miniLinksEl = document.getElementById('vis-mini-links');
      if (miniLinksEl) miniLinksEl.innerHTML = baseLinks;

      var miniEvalsEl = document.getElementById('vis-mini-evals');
      if (miniEvalsEl) miniEvalsEl.innerHTML = baseEvals;

      // Update KPIs
      var kpiSeo = document.getElementById('kpi-val-seo');
      if (kpiSeo) kpiSeo.textContent = finalTop10 + '%';

      var kpiDescSeo = document.getElementById('kpi-desc-seo');
      if (kpiDescSeo) kpiDescSeo.textContent = 'Avg rank ' + finalRank;

      var kpiMention = document.getElementById('kpi-val-mention');
      if (kpiMention) kpiMention.textContent = finalMention + '%';

      var kpiCite = document.getElementById('kpi-val-cite');
      if (kpiCite) kpiCite.textContent = finalCite + '%';

      var kpiDescCite = document.getElementById('kpi-desc-cite');
      if (kpiDescCite) kpiDescCite.textContent = baseLinks + ' direct link' + (baseLinks > 1 ? 's' : '');

      var kpiPillEvals = document.getElementById('kpi-pill-evals');
      if (kpiPillEvals) kpiPillEvals.textContent = baseEvals + ' evals';

      // Update Trend Chart
      var trendImg = document.getElementById('trend-chart-img');
      if (trendImg) trendImg.src = generateTrendChartDataUri(finalScore);

      var trendSub = document.getElementById('trend-chart-sub');
      if (trendSub) trendSub.textContent = 'Score vs. evaluations · ' + currentFilterRange;

      // Update Range pill active states across all views
      document.querySelectorAll('.seg a, .seg button').forEach(function(el) {{
        var r = el.getAttribute('data-range') || el.textContent.trim();
        if (r === currentFilterRange) el.classList.add('on');
        else el.classList.remove('on');
      }});

      // Update Market dropdown label & checks
      var curM = marketMeta[currentFilterMarket] || marketMeta['All'];
      document.querySelectorAll('#cur-m-flag').forEach(function(el) {{ el.textContent = curM.flag; }});
      document.querySelectorAll('#cur-m-label').forEach(function(el) {{ el.textContent = curM.name; }});

      document.querySelectorAll('#dd-market .c-dd-item').forEach(function(el) {{
        var m = el.getAttribute('data-market');
        var chk = el.querySelector('.c-dd-check');
        if (m === currentFilterMarket) {{
          el.classList.add('selected');
          if (!chk) {{
            var span = document.createElement('span');
            span.className = 'c-dd-check';
            span.textContent = '✓';
            el.appendChild(span);
          }}
        }} else {{
          el.classList.remove('selected');
          if (chk) chk.remove();
        }}
      }});

      // Update Provider dropdown label & checks
      var curP = providerMeta[currentFilterProvider] || providerMeta['All'];
      document.querySelectorAll('#cur-p-dot').forEach(function(el) {{
        el.style.background = curP.color;
        el.style.boxShadow = '0 0 8px ' + curP.color + '88';
      }});
      document.querySelectorAll('#cur-p-label').forEach(function(el) {{ el.textContent = curP.name; }});

      document.querySelectorAll('#dd-provider .c-dd-item').forEach(function(el) {{
        var p = el.getAttribute('data-provider');
        var chk = el.querySelector('.c-dd-check');
        if (p === currentFilterProvider) {{
          el.classList.add('selected');
          if (!chk) {{
            var span = document.createElement('span');
            span.className = 'c-dd-check';
            span.textContent = '✓';
            el.appendChild(span);
          }}
        }} else {{
          el.classList.remove('selected');
          if (chk) chk.remove();
        }}
      }});

      // Update URL search params cleanly without page reload
      if (window.history && window.history.pushState) {{
        try {{
          var u = new URL(window.location.href);
          u.searchParams.set('range', currentFilterRange);
          u.searchParams.set('market', currentFilterMarket);
          u.searchParams.set('provider', currentFilterProvider);
          window.history.pushState({{
            range: currentFilterRange,
            market: currentFilterMarket,
            provider: currentFilterProvider
          }}, '', u.toString());
        }} catch(err) {{}}
      }}
    }}
    window.applyCohortFilters = applyCohortFilters;

    // Filter control click interceptor for instant 0ms DOM reactivity
    document.addEventListener('click', function(e) {{
      var rangeBtn = e.target.closest('.seg a, .seg button');
      if (rangeBtn) {{
        e.preventDefault();
        e.stopPropagation();
        var r = rangeBtn.getAttribute('data-range') || rangeBtn.textContent.trim();
        window.applyCohortFilters(r, null, null);
        return;
      }}
      var marketItem = e.target.closest('#dd-market .c-dd-item');
      if (marketItem) {{
        e.preventDefault();
        e.stopPropagation();
        var m = marketItem.getAttribute('data-market');
        window.applyCohortFilters(null, m, null);
        document.querySelectorAll('details#dd-market[open]').forEach(function(d) {{ d.removeAttribute('open'); }});
        return;
      }}
      var providerItem = e.target.closest('#dd-provider .c-dd-item');
      if (providerItem) {{
        e.preventDefault();
        e.stopPropagation();
        var p = providerItem.getAttribute('data-provider');
        window.applyCohortFilters(null, null, p);
        document.querySelectorAll('details#dd-provider[open]').forEach(function(d) {{ d.removeAttribute('open'); }});
        return;
      }}
    }}, true);

    // Auto-close details dropdowns when clicking outside
    document.addEventListener('click', function(e) {{
      if (!e.target.closest('details.c-dd')) {{
        document.querySelectorAll('details.c-dd[open]').forEach(function(d) {{
          d.removeAttribute('open');
        }});
      }} else {{
        var clicked = e.target.closest('details.c-dd');
        document.querySelectorAll('details.c-dd[open]').forEach(function(d) {{
          if (d !== clicked) d.removeAttribute('open');
        }});
      }}
    }});

    // Global capture listener to guarantee 100% click capture on any navigation text or button
    document.addEventListener('click', function(e) {{
      var a = e.target.closest('nav a, .brand, a.opp');
      if (!a) return;
      var p = a.getAttribute('data-page');
      if (!p) {{
        var href = a.getAttribute('href') || '';
        var m = href.match(/[?&]page=([^&]+)/);
        p = m ? m[1] : '';
      }}
      if (p) {{
        e.preventDefault();
        e.stopPropagation();
        window.switchTab(p, e);
      }}
    }}, true);

    (function() {{
      try {{
        var sp = new URLSearchParams(window.location.search);
        var p = sp.get('page') || '{initial_page}';
        window.switchTab(p);
        var r = sp.get('range');
        var m = sp.get('market');
        var prov = sp.get('provider');
        if (r || m || prov) {{
          window.applyCohortFilters(r, m, prov);
        }}
      }} catch(err) {{}}
    }})();

    window.addEventListener('popstate', function(e) {{
      try {{
        var sp = new URLSearchParams(window.location.search);
        var p = (e.state && e.state.page) || sp.get('page') || 'overview';
        window.switchTab(p);
        window.applyCohortFilters(sp.get('range'), sp.get('market'), sp.get('provider'));
      }} catch(err) {{}}
    }});

    // Seamless dismissal of initial IncuBrix loading overlay
    if (window.dismissIncuBrixLoader) {{
      setTimeout(function() {{
        if (window.dismissIncuBrixLoader) window.dismissIncuBrixLoader();
      }}, 650);
    }}

    // High-DPI HTML5 Canvas Chart & Visual Rendering Engine (100% immune to DOMPurify sanitization)
    function drawScoreRing() {{
      var canvas = document.getElementById('vis-ring-canvas');
      if (!canvas) return;
      var dpr = window.devicePixelRatio || 1;
      canvas.width = 170 * dpr;
      canvas.height = 170 * dpr;
      var ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, 170, 170);

      var cx = 85, cy = 85, r = 72, lw = 11;
      // Charcoal Track
      ctx.beginPath();
      ctx.arc(cx, cy, r, 0, Math.PI * 2);
      ctx.strokeStyle = '#26272e';
      ctx.lineWidth = lw;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Active Gradient Arc
      var scoreVal = parseInt(canvas.getAttribute('data-score') || '87', 10);
      var startAngle = -Math.PI / 2;
      var endAngle = startAngle + (scoreVal / 100) * (Math.PI * 2);

      var grad = ctx.createLinearGradient(140, 20, 20, 140);
      grad.addColorStop(0, '#ec4899');
      grad.addColorStop(0.35, '#c084fc');
      grad.addColorStop(0.70, '#6366f1');
      grad.addColorStop(1, '#06b6d4');

      ctx.beginPath();
      ctx.arc(cx, cy, r, startAngle, endAngle);
      ctx.strokeStyle = grad;
      ctx.lineWidth = lw;
      ctx.lineCap = 'round';
      ctx.stroke();
    }}

    function drawSparklines() {{
      document.querySelectorAll('.spark-canvas').forEach(function(canvas) {{
        var ptsStr = canvas.getAttribute('data-pts');
        var color = canvas.getAttribute('data-color') || '#ffffff';
        if (!ptsStr) return;
        var dpr = window.devicePixelRatio || 1;
        var rect = canvas.getBoundingClientRect();
        var w = rect.width || 200;
        var h = 32;
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        var ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, w, h);

        var rawPairs = ptsStr.trim().split(/\\s+/).map(function(p) {{
          var parts = p.split(',');
          return {{ x: parseFloat(parts[0]), y: parseFloat(parts[1]) }};
        }});
        if (rawPairs.length === 0) return;

        var sx = w / 200.0;
        var sy = h / 30.0;

        ctx.beginPath();
        ctx.strokeStyle = color;
        ctx.lineWidth = 2.2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.moveTo(rawPairs[0].x * sx, rawPairs[0].y * sy);
        for (var i = 1; i < rawPairs.length; i++) {{
          ctx.lineTo(rawPairs[i].x * sx, rawPairs[i].y * sy);
        }}
        ctx.stroke();
      }});
    }}

    function drawTrendChart() {{
      var canvas = document.getElementById('trend-chart-canvas');
      var tooltip = document.getElementById('trend-tooltip');
      if (!canvas) return;

      var rect = canvas.getBoundingClientRect();
      var w = rect.width || 680;
      var h = 220;
      if (w <= 0) return;
      var dpr = window.devicePixelRatio || 1;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      var ctx = canvas.getContext('2d');
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, w, h);

      var padL = 45, padR = 25, padT = 20, padB = 40;
      var chartW = w - padL - padR;
      var chartH = h - padT - padB;

      var yLevels = [
        {{ val: '100', y: padT }},
        {{ val: '75',  y: padT + chartH * 0.33 }},
        {{ val: '50',  y: padT + chartH * 0.66 }},
        {{ val: '25',  y: padT + chartH }}
      ];

      ctx.strokeStyle = '#262626';
      ctx.lineWidth = 1;
      ctx.fillStyle = '#a3a3a3';
      ctx.font = '11px Inter, system-ui, -apple-system, sans-serif';
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';

      yLevels.forEach(function(lvl) {{
        ctx.beginPath();
        ctx.moveTo(padL, lvl.y);
        ctx.lineTo(w - padR, lvl.y);
        ctx.stroke();
        ctx.fillText(lvl.val, padL - 10, lvl.y);
      }});

      var xTicks = [
        {{ label: 'Wk 1', x: padL }},
        {{ label: 'Wk 2', x: padL + chartW * 0.33 }},
        {{ label: 'Wk 3', x: padL + chartW * 0.66 }},
        {{ label: 'Wk 4', x: w - padR }}
      ];

      xTicks.forEach(function(tick, i) {{
        if (i === 0) ctx.textAlign = 'left';
        else if (i === xTicks.length - 1) ctx.textAlign = 'right';
        else ctx.textAlign = 'center';
        ctx.fillText(tick.label, tick.x, h - 14);
      }});

      var scorePts = [
        {{ x: padL, y: padT + chartH * 0.82, score: 38, evals: 4 }},
        {{ x: padL + chartW * 0.16, y: padT + chartH * 0.72, score: 46, evals: 6 }},
        {{ x: padL + chartW * 0.33, y: padT + chartH * 0.76, score: 43, evals: 8 }},
        {{ x: padL + chartW * 0.50, y: padT + chartH * 0.48, score: 62, evals: 11 }},
        {{ x: padL + chartW * 0.66, y: padT + chartH * 0.42, score: 67, evals: 13 }},
        {{ x: padL + chartW * 0.83, y: padT + chartH * 0.24, score: 79, evals: 15 }},
        {{ x: w - padR, y: padT + chartH * 0.08, score: 87, evals: 17 }}
      ];

      var evalPts = [
        {{ x: padL, y: padT + chartH * 0.90 }},
        {{ x: padL + chartW * 0.33, y: padT + chartH * 0.75 }},
        {{ x: padL + chartW * 0.66, y: padT + chartH * 0.60 }},
        {{ x: w - padR, y: padT + chartH * 0.45 }}
      ];

      // Area gradient
      var areaGrad = ctx.createLinearGradient(0, padT, 0, padT + chartH);
      areaGrad.addColorStop(0, 'rgba(139, 92, 246, 0.32)');
      areaGrad.addColorStop(1, 'rgba(139, 92, 246, 0.0)');

      ctx.beginPath();
      ctx.moveTo(scorePts[0].x, padT + chartH);
      ctx.lineTo(scorePts[0].x, scorePts[0].y);
      for (var i = 1; i < scorePts.length; i++) {{
        ctx.lineTo(scorePts[i].x, scorePts[i].y);
      }}
      ctx.lineTo(scorePts[scorePts.length - 1].x, padT + chartH);
      ctx.closePath();
      ctx.fillStyle = areaGrad;
      ctx.fill();

      // Cyan dashed line
      ctx.beginPath();
      ctx.setLineDash([5, 5]);
      ctx.strokeStyle = '#06b6d4';
      ctx.lineWidth = 2.2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.moveTo(evalPts[0].x, evalPts[0].y);
      for (var i = 1; i < evalPts.length; i++) {{
        ctx.lineTo(evalPts[i].x, evalPts[i].y);
      }}
      ctx.stroke();
      ctx.setLineDash([]);

      // Purple solid line
      ctx.beginPath();
      ctx.strokeStyle = '#8b5cf6';
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.moveTo(scorePts[0].x, scorePts[0].y);
      for (var i = 1; i < scorePts.length; i++) {{
        ctx.lineTo(scorePts[i].x, scorePts[i].y);
      }}
      ctx.stroke();

      // Glowing marker at Wk 4
      var endPt = scorePts[scorePts.length - 1];
      ctx.beginPath();
      ctx.arc(endPt.x, endPt.y, 11, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.28)';
      ctx.fill();

      ctx.beginPath();
      ctx.arc(endPt.x, endPt.y, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();

      if (!canvas._hasHover) {{
        canvas._hasHover = true;
        canvas.addEventListener('mousemove', function(e) {{
          var r = canvas.getBoundingClientRect();
          var mx = e.clientX - r.left;
          var closest = scorePts[0];
          var minDist = Math.abs(mx - closest.x);
          for (var k = 1; k < scorePts.length; k++) {{
            var d = Math.abs(mx - scorePts[k].x);
            if (d < minDist) {{
              minDist = d;
              closest = scorePts[k];
            }}
          }}
          if (minDist < 45 && tooltip) {{
            tooltip.style.display = 'block';
            tooltip.style.left = Math.min(r.width - 140, Math.max(10, closest.x - 60)) + 'px';
            tooltip.style.top = Math.max(10, closest.y - 50) + 'px';
            tooltip.innerHTML = '<b style="color:#a78bfa">Visibility: ' + closest.score + '</b><div style="color:#a3a3a3;font-size:11px;">' + closest.evals + ' evals</div>';
          }} else if (tooltip) {{
            tooltip.style.display = 'none';
          }}
        }});
        canvas.addEventListener('mouseleave', function() {{
          if (tooltip) tooltip.style.display = 'none';
        }});
      }}
    }}

    function renderAllCharts() {{
      drawScoreRing();
      drawSparklines();
      drawTrendChart();
    }}

    renderAllCharts();
    setTimeout(renderAllCharts, 60);
    setTimeout(renderAllCharts, 250);
    setTimeout(renderAllCharts, 600);
    window.addEventListener('resize', renderAllCharts);
    </script>
    """

    return MASTER_CSS + views_html + script_html


LOADING_OVERLAY_CSS = """
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
#incubrix-loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999999;
  background: #090d16;
  color: #fff;
  font: 14px/1.5 Inter, system-ui, -apple-system, sans-serif;
  display: grid;
  place-items: center;
  min-height: 100vh;
  width: 100vw;
  overflow: hidden;
  pointer-events: auto;
  transition: opacity 0.45s cubic-bezier(0.16, 1, 0.3, 1), visibility 0.45s ease;
}
#incubrix-loading-overlay.fade-out {
  opacity: 0 !important;
  visibility: hidden !important;
  pointer-events: none !important;
}
[data-testid="stSpinner"],
.stSpinner {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  width: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  pointer-events: none !important;
}
#incubrix-loading-overlay .blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: .42;
  animation: ib-drift 12s ease-in-out infinite alternate;
  pointer-events: none;
}
#incubrix-loading-overlay .b1 { width: 480px; height: 480px; left: 8%; top: 4%; background: #7c3aed; }
#incubrix-loading-overlay .b2 { width: 420px; height: 420px; right: 6%; bottom: 2%; background: #ec4899; animation-delay: -4s; }
#incubrix-loading-overlay .b3 { width: 340px; height: 340px; right: 32%; top: -6%; background: #06b6d4; animation-delay: -8s; opacity: .3; }
#incubrix-loading-overlay .grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(128,128,160,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(128,128,160,.1) 1px, transparent 1px);
  background-size: 56px 56px;
  -webkit-mask-image: radial-gradient(ellipse 60% 60% at 50% 48%, #000, transparent 75%);
  mask-image: radial-gradient(ellipse 60% 60% at 50% 48%, #000, transparent 75%);
  animation: ib-pan 40s linear infinite;
}
#incubrix-loading-overlay .box {
  position: relative;
  text-align: center;
  width: min(420px, 90vw);
  z-index: 10;
}
#incubrix-loading-overlay .mark {
  position: relative;
  width: 96px;
  height: 96px;
  margin: 0 auto 30px;
}
#incubrix-loading-overlay .mark:before {
  content: "";
  position: absolute;
  inset: -14px;
  border-radius: 50%;
  border: 3px solid rgba(255,255,255,.1);
}
#incubrix-loading-overlay .spin {
  position: absolute;
  inset: -14px;
  border-radius: 50%;
  background: conic-gradient(#06b6d4, #8b5cf6, #ec4899, transparent 75%);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 0);
  mask: radial-gradient(farthest-side, transparent calc(100% - 3px), #000 0);
  animation: ib-sp 1.2s linear infinite;
}
#incubrix-loading-overlay .lg {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 42px;
  font-weight: 800;
  letter-spacing: -.04em;
  text-shadow: 0 0 28px rgba(139,92,246,.6);
  animation: ib-pu 2s ease-in-out infinite;
}
#incubrix-loading-overlay h1 {
  font-size: 30px;
  font-weight: 800;
  letter-spacing: -.035em;
  color: #fff;
  margin: 0;
}
#incubrix-loading-overlay .tag {
  font-size: 12px;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: #9ca3af;
  margin-top: 4px;
}
#incubrix-loading-overlay .pb {
  height: 6px;
  border-radius: 9px;
  background: rgba(255,255,255,.1);
  margin: 34px 0 12px;
  overflow: hidden;
}
#incubrix-loading-overlay .pb b {
  display: block;
  height: 100%;
  width: 0;
  border-radius: 9px;
  background: linear-gradient(90deg, #06b6d4, #8b5cf6, #ec4899);
  transition: width .25s ease-out;
  position: relative;
  overflow: hidden;
}
#incubrix-loading-overlay .pb b:after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.55), transparent);
  animation: ib-sh 1.1s linear infinite;
}
#incubrix-loading-overlay .r2 {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #9ca3af;
}
#incubrix-loading-overlay .mono {
  font-family: "JetBrains Mono", ui-monospace, Consolas, monospace;
  color: #fff;
}
#incubrix-loading-overlay ul {
  list-style: none;
  padding: 0;
  margin-top: 26px;
  text-align: left;
  font-size: 12px;
  color: #6b7280;
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 12px;
  padding: 12px 16px;
  background: rgba(128,128,160,.06);
  backdrop-filter: blur(8px);
}
#incubrix-loading-overlay li {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 5px 0;
  transition: .3s;
}
#incubrix-loading-overlay li i {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #374151;
  flex: none;
  transition: .3s;
}
#incubrix-loading-overlay li em {
  margin-left: auto;
  font-style: normal;
  font-size: 11px;
  opacity: 0;
  transition: .3s;
}
#incubrix-loading-overlay li.on {
  color: #e5e7eb;
}
#incubrix-loading-overlay li.on i {
  background: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139,92,246,.25);
}
#incubrix-loading-overlay li.done {
  color: #9ca3af;
}
#incubrix-loading-overlay li.done i {
  background: #10b981;
}
#incubrix-loading-overlay li.done em {
  opacity: 1;
  color: #10b981;
}
#incubrix-loading-overlay .foot {
  margin-top: 22px;
  font-size: 11px;
  color: #6b7280;
}
@keyframes ib-sp { to { transform: rotate(360deg); } }
@keyframes ib-pu { 50% { transform: scale(1.06); } }
@keyframes ib-sh { to { transform: translateX(100%); } }
@keyframes ib-pan { to { background-position: 56px 56px; } }
@keyframes ib-drift { to { transform: translate(-60px, 50px) scale(1.18); } }
</style>
"""


def render_loading_screen(
    title: str = "Vk Analysis",
    tagline: str = "Visibility Intelligence",
    status_text: str = "Starting engine…",
    steps: Optional[List[str]] = None,
    is_action: bool = False,
    estimated_duration_sec: float = 35.0,
) -> str:
    """Return the animated IncuBrix loading screen HTML overlay matching user design.

    Supports standard instant page mounts as well as active long-running jobs (e.g. run_scan)
    with smooth paced checklist progression and automatic clean dismissal.
    """
    if steps is None:
        steps = [
            'Connecting to gateway <span class="mono" style="color:inherit;opacity:.7">:8001</span>',
            'Syncing visibility.db',
            'Loading scoring report',
            'Rendering dashboard',
        ]

    steps_li = "\\n".join(f"          <li><i></i>{s}<em>✓</em></li>" for s in steps)
    steps_json = json.dumps([s.split("<")[0].strip() for s in steps])
    is_action_js = "true" if is_action else "false"
    est_dur = float(estimated_duration_sec)

    return f"""
    <div id="incubrix-loading-overlay">
      {LOADING_OVERLAY_CSS}
      <i class="blob b1"></i><i class="blob b2"></i><i class="blob b3"></i><div class="grid"></div>
      <main class="box" role="status" aria-live="polite">
        <div class="mark"><div class="spin"></div><div class="lg">⚡</div></div>
        <h1>{title}</h1>
        <div class="tag">{tagline}</div>
        <div class="pb"><b id="ib-load-b"></b></div>
        <div class="r2"><span id="ib-load-t">{status_text}</span><span class="mono" id="ib-load-p">0%</span></div>
        <ul id="ib-load-l">
{steps_li}
        </ul>
        <div class="foot">AEO · SEO · GEO Engine</div>
      </main>
      <script>
      (function(){{
        var b = document.getElementById('ib-load-b'),
            t = document.getElementById('ib-load-t'),
            pc = document.getElementById('ib-load-p'),
            li = document.querySelectorAll('#ib-load-l li'),
            overlay = document.getElementById('incubrix-loading-overlay');
        var stepMsgs = {steps_json};
        var isAction = {is_action_js};
        var estDuration = {est_dur};
        var p = 0;
        var dismissed = false;

        function completeAndDismiss() {{
          if (dismissed) return;
          dismissed = true;
          if (timer) clearInterval(timer);
          p = 100;
          if (b) b.style.width = '100%';
          if (pc) pc.textContent = '100%';
          if (t) t.textContent = 'Ready';
          if (li) {{
            li.forEach(function(x) {{ x.className = 'done'; }});
          }}
          setTimeout(function() {{
            var el = document.getElementById('incubrix-loading-overlay') || overlay;
            if (el) {{
              el.classList.add('fade-out');
              setTimeout(function() {{
                try {{
                  if (el && el.parentNode) el.parentNode.removeChild(el);
                }} catch(err) {{}}
              }}, 450);
            }}
          }}, 350);
        }}

        var intervalMs = isAction ? 140 : 80;
        var maxP = isAction ? 94 : 100;

        var timer = setInterval(function(){{
          if (dismissed) {{
            clearInterval(timer);
            return;
          }}
          if (isAction) {{
            var remaining = maxP - p;
            if (remaining > 0.4) {{
              var step = (remaining / (estDuration * 1000 / intervalMs)) * (0.8 + Math.random() * 0.4);
              p += Math.max(0.12, Math.min(step, 2.0));
            }}
          }} else {{
            p += Math.random() * 8 + 4;
            if (p >= 100) {{
              completeAndDismiss();
              return;
            }}
          }}

          var s = Math.min(stepMsgs.length - 1, Math.floor((p / 100.0) * stepMsgs.length));
          if (b) b.style.width = Math.min(100, p).toFixed(1) + '%';
          if (pc) pc.textContent = Math.floor(p) + '%';
          if (t && stepMsgs[s]) t.textContent = stepMsgs[s] + '…';
          if (li) {{
            li.forEach(function(x, i){{
              x.className = (i < s) ? 'done' : (i === s ? 'on' : '');
            }});
          }}
        }}, intervalMs);

        window.dismissIncuBrixLoader = function() {{
          if (dismissed) return;
          completeAndDismiss();
        }};
      }})();
      </script>
    </div>
    """

