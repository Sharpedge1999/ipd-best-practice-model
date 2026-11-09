// V1 round 3: close-up screenshots of the changed regions (offline, single-file copy under /tmp), plus a DI proximity
// measurement between message-flow and sequence-flow segments inside those regions.
// Usage: node tools/validate/v1_r3_zoomshots.mjs --html <copy.html> --out-dir <dir> --json <file>
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const arg = (n, d) => { const i = process.argv.indexOf(n); return i >= 0 ? process.argv[i + 1] : d; };
const html = arg('--html'), outDir = arg('--out-dir'), jsonOut = arg('--json');
fs.mkdirSync(outDir, { recursive: true });
const chromium = createRequire(path.join(ROOT, 'viewer', 'package.json'))('playwright-core').chromium;
const REGIONS = [
  { name: 'L3_block', diagram: 'L3_DIAGRAM', ids: ['L3_A1', 'L3_G1', 'L3_A2', 'L3_G5', 'L3_A3', 'L3_G6', 'L3_G2'], zoom: 1 },
  { name: 'L4_02_investigator', diagram: 'L4_02_DIAGRAM', ids: ['L4_02_S2', 'L4_02_A13', 'L4_02_A14', 'L4_02_G4', 'L4_02_A15', 'L4_02_A16', 'L4_02_G5', 'L4_02_E3'], zoom: 0.9 },
  { name: 'L4_02_channels', diagram: 'L4_02_DIAGRAM', ids: ['L4_02_S1', 'L4_02_G1', 'L4_02_A1', 'L4_02_A6'], zoom: 1 },
  { name: 'L4_03_sponsor_entry', diagram: 'L4_03_DIAGRAM', ids: ['L4_03_S1', 'L4_03_A14', 'L4_03_G1', 'L4_03_A1', 'L4_03_G4'], zoom: 1 },
];
const fileUrl = pathToFileURL(path.resolve(html)).href;
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
await ctx.route('**/*', r => { const u = r.request().url(); return (u.split('#')[0] === fileUrl || /^(data|blob):/.test(u)) ? r.continue() : r.abort(); });
const page = await ctx.newPage();
const cons = [];
page.on('console', m => { if (m.type() === 'error') cons.push(m.text()); });
await page.goto(fileUrl);
await page.waitForSelector('html[data-ready="1"]', { timeout: 60000 });
const res = [];
for (const R of REGIONS) {
  await page.evaluate(id => window.ipdApp.open(id), R.diagram);
  await page.evaluate(() => window.ipdApp.idle());
  const info = await page.evaluate(({ ids, zoom }) => {
    const v = window.ipdApp.viewer, reg = v.get('elementRegistry'), canvas = v.get('canvas');
    const els = ids.map(i => reg.get(i)).filter(Boolean);
    const x0 = Math.min(...els.map(e => e.x)), y0 = Math.min(...els.map(e => e.y));
    const x1 = Math.max(...els.map(e => e.x + e.width)), y1 = Math.max(...els.map(e => e.y + e.height));
    const outer = canvas.viewbox().outer;
    const w = outer.width / zoom, h = outer.height / zoom;
    canvas.viewbox({ x: (x0 + x1) / 2 - w / 2, y: (y0 + y1) / 2 - h / 2, width: w, height: h });
    // proximity: parallel message-flow vs sequence-flow segments closer than 10 px over more than 20 px
    const conns = reg.getAll().filter(e => e.waypoints && (e.type === 'bpmn:MessageFlow' || e.type === 'bpmn:SequenceFlow'));
    const segs = c => c.waypoints.slice(1).map((p, k) => [c.waypoints[k], p]);
    const close = [];
    for (const m of conns.filter(c => c.type === 'bpmn:MessageFlow')) for (const s of conns.filter(c => c.type === 'bpmn:SequenceFlow')) {
      for (const [a, b] of segs(m)) for (const [c, d] of segs(s)) {
        const hor = (p, q) => Math.abs(p.y - q.y) < 0.5, ver = (p, q) => Math.abs(p.x - q.x) < 0.5;
        if (hor(a, b) && hor(c, d)) {
          const ov = Math.min(Math.max(a.x, b.x), Math.max(c.x, d.x)) - Math.max(Math.min(a.x, b.x), Math.min(c.x, d.x));
          const gap = Math.abs(a.y - c.y);
          if (ov > 20 && gap < 10) close.push(`${m.id} || ${s.id} horizontal, gap ${gap.toFixed(0)} px over ${ov.toFixed(0)} px`);
        }
        if (ver(a, b) && ver(c, d)) {
          const ov = Math.min(Math.max(a.y, b.y), Math.max(c.y, d.y)) - Math.max(Math.min(a.y, b.y), Math.min(c.y, d.y));
          const gap = Math.abs(a.x - c.x);
          if (ov > 20 && gap < 10) close.push(`${m.id} || ${s.id} vertical, gap ${gap.toFixed(0)} px over ${ov.toFixed(0)} px`);
        }
      }
    }
    return { box: [x0, y0, x1, y1].map(Math.round), close };
  }, R);
  await page.waitForTimeout(300);
  const file = path.join(outDir, `${R.name}.png`);
  await page.screenshot({ path: file });
  res.push({ region: R.name, diagram: R.diagram, file, ...info });
}
await browser.close();
fs.writeFileSync(jsonOut, JSON.stringify({ regions: res, console_errors: cons }, null, 1));
console.log(JSON.stringify({ regions: res.map(r => ({ region: r.region, close: r.close })), console_errors: cons }, null, 1));
