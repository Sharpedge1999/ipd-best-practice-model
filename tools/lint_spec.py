#!/usr/bin/env python3
"""Lint model specs (L3 / L4) against the S0 contract - structure only.

Usage:
    python -I tools/lint_spec.py <spec.yaml> [<spec.yaml> ...]
        [--registry contracts/source_registry.yaml] [--parent <L3 spec.yaml>]

Checks (rule tags in brackets):
    [YAML]    file parses as YAML
    [SCHEMA]  contracts/spec.schema.json (draft 2020-12)
    [DUPID]   ids unique across pools, lanes, nodes, flows, message flows,
              data and groups within the model
    [NAMING]  node id prefix matches the node type; reserved XML suffixes
    [REF]     references resolve: lanes -> pools, nodes -> lanes/pools,
              flow endpoints, message flow endpoints, data assoc, group
              members, node.group, interface, rule_exceptions, parent,
              annotation assoc (nodes or sequence flows)
    [STRUCT]  what the converter cannot build: sequence flow across pools,
              message flow inside one pool or on a gateway, data across
              pools or on gateways, annotations associated with elements
              in more than one pool, nodes in collapsed pools, missing lane
              in a laned pool, >1 default flow per source, not exactly one
              internal expanded pool
    [RULEX]   rule_exceptions required by the contract (ROL-03 for an
              expanded external pool, FLW-01 for intermediate events)
    [SRC]     src keys exist in the registry
    [CHARS]   no em dash or middle dot in any string
Graph rules (reachability, block structure, labels, sizes) belong to V1.

Exit codes: 0 no errors, 1 errors found, 2 usage or contract-load error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "contracts" / "spec.schema.json"
REGISTRY_PATH = ROOT / "contracts" / "source_registry.yaml"

GATEWAYS = {"xor-split", "xor-join", "and-split", "and-join", "or-split", "or-join"}
STARTS = {"start", "start-message", "start-timer"}
INTERMEDIATES = {"intermediate-catch-message", "intermediate-throw-message", "intermediate-catch-timer"}
PREFIX_TYPES = {
    "S": STARTS,
    "E": {"end"},
    "A": {"task", "call-activity"},
    "G": GATEWAYS,
    "I": INTERMEDIATES,
}
RESERVED_SUFFIXES = ("_COLLAB", "_PROCESS", "_LANESET", "_MESSAGE", "_OBJECT", "_STORE",
                     "_IN", "_OUT", "_PROPERTY", "_CATEGORY", "_VALUE", "_DIAGRAM", "_PLANE", "_di")
RESERVED_SUFFIX_RE = re.compile(r"_ASSOC\d+$")
FORBIDDEN_CHARS = {"\u2014": "em dash", "\u00b7": "middle dot"}


class Report:
    def __init__(self):
        self.errors = 0

    def error(self, rule, eid, path, msg):
        self.errors += 1
        print(f"ERROR [{rule}] {eid or '-'} ({path}): {msg}")


def load_registry(path):
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise ValueError("registry must be a mapping with a 'sources' list")
    return {rec["key"]: rec for rec in data["sources"] if isinstance(rec, dict) and "key" in rec}


def items(spec, key):
    value = spec.get(key)
    if not isinstance(value, list):
        return []
    return [x for x in value if isinstance(x, dict)]


def iter_strings(obj, where=""):
    if isinstance(obj, str):
        yield where, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, f"{where}/{k}" if where else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{where}/{i}")


def load_yaml(path, rep, shown):
    try:
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        rep.error("YAML", None, shown, f"does not parse: {exc}")
    except OSError as exc:
        rep.error("IO", None, shown, str(exc))
    return None


def lint_spec(path, validator, registry, parent_spec, rep):
    shown = str(path)
    before = rep.errors
    spec = load_yaml(path, rep, shown)
    if spec is None:
        if rep.errors == before:
            rep.error("YAML", None, shown, "empty file")
        return
    if not isinstance(spec, dict):
        rep.error("SCHEMA", None, shown, "top level must be a mapping")
        return

    model = spec.get("id") if isinstance(spec.get("id"), str) else "?"

    # --- schema ------------------------------------------------------------
    for err in sorted(validator.iter_errors(spec), key=lambda e: [str(p) for p in e.absolute_path]):
        p = list(err.absolute_path)
        eid = None
        if len(p) >= 2 and isinstance(spec.get(p[0]), list) and isinstance(p[1], int):
            elem = spec[p[0]][p[1]] if p[1] < len(spec[p[0]]) else None
            if isinstance(elem, dict):
                eid = elem.get("id")
        where = "/".join(str(x) for x in p) or "(root)"
        rep.error("SCHEMA", eid, shown, f"{where}: {err.message}")

    pools = items(spec, "pools")
    lanes = items(spec, "lanes")
    nodes = items(spec, "nodes")
    flows = items(spec, "flows")
    mflows = items(spec, "message_flows")
    data = items(spec, "data")
    groups = items(spec, "groups")
    rulex = items(spec, "rule_exceptions")
    annotations = items(spec, "annotations")

    # --- id index ----------------------------------------------------------
    kinds = {}
    for kind, coll in (("pool", pools), ("lane", lanes), ("node", nodes), ("flow", flows),
                       ("message flow", mflows), ("data", data), ("group", groups),
                       ("annotation", annotations)):
        for el in coll:
            eid = el.get("id")
            if not isinstance(eid, str):
                continue
            if eid in kinds:
                rep.error("DUPID", eid, shown, f"id used twice ({kinds[eid]} and {kind})")
            else:
                kinds[eid] = kind
    pool_by = {p["id"]: p for p in pools if isinstance(p.get("id"), str)}
    lane_by = {l["id"]: l for l in lanes if isinstance(l.get("id"), str)}
    node_by = {n["id"]: n for n in nodes if isinstance(n.get("id"), str)}
    group_by = {g["id"]: g for g in groups if isinstance(g.get("id"), str)}
    mflow_ids = {m["id"] for m in mflows if isinstance(m.get("id"), str)}

    # --- naming ------------------------------------------------------------
    for nid, node in node_by.items():
        allowed = PREFIX_TYPES.get(nid[:1], set())
        if node.get("type") not in allowed:
            rep.error("NAMING", nid, shown, f"id prefix '{nid[:1]}' does not fit type '{node.get('type')}'")
    for eid in list(pool_by) + list(lane_by) + list(group_by):
        if eid.endswith(RESERVED_SUFFIXES) or RESERVED_SUFFIX_RE.search(eid):
            rep.error("NAMING", eid, shown, "id ends with a reserved XML suffix (decisions.md B3)")

    # --- pools ---------------------------------------------------------------
    internal = [p for p in pools if p.get("kind") == "internal"]
    if len(internal) != 1:
        rep.error("STRUCT", None, shown, f"exactly one internal pool required, found {len(internal)}")
    for p in internal:
        if p.get("expanded") is not True:
            rep.error("STRUCT", p.get("id"), shown, "the internal pool must be expanded")
    rulex_set = {(r.get("rule"), r.get("element")) for r in rulex}
    for pid, pool in pool_by.items():
        if pool.get("kind") == "external" and pool.get("expanded") is True and ("ROL-03", pid) not in rulex_set:
            rep.error("RULEX", pid, shown, "expanded external pool needs a rule_exceptions entry ROL-03 (D1)")

    # --- lanes ---------------------------------------------------------------
    lanes_of_pool = {}
    for lid, lane in lane_by.items():
        pid = lane.get("pool")
        if pid not in pool_by:
            rep.error("REF", lid, shown, f"lane pool '{pid}' does not exist")
            continue
        lanes_of_pool.setdefault(pid, []).append(lid)
        if pool_by[pid].get("expanded") is not True:
            rep.error("STRUCT", lid, shown, f"lane in collapsed pool '{pid}'")

    # --- nodes -> pool -------------------------------------------------------
    pool_of = {}
    for nid, node in node_by.items():
        lid, pid = node.get("lane"), node.get("pool")
        resolved = None
        if lid is not None:
            if lid not in lane_by:
                rep.error("REF", nid, shown, f"lane '{lid}' does not exist")
            else:
                resolved = lane_by[lid].get("pool")
        if pid is not None:
            if pid not in pool_by:
                rep.error("REF", nid, shown, f"pool '{pid}' does not exist")
            elif resolved is not None and resolved != pid:
                rep.error("REF", nid, shown, f"lane '{lid}' belongs to '{resolved}', not to pool '{pid}'")
            else:
                resolved = pid
        if resolved in pool_by:
            pool_of[nid] = resolved
            if pool_by[resolved].get("expanded") is not True:
                rep.error("STRUCT", nid, shown, f"node in collapsed pool '{resolved}'")
            if lid is None and lanes_of_pool.get(resolved):
                rep.error("STRUCT", nid, shown, f"pool '{resolved}' has lanes; node needs a lane")

    # --- sequence flows ------------------------------------------------------
    defaults = {}
    for fl in flows:
        fid = fl.get("id")
        ends_ok = True
        for end in ("from", "to"):
            ref = fl.get(end)
            if ref not in node_by:
                rep.error("REF", fid, shown, f"flow {end} '{ref}' is not a node")
                ends_ok = False
        if ends_ok:
            pa, pb = pool_of.get(fl["from"]), pool_of.get(fl["to"])
            if pa and pb and pa != pb:
                rep.error("STRUCT", fid, shown, f"sequence flow crosses pools ({pa} -> {pb}); use a message flow")
        if fl.get("default") is True:
            defaults.setdefault(fl.get("from"), []).append(fid)
    for src_node, fids in defaults.items():
        if len(fids) > 1:
            rep.error("STRUCT", src_node, shown, f"more than one default flow: {', '.join(map(str, fids))}")

    # --- message flows -------------------------------------------------------
    for mf in mflows:
        mid = mf.get("id")
        sides = []
        for end in ("from", "to"):
            ref = mf.get(end)
            if ref in node_by:
                if node_by[ref].get("type") in GATEWAYS:
                    rep.error("STRUCT", mid, shown, f"message flow {end} '{ref}' is a gateway")
                sides.append(pool_of.get(ref))
            elif ref in pool_by:
                sides.append(ref)
            else:
                rep.error("REF", mid, shown, f"message flow {end} '{ref}' is neither a node nor a pool")
                sides.append(None)
        if len(sides) == 2 and sides[0] and sides[0] == sides[1]:
            rep.error("STRUCT", mid, shown, f"message flow inside one pool ({sides[0]})")

    # --- data ----------------------------------------------------------------
    for d in data:
        did = d.get("id")
        d_pools = set()
        for a in d.get("assoc") or []:
            if not isinstance(a, dict):
                continue
            ref = a.get("node")
            if ref not in node_by:
                rep.error("REF", did, shown, f"data assoc node '{ref}' does not exist")
                continue
            if node_by[ref].get("type") in GATEWAYS:
                rep.error("STRUCT", did, shown, f"data assoc on gateway '{ref}'")
            if ref in pool_of:
                d_pools.add(pool_of[ref])
        if len(d_pools) > 1:
            rep.error("STRUCT", did, shown, f"data associated with nodes in several pools: {sorted(d_pools)}")

    # --- annotations (S0-18) ------------------------------------------------
    flow_by = {f["id"]: f for f in flows if isinstance(f.get("id"), str)}
    for ta in annotations:
        tid = ta.get("id")
        ta_pools = []
        for ref in ta.get("assoc") or []:
            if ref in node_by:
                ta_pools.append(pool_of.get(ref))
            elif ref in flow_by:
                ta_pools.append(pool_of.get(flow_by[ref].get("from")))
            else:
                rep.error("REF", tid, shown, f"annotation assoc '{ref}' is neither a node nor a sequence flow")
        distinct = {x for x in ta_pools if x}
        if len(distinct) > 1:
            rep.error("STRUCT", tid, shown, f"annotation associated with elements in several pools: {sorted(distinct)}")

    # --- groups --------------------------------------------------------------
    for gid, g in group_by.items():
        for m in g.get("members") or []:
            if m not in node_by:
                rep.error("REF", gid, shown, f"group member '{m}' is not a node")
    for nid, node in node_by.items():
        gid = node.get("group")
        if gid is None:
            continue
        if gid not in group_by:
            rep.error("REF", nid, shown, f"group '{gid}' does not exist")
        elif nid not in (group_by[gid].get("members") or []):
            rep.error("REF", nid, shown, f"node names group '{gid}' but is not in its members")

    # --- interface -----------------------------------------------------------
    internal_ids = {p.get("id") for p in internal}
    iface = spec.get("interface") if isinstance(spec.get("interface"), dict) else {}
    for key, types in (("start", STARTS), ("ends", {"end"})):
        for ref in iface.get(key) or []:
            if ref not in node_by:
                rep.error("REF", ref, shown, f"interface {key} '{ref}' is not a node")
            elif node_by[ref].get("type") not in types:
                rep.error("REF", ref, shown, f"interface {key} '{ref}' has type '{node_by[ref].get('type')}'")
            elif pool_of.get(ref) not in internal_ids:
                rep.error("STRUCT", ref, shown, f"interface {key} '{ref}' is not in the internal pool")
    for ref in iface.get("message_flows") or []:
        if ref not in mflow_ids:
            rep.error("REF", ref, shown, f"interface message flow '{ref}' does not exist")

    # --- calls / parent ------------------------------------------------------
    for nid, node in node_by.items():
        if node.get("type") == "call-activity" and node.get("calls") == model:
            rep.error("REF", nid, shown, "call activity calls its own model")
    parent = spec.get("parent")
    if spec.get("level") == "L4" and isinstance(parent, dict):
        if parent.get("model") != "L3":
            rep.error("REF", model, shown, f"parent model must be L3, found '{parent.get('model')}'")
        if parent_spec is not None:
            pnodes = {n.get("id"): n for n in items(parent_spec, "nodes")}
            pn = pnodes.get(parent.get("node"))
            if pn is None:
                rep.error("REF", model, shown, f"parent node '{parent.get('node')}' not in parent spec")
            elif pn.get("type") != "call-activity" or pn.get("calls") != model:
                rep.error("REF", model, shown, f"parent node '{parent.get('node')}' is not a call activity calling {model}")

    # --- rule exceptions -----------------------------------------------------
    for r in rulex:
        if r.get("element") not in kinds:
            rep.error("REF", r.get("element"), shown, f"rule_exception {r.get('rule')} element does not exist")
    for nid, node in node_by.items():
        if node.get("type") in INTERMEDIATES and ("FLW-01", nid) not in rulex_set:
            rep.error("RULEX", nid, shown, "intermediate event needs a rule_exceptions entry FLW-01 (S0-08)")

    # --- src keys ------------------------------------------------------------
    for coll in (pools, lanes, nodes, mflows, data, annotations):
        for el in coll:
            for s in el.get("src") or []:
                if isinstance(s, dict) and isinstance(s.get("key"), str) and s["key"] not in registry:
                    rep.error("SRC", el.get("id"), shown, f"src key '{s['key']}' is not in the registry")

    # --- characters ----------------------------------------------------------
    for where, text in iter_strings(spec):
        for ch, name in FORBIDDEN_CHARS.items():
            if ch in text:
                rep.error("CHARS", None, shown, f"{where}: contains {name}; use '-'")

    n = rep.errors - before
    print(f"{shown}: {'OK' if n == 0 else 'FAIL'} (model {model}, {len(node_by)} nodes, {n} errors)")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lint model spec YAML files (contract S0).")
    parser.add_argument("files", nargs="+", help="spec files, e.g. spec/L4-01.yaml")
    parser.add_argument("--registry", default=str(REGISTRY_PATH), help="source registry YAML")
    parser.add_argument("--parent", default=None, help="L3 spec used to resolve parent.node of L4 specs")
    args = parser.parse_args(argv)

    try:
        with open(SCHEMA_PATH, encoding="utf-8") as fh:
            schema = json.load(fh)
        Draft202012Validator.check_schema(schema)
        registry = load_registry(args.registry)
    except Exception as exc:
        print(f"ERROR [CONTRACT] - (contracts): cannot load contracts: {exc}")
        return 2

    rep = Report()
    parent_spec = None
    if args.parent:
        parent_spec = load_yaml(args.parent, rep, args.parent)
        if not isinstance(parent_spec, dict):
            print(f"ERROR [CONTRACT] - ({args.parent}): parent spec unreadable")
            return 2
    validator = Draft202012Validator(schema)
    for f in args.files:
        lint_spec(Path(f), validator, registry, parent_spec, rep)
    print(f"TOTAL: {rep.errors} errors in {len(args.files)} file(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
