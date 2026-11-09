// V1 layer L1: bpmn-moddle import (with the ipd extension) and bpmnlint "recommended"
// on every given .bpmn file. Read-only on the inputs; prints one JSON document to stdout.
//
// Usage: node tools/validate/v1_moddle_lint.mjs <file.bpmn> [...]
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const VENDOR = path.join(ROOT, 'vendor', 'node');
const require = createRequire(path.join(VENDOR, 'package.json'));
const { BpmnModdle } = await import(pathToFileURL(path.join(VENDOR, 'node_modules', 'bpmn-moddle', 'dist', 'index.js')).href);
const ipd = JSON.parse(fs.readFileSync(path.join(ROOT, 'contracts', 'ipd_moddle.json'), 'utf8'));
const Linter = require('bpmnlint/lib/linter');
const NodeResolver = require('bpmnlint/lib/resolver/node-resolver');
const recommended = require('bpmnlint/config/recommended.js');
const pkg = (n) => JSON.parse(fs.readFileSync(path.join(VENDOR, 'node_modules', n, 'package.json'), 'utf8')).version;

const files = process.argv.slice(2);
const out = { tool: 'v1_moddle_lint.mjs', versions: { 'bpmn-moddle': pkg('bpmn-moddle'), bpmnlint: pkg('bpmnlint') },
  recommended_rules: recommended.rules, files: {} };
for (const f of files) {
  const xml = fs.readFileSync(f, 'utf8');
  const moddle = new BpmnModdle({ ipd });
  const rec = { import_warnings: [], lint: {} };
  try {
    const { rootElement, warnings } = await moddle.fromXML(xml);
    rec.import_warnings = warnings.map(w => String(w.message || w));
    // count ipd:trace and ipd:source as seen by moddle
    let traces = 0, sources = 0;
    const seen = new Set();
    const walk = (o) => {
      if (!o || typeof o !== 'object' || seen.has(o)) return;
      seen.add(o);
      if (o.$type === 'ipd:Trace') { traces++; sources += (o.sources || []).length; }
      for (const k of Object.keys(o)) {
        if (k.startsWith('$') && k !== '$children') continue;
        const v = o[k];
        if (Array.isArray(v)) v.forEach(walk); else if (v && typeof v === 'object' && v.$type) walk(v);
      }
    };
    walk(rootElement);
    rec.moddle_traces = traces; rec.moddle_sources = sources;
    rec.xml_traces = (xml.match(/<ipd:trace[\s>]/g) || []).length;
    rec.xml_sources = (xml.match(/<ipd:source[\s>]/g) || []).length;
    rec.xml_ids = (xml.match(/\sid="/g) || []).length;
    // lossless round trip: export and re-import, compare trace/source counts and element ids
    const { xml: xml2 } = await moddle.toXML(rootElement, { format: true });
    const again = await new BpmnModdle({ ipd }).fromXML(xml2);
    rec.reimport_warnings = again.warnings.map(w => String(w.message || w));
    rec.roundtrip_traces = (xml2.match(/<ipd:trace[\s>]/g) || []).length;
    rec.roundtrip_sources = (xml2.match(/<ipd:source[\s>]/g) || []).length;
    rec.roundtrip_ids = (xml2.match(/\sid="/g) || []).length;
    const idset = (x) => new Set([...x.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]));
    const a = idset(xml), b = idset(xml2);
    rec.roundtrip_missing_ids = [...a].filter(i => !b.has(i)).slice(0, 20);
    const linter = new Linter({ config: { extends: 'bpmnlint:recommended' }, resolver: new NodeResolver({ requireLibrary: require }) });
    const results = await linter.lint(rootElement);
    for (const [rule, reports] of Object.entries(results)) {
      if (reports.length) rec.lint[rule] = reports.map(r => ({ category: r.category, id: r.id, message: r.message }));
    }
  } catch (e) {
    rec.fatal = String(e && e.stack || e);
  }
  out.files[f] = rec;
}
process.stdout.write(JSON.stringify(out, null, 1));
