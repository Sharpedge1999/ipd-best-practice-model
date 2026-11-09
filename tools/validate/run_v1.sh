#!/usr/bin/env bash
# V1 validation, all layers, offline. Usage: bash tools/validate/run_v1.sh [round]   (default r1)
# Writes only validation/report_<round>.{json,md}, /tmp/v1r, /tmp/v1_l5 and /tmp/v1_pub. Review judgements are data in
# tools/validate/v1_review_judgements[_<round>].json and must be re-judged by hand when the specs change.
set -euo pipefail
R=${1:-r1}
P=/home/claude/ipd
cd "$P"
mkdir -p /tmp/v1r /tmp/v1_l5/screens
sha256sum -c spec/FROZEN.sha256
python -I tools/validate/v1_spec.py --out /tmp/v1r/spec.json
python -I tools/validate/v1_bpmn.py --xsd-dir vendor/xsd_v1/omg --out /tmp/v1r/bpmn.json
python -I tools/validate/v1_l1_moddle.py --out /tmp/v1r/moddle.json
python -I tools/validate/v1_report.py --round "$R" --layer L0 --src /tmp/v1r/spec.json
python -I tools/validate/v1_report.py --round "$R" --layer L1 --src /tmp/v1r/bpmn.json --src /tmp/v1r/moddle.json
python -I tools/validate/v1_report.py --round "$R" --layer L2 --src /tmp/v1r/spec.json
python -I tools/validate/v1_report.py --round "$R" --layer L3 --src /tmp/v1r/spec.json --src /tmp/v1r/bpmn.json
python -I tools/validate/v1_report.py --round "$R" --layer L4 --src /tmp/v1r/spec.json --src /tmp/v1r/bpmn.json
python -I tools/validate/v1_review_sample.py --dump /tmp/v1r/sample.txt
J=tools/validate/v1_review_judgements_${R}.json; [ -f "$J" ] || J=tools/validate/v1_review_judgements.json
python -I tools/validate/v1_review_sample.py --judge "$J" --out /tmp/v1r/review.json
python -I tools/validate/v1_report.py --round "$R" --layer REVIEW --src /tmp/v1r/review.json
cp out/ipd_best_practice_map.html out/citations.json /tmp/v1_l5/
(cd /tmp && node "$P/tools/test_viewer.mjs" --html /tmp/v1_l5/ipd_best_practice_map.html --citations /tmp/v1_l5/citations.json \
   --screens /tmp/v1_l5/screens --json-out /tmp/v1_l5/test_results.json > /tmp/v1_l5/test_stdout.txt 2>&1) || true
python -I tools/validate/v1_expected_traces.py out/ipd_best_practice.bpmn /tmp/v1r/expected_traces.json
(cd /tmp && node "$P/tools/validate/v1_render.mjs" --html /tmp/v1_l5/ipd_best_practice_map.html --bpmn "$P/out/ipd_best_practice.bpmn" \
   --expected /tmp/v1r/expected_traces.json --citations /tmp/v1_l5/citations.json --out /tmp/v1r/render.json)
python -I tools/validate/v1_selfcontained.py --html /tmp/v1_l5/ipd_best_practice_map.html --out /tmp/v1r/selfcontained.json
# round 3 additions: FLW-05 table evidence, DI measurements (LAY-02), close-ups of changed regions, publish variant
python -I tools/validate/v1_r3_flw05.py --out /tmp/v1r/flw05.json > /dev/null
python -I tools/validate/v1_r3_di.py out/ipd_best_practice.bpmn --out /tmp/v1r/di_r3.json > /dev/null
(cd /tmp && node "$P/tools/validate/v1_r3_zoomshots.mjs" --html /tmp/v1_l5/ipd_best_practice_map.html --out-dir /tmp/v1_l5/r3zoom --json /tmp/v1r/zoomshots.json > /dev/null)
if [ -d out/publish ]; then
  rm -rf /tmp/v1_pub && mkdir -p /tmp/v1_pub/screens /tmp/v1_pub/w1screens && cp -r out/publish /tmp/v1_pub/publish
  python -I tools/validate/v1_expected_traces.py /tmp/v1_pub/publish/data/ipd_best_practice.bpmn /tmp/v1r/expected_traces_pub.json
  (cd /tmp && node "$P/tools/validate/v1_publish.mjs" --dir /tmp/v1_pub/publish --expected /tmp/v1r/expected_traces_pub.json \
     --out /tmp/v1r/publish.json --screens /tmp/v1_pub/screens | head -1)
  (cd /tmp && node "$P/tools/test_viewer.mjs" --publish-dir /tmp/v1_pub/publish --screens /tmp/v1_pub/w1screens \
     --json-out /tmp/v1_pub/w1_test_results.json > /tmp/v1_pub/w1_stdout.txt 2>&1) || true
fi
echo "L5: build /tmp/v1r/l5_w1suite.json from /tmp/v1_l5/test_results.json, /tmp/v1_pub/w1_test_results.json plus the screenshot judgement, then:"
echo "python -I tools/validate/v1_report.py --round $R --layer L5 --src /tmp/v1r/l5_w1suite.json --src /tmp/v1r/render.json --src /tmp/v1r/selfcontained.json --src /tmp/v1r/publish.json"
echo "then: python -I tools/validate/v1_report.py --round $R --md-only --compare <previous round> [--verdict ... --verdict-file ...]"
python -I tools/validate/v1_selftest.py | tail -1
python -I tools/validate/v1_selftest.py --bpmn-only --work /tmp/v1_selftest_bpmn | tail -1
