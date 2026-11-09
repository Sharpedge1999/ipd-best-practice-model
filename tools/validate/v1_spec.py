#!/usr/bin/env python3
"""V1 layers L0 (contract), L2 (graph), L3 (auto rules) and L4 (traceability) on the frozen specs.

Independent of tools/lint_spec.py (own schema run, own reference resolution, own graph code).
Read-only on all inputs. Writes one JSON document (errors + passed checks + facts) to --out.

Usage: python -I tools/validate/v1_spec.py --out <json>
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, OrderedDict, defaultdict

import jsonschema
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STRENGTH = {"binding-law": 4, "binding-ICH": 3, "guidance": 2, "best-practice": 1, "verify-binding": 0}
ACT = ("task", "call-activity")
START = ("start", "start-message", "start-timer")
END = ("end",)
GW = ("xor-split", "xor-join", "and-split", "and-join", "or-split", "or-join")
SPLIT = ("xor-split", "and-split", "or-split")
JOIN = ("xor-join", "and-join", "or-join")
FAM = {t: t.split("-")[0] for t in GW}
PALETTE = set(ACT + START + END + ("xor-split", "xor-join", "and-split", "and-join"))
ERRORS = []
PASSED = []
FACTS = {}


def err(rule, layer, model, element, msg, severity="MUST", owner="B1", status="open", **kw):
    d = OrderedDict(rule_id=rule, layer=layer, model=model, element=element, message=msg, severity=severity,
                    owner=owner, status=status)
    d.update(kw)
    ERRORS.append(d)


def ok(layer, check, count, note=""):
    PASSED.append(OrderedDict(layer=layer, check=check, count=count, note=note))


def load(p):
    return yaml.safe_load(open(os.path.join(ROOT, p), encoding="utf-8"))


# ------------------------------------------------------------------ inputs
SPECS = OrderedDict()
SPEC_DIR = os.path.join(ROOT, "spec")
for _i, _a in enumerate(sys.argv):  # --spec-dir must be known before the module-level load (self-tests on seeded copies)
    if _a == "--spec-dir" and _i + 1 < len(sys.argv):
        SPEC_DIR = os.path.abspath(sys.argv[_i + 1])
for f in sorted(glob.glob(os.path.join(SPEC_DIR, "*.yaml"))):
    s = yaml.safe_load(open(f, encoding="utf-8"))
    SPECS[s["id"]] = s
SCHEMA = json.load(open(os.path.join(ROOT, "contracts", "spec.schema.json")))
REG = load("contracts/source_registry.yaml")
REGKEYS = {s["key"]: s for s in REG["sources"]}
REQS = OrderedDict((r["id"], r) for r in load("synthesis/requirements.yaml"))
FIND = OrderedDict((f["id"], f) for f in load("synthesis/merged_findings.yaml"))
GLOSS = load("synthesis/glossary.yaml")
NOTES = open(os.path.join(SPEC_DIR, "notes.md"), encoding="utf-8").read()
L3CUT = open(os.path.join(ROOT, "synthesis", "l3_cut.md"), encoding="utf-8").read()
FIND_BY_KEYLOC = defaultdict(list)
for f in FIND.values():
    FIND_BY_KEYLOC[(f["src"], f["loc"])].append(f)
INPUTS = ["spec/*.yaml (sha256 checked against spec/FROZEN.sha256)", "spec/notes.md", "contracts/spec.schema.json",
          "contracts/source_registry.yaml", "synthesis/requirements.yaml", "synthesis/merged_findings.yaml",
          "synthesis/glossary.yaml", "synthesis/l3_cut.md"]


def nodes(s):
    return OrderedDict((n["id"], n) for n in s["nodes"])


def pool_of(s, n):
    if n.get("pool"):
        return n["pool"]
    lanes = {l["id"]: l for l in s.get("lanes", [])}
    return lanes[n["lane"]]["pool"] if n.get("lane") in lanes else None


def endpoint_pool(s, ref):
    nd = nodes(s)
    if ref in nd:
        return pool_of(s, nd[ref])
    return ref if ref in {p["id"] for p in s["pools"]} else None


def traced(s):
    """Elements carrying trace fields: nodes and message flows."""
    for n in s["nodes"]:
        yield "node", n
    for m in s.get("message_flows", []):
        yield "message_flow", m


# ------------------------------------------------------------------ L0 contract
def l0():
    v = jsonschema.Draft202012Validator(SCHEMA)
    n_schema = 0
    for mid, s in SPECS.items():
        for e in sorted(v.iter_errors(s), key=lambda e: list(e.path)):
            err("SCHEMA", "L0", mid, "/".join(map(str, e.path)) or "-", e.message[:300])
        n_schema += 1
        # unique ids
        ids = Counter()
        for k in ("pools", "lanes", "nodes", "flows", "message_flows", "data", "groups", "annotations"):
            for x in s.get(k, []):
                ids[x["id"]] += 1
        for i, c in ids.items():
            if c > 1:
                err("ID-UNIQUE", "L0", mid, i, "id used %d times in the model" % c)
        nd = nodes(s)
        pools = {p["id"]: p for p in s["pools"]}
        lanes = {l["id"]: l for l in s.get("lanes", [])}
        fl = {f["id"] for f in s["flows"]}
        mfs = {m["id"] for m in s.get("message_flows", [])}
        allids = set(ids)
        for l in lanes.values():
            if l["pool"] not in pools:
                err("REF", "L0", mid, l["id"], "lane pool %s does not resolve" % l["pool"])
        for n in nd.values():
            if n.get("lane") and n["lane"] not in lanes:
                err("REF", "L0", mid, n["id"], "lane %s does not resolve" % n["lane"])
            if n.get("pool") and n["pool"] not in pools:
                err("REF", "L0", mid, n["id"], "pool %s does not resolve" % n["pool"])
            if n.get("pool") and any(l["pool"] == n["pool"] for l in lanes.values()):
                err("REF", "L0", mid, n["id"], "node placed on pool %s which has lanes (S0-09)" % n["pool"])
            p = pool_of(s, n)
            if p and not pools[p]["expanded"]:
                err("REF", "L0", mid, n["id"], "node in collapsed pool %s (S0-09)" % p)
            if n["type"] == "call-activity" and n.get("calls"):
                if n["calls"] not in SPECS:
                    err("REF", "L0", mid, n["id"], "calls %s: no such spec" % n["calls"])
        for f in s["flows"]:
            for k in ("from", "to"):
                if f[k] not in nd:
                    err("REF", "L0", mid, f["id"], "flow %s %s does not resolve" % (k, f[k]))
        for m in s.get("message_flows", []):
            for k in ("from", "to"):
                if m[k] not in nd and m[k] not in pools:
                    err("REF", "L0", mid, m["id"], "message flow %s %s does not resolve" % (k, m[k]))
        for d in s.get("data", []):
            for a in d["assoc"]:
                if a["node"] not in nd:
                    err("REF", "L0", mid, d["id"], "data assoc %s does not resolve" % a["node"])
        for g in s.get("groups", []):
            for x in g["members"]:
                if x not in nd:
                    err("REF", "L0", mid, g["id"], "group member %s does not resolve" % x)
            if any(n.get("group") not in (None, g["id"]) for x in g["members"] for n in [nd.get(x, {})]):
                pass
        for n in nd.values():
            if n.get("group"):
                g = [g for g in s.get("groups", []) if g["id"] == n["group"]]
                if not g or n["id"] not in g[0]["members"]:
                    err("REF", "L0", mid, n["id"], "node group %s not consistent with groups[].members" % n["group"])
        for g in s.get("groups", []):
            for x in g["members"]:
                if nd.get(x, {}).get("group") != g["id"]:
                    err("REF", "L0", mid, x, "member of %s but node.group is %r" % (g["id"], nd.get(x, {}).get("group")),
                        severity="SHOULD")
        for a in s.get("annotations", []):
            for x in a["assoc"]:
                if x not in nd and x not in fl:
                    err("REF", "L0", mid, a["id"], "annotation assoc %s does not resolve" % x)
        for r in s.get("rule_exceptions", []):
            if r["element"] not in allids:
                err("REF", "L0", mid, r["element"], "rule_exception element does not resolve")
        itf = s.get("interface") or {}
        for k in ("start", "ends"):
            for x in itf.get(k, []):
                if x not in nd:
                    err("REF", "L0", mid, x, "interface.%s does not resolve" % k)
        for x in itf.get("message_flows", []):
            if x not in mfs:
                err("REF", "L0", mid, x, "interface.message_flows does not resolve")
        par = s.get("parent")
        if par:
            if par["model"] not in SPECS or par["node"] not in nodes(SPECS[par["model"]]):
                err("REF", "L0", mid, "parent", "parent %s does not resolve" % par)
        # src keys, REQ ids, src {key, loc} vs findings of the element's REQs
        def check_src(kind, el, where, need_finding=False):
            for x in el.get("src", []):
                if x["key"] not in REGKEYS:
                    err("SRC-KEY", "L0", mid, where, "src key %s not in source_registry.yaml" % x["key"])
                elif need_finding and (x["key"], x["loc"]) not in FIND_BY_KEYLOC:
                    err("SRC-LOC", "L0", mid, where, "%s src %s %s has no finding with that key and loc" % (kind, x["key"], x["loc"]))
        for p in s["pools"]:
            check_src("pool", p, p["id"], True)
        for l in s.get("lanes", []):
            check_src("lane", l, l["id"], True)
        for d in s.get("data", []):
            check_src("data", d, d["id"], True)
        for a in s.get("annotations", []):
            check_src("annotation", a, a["id"], True)
        for kind, el in traced(s):
            check_src(kind, el, el["id"])
            for q in el.get("req", []):
                if q not in REQS:
                    err("REQ-ID", "L0", mid, el["id"], "REQ %s not in requirements.yaml" % q)
            # findings behind REQs
            fids = []
            for q in el.get("req", []):
                fids += REQS.get(q, {}).get("findings", [])
            fset = [FIND[i] for i in OrderedDict.fromkeys(fids) if i in FIND]
            for i in fids:
                if i not in FIND:
                    err("FINDING-ID", "L0", mid, el["id"], "finding %s of its REQs not in merged_findings" % i, owner="Y1")
            if not el.get("req"):
                # no REQs: every src pair must at least exist in some finding
                for x in el.get("src", []):
                    if (x["key"], x["loc"]) not in FIND_BY_KEYLOC:
                        err("SRC-LOC", "L0", mid, el["id"], "src %s %s has no finding with that key and loc" % (x["key"], x["loc"]))
                continue
            pairs = {(f["src"], f["loc"]) for f in fset}
            keys = {f["src"] for f in fset}
            for x in el.get("src", []):
                kl = (x["key"], x["loc"])
                if kl not in pairs:
                    if x["key"] in keys:
                        alts = sorted({f["loc"] for f in fset if f["src"] == x["key"]})
                        err("SRC-LOC", "L0", mid, el["id"], "src %s loc %r not among the findings of its REQs (loc mismatch; REQ findings give %s)"
                            % (x["key"], x["loc"], alts))
                    else:
                        err("SRC-LOC", "L0", mid, el["id"], "src %s %s not backed by any finding of its REQs" % kl)
                    continue
                # pages: every finding page for the pair must be in the spec page; nothing else
                pages = list(OrderedDict.fromkeys(f["page"] for f in fset if (f["src"], f["loc"]) == kl and f.get("page")))
                sp = x.get("page", "")
                rest = sp
                for pg in sorted(pages, key=len, reverse=True):
                    if pg not in sp:
                        err("SRC-PAGE", "L0", mid, el["id"], "src %s %s: finding page %r missing from spec page" % (kl[0], kl[1], pg),
                            severity="SHOULD")
                    rest = rest.replace(pg, "")
                if rest.replace(";", "").strip():
                    err("SRC-PAGE", "L0", mid, el["id"], "src %s %s: spec page has text %r not found in any finding page" % (kl[0], kl[1], rest.strip()),
                        severity="SHOULD")
    ok("L0", "spec schema (jsonschema Draft 2020-12, own run, contracts/spec.schema.json)", n_schema)
    n_ids = sum(len(s.get(k, [])) for s in SPECS.values() for k in ("pools", "lanes", "nodes", "flows", "message_flows", "data", "groups", "annotations"))
    ok("L0", "ids unique within each model (all id kinds)", n_ids)
    n_ref = sum(2 * len(s["flows"]) + 2 * len(s.get("message_flows", [])) + len(s["nodes"]) + sum(len(d["assoc"]) for d in s.get("data", []))
                + sum(len(g["members"]) for g in s.get("groups", [])) + len(s.get("rule_exceptions", [])) for s in SPECS.values())
    ok("L0", "references resolve (lanes, pools, flows, message flows, data, groups, annotations, rule_exceptions, interface, parent, calls)", n_ref)
    n_src = sum(len(el.get("src", [])) for s in SPECS.values() for k in ("pools", "lanes", "nodes", "message_flows", "data", "annotations") for el in s.get(k, []))
    ok("L0", "src keys in contracts/source_registry.yaml; src {key, loc} pairs among the findings behind the element's REQs (or in some finding for elements without REQs)", n_src)
    n_req = sum(len(el.get("req", [])) for s in SPECS.values() for _, el in traced(s))
    ok("L0", "REQ ids exist in synthesis/requirements.yaml; their findings exist in merged_findings.yaml", n_req)


# ------------------------------------------------------------------ graph helpers
def process_graphs(s):
    """One graph per expanded pool: {pool: (node ids, succ, pred)}."""
    nd = nodes(s)
    g = OrderedDict()
    for p in s["pools"]:
        if p["expanded"]:
            g[p["id"]] = ([i for i, n in nd.items() if pool_of(s, n) == p["id"]], defaultdict(list), defaultdict(list))
    for f in s["flows"]:
        if f["from"] not in nd or f["to"] not in nd:
            continue  # reported as REF in L0
        pf, pt = pool_of(s, nd[f["from"]]), pool_of(s, nd[f["to"]])
        if pf not in g or pt not in g:
            continue  # node in a collapsed or unknown pool: reported in L0
        if pf != pt:
            err("ROL-02", "L3", s["id"], f["id"], "sequence flow crosses pools %s -> %s" % (pf, pt))
            continue
        g[pf][1][f["from"]].append(f["to"])
        g[pf][2][f["to"]].append(f["from"])
    return g


def dominators(nodes_, succ, pred, entry):
    allset = set(nodes_) | {entry}
    dom = {n: set(allset) for n in nodes_}
    dom[entry] = {entry}
    changed = True
    while changed:
        changed = False
        for n in nodes_:
            ps = pred[n]
            new = {n} | (set.intersection(*[dom[p] for p in ps]) if ps else set())
            if new != dom[n]:
                dom[n] = new
                changed = True
    return dom


def reduce_blocks(s, pid, node_ids, succ, pred):
    """Reduction-based block-structure check (FLW-04 with DEC-06 pruning). Returns remaining gateways."""
    nd = nodes(s)
    dec06 = {r["element"] for r in s.get("rule_exceptions", []) if r["rule"] == "DEC-06"}
    kind = {i: nd[i]["type"] for i in node_ids}
    S = {i: list(succ[i]) for i in node_ids}
    P = {i: list(pred[i]) for i in node_ids}
    alive = set(node_ids)
    terminal = {i for i in node_ids if kind[i] in END}
    notes = []
    changed = True
    while changed:
        changed = False
        # sequence reduction
        for i in list(alive):
            if kind[i] in START or i in terminal:
                continue
            if len(P[i]) == 1 and len(S[i]) == 1 and S[i][0] != i:
                a, b = P[i][0], S[i][0]
                S[a] = [b if x == i else x for x in S[a]]
                P[b] = [a if x == i else x for x in P[b]]
                alive.discard(i)
                changed = True
                break
        if changed:
            continue
        # block reduction: split whose outs all go to one join whose ins all come from it
        for i in list(alive):
            if kind[i] in SPLIT and len(S[i]) >= 2 and len(set(S[i])) == 1:
                j = S[i][0]
                if kind.get(j) in JOIN and set(P[j]) == {i} and len(P[j]) == len(S[i]):
                    if FAM[kind[i]] != FAM[kind[j]]:
                        rule = "FLW-08" if (FAM[kind[i]] != "and" and FAM[kind[j]] == "and") else "FLW-04"
                        err(rule, "L2", s["id"], j, "%s %s is closed by %s %s" % (kind[i], i, kind[j], j))
                    # contract i,j into i
                    S[i] = list(S[j])
                    for b in S[j]:
                        P[b] = [i if x == j else x for x in P[b]]
                    alive.discard(j)
                    kind[i] = "merged"
                    changed = True
                    break
        if changed:
            continue
        # DEC-06 pruning: XOR split with DEC-06 drops branches that end in a terminal
        for i in list(alive):
            if i in dec06 and kind[i] == "xor-split":
                keep = []
                pruned = []
                for b in S[i]:
                    if b in terminal and len(P[b]) == 1:
                        pruned.append(b)
                    else:
                        keep.append(b)
                if pruned:
                    for b in pruned:
                        alive.discard(b)
                    S[i] = keep
                    notes.append("%s: DEC-06 branch(es) to %s" % (i, ",".join(pruned)))
                    if not keep:
                        terminal.add(i)
                    changed = True
                    break
    # a DEC-06 split whose branches all ended in their own end events has become a terminal: structured
    leftover = [i for i in alive if i not in terminal and (kind[i] in GW or (kind[i] == "merged" and len(S[i]) > 1))]
    # every start must now lead straight to terminals (anything else is an unreduced fragment)
    for i in alive:
        if kind[i] in START and any(b not in terminal for b in S[i]) and not leftover:
            leftover.append(i)
    return leftover, notes


def l2():
    n_proc = 0
    for mid, s in SPECS.items():
        nd = nodes(s)
        dec05 = {r["element"] for r in s.get("rule_exceptions", []) if r["rule"] == "DEC-05"}
        dec06 = {r["element"] for r in s.get("rule_exceptions", []) if r["rule"] == "DEC-06"}
        graphs = process_graphs(s)
        for pid, (ids, succ, pred) in graphs.items():
            n_proc += 1
            starts = [i for i in ids if nd[i]["type"] in START]
            ends = [i for i in ids if nd[i]["type"] in END]
            if not starts:
                err("FLW-09", "L2", mid, pid, "process without start event")
            if not ends:
                err("FLW-09", "L2", mid, pid, "process without end event")
            # FLW-09 in/out of events
            for i in starts:
                if pred[i]:
                    err("FLW-09", "L2", mid, i, "start event has incoming sequence flow")
                if len(succ[i]) != 1:
                    err("FLW-03", "L2", mid, i, "start event has %d outgoing sequence flows" % len(succ[i]))
            for i in ends:
                if succ[i]:
                    err("FLW-09", "L2", mid, i, "end event has outgoing sequence flow")
                if len(pred[i]) != 1:
                    err("FLW-03", "L2", mid, i, "end event has %d incoming sequence flows (implicit join)" % len(pred[i]))
            # FLW-03 activities
            for i in ids:
                t = nd[i]["type"]
                if t in ACT and (len(pred[i]) != 1 or len(succ[i]) != 1):
                    err("FLW-03", "L2", mid, i, "activity has %d incoming / %d outgoing sequence flows" % (len(pred[i]), len(succ[i])))
                if t in GW:
                    ins, outs = len(pred[i]), len(succ[i])
                    if t in SPLIT and not (ins == 1 and outs >= 2):
                        err("FLW-04", "L2", mid, i, "%s with %d in / %d out (a split needs 1 in, >= 2 out)" % (t, ins, outs))
                    if t in JOIN and not (ins >= 2 and outs == 1):
                        err("FLW-04", "L2", mid, i, "%s with %d in / %d out (a join needs >= 2 in, 1 out)" % (t, ins, outs))
            # reachability
            seen = set()
            stack = list(starts)
            while stack:
                x = stack.pop()
                if x in seen:
                    continue
                seen.add(x)
                stack += succ[x]
            for i in ids:
                if i not in seen:
                    err("REACH", "L2", mid, i, "not reachable from a start event")
            back = set()
            stack = list(ends)
            while stack:
                x = stack.pop()
                if x in back:
                    continue
                back.add(x)
                stack += pred[x]
            for i in ids:
                if i not in back:
                    err("REACH", "L2", mid, i, "no end event reachable")
            # joins: immediate dominator must be a split of the same family (FLW-04 / FLW-08)
            if starts:
                entry = "__entry__"
                succ2 = defaultdict(list, {k: list(v) for k, v in succ.items()})
                pred2 = defaultdict(list, {k: list(v) for k, v in pred.items()})
                for st in starts:
                    pred2[st].append(entry)
                dom = dominators(ids, succ2, pred2, entry)
                for j in ids:
                    t = nd[j]["type"]
                    if t in JOIN:
                        cands = [d for d in dom[j] if d != j and d != entry]
                        # immediate dominator = the dominator dominated by all others
                        idom = None
                        for d in cands:
                            if all(c in dom[d] for c in cands):
                                idom = d
                        if idom is None or nd[idom]["type"] not in SPLIT:
                            # find nearest split dominator
                            sd = [d for d in cands if nd[d]["type"] in SPLIT]
                            near = None
                            for d in sd:
                                if all(c in dom[d] for c in sd):
                                    near = d
                            idom = near
                        if idom is None:
                            err("FLW-04", "L2", mid, j, "join without a dominating split")
                        elif FAM[nd[idom]["type"]] != FAM[t]:
                            rule = "FLW-08" if FAM[t] == "and" else "FLW-04"
                            err(rule, "L2", mid, j, "%s %s joins branches opened by %s %s" % (t, j, nd[idom]["type"], idom))
            left, pruned = reduce_blocks(s, pid, ids, succ, pred)
            for g in left:
                if g in dec05:
                    err("FLW-04", "L2", mid, g, "unstructured fragment (DEC-05 annotated)", severity="SHOULD", status="documented-exception")
                else:
                    err("FLW-04", "L2", mid, g, "block structure not reducible at this gateway (no matching join; no DEC-05/DEC-06 annotation covers it)")
            FACTS.setdefault("dec06_pruned", {})["%s/%s" % (mid, pid)] = pruned
        # DEC-06 annotations that are not needed or wrong
        for g in dec06:
            n = nd.get(g)
            if not n or n["type"] != "xor-split":
                if n and n["type"] in END:
                    continue
                err("DEC-06", "L2", mid, g, "DEC-06 annotation on a non-XOR element", severity="SHOULD")
    ok("L2", "reachability, FLW-03, FLW-04 (reduction + dominator), FLW-08, FLW-09 per process", n_proc)


# ------------------------------------------------------------------ L3 auto rules
# Reviewed lexicon of English verbs in base (imperative) form used in business process labels. A first word
# outside it is reported for a manual look (SHOULD); a first word that is clearly an action noun or gerund is MUST.
VERB_LEXICON = set("""
accept address adapt adjust agree allocate analyse analyze approve archive assess assign audit build calculate capture
categorise categorize characterise characterize check classify close collect communicate compile complete conduct configure
confirm consider consult correct create decide define deliver describe design detect determine develop deviate document
draft enter escalate establish estimate evaluate examine explain file finalise finalize flag handle identify implement
inform initiate instruct investigate keep link list log maintain manage map measure monitor notify obtain perform plan
prepare prioritise prioritize provide publish rate receive reconcile record reject remediate report request resolve retain
retrain review revise run schedule secure select send set sign specify submit summarise summarize track train transfer
update upload validate verify write
""".split())
INTRANSITIVE = {"deviate", "agree"}  # verbs that take no direct object; "verb + to ..." then lacks the object of LBL-01
PARTICIPLE_IRREG = {"done", "met", "set", "taken", "given", "written", "made", "held", "sent", "begun", "found", "known",
                    "shown", "run", "brought", "kept", "left", "built", "drawn", "chosen", "seen", "paid", "led"}


def is_participle(w):
    w = w.lower().strip(".,")
    return w.endswith("ed") or w in PARTICIPLE_IRREG


VERBS = None


def l3():
    global VERBS
    label_types = defaultdict(set)
    label_where = defaultdict(list)
    for mid, s in SPECS.items():
        nd = nodes(s)
        pools = {p["id"]: p for p in s["pools"]}
        expanded = [p for p in s["pools"] if p["expanded"]]
        acts = [n for n in nd.values() if n["type"] in ACT]
        nn = len(nd)
        n_el = nn + len(s.get("data", [])) + len(s.get("annotations", []))
        FACTS.setdefault("size", {})[mid] = dict(activities=len(acts), nodes=nn, elements=n_el,
                                                 flows=len(s["flows"]), message_flows=len(s.get("message_flows", [])),
                                                 gateway_types=sorted({FAM[n["type"]] for n in nd.values() if n["type"] in GW}))
        # SCP-03 / SCP-04
        documented = ("SCP-03, %s" % mid) in NOTES
        if not (5 <= len(acts) <= 15) or nn > 31:
            err("SCP-03", "L3", mid, "-", "%d activities, %d nodes (target 5-15 activities, <= 31 nodes)" % (len(acts), nn),
                severity="SHOULD", status="documented-deviation" if documented else "open")
        if n_el > 50:
            err("SCP-04", "L3", mid, "-", "%d elements > 50" % n_el)
        # FLW-01 palette
        for n in nd.values():
            t = n["type"]
            if t in ("or-split", "or-join"):
                continue  # DEC-02 exception, checked under FLW-07
            if t not in PALETTE:
                ex = [r for r in s.get("rule_exceptions", []) if r["rule"] == "FLW-01" and r["element"] == n["id"]]
                if not ex:
                    err("FLW-01", "L3", mid, n["id"], "node type %s outside the descriptive palette" % t)
        # FLW-06
        for n in nd.values():
            if n["type"] in SPLIT:
                k = sum(1 for f in s["flows"] if f["from"] == n["id"])
                if k > 3:
                    err("FLW-06", "L3", mid, n["id"], "%d branches > 3" % k, severity="SHOULD")
            if n["type"] in JOIN:
                k = sum(1 for f in s["flows"] if f["to"] == n["id"])
                if k > 3:
                    err("FLW-06", "L3", mid, n["id"], "join of %d branches > 3" % k, severity="SHOULD")
        gtypes = FACTS["size"][mid]["gateway_types"]
        if len(gtypes) >= 3:
            err("FLW-06", "L3", mid, "-", "%d gateway types %s" % (len(gtypes), gtypes), severity="SHOULD",
                status="documented-deviation" if "FLW-06" in NOTES else "open")
        # FLW-07
        for n in nd.values():
            if n["type"] == "or-split":
                outs = [f for f in s["flows"] if f["from"] == n["id"]]
                d = [f for f in outs if f.get("default")]
                if not n.get("justification"):
                    err("FLW-07", "L3", mid, n["id"], "OR split without justification", severity="SHOULD")
                if len(d) != 1:
                    # round 3: a documented SHOULD deviation ('- FLW-07, <model> <gateway>:' in notes.md section 8) is reported as documented
                    dm = re.search(r"- FLW-07, %s %s: ([^\n]*)" % (re.escape(mid), re.escape(n["id"])), NOTES)
                    err("FLW-07", "L3", mid, n["id"], "OR split with %d default flows (needs exactly 1)%s" % (
                        len(d), ("; documented SHOULD deviation in notes.md section 8: " + dm.group(1)) if dm else ""),
                        severity="SHOULD", status="documented-deviation" if dm else "open")
                # round 3: default-path check. The default flow of an inclusive gateway runs only when no other condition holds
                # (OMG BPMN 2.0.2 10.6.3), so a default path must not carry work that has to run together with a true branch.
                # Safe form: the default flow goes straight to the OR join that every other branch reaches.
                succ = defaultdict(list)
                for ff in s["flows"]:
                    succ[ff["from"]].append(ff["to"])

                def reach(start):
                    seen, st = set(), [start]
                    while st:
                        x = st.pop()
                        if x in seen:
                            continue
                        seen.add(x)
                        st.extend(succ[x])
                    return seen
                for f in d:
                    tgt = nd[f["to"]]
                    others = [o for o in outs if not o.get("default")]
                    if tgt["type"] == "or-join" and all(f["to"] in reach(o["to"]) for o in others):
                        FACTS.setdefault("or_default_paths", []).append("%s %s %s %r -> OR join %s (empty default path)" % (mid, n["id"], f["id"], f.get("label"), f["to"]))
                    else:
                        err("FLW-07", "L3", mid, f["id"], "default flow %s %r of OR split %s leads to %s %r, not straight to the OR join of the split; the "
                            "default runs only when no other condition holds (OMG BPMN 2.0.2 10.6.3), so %s is skipped whenever another branch is "
                            "taken - check that it never has to run together with the other branches" % (
                                f["id"], f.get("label"), n["id"], f["to"], tgt.get("label") or tgt["type"], f["to"]))
                # OMG 10.6.3: the default flow of an inclusive gateway is taken only if no other condition is true
                for f in d:
                    if re.search(r"\b(always|in all cases|every time|in any case)\b", f.get("label") or "", re.I):
                        others = [o.get("label") or o["to"] for o in outs if not o.get("default")]
                        err("FLW-07", "L3", mid, f["id"], "default flow %s %r of OR split %s is labelled as unconditional, but an inclusive gateway takes its "
                            "default flow only when no other outgoing condition is true (OMG BPMN 2.0.2 10.6.3): whenever %s holds, %s is NOT started. "
                            "Repair: make %s a conditional (non-default) flow that is always true and state the FLW-07 SHOULD deviation (no default needed "
                            "because one path is always taken), or keep the AND split with the reading convention."
                            % (f["id"], f.get("label"), n["id"], others, f["to"], f["id"]))
        for f in s["flows"]:
            if f.get("default") and nd[f["from"]]["type"] not in ("xor-split", "or-split"):
                err("FLW-02", "L3", mid, f["id"], "default flow on a %s" % nd[f["from"]]["type"], severity="SHOULD")
        # LBL-01 / LBL-02 / LBL-03
        for n in nd.values():
            t, lab = n["type"], n.get("label")
            if lab:
                construct = "event" if t in START + END else ("gateway" if t in GW else t)
                label_types[lab].add(construct)
                label_where[lab].append("%s %s" % (mid, n["id"]))
            if t in ACT:
                if ":" in lab or "—" in lab:
                    err("LBL-01", "L3", mid, n["id"], "activity label %r contains ':' or em dash" % lab)
                ws = lab.split()
                w0 = ws[0]
                if w0.lower() in VERB_LEXICON and w0[0].isupper():
                    pass
                elif w0.lower().endswith(("tion", "ment", "ance", "ing", "al", "sis")) or not w0[0].isupper():
                    err("LBL-01", "L3", mid, n["id"], "activity label %r does not start with an imperative verb (action noun or gerund)" % lab)
                else:
                    err("LBL-01", "L3", mid, n["id"], "first word of %r not in the reviewed verb lexicon; check that it is an imperative verb" % lab,
                        severity="SHOULD")
                if len(ws) < 2:
                    err("LBL-01", "L3", mid, n["id"], "activity label %r has no object" % lab)
                elif w0.lower() in INTRANSITIVE and ws[1].lower() in ("to", "on", "with", "from"):
                    err("LBL-01", "L3", mid, n["id"], "activity label %r has no direct object (intransitive verb + %r); e.g. name what is deviated from" % (lab, ws[1]),
                        severity="SHOULD")
            if t in START + END:
                ws = lab.split()
                if not any(is_participle(w) for w in ws):
                    err("LBL-02", "L3", mid, n["id"], "event label %r has no past participle (state)" % lab)
                if ws and ws[0].lower() in VERBS:
                    err("LBL-02", "L3", mid, n["id"], "event label %r starts with an imperative verb" % lab)
            if t in ("xor-split", "or-split"):
                if not lab or not lab.endswith("?"):
                    err("LBL-03", "L3", mid, n["id"], "split label %r does not end with '?'" % lab)
                outs = [f for f in s["flows"] if f["from"] == n["id"]]
                for f in outs:
                    if not (f.get("label") or "").strip():
                        err("LBL-03", "L3", mid, f["id"], "outgoing flow of split %s without answer label" % n["id"])
                labs = [f.get("label") for f in outs]
                if len(set(labs)) != len(labs):
                    err("LBL-03", "L3", mid, n["id"], "duplicate answer labels %s" % labs)
            if t in JOIN + ("and-split",) and lab:
                err("LBL-03", "L3", mid, n["id"], "%s carries a label (S0-14 convention)" % t, severity="SHOULD")
        for f in s["flows"]:
            if f.get("label") and nd[f["from"]]["type"] not in ("xor-split", "or-split"):
                err("LBL-03", "L3", mid, f["id"], "label %r on a flow that does not leave a split" % f["label"], severity="SHOULD")
        # end event labels unique per process
        per = defaultdict(list)
        for n in nd.values():
            if n["type"] in END:
                per[(pool_of(s, n), n["label"])].append(n["id"])
        for (p, lab), ids_ in per.items():
            if len(ids_) > 1:
                err("FLW-09", "L2", mid, ",".join(ids_), "several end events with the same outcome %r in %s" % (lab, p))
        # ROL-01 lanes
        gl = {l["lane_id"]: l for l in GLOSS["lane_roles"]}
        for l in s.get("lanes", []):
            g = gl.get(l["id"])
            if not g or g["name"] != l["name"] or g["pool"] != l["pool"]:
                err("ROL-01", "L3", mid, l["id"], "lane %r not a glossary lane role (glossary.yaml lane_roles)" % l["name"])
            if not l.get("src"):
                err("ROL-01", "L3", mid, l["id"], "lane without src")
        for p in s["pools"]:
            gp = [x for x in GLOSS["pools"] if x["id"] == p["id"]]
            if not gp or gp[0]["name"] != p["name"] or gp[0]["kind"] != p["kind"]:
                err("LBL-05", "L3", mid, p["id"], "pool id/name/kind differs from glossary pools")
        # ROL-02 message flows
        for m in s.get("message_flows", []):
            pf, pt = endpoint_pool(s, m["from"]), endpoint_pool(s, m["to"])
            if pf == pt:
                err("ROL-02", "L3", mid, m["id"], "message flow inside pool %s" % pf)
            for k in ("from", "to"):
                x = nd.get(m[k])
                if x and x["type"] in GW:
                    err("ROL-02", "L3", mid, m["id"], "message flow %s attaches to gateway %s" % (k, m[k]))
                if m[k].startswith("L_"):
                    err("ROL-02", "L3", mid, m["id"], "message flow attaches to lane %s" % m[k])
            x = nd.get(m["to"])
            if x and x["type"] in START and x["type"] != "start-message":
                err("ROL-02", "L3", mid, m["id"], "message flow into %s start event %s (not a message start)" % (x["type"], x["id"]))
            if x and x["type"] in END:
                err("ROL-02", "L3", mid, m["id"], "message flow into end event %s" % x["id"])
            y = nd.get(m["from"])
            if y and y["type"] in START:
                err("ROL-02", "L3", mid, m["id"], "message flow out of start event %s" % y["id"])
            if y and y["type"] in END:
                err("ROL-02", "L3", mid, m["id"], "message flow out of a none end event %s" % y["id"])
        for n in nd.values():
            if n["type"] == "start-message":
                inc = [m for m in s.get("message_flows", []) if m["to"] == n["id"]]
                if not inc:
                    err("ROL-02", "L3", mid, n["id"], "message start event without incoming message flow", severity="SHOULD")
                labels = sorted({m["label"] for m in inc})
                if len(labels) > 1:
                    origin = (" The combined start is prescribed by synthesis/l3_cut.md (%s), so the repair needs an orchestrator decision: "
                              "either one message start event per trigger in the Sponsor process (the routing gateway after S1 then disappears; "
                              "interface.start and the l3_cut trigger list both starts), or an explicit, named exception to FLW-09 (precedence rule of bpmn-design-criteria)."
                              % ("A3 trigger line" if n["label"] in L3CUT else "not named there")) if n["label"] in L3CUT else ""
                    exc = [r for r in s.get("rule_exceptions", []) if r["rule"] == "FLW-09" and r["element"] == n["id"]]
                    if exc:
                        err("FLW-09", "L2", mid, n["id"], "one start event %r receives %d message types %s; documented rule exception accepted by the "
                            "orchestrator (rule_exceptions FLW-09, conflicts.md C-27: one business trigger, revisitable by the user)"
                            % (n["label"], len(labels), labels), status="documented-exception")
                    else:
                        err("FLW-09", "L2", mid, n["id"], "one start event %r receives %d different triggers %s; FLW-09 requires one start event per trigger.%s"
                            % (n["label"], len(labels), labels, origin))
        # expanded external pools: ROL-03 exception recorded
        for p in s["pools"]:
            if p["kind"] == "external" and p["expanded"]:
                if not any(r["rule"] == "ROL-03" and r["element"] == p["id"] for r in s.get("rule_exceptions", [])):
                    err("ROL-03", "L3", mid, p["id"], "expanded external pool without ROL-03 rule_exception", severity="SHOULD")
            if p["kind"] == "external" and not p["expanded"] and any(r["rule"] == "ROL-03" and r["element"] == p["id"] for r in s.get("rule_exceptions", [])):
                err("ROL-03", "L3", mid, p["id"], "ROL-03 exception recorded for a collapsed pool", severity="SHOULD")
            if not p["expanded"]:
                used = [m for m in s.get("message_flows", []) if p["id"] in (m["from"], m["to"])]
                if not used:
                    # by design: every model repeats the same external pools (workflow_plan section 4, LBL-05); fact only
                    FACTS.setdefault("collapsed_pools_without_message_flow", []).append("%s %s" % (mid, p["id"]))
        # CHARS / bare CTR in every string
        def walk(o, path):
            if isinstance(o, dict):
                for k, v in o.items():
                    walk(v, path + "/" + str(k))
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, path + "/%d" % i)
            elif isinstance(o, str):
                if "—" in o or "·" in o:
                    err("CHARS", "L3", mid, path, "em dash or middle dot in %r" % o[:80])
                if re.search(r"(?<![A-Za-z])CTR(?![A-Za-z])", o) and not re.search(r"EU CTR", o):
                    err("TERM-CTR", "L3", mid, path, "bare 'CTR' in %r" % o[:80], severity="SHOULD")
        walk(s, "")
    # LBL-05 label used for more than one construct (start and end events count as one construct: a hand-off state)
    for lab, ts in label_types.items():
        if len(ts) > 1:
            if ts == {"call-activity", "task"}:
                msg = ("label %r names both a whole L3 step (call activity) and one task inside its child model; "
                       "one name for two different things - give the task a narrower name" % lab)
            else:
                msg = "label %r used for different constructs %s" % (lab, sorted(ts))
            err("LBL-05", "L3", "*", "; ".join(label_where[lab]), msg, severity="SHOULD")
    # SCP-07 duplicated task labels across models (same step modelled twice); same-model duplicates in different pools are facts
    tasks = defaultdict(list)
    for mid, s in SPECS.items():
        for n in s["nodes"]:
            if n["type"] == "task":
                tasks[n["label"].lower()].append((mid, n["id"], pool_of(s, n)))
    n_tasks = sum(len(v) for v in tasks.values())
    for lab, where in tasks.items():
        models = {w[0] for w in where}
        if len(models) > 1:
            err("SCP-07", "L3", "*", "; ".join("%s %s" % w[:2] for w in where),
                "task %r modelled in %d models (reuse via call activity or distinct names)" % (lab, len(models)), severity="SHOULD")
        elif len(where) > 1:
            FACTS.setdefault("same_label_tasks_in_one_model", []).append("; ".join("%s %s (%s)" % w for w in where) + " %r" % lab)
    ok("L3", "SCP-07 no task label repeated across models", n_tasks)
    # notes.md section 8 statements that no longer match the specs (stale SHOULD deviations)
    m = re.search(r"- FLW-06: ([^\n]*)", NOTES)
    if m:
        named = re.findall(r"L4-0\d", m.group(1))
        stale = [x for x in named if x in FACTS["size"] and len(FACTS["size"][x]["gateway_types"]) < 3]
        if stale:
            err("NOTES", "L3", ",".join(stale), "notes.md section 8",
                "FLW-06 deviation says these models use three gateway types, but they use %s; remove or correct the stale line"
                % "; ".join("%s %s" % (x, "/".join(FACTS["size"][x]["gateway_types"])) for x in stale), severity="SHOULD")
    # L3 call activity label vs L4 title (LBL-05)
    l3 = SPECS["L3"]
    for n in l3["nodes"]:
        if n["type"] == "call-activity" and n.get("calls"):
            c = SPECS.get(n["calls"])
            if c and c["title"] != n["label"]:
                err("LBL-05", "L3", "L3", n["id"], "call activity label %r != called model title %r" % (n["label"], c["title"]))
    ok("L3", "SCP-03/04, FLW-01/06/07, LBL-01/02/03 (heuristics), ROL-01/02, CHARS per model", len(SPECS))
    orsplits = ["%s %s" % (m, n["id"]) for m, s in SPECS.items() for n in s["nodes"] if n["type"] == "or-split"]
    bad_default = [e for e in ERRORS if e["rule_id"] == "FLW-07" and ("not straight to the OR join" in e["message"] or "labelled as unconditional" in e["message"])]
    if not bad_default:
      ok("L3", "FLW-07 OR default-flow check (round 3, OMG 10.6.3): every OR split listed; every default flow goes straight to the OR join that all "
       "other branches reach (empty default path), so no default path carries work that must run together with a true branch; "
       "no default labelled as unconditional", len(orsplits),
       note="OR splits: %s; default paths: %s" % (", ".join(orsplits) or "none", "; ".join(FACTS.get("or_default_paths", [])) or "none"))


def scp06():
    l3 = SPECS["L3"]
    nd3 = nodes(l3)
    n_ok = 0
    for n in l3["nodes"]:
        if n["type"] != "call-activity" or not n.get("calls"):
            continue
        kids = [m for m, s in SPECS.items() if (s.get("parent") or {}).get("node") == n["id"] and (s.get("parent") or {}).get("model") == "L3"]
        if len(kids) != 1 or kids[0] != n["calls"]:
            err("SCP-06", "L3", "L3", n["id"], "call activity has child models %s, calls %s" % (kids, n["calls"]))
            continue
        c = SPECS[kids[0]]
        cn = nodes(c)
        itf = c.get("interface") or {}
        # interface events: in the internal pool, right types
        for x in itf.get("start", []):
            if cn.get(x, {}).get("type") not in START or pool_of(c, cn[x]) != "P_SPON":
                err("SCP-06", "L3", c["id"], x, "interface start is not a start event of the Sponsor process")
        for x in itf.get("ends", []):
            if cn.get(x, {}).get("type") not in END or pool_of(c, cn[x]) != "P_SPON":
                err("SCP-06", "L3", c["id"], x, "interface end is not an end event of the Sponsor process")
        sp_starts = [i for i, x in cn.items() if x["type"] in START and pool_of(c, x) == "P_SPON"]
        sp_ends = [i for i, x in cn.items() if x["type"] in END and pool_of(c, x) == "P_SPON"]
        if set(sp_starts) != set(itf.get("start", [])):
            err("SCP-06", "L3", c["id"], "interface", "Sponsor start events %s != interface.start %s" % (sp_starts, itf.get("start")))
        if set(sp_ends) != set(itf.get("ends", [])):
            err("SCP-06", "L3", c["id"], "interface", "Sponsor end events %s != interface.ends %s" % (sp_ends, itf.get("ends")))
        # hand-offs: every parent message flow of this call activity reappears (pool + identical label)
        parent_mf = [m for m in l3.get("message_flows", []) if n["id"] in (m["from"], m["to"])]
        child_mf = {m["id"]: m for m in c.get("message_flows", [])}
        used = set()
        for pm in parent_mf:
            out = pm["from"] == n["id"]
            other = pm["to"] if out else pm["from"]
            other_pool = endpoint_pool(l3, other)
            cand = []
            for cid, cm in child_mf.items():
                if cm["label"] != pm["label"]:
                    continue
                pf, pt = endpoint_pool(c, cm["from"]), endpoint_pool(c, cm["to"])
                if out and pf == "P_SPON" and pt == other_pool:
                    cand.append(cid)
                if not out and pt == "P_SPON" and pf == other_pool:
                    cand.append(cid)
            if not cand:
                err("SCP-06", "L3", c["id"], pm["id"], "L3 hand-off %s %r (to %s) has no child message flow with identical label and pools" % (pm["id"], pm["label"], other_pool))
                continue
            inif = [x for x in cand if x in itf.get("message_flows", [])]
            if not inif:
                err("SCP-06", "L3", c["id"], cand[0], "child message flow realising L3 %s not listed in interface.message_flows" % pm["id"])
            used.update(cand)
            n_ok += 1
        for x in itf.get("message_flows", []):
            if x not in used:
                err("SCP-06", "L3", c["id"], x, "interface.message_flows lists %s, which realises no L3 hand-off of %s" % (x, n["id"]))
        # child Sponsor<->external message flows that the parent does not show (lossless the other way round)
        for cid, cm in child_mf.items():
            pf, pt = endpoint_pool(c, cm["from"]), endpoint_pool(c, cm["to"])
            if "P_SPON" in (pf, pt) and cid not in used:
                other = pt if pf == "P_SPON" else pf
                direction = "to" if pf == "P_SPON" else "from"
                if not any(pm["label"] == cm["label"] for pm in parent_mf):
                    FACTS.setdefault("child_handoffs_not_on_L3", []).append("%s %s %s %s %r" % (c["id"], cid, direction, other, cm["label"]))
        # trigger: a child start that is a message start receives a hand-off the parent does not show
        for x in itf.get("start", []):
            if cn[x]["type"] == "start-message":
                inc = [m for m in c.get("message_flows", []) if m["to"] == x]
                pools_in = sorted({endpoint_pool(c, m["from"]) for m in inc})
                shown = [pm for pm in parent_mf if pm["to"] == n["id"]]
                if inc and not shown:
                    doc = "all sent by the call activity" in NOTES
                    err("SCP-06", "L3", "L3", n["id"], "child %s is triggered by message(s) %s from %s, but L3 shows no incoming hand-off on %s, "
                        "so the L3 reader does not see what starts the step (notes.md section 7: L3 shows outgoing hand-offs only)"
                        % (c["id"], sorted({m["label"] for m in inc}), pools_in, n["id"]), severity="SHOULD",
                        status="documented-choice" if doc else "open")
    ok("L3", "SCP-06 each L3 call activity has exactly one child; every L3 hand-off reappears in the child (pool + identical label) and is listed in interface.message_flows", n_ok)
    # child start/end events vs the parent step's input/output = trigger and outcomes of the confirmed L3 cut
    cov = open(os.path.join(SPEC_DIR, "coverage.md"), encoding="utf-8").read()
    cov_rows = defaultdict(list)  # step -> [(l3_cut outcome, realised-by text, quoted labels)]
    sec = cov.split("## l3_cut outcomes", 1)[-1]
    for line in sec.splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) >= 3 and re.match(r"^A\d$", cols[0]):
            cov_rows[cols[0]].append((cols[1], cols[2], re.findall(r"'([^']+)'", cols[2])))
    n_io = 0
    for step in re.split(r"\n## ", L3CUT)[1:]:
        hm = re.match(r"(A\d) - ", step)
        if not hm:
            continue
        sid = hm.group(1)
        node = nd3.get(sid)
        if not node or not node.get("calls"):
            continue
        c = SPECS[node["calls"]]
        cn = nodes(c)
        tl = re.search(r"\*\*Trigger \(start event\):\*\*\s*([^\n]*)", step)
        ol = re.search(r"\*\*Outcomes \(end events\):\*\*\s*([^\n]*)", step)
        if not tl or not ol:
            err("SCP-06", "L3", "L3", sid, "l3_cut.md gives no trigger/outcome line for this step; cannot match the child", severity="SHOULD", owner="Y1")
            continue
        trig = {re.split(r" \(|;|\. ", tl.group(1))[0].strip().rstrip(".")} | set(re.findall(r'"([^"]+)"', tl.group(1)))
        # formats: "A; B (Sponsor); C (Investigator/institution)." or "Sponsor: A; B. Investigator/institution: C; D (note)."
        outs = []
        for o in re.split(r";|\.\s+", ol.group(1)):
            o = re.sub(r"^\s*(Sponsor|Investigator/institution|Monitor|IRB/IEC|Regulatory authority)\s*:\s*", "", o)
            o = re.split(r" \(", o)[0].strip().rstrip(".")
            if o and o not in outs:
                outs.append(o)
        for x in c["interface"]["start"]:
            n_io += 1
            if cn[x]["label"] not in trig:
                err("SCP-06", "L3", c["id"], x, "Sponsor start %r is not the trigger of L3 %s in l3_cut.md (%s)" % (cn[x]["label"], sid, sorted(trig)))
        ends_all = {x["label"]: i for i, x in cn.items() if x["type"] in END}
        documented_labels = set()
        for o_, txt, q in cov_rows[sid]:
            documented_labels |= set(q)
        for o in outs:
            n_io += 1
            if o in ends_all:
                continue
            row = [r for r in cov_rows[sid] if r[0] == o]
            alt = [q for r in row for q in r[2] if q in ends_all]
            if alt:
                err("SCP-06", "L3", c["id"], sid, "l3_cut outcome %r of %s realised by end event %s %r with another label (coverage.md: %s)"
                    % (o, sid, ends_all[alt[0]], alt[0], row[0][1][:160]), severity="SHOULD", status="documented-deviation")
            else:
                err("SCP-06", "L3", c["id"], sid, "l3_cut outcome %r of %s has no end event with identical label in %s" % (o, sid, c["id"]))
        for x in c["interface"]["ends"]:
            lab = cn[x]["label"]
            if lab not in outs and lab not in documented_labels:
                err("SCP-06", "L3", c["id"], x, "Sponsor end %r is no l3_cut outcome of %s and not documented in coverage.md" % (lab, sid), severity="SHOULD")
    ok("L3", "SCP-06 child Sponsor start = l3_cut trigger; every l3_cut outcome is an end event of the child", n_io)


# ------------------------------------------------------------------ L4 traceability
def strongest(reqs):
    return max((REQS[q]["binding"] for q in reqs), key=lambda b: STRENGTH[b])


def l4():
    on_el = defaultdict(list)
    n_el = 0
    open_text = defaultdict(str)
    step_of_model = {}
    for n in SPECS["L3"]["nodes"]:
        if n.get("calls"):
            step_of_model[n["calls"]] = n["id"]
    for mid, s in SPECS.items():
        open_text[mid] = "\n".join(s.get("open_items", []))
        for kind, el in traced(s):
            reqs = [q for q in el.get("req", []) if q in REQS]
            if el.get("type") in ACT:
                for k in ("src", "req", "binding"):
                    if not el.get(k):
                        err("TRACE-FIELDS", "L4", mid, el["id"], "%s without %s" % (el["type"], k))
            if not reqs:
                if el.get("binding") or el.get("draft"):
                    err("BINDING", "L4", mid, el["id"], "binding/draft without req")
                continue
            n_el += 1
            for q in reqs:
                if mid != "L3":
                    on_el[q].append("%s %s" % (mid, el["id"]))
                r = REQS[q]
                if r["status"] == "out_of_scope":
                    err("REQ-SCOPE", "L4", mid, el["id"], "%s is out_of_scope (%s) but sits on an element" % (q, r.get("reason", "")[:80]))
                if mid != "L3" and r["status"] == "in_scope" and r["l3_step"] != step_of_model.get(mid):
                    err("REQ-STEP", "L4", mid, el["id"], "%s mapped to step %s but placed in %s (step %s)" % (q, r["l3_step"], mid, step_of_model.get(mid)),
                        severity="SHOULD")
            want = strongest(reqs)
            if el.get("binding") != want:
                err("BINDING", "L4", mid, el["id"], "binding %s != strongest REQ binding %s (%s)" % (el.get("binding"), want, reqs))
            want_draft = any(REQS[q]["draft"] for q in reqs)
            if bool(el.get("draft")) != want_draft:
                err("DRAFT", "L4", mid, el["id"], "draft=%s but REQs with draft-only support: %s" % (el.get("draft"), [q for q in reqs if REQS[q]["draft"]]))
            # binding-law / binding-ICH must rest on a non-draft REQ of that class, backed by non-draft findings of that class
            if el.get("binding") in ("binding-law", "binding-ICH"):
                sup = [q for q in reqs if REQS[q]["binding"] == el["binding"] and not REQS[q]["draft"]]
                if not sup:
                    err("BINDING-SUPPORT", "L4", mid, el["id"], "claims %s without a non-draft REQ of that class" % el["binding"])
                else:
                    good = False
                    for q in sup:
                        fs = [FIND[i] for i in REQS[q]["findings"] if i in FIND]
                        if any(f["binding"] == el["binding"] and not f.get("draft") for f in fs):
                            good = True
                    if not good:
                        err("BINDING-SUPPORT", "L4", mid, el["id"], "claims %s but no non-draft finding of that class behind %s" % (el["binding"], sup), owner="Y1")
            # jurisdiction = union of REQ jurisdictions
            if mid != "L3" or el.get("jurisdiction"):
                wj = set()
                for q in reqs:
                    wj |= set(REQS[q]["jurisdiction"])
                if set(el.get("jurisdiction", [])) != wj:
                    err("JURISDICTION", "L4", mid, el["id"], "jurisdiction %s != union of REQ jurisdictions %s" % (el.get("jurisdiction"), sorted(wj)),
                        severity="SHOULD")
            # verify items
            have = el.get("verify", [])
            for q in reqs:
                for vi in REQS[q].get("verify", []):
                    if vi not in have:
                        # B1 successor de-duplication (notes.md, last section): an item is dropped only where a fuller item on the
                        # same question is kept; accept as documented if notes names the element and the dropped item's reference
                        # and the element keeps an item citing the same finding
                        refs = re.findall(r"\((R\d-\d{3}|C-\d+)\)", vi)
                        succ_notes = NOTES.split("## B1 successor changes", 1)[-1]
                        el_named = re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(el["id"]), succ_notes) and (mid == "L3" or mid in succ_notes)
                        kept = []
                        for r_ in refs:
                            fid = r_ if r_.startswith("R") else None
                            if fid is None:  # C-xx: the conflict cites findings; accept a kept item quoting any finding of the REQ
                                kept += [h for h in have if any(f_ in h or (FIND.get(f_, {}).get("verify") and any(v_ in h for v_ in FIND[f_]["verify"]))
                                                                for f_ in REQS[q]["findings"])]
                            else:
                                kept += [h for h in have if fid in h or any(v_ in h for v_ in FIND.get(fid, {}).get("verify", []))]
                        doc = bool(refs) and el_named and any(r_ in succ_notes for r_ in refs) and bool(kept)
                        err("VERIFY", "L4", mid, el["id"], "%s verify item missing: %r%s" % (q, vi[:140], (" (de-duplicated by B1; kept: %r)" % kept[0][:100]) if doc else ""),
                            severity="SHOULD" if doc else "MUST", status="documented-deviation" if doc else "open")
                for fid in REQS[q]["findings"]:
                    f = FIND.get(fid)
                    for vi in (f or {}).get("verify", []):
                        core = vi.strip()
                        if not any(core in h or core.replace("[verify]", "").strip() in h for h in have):
                            # Y1 is responsible if the REQ itself dropped the finding's item
                            inreq = any(core in x or core.replace("[verify]", "").strip() in x for x in REQS[q].get("verify", []))
                            err("VERIFY", "L4", mid, el["id"], "finding %s (%s) verify item not on element: %r" % (fid, q, vi[:140]),
                                owner="B1" if inreq else "Y1", severity="SHOULD" if not inreq else "MUST")
            # src completeness: every finding of the REQs is cited (B1 derivation rule, notes section 4)
            pairs = {(x["key"], x["loc"]) for x in el.get("src", [])}
            for q in reqs:
                for fid in REQS[q]["findings"]:
                    f = FIND.get(fid)
                    if f and (f["src"], f["loc"]) not in pairs:
                        err("SRC-COMPLETE", "L4", mid, el["id"], "finding %s (%s %s) of %s not in src" % (fid, f["src"], f["loc"], q), severity="SHOULD")
            # deadline present on tasks when a REQ has one
            if el.get("type") == "task" or kind == "message_flow":
                dl = [REQS[q]["deadline"] for q in reqs if not re.match(r"^\s*(none\b|$)", REQS[q]["deadline"] or "", re.I)]
                if dl and not el.get("deadline"):
                    err("DEADLINE", "L4", mid, el["id"], "REQ deadline(s) %s not shown on the element" % dl, severity="SHOULD")
    # coverage
    inb = [q for q, r in REQS.items() if r["status"] == "in_scope" and r["binding"] in ("binding-law", "binding-ICH")]
    ins = [q for q, r in REQS.items() if r["status"] == "in_scope"]
    miss_b = [q for q in inb if not on_el.get(q)]
    miss_s = [q for q in ins if not on_el.get(q)]
    for q in miss_b:
        err("COVERAGE", "L4", "*", q, "in-scope binding REQ on no L4 element")
    for q in miss_s:
        if q not in miss_b:
            err("COVERAGE", "L4", "*", q, "in-scope REQ on no L4 element", severity="SHOULD")
    FACTS["coverage"] = dict(in_scope_binding=len(inb), in_scope_binding_on_element=len(inb) - len(miss_b),
                             in_scope=len(ins), in_scope_on_element=len(ins) - len(miss_s))
    # interface REQs
    itf = [q for q, r in REQS.items() if r["status"] == "interface"]
    n_el_itf = n_oi = 0
    for q in itf:
        els = on_el.get(q, [])
        good_el = []
        for e in els:
            mid, eid = e.split()
            s = SPECS[mid]
            nd = nodes(s)
            if eid in nd and (nd[eid].get("interface") or nd[eid]["type"] in START + END):
                good_el.append(e)
            elif eid.startswith("M"):
                good_el.append(e)
        in_oi = [m for m, t in open_text.items() if q in t]
        if good_el:
            n_el_itf += 1
        elif in_oi:
            n_oi += 1
        else:
            err("INTERFACE", "L4", "*", q, "interface REQ neither on an interface element nor in open_items (on: %s)" % els)
        bad = [e for e in els if e not in good_el]
        for e in bad:
            err("INTERFACE", "L4", e.split()[0], e.split()[1], "interface REQ %s on a non-interface element" % q, severity="SHOULD")
    FACTS["interface"] = dict(total=len(itf), on_element=n_el_itf, in_open_items=n_oi)
    # L3 call activities carry every in-scope REQ of their step
    for n in SPECS["L3"]["nodes"]:
        if n["type"] == "call-activity":
            want = {q for q, r in REQS.items() if r["status"] == "in_scope" and r["l3_step"] == n["id"]}
            have = set(n.get("req", []))
            if want - have:
                err("COVERAGE", "L4", "L3", n["id"], "missing in-scope REQs of its step (B1 convention, notes.md section 4): %s" % sorted(want - have),
                    severity="SHOULD")
            if have - want:
                err("COVERAGE", "L4", "L3", n["id"], "carries REQs that are not in-scope REQs of its step: %s" % sorted(have - want), severity="SHOULD")
    # REQ-level consistency (owner Y1)
    for q, r in REQS.items():
        fs = [FIND[i] for i in r["findings"] if i in FIND]
        if not fs:
            err("REQ-FINDINGS", "L4", "*", q, "REQ without findings", owner="Y1")
            continue
        top = max(STRENGTH[f["binding"]] for f in fs)
        sb = [f for f in fs if STRENGTH[f["binding"]] == top]
        if STRENGTH[r["binding"]] != top:
            err("REQ-BINDING", "L4", "*", q, "REQ binding %s != strongest finding binding" % r["binding"], owner="Y1")
        if bool(r["draft"]) != all(f.get("draft") for f in sb):
            err("REQ-DRAFT", "L4", "*", q, "REQ draft flag inconsistent with its strongest findings", owner="Y1")
        for f in fs:
            reg = REGKEYS.get(f["src"], {})
            if f["binding"] == "binding-law" and (f["jurisdiction"] == "ICH" or re.match(r"^[EM]\d", f["src"])):
                err("ICH-NOT-LAW", "L4", "*", f["id"], "ICH finding classified binding-law", owner="Y1")
            if reg.get("binding_default") == "best-practice" and f["binding"] in ("binding-law", "binding-ICH"):
                err("BINDING-SRC", "L4", "*", f["id"], "best-practice source %s with binding %s" % (f["src"], f["binding"]), owner="Y1")
            if reg.get("draft") and not f.get("draft"):
                err("DRAFT-SRC", "L4", "*", f["id"], "finding from draft source %s without draft: true" % f["src"], owner="Y1", severity="SHOULD")
            if f["binding"] in ("binding-law", "binding-ICH") and f.get("draft"):
                err("BINDING-SRC", "L4", "*", f["id"], "binding finding marked draft", owner="Y1")
            if q not in f.get("req", []):
                err("REQ-FINDINGS", "L4", "*", f["id"], "finding listed in %s but its req field is %s" % (q, f.get("req")), owner="Y1", severity="SHOULD")
    ok("L4", "binding, draft, support, verify, src completeness per traced element", n_el)


def main():
    global VERBS
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--spec-dir", default=None, help="spec directory (default spec/); used for seeded-fault self-tests")
    a = ap.parse_args()
    VERBS = set()
    for s in SPECS.values():
        for n in s["nodes"]:
            if n["type"] in ACT:
                VERBS.add(n["label"].split()[0].lower())
    l0()
    l2()
    l3()
    scp06()
    l4()
    FACTS["verbs"] = sorted(VERBS)
    FACTS["spec_dir"] = SPEC_DIR
    json.dump(dict(errors=ERRORS, passed=PASSED, facts=FACTS, inputs=INPUTS), open(a.out, "w"), indent=1)
    c = Counter((e["layer"], e["rule_id"], e["severity"]) for e in ERRORS)
    for k, v in sorted(c.items()):
        print(k, v)
    print("v1_spec: %d errors, %d passed checks" % (len(ERRORS), len(PASSED)))


if __name__ == "__main__":
    sys.exit(main())
