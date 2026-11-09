#!/usr/bin/env node
// Render every BPMNDiagram of a .bpmn file to PNG with bpmn-js (NavigatedViewer)
// in headless Chrome. Offline: bundle and CSS are inlined, no network.
//
// Usage: node tools/render_screens.mjs --bpmn <file> --out-dir <dir>
//                  [--report <file.report.json>] [--zones]
// --zones draws the reserved overlay zones (from the spec2bpmn report) as
// dashed boxes, for the B2 visual clearance check. Without --zones the PNG
// shows the plain diagram.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const VENDOR = path.join(ROOT, 'vendor', 'node');
const require = createRequire(path.join(VENDOR, 'package.json'));
const { chromium } = require('playwright-core');

function arg(name, dflt) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : dflt;
}
const bpmnFile = arg('--bpmn');
const outDir = arg('--out-dir');
const reportFile = arg('--report');
const showZones = process.argv.includes('--zones');
if (!bpmnFile || !outDir) {
  console.error('usage: render_screens.mjs --bpmn <file> --out-dir <dir> [--report <json>] [--zones]');
  process.exit(2);
}
fs.mkdirSync(outDir, { recursive: true });

const xml = fs.readFileSync(bpmnFile, 'utf8');
const ipd = fs.readFileSync(path.join(ROOT, 'contracts', 'ipd_moddle.json'), 'utf8');
const bjs = path.join(VENDOR, 'node_modules', 'bpmn-js', 'dist');
const bundle = fs.readFileSync(path.join(bjs, 'bpmn-navigated-viewer.production.min.js'), 'utf8');
const css = ['diagram-js.css', 'bpmn-js.css'].map(f => fs.readFileSync(path.join(bjs, 'assets', f), 'utf8')).join('\n');
const report = reportFile ? JSON.parse(fs.readFileSync(reportFile, 'utf8')) : { models: [] };
const zonesByDiagram = {};
for (const m of report.models) zonesByDiagram[m.diagram] = m.overlay_zones;

const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>${css}
html,body{margin:0;padding:0;background:#fff}#c{position:absolute;left:0;top:0;width:100%;height:100%}
.zone{border:1px dashed #d33;background:rgba(220,50,50,0.08);box-sizing:border-box;font:9px Arial;color:#d33}
</style></head><body><div id="c"></div><script>${bundle}</script></body></html>`;

const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
const errors = [];
page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errors.push(m.text()); });
page.on('pageerror', e => errors.push(String(e)));
await page.route('**/*', r => r.abort());
await page.setContent(html, { waitUntil: 'load' });

const diagrams = await page.evaluate(async ({ xml, ipd }) => {
  window.viewer = new BpmnJS({ container: '#c', moddleExtensions: { ipd: JSON.parse(ipd) } });
  const res = await window.viewer.importXML(xml);
  window.importWarnings = res.warnings.map(w => w.message);
  return window.viewer.getDefinitions().diagrams.map(d => d.id);
}, { xml, ipd });

const results = [];
for (const id of diagrams) {
  const box = await page.evaluate(async ({ id, zones, showZones }) => {
    const r = await window.viewer.open(id);
    const canvas = window.viewer.get('canvas');
    if (showZones && zones) {
      const layer = canvas.getLayer('zones', 2000);
      layer.innerHTML = '';
      const ns = 'http://www.w3.org/2000/svg';
      for (const [eid, z] of Object.entries(zones)) {
        const rect = document.createElementNS(ns, 'rect');
        rect.setAttribute('x', z[0]); rect.setAttribute('y', z[1]);
        rect.setAttribute('width', z[2]); rect.setAttribute('height', z[3]);
        rect.setAttribute('fill', 'rgba(220,50,50,0.07)'); rect.setAttribute('stroke', '#d33');
        rect.setAttribute('stroke-dasharray', '4 3');
        layer.appendChild(rect);
      }
    }
    // call activities: free space between the rendered label text and the shape bottom
    // (W1 "Open L4" chip sits at the bottom border); measured on the bpmn-js SVG
    const reg = window.viewer.get('elementRegistry');
    const callLabels = reg.filter(e => e.type === 'bpmn:CallActivity').map(e => {
      const t = reg.getGraphics(e).querySelector('.djs-visual text');
      if (!t) return { id: e.id, free: null };
      const bb = t.getBBox();
      return { id: e.id, free: Math.floor(e.height - (bb.y + bb.height)), width: e.width };
    });
    const inner = canvas.viewbox().inner;
    return { warnings: r.warnings.map(w => w.message), x: inner.x, y: inner.y, w: inner.width, h: inner.height, callLabels };
  }, { id, zones: zonesByDiagram[id], showZones });
  const W = Math.ceil(box.w + 40), H = Math.ceil(box.h + 40);
  await page.setViewportSize({ width: Math.min(W, 6000), height: Math.min(H, 6000) });
  await page.evaluate(({ x, y, w, h }) => {
    const canvas = window.viewer.get('canvas');
    canvas.resized();
    canvas.viewbox({ x: x - 20, y: y - 20, width: w + 40, height: h + 40 });
  }, box);
  const file = path.join(outDir, `${id}${showZones ? '_zones' : ''}.png`);
  await page.screenshot({ path: file, fullPage: false });
  results.push({ diagram: id, file, width: W, height: H, warnings: box.warnings, callLabels: box.callLabels });
}
const importWarnings = await page.evaluate(() => window.importWarnings);
await browser.close();
console.log(JSON.stringify({ diagrams: results, importWarnings, consoleErrors: errors }, null, 2));
