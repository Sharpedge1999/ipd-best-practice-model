// V1 layer L5 (round 3): independent check of the publish variant (out/publish) served from a /tmp copy, offline.
// - python3 -I -m http.server serves the copy on 127.0.0.1 (own files);
// - the two pinned CDN script URLs are routed to the local files of the same package version in viewer/node_modules,
//   served with Access-Control-Allow-Origin so that the browser itself verifies the integrity (SRI) attribute;
// - every other request is aborted and reported;
// - asserts: zero console errors, zero page errors, no SRI/integrity message, only CDN + own-file requests,
//   every BPMNDiagram opens, overlay set per diagram = elements with ipd:source (expectations from the served XML via
//   v1_expected_traces.py), badges = ipd:trace, minimap closed by default;
// - negative control: a second page load with one CDN body altered by one byte must be blocked by SRI.
// Usage: node tools/validate/v1_publish.mjs --dir <copy of out/publish> --expected <json> --out <json> [--screens <dir>]
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const arg = (n, d) => { const i = process.argv.indexOf(n); return i >= 0 ? process.argv[i + 1] : d; };
const dir = path.resolve(arg('--dir')), outFile = arg('--out'), screens = arg('--screens', '');
const EXP = JSON.parse(fs.readFileSync(arg('--expected'), 'utf8'));
const chromium = createRequire(path.join(ROOT, 'viewer', 'package.json'))('playwright-core').chromium;
const errors = [], passed = [], notes = [];
const E = (rule, el, msg, sev = 'MUST') => errors.push({ rule_id: rule, layer: 'L5', model: 'publish', element: el, message: msg, severity: sev, owner: 'W1', status: 'open' });
const P = (check, count, note = '') => passed.push({ layer: 'L5', check, count, note });

// ---- static: script tags, pinned versions, SRI = sha384 of the local pinned file
const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
const tags = [...html.matchAll(/<script\b([^>]*)>/gi)].map(m => m[1]).filter(a => /\ssrc=/.test(a)).map(a => ({
  src: (a.match(/\ssrc="([^"]*)"/) || [])[1], integrity: (a.match(/\sintegrity="([^"]*)"/) || [])[1], crossorigin: (a.match(/\scrossorigin="([^"]*)"/) || [])[1] }));
const cdn = new Map();
const sri = b => 'sha384-' + crypto.createHash('sha384').update(b).digest('base64');
const staticProblems = [];
for (const t of tags) {
  const m = (t.src || '').match(/^https:\/\/cdn\.jsdelivr\.net\/npm\/((?:@[^/@]+\/)?[^/@]+)@([^/]+)\/(.+)$/);
  if (!m) { if (/^https?:/i.test(t.src)) staticProblems.push('external script not on cdn.jsdelivr.net: ' + t.src); continue; }
  const [, pkg, ver, file] = m, pdir = path.join(ROOT, 'viewer', 'node_modules', pkg);
  const have = JSON.parse(fs.readFileSync(path.join(pdir, 'package.json'), 'utf8')).version;
  if (have !== ver) { staticProblems.push(`${pkg}@${ver} pinned, local ${have}`); continue; }
  const body = fs.readFileSync(path.join(pdir, file));
  if (t.integrity !== sri(body)) staticProblems.push(`${t.src}: integrity ${t.integrity} != sha384 of local file ${sri(body)}`);
  if (t.crossorigin !== 'anonymous') staticProblems.push(`${t.src}: crossorigin=${t.crossorigin}`);
  cdn.set(t.src, body);
}
const pins = [...cdn.keys()].map(u => u.replace('https://cdn.jsdelivr.net/npm/', ''));
if (cdn.size !== 2) staticProblems.push(`expected 2 pinned CDN scripts, found ${cdn.size}: ${pins}`);
const ownScripts = tags.filter(t => !/^https?:/i.test(t.src)).map(t => t.src);
if (staticProblems.length) E('VIEW-SRI', 'index.html', 'static script check: ' + staticProblems.join(' | '));
else P(`static: exactly 2 CDN scripts (${pins.join(', ')}), each pinned to the version in viewer/node_modules, integrity = sha384 of that file, crossorigin="anonymous"; own scripts ${ownScripts.join(', ')}`, 2);
const links = [...html.matchAll(/<link\b[^>]*>/gi)].map(m => m[0]);
const extCss = links.filter(l => /stylesheet/i.test(l));
if (extCss.length) E('VIEW-SELFCONTAINED', 'index.html', 'stylesheet links: ' + extCss.join(' '), 'SHOULD');
else P('static: no stylesheet link (CSS inline); only <link rel="icon" href="data:,">', links.length);

// ---- server
const server = spawn('python3', ['-I', '-u', '-m', 'http.server', '0', '--bind', '127.0.0.1', '--directory', dir], { stdio: ['ignore', 'pipe', 'pipe'] });
const port = await new Promise((resolve, reject) => {
  let buf = '';
  const t = setTimeout(() => reject(new Error('http.server did not start')), 15000);
  server.stdout.on('data', d => { buf += d; const m = buf.match(/port (\d+)/); if (m) { clearTimeout(t); resolve(Number(m[1])); } });
});
const origin = `http://127.0.0.1:${port}`;
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] });

async function load(tamper) {
  const ctx = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const reqs = [], blocked = [], cdnServed = [];
  await ctx.route('**/*', r => {
    const u = r.request().url();
    reqs.push(u);
    if (cdn.has(u)) {
      let body = cdn.get(u);
      if (tamper && u === tamper) body = Buffer.concat([body, Buffer.from('\n/* tampered */\n')]);
      cdnServed.push(u);
      return r.fulfill({ status: 200, body, headers: { 'content-type': 'application/javascript; charset=utf-8', 'access-control-allow-origin': '*' } });
    }
    if (u.startsWith(origin + '/') || /^(data|blob):/.test(u)) return r.continue();
    blocked.push(u);
    return r.abort();
  });
  const page = await ctx.newPage();
  const cons = [], pageErr = [], dialogs = [];
  page.on('console', m => { if (m.type() === 'error' || /integrity/i.test(m.text())) cons.push(m.type() + ': ' + m.text()); });
  page.on('pageerror', e => pageErr.push(String(e)));
  page.on('dialog', d => { dialogs.push(d.type()); d.dismiss(); });
  await page.goto(origin + '/index.html');
  return { ctx, page, reqs, blocked, cdnServed, cons, pageErr, dialogs };
}

// ---- main load
const L = await load(null);
let ready = true;
try { await L.page.waitForSelector('html[data-ready="1"]', { timeout: 60000 }); } catch (e) { ready = false; }
if (!ready) {
  const msg = await L.page.evaluate(() => (document.getElementById('canvas-msg') || {}).textContent || '');
  E('VIEW-OPEN', '-', 'viewer did not become ready: ' + msg + ' | console ' + L.cons.slice(0, 3).join(' | '));
} else {
  P('page loads from the local server with the CDN routed to the pinned local files; viewer ready (data-ready=1)', 1);
  const warn = await L.page.evaluate(() => window.ipdImportWarnings || []);
  if (warn.length) E('VIEW-IMPORT', '-', 'bpmn-js import warnings: ' + warn.slice(0, 3).join(' | ')); else P('bpmn-js import of the served XML (data/ipd_best_practice.bpmn): 0 warnings', 0);
  const BB = { 'binding-law': 'LAW', 'binding-ICH': 'ICH', 'guidance': 'GUIDANCE', 'best-practice': 'BP', 'verify-binding': 'VERIFY' };
  const ORDER = ['LAW', 'ICH', 'GUIDANCE', 'DRAFT', 'BP', 'VERIFY'];
  const expBadges = t => { const b = new Set(); if (t.binding) b.add(BB[t.binding]); if (t.draft) b.add('DRAFT');
    if (t.verify || t.binding === 'verify-binding' || t.sources.some(s => /\[verify/.test(s.loc + s.page))) b.add('VERIFY'); return ORDER.filter(x => b.has(x)); };
  const per = [];
  let nOv = 0, nBadge = 0, nMini = 0;
  for (const d of EXP.diagrams) {
    const model = d.id.replace(/_DIAGRAM$/, '');
    await L.page.evaluate(id => window.ipdApp.open(id), d.id);
    await L.page.evaluate(() => window.ipdApp.idle());
    await L.page.waitForTimeout(200);
    const info = await L.page.evaluate(() => {
      const v = window.ipdApp.viewer;
      const root = v.get('canvas').getRootElement();
      const ov = [...document.querySelectorAll('.ipd-ov[data-ipd-el]')].map(o => ({ id: o.getAttribute('data-ipd-el'), badges: [...o.querySelectorAll('.b')].map(b => b.textContent.trim()) }));
      const mm = document.querySelector('.djs-minimap');
      const mmOpen = !!(mm && mm.classList.contains('open'));
      const zoom = v.get('canvas').zoom();
      return { root: root && root.id, ov, mmOpen, zoom };
    });
    if (info.root !== d.collab) E('VIEW-OPEN', d.id, `diagram did not open (canvas root ${info.root}, expected ${d.collab})`);
    if (info.mmOpen) E('VIEW-READABILITY', d.id, 'minimap open by default', 'SHOULD'); else nMini++;
    const want = Object.entries(EXP.traced).filter(([id, t]) => id.startsWith(model + '_') && !id.slice(model.length + 1).match(/^(P_|L_)/) && t.sources.length && !['participant', 'lane', 'process'].includes(t.tag)).map(([id]) => id).sort();
    const got = [...new Set(info.ov.map(o => o.id))].sort();
    const missing = want.filter(i => !got.includes(i)), extra = got.filter(i => !want.includes(i));
    if (missing.length || extra.length) E('VIEW-OVERLAY', d.id, `overlay set != elements with ipd:source (missing ${missing}, extra ${extra})`);
    if (info.ov.length !== got.length) E('VIEW-OVERLAY', d.id, `${info.ov.length - got.length} duplicate overlays`, 'SHOULD');
    for (const o of info.ov) { const t = EXP.traced[o.id]; if (!t) continue; nBadge++;
      const ex = expBadges(t); if (JSON.stringify(ex) !== JSON.stringify(o.badges)) E('LAY-04', o.id, `badges ${JSON.stringify(o.badges)} != ${JSON.stringify(ex)}`); }
    nOv += got.length;
    per.push({ diagram: d.id, opened: info.root === d.collab, overlays: got.length, expected: want.length, zoom: Math.round(info.zoom * 100) });
    if (screens && ['L3_DIAGRAM', 'L4_02_DIAGRAM', 'L4_03_DIAGRAM'].includes(d.id)) await L.page.screenshot({ path: path.join(screens, `publish_${d.id}.png`) });
  }
  P(`every diagram opens (${EXP.diagrams.length} BPMNDiagrams of the served XML) and its overlay set equals the elements with ipd:source`, nOv,
    per.map(p => `${p.diagram} ${p.overlays}/${p.expected} (zoom ${p.zoom}%)`).join(', '));
  P('overlay badges equal the badges derived from ipd:trace (LAY-04)', nBadge);
  P('minimap closed by default on every diagram', nMini);
  const wm = await L.page.evaluate(() => !!document.querySelector('a[href^="https://bpmn.io"], .bjs-powered-by'));
  if (!wm) E('VIEW-LICENCE', '-', 'bpmn.io watermark missing', 'SHOULD'); else P('bpmn.io watermark present (licence)', 1);
}
const own = [...new Set(L.reqs.filter(u => u.startsWith(origin + '/')).map(u => u.slice(origin.length + 1).split('?')[0]))].sort();
const cdnReq = [...new Set(L.reqs.filter(u => cdn.has(u)))];
const other = L.reqs.filter(u => !u.startsWith(origin + '/') && !cdn.has(u) && !/^(data|blob):/.test(u));
if (other.length || L.blocked.length) E('VIEW-NETWORK', '-', `requests outside CDN + own files: ${[...new Set(other)].slice(0, 6)}`);
else P(`network: only the 2 pinned CDN scripts and own files (${own.join(', ')}); no other request`, L.reqs.length, `CDN ${cdnReq.length}, own ${own.length}`);
const sriMsgs = L.cons.filter(c => /integrity/i.test(c));
if (sriMsgs.length) E('VIEW-SRI', '-', 'SRI messages: ' + sriMsgs.slice(0, 3).join(' | ')); else P('no SRI / integrity message (both CDN scripts accepted by the browser integrity check)', 0);
const ce = L.cons.filter(c => c.startsWith('error'));
if (ce.length) E('VIEW-CONSOLE', '-', 'console errors: ' + ce.slice(0, 3).join(' | ')); else P('zero console errors', 0);
if (L.pageErr.length) E('VIEW-CONSOLE', '-', 'page errors: ' + L.pageErr.slice(0, 3).join(' | ')); else P('zero page errors', 0);
if (L.dialogs.length) E('VIEW-DIALOG', '-', 'dialogs: ' + L.dialogs.join(',')); else P('no alert/confirm/prompt dialog', 0);
await L.ctx.close();

// ---- negative control: tampered CDN body must be rejected by SRI
const first = [...cdn.keys()][0];
const N = await load(first);
await N.page.waitForTimeout(4000);
const nReady = await N.page.evaluate(() => document.documentElement.getAttribute('data-ready'));
const nMsg = await N.page.evaluate(() => (document.getElementById('canvas-msg') || {}).textContent || '');
const nSri = N.cons.filter(c => /integrity/i.test(c));
if (nSri.length && nReady !== '1') P('negative control: one CDN body altered by one comment line -> browser blocks it (integrity message) and the page shows its failure message instead of a diagram', 1,
  `${nSri[0].slice(0, 160)} | canvas: ${nMsg.slice(0, 120)}`);
else E('VIEW-SRI', '-', `negative control failed: tampered ${first} not blocked (ready=${nReady}, integrity messages ${nSri.length})`);
await N.ctx.close();
await browser.close();
server.kill();
fs.writeFileSync(outFile, JSON.stringify({ errors, passed, notes, perDiagram: [], origin, own_files: own, cdn: pins,
  inputs: [dir + ' (copy of out/publish)', 'viewer/node_modules (pinned CDN stand-ins)'] }, null, 1));
console.log(`v1_publish: ${errors.length} errors, ${passed.length} passed`);
for (const e of errors) console.log('ERR', e.rule_id, e.element, e.message.slice(0, 300));
for (const p of passed) console.log('OK ', p.check.slice(0, 140), p.count, (p.note || '').slice(0, 300));
process.exit(0);
