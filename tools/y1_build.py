#!/usr/bin/env python3
"""Y1 synthesis build (deterministic). Run: python -I tools/y1_build.py

Inputs : research/R1..R5_*.yaml, synthesis/x1_corrections.yaml (X1 overlay), synthesis/requirements_src.yaml,
         vendor/sources/INDEX.md, synthesis/l3_cut.md (markers only)
Outputs: synthesis/requirements.yaml, synthesis/merged_findings.yaml,
         synthesis/req_to_step.yaml, synthesis/verification_worklist.yaml,
         synthesis/l3_cut.md (REQ lists between <!--REQS:An--> markers)
Prints the G2 self-check. Exit 1 if a structural check fails.
"""
import math
import random
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ["R1_ich_e6r3.yaml", "R2_ich_other.yaml", "R3_eu.yaml", "R4_us.yaml", "R5_industry.yaml"]
SYN = ROOT / "synthesis"
SEED = 20261106
STEPS = [f"A{i}" for i in range(1, 9)]
STRENGTH = {"binding-law": 4, "binding-ICH": 3, "guidance": 2, "best-practice": 1, "verify-binding": 0}
MODAL_RANK = {"must": 5, "should": 4, "may": 3, "definition": 2, "example": 1}
JUR_ORDER = {"ICH": 0, "EU": 1, "US": 2}
UNUSABLE_LOCAL = {"CTIS-TM05": "local copy is an HTTP 404 page (R3 notes)"}

E6R3_ROUTE = ("ICH E6(R3) Step 4. EU: EU CTR Art. 47 requires conduct per GCP principles and 'appropriate account' of "
              "ICH GCP; EMA scientific guideline, Principles and Annex 1 effective 23 Jul 2025, Annex 2 and consolidated "
              "text effective 15 Jan 2027; EU CTR prevails over conflicting guideline text (Q&A 1.5). US: FDA guidance, "
              "nonbinding (Principles and Annex 1 final Sept 2025; Annex 2 draft); binding only where 21 CFR restates it")
ICH_OTHER_ROUTE = ("ICH Step 4 guideline. EU and US adoption of {key} not checked by the research stems [verify binding]; "
                   "in the US ICH guidelines are guidance only")
ROUTES = {
    "E6R3": E6R3_ROUTE,
    "EUCTR": "Regulation (EU) No 536/2014, directly applicable in all EU Member States",
    "21CFR312": "US federal regulation 21 CFR Part 312, binding",
    "21CFR56": "US federal regulation 21 CFR Part 56, binding",
    "21CFR50": "US federal regulation 21 CFR Part 50, binding",
    "FDA-ESTUDY": "FDA guidance with binding effect for electronic format under FD&C Act 745A(a) [verify binding]",
    "EMA-SB": "EMA guideline interpreting EU CTR Art. 52 (non-binding guidance)",
    "EUCTR-QA": "European Commission Q&A on EU CTR, EudraLex Volume 10 (non-binding guidance)",
    "CTIS-BT-SB24": "EMA CTIS training material (non-binding guidance)",
    "CTIS-TM17": "EMA CTIS training material (non-binding guidance)",
    "CTIS-TM05": "EMA CTIS training material, 2021 (non-binding guidance)",
    "EMA-E6R3": "EMA adoption notice of ICH E6(R3) (EU effective dates)",
    "FDA-PD24": "FDA draft guidance, Dec 2024 (nonbinding, not for implementation)",
    "FDA-E6R3": "FDA final guidance (nonbinding)",
    "FDA-E6R3-A2": "FDA draft guidance (nonbinding)",
    "FDA-RBM13": "FDA final guidance, 2013 (nonbinding)",
    "FDA-RBM23": "FDA final guidance, 2023 (nonbinding)",
    "FDA-SDTCG": "FDA technical conformance guide (nonbinding)",
}
BP_ROUTE = "Industry best practice or data standard; no regulatory status"
ICH_OTHER = {"E8R1", "E3", "E3QA", "E9", "E9R1", "M11", "M11-TEMPLATE"}


def route_for(key):
    if key in ROUTES:
        return ROUTES[key]
    if key in ICH_OTHER:
        return ICH_OTHER_ROUTE.format(key=key)
    return BP_ROUTE


def load_findings():
    out = []
    for name in RESEARCH:
        out += yaml.safe_load((ROOT / "research" / name).read_text(encoding="utf-8"))
    return out


def parse_index():
    rows = {}
    for line in (ROOT / "vendor" / "sources" / "INDEX.md").read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and cells[1].startswith("vendor/"):
            rows.setdefault(cells[0], []).append((cells[1], cells[2]))
    return rows


def local_text(rec, index):
    key = rec["src"]
    if key in UNUSABLE_LOCAL or key not in index:
        return None
    entries = index[key]
    for path, url in entries:
        if url == rec.get("url"):
            chosen = path
            break
    else:
        chosen = entries[0][0]
    return chosen if (ROOT / chosen).is_file() else None


def norm_verify(fid, item):
    item = item.strip()
    if item.lower().startswith("[verify"):
        return f"{item} ({fid})"
    return f"[verify] {item} ({fid})"


def apply_x1(findings):
    """Overlay synthesis/x1_corrections.yaml (X1 gate G4) on copies of the research records."""
    path = SYN / "x1_corrections.yaml"
    corr = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else []
    by_id = {c["id"]: c for c in corr or []}
    out = []
    for f in findings:
        c = by_id.get(f["id"])
        if not c:
            out.append(f)
            continue
        g = dict(f)
        g.update(c.get("set") or {})
        if c.get("drop_verify"):
            g["verify"] = []
        if c.get("drop_verify_containing"):
            g["verify"] = [v for v in g.get("verify") or [] if c["drop_verify_containing"] not in v]
        g["x1"] = c["x1"]
        out.append(g)
    missing = set(by_id) - {f["id"] for f in findings}
    if missing:
        raise SystemExit(f"x1_corrections: unknown ids {sorted(missing)}")
    return out


def main():
    raw_findings = load_findings()
    raw_map = {f["id"]: f for f in raw_findings}
    findings = apply_x1(raw_findings)
    fmap = {f["id"]: f for f in findings}
    src = yaml.safe_load((SYN / "requirements_src.yaml").read_text(encoding="utf-8"))
    errors = []

    reqs = []
    f_to_req = {fid: [] for fid in fmap}
    dup_of = {}
    for n, e in enumerate(src, start=1):
        rid = f"REQ-{n:03d}"
        fl = e["f"]
        for fid in fl:
            if fid not in fmap:
                errors.append(f"{rid} ({e['k']}): unknown finding {fid}")
        fl = [x for x in fl if x in fmap]
        if not fl:
            errors.append(f"{rid}: no findings")
            continue
        for fid in fl:
            f_to_req[fid].append(rid)
        for d, c in (e.get("dup") or {}).items():
            if d not in fl or c not in fl:
                errors.append(f"{rid}: dup pair {d}->{c} not within REQ findings")
            dup_of[d] = c
        recs = [fmap[x] for x in fl]
        top = max(STRENGTH[r["binding"]] for r in recs)
        strongest = [r for r in recs if STRENGTH[r["binding"]] == top]
        binding = strongest[0]["binding"]
        draft = all(bool(r.get("draft")) for r in strongest)
        modal = max((r["modal"] for r in strongest), key=MODAL_RANK.get)
        keys = list(OrderedDict.fromkeys(r["src"] for r in strongest))
        route = "; ".join(f"{k}: {route_for(k)}" for k in keys)
        jur = sorted({r["jurisdiction"] for r in recs}, key=JUR_ORDER.get)
        first = recs[0]

        def dflt(field, fallback=""):
            if field in e:
                return e[field]
            v = (first.get({"t": "trigger", "d": "deadline", "r": "recipient", "rec": "record"}[field]) or "").strip()
            return v if v else fallback

        st = e["st"]
        if st in STEPS:
            status, step, reason = "in_scope", st, ""
        elif st == "OOS":
            status, step, reason = "out_of_scope", None, e.get("why", "")
        elif st.startswith("INT:"):
            status, step, reason = "interface", st.split(":", 1)[1], e.get("why", "")
        else:
            errors.append(f"{rid}: bad st {st}")
            continue
        if status != "in_scope" and not reason:
            errors.append(f"{rid}: {status} without reason")
        verify = list(e.get("v") or [])
        if binding == "binding-ICH" and any(k in ICH_OTHER for k in keys):
            verify.append("[verify binding] EU/US adoption of " + ", ".join(k for k in keys if k in ICH_OTHER)
                          + " not checked by the research stems (C-06)")
        for r in recs:
            for item in r.get("verify") or []:
                verify.append(norm_verify(r["id"], item))
        if draft:
            verify.append("[verify] basis is draft guidance only - shown as DRAFT, never a binding step")
        verify = list(OrderedDict.fromkeys(verify))
        reqs.append(OrderedDict([
            ("id", rid), ("statement", e["s"]), ("party_norm", e["p"]),
            ("trigger", dflt("t")), ("action", e["a"]), ("deadline", dflt("d", "none")),
            ("recipient", dflt("r")), ("record", dflt("rec")),
            ("jurisdiction", jur), ("binding", binding), ("modal", modal), ("draft", draft), ("binding_route", route),
            ("findings", fl), ("l3_step", step), ("status", status), ("reason", reason),
            ("verify", verify),
        ]))

    # --- coverage and dup checks
    for fid, rl in f_to_req.items():
        if not rl:
            errors.append(f"finding {fid} not assigned to any REQ")
    for d, c in dup_of.items():
        if c in dup_of:
            errors.append(f"dup chain {d}->{c}->{dup_of[c]}")

    # --- merged findings
    merged = []
    for f in findings:
        rec = OrderedDict(f)
        rec["dup_of"] = dup_of.get(f["id"])
        rec["req"] = sorted(set(f_to_req[f["id"]]))
        merged.append(dict(rec))

    # --- req_to_step
    r2s = OrderedDict()
    for r in reqs:
        if r["status"] == "in_scope":
            r2s[r["id"]] = r["l3_step"]
        elif r["status"] == "interface":
            r2s[r["id"]] = {"status": "interface", "near_step": r["l3_step"], "reason": r["reason"]}
        else:
            r2s[r["id"]] = {"status": "out_of_scope", "reason": r["reason"]}

    # --- verification worklist
    index = parse_index()
    must = {f["id"] for f in findings if f["binding"] in ("binding-law", "binding-ICH") or (f.get("quote") or "").strip()}
    pool = sorted(f["id"] for f in findings if f["binding"] in ("guidance", "best-practice"))
    k = math.ceil(0.25 * len(pool))
    sample = sorted(random.Random(SEED).sample(pool, k))
    chosen = sorted(must | set(sample))
    items = []
    for fid in chosen:
        f = raw_map[fid]  # worklist = records as given to X1 (before corrections)
        items.append(OrderedDict([
            ("id", fid), ("src", f["src"]), ("doc", f["doc"]), ("url", f["url"]), ("loc", f["loc"]),
            ("page", f.get("page", "")), ("paraphrase", f["paraphrase"]), ("quote", f.get("quote", "")),
            ("local_text", local_text(f, index)),
        ]))
    n_bind = sum(1 for f in findings if f["binding"] in ("binding-law", "binding-ICH"))
    n_quote = sum(1 for f in findings if (f.get("quote") or "").strip())
    worklist = OrderedDict([
        ("meta", OrderedDict([
            ("purpose", "Input for blind verification X1: check each item's loc, page, paraphrase and quote against the source."),
            ("selection", "100% of binding-law and binding-ICH findings; every finding with a quote; "
                          "deterministic 25% sample of guidance and best-practice findings"),
            ("sample_method", "Python random.Random(seed).sample over the sorted guidance/best-practice ids, k = ceil(0.25 * n)"),
            ("seed", SEED),
            ("counts", OrderedDict([("binding_findings", n_bind), ("findings_with_quote", n_quote),
                                    ("guidance_best_practice_pool", len(pool)), ("sample_size", k),
                                    ("items_total", len(items))])),
            ("sampled_ids", sample),
            ("local_text_note", "path from vendor/sources/INDEX.md; null if no usable local copy"),
        ])),
        ("items", items),
    ])

    def dump(obj, path, header=""):
        def rep_od(dumper, data):
            return dumper.represent_dict(data.items())
        yaml.add_representer(OrderedDict, rep_od, Dumper=yaml.SafeDumper)
        text = yaml.safe_dump(obj, sort_keys=False, allow_unicode=True, width=10000, default_flow_style=False)
        path.write_text(header + text, encoding="utf-8")

    dump(reqs, SYN / "requirements.yaml",
         "# Requirements (Y1). Built by tools/y1_build.py from synthesis/requirements_src.yaml and research/*.yaml.\n"
         "# binding = strongest binding class of the REQ's findings; modal = strongest modal among the findings of that class\n"
         "# (must > should > may > definition > example); draft = true only if all strongest-class findings are draft;\n"
         "# l3_step = mapped step (in_scope) or the step that hands off to the placeholder (interface); null if out_of_scope.\n")
    dump(merged, SYN / "merged_findings.yaml",
         "# All research findings R1-R5 (537) plus dup_of (canonical finding id or null) and req (REQ ids). Records corrected after\n"
         "# X1 verification (synthesis/x1_corrections.yaml) carry an x1 field; all other records are unchanged research records.\n"
         "# dup_of marks a finding that restates the same obligation as the canonical finding of the same REQ without\n"
         "# adding trigger, deadline, recipient or record; it stays in the REQ's findings and source list.\n")
    dump(r2s, SYN / "req_to_step.yaml", "# REQ id -> L3 step (in_scope) or status with reason. Built by tools/y1_build.py.\n")
    dump(worklist, SYN / "verification_worklist.yaml",
         "# Verification worklist for X1 (blind). Contains source data only - nothing about the model.\n")

    # --- l3_cut.md markers
    l3 = (SYN / "l3_cut.md").read_text(encoding="utf-8")
    for step in STEPS:
        ins = [r for r in reqs if r["status"] == "in_scope" and r["l3_step"] == step]
        c = Counter(r["binding"] for r in ins)
        nd = sum(1 for r in ins if r["draft"])
        txt = (f"{len(ins)} REQs - binding-law {c['binding-law']}, binding-ICH {c['binding-ICH']}, "
               f"guidance {c['guidance']} (of which draft {nd}), best-practice {c['best-practice']}: "
               + ", ".join(r["id"] for r in ins))
        l3 = re.sub(rf"<!--REQS:{step}-->.*?<!--/REQS:{step}-->", f"<!--REQS:{step}-->{txt}<!--/REQS:{step}-->", l3, flags=re.S)
        ints = [r for r in reqs if r["status"] == "interface" and r["l3_step"] == step]
        itxt = ", ".join(f"{r['id']} ({r['action']})" for r in ints) or "none"
        l3 = re.sub(rf"<!--INTS:{step}-->.*?<!--/INTS:{step}-->", f"<!--INTS:{step}-->{itxt}<!--/INTS:{step}-->", l3, flags=re.S)
    (SYN / "l3_cut.md").write_text(l3, encoding="utf-8")

    # --- G2 self-check
    print("== G2 self-check ==")
    print(f"findings: {len(findings)}; REQs: {len(reqs)}")
    print("REQ by status:", dict(Counter(r["status"] for r in reqs)))
    print("REQ by binding:", dict(Counter(r["binding"] for r in reqs)), "draft:", sum(r["draft"] for r in reqs))
    bind = [r for r in reqs if r["binding"] in ("binding-law", "binding-ICH")]
    unmapped = [r["id"] for r in bind if not ((r["status"] == "in_scope" and r["l3_step"] in STEPS)
                                              or (r["status"] != "in_scope" and r["reason"]))]
    print(f"binding REQs: {len(bind)}; unmapped without reason: {unmapped or 'none'}")
    canon_no_req = [m["id"] for m in merged if m["dup_of"] is None and not m["req"]]
    dup_bad = [m["id"] for m in merged if m["dup_of"] and dup_of.get(m["dup_of"])]
    print(f"canonical findings without req: {canon_no_req or 'none'}; dup_of pointing to non-canonical: {dup_bad or 'none'}")
    print("dup_of count:", len(dup_of))
    for step in STEPS:
        ins = [r for r in reqs if r["status"] == "in_scope" and r["l3_step"] == step]
        c = Counter(r["binding"] for r in ins)
        print(f"  {step}: {len(ins):3d}  law {c['binding-law']:2d}  ICH {c['binding-ICH']:2d}  guid {c['guidance']:2d}"
              f" (draft {sum(r['draft'] for r in ins)})  bp {c['best-practice']:2d}")
    draft_binding = [r["id"] for r in reqs if r["draft"] and r["binding"] != "guidance"]
    print("draft REQs not guidance:", draft_binding or "none")
    print(f"worklist items: {len(items)} (binding {n_bind}, quotes {n_quote}, sample {k} of {len(pool)}, seed {SEED})")
    if errors:
        print("ERRORS:")
        for x in errors:
            print("  ", x)
        return 1
    print("structural checks: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
