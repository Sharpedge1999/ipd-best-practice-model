#!/usr/bin/env python3
"""V1 review: draw the semantic spot-check sample and dump the evidence for each sampled task.

Sample: 25 tasks (spec node type 'task'), random.Random(20261106).sample() over the sorted list of (model, id)
pairs. For each task: label, lane/pool, party, deadline, then each REQ (statement, party, action, deadline) and
each finding behind it (paraphrase, party, deadline, quote). The judgement itself is recorded in
tools/validate/v1_review_judgements.json and turned into error records by --judge.

Usage: python -I tools/validate/v1_review_sample.py --dump /tmp/x.txt
       python -I tools/validate/v1_review_sample.py --judge tools/validate/v1_review_judgements.json --out /tmp/review.json
"""
import argparse
import glob
import json
import os
import random

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = 20261106
N = 25


def load():
    specs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "spec", "L*.yaml"))):
        s = yaml.safe_load(open(f, encoding="utf-8"))
        specs[s["id"]] = s
    reqs = {r["id"]: r for r in yaml.safe_load(open(os.path.join(ROOT, "synthesis", "requirements.yaml"), encoding="utf-8"))}
    finds = {f["id"]: f for f in yaml.safe_load(open(os.path.join(ROOT, "synthesis", "merged_findings.yaml"), encoding="utf-8"))}
    return specs, reqs, finds


def sample(specs):
    pairs = sorted((m, n["id"]) for m, s in specs.items() for n in s["nodes"] if n["type"] == "task")
    return pairs, random.Random(SEED).sample(pairs, N)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--judge")
    ap.add_argument("--out")
    a = ap.parse_args()
    specs, reqs, finds = load()
    pairs, smp = sample(specs)
    if a.dump:
        out = ["population: %d tasks; sample (seed %d): %s" % (len(pairs), SEED, ", ".join("%s %s" % p for p in smp)), ""]
        for k, (m, i) in enumerate(smp, 1):
            s = specs[m]
            n = next(x for x in s["nodes"] if x["id"] == i)
            lanes = {l["id"]: l["name"] for l in s.get("lanes", [])}
            where = lanes.get(n.get("lane"), n.get("pool"))
            out.append("=" * 100)
            out.append("#%d %s %s %r  [%s]  binding=%s draft=%s deadline=%r party=%r" % (k, m, i, n["label"], where, n.get("binding"), n.get("draft", False),
                                                                                       n.get("deadline", ""), n.get("party", "")))
            ins = [f["from"] for f in s["flows"] if f["to"] == i]
            outs = [f["to"] for f in s["flows"] if f["from"] == i]
            mfs = ["%s %s->%s %r" % (x["id"], x["from"], x["to"], x["label"]) for x in s.get("message_flows", []) if i in (x["from"], x["to"])]
            out.append("   flow in %s out %s; message flows %s" % (ins, outs, mfs))
            for q in n.get("req", []):
                r = reqs[q]
                out.append("   %s [%s %s%s] party=%s deadline=%r" % (q, r["binding"], r["status"], " DRAFT" if r["draft"] else "", r["party_norm"], r["deadline"]))
                out.append("      statement: %s" % r["statement"])
                out.append("      action: %s | trigger: %s | recipient: %s" % (r["action"], r["trigger"], r["recipient"]))
                for fid in r["findings"]:
                    f = finds[fid]
                    out.append("      - %s %s %s (%s%s) party=%r deadline=%r" % (fid, f["src"], f["loc"], f["binding"], " draft" if f.get("draft") else "", f["party"], f["deadline"]))
                    out.append("        paraphrase: %s" % f["paraphrase"])
                    if f.get("quote"):
                        out.append("        quote: %s" % f["quote"])
            out.append("")
        open(a.dump, "w", encoding="utf-8").write("\n".join(out))
        print("dumped %d sampled tasks to %s" % (len(smp), a.dump))
    if a.judge:
        j = json.load(open(a.judge, encoding="utf-8"))
        errors, passed = [], []
        jk = {(x["model"], x["element"]): x for x in j["tasks"]}
        missing = [p for p in smp if p not in jk]
        extra = [k for k in jk if k not in smp]
        assert not missing and not extra, "judgement file does not match the sample: missing %s extra %s" % (missing, extra)
        n_ok = 0
        for m, i in smp:
            x = jk[(m, i)]
            if x["verdict"] == "ok":
                n_ok += 1
                continue
            errors.append(dict(rule_id=x.get("rule_id", "GEN-03"), layer="REVIEW", model=m, element=i, message=x["message"],
                               severity=x["severity"], owner=x["owner"], status="open"))
        for e in j.get("other_findings", []):
            errors.append(dict(layer="REVIEW", status=e.get("status", "open"), **{k: v for k, v in e.items() if k != "status"}))
        for p in j.get("passed", []):
            passed.append(dict(layer="REVIEW", **p))
        passed.append(dict(layer="REVIEW", check="semantic spot check: task label and REQ statements match the finding paraphrases (no invented obligation, actor or deadline); sample = random.Random(%d).sample(sorted (model, id) task pairs, %d) of %d tasks: %s"
                           % (SEED, N, len(pairs), ", ".join("%s %s" % p for p in smp)), count=n_ok, note="%d of %d sampled tasks without finding" % (n_ok, N)))
        json.dump(dict(errors=errors, passed=passed, not_checked=j.get("not_checked", []),
                       inputs=["spec/*.yaml", "spec/notes.md", "synthesis/requirements.yaml", "synthesis/merged_findings.yaml", "synthesis/glossary.yaml",
                               "synthesis/l3_cut.md", "synthesis/conflicts.md", "tools/validate/v1_review_judgements.json"]),
                  open(a.out, "w", encoding="utf-8"), indent=1)
        print("review: %d error records, %d passed" % (len(errors), len(passed)))


if __name__ == "__main__":
    main()
