// V1 layer L5: independent render check of the self-contained viewer (copy under /tmp), offline.
// Expectations come from the BPMN XML (ipd:trace), not from citations.json:
//  - every request is the file itself, data: or blob: (all others aborted and reported)
//  - zero console errors and page errors, zero bpmn-js import warnings
//  - every BPMNDiagram of out/ipd_best_practice.bpmn opens (canvas root = its collaboration)
//  - overlay set per diagram = elements of that model with ipd:source children, except participants and lanes
//  - overlay badges = binding badge + DRAFT (draft="true") + VERIFY (ipd:verify, verify-binding, [verify] in loc/page)
//  - the panel of a selected element lists all its source keys/locs and REQ ids
//  - runtime DOM audit: every src/href is data:/blob:/#, a panel source link, or the bpmn.io watermark
// Usage: node tools/validate/v1_render.mjs --html <copy.html> --bpmn <ipd_best_practice.bpmn> --expected <v1_expected_traces.json> --citations <citations.json> --out <json> [--screens <dir>]
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const arg = (n, d) => { const i = process.argv.indexOf(n); return i >= 0 ? process.argv[i + 1] : d; };
const htmlFile = arg('--html'), bpmnFile = arg('--bpmn'), citFile = arg('--citations'), outFile = arg('--out');
const screens = arg('--screens', '');
const chromium = createRequire(path.join(ROOT, 'viewer', 'package.json'))('playwright-core').chromium;
const cit = JSON.parse(fs.readFileSync(citFile, 'utf8'));

// ---- expectations from the XML, parsed by tools/validate/v1_expected_traces.py (lxml) into --expected
const EXP = JSON.parse(fs.readFileSync(arg('--expected'), 'utf8'));
const diagrams = EXP.diagrams;
const traced = EXP.traced;
const BB = { 'binding-law': 'LAW', 'binding-ICH': 'ICH', 'guidance': 'GUIDANCE', 'best-practice': 'BP', 'verify-binding': 'VERIFY' };
const ORDER = ['LAW', 'ICH', 'GUIDANCE', 'DRAFT', 'BP', 'VERIFY'];
function expBadges(t) {
  const b = new Set();
  if (t.binding) b.add(BB[t.binding]);
  if (t.draft) b.add('DRAFT');
  if (t.verify || t.binding === 'verify-binding' || t.sources.some(s => /\[verify/.test(s.loc + s.page))) b.add('VERIFY');
  return ORDER.filter(x => b.has(x));
}
const allowedLinks = new Set();
// panel source links = every http(s) URL that occurs in citations.json (registry and finding URLs)
const citText = fs.readFileSync(citFile, 'utf8');
for (const m of citText.matchAll(/https?:\/\/[^"\s\\]+/g)) allowedLinks.add(m[0]);

const errors = [], passed = [], notes = [];
const E = (rule, el, msg, sev = 'MUST') => errors.push({ rule_id: rule, layer: 'L5', model: 'viewer', element: el, message: msg, severity: sev, owner: 'W1', status: 'open' });
const P = (check, count, note = '') => passed.push({ layer: 'L5', check, count, note });

const fileUrl = pathToFileURL(path.resolve(htmlFile)).href;
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
const requests = [], blocked = [];
await ctx.route('**/*', r => {
  const u = r.request().url();
  requests.push(u.slice(0, 120));
  if (u.split('#')[0] === fileUrl || /^(data|blob):/.test(u)) return r.continue();
  blocked.push(u);
  return r.abort();
});
const page = await ctx.newPage();
const consoleErr = [], pageErr = [];
page.on('console', m => { if (m.type() === 'error') consoleErr.push(m.text()); });
page.on('pageerror', e => pageErr.push(String(e)));
page.on('dialog', d => { E('VIEW-DIALOG', '-', 'dialog opened: ' + d.type()); d.dismiss(); });
await page.goto(fileUrl);
await page.waitForSelector('html[data-ready="1"]', { timeout: 60000 });
const warn = await page.evaluate(() => window.ipdImportWarnings || []);
if (warn.length) E('VIEW-IMPORT', '-', 'bpmn-js import warnings: ' + warn.slice(0, 3).join(' | ')); else P('bpmn-js import of the embedded XML: 0 warnings', 0);

const perDiagram = [];
let nOv = 0, nBadge = 0;
for (const d of diagrams) {
  const model = d.id.replace(/_DIAGRAM$/, '');
  await page.evaluate(id => window.ipdApp.open(id), d.id);
  await page.evaluate(() => window.ipdApp.idle());
  await page.waitForTimeout(150);
  const info = await page.evaluate(() => {
    const v = window.ipdApp.viewer;
    const root = v.get('canvas').getRootElement();
    const ov = [...document.querySelectorAll('.ipd-ov[data-ipd-el]')].map(o => ({ id: o.getAttribute('data-ipd-el'), badges: [...o.querySelectorAll('.b')].map(b => b.textContent.trim()) }));
    const shapes = v.get('elementRegistry').getAll().length;
    return { root: root && root.id, ov, shapes };
  });
  if (info.root !== d.collab) E('VIEW-OPEN', d.id, `diagram did not open (canvas root ${info.root}, expected ${d.collab})`);
  if (screens) await page.screenshot({ path: path.join(screens, `${d.id}.png`) });
  const want = Object.entries(traced).filter(([id, t]) => id.startsWith(model + '_') && !id.slice(model.length + 1).match(/^(P_|L_)/) && t.sources.length && !['participant', 'lane', 'process'].includes(t.tag)).map(([id]) => id).sort();
  const got = [...new Set(info.ov.map(o => o.id))].sort();
  const missing = want.filter(i => !got.includes(i)), extra = got.filter(i => !want.includes(i));
  if (missing.length || extra.length) E('VIEW-OVERLAY', d.id, `overlay set != elements with ipd:source (missing ${missing}, extra ${extra})`);
  const dup = info.ov.length - got.length;
  if (dup) E('VIEW-OVERLAY', d.id, `${dup} duplicate overlays`, 'SHOULD');
  for (const o of info.ov) {
    const t = traced[o.id]; if (!t) continue;
    nBadge++;
    const exp = expBadges(t);
    if (JSON.stringify(exp) !== JSON.stringify(o.badges)) E('LAY-04', o.id, `overlay badges ${JSON.stringify(o.badges)} != expected from ipd:trace ${JSON.stringify(exp)}`);
  }
  nOv += got.length;
  perDiagram.push({ diagram: d.id, opened: info.root === d.collab, overlays: got.length, expected: want.length, shapes: info.shapes });
}
P(`every diagram opens (${diagrams.length} BPMNDiagrams of the XML) and its overlay set equals the elements with ipd:source (participants and lanes are panel-only by design)`, nOv,
  perDiagram.map(p => `${p.diagram} ${p.overlays}/${p.expected}`).join(', '));
P('overlay badges are text (LAW/ICH/GUIDANCE/DRAFT/BP/VERIFY) and equal the badges derived from ipd:trace (LAY-04: meaning not by colour alone)', nBadge);

// panel: every traced task of two models
let nPanel = 0;
for (const model of ['L4_03', 'L4_05']) {
  await page.evaluate(id => window.ipdApp.open(id), model + '_DIAGRAM');
  await page.evaluate(() => window.ipdApp.idle());
  for (const [id, t] of Object.entries(traced)) {
    if (!id.startsWith(model + '_') || !['task', 'callActivity'].includes(t.tag)) continue;
    await page.evaluate(i => window.ipdApp.select(i), id);
    await page.waitForTimeout(30);
    const txt = await page.evaluate(() => document.querySelector('#panel-body').innerText);
    const miss = t.sources.filter(s => !txt.includes(s.key) || !txt.includes(s.loc.replace(/^21CFR\d+/, '').slice(0, 12))).map(s => s.key + ' ' + s.loc);
    const missR = t.reqs.filter(r => !txt.includes(r));
    if (miss.length || missR.length) E('VIEW-PANEL', id, `panel lacks sources ${miss.slice(0, 4)} / REQs ${missR}`);
    if (!txt.includes(t.binding)) E('VIEW-PANEL', id, `panel does not show binding ${t.binding}`, 'SHOULD');
    nPanel++;
  }
}
P('panel of every task/call activity of L4-03 and L4-05 lists all its source keys and locs, REQ ids and binding', nPanel);

// runtime DOM audit of src/href
const urls = await page.evaluate(() => {
  const out = [];
  for (const el of document.querySelectorAll('*')) {
    for (const a of ['src', 'href', 'xlink:href', 'srcset', 'action', 'poster']) {
      const v = el.getAttribute(a); if (v) out.push({ tag: el.tagName.toLowerCase(), a, v, cls: el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className });
    }
  }
  return out;
});
const bad = urls.filter(u => !/^(data:|blob:|#|javascript:void)/.test(u.v) && !(u.tag === 'a' && allowedLinks.has(u.v)) && !(u.tag === 'a' && /^https?:\/\/bpmn\.io\/?$/.test(u.v)));
if (bad.length) E('VIEW-SELFCONTAINED', '-', 'runtime src/href outside data:/blob:/#, panel source links and bpmn.io watermark: ' + JSON.stringify(bad.slice(0, 5)));
else P('runtime DOM audit: every src/href is data:/blob:/#, a panel source link from citations.json, or the bpmn.io watermark', urls.length,
  `${urls.filter(u => u.tag === 'a' && allowedLinks.has(u.v)).length} source links, ${urls.filter(u => /bpmn\.io/.test(u.v)).length} watermark`);

if (blocked.length) E('VIEW-NETWORK', '-', `${blocked.length} external requests attempted: ${blocked.slice(0, 5)}`);
else P('network: no request other than the file itself, data: and blob: (all others would be aborted)', requests.length);
if (consoleErr.length) E('VIEW-CONSOLE', '-', 'console errors: ' + consoleErr.slice(0, 3).join(' | '));
else P('zero console errors', 0);
if (pageErr.length) E('VIEW-CONSOLE', '-', 'page errors: ' + pageErr.slice(0, 3).join(' | '));
else P('zero page errors', 0);
await browser.close();
fs.writeFileSync(outFile, JSON.stringify({ errors, passed, perDiagram, notes, inputs: [htmlFile, bpmnFile, citFile] }, null, 1));
console.log(`v1_render: ${errors.length} errors, ${passed.length} passed`);
