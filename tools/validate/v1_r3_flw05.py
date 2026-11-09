#!/usr/bin/env python3
"""V1 round 3: FLW-05 evidence check of spec/notes.md section 6 (gateway -> deciding element table).

Mechanical part of the FLW-05 review (the plausibility judgement stays manual):
  1. every XOR/OR split of every spec has exactly one row with the identical question; no row for a missing gateway;
  2. every quoted element label in a row ("<model> <id> \"<label>\"" or "<id> \"<label>\"") equals the spec label of that id;
  3. every row that says "directly before" names the element that is the direct predecessor of the gateway
     (one sequence flow, possibly through an XOR/OR join).
Read-only. Usage: python -I tools/validate/v1_r3_flw05.py [--out /tmp/x.json]
"""
import argparse
import glob
import json
import os
import re

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    a = ap.parse_args()
    specs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "spec", "L*.yaml"))):
        s = yaml.safe_load(open(f, encoding="utf-8"))
        specs[s["id"]] = s
    notes = open(os.path.join(ROOT, "spec", "notes.md"), encoding="utf-8").read()
    sec = notes.split("## 6. FLW-05", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in sec.splitlines():
        m = re.match(r"\| (L3|L4-0\d) \| (G\d+) \| (.*?) \| (.*) \|$", line)
        if m:
            rows.append(dict(model=m.group(1), gw=m.group(2), question=m.group(3), decider=m.group(4)))
    splits = {(mid, n["id"]): n for mid, s in specs.items() for n in s["nodes"] if n["type"] in ("xor-split", "or-split")}
    issues, ok = [], []
    seen = {}
    for r in rows:
        k = (r["model"], r["gw"])
        seen.setdefault(k, []).append(r)
        if k not in splits:
            issues.append(dict(kind="stale row", model=r["model"], element=r["gw"], detail="row for a gateway that is not an XOR/OR split in the spec: %r" % r["question"]))
            continue
        if splits[k].get("label") != r["question"]:
            issues.append(dict(kind="question", model=r["model"], element=r["gw"], detail="row question %r != spec label %r" % (r["question"], splits[k].get("label"))))
        # quoted labels
        for mm in re.finditer(r"(?:(L3|L4-0\d) )?(A\d+[a-z]?|S\d+|E\d+) \"([^\"]+)\"", r["decider"]):
            mid = mm.group(1) or r["model"]
            el, lab = mm.group(2), mm.group(3)
            nd = {n["id"]: n for n in specs[mid]["nodes"]}
            if el not in nd:
                issues.append(dict(kind="label", model=r["model"], element=r["gw"], detail="row names %s %s which does not exist" % (mid, el)))
            elif nd[el].get("label") != lab:
                issues.append(dict(kind="label", model=r["model"], element=r["gw"], detail="row quotes %s %s as %r, spec label is %r" % (mid, el, lab, nd[el].get("label"))))
        # directly before
        if "directly before" in r["decider"]:
            mm = re.search(r"(?:(L3|L4-0\d) )?(A\d+[a-z]?)", r["decider"])
            s = specs[r["model"]]
            nd = {n["id"]: n for n in s["nodes"]}
            preds = [f["from"] for f in s["flows"] if f["to"] == r["gw"]]
            direct = set()
            for p in preds:
                if nd[p]["type"] in ("xor-join", "or-join"):
                    direct |= {f["from"] for f in s["flows"] if f["to"] == p}
                else:
                    direct.add(p)
            if not mm or mm.group(2) not in direct:
                issues.append(dict(kind="directly before", model=r["model"], element=r["gw"],
                                   detail="row says 'directly before' %s, but the predecessors of %s are %s" % (mm.group(2) if mm else "?", r["gw"], sorted(direct))))
        ok.append("%s %s" % k)
    for k in splits:
        if k not in seen:
            issues.append(dict(kind="missing row", model=k[0], element=k[1], detail="XOR/OR split %r has no row in notes.md section 6" % splits[k].get("label")))
    for k, v in seen.items():
        if len(v) > 1:
            issues.append(dict(kind="duplicate row", model=k[0], element=k[1], detail="%d rows" % len(v)))
    res = dict(n_splits=len(splits), n_rows=len(rows), splits=sorted("%s %s" % k for k in splits), issues=issues)
    print(json.dumps(res, indent=1))
    if a.out:
        json.dump(res, open(a.out, "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
