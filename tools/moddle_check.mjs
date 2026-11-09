#!/usr/bin/env node
// B2 moddle check: import a .bpmn with bpmn-moddle + the ipd extension
// (contracts/ipd_moddle.json), report warnings, export again, re-import and
// compare the two object graphs semantically (lossless round trip). ipd:trace
// is compared separately and reported with counts. Optional bpmnlint smoke run
// (recommended config); V1 owns the full lint.
//
// Usage: node tools/moddle_check.mjs --bpmn <file> [--export <file>] [--lint]
// Prints one JSON object; exit 0 = zero warnings and lossless, 1 = otherwise.
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const VENDOR = path.join(ROOT, 'vendor', 'node');
const require = createRequire(path.join(VENDOR, 'package.json'));
const { BpmnModdle } = await import(pathToFileURL(path.join(VENDOR, 'node_modules', 'bpmn-moddle', 'dist', 'index.js')).href);

function arg(name) {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : undefined;
}
const file = arg('--bpmn');
const exportFile = arg('--export');
const doLint = process.argv.includes('--lint');
if (!file) {
  console.error('usage: moddle_check.mjs --bpmn <file> [--export <file>] [--lint]');
  process.exit(2);
}
const ipd = JSON.parse(fs.readFileSync(path.join(ROOT, 'contracts', 'ipd_moddle.json'), 'utf8'));
const xml = fs.readFileSync(file, 'utf8');

// canonical dump of a moddle object graph: containment tree with attribute
// values and references written as ids
function dump(el, seen = new Set()) {
  if (el === null || el === undefined) return el;
  if (typeof el !== 'object') return el;
  if (seen.has(el)) return { $cycle: el.id || el.$type };
  seen.add(el);
  const out = { $type: el.$type };
  const desc = el.$descriptor;
  for (const p of desc.properties) {
    const v = el.get(p.name);
    if (v === undefined || v === null) continue;
    if (p.isMany && Array.isArray(v) && v.length === 0) continue;
    if (p.isReference) {
      out[p.name] = p.isMany ? v.map(r => (r && r.id) || String(r)) : ((v && v.id) || String(v));
    } else if (p.isMany) {
      out[p.name] = v.map(x => (typeof x === 'object' ? dump(x, seen) : x));
    } else if (typeof v === 'object') {
      out[p.name] = dump(v, seen);
    } else {
      out[p.name] = v;
    }
  }
  const attrs = {};
  for (const [k, v] of Object.entries(el.$attrs || {})) {
    if (!k.startsWith('xmlns')) attrs[k] = v;
  }
  if (Object.keys(attrs).length) out.$attrs = attrs;
  return out;
}

function collectTraces(el, acc, owner = null, seen = new Set()) {
  if (!el || typeof el !== 'object' || seen.has(el)) return acc;
  seen.add(el);
  if (el.$type === 'ipd:Trace') {
    acc.push({
      owner,
      binding: el.binding, jurisdiction: el.jurisdiction, deadline: el.deadline,
      draft: el.draft,
      sources: (el.sources || []).map(s => [s.key, s.loc, s.page === undefined ? null : s.page]),
      reqs: (el.reqs || []).map(r => r.id),
      verify: (el.verifyItems || []).map(v => v.text),
    });
    return acc;
  }
  const desc = el.$descriptor;
  if (!desc) return acc;
  for (const p of desc.properties) {
    if (p.isReference) continue;
    const v = el.get(p.name);
    const items = p.isMany ? (v || []) : [v];
    for (const x of items) {
      if (x && typeof x === 'object') collectTraces(x, acc, el.id || owner, seen);
    }
  }
  return acc;
}

const moddle = new BpmnModdle({ ipd });
const r1 = await moddle.fromXML(xml);
const warnings1 = r1.warnings.map(w => w.message);
const { xml: xml2 } = await moddle.toXML(r1.rootElement, { format: true });
if (exportFile) fs.writeFileSync(exportFile, xml2);
const moddle2 = new BpmnModdle({ ipd });
const r2 = await moddle2.fromXML(xml2);
const warnings2 = r2.warnings.map(w => w.message);

const d1 = JSON.stringify(dump(r1.rootElement));
const d2 = JSON.stringify(dump(r2.rootElement));
const t1 = collectTraces(r1.rootElement, []);
const t2 = collectTraces(r2.rootElement, []);
const traceLossless = JSON.stringify(t1) === JSON.stringify(t2);

// ipd:trace elements present in the source text (independent count)
const rawTraceCount = (xml.match(/<ipd:trace[\s>]/g) || []).length;
const rawSourceCount = (xml.match(/<ipd:source[\s>/]/g) || []).length;
const modelSourceCount = t1.reduce((n, t) => n + t.sources.length, 0);

let lint = null;
if (doLint) {
  const Linter = require('bpmnlint/lib/linter');
  const NodeResolver = require('bpmnlint/lib/resolver/node-resolver');
  const linter = new Linter({ config: { extends: 'bpmnlint:recommended' }, resolver: new NodeResolver() });
  const results = await linter.lint(r1.rootElement);
  lint = {};
  for (const [rule, reports] of Object.entries(results)) {
    if (reports.length) lint[rule] = reports.map(r => `${r.category} ${r.id}: ${r.message}`);
  }
}

const out = {
  file,
  import_warnings: warnings1,
  reimport_warnings: warnings2,
  graph_lossless: d1 === d2,
  trace_lossless: traceLossless,
  trace_count: t1.length,
  trace_count_in_xml: rawTraceCount,
  source_count: modelSourceCount,
  source_count_in_xml: rawSourceCount,
  traces_without_owner: t1.filter(t => !t.owner).length,
  export_file: exportFile || null,
  bpmnlint_recommended: lint,
};
console.log(JSON.stringify(out, null, 2));
const ok = warnings1.length === 0 && warnings2.length === 0 && d1 === d2 && traceLossless
  && t1.length === rawTraceCount && modelSourceCount === rawSourceCount;
process.exit(ok ? 0 : 1);
