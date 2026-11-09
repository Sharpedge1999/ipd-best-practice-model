# iPD best-practice reference model (BPMN 2.0)

Best-practice reference model of important protocol deviation (iPD) management in clinical development, derived outside-in from ICH, EU and US sources plus industry best practice. Every modelled element carries the sources it rests on (BPMN extension `ipd:trace`, namespace `urn:ipd-best-practice:trace:1.0`), and the interactive map shows them under each step.

Status: final build 07 Nov 2026; viewer fix (readable labels on highlighted and selected elements) 09 Nov 2026; side panel closed by default and opened by a click on a step, with a step description (what happens, at a glance; requirements and sources folded) 09 Nov 2026. Independent validation (3 rounds): pass with documented exceptions, 0 open MUST. **Not validated by process owners (GEN-06)** - fit to the real process is open. Open decisions, [verify] items and gaps: `register/HANDOVER_iPD_Best_Practice_Model.md`.

## Deliverables

| Path | Content |
|---|---|
| `out/ipd_best_practice.bpmn` | BPMN 2.0 XML with DI: L3 overview plus eight L4 models in one definitions file; per-model files in `out/models/` |
| `out/ipd_best_practice_map.html` | Interactive map, one self-contained file (works offline) |
| `out/publish/` | Hosted variant of the map: bpmn-js 18.31.1 and diagram-js-minimap 5.6.0 from jsDelivr with SRI, model and citations as own files |
| GitHub Pages | `.github/workflows/pages.yml` publishes `out/publish/` on every push to `main` that changes it (plus the offline map as `offline.html`). One-time setup: Settings → Pages → Source: GitHub Actions |
| `out/citations.json` | Trace data per element (sources, findings, requirements) used by the map |
| `register/` | Requirements register (`iPD_Requirements_Register.md`, split copy in `parts/`) and handover |

## Model

Scope: from "CtQ factors identified" to "iPDs reported in clinical study report and records archived". Jurisdictions ICH + EU + US; generic GCP roles as lanes and pools.

| L3 | Step | L4 model |
|---|---|---|
| A1 | Define trial-specific iPD criteria | `spec/L4-01.yaml` |
| A2 | Identify protocol deviations | `spec/L4-02.yaml` |
| A3 | Manage intentional protocol deviations | `spec/L4-03.yaml` |
| A4 | Document and classify protocol deviations | `spec/L4-04.yaml` |
| A5 | Assess and notify reportable noncompliance (parallel to A4) | `spec/L4-05.yaml` |
| A6 | Remediate deviations and noncompliance | `spec/L4-06.yaml` |
| A7 | Finalise iPDs for clinical study report | `spec/L4-07.yaml` |
| A8 | Archive deviation records | `spec/L4-08.yaml` |

Evidence base: 537 findings, 271 requirements (59 binding law, 138 ICH, 58 guidance of which 24 rest on draft guidance only, 16 best practice), 27 documented conflicts (C-01 to C-27). All 134 in-scope binding requirements sit on model elements.

## Repository layout

| Folder | Content |
|---|---|
| `context/` | Brief, workflow plan, BPMN design criteria used for modelling and validation |
| `contracts/` | Schemas, source registry, `ipd:trace` extension (moddle descriptor), decision log S0 |
| `research/` | Findings of the five research stems R1-R5 |
| `synthesis/` | Merged findings, requirements, conflicts, L3 cut, requirement-to-step map, glossary |
| `spec/` | Frozen YAML specs of L3 and L4-01 to L4-08 (`FROZEN.sha256`) |
| `tools/` | Linters, spec-to-BPMN converter and layout, gates, viewer build and tests, validation scripts (`tools/validate/`) |
| `viewer/` | Viewer source (`src/`) and pinned npm dependencies (`package.json`) |
| `verification/` | Blind verification of findings against source texts (X1) |
| `validation/` | Independent validation reports, rounds 1-3 |
| `vendor/` | Official source texts downloaded for verification (`sources/INDEX.md`, `fetch_log.tsv`), BPMN XSD, tool dependencies (`node/package.json`) |
| `fixtures/` | Test fixtures for the linters and converter |
| `out/` | Build outputs, rendered screens and self-test outputs |

## Rebuild

Requirements: Python 3.13 with `pyyaml`, `lxml`, `jsonschema`; Node 22; Google Chrome for the headless tests. Install the npm dependencies with `npm ci` in `viewer/` and in `vendor/node/` (not committed).

```sh
# 1. Lint specs, convert to BPMN 2.0 (also writes out/ipd_best_practice.report.json), run the gate
python -I tools/lint_spec.py spec/*.yaml
python -I tools/spec2bpmn.py --specs spec --out out/ipd_best_practice.bpmn --models-out out/models
python -I tools/b2_gate.py --specs spec --out out/ipd_best_practice.bpmn --models-out out/models

# 2. Build the map (single file and hosted variant)
python -I tools/build_viewer.py --bpmn out/ipd_best_practice.bpmn --report out/ipd_best_practice.report.json \
  --findings synthesis/merged_findings.yaml --requirements synthesis/requirements.yaml \
  --registry contracts/source_registry.yaml --out out/ipd_best_practice_map.html --citations-out out/citations.json \
  --source-basis "Sources read 06 Nov 2026; ICH E6(R3) consolidated text of 16 Jun 2026" \
  --publish-dir out/publish --publish-bpmn-name ipd_best_practice.bpmn.xml

# 3. Test the map
node tools/test_viewer.mjs --html out/ipd_best_practice_map.html --citations out/citations.json --screens out/screens
node tools/test_viewer.mjs --publish-dir out/publish --screens out/publish_screens
```

The viewer build is deterministic: the same inputs give byte-identical outputs.

## Notes

- Texts under `vendor/sources/` are third-party documents (ICH, EU, FDA, eCFR, industry bodies) kept only to make the verification reproducible; rights remain with their owners. Their URLs are in `contracts/source_registry.yaml`.
- Hyphen "-" instead of em dash and no middle dot are deliberate conventions of all texts in this repository.
