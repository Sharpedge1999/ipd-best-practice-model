#!/usr/bin/env node
// W1 headless test of the self-contained iPD viewer page (playwright-core + Chrome, offline).
//
// Usage: node tools/test_viewer.mjs --html <page.html> --citations <citations.json> --screens <dir>
//                                   [--chrome /usr/bin/google-chrome] [--json-out <file>] [--expect-may <id,id>]
//        node tools/test_viewer.mjs --publish-dir <dir> --screens <dir> [...]   (multi-file hosted variant)
// --publish-dir: serves <dir> with python -I -m http.server on 127.0.0.1, routes the pinned jsDelivr script URLs
// of index.html to the local files in viewer/node_modules (so SRI is checked by the browser) and replaces the
// single-file self-containment checks by: CDN scripts exactly the pinned ones with sha384 integrity and
// crossorigin, no third-party code in the publish files, network = those scripts + own files, plus an SRI
// tamper check. All other assertions are the same.
// Checks: static self-containment (no external src/href outside scripts, size < 5 MB, no dialog APIs),
// zero console errors / page errors, no network requests except the file itself and data:/blob:,
// every diagram opens and renders, overlay count per diagram = elements with sources (citations.json,
// cross-checked against ipd:trace in the imported model), overlays inside their zones and clear of
// other shapes, labels, edges and overlays, click panel content, filters and match counts, hash
// routing, copy button, responsive panel, runtime href/src audit; default view (Fit when legible, else 75 %
// at the left edge, centred on the Sponsor pool, process start event and its first step kept in view), minimap (inlined, closed by default on every diagram,
// toggle, choice held across diagrams, navigation), MAY chip for elements whose REQs are all modal "may" (--expect-may lists
// element ids that must carry it) and REQ modal in the panel. Screenshots go to --screens.
// Exit code: 0 all assertions pass, 1 failures, 2 usage error.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawn } from 'node:child_process';
import crypto from 'node:crypto';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
function arg(name, dflt) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : dflt; }
const publishDir = arg('--publish-dir') ? path.resolve(arg('--publish-dir')) : null;
const htmlFile = arg('--html', publishDir ? path.join(publishDir, 'index.html') : undefined);
const citFile = arg('--citations', publishDir ? path.join(publishDir, 'data', 'citations.json') : undefined);
const screens = arg('--screens');
const chromePath = arg('--chrome', '/usr/bin/google-chrome');
const jsonOut = arg('--json-out');
const expectMay = (arg('--expect-may', '') || '').split(',').map(x => x.trim()).filter(Boolean);
// spec values of the default view (W1 change 1): below LEGIBLE fit zoom, open at READABLE_ZOOM
const LEGIBLE = 0.6, READABLE_ZOOM = 0.75;
const BINDING_BADGE = { 'binding-law': 'LAW', 'binding-ICH': 'ICH', 'guidance': 'GUIDANCE', 'best-practice': 'BP', 'verify-binding': 'VERIFY' };
function mayOnly(rec) { return rec.reqs.length > 0 && rec.reqs.every(q => q.found && q.modal === 'may'); }
if (!htmlFile || !citFile || !screens) {
  console.error('usage: test_viewer.mjs (--html <page.html> --citations <citations.json> | --publish-dir <dir>) --screens <dir> [--chrome <path>] [--json-out <file>] [--expect-may <ids>]');
  process.exit(2);
}
let chromium;
for (const base of [path.join(ROOT, 'viewer'), path.join(ROOT, 'vendor', 'node')]) {
  try { chromium = createRequire(path.join(base, 'package.json'))('playwright-core').chromium; break; } catch (e) { /* next */ }
}
if (!chromium) { console.error('playwright-core not found (viewer/node_modules or vendor/node)'); process.exit(2); }

fs.mkdirSync(screens, { recursive: true });
const CIT = JSON.parse(fs.readFileSync(citFile, 'utf8'));
const EL = CIT.elements;
const html = fs.readFileSync(htmlFile, 'utf8');
const fileUrl = pathToFileURL(path.resolve(htmlFile)).href;
let pageUrl = fileUrl, origin = null, server = null;
// publish variant: pinned CDN script URL -> local file of the same package version in viewer/node_modules
const cdnMap = new Map();
const sri384 = file => 'sha384-' + crypto.createHash('sha384').update(fs.readFileSync(file)).digest('base64');
function ownRel(u) {
  if (!publishDir || typeof u !== 'string' || !/^[A-Za-z0-9_][A-Za-z0-9_./-]*$/.test(u) || u.includes('..')) return false;
  return fs.existsSync(path.join(publishDir, u));
}
if (publishDir) {
  for (const m of html.matchAll(/<script\b[^>]*\ssrc="(https:\/\/cdn\.jsdelivr\.net\/npm\/((?:@[^/@]+\/)?[^/@]+)@([^/]+)\/([^"]+))"/g)) {
    const [, url, pkg, ver, file] = m, dir = path.join(ROOT, 'viewer', 'node_modules', pkg);
    const pj = path.join(dir, 'package.json');
    if (fs.existsSync(pj) && JSON.parse(fs.readFileSync(pj, 'utf8')).version === ver && fs.existsSync(path.join(dir, file))) cdnMap.set(url, path.join(dir, file));
  }
  server = spawn('python3', ['-I', '-u', '-m', 'http.server', '0', '--bind', '127.0.0.1', '--directory', publishDir], { stdio: ['ignore', 'pipe', 'ignore'] });
  process.on('exit', () => { try { server.kill(); } catch (e) { /* gone */ } });
  const port = await new Promise((resolve, reject) => {
    let buf = '';
    const t = setTimeout(() => reject(new Error('http.server did not start')), 15000);
    server.stdout.on('data', d => { buf += d; const m = buf.match(/port (\d+)/); if (m) { clearTimeout(t); resolve(Number(m[1])); } });
    server.on('exit', c => reject(new Error('http.server exited with ' + c)));
  });
  origin = `http://127.0.0.1:${port}`;
  pageUrl = origin + '/index.html';
}

const results = [];
let failures = 0;
function check(ok, name, detail) {
  results.push({ ok: !!ok, name, detail: detail === undefined ? '' : detail });
  if (!ok) failures++;
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}${detail !== undefined && detail !== '' ? ' - ' + (typeof detail === 'string' ? detail : JSON.stringify(detail)) : ''}`);
}
const notes = [];
function note(s) { notes.push(s); console.log('NOTE ' + s); }

// ---------------------------------------------------------------- static checks
const size = Buffer.byteLength(html, 'utf8');
check(size < 5 * 1024 * 1024, 'static: HTML size under 5 MB', `${size} bytes`);
const markup = html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '<script></script>')
  .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, '<style></style>');
const attrUrls = [...markup.matchAll(/\s(?:src|href|srcset|action|poster|data)\s*=\s*["']?([^"'\s>]+)/gi)].map(m => m[1]);
const extAttr = attrUrls.filter(u => !/^(data:|blob:|#)/i.test(u));
if (!publishDir) {
  check(extAttr.length === 0, 'static: no external URL in src/href attributes of the markup', extAttr);
  check(!/<link\b[^>]*rel=["']?stylesheet/i.test(markup) && !/<script\b[^>]*\ssrc=/i.test(html.replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, m => m.slice(0, m.indexOf('>') + 1))),
    'static: no external stylesheet or script tags');
} else {
  const V = CIT.meta.viewer || {};
  const want = [`https://cdn.jsdelivr.net/npm/bpmn-js@${V.bpmn_js}/dist/bpmn-navigated-viewer.production.min.js`,
    `https://cdn.jsdelivr.net/npm/diagram-js-minimap@${V.minimap}/dist/diagram-minimap.umd.prod.js`];
  const tags = [...html.matchAll(/<script\b([^>]*)>/gi)].map(m => m[1]).filter(a => /\ssrc=/.test(a)).map(a => ({
    src: (a.match(/\ssrc="([^"]*)"/) || [])[1], integrity: (a.match(/\sintegrity="([^"]*)"/) || [])[1], crossorigin: (a.match(/\scrossorigin="([^"]*)"/) || [])[1] }));
  const cdnTags = tags.filter(t => /^https?:/i.test(t.src));
  const sriProblems = [];
  if (JSON.stringify(cdnTags.map(t => t.src)) !== JSON.stringify(want)) sriProblems.push({ cdn: cdnTags.map(t => t.src), want });
  cdnTags.forEach(t => {
    if (!cdnMap.has(t.src)) sriProblems.push(t.src + ': no pinned local file of this version');
    else if (t.integrity !== sri384(cdnMap.get(t.src))) sriProblems.push(`${t.src}: integrity ${t.integrity} != ${sri384(cdnMap.get(t.src))}`);
    if (t.crossorigin !== 'anonymous') sriProblems.push(t.src + ': crossorigin ' + t.crossorigin);
  });
  check(sriProblems.length === 0, `static: exactly the two pinned CDN scripts, each with sha384 integrity of the local pinned file and crossorigin="anonymous"`, sriProblems.length ? sriProblems : cdnTags.map(t => t.integrity));
  const ownTags = tags.filter(t => !/^https?:/i.test(t.src));
  check(ownTags.length > 0 && ownTags.every(t => ownRel(t.src)) && !/<link\b[^>]*rel=["']?stylesheet/i.test(markup),
    'static: other scripts are own files by relative path; no stylesheet links (all CSS inline)', ownTags.map(t => t.src));
  const badAttr = extAttr.filter(u => !want.includes(u) && !ownRel(u));
  check(badAttr.length === 0, 'static: markup src/href only data:, own relative files and the two pinned CDN scripts', badAttr);
  // no inline or copied third-party code anywhere in the publish files; licence notices kept
  const files = [];
  (function walk(d) { for (const e of fs.readdirSync(d, { withFileTypes: true })) { const f = path.join(d, e.name); if (e.isDirectory()) walk(f); else files.push(f); } })(publishDir);
  const probes = [...cdnMap.values()].flatMap(f => { const t = fs.readFileSync(f, 'utf8'); return [0.25, 0.5, 0.75].map(q => t.slice(Math.floor(t.length * q), Math.floor(t.length * q) + 120)); });
  const copies = files.filter(f => { const t = fs.readFileSync(f, 'utf8'); return /\.BpmnJS=|\.DiagramJSMinimap=/.test(t) || probes.some(p => t.includes(p)); });
  check(probes.length === 6 && copies.length === 0, `static: no third-party code in the ${files.length} publish files (bundle probes and UMD globals absent)`, copies.map(f => path.relative(publishDir, f)));
  check(/<!--[^]*?bpmn-js - bpmn-navigated-viewer v[\d.]+ \| Copyright[^]*?-->/.test(html) && /<!--[^]*?diagram-js-minimap v[\d.]+[^]*?The MIT License[^]*?-->/.test(html),
    'static: licence notices of bpmn-js and diagram-js-minimap kept in index.html');
  const sameApp = fs.readFileSync(path.join(publishDir, 'app.js'), 'utf8') === fs.readFileSync(path.join(ROOT, 'viewer', 'src', 'app.js'), 'utf8') &&
    fs.readFileSync(path.join(publishDir, 'boot.js'), 'utf8') === fs.readFileSync(path.join(ROOT, 'viewer', 'src', 'boot.js'), 'utf8');
  const cfg = JSON.parse((html.match(/<script id="ipd-publish" type="application\/json">([^<]*)<\/script>/) || [])[1] || 'null');
  const srcBpmn = path.join(ROOT, CIT.meta.inputs.bpmn.file);
  check(sameApp && cfg && ownRel(cfg.bpmn) && ownRel(cfg.citations) && fs.readFileSync(path.join(publishDir, cfg.bpmn)).equals(fs.readFileSync(srcBpmn)) &&
    path.resolve(publishDir, cfg.citations) === path.resolve(citFile),
    `static: app.js and boot.js equal viewer/src; ${cfg && cfg.bpmn} equals ${CIT.meta.inputs.bpmn.file}; citations from ${cfg && cfg.citations}`);
  const bootJs = fs.readFileSync(path.join(ROOT, 'viewer', 'src', 'boot.js'), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');
  check(!/\b(alert|confirm|prompt)\s*\(/.test(bootJs) && !/window\.open\b|XMLHttpRequest|WebSocket|EventSource|sendBeacon/.test(bootJs) && !/https?:/.test(bootJs),
    'static: boot.js uses no dialogs or window.open; fetch only for own relative files');
}
const cssBlocks = [...html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)].map(m => m[1]).join('\n');
const cssUrls = [...cssBlocks.matchAll(/url\(\s*['"]?([^'")]+)/gi)].map(m => m[1]).filter(u => !/^(data:|#)/.test(u));
check(cssUrls.length === 0, 'static: CSS url() only data: URIs', cssUrls);
check(!/@import/i.test(cssBlocks), 'static: no CSS @import');
const appJsRaw = fs.readFileSync(path.join(ROOT, 'viewer', 'src', 'app.js'), 'utf8');
const appJs = appJsRaw.replace(/\/\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '').replace(/\s\/\/ .*$/gm, '');
check(!/\b(alert|confirm|prompt)\s*\(/.test(appJs) && !/window\.open\b/.test(appJs) && !/\bfetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon/.test(appJs),
  'static: app script uses no dialogs, window.open or network APIs');
const lsLines = appJs.split('\n').map((l, i, a) => ({ l, prev: (a.slice(Math.max(0, i - 2), i).join(' ')) })).filter(x => /localStorage|sessionStorage|indexedDB/.test(x.l));
check(lsLines.length > 0 && lsLines.every(x => /try\s*\{/.test(x.l) || /try\s*\{\s*$/.test(x.prev)), 'static: storage only inside try/catch', lsLines.length + ' uses');
if (!publishDir) check(/\/\*! diagram-js-minimap v\d+\.\d+\.\d+[\s\S]{0,200}The MIT License/.test(html) && /\.DiagramJSMinimap=/.test(html) && /\.djs-minimap\b/.test(cssBlocks),
  'static: diagram-js-minimap bundle, its CSS and MIT licence notice inlined', CIT.meta.viewer && CIT.meta.viewer.minimap);
else check(/\.djs-minimap\b/.test(cssBlocks) && /\.djs-container\b/.test(cssBlocks) && /\.bjs-container\b/.test(cssBlocks),
  'static: third-party CSS (diagram-js, bpmn-js, diagram-js-minimap) inline', CIT.meta.viewer && CIT.meta.viewer.minimap);
const visibleStatic = markup.replace(/<[^>]+>/g, ' ');
check(!/[—·]/.test(visibleStatic), 'static: no em dash or middle dot in the page markup');

// ---------------------------------------------------------------- browser
const browser = await chromium.launch({ executablePath: chromePath, headless: true, args: ['--no-sandbox'] });
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 1 });
try { await context.grantPermissions(['clipboard-read', 'clipboard-write']); } catch (e) { note('clipboard permissions not grantable: ' + e.message); }
const external = [];
const allRequests = [];
async function routeAll(ctx, extList, tamper) {
  await ctx.route('**/*', route => {
    const u = route.request().url();
    if (publishDir) {
      if (u.startsWith(origin + '/')) return route.continue();
      if (cdnMap.has(u)) {
        // jsDelivr stand-in: the pinned local file, with the CORS header the CDN sends (needed for crossorigin + SRI)
        let body = fs.readFileSync(cdnMap.get(u));
        if (tamper && tamper(u)) body = Buffer.concat([body, Buffer.from('\n/* tampered */\n')]);
        return route.fulfill({ status: 200, contentType: 'application/javascript; charset=utf-8', headers: { 'Access-Control-Allow-Origin': '*' }, body });
      }
    } else if (u.split('#')[0] === fileUrl) return route.continue();
    if (/^(data|blob):/.test(u)) return route.continue();
    extList.push(u);
    return route.abort();
  });
}
await routeAll(context, external);
const consoleErrors = [], pageErrors = [], dialogs = [], popups = [];
const ownPages = new Set();
const seenPages = [];
context.on('page', p => seenPages.push(p));
async function newPage() { const p = await context.newPage(); ownPages.add(p); return p; }
let page = await newPage();
function wire(p) {
  p.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  p.on('pageerror', e => pageErrors.push(String(e)));
  p.on('dialog', d => { dialogs.push(d.message()); d.dismiss().catch(() => {}); });
  p.on('request', r => allRequests.push(r.url()));
}
wire(page);

async function load(p, hash) {
  await p.goto(pageUrl + (hash ? '#' + hash : ''), { waitUntil: 'load' });
  await p.waitForFunction(() => document.documentElement.getAttribute('data-ready') === '1', null, { timeout: 20000 });
  await p.evaluate(() => window.ipdApp.idle());
}
// Screen point on an element for a real mouse click: the default view (75 %, left edge) does not show the whole
// diagram, so scroll the element into the canvas first and take a point whose topmost node belongs to the element
// (not the minimap, an overlay or the side panel). pref: 'center' or 'corner' (12 px inside the top-left corner).
async function clickPoint(p, id, pref) {
  return p.evaluate(({ id, pref }) => {
    const v = window.ipdApp.viewer, c = v.get('canvas'), reg = v.get('elementRegistry'), el = reg.get(id), gfx = reg.getGraphics(id);
    const cr = document.querySelector('#canvas').getBoundingClientRect();
    let g = gfx.getBoundingClientRect();
    if (g.left < cr.left + 10 || g.right > cr.right - 10 || g.top < cr.top + 10 || g.bottom > cr.bottom - 10) {
      c.scrollToElement(el, { top: 220, bottom: 120, left: 120, right: 120 });
      g = gfx.getBoundingClientRect();
    }
    const pts = [[g.left + g.width / 2, g.top + g.height / 2], [g.left + 12, g.top + 12], [g.left + 12, g.bottom - 12], [g.right - 12, g.top + 12]];
    if (pref === 'corner') pts.unshift(pts.splice(1, 1)[0]);
    for (const [x, y] of pts) {
      const n = document.elementFromPoint(x, y), own = n && n.closest('.djs-element');
      if (own && own.getAttribute('data-element-id') === id) return { x, y, ok: true };
    }
    return { x: pts[0][0], y: pts[0][1], ok: false, top: (document.elementFromPoint(pts[0][0], pts[0][1]) || {}).className };
  }, { id, pref });
}
async function openD(p, id) {
  await p.evaluate(id => window.ipdApp.open(id), id);
  await p.waitForFunction(id => document.documentElement.getAttribute('data-diagram') === id, id, { timeout: 10000 });
  await p.evaluate(() => window.ipdApp.idle());
  await p.waitForTimeout(50);
}

await load(page);
check(await page.evaluate(() => location.hash) === '#' + CIT.diagrams[0].hash, 'routing: first view sets the hash', await page.evaluate(() => location.hash));
check(await page.evaluate(() => document.documentElement.getAttribute('data-diagram')) === CIT.diagrams.find(d => d.level === 'L3').id, 'routing: L3 opens first');
const importWarnings = await page.evaluate(() => window.ipdImportWarnings);
check(importWarnings.length === 0, 'import: zero bpmn-js import warnings', importWarnings);
const hdr = await page.evaluate(() => ({ t: document.querySelector('#page-title').textContent, s: document.querySelector('#page-status').textContent }));
check(hdr.t === 'Important protocol deviation (iPD) management - best-practice reference model (BPMN 2.0)', 'header: title text');
check(hdr.s === 'Outside-in reference model derived from ICH, EU and US sources - not validated by process owners', 'header: status line');

const perDiagram = [];
for (const d of CIT.diagrams) {
  await openD(page, d.id);
  const hash = await page.evaluate(() => location.hash);
  check(hash === '#' + d.hash, `routing: ${d.id} shows #${d.hash} in location.hash`, hash);
  // (5) default view: Fit when the fit zoom is legible, else 75 % at the left edge, centred on the Sponsor pool
  const view = await page.evaluate(() => {
    const v = window.ipdApp.viewer, c = v.get('canvas'), reg = v.get('elementRegistry');
    const vb = c.viewbox();
    const box = e => ({ id: e.id, name: (e.businessObject && e.businessObject.name) || '', x: e.x, y: e.y, width: e.width, height: e.height });
    const mm = window.ipdApp.minimap, mmEl = document.querySelector('#canvas .djs-minimap'), btn = document.querySelector('#mm-toggle');
    return { edge: window.ipdApp.constants.EDGE, vb: { x: vb.x, y: vb.y, width: vb.width, height: vb.height }, inner: vb.inner, outer: vb.outer,
      zoom: c.zoom(), state: window.ipdApp.state.view, readout: document.querySelector('#z-level').textContent,
      pools: reg.filter(e => e.type === 'bpmn:Participant' && e.businessObject.processRef).map(box),
      starts: reg.filter(e => e.type === 'bpmn:StartEvent').map(e => Object.assign(box(e), { label: e.label ? box(e.label) : null,
        next: (e.outgoing || []).filter(c => c.type === 'bpmn:SequenceFlow' && c.target).map(c => Object.assign(box(c.target), { label: c.target.label ? box(c.target.label) : null })) })),
      mm: { module: !!mm, dom: !!mmEl, open: !!(mm && mm.isOpen()), cls: !!(mmEl && mmEl.classList.contains('open')),
        visible: !!(mmEl && mmEl.offsetWidth > 0 && mmEl.offsetHeight > 0), items: mmEl ? mmEl.querySelectorAll('.map svg [id^="djs-minimap-"]').length : 0,
        pressed: btn.getAttribute('aria-pressed'), text: btn.textContent, rect: mmEl ? (r => ({ w: r.width, h: r.height }))(mmEl.getBoundingClientRect()) : null } };
  });
  {
    const fit = Math.min(1, view.outer.width / view.inner.width, view.outer.height / view.inner.height);
    const pct = z => Math.round(z * 100) + '%';
    const vp = [];
    let desc;
    if (fit < LEGIBLE) {
      const w = view.outer.width / READABLE_ZOOM, h = view.outer.height / READABLE_ZOOM, E = view.edge;
      const inside = (p, e) => { const cx = e.x + e.width / 2, cy = e.y + e.height / 2; return cx >= p.x && cx <= p.x + p.width && cy >= p.y && cy <= p.y + p.height; };
      const sponsor = view.pools.filter(p => /(^|[^a-z])sponsor([^a-z]|$)/i.test(p.name)).sort((a, b) => b.width * b.height - a.width * a.height)[0];
      // process start: leftmost start event; at equal x the one in the Sponsor pool
      const byX = (a, b) => a.x - b.x || a.y - b.y;
      let start = view.starts.slice().sort(byX)[0];
      const sStart = sponsor ? view.starts.filter(st => inside(sponsor, st)).sort(byX)[0] : null;
      if (start && sStart && Math.abs(sStart.x - start.x) < 1) start = sStart;
      if (Math.abs(view.zoom - READABLE_ZOOM) > 0.005) vp.push(`zoom ${view.zoom} != ${READABLE_ZOOM}`);
      const expX = start && start.x + start.width + E > view.inner.x - E + w ? start.x - 3 * E : view.inner.x - E;
      if (Math.abs(view.vb.x - expX) > 1) vp.push(`left edge x ${view.vb.x.toFixed(1)} != ${expX.toFixed(1)}`);
      let span = null;
      if (start) {
        // start event and its direct successors, each with label and source box
        span = { top: Infinity, bottom: -Infinity };
        [start].concat(start.next).forEach(e => {
          const z = EL[e.id] && EL[e.id].zone, l = e.label;
          span.top = Math.min(span.top, e.y, l ? l.y : Infinity, z ? z[1] : Infinity);
          span.bottom = Math.max(span.bottom, e.y + e.height, l ? l.y + l.height : -Infinity, z ? z[1] + z[3] : -Infinity);
        });
        if (start.x < view.vb.x || start.x + start.width > view.vb.x + view.vb.width || span.top < view.vb.y - 0.5 || span.bottom > view.vb.y + view.vb.height + 0.5)
          vp.push(`process start ${start.id} and its first step (with labels and source boxes) not in view`);
      }
      let centred = '';
      if (sponsor) {
        const target = sponsor.y + sponsor.height / 2 - h / 2, top = view.inner.y - E, bottom = view.inner.y + view.inner.height + E - h;
        let y = target, why = [];
        if (span && span.top < y + E) { y = span.top - E; why.push('keep the process start in view'); }
        if (span && span.bottom > y + h - E) { y = span.bottom + E - h; why.push('keep the process start in view'); }
        const expY = Math.max(Math.min(top, bottom), Math.min(Math.max(top, bottom), y));
        if (Math.abs(expY - y) >= 0.5) why.push('avoid an empty band');
        if (Math.abs(view.vb.y - expY) > 1) vp.push(`y ${view.vb.y.toFixed(1)} != ${expY.toFixed(1)} (Sponsor centre, process start kept, clamped to the diagram)`);
        const need = Math.max(sponsor.y + sponsor.height, span ? span.bottom : -Infinity) - Math.min(sponsor.y, span ? span.top : Infinity);
        if (need <= h - 2 * E && (sponsor.y < view.vb.y - 0.5 || sponsor.y + sponsor.height > view.vb.y + view.vb.height + 0.5)) vp.push(`Sponsor pool ${sponsor.id} not fully in view`);
        centred = Math.abs(expY - target) < 0.5 ? 'exactly centred on' : `centred on (shifted ${Math.round(Math.abs(expY - target) * READABLE_ZOOM)} px to ${[...new Set(why)].join(' and ')})`;
        if (view.state.pool !== sponsor.id) vp.push(`page anchored on ${view.state.pool}, expected ${sponsor.id}`);
      } else {
        note(`${d.id}: no expanded pool named Sponsor; vertical anchor falls back to the pool of the first start event`);
      }
      if (view.state.mode !== 'readable') vp.push('state.view.mode ' + view.state.mode);
      desc = `${pct(view.zoom)} (Fit ${pct(fit)} < ${pct(LEGIBLE)}), left edge, process start ${start ? start.id : '-'} in view, ${centred || 'no'} Sponsor pool`;
    } else {
      if (Math.abs(view.zoom - fit) > 0.005) vp.push(`zoom ${view.zoom} != fit ${fit}`);
      if (view.state.mode !== 'fit') vp.push('state.view.mode ' + view.state.mode);
      desc = `Fit ${pct(fit)} (legible)`;
    }
    if (!view.readout.startsWith('Zoom ' + pct(view.zoom))) vp.push('readout ' + view.readout);
    check(vp.length === 0, `view: ${d.id} opens at ${desc}`, vp);
    check(view.zoom >= LEGIBLE - 0.005, `view: ${d.id} default zoom ${pct(view.zoom)} >= ${pct(LEGIBLE)}`);
    // minimap: present on every diagram and closed by default, so it hides nothing in the default view
    const wide = view.inner.width * view.zoom > view.outer.width + 1, m = view.mm;
    check(m.module && m.dom && !m.open && !m.cls && !m.visible && m.pressed === 'false' && m.text === 'Show minimap',
      `minimap: ${d.id} present, closed by default (diagram ${wide ? 'wider' : 'not wider'} than the canvas at ${pct(view.zoom)})`, m);
  }
  // (6) MAY chip next to the binding badge on elements whose REQs are all modal "may"
  {
    const mayDom = await page.evaluate(() => Array.from(document.querySelectorAll('.ipd-ov[data-ipd-el]')).filter(n => n.querySelector('.ipd-may')).map(n => {
      const c = n.querySelector('.ipd-may'), prev = c.previousElementSibling;
      return { id: n.getAttribute('data-ipd-el'), text: c.textContent, inRow: !!c.closest('.row'), prev: prev ? prev.textContent : null, prevIsBadge: !!(prev && prev.classList.contains('b')) };
    }));
    const exp = d.overlay_elements.filter(id => mayOnly(EL[id])).sort();
    const got = mayDom.map(x => x.id).sort();
    const mp = [];
    if (JSON.stringify(got) !== JSON.stringify(exp)) mp.push({ got, exp });
    mayDom.forEach(x => {
      const bb = BINDING_BADGE[EL[x.id].binding];
      if (x.text !== 'MAY' || !x.inRow) mp.push(`${x.id}: chip "${x.text}" outside the badge row`);
      if (bb ? !(x.prevIsBadge && x.prev === bb) : x.prev !== null) mp.push(`${x.id}: chip not right after the binding badge ${bb || '(none)'} (after ${x.prev})`);
    });
    d.elements.forEach(id => { if (!!EL[id].may_only !== mayOnly(EL[id])) mp.push(`${id}: may_only flag ${EL[id].may_only} vs REQ modals`); });
    if (!CIT.meta.modal_loaded && exp.length) mp.push('MAY chips without modal data');
    check(mp.length === 0, `may: ${d.id} MAY chip on ${exp.length} element(s) whose REQs are all modal "may", next to the binding badge${CIT.meta.modal_loaded ? '' : ' (no modal field in the requirements: none)'}`, mp);
  }
  const info = await page.evaluate(({ d, EL }) => {
    const v = window.ipdApp.viewer, reg = v.get('elementRegistry'), ov = v.get('overlays'), canvas = v.get('canvas');
    const missing = d.elements.filter(id => !reg.get(id));
    const svgEls = document.querySelectorAll('#canvas .djs-element').length;
    const srcOnly = ov.get({ type: 'ipd-src' });
    const src = srcOnly.concat(ov.get({ type: 'ipd-ifc' }));   // geometry covers interface chips without sources too
    const srcIds = srcOnly.map(o => o.element.id).sort();
    const chips = ov.get({ type: 'ipd-open' }).map(o => o.element.id).sort();
    // independent count from the imported model: elements with ipd:trace sources (lanes / pools excluded: panel only)
    const fromModel = reg.filter(e => {
      if (e.type === 'label' || e.type === 'bpmn:Lane' || e.type === 'bpmn:Participant') return false;
      const bo = e.businessObject, ext = bo && bo.extensionElements;
      const tr = ext && (ext.values || []).find(x => x.$type === 'ipd:Trace');
      return tr && (tr.sources || []).length > 0;
    }).map(e => e.id).sort();
    const laneTraces = reg.filter(e => (e.type === 'bpmn:Lane' || e.type === 'bpmn:Participant')).filter(e => {
      const ext = e.businessObject.extensionElements; const tr = ext && (ext.values || []).find(x => x.$type === 'ipd:Trace');
      return tr && (tr.sources || []).length > 0;
    }).map(e => e.id).sort();
    // geometry
    const vb = canvas.viewbox(), crect = document.querySelector('#canvas').getBoundingClientRect();
    const geo = [];
    const zones = {};
    d.elements.forEach(id => { if (EL[id].zone) zones[id] = EL[id].zone; });
    const shapes = reg.filter(e => e.type !== 'label' && !e.waypoints && e.parent && !/^bpmn:(Participant|Lane|Group)$/.test(e.type));
    const labels = reg.filter(e => e.type === 'label');
    const conns = reg.filter(e => !!e.waypoints);
    function hit(a, b) { return a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height; }
    function segHit(p, q, r) {
      // axis-aligned or general segment vs rectangle interior (shrunk by 0.5 px)
      const x0 = r.x + .5, y0 = r.y + .5, x1 = r.x + r.width - .5, y1 = r.y + r.height - .5;
      const steps = 40;
      for (let i = 0; i <= steps; i++) { const x = p.x + (q.x - p.x) * i / steps, y = p.y + (q.y - p.y) * i / steps; if (x > x0 && x < x1 && y > y0 && y < y1) return true; }
      return false;
    }
    src.forEach(o => {
      const id = o.element.id, z = zones[id];
      const wrap = o.html, box = wrap.querySelector('.ipd-ov') || wrap;
      const r = wrap.getBoundingClientRect();
      const zr = z ? { x: z[0], y: z[1], width: z[2], height: z[3] } : null;
      const g = { id, zone: z, w: box.offsetWidth, h: box.offsetHeight, clipped: box.scrollHeight > box.clientHeight + 1 || box.scrollWidth > box.clientWidth + 1,
        truncated: Array.from(box.querySelectorAll('.src')).filter(n => n.scrollWidth > n.clientWidth + 1).map(n => n.textContent), problems: [] };
      if (!zr) { g.problems.push('no zone'); geo.push(g); return; }
      if (g.w > z[2] + 0.5 || g.h > z[3] + 0.5) g.problems.push(`box ${g.w}x${g.h} exceeds zone ${z[2]}x${z[3]}`);
      if (g.clipped) g.problems.push('content clipped');
      const ex = crect.left + (z[0] - vb.x) * vb.scale, ey = crect.top + (z[1] - vb.y) * vb.scale;
      if (Math.abs(r.left - ex) > 1.5 || Math.abs(r.top - ey) > 1.5) g.problems.push(`screen offset ${Math.round(r.left - ex)},${Math.round(r.top - ey)}`);
      const owner = reg.get(id);
      // the drawn box (not the reserved zone) must stay clear of other things
      const drawn = { x: z[0] + box.offsetLeft, y: z[1] + box.offsetTop, width: g.w, height: g.h };
      if (box.offsetLeft < -0.5 || box.offsetLeft + g.w > z[2] + 0.5) g.problems.push('box leaves the zone horizontally');
      shapes.forEach(s => { if (s.id !== id && hit(drawn, s)) g.problems.push('covers shape ' + s.id); });
      labels.forEach(l => { if (l.labelTarget !== owner && hit(drawn, l)) g.problems.push('covers label of ' + (l.labelTarget && l.labelTarget.id)); });
      conns.forEach(c => {
        if (c.id === id) return;
        for (let i = 0; i + 1 < c.waypoints.length; i++) if (segHit(c.waypoints[i], c.waypoints[i + 1], drawn)) { g.problems.push('crossed by edge ' + c.id); break; }
      });
      src.forEach(o2 => {
        if (o2.element.id === id) return; const z2 = zones[o2.element.id]; if (!z2) return;
        const b2 = o2.html.querySelector('.ipd-ov') || o2.html;
        if (hit(drawn, { x: z2[0] + b2.offsetLeft, y: z2[1] + b2.offsetTop, width: b2.offsetWidth, height: b2.offsetHeight })) g.problems.push('overlaps overlay of ' + o2.element.id);
      });
      geo.push(g);
    });
    // chips: on the call activity (a tab on its bottom border at most), clear of its label text and markers,
    // and clear of other shapes, labels, edges and source boxes
    const chipGeo = ov.get({ type: 'ipd-open' }).map(o => {
      const el = o.element, b = o.html, pos = o.position;
      const r = { x: pos.left, y: pos.top, width: b.offsetWidth, height: b.offsetHeight };
      const abs = { x: el.x + r.x, y: el.y + r.y, width: r.width, height: r.height };
      const problems = [];
      if (r.x < 0 || r.y < 0 || r.x + r.width > el.width || r.y + r.height > el.height + 6) problems.push('outside its shape and border tab area');
      const vis = reg.getGraphics(el).querySelector('.djs-visual');
      Array.from(vis.children).forEach((c, i) => { if (i === 0) return; const bb = c.getBBox(); if (bb.width && bb.height && hit(r, bb)) problems.push('covers ' + c.tagName); });
      shapes.forEach(s => { if (s.id !== el.id && hit(abs, s)) problems.push('covers shape ' + s.id); });
      labels.forEach(l => { if (l.labelTarget !== el && hit(abs, l)) problems.push('covers label of ' + (l.labelTarget && l.labelTarget.id)); });
      conns.forEach(c => { for (let i = 0; i + 1 < c.waypoints.length; i++) if (segHit(c.waypoints[i], c.waypoints[i + 1], abs)) { problems.push('crossed by edge ' + c.id); break; } });
      src.forEach(o2 => { const z2 = zones[o2.element.id], b2 = o2.html.querySelector('.ipd-ov') || o2.html; if (z2 && hit(abs, { x: z2[0] + b2.offsetLeft, y: z2[1] + b2.offsetTop, width: b2.offsetWidth, height: b2.offsetHeight })) problems.push('overlaps source box of ' + o2.element.id); });
      return { id: el.id, problems };
    });
    // DRAFT badges, interface placeholders, text annotations, trace record/party (from the imported model)
    const traceOf = e => { const ext = e.businessObject && e.businessObject.extensionElements; return ext && (ext.values || []).find(x => x.$type === 'ipd:Trace'); };
    const badgeRows = srcOnly.map(o => ({ id: o.element.id, badges: Array.from(o.html.querySelectorAll('.ipd-ov .row .b')).map(b => b.textContent) }));
    const traceModel = {};
    reg.forEach(e => { const t = traceOf(e); if (t && e.type !== 'label') traceModel[e.id] = { draft: t.draft === true || t.draft === 'true', binding: t.binding || '', record: t.record || '', party: t.party || '' }; });
    const callActs = reg.filter(e => e.type === 'bpmn:CallActivity').map(e => {
      const n = Array.from(document.querySelectorAll('.ipd-ov')).find(x => x.getAttribute('data-ipd-el') === e.id);
      return { id: e.id, noCalled: !e.businessObject.calledElement, chip: n && n.querySelector('.ipd-ifc') ? n.querySelector('.ipd-ifc').textContent : '',
        open: ov.get({ element: e.id, type: 'ipd-open' }).length };
    });
    const annotations = reg.filter(e => e.type === 'bpmn:TextAnnotation').map(e => {
      const t = traceOf(e);
      const covered = src.filter(o => o.element.id !== e.id).filter(o => {
        const z = zones[o.element.id]; if (!z) return false; const b = o.html.querySelector('.ipd-ov') || o.html;
        return hit({ x: z[0] + b.offsetLeft, y: z[1] + b.offsetTop, width: b.offsetWidth, height: b.offsetHeight }, e);
      }).map(o => o.element.id);
      return { id: e.id, hasSrc: !!(t && (t.sources || []).length), overlays: ov.get({ element: e.id, type: 'ipd-src' }).length, covered };
    });
    const associations = reg.filter(e => e.type === 'bpmn:Association').length;
    return { missing, svgEls, srcIds, chips, fromModel, laneTraces, geo, chipGeo, chipsSkipped: window.ipdApp.state.chipsSkipped.slice(),
      badgeRows, traceModel, callActs, annotations, associations };
  }, { d, EL });
  check(info.missing.length === 0 && info.svgEls > 0, `render: ${d.id} renders all ${d.elements.length} trace records (${info.svgEls} SVG elements)`, info.missing);
  const expected = d.overlay_elements.slice().sort();
  const withSrc = d.elements.filter(id => EL[id].sources.length && EL[id].overlay).sort();
  check(JSON.stringify(info.srcIds) === JSON.stringify(expected) && expected.length === withSrc.length,
    `overlays: ${d.id} overlay count ${info.srcIds.length} = elements with sources ${expected.length} (citations.json)`, { got: info.srcIds, expected });
  check(JSON.stringify(info.fromModel) === JSON.stringify(expected),
    `overlays: ${d.id} overlay set = elements with ipd:source in the imported model (${info.fromModel.length})`, { model: info.fromModel });
  const panelOnly = d.panel_only_elements.slice().sort();
  check(JSON.stringify(info.laneTraces) === JSON.stringify(panelOnly), `overlays: ${d.id} lanes/pools with sources are panel-only (${panelOnly.length})`, info.laneTraces);
  const geoProblems = info.geo.filter(g => g.problems.length);
  check(geoProblems.length === 0, `overlays: ${d.id} all ${info.geo.length} boxes inside their zones, unclipped, clear of shapes, labels, edges and other overlays`, geoProblems.map(g => ({ id: g.id, p: g.problems })));
  const trunc = info.geo.filter(g => g.truncated.length);
  if (trunc.length) note(`${d.id}: ${trunc.length} overlay line(s) shortened with an ellipsis (full text in tooltip and panel): ` + trunc.map(g => g.id + ' ' + g.truncated.join(' / ')).join('; '));
  // (1) DRAFT next to the binding badge whenever the element's trace or one of its REQs is draft
  const draftProblems = [];
  let draftCases = 0;
  info.badgeRows.forEach(r => {
    const rec = EL[r.id], tm = info.traceModel[r.id] || { draft: false, binding: '' };
    const wantDraft = tm.draft || rec.reqs.some(q => q.draft);
    const bindingBadge = { 'binding-law': 'LAW', 'binding-ICH': 'ICH', 'guidance': 'GUIDANCE', 'best-practice': 'BP', 'verify-binding': 'VERIFY' }[tm.binding];
    if (wantDraft) draftCases++;
    if (JSON.stringify(r.badges) !== JSON.stringify(rec.badges)) draftProblems.push(`${r.id}: DOM ${r.badges} vs citations ${rec.badges}`);
    if (wantDraft !== r.badges.includes('DRAFT')) draftProblems.push(`${r.id}: DRAFT expected ${wantDraft}`);
    if (bindingBadge && !r.badges.includes(bindingBadge)) draftProblems.push(`${r.id}: binding badge ${bindingBadge} missing`);
  });
  check(draftProblems.length === 0, `badges: ${d.id} DRAFT shown with the binding badge on all ${draftCases} draft element(s); badges match citations (${info.badgeRows.length})`, draftProblems);
  // (2) interface placeholders: no calledElement (or ipd marker) -> interface chip, no "Open L4"
  const ifcProblems = [];
  info.callActs.forEach(c => {
    const rec = EL[c.id], isIfc = !!(rec && rec.calls && rec.calls.interface);
    if (c.noCalled && !isIfc) ifcProblems.push(`${c.id}: no calledElement but not flagged as interface`);
    if (isIfc && (c.chip !== 'Interface - outside this model' || c.open !== 0)) ifcProblems.push(`${c.id}: chip "${c.chip}", open chips ${c.open}`);
    if (!isIfc && c.chip) ifcProblems.push(`${c.id}: interface chip on a drill-down call activity`);
  });
  const nIfc = info.callActs.filter(c => EL[c.id] && EL[c.id].calls && EL[c.id].calls.interface).length;
  check(ifcProblems.length === 0, `interface: ${d.id} ${nIfc} interface placeholder(s) show "Interface - outside this model" and no "Open L4" chip`, ifcProblems);
  // (3) text annotations: rendered, never covered by an overlay, overlay only when they carry sources
  const annProblems = info.annotations.filter(a => a.covered.length || a.overlays !== (a.hasSrc ? 1 : 0)).map(a => ({ id: a.id, covered: a.covered, overlays: a.overlays, hasSrc: a.hasSrc }));
  check(annProblems.length === 0, `annotations: ${d.id} ${info.annotations.length} text annotation(s) (${info.associations} association(s)) not covered; overlay only with sources (${info.annotations.filter(a => a.hasSrc).length})`, annProblems);
  // (4) record / party from ipd:trace attributes (S0-17) take precedence
  const rpProblems = Object.entries(info.traceModel).filter(([id, t]) => EL[id] && ((t.record && EL[id].record !== t.record) || (t.party && EL[id].party !== t.party))).map(([id]) => id);
  check(rpProblems.length === 0, `trace: ${d.id} record/party attributes used where present (${Object.values(info.traceModel).filter(t => t.record || t.party).length})`, rpProblems);

  const expChips = d.call_targets.filter(c => c.available && !c.interface).map(c => c.element_id).sort();
  check(JSON.stringify(info.chips) === JSON.stringify(expChips) && info.chipsSkipped.length === 0,
    `chips: ${d.id} "Open L4" chip on every call activity with an L4 (${expChips.length})`, { got: info.chips, skipped: info.chipsSkipped });
  const chipProblems = info.chipGeo.filter(c => c.problems.length);
  check(chipProblems.length === 0, `chips: ${d.id} chips inside the shape, clear of label and markers`, chipProblems);
  const unavailable = d.call_targets.filter(c => !c.available && !c.interface).map(c => c.model);
  if (unavailable.length) note(`${d.id}: call activities without an L4 diagram in this file: ${unavailable.join(', ')}`);

  // screenshots: fit view, and a 1:1 detail view of the first overlay
  await page.screenshot({ path: path.join(screens, `${d.id}.png`) });
  if (d.overlay_elements.length) {
    const first = d.overlay_elements.find(id => EL[id].type !== 'bpmn:MessageFlow') || d.overlay_elements[0];
    await page.evaluate(id => {
      const v = window.ipdApp.viewer, c = v.get('canvas'), el = v.get('elementRegistry').get(id);
      const z = window.ipdApp.data.elements[id].zone;
      const box = c.viewbox();
      c.zoom(1);
      const vb = c.viewbox();
      const cx = z ? z[0] + z[2] / 2 : el.x, cy = z ? z[1] : el.y;
      c.viewbox({ x: cx - vb.outer.width / 2, y: cy - vb.outer.height / 2, width: vb.outer.width, height: vb.outer.height });
    }, first);
    await page.waitForTimeout(50);
    await page.screenshot({ path: path.join(screens, `${d.id}_detail.png`) });
    await page.evaluate(() => window.ipdApp.viewer.get('canvas').zoom('fit-viewport', 'auto'));
  }
  perDiagram.push({ diagram: d.id, overlays: info.srcIds.length, expected: expected.length, panel_only: panelOnly.length, chips: info.chips.length });
}

// ---------------------------------------------------------------- minimap: toggle, sticky choice, navigation
{
  const mmState = p => p.evaluate(() => {
    const m = window.ipdApp.minimap, el = document.querySelector('#canvas .djs-minimap'), b = document.querySelector('#mm-toggle');
    return { open: !!(m && m.isOpen()), cls: !!(el && el.classList.contains('open')), visible: !!(el && el.offsetWidth > 0), pressed: b.getAttribute('aria-pressed'),
      text: b.textContent, items: el ? el.querySelectorAll('.map svg [id^="djs-minimap-"]').length : 0, attr: document.documentElement.getAttribute('data-minimap') };
  });
  const consistent = (s, open) => s.open === open && s.cls === open && s.visible === open && s.pressed === String(open) &&
    s.text === (open ? 'Hide minimap' : 'Show minimap') && s.attr === (open ? 'open' : 'closed') && (!open || s.items > 0);
  // a diagram wider than the canvas at its opening zoom (for the navigation check), else the first one
  let md = CIT.diagrams[0].id;
  for (const d of CIT.diagrams) {
    await openD(page, d.id);
    if (await page.evaluate(() => { const vb = window.ipdApp.viewer.get('canvas').viewbox(); return vb.inner.width * vb.scale > vb.outer.width + 1; })) { md = d.id; break; }
  }
  await openD(page, md);
  const s0 = await mmState(page);
  await page.click('#mm-toggle');
  const s1 = await mmState(page);
  await page.click('#mm-toggle');
  const s2 = await mmState(page);
  check(consistent(s0, false) && consistent(s1, true) && consistent(s2, false), `minimap: navigation-bar button toggles it on ${md} (closed -> open -> closed; text, aria-pressed, map)`, { s0, s1, s2 });
  // the user's choice holds across diagrams: open it, open another diagram and come back
  await page.click('#mm-toggle');
  const other = CIT.diagrams.find(d => d.id !== md);
  if (other) await openD(page, other.id);
  const so = await mmState(page);
  await openD(page, md);
  const sb = await mmState(page);
  check(consistent(so, true) && consistent(sb, true), `minimap: an opened minimap stays open on ${other ? other.id + ' and ' : ''}${md} after the user opened it`, { so, sb });
  // click in the map moves the view (map centre point -> canvas centre)
  const nav = await page.evaluate(() => {
    const svg = document.querySelector('#canvas .djs-minimap .map svg'), r = svg.getBoundingClientRect();
    return { x: r.right - 12, y: r.top + r.height / 2, before: window.ipdApp.viewer.get('canvas').viewbox().x };
  });
  await page.mouse.click(nav.x, nav.y);
  await page.waitForTimeout(80);
  const after = await page.evaluate(() => window.ipdApp.viewer.get('canvas').viewbox().x);
  check(after > nav.before + 50, `minimap: click near the right end of the map pans the canvas to the right (viewbox x ${Math.round(nav.before)} -> ${Math.round(after)})`);
  await page.screenshot({ path: path.join(screens, `${md}_minimap.png`) });
  // ... and a closed one stays closed: close it, open another diagram and come back
  await page.click('#mm-toggle');
  if (other) { await openD(page, other.id); }
  const s3 = await mmState(page);
  await openD(page, md);
  const s4 = await mmState(page);
  check(consistent(s3, false) && consistent(s4, false), `minimap: a closed minimap stays closed on ${other ? other.id + ' and ' : ''}${md} after the user closed it`, { s3, s4 });
  // later checks click on canvas elements: the minimap stays closed for them
}

// ---------------------------------------------------------------- MAY chip and REQ modal in the panel
{
  const may = Object.values(EL).filter(r => mayOnly(r));
  expectMay.forEach(id => check(EL[id] && mayOnly(EL[id]) && EL[id].overlay, `may: expected may-only element ${id} has all REQs modal "may" and a source box`, EL[id] ? EL[id].reqs.map(q => q.id + ':' + q.modal) : 'not in citations'));
  const mpanel = async id => {
    const rec = EL[id];
    await openD(page, rec.diagram);
    await page.evaluate(id => window.ipdApp.select(id), id);
    await page.waitForTimeout(60);
    return page.evaluate(() => ({ text: document.querySelector('#panel-body').innerText, chip: !!document.querySelector('#panel-body .badges .ipd-may'),
      canvasChip: Array.from(document.querySelectorAll('.ipd-ov[data-ipd-el]')).some(n => n.getAttribute('data-ipd-el') === window.ipdApp.state.selected && n.querySelector('.ipd-may')) }));
  };
  const modalLines = (rec, t) => rec.reqs.filter(q => q.found).every(q => t.includes('Modal: ' + (q.modal || 'not stated in requirements.yaml')));
  if (may.length) {
    const m = EL[expectMay[0]] || may.find(r => r.overlay) || may[0];
    const t = await mpanel(m.id);
    check(t.chip && (!m.overlay || t.canvasChip) && modalLines(m, t.text) && t.text.includes('every linked requirement is optional (MAY)'),
      `may: ${m.id} shows the MAY chip on the canvas and in the panel, and "Modal: may" for each of its ${m.reqs.length} REQ(s)`);
    await page.screenshot({ path: path.join(screens, `${m.diagram}_may.png`) });
  } else if (CIT.meta.modal_loaded) {
    note('modal data loaded, but no element has only modal "may" REQs');
  }
  if (CIT.meta.modal_loaded) {
    const mixed = Object.values(EL).find(r => r.overlay && r.reqs.some(q => q.modal === 'may') && !mayOnly(r));
    const absent = Object.values(EL).find(r => r.overlay && r.reqs.some(q => q.found && !q.modal));
    for (const r of [mixed, absent].filter(Boolean)) {
      const t = await mpanel(r.id);
      check(!t.chip && !t.canvasChip && modalLines(r, t.text), `may: ${r.id} (REQ modals ${r.reqs.map(q => q.id + ' ' + (q.modal || 'absent')).join(', ')}) shows each modal in the panel and no MAY chip`);
    }
    if (!mixed) note('no element mixes "may" with other modals');
    if (!absent) note('every REQ has a modal');
  } else {
    const r = Object.values(EL).filter(x => x.reqs.length).sort((a, b) => b.reqs.length - a.reqs.length)[0];
    if (r) {
      const t = await mpanel(r.id);
      check(!t.chip && !t.canvasChip && !t.text.includes('Modal:') && !await page.evaluate(() => !!document.querySelector('.ipd-may')),
        `may: without a modal field in the requirements the page shows no MAY chip and no modal line (${r.id}, ${r.reqs.length} REQ)`);
    }
  }
}

// ---------------------------------------------------------------- click a task -> panel
const taskDiagram = CIT.diagrams.find(d => d.level === 'L4' && d.overlay_elements.some(id => EL[id].type === 'bpmn:Task')) ||
  CIT.diagrams.find(d => d.overlay_elements.some(id => EL[id].type === 'bpmn:Task'));
if (taskDiagram) {
  await openD(page, taskDiagram.id);
  const tasks = taskDiagram.overlay_elements.filter(id => EL[id].type === 'bpmn:Task');
  const taskId = tasks.slice().sort((a, b) => EL[b].sources.length - EL[a].sources.length)[0];
  const rec = EL[taskId];
  const box = await clickPoint(page, taskId, 'center');
  if (!box.ok) note(`click point on ${taskId} is covered: ${JSON.stringify(box)}`);
  await page.mouse.click(box.x, box.y);
  await page.waitForTimeout(100);
  const panel = await page.evaluate(() => ({ h2: (document.querySelector('#panel-body h2') || {}).textContent || '', text: document.querySelector('#panel-body').innerText, sel: window.ipdApp.state.selected }));
  const missingSrc = rec.sources.filter(s => !panel.text.includes(s.key) || !panel.text.includes(s.loc) || (s.title && !panel.text.includes(s.title)) || (s.page && !panel.text.includes(s.page)));
  check(panel.sel === taskId && panel.h2 === rec.label, `panel: click on task ${taskId} opens its panel`, panel.h2);
  check(missingSrc.length === 0 && panel.text.includes(`Sources (${rec.sources.length})`), `panel: shows all ${rec.sources.length} sources of ${taskId} (key, loc, page, document title)`, missingSrc);
  const reqOk = rec.reqs.every(r => panel.text.includes(r.id));
  check(reqOk, `panel: shows the REQ ids of ${taskId}`, rec.reqs.map(r => r.id));
  check(panel.text.includes('Binding') && panel.text.includes(rec.binding || 'not set'), `panel: shows binding of ${taskId}`);
  if (rec.verify.length) {
    const vcount = await page.evaluate(() => Array.from(document.querySelectorAll('#panel-body .verify')).filter(n => n.textContent.startsWith('VERIFY')).length);
    check(vcount >= rec.verify.length, `panel: open verify items highlighted with the text VERIFY (${vcount})`);
  }
  await page.screenshot({ path: path.join(screens, `${taskDiagram.id}_panel.png`) });
  // a task with a verify item, if any (VERIFY highlight), screenshot
  const vt = taskDiagram.overlay_elements.find(id => EL[id].verify.length && id !== taskId);
  if (vt) {
    await page.evaluate(id => window.ipdApp.select(id), vt);
    await page.waitForTimeout(80);
    const vcount = await page.evaluate(() => Array.from(document.querySelectorAll('#panel-body .verify')).filter(n => n.textContent.startsWith('VERIFY')).length);
    check(vcount >= EL[vt].verify.length, `panel: ${vt} verify items shown with the text VERIFY (${vcount})`);
    await page.screenshot({ path: path.join(screens, `${taskDiagram.id}_panel_verify.png`) });
  }
  // selecting a step from the default view zooms to 100 %
  const zAfter = await page.evaluate(() => window.ipdApp.viewer.get('canvas').zoom());
  check(Math.abs(zAfter - 1) < 0.01, `zoom: selecting a step from the default view zooms to 100% (${zAfter.toFixed(2)})`);
  // click on the source overlay box selects the element too (from the fit view)
  await page.click('#z-fit');
  const ovId = taskDiagram.overlay_elements.find(id => id !== taskId) || taskId;
  const ovBox = await page.evaluate(id => {
    const n = Array.from(document.querySelectorAll('.ipd-ov')).find(x => x.getAttribute('data-ipd-el') === id).getBoundingClientRect();
    return { x: n.left + Math.min(20, n.width / 2), y: n.top + Math.min(8, n.height / 2), w: n.width };
  }, ovId);
  await page.mouse.click(ovBox.x, ovBox.y);
  await page.waitForTimeout(80);
  check(await page.evaluate(() => window.ipdApp.state.selected) === ovId, `panel: click on the source box of ${ovId} selects it`);
  const zFit = await page.evaluate(() => window.ipdApp.viewer.get('canvas').zoom());
  check(Math.abs(zFit - 1) < 0.01, `zoom: selecting a step from the Fit view zooms to 100% (${zFit.toFixed(2)})`);
  // empty-canvas click -> list
  await page.evaluate(() => window.ipdApp.select(null));
  const list = await page.evaluate(() => document.querySelector('#panel-body').textContent);  // includes collapsed REQs
  const reqIds = [...new Set(taskDiagram.elements.flatMap(id => EL[id].filterable ? EL[id].reqs.map(r => r.id) : []))];
  check(reqIds.every(r => list.includes(r)) && list.includes('Requirements on this diagram'), `panel: no selection lists all ${reqIds.length} REQ ids of ${taskDiagram.id} grouped by element`);
} else {
  check(false, 'panel: no task with sources found to click');
}

// ---------------------------------------------------------------- drill-down, back, breadcrumb
const l3 = CIT.diagrams.find(d => d.level === 'L3');
const ct = l3 && l3.call_targets.find(c => c.available && !c.interface);
if (ct) {
  await openD(page, l3.id);
  const c = await clickPoint(page, ct.element_id, 'corner');
  if (!c.ok) note(`click point on ${ct.element_id} is covered: ${JSON.stringify(c)}`);
  await page.mouse.click(c.x, c.y);
  await page.waitForFunction(id => document.documentElement.getAttribute('data-diagram') === id, ct.diagram, { timeout: 5000 }).catch(() => {});
  await page.evaluate(() => window.ipdApp.idle());
  check(await page.evaluate(() => document.documentElement.getAttribute('data-diagram')) === ct.diagram &&
    await page.evaluate(() => location.hash) === '#' + CIT.diagrams.find(d => d.id === ct.diagram).hash,
    `drill-down: click on call activity ${ct.element_id} opens ${ct.diagram}`);
  const crumbs = await page.evaluate(() => document.querySelector('#crumbs').innerText.replace(/\s+/g, ' '));
  check(crumbs.includes(l3.model) && crumbs.includes(ct.model), 'breadcrumb: shows L3 > L4', crumbs);
  await page.click('#back');
  await page.waitForFunction(id => document.documentElement.getAttribute('data-diagram') === id, l3.id, { timeout: 5000 }).catch(() => {});
  check(await page.evaluate(() => location.hash) === '#' + l3.hash, 'back control returns to L3');
  // chip
  const chip = await page.evaluate(id => {
    const n = document.querySelector('.ipd-chip[data-ipd-open]'); if (!n) return null; const r = n.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  });
  if (chip) {
    await page.mouse.click(chip.x, chip.y);
    await page.waitForFunction(id => document.documentElement.getAttribute('data-diagram') === id, ct.diagram, { timeout: 5000 }).catch(() => {});
    check(await page.evaluate(() => document.documentElement.getAttribute('data-diagram')) === ct.diagram, 'drill-down: "Open L4" chip opens the L4');
    await page.click('#crumbs .link');
    await page.waitForFunction(id => document.documentElement.getAttribute('data-diagram') === id, l3.id, { timeout: 5000 }).catch(() => {});
    check(await page.evaluate(() => location.hash) === '#' + l3.hash, 'breadcrumb link returns to L3');
  } else {
    check(false, 'drill-down: chip not found');
  }
  // browser history back (hashchange)
  await openD(page, ct.diagram);
  await page.goBack();
  await page.waitForTimeout(150);
  await page.evaluate(() => window.ipdApp.idle());
  check(await page.evaluate(() => document.documentElement.getAttribute('data-diagram')) === l3.id, 'routing: browser back (hashchange) returns to L3');
}

// ---------------------------------------------------------------- interface placeholder click: panel, no drill-down
{
  const idg = CIT.diagrams.find(d => d.call_targets.some(c => c.interface));
  if (idg) {
    const it = idg.call_targets.find(c => c.interface), rec = EL[it.element_id];
    await openD(page, idg.id);
    const c = await clickPoint(page, it.element_id, 'corner');
    if (!c.ok) note(`click point on ${it.element_id} is covered: ${JSON.stringify(c)}`);
    await page.mouse.click(c.x, c.y);
    await page.waitForTimeout(150);
    await page.evaluate(() => window.ipdApp.idle());
    const st = await page.evaluate(() => ({ d: document.documentElement.getAttribute('data-diagram'), hash: location.hash, sel: window.ipdApp.state.selected, text: document.querySelector('#panel-body').innerText }));
    check(st.d === idg.id && st.sel === it.element_id, `interface: click on ${it.element_id} stays on ${idg.id} and opens its panel`, { d: st.d, sel: st.sel });
    const miss = rec.reqs.map(r => r.id).concat(rec.sources.map(s => s.key + ' ' + s.loc)).filter(t => !st.text.includes(t));
    check(st.text.includes('Interface - outside this model') && st.text.includes('Interface requirements') && miss.length === 0,
      `interface: panel shows the interface note, its REQs and sources (${rec.reqs.length} REQ, ${rec.sources.length} source)`, miss);
    await page.screenshot({ path: path.join(screens, `${idg.id}_interface.png`) });
  } else {
    note('no interface placeholder in this model');
  }
  const pd = CIT.diagrams.find(d => d.elements.some(id => EL[id].party && EL[id].overlay));
  if (pd) {
    const pid = pd.elements.find(id => EL[id].party && EL[id].overlay);
    await openD(page, pd.id);
    await page.evaluate(id => window.ipdApp.select(id), pid);
    const t = await page.evaluate(() => document.querySelector('#panel-body').innerText);
    check(t.includes(EL[pid].party) && (!EL[pid].record || t.includes(EL[pid].record)), `trace: panel of ${pid} shows party and record from ipd:trace`);
  }
}

// ---------------------------------------------------------------- filters
function expectedCount(d, f) {
  const q = (f.q || '').trim().toLowerCase();
  return d.filterable.filter(id => {
    const r = EL[id];
    if (f.binding && !r.badges.includes(f.binding)) return false;
    if (f.jur && !r.jurisdiction.includes(f.jur)) return false;
    if (f.keys && f.keys.length && !r.sources.some(s => f.keys.includes(s.key))) return false;
    if (q && !r.search.includes(q)) return false;
    return true;
  }).length;
}
async function uiState(p) {
  return p.evaluate(() => {
    const v = window.ipdApp.viewer, c = v.get('canvas'), d = window.ipdApp.state.diagram;
    const ids = d.filterable.filter(id => v.get('elementRegistry').get(id));
    return { count: document.querySelector('#match-count').getAttribute('data-count'), text: document.querySelector('#match-count').textContent,
      match: ids.filter(id => c.hasMarker(id, 'ipd-match')).length, dim: ids.filter(id => c.hasMarker(id, 'ipd-dim')).length, total: ids.length };
  });
}
const fd = CIT.diagrams.find(d => d.level === 'L4') || CIT.diagrams[0];
await openD(page, fd.id);
await page.evaluate(() => window.ipdApp.select(null));
const keyCounts = {};
fd.filterable.forEach(id => [...new Set(EL[id].sources.map(s => s.key))].forEach(k => { keyCounts[k] = (keyCounts[k] || 0) + 1; }));
const fkey = Object.keys(keyCounts).sort((a, b) => keyCounts[a] - keyCounts[b] || a.localeCompare(b))[0];
if (fkey) {
  await page.click('#f-keys summary');
  await page.check(`#f-keys-list input[value="${fkey}"]`);
  await page.click('#f-keys summary');
  const exp = expectedCount(fd, { keys: [fkey] });
  const s = await uiState(page);
  check(Number(s.count) === exp && s.match === exp && s.dim === s.total - exp, `filter: source key ${fkey} on ${fd.id} -> ${exp} matches (count, highlight, dim)`, s);
  await page.screenshot({ path: path.join(screens, `${fd.id}_filter.png`) });
  const listText = await page.evaluate(() => document.querySelector('#panel-body').innerText);
  check(listText.includes(`Matching elements (${exp})`), 'filter: panel lists the matching elements');
  await page.click('#f-clear');
}
for (const f of [{ binding: 'DRAFT' }, { binding: 'VERIFY' }, { binding: 'LAW' }, { jur: 'US' }, { jur: 'EU' }]) {
  if (f.binding) await page.selectOption('#f-binding', f.binding);
  if (f.jur) await page.selectOption('#f-jur', f.jur);
  const exp = expectedCount(fd, f), s = await uiState(page);
  check(Number(s.count) === exp && s.match === exp, `filter: ${JSON.stringify(f)} on ${fd.id} -> ${exp} matches`, s);
  await page.click('#f-clear');
}
const someLabel = fd.filterable.map(id => EL[id].label).find(l => l && l.length > 8);
if (someLabel) {
  const q = someLabel.split(/\s+/).slice(-2).join(' ');
  await page.fill('#f-q', q);
  const exp = expectedCount(fd, { q }), s = await uiState(page);
  check(Number(s.count) === exp && exp > 0 && s.match === exp, `filter: free text "${q}" on ${fd.id} -> ${exp} matches`, s);
  await page.click('#f-clear');
}
const cleared = await uiState(page);
check(cleared.match === 0 && cleared.dim === 0 && cleared.count === '', 'filter: clear removes all highlights');

// ---------------------------------------------------------------- zoom buttons
{
  await page.click('#z-fit');
  const z0 = await page.evaluate(() => window.ipdApp.viewer.get('canvas').zoom());
  await page.click('#z-in');
  const z1 = await page.evaluate(() => window.ipdApp.viewer.get('canvas').zoom());
  await page.click('#z-100');
  const z2 = await page.evaluate(() => window.ipdApp.viewer.get('canvas').zoom());
  await page.click('#z-fit');
  const z3 = await page.evaluate(() => window.ipdApp.viewer.get('canvas').zoom());
  check(z1 > z0 && Math.abs(z2 - 1) < 0.01 && Math.abs(z3 - z0) < 0.01, 'zoom: +, 100% and Fit buttons work', { z0, z1, z2, z3 });
  const rd = await page.evaluate(() => document.querySelector('#z-level').textContent);
  check(rd.startsWith('Zoom ' + Math.round(z3 * 100) + '%'), 'zoom: readout shows the current zoom', rd);
}

// ---------------------------------------------------------------- copy button
await page.evaluate(() => document.querySelector('#copy-xml').scrollIntoView());
await page.click('#copy-xml');
await page.waitForFunction(() => document.querySelector('#copy-status').hasAttribute('data-ok'), null, { timeout: 5000 }).catch(() => {});
const copy = await page.evaluate(async () => {
  const ok = document.querySelector('#copy-status').getAttribute('data-ok');
  let clip = null;
  try { clip = await navigator.clipboard.readText(); } catch (e) { clip = null; }
  return { ok, status: document.querySelector('#copy-status').textContent, clip, fallback: !document.querySelector('#copy-fallback').hidden ? document.querySelector('#copy-fallback').value : null };
});
const bpmnPath = path.join(ROOT, CIT.meta.inputs.bpmn.file);
const bpmnXml = fs.existsSync(bpmnPath) ? fs.readFileSync(bpmnPath, 'utf8') : null;
if (copy.ok === '1' && copy.clip !== null) check(copy.clip === bpmnXml, 'copy: clipboard holds the exact BPMN XML', `${copy.clip.length} chars`);
else check(copy.status.length > 0 && (copy.ok === '1' || copy.fallback === bpmnXml), 'copy: in-page confirmation (or manual-copy fallback with the exact XML)', copy.status);
await page.screenshot({ path: path.join(screens, 'legend.png'), fullPage: true });

// ---------------------------------------------------------------- watermark visible, runtime href/src audit
await page.evaluate(() => window.scrollTo(0, 0));
const wm = await page.evaluate(() => {
  const a = document.querySelector('.bjs-powered-by'); if (!a) return { present: false };
  const r = a.getBoundingClientRect(); const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
  return { present: true, visible: r.width > 0 && r.height > 0 && !!top && (a === top || a.contains(top)) };
});
check(wm.present && wm.visible, 'licence: bpmn.io watermark present and not covered');
const allowedUrls = new Set();
Object.values(EL).forEach(r => { r.sources.forEach(s => s.url && allowedUrls.add(s.url)); r.reqs.forEach(q => q.findings.forEach(f => f.url && allowedUrls.add(f.url))); });
Object.values(CIT.findings || {}).forEach(f => f.url && allowedUrls.add(f.url));
const audit = [];
for (const d of CIT.diagrams) {
  await openD(page, d.id);
  for (const id of d.elements) {
    await page.evaluate(id => window.ipdApp.select(id), id);
    const bad = await page.evaluate(() => Array.from(document.querySelectorAll('[src],[href],[srcset],[action]')).map(n => ({
      tag: n.tagName, cls: n.className && n.className.baseVal !== undefined ? n.className.baseVal : n.className,
      url: n.getAttribute('src') || n.getAttribute('href') || n.getAttribute('srcset') || n.getAttribute('action'),
      inPanel: !!n.closest('#panel'), target: n.getAttribute('target') })).filter(x => !/^(data:|blob:|#)/.test(x.url || '#')));
    bad.forEach(b => {
      const ok = (b.tag === 'A' && b.inPanel && /src-link/.test(b.cls) && allowedUrls.has(b.url)) || (b.tag === 'A' && /bjs-powered-by/.test(b.cls)) ||
        (!!publishDir && b.tag === 'SCRIPT' && (cdnMap.has(b.url) || ownRel(b.url)));
      if (!ok) audit.push({ element: id, ...b });
    });
  }
}
check(audit.length === 0, 'runtime: external URLs only in panel source links (from citations) and the bpmn.io licence watermark' +
  (publishDir ? ' (plus the pinned CDN and own script tags)' : ''), audit.slice(0, 10));
const dashes = await page.evaluate(() => /[—·]/.test(document.body.innerText));
if (dashes) note('page text contains an em dash or middle dot from the model or findings content (kept verbatim)');
else check(true, 'runtime: no em dash or middle dot in the rendered page text');

// ---------------------------------------------------------------- hash routing on load
const page2 = await newPage(); wire(page2);
const l4 = CIT.diagrams.find(d => d.level === 'L4');
if (l4) {
  await load(page2, l4.hash);
  check(await page2.evaluate(() => document.documentElement.getAttribute('data-diagram')) === l4.id, `routing: loading #${l4.hash} opens ${l4.id}`);
}
await load(page2, 'not-a-view');
check(await page2.evaluate(() => location.hash) === '#' + l3.hash, 'routing: unknown hash falls back to #' + l3.hash);
await page2.close();

// ---------------------------------------------------------------- responsive
const page3 = await newPage(); wire(page3);
await page3.setViewportSize({ width: 820, height: 1000 });
await load(page3, fd.hash);
const resp = await page3.evaluate(() => {
  const cw = document.querySelector('.canvas-wrap').getBoundingClientRect(), p = document.querySelector('#panel').getBoundingClientRect();
  return { below: p.top >= cw.bottom - 1, bodyHidden: getComputedStyle(document.querySelector('#panel-body')).display === 'none', toggle: getComputedStyle(document.querySelector('#panel-toggle')).display !== 'none' };
});
check(resp.below && resp.bodyHidden && resp.toggle, 'responsive: under 900 px the panel collapses below the canvas', resp);
const tid = fd.overlay_elements.find(id => EL[id].type === 'bpmn:Task') || fd.overlay_elements[0];
if (tid) {
  await page3.evaluate(id => window.ipdApp.select(id), tid);
  await page3.waitForTimeout(80);
  const open = await page3.evaluate(() => getComputedStyle(document.querySelector('#panel-body')).display !== 'none');
  check(open, 'responsive: selecting an element expands the panel');
  await page3.screenshot({ path: path.join(screens, `${fd.id}_narrow.png`), fullPage: true });
}
await page3.close();

check(consoleErrors.length === 0, 'console: zero console errors', consoleErrors);
check(pageErrors.length === 0, 'console: zero page errors', pageErrors);
check(dialogs.length === 0, 'no alert/confirm/prompt dialogs', dialogs);
seenPages.filter(p => !ownPages.has(p)).forEach(p => popups.push(p.url()));
check(popups.length === 0, 'no popups (window.open)', popups);
if (!publishDir) {
  const nonLocal = allRequests.filter(u => u.split('#')[0] !== fileUrl && !/^(data|blob):/.test(u));
  check(external.length === 0 && nonLocal.length === 0, 'network: no requests except the file itself, data: and blob:', { aborted: external, other: nonLocal });
} else {
  const own = [...new Set(allRequests.filter(u => u.startsWith(origin + '/')).map(u => u.slice(origin.length + 1).split('#')[0].split('?')[0]))].sort();
  const ownBad = own.filter(p => !ownRel(p));
  const cdnSeen = [...new Set(allRequests.filter(u => cdnMap.has(u)))].sort();
  const other = allRequests.filter(u => !u.startsWith(origin + '/') && !cdnMap.has(u) && !/^(data|blob):/.test(u));
  check(external.length === 0 && other.length === 0 && ownBad.length === 0 && cdnMap.size === 2 && JSON.stringify(cdnSeen) === JSON.stringify([...cdnMap.keys()].sort()),
    `network: only the two pinned CDN scripts and the page's own files (${own.join(', ')})`, { aborted: external, other, ownBad, cdnSeen });
  // SRI is enforced: a CDN script with one changed byte is refused and the page says so (separate context)
  const tctx = await browser.newContext({ viewport: { width: 1200, height: 800 } });
  const tExt = [], tErr = [];
  await routeAll(tctx, tExt, u => /bpmn-js@/.test(u));
  const tp = await tctx.newPage();
  tp.on('console', m => { if (m.type() === 'error') tErr.push(m.text()); });
  await tp.goto(pageUrl, { waitUntil: 'load' });
  await tp.waitForFunction(() => !document.querySelector('#canvas-msg').hidden, null, { timeout: 10000 }).catch(() => {});
  const ts = await tp.evaluate(() => ({ bpmnjs: typeof window.BpmnJS, ready: document.documentElement.getAttribute('data-ready'), msg: document.querySelector('#canvas-msg').textContent }));
  check(ts.bpmnjs === 'undefined' && ts.ready !== '1' && tErr.some(e => /integrity/i.test(e)) && /integrity/.test(ts.msg),
    'sri: a tampered bpmn-js response is blocked by the browser (integrity error) and the page shows a message', { ...ts, errors: tErr.slice(0, 2) });
  await tctx.close();
}
await browser.close();
if (server) server.kill();

const summary = { html: htmlFile, size, failures, assertions: results.length, perDiagram, notes, screens,
  publish: publishDir ? { dir: publishDir, origin, cdn: [...cdnMap.keys()] } : undefined };
if (jsonOut) fs.writeFileSync(jsonOut, JSON.stringify({ ...summary, results }, null, 2) + '\n');
console.log(`\n${failures === 0 ? 'ALL PASS' : failures + ' FAILURE(S)'}: ${results.length} assertions`);
process.exit(failures === 0 ? 0 : 1);
