#!/usr/bin/env python3
"""Deterministic automatic layout for iPD BPMN models (step B2).

Used by tools/spec2bpmn.py. Works on spec ids only (no XML). All coordinates
are integers; iteration follows spec order or sorted keys, so the same specs
always give the same geometry.

Conventions (also stated in out/build_log.md for the viewer builder):

* Time runs left to right. Column = longest path from the start events within
  each process (sequence flows weight 1, back edges of loops ignored), refined
  by message flows between nodes (receiver never left of sender, weight 0), so
  that message flows can run vertically (LAY-02). Ties: spec order.
* Lanes are rows. Inside a lane, row 0 (the bottom row) holds the happy path
  (path: main or no path); alt/exception nodes, data elements and text
  annotations take the first free row above it. Every node of a row is centred
  on the row's centre line, so the happy path is one straight line per lane
  (LAY-01). Rows are only as tall as their content plus the overlay clearance.
* Pool order is global per pool id (pool_slots): top band (one collapsed pool),
  external pools that are expanded in any model (collapsed there: band in the
  same slot), the internal (Sponsor) pool, bottom bands. Same on every diagram.
* Overlay clearance: below every task, call activity, event, gateway, data
  element and sourced text annotation a zone of OVERLAY_H px (width
  max(OVERLAY_W, shape width), centred) is kept free of shapes, labels and
  edges, inside the lane. Activities / annotations: zone starts ZONE_GAP_ACT px
  below the shape; events / gateways / data: ZONE_GAP_LABEL px below the DI
  label (LABEL_GAP px below the shape). Message flows: OVERLAY_W x OVERLAY_H
  directly below the DI label, normally inside a pool gap.
* Call activities are at least 160 px wide and keep >= 20 px free below their
  label text (viewer "Open L4" chip at the bottom-right, right of the marker).
* Edges are orthogonal, routed on a sparse grid (Dijkstra) with costs for
  length, bends, crossings and overlaps, then one rip-up-and-reroute pass;
  shapes, labels and overlay zones are obstacles. Sequence flows, data and
  annotation associations stay inside their pool.
"""

import heapq
import math
import re
from bisect import bisect_left, bisect_right

# ------------------------------------------------------------------ sizes
TASK_SIZES = [(120, 80), (140, 80), (160, 90), (180, 100), (200, 110),
              (220, 120), (240, 130), (260, 140)]
CALL_SIZES = [(160, 80), (160, 90), (180, 90), (180, 100), (200, 110),
              (220, 120), (240, 130), (260, 140)]
ANNOT_WIDTHS = [160, 200, 240]
EVENT_SIZE = (36, 36)
GATEWAY_SIZE = (50, 50)
DATA_OBJECT_SIZE = (36, 50)
DATA_STORE_SIZE = (50, 50)

POOL_X = 20
POOL_Y = 20
POOL_HEADER = 30
LANE_HEADER = 30
LEFT_MARGIN = 50
RIGHT_MARGIN = 60
COL_GAP = 44            # channel between columns (vertical edge tracks)
CHANNEL_TRACKS = (12, 22, 32)
MIN_COL_W = 150
TOP_PAD = 30            # corridor above the shapes of a row
BOTTOM_PAD = 6
OVERLAY_W = 150
OVERLAY_H = 70
ZONE_SLACK = 4          # zone is reserved OVERLAY_H + ZONE_SLACK high
ZONE_GAP_ACT = 6
LABEL_GAP = 4
ZONE_GAP_LABEL = 4
BAND_H = 60
POOL_GAP_MIN = 30
GAP_PAD = 10
EMPTY_ROW_H = 120
GROUP_PAD = 10
HALO = 8
GBORDER = 5

EXT_FONT = 11
EXT_LH = 13.2
EMB_FONT = 12
EMB_LH = 14.4
EMB_PAD = 7
MEASURE_SAFETY = 1.10
NODE_LABEL_WIDTHS = [90, 110, 130, 150]
EDGE_LABEL_WIDTHS = [90, 120, 150]

# routing costs (pixel equivalents)
BEND_COST = 30
CROSS_COST = 400
CROSS_COST_MSG = 150      # message flows are expected to cross sequence flows (vertical hand-offs)
MSG_HORIZ_FACTOR = 2      # horizontal length costs double for message flows (LAY-02)
TIE_EPS = 0.001
SINK_SHIFT = True         # an end event may move up to 2 columns right to stay on its predecessor's row (one per predecessor)
MSG_COLLINEAR_FACTOR = 0.0  # per px: message vertical on the x of another message vertical (other heights)
MSG_NEAR_FACTOR = 3.0     # per px: message vertical within MSG_NEAR_PX of another one over the same heights
MSG_NEAR_PX = 20
GAP_NEAR_PX = OVERLAY_W + 8  # in a pool gap a message flow label (+ zone) sits beside its vertical
GAP_NEAR_FACTOR = 2.0
GAP_HORIZ_FACTOR = 2.0    # extra per px for a horizontal message run inside a pool gap (label space, border)
OVERLAP_COST = 3000
DOCK_INSET = 12           # bottom message dock: px inside the activity's left / right edge (clear of the rounded corner)
DOCK_STEP = 14            # further bottom docks on the same side
DOCK_CORRIDOR = 26        # extra activity width per bottom message dock (dock inset + gap to the overlay zone)
MSG_MIN_RUN = 20          # straight run of a message flow at both ends (start circle, arrowhead)
MSG_SHORT_RUN_COST = 5000
HUG_PX = 16               # soft clearance band beside a foreign shape (hard halo: HALO px)
HUG_FACTOR = 1.0          # extra cost per px of running inside that band
BAND_CROSS_COST = 2500

DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]     # R, D, L, U (screen y grows down)
R, D, L, U = 0, 1, 2, 3
SIDE_OUT = {"R": R, "B": D, "L": L, "T": U}
SIDE_IN = {"L": R, "T": D, "R": L, "B": U}

ACTIVITY_TYPES = {"task", "call-activity"}
GATEWAY_TYPES = {"xor-split", "xor-join", "and-split", "and-join", "or-split", "or-join"}

# Arial / Liberation Sans advance widths, 1/1000 em (Helvetica-compatible metrics)
_AW = {" ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191,
       "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
       ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556, "@": 1015,
       "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556, "`": 333, "{": 334, "|": 260,
       "}": 334, "~": 584}
_AW.update({c: 556 for c in "0123456789"})
_AW.update(dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                    [667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833,
                     722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611])))
_AW.update(dict(zip("abcdefghijklmnopqrstuvwxyz",
                    [556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833,
                     556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500])))


# ------------------------------------------------------------------ text
def text_width(text, size):
    return sum(_AW.get(ch, 600) for ch in text) * size / 1000.0 * MEASURE_SAFETY


def _js_round(x):
    return int(math.floor(x + 0.5))


def _semantic_shorten(line, max_len):
    """Port of diagram-js Text.js semanticShorten (incl. its stop at empty parts)."""
    parts = re.split(r"(\s|-|\u00AD)", line)
    short, length = [], 0
    if len(parts) > 1:
        for part in parts:
            if not part:
                break
            if len(part) + length < max_len:
                short.append(part)
                length += len(part)
            else:
                if part in ("-", "\u00AD") and short:
                    short.pop()
                break
    if short and short[-1] == "\u00AD":
        short[-1] = "-"
    return "".join(short)


def _shorten_line(line, width, max_w):
    length = max(len(line) * (max_w / width), 1)
    s = _semantic_shorten(line, length)
    if not s:
        s = line[:max(_js_round(length - 1), 1)]
    return s


def wrap(text, max_w, size):
    """Line breaks as diagram-js Text.layoutText computes them (with estimated widths)."""
    lines = re.split(r"\u00AD?\r?\n", text or "")
    out = []
    while lines:
        original = lines.pop(0)
        fit = original
        while True:
            w = text_width(fit, size) if fit else 0
            if fit in (" ", "") or w <= max_w or len(fit) < 2:
                break
            fit = _shorten_line(fit, w, max_w)
        if len(fit) < len(original):
            lines.insert(0, original[len(fit):].strip())
        out.append(fit)
    return out or [""]


def _midword_breaks(lines):
    n = 0
    for a, b in zip(lines, lines[1:]):
        if a and b and a[-1].isalnum() and b[0].isalnum():
            n += 1
    return n


def ext_label_box(text, widths):
    """(width, height, lines) of an external label (bpmn-js wraps at the DI label width)."""
    cands = [(w, wrap(text, w, EXT_FONT)) for w in widths]
    pick = None
    for test in (lambda ls: len(ls) <= 2 and not _midword_breaks(ls),
                 lambda ls: len(ls) <= 2,
                 lambda ls: len(ls) <= 3 and not _midword_breaks(ls),
                 lambda ls: len(ls) <= 3):
        for w, ls in cands:
            if test(ls):
                pick = (w, ls)
                break
        if pick:
            break
    if pick is None:
        pick = cands[-1]
    w, lines = pick
    if len(lines) == 1:
        # one line: box hugs the text (estimate includes MEASURE_SAFETY, so no re-wrap)
        w = min(w, int(math.ceil(text_width(lines[0], EXT_FONT))) + 6)
    height = int(math.ceil(len(lines) * EXT_LH)) + 4
    return w, height, lines


def activity_size(text, call_activity, min_w=0):
    """Smallest standard size that fits the text; widened (same height) to min_w if needed."""
    w, h = _activity_size(text, call_activity)
    if w < min_w:
        w = int(math.ceil(min_w / 10.0)) * 10
    return (w, h)


def _activity_size(text, call_activity):
    reserve = 40 if call_activity else 12
    sizes = CALL_SIZES if call_activity else TASK_SIZES
    fitting = []
    for w, h in sizes:
        lines = wrap(text, w - 2 * EMB_PAD, EMB_FONT)
        if len(lines) * EMB_LH <= h - reserve:
            fitting.append(((w, h), lines))
    if not fitting:
        return sizes[-1]
    for (w, h), lines in fitting:
        if w > 180:
            break
        if not _midword_breaks(lines):
            return (w, h)
    return fitting[0][0]


def annotation_size(text):
    """bpmn-js renders annotation text left-top with padding 7 (12 px font)."""
    for w in ANNOT_WIDTHS:
        lines = wrap(text, w - 14, EMB_FONT)
        if len(lines) <= 4:
            break
    return w, int(math.ceil(len(lines) * EMB_LH)) + 18


# ------------------------------------------------------------------ geometry
def right(r):
    return r[0] + r[2]


def bottom(r):
    return r[1] + r[3]


def inflate(r, d):
    return (r[0] - d, r[1] - d, r[2] + 2 * d, r[3] + 2 * d)


def union(rects):
    x0 = min(r[0] for r in rects)
    y0 = min(r[1] for r in rects)
    x1 = max(right(r) for r in rects)
    y1 = max(bottom(r) for r in rects)
    return (x0, y0, x1 - x0, y1 - y0)


def rects_overlap(a, b):
    """True if the open interiors intersect."""
    return a[0] < right(b) and b[0] < right(a) and a[1] < bottom(b) and b[1] < bottom(a)


def seg_hits_rect(p, q, r):
    """Axis-parallel segment p-q intersects the open interior of rect r."""
    x0, y0, x1, y1 = r[0], r[1], right(r), bottom(r)
    if p[1] == q[1]:
        y = p[1]
        a, b = sorted((p[0], q[0]))
        return y0 < y < y1 and a < x1 and b > x0
    x = p[0]
    a, b = sorted((p[1], q[1]))
    return x0 < x < x1 and a < y1 and b > y0


def center(r):
    return (r[0] + r[2] // 2, r[1] + r[3] // 2)


# ------------------------------------------------------------------ pool order
SLOT_RANK = {"top": 0, "external": 1, "internal": 2, "bottom": 3}


def node_pools(spec):
    lane_pool = {l["id"]: l["pool"] for l in spec.get("lanes") or []}
    out = {}
    for n in spec["nodes"]:
        out[n["id"]] = lane_pool[n["lane"]] if n.get("lane") else n["pool"]
    return out


def pool_slots(specs):
    """Global vertical slot per pool id, identical on every diagram of a run.

    internal pool -> 'internal'; a pool that is an expanded external pool in any
    model -> 'external' (drawn above the internal pool, as a band where it is
    collapsed); of the remaining (always collapsed) pools the one with the
    highest share of message flows to 'external' pools goes 'top' (if there are
    two or more such pools, or its share is above one half), the rest 'bottom'.
    Returns {pool id: (slot rank, first-seen index)}.
    """
    order, kind = [], {}
    for spec in specs:
        for p in spec["pools"]:
            if p["id"] not in order:
                order.append(p["id"])
            if p["kind"] == "internal":
                kind[p["id"]] = "internal"
            elif p["expanded"]:
                kind[p["id"]] = "external"
    rest = [pid for pid in order if pid not in kind]
    ext, total = {}, {}
    for spec in specs:
        npool = node_pools(spec)
        for mf in spec.get("message_flows") or []:
            for a, b in ((mf["from"], mf["to"]), (mf["to"], mf["from"])):
                if a in rest:
                    other = npool.get(b, b)
                    total[a] = total.get(a, 0) + 1
                    if kind.get(other) == "external":
                        ext[a] = ext.get(a, 0) + 1
    for pid in rest:
        kind[pid] = "bottom"
    if rest:
        share = {pid: (ext.get(pid, 0) / total[pid]) if total.get(pid) else 0.0 for pid in rest}
        top = sorted(rest, key=lambda pid: (-share[pid], order.index(pid)))[0]
        if len(rest) >= 2 or share[top] > 0.5:
            kind[top] = "top"
    return {pid: (SLOT_RANK[kind[pid]], order.index(pid)) for pid in order}


# ------------------------------------------------------------------ layout
class LayoutResult:
    def __init__(self):
        self.shapes = {}        # spec id -> rect (pools, lanes, nodes, data, annotations, groups)
        self.labels = {}        # spec id -> rect
        self.edges = {}         # edge key -> [(x, y), ...]
        self.zones = {}         # spec id -> rect (overlay clearance, OVERLAY_H high)
        self.unit_of = {}
        self.pool_order = []
        self.columns = {}
        self.rows = {}
        self.warnings = []
        self.stats = {}


class ModelLayout:
    def __init__(self, spec, slots):
        self.spec = spec
        self.slots = slots
        self.res = LayoutResult()
        self.pools = {p["id"]: p for p in spec["pools"]}
        self.lanes = spec.get("lanes") or []
        self.nodes = spec["nodes"]
        self.node_by = {n["id"]: n for n in self.nodes}
        self.flows = spec.get("flows") or []
        self.flow_by = {f["id"]: f for f in self.flows}
        self.mflows = spec.get("message_flows") or []
        self.data = spec.get("data") or []
        self.annots = spec.get("annotations") or []
        self.groups = spec.get("groups") or []
        self.node_pool = node_pools(spec)
        self.size = {}
        self.label_size = {}
        self.has_zone = set()
        # all placed leaf elements: flow nodes, data, annotations (spec order)
        self.elems = [n["id"] for n in self.nodes] + [d["id"] for d in self.data] + [a["id"] for a in self.annots]
        self.kind = {}
        for n in self.nodes:
            t = n["type"]
            self.kind[n["id"]] = "activity" if t in ACTIVITY_TYPES else ("gateway" if t in GATEWAY_TYPES else "event")
        for d in self.data:
            self.kind[d["id"]] = "data"
        for a in self.annots:
            self.kind[a["id"]] = "annotation"
        # message flows dock on the activity edge that faces the other pool (LAY-02):
        # top if the other end lies in a pool above, bottom if below (pools are stacked)
        order = sorted([p["id"] for p in spec["pools"]], key=lambda pid: slots[pid])
        self.pool_idx = {pid: i for i, pid in enumerate(order)}
        self.msg_down = {}            # activity id -> [message flow ids leaving / entering its bottom edge]
        self.msg_facing = {}          # (message flow id, end ref) -> "up" | "down"
        for mf in self.mflows:
            for a, b in ((mf["from"], mf["to"]), (mf["to"], mf["from"])):
                pa = self.pool_idx[self.node_pool.get(a, a)]
                pb = self.pool_idx[self.node_pool.get(b, b)]
                facing = "down" if pb > pa else "up"
                self.msg_facing[(mf["id"], a)] = facing
                if facing == "down" and self.kind.get(a) == "activity":
                    self.msg_down.setdefault(a, []).append(mf["id"])

    # ---------------------------------------------------------------- run
    def run(self):
        self._sizes()
        self._columns()
        self._match_message_widths()
        self._rows()
        base_warnings = list(self.res.warnings)
        self.gap_extra = {}
        for attempt in range(4):
            res = LayoutResult()
            res.warnings = list(base_warnings)
            res.columns, res.rows, res.unit_of = self.res.columns, self.res.rows, self.res.unit_of
            self.res = res
            self.failed_mlabels = []
            self._coordinates()
            self._groups_prepare()
            self._route_all()
            self._place_edge_labels()
            if not self.failed_mlabels or attempt == 3:
                break
            for mid, crossed in self.failed_mlabels:
                lw, lh = self.mlabel[mid]
                for g in crossed:
                    self.gap_extra[g] = self.gap_extra.get(g, 0) + lh + 4 + OVERLAY_H + ZONE_SLACK + GAP_PAD
        for mid, crossed in self.failed_mlabels:
            self.res.warnings.append(f"message flow {mid}: no label position with free overlay zone")
        self._groups_finish()
        return self.res

    # ---------------------------------------------------------------- sizes
    def _sizes(self):
        for n in self.nodes:
            t = n["type"]
            if t in ACTIVITY_TYPES:
                nb = len(self.msg_down.get(n["id"], []))
                self.size[n["id"]] = activity_size(n.get("label", ""), t == "call-activity",
                                                   OVERLAY_W + DOCK_CORRIDOR * nb if nb else 0)
            elif t in GATEWAY_TYPES:
                self.size[n["id"]] = GATEWAY_SIZE
            else:
                self.size[n["id"]] = EVENT_SIZE
            if t not in ACTIVITY_TYPES and n.get("label"):
                self.label_size[n["id"]] = ext_label_box(n["label"], NODE_LABEL_WIDTHS)[:2]
            self.has_zone.add(n["id"])
        for d in self.data:
            self.size[d["id"]] = DATA_OBJECT_SIZE if d["type"] == "data-object" else DATA_STORE_SIZE
            self.label_size[d["id"]] = ext_label_box(d["label"], NODE_LABEL_WIDTHS)[:2]
            self.has_zone.add(d["id"])
        for a in self.annots:
            self.size[a["id"]] = annotation_size(a["text"])
            if a.get("src"):
                self.has_zone.add(a["id"])

    def _match_message_widths(self):
        """Two activities linked by a message flow in the same column get the same width, so
        that the bottom dock of one lines up with a top port of the other (vertical hand-off)."""
        for mf in self.mflows:
            a, b = mf["from"], mf["to"]
            if self.kind.get(a) == "activity" and self.kind.get(b) == "activity" and self.col[a] == self.col[b]:
                w = max(self.size[a][0], self.size[b][0])
                self.size[a] = (w, self.size[a][1])
                self.size[b] = (w, self.size[b][1])

    # ---------------------------------------------------------------- columns
    def _columns(self):
        order = {n["id"]: i for i, n in enumerate(self.nodes)}
        succ = {n["id"]: [] for n in self.nodes}
        for f in self.flows:
            succ[f["from"]].append((f["to"], f["id"]))
        color, back = {}, set()
        starts = [n["id"] for n in self.nodes if n["type"].startswith("start")]
        roots = starts + [n["id"] for n in self.nodes if n["id"] not in starts]
        for r0 in roots:
            if r0 in color:
                continue
            color[r0] = 1
            stack = [(r0, iter(succ[r0]))]
            while stack:
                v, it = stack[-1]
                nxt = next(it, None)
                if nxt is None:
                    color[v] = 2
                    stack.pop()
                    continue
                w, fid = nxt
                c = color.get(w, 0)
                if c == 1:
                    back.add(fid)
                elif c == 0:
                    color[w] = 1
                    stack.append((w, iter(succ[w])))
        self.back_edges = back
        edges = {n["id"]: [] for n in self.nodes}
        for f in self.flows:
            if f["id"] not in back:
                edges[f["from"]].append((f["to"], 1))

        def reaches(a, b):
            seen, todo = {a}, [a]
            while todo:
                v = todo.pop()
                if v == b:
                    return True
                for w, _ in edges[v]:
                    if w not in seen:
                        seen.add(w)
                        todo.append(w)
            return False

        for mf in self.mflows:
            a, b = mf["from"], mf["to"]
            if a in self.node_by and b in self.node_by:
                if not reaches(b, a):
                    edges[a].append((b, 0))
                else:
                    self.res.warnings.append(f"message flow {mf['id']}: column constraint dropped (would form a cycle)")
        indeg = {v: 0 for v in edges}
        for v in edges:
            for w, _ in edges[v]:
                indeg[w] += 1
        col = {v: 0 for v in edges}
        ready = [(order[v], v) for v in edges if indeg[v] == 0]
        heapq.heapify(ready)
        while ready:
            _, v = heapq.heappop(ready)
            for w, wt in edges[v]:
                col[w] = max(col[w], col[v] + wt)
                indeg[w] -= 1
                if indeg[w] == 0:
                    heapq.heappush(ready, (order[w], w))
        m = min(col.values()) if col else 0
        self.col = {v: c - m for v, c in col.items()}
        self.ncols = (max(self.col.values()) + 1) if self.col else 1
        self.res.columns = dict(self.col)

    # ---------------------------------------------------------------- rows
    def _unit_of_node(self, nid):
        n = self.node_by[nid]
        return n.get("lane") or n.get("pool")

    def _anchor_node(self, ref):
        """Node that places an artifact: the node itself or the source of a sequence flow."""
        return ref if ref in self.node_by else self.flow_by[ref]["from"]

    def _rows(self):
        occupied, row, unit = {}, {}, {}
        spec_idx = {n["id"]: i for i, n in enumerate(self.nodes)}
        mains = [n for n in self.nodes if n.get("path", "main") == "main"]
        others = sorted([n for n in self.nodes if n.get("path", "main") != "main"],
                        key=lambda n: (self.col[n["id"]], spec_idx[n["id"]]))
        main_ids = {n["id"] for n in mains}
        preds = {}
        outdeg = {}
        for f in self.flows:
            preds.setdefault(f["to"], []).append(f["from"])
            outdeg[f["from"]] = outdeg.get(f["from"], 0) + 1
        msg_nodes = {m["from"] for m in self.mflows} | {m["to"] for m in self.mflows}
        shifted_from = set()
        for n in mains + others:
            nid = n["id"]
            u = self._unit_of_node(nid)
            c = self.col[nid]
            if nid in main_ids:
                r = 0
            else:
                # keep a branch on the row of its predecessor (fewer bends, lower lanes)
                pr = [row[p] for p in preds.get(nid, []) if p in row and unit.get(p) == u]
                r = max(1, min(pr)) if pr else 1
                p0 = preds.get(nid, [None])[0]
                if (SINK_SHIFT and (u, r, c) in occupied and n["type"] == "end" and not outdeg.get(nid)
                        and nid not in msg_nodes and p0 not in shifted_from):
                    for k in (1, 2):
                        if c + k < self.ncols and (u, r, c + k) not in occupied:
                            c = c + k
                            self.col[nid] = c
                            shifted_from.add(p0)
                            break
            while (u, r, c) in occupied:
                r += 1
            occupied[(u, r, c)] = nid
            row[nid] = r
            unit[nid] = u
        self.res.columns = dict(self.col)
        # cells holding an activity with a message flow to a pool above: a data element placed above
        # it would block the vertical hand-off (LAY-02); annotations keep their column (reading order)
        up_dock = {(unit[n], row[n], self.col[n]) for (mid, n), f in self.msg_facing.items()
                   if f == "up" and n in row and self.kind.get(n) == "activity"}
        self.art_col = {}
        artifacts = [(d["id"], d["assoc"][0]["node"]) for d in self.data] + \
                    [(a["id"], self._anchor_node(a["assoc"][0])) for a in self.annots]
        for aid, first in artifacts:
            u = self._unit_of_node(first)
            c0 = self.col[first]
            if self.kind[aid] == "annotation" and a_is_flow(self, aid):
                f = self.flow_by[next(a for a in self.annots if a["id"] == aid)["assoc"][0]]
                c0 = min(self.col[f["from"]], self.col[f["to"]])
            prefs = [c for c in (c0 + 1, c0, c0 + 2, c0 - 1) if c >= 0]
            r = 1
            placed = False
            while not placed:
                for c in prefs:
                    if (u, r, c) not in occupied and not (self.kind[aid] == "data" and any(
                            (u, rr, c) in up_dock for rr in range(r))):
                        occupied[(u, r, c)] = aid
                        row[aid] = r
                        unit[aid] = u
                        self.art_col[aid] = c
                        self.ncols = max(self.ncols, c + 1)
                        placed = True
                        break
                r += 1
        per_unit = {}
        for eid, u in unit.items():
            per_unit.setdefault(u, set()).add(row[eid])
        remap = {u: {r: i for i, r in enumerate(sorted(rs))} for u, rs in per_unit.items()}
        self.row = {eid: remap[unit[eid]][r] for eid, r in row.items()}
        self.unit = unit
        self.res.rows = dict(self.row)
        self.res.unit_of = dict(unit)

    def _col_of(self, eid):
        return self.col[eid] if eid in self.col else self.art_col[eid]

    # ---------------------------------------------------------------- coordinates
    def _zone_top_rel(self, eid, h_row):
        """Zone top relative to the row's shape band top (shape centred in band of h_row)."""
        w, h = self.size[eid]
        shape_bottom = (h_row - h) // 2 + h
        if self.kind[eid] in ("activity", "annotation"):
            return shape_bottom + ZONE_GAP_ACT
        lh = self.label_size.get(eid, (0, 0))[1]
        if lh:
            return shape_bottom + LABEL_GAP + lh + ZONE_GAP_LABEL
        return shape_bottom + LABEL_GAP + ZONE_GAP_LABEL

    def _below(self, eid, h_row):
        if eid in self.has_zone:
            return self._zone_top_rel(eid, h_row) + OVERLAY_H + ZONE_SLACK - h_row
        w, h = self.size[eid]
        return (h_row - h) // 2 + h + 6 - h_row

    def _coordinates(self):
        res = self.res
        colw = [MIN_COL_W] * self.ncols
        for eid in self.elems:
            c = self._col_of(eid)
            colw[c] = max(colw[c], self.size[eid][0], self.label_size.get(eid, (0, 0))[0])
        self.colw = colw
        self.content_x0 = POOL_X + POOL_HEADER + LANE_HEADER + LEFT_MARGIN
        colx = [self.content_x0]
        for c in range(1, self.ncols):
            colx.append(colx[-1] + colw[c - 1] + COL_GAP)
        self.colx = colx
        content_x1 = colx[-1] + colw[-1] + RIGHT_MARGIN
        pool_w = content_x1 - POOL_X
        self.pool_w = pool_w

        order = sorted([p["id"] for p in self.spec["pools"]], key=lambda pid: self.slots[pid])
        res.pool_order = order
        units_of_pool = {}
        for pid in order:
            p = self.pools[pid]
            if not p["expanded"]:
                continue
            ls = [l["id"] for l in self.lanes if l["pool"] == pid]
            units_of_pool[pid] = ls if ls else [pid]
        unit_seq = [u for pid in order if pid in units_of_pool for u in units_of_pool[pid]]
        elems_of_unit = {}
        for eid in self.elems:
            elems_of_unit.setdefault(self.unit[eid], []).append(eid)
        unit_rows = {}
        for u, eids in elems_of_unit.items():
            rows = {}
            for eid in eids:
                rows.setdefault(self.row[eid], []).append(eid)
            unit_rows[u] = rows
        # rows that hold the top-most members of a group get room for the group header
        extra_top = {}
        for g in self.groups:
            lh = ext_label_box(g["label"], [150, 200, 250])[1]
            best = None
            for m in g["members"]:
                key = (unit_seq.index(self.unit[m]), -self.row[m])
                if best is None or key < best[0]:
                    best = (key, (self.unit[m], self.row[m]))
            if best:
                extra_top[best[1]] = max(extra_top.get(best[1], 0), GROUP_PAD + lh + 4 + 6 - TOP_PAD)
        row_h, row_hmax, row_top_pad, unit_h = {}, {}, {}, {}
        for u in unit_seq:
            rows = unit_rows.get(u, {})
            if not rows:
                unit_h[u] = EMPTY_ROW_H
                continue
            total = 0
            for r in sorted(rows):
                hmax = max(self.size[e][1] for e in rows[r])
                below = max(self._below(e, hmax) for e in rows[r])
                tp = TOP_PAD + max(0, extra_top.get((u, r), 0))
                row_hmax[(u, r)] = hmax
                row_top_pad[(u, r)] = tp
                row_h[(u, r)] = tp + hmax + below + BOTTOM_PAD
                total += row_h[(u, r)]
            unit_h[u] = total

        idx = {pid: i for i, pid in enumerate(order)}
        gap_need = [POOL_GAP_MIN] * max(0, len(order) - 1)
        self.mlabel = {}
        self.mgaps = {}
        for mf in self.mflows:
            lw, lh, _ = ext_label_box(mf["label"], EDGE_LABEL_WIDTHS)
            self.mlabel[mf["id"]] = (lw, lh)
            pa = idx[self.node_pool.get(mf["from"], mf["from"])]
            pb = idx[self.node_pool.get(mf["to"], mf["to"])]
            self.mgaps[mf["id"]] = list(range(min(pa, pb), max(pa, pb)))
            for g in self.mgaps[mf["id"]]:
                gap_need[g] = max(gap_need[g], GAP_PAD + lh + 4 + OVERLAY_H + ZONE_SLACK + GAP_PAD)
        for g, extra in self.gap_extra.items():
            gap_need[g] += extra
        self.gaps = []
        y = POOL_Y
        for i, pid in enumerate(order):
            p = self.pools[pid]
            h = sum(unit_h[u] for u in units_of_pool[pid]) if p["expanded"] else BAND_H
            res.shapes[pid] = (POOL_X, y, pool_w, h)
            if p["expanded"]:
                uy = y
                for u in units_of_pool[pid]:
                    if u != pid:
                        res.shapes[u] = (POOL_X + POOL_HEADER, uy, pool_w - POOL_HEADER, unit_h[u])
                    rows = unit_rows.get(u, {})
                    ry = uy
                    for r in sorted(rows, reverse=True):
                        hmax = row_hmax[(u, r)]
                        band_top = ry + row_top_pad[(u, r)]
                        for eid in sorted(rows[r], key=lambda e: self._col_of(e)):
                            w, h2 = self.size[eid]
                            c = self._col_of(eid)
                            cx = colx[c] + colw[c] // 2
                            res.shapes[eid] = (cx - w // 2, band_top + (hmax - h2) // 2, w, h2)
                        ry += row_h[(u, r)]
                    uy += unit_h[u]
            if i < len(order) - 1:
                gtop = y + h
                y = gtop + gap_need[i]
                self.gaps.append((gtop, y))
        self.unit_rect = {u: res.shapes[u] for u in unit_seq}
        self._assign_docks()
        for eid in self.elems:
            r = res.shapes[eid]
            cx = r[0] + r[2] // 2
            if eid in self.label_size:
                lw, lh = self.label_size[eid]
                res.labels[eid] = (cx - lw // 2, bottom(r) + LABEL_GAP, lw, lh)
            if eid not in self.has_zone:
                continue
            zw = max(OVERLAY_W, r[2])
            zx = cx - zw // 2
            if eid in self.msg_down:
                # bottom message docks: 150 px zone aligned away from the dock corridors
                zw, zx = OVERLAY_W, self._dock_zone_x(eid, r)
            if self.kind[eid] in ("activity", "annotation"):
                ztop = bottom(r) + ZONE_GAP_ACT
            elif eid in res.labels:
                ztop = bottom(res.labels[eid]) + ZONE_GAP_LABEL
            else:
                ztop = bottom(r) + LABEL_GAP + ZONE_GAP_LABEL
            res.zones[eid] = (zx, ztop, zw, OVERLAY_H)
        res.stats["width"] = pool_w + 2 * POOL_X
        res.stats["height"] = bottom(res.shapes[order[-1]]) + POOL_Y
        res.stats["columns"] = self.ncols

    # ---------------------------------------------------------------- message docks
    def _assign_docks(self):
        """Bottom dock x per (message flow, activity): flows whose other end lies left of the
        activity take the left corridor, the others the right one (two flows: one each side)."""
        res = self.res
        self.dock_x, self.dock_n = {}, {}
        for aid, mids in sorted(self.msg_down.items()):
            r = res.shapes[aid]
            own = self.col[aid]
            mf_by = {m["id"]: m for m in self.mflows}

            def other_col(mid):
                m = mf_by[mid]
                b = m["to"] if m["from"] == aid else m["from"]
                return self.col.get(b, own)
            order = sorted(mids, key=lambda mid: (other_col(mid), mids.index(mid)))
            if len(order) == 1:
                sides = ["L" if other_col(order[0]) < own else "R"]
            else:
                nl = len(order) // 2
                sides = ["L"] * nl + ["R"] * (len(order) - nl)
            kl = kr = 0
            for mid, side in zip(order, sides):
                if side == "L":
                    self.dock_x[(mid, aid)] = r[0] + DOCK_INSET + DOCK_STEP * kl
                    kl += 1
                else:
                    self.dock_x[(mid, aid)] = right(r) - DOCK_INSET - DOCK_STEP * kr
                    kr += 1
            self.dock_n[aid] = (kl, kr)
        # top-edge x positions that line up with a bottom dock in another pool (vertical hand-off)
        self.top_align = {}
        all_docks = sorted(set(self.dock_x.values()))
        for eid in self.elems:
            if self.kind[eid] != "activity":
                continue
            r = res.shapes[eid]
            lo, hi = r[0] + DOCK_INSET, right(r) - DOCK_INSET
            self.top_align[eid] = [x for x in all_docks if lo <= x <= hi]

    def _dock_zone_x(self, eid, r):
        nl, nr = self.dock_n[eid]
        return r[0] + nl * (r[2] - OVERLAY_W) // (nl + nr)

    # ---------------------------------------------------------------- groups
    def _groups_prepare(self):
        res = self.res
        self.group_label = {}
        for g in self.groups:
            rects = []
            for m in g["members"]:
                rects.append(res.shapes[m])
                if m in res.labels:
                    rects.append(res.labels[m])
                if m in res.zones:
                    rects.append(res.zones[m])
            u = union(rects)
            lw, lh, _ = ext_label_box(g["label"], [150, 200, 250])
            top = u[1] - GROUP_PAD - lh - 4
            box = (u[0] - GROUP_PAD, top, u[2] + 2 * GROUP_PAD, bottom(u) + GROUP_PAD - 2 - top)
            res.shapes[g["id"]] = box
            lw = min(lw, box[2] - 12)
            res.labels[g["id"]] = (box[0] + 6, box[1] + 4, lw, lh)
            self.group_label[g["id"]] = res.labels[g["id"]]

    def _groups_finish(self):
        res = self.res
        for g in self.groups:
            box = res.shapes[g["id"]]
            for eid in self.elems:
                if eid in g["members"] or not rects_overlap(box, res.shapes[eid]):
                    continue
                if self.kind[eid] in ("data", "annotation") and self._artifact_anchor(eid) in g["members"]:
                    continue        # artifact attached to a member may sit inside the frame
                res.warnings.append(f"group {g['id']} overlaps non-member {eid}")

    def _artifact_anchor(self, eid):
        for d in self.data:
            if d["id"] == eid:
                return d["assoc"][0]["node"]
        for a in self.annots:
            if a["id"] == eid:
                return self._anchor_node(a["assoc"][0])
        return None

    # ---------------------------------------------------------------- routing grid
    def _build_grid(self):
        res = self.res
        xs, ys = set(), set()
        for c in range(self.ncols):
            x0 = self.colx[c]
            x1 = x0 + self.colw[c]
            xs.add(x0 + self.colw[c] // 2)
            xs.update(x1 + t for t in CHANNEL_TRACKS)
        xs.update([self.content_x0 - 16, self.content_x0 - 32])
        for eid in self.elems:
            r = res.shapes[eid]
            cx, cy = center(r)
            xs.update([r[0], right(r), cx, cx - r[2] // 4, cx + r[2] // 4])
            if self.kind[eid] == "activity":
                xs.update([r[0] + DOCK_INSET, right(r) - DOCK_INSET])
                xs.update(self.top_align.get(eid, []))
            ys.update([r[1], bottom(r), cy, cy - r[3] // 4, cy + r[3] // 4, r[1] - 12, r[1] - 24])
            if eid in res.zones:
                ys.add(bottom(res.zones[eid]) + ZONE_SLACK + 4)
            elif eid in res.labels:
                ys.add(bottom(res.labels[eid]) + 6)
        xs.update(self.dock_x.values())
        for u, ur in self.unit_rect.items():
            ys.update([ur[1] + 8, ur[1] + 18])
        for (g0, g1) in self.gaps:
            ys.update([g0 + 8, (g0 + g1) // 2, g1 - 8])
        self.no_horiz_y = set()
        for pid in res.pool_order:
            pr = res.shapes[pid]
            ys.update([pr[1], bottom(pr)])
            self.no_horiz_y.update([pr[1], bottom(pr)])
        for u, ur in self.unit_rect.items():
            if u not in self.pools:
                self.no_horiz_y.update([ur[1], bottom(ur)])
        self.xs = sorted(xs)
        self.ys = sorted(ys)
        self.xi = {x: i for i, x in enumerate(self.xs)}
        self.yi = {y: j for j, y in enumerate(self.ys)}
        obst = []
        for eid in self.elems:
            r = res.shapes[eid]
            obst.append((r, eid, "shape"))
            obst.append((inflate(r, HALO), eid, "halo"))
            if eid in res.labels:
                obst.append((inflate(res.labels[eid], 3), eid, "label"))
            if eid in res.zones:
                # zone obstacle spans from the shape bottom to the zone bottom, 4 px wider
                # on each side, so that no edge squeezes between shape and zone or runs on its border
                z = res.zones[eid]
                zb = z[1] + OVERLAY_H + ZONE_SLACK
                obst.append(((z[0] - 4, bottom(r), z[2] + 8, zb - bottom(r)), eid, "zone"))
        for pid in res.pool_order:
            if not self.pools[pid]["expanded"]:
                obst.append((res.shapes[pid], pid, "band"))
        for gid, lr in self.group_label.items():
            obst.append((inflate(lr, 2), gid, "glabel"))
        self.obst = obst
        nx, ny = len(self.xs), len(self.ys)
        blocked = {}
        for idx, (r, owner, kind) in enumerate(obst):
            x0, y0, x1, y1 = r[0], r[1], right(r), bottom(r)
            j0, j1 = bisect_right(self.ys, y0), bisect_left(self.ys, y1)
            i0, i1 = max(0, bisect_right(self.xs, x0) - 1), bisect_left(self.xs, x1)
            for j in range(j0, j1):
                for i in range(i0, min(i1, nx - 1)):
                    if self.xs[i] < x1 and self.xs[i + 1] > x0:
                        blocked.setdefault((i, j, 0), []).append(idx)
            i0b, i1b = bisect_right(self.xs, x0), bisect_left(self.xs, x1)
            j0b, j1b = max(0, bisect_right(self.ys, y0) - 1), bisect_left(self.ys, y1)
            for i in range(i0b, i1b):
                for j in range(j0b, min(j1b, ny - 1)):
                    if self.ys[j] < y1 and self.ys[j + 1] > y0:
                        blocked.setdefault((i, j, 1), []).append(idx)
        self.blocked = blocked
        # soft clearance: unit segments running parallel to a shape border at HALO..HUG_PX px
        # (outside the hard halo) cost extra for edges that do not end at that shape
        hug = {}
        for eid in self.elems:
            r = res.shapes[eid]
            x0, y0, x1, y1 = r[0], r[1], right(r), bottom(r)
            for ylo, yhi in ((y0 - HUG_PX, y0 - HALO), (y1 + HALO, y1 + HUG_PX)):
                for j in range(bisect_left(self.ys, ylo), bisect_right(self.ys, yhi)):
                    for i in range(max(0, bisect_right(self.xs, x0) - 1), min(bisect_left(self.xs, x1), nx - 1)):
                        if self.xs[i] < x1 and self.xs[i + 1] > x0:
                            hug.setdefault((i, j, 0), []).append(eid)
            for xlo, xhi in ((x0 - HUG_PX, x0 - HALO), (x1 + HALO, x1 + HUG_PX)):
                for i in range(bisect_left(self.xs, xlo), bisect_right(self.xs, xhi)):
                    for j in range(max(0, bisect_right(self.ys, y0) - 1), min(bisect_left(self.ys, y1), ny - 1)):
                        if self.ys[j] < y1 and self.ys[j + 1] > y0:
                            hug.setdefault((i, j, 1), []).append(eid)
        # horizontal runs close to a pool or lane border read as running on it
        # (inside the pool only; pool gaps hold the message flow labels)
        bands = set()
        for u, ur in self.unit_rect.items():
            bands.add((ur[1] + 1, ur[1] + HUG_PX))
            bands.add((bottom(ur) - HUG_PX, bottom(ur) - 1))
        for ylo, yhi in sorted(bands):
            for j in range(bisect_left(self.ys, ylo), bisect_right(self.ys, yhi)):
                for i in range(nx - 1):
                    hug.setdefault((i, j, 0), []).append("_border")
        # group frames: running parallel within HUG_PX (outside the hard GBORDER band)
        for g in self.groups:
            gb = res.shapes[g["id"]]
            gx0, gy0, gx1, gy1 = gb[0], gb[1], right(gb), bottom(gb)
            for yl in (gy0, gy1):
                for ylo, yhi in ((yl - HUG_PX, yl - GBORDER), (yl + GBORDER, yl + HUG_PX)):
                    for j in range(bisect_left(self.ys, ylo), bisect_right(self.ys, yhi)):
                        for i in range(max(0, bisect_right(self.xs, gx0) - 1), min(bisect_left(self.xs, gx1), nx - 1)):
                            hug.setdefault((i, j, 0), []).append("_group")
            for xl in (gx0, gx1):
                for xlo, xhi in ((xl - HUG_PX, xl - GBORDER), (xl + GBORDER, xl + HUG_PX)):
                    for i in range(bisect_left(self.xs, xlo), bisect_right(self.xs, xhi)):
                        for j in range(max(0, bisect_right(self.ys, gy0) - 1), min(bisect_left(self.ys, gy1), ny - 1)):
                            hug.setdefault((i, j, 1), []).append("_group")
        self.hug = hug
        # group frames: edges may cross them but must not run along them (within GBORDER px)
        for g in self.groups:
            gb = res.shapes[g["id"]]
            for (x0, y0, x1, y1, orient) in ((gb[0], gb[1], gb[0], bottom(gb), 1), (right(gb), gb[1], right(gb), bottom(gb), 1),
                                             (gb[0], gb[1], right(gb), gb[1], 0), (gb[0], bottom(gb), right(gb), bottom(gb), 0)):
                idx = len(self.obst)
                rect = (x0 - GBORDER, y0 - GBORDER, x1 - x0 + 2 * GBORDER, y1 - y0 + 2 * GBORDER)
                self.obst.append((rect, g["id"], "gborder"))
                if orient == 1:      # vertical border: block vertical unit segments running inside the band
                    for i in range(bisect_right(self.xs, rect[0]), bisect_left(self.xs, right(rect))):
                        for j in range(max(0, bisect_right(self.ys, y0) - 1), min(bisect_left(self.ys, y1), ny - 1)):
                            if self.ys[j] < y1 and self.ys[j + 1] > y0:
                                blocked.setdefault((i, j, 1), []).append(idx)
                else:
                    for j in range(bisect_right(self.ys, rect[1]), bisect_left(self.ys, bottom(rect))):
                        for i in range(max(0, bisect_right(self.xs, x0) - 1), min(bisect_left(self.xs, x1), nx - 1)):
                            if self.xs[i] < x1 and self.xs[i + 1] > x0:
                                blocked.setdefault((i, j, 0), []).append(idx)
        self.seg_use = {}
        self.pt_h = {}
        self.pt_v = {}
        self.committed = {}
        self.msg_vx = {}          # x index -> number of message flows with a vertical segment there
        self.msg_vseg = {}        # (x index, y index) -> message flows using that vertical unit segment
        self.gap_rows = {j for j in range(ny - 1) for (g0, g1) in self.gaps
                         if g0 <= self.ys[j] and self.ys[j + 1] <= g1}
        self.gap_ys = {y for y in self.ys for (g0, g1) in self.gaps if g0 < y < g1}
        self.msg_keys = {mf["id"] for mf in self.mflows}

    @staticmethod
    def _seg_key(i, j, d):
        if d == R:
            return (i, j, 0)
        if d == L:
            return (i - 1, j, 0)
        if d == D:
            return (i, j, 1)
        return (i, j - 1, 1)

    # ---------------------------------------------------------------- ports
    def _ports(self, eid, purpose, key=None):
        x, y, w, h = self.res.shapes[eid]
        cx, cy = center(self.res.shapes[eid])
        if self.kind[eid] == "activity" and purpose == "message":
            # LAY-02: only the edge that faces the other pool; bottom = the assigned dock corridor
            if self.msg_facing.get((key, eid)) == "down":
                mine = self.dock_x.get((key, eid))
                return [("B", (dx, y + h), "mid" if dx == mine else "off")
                        for dx in sorted({v for (m, a), v in self.dock_x.items() if a == eid})]
            q = w // 4
            xs = sorted({cx, cx - q, cx + q, x + DOCK_INSET, x + w - DOCK_INSET} | set(self.top_align.get(eid, [])))
            return [("T", (tx, y), "mid" if tx == cx else "off") for tx in xs]
        ports = [("R", (x + w, cy), "mid"), ("L", (x, cy), "mid"), ("T", (cx, y), "mid"), ("B", (cx, y + h), "mid")]
        if self.kind[eid] == "gateway" and purpose in ("seq", "data"):
            # docking points on the upper diamond edges (third branch of a split / join);
            # routing starts on the bounding box, the waypoint sits on the diamond edge
            q = w // 4
            ports += [("T", (cx + q, y), "dia"), ("T", (cx - q, y), "dia")]
        if self.kind[eid] in ("activity", "annotation") and purpose in ("message", "data"):
            q, s = w // 4, h // 4
            ports += [("T", (cx - q, y), "off"), ("T", (cx + q, y), "off"),
                      ("B", (cx - q, y + h), "off"), ("B", (cx + q, y + h), "off"),
                      ("T", (x + DOCK_INSET, y), "off"), ("T", (x + w - DOCK_INSET, y), "off"),
                      ("R", (x + w, cy + s), "off"), ("L", (x, cy + s), "off"),
                      ("R", (x + w, cy - s), "off"), ("L", (x, cy - s), "off")]
            if purpose == "message":
                ports = [p for p in ports if not (p[0] in ("L", "R") and p[2] == "mid")]
        return ports

    def _port_cost(self, eid, side, kind, purpose, role):
        if purpose == "seq":
            extra = 25 if kind == "dia" else 0
            if role == "src":
                return {"R": 0, "T": 20, "B": 20, "L": 300}[side] + extra
            return {"L": 0, "T": 20, "B": 20, "R": 300}[side] + extra
        if purpose == "message":
            if side == "B" and self.kind.get(eid) == "activity":
                return 0 if kind == "mid" else 40          # the dock corridor assigned to this flow
            return (0 if kind == "mid" else 8) if side in ("T", "B") else 25
        if self.kind.get(eid) == "annotation":
            return 0 if side == "L" else 40          # association enters the bracket side
        return 0 if kind == "mid" else 6

    def _endpoint(self, ref, other_ref, purpose, role, key=None):
        out = []
        if ref in self.size:
            for side, pt, kind in self._ports(ref, purpose, key):
                if pt[0] not in self.xi or pt[1] not in self.yi:
                    continue
                d = SIDE_OUT[side] if role == "src" else SIDE_IN[side]
                out.append(((self.xi[pt[0]], self.yi[pt[1]]), d, self._port_cost(ref, side, kind, purpose, role)))
            return out
        if ref in self.flow_by:          # annotation association from a sequence flow
            cells = self.committed.get(ref, {}).get("cells", [])
            dirs = self.committed.get(ref, {}).get("dirs", [])
            for k in range(2, len(cells) - 2):
                if dirs[k] != dirs[k + 1]:
                    continue                      # corner
                axis_h = dirs[k] in (R, L)
                for d in ((U, D) if axis_h else (L, R)):
                    out.append((cells[k], d, 0))
            return out
        pr = self.res.shapes[ref]
        other_y = center(self.res.shapes[other_ref])[1] if other_ref in self.res.shapes else pr[1]
        if other_y > center(pr)[1]:
            y, d_out, d_in = bottom(pr), D, U
        else:
            y, d_out, d_in = pr[1], U, D
        j = self.yi[y]
        for x in self.xs:
            if x < self.content_x0 - 32 or x > right(pr) - 20:
                continue
            out.append(((self.xi[x], j), d_out if role == "src" else d_in, 0))
        return out

    # ---------------------------------------------------------------- dijkstra
    def _seg_cost(self, key, allowed, purpose):
        """None if the unit segment is blocked, else the extra cost of using it."""
        if key[2] == 0 and self.ys[key[1]] in self.no_horiz_y:
            return None
        bl = self.blocked.get(key)
        if not bl:
            return 0
        extra = 0
        for idx in bl:
            r, owner, kind = self.obst[idx]
            if kind == "halo" and owner in allowed:
                continue
            if kind == "band" and purpose == "message" and owner not in allowed and key[2] == 1:
                extra += BAND_CROSS_COST   # crossing a black-box pool band vertically
                continue
            return None
        return extra

    def _route(self, src_ref, tgt_ref, purpose, bounds, key=None):
        sources = self._endpoint(src_ref, tgt_ref, purpose, "src", key)
        targets = {}
        for pt, d, cost in self._endpoint(tgt_ref, src_ref, purpose, "tgt", key):
            if (pt, d) not in targets or cost < targets[(pt, d)]:
                targets[(pt, d)] = cost
        allowed = {src_ref, tgt_ref}
        xs, ys = self.xs, self.ys
        nx, ny = len(xs), len(ys)
        bx0, by0, bx1, by1 = bounds
        cross_cost = CROSS_COST_MSG if purpose == "message" else CROSS_COST
        src_x = center(self.res.shapes[src_ref])[0] if src_ref in self.size else None
        # own endpoint shapes: edges must not run along their bounding-box lines
        own_rects = [self.res.shapes[r] for r in (src_ref, tgt_ref) if r in self.size]

        def on_own_border(i, j, nd):
            for r in own_rects:
                if nd in (R, L):
                    y = ys[j]
                    if y in (r[1], bottom(r)):
                        a, b = sorted((xs[i], xs[i + (1 if nd == R else -1)]))
                        if a < right(r) + HALO and b > r[0] - HALO:
                            return True
                else:
                    x = xs[i]
                    if x in (r[0], right(r)):
                        a, b = sorted((ys[j], ys[j + (1 if nd == D else -1)]))
                        if a < bottom(r) + HALO and b > r[1] - HALO:
                            return True
            return False
        dist, prev, heap, cnt = {}, {}, [], 0
        for pt, d, cost in sources:
            st = (pt[0], pt[1], d, 0, 0, 0)     # + run since the last bend (message flows, capped), bent yet
            if cost < dist.get(st, 1e18):
                dist[st] = cost
                prev[st] = None
                heap.append((cost, cnt, st))
                cnt += 1
        heapq.heapify(heap)
        final = None
        while heap:
            cost, _, st = heapq.heappop(heap)
            if cost > dist.get(st, 1e18):
                continue
            i, j, d, phase, run, bent = st
            if phase == 2:
                final = st
                break
            for nd in ((d,) if phase == 0 else (d, (d + 1) % 4, (d + 3) % 4)):
                di, dj = DIRS[nd]
                ni, nj = i + di, j + dj
                if not (0 <= ni < nx and 0 <= nj < ny):
                    continue
                px, py = xs[ni], ys[nj]
                if not (bx0 <= px <= bx1 and by0 <= py <= by1):
                    continue
                key = self._seg_key(i, j, nd)
                extra = self._seg_cost(key, allowed, purpose)
                if extra is None or (own_rects and on_own_border(i, j, nd)):
                    continue
                step = abs(px - xs[i]) + abs(py - ys[j])
                c2 = cost + step + extra
                if purpose == "message" and nd in (R, L):
                    c2 += step * (MSG_HORIZ_FACTOR - 1)
                    if self.ys[j] in self.gap_ys:
                        c2 += step * GAP_HORIZ_FACTOR
                if purpose == "message" and nd in (U, D) and self.msg_vx:
                    jlo = key[1]
                    if self.msg_vx.get(i) and (i, jlo) not in self.msg_vseg:
                        c2 += step * MSG_COLLINEAR_FACTOR
                    for di2 in (-2, -1, 1, 2):
                        i2 = i + di2
                        if 0 <= i2 < nx and (i2, jlo) in self.msg_vseg and abs(xs[i2] - xs[i]) < MSG_NEAR_PX:
                            c2 += step * MSG_NEAR_FACTOR
                            break
                    if jlo in self.gap_rows:
                        lo = bisect_left(xs, xs[i] - GAP_NEAR_PX + 1)
                        hi = bisect_right(xs, xs[i] + GAP_NEAR_PX - 1)
                        if any((i2, jlo) in self.msg_vseg for i2 in range(lo, hi) if i2 != i):
                            c2 += step * GAP_NEAR_FACTOR
                if purpose == "message":
                    nrun, nbent = (min(run + step, MSG_MIN_RUN), bent) if nd == d else (min(step, MSG_MIN_RUN), 1)
                    if nd != d and run < MSG_MIN_RUN:
                        c2 += MSG_SHORT_RUN_COST      # run before this bend too short (start run or a jog)
                else:
                    nrun, nbent = 0, 0
                if nd != d:
                    c2 += BEND_COST
                    if nd in (U, D) and src_x is not None:
                        c2 += TIE_EPS * abs(xs[i] - src_x)   # tie-break: turn vertical near the source
                if key in self.seg_use:
                    c2 += OVERLAP_COST + step * 5
                hg = self.hug.get(key)
                if hg and any(o not in allowed for o in hg):
                    c2 += step * HUG_FACTOR
                if nd in (R, L):
                    if self.pt_v.get((ni, nj)):
                        c2 += cross_cost
                elif self.pt_h.get((ni, nj)):
                    c2 += cross_cost
                tc = targets.get(((ni, nj), nd))
                if tc is not None:
                    if purpose == "message" and nbent and nrun < MSG_MIN_RUN:
                        tc = tc + MSG_SHORT_RUN_COST      # final run into the target too short
                    fs = (ni, nj, nd, 2, nrun, nbent)
                    if c2 + tc < dist.get(fs, 1e18):
                        dist[fs] = c2 + tc
                        prev[fs] = st
                        heapq.heappush(heap, (c2 + tc, cnt, fs))
                        cnt += 1
                ns = (ni, nj, nd, 1, nrun, nbent)
                if c2 < dist.get(ns, 1e18):
                    dist[ns] = c2
                    prev[ns] = st
                    heapq.heappush(heap, (c2, cnt, ns))
                    cnt += 1
        if final is None:
            return None
        pts = []
        st = final
        while st is not None:
            pts.append(st)
            st = prev[st]
        pts.reverse()
        return pts

    def _commit(self, key, states):
        cells = [(s[0], s[1]) for s in states]
        dirs = [s[2] for s in states]
        segs, hp, vp = [], [], []
        for k in range(1, len(cells)):
            sk = self._seg_key(cells[k - 1][0], cells[k - 1][1], dirs[k])
            segs.append(sk)
            self.seg_use[sk] = self.seg_use.get(sk, 0) + 1
        for k, cell in enumerate(cells):
            h = (k > 0 and dirs[k] in (R, L)) or (k + 1 < len(cells) and dirs[k + 1] in (R, L))
            v = (k > 0 and dirs[k] in (U, D)) or (k + 1 < len(cells) and dirs[k + 1] in (U, D))
            if h:
                self.pt_h[cell] = self.pt_h.get(cell, 0) + 1
                hp.append(cell)
            if v:
                self.pt_v[cell] = self.pt_v.get(cell, 0) + 1
                vp.append(cell)
        vx = []
        if key in self.msg_keys:
            vx = sorted({cells[k][0] for k in range(1, len(cells)) if dirs[k] in (U, D)})
            for i in vx:
                self.msg_vx[i] = self.msg_vx.get(i, 0) + 1
            for sk in segs:
                if sk[2] == 1:
                    self.msg_vseg[(sk[0], sk[1])] = self.msg_vseg.get((sk[0], sk[1]), 0) + 1
        self.committed[key] = {"cells": cells, "dirs": dirs, "segs": segs, "hp": hp, "vp": vp, "vx": vx}

    def _uncommit(self, key):
        c = self.committed.pop(key, None)
        if not c:
            return
        for sk in c["segs"]:
            self.seg_use[sk] -= 1
            if not self.seg_use[sk]:
                del self.seg_use[sk]
        for cell in c["hp"]:
            self.pt_h[cell] -= 1
            if not self.pt_h[cell]:
                del self.pt_h[cell]
        for cell in c["vp"]:
            self.pt_v[cell] -= 1
            if not self.pt_v[cell]:
                del self.pt_v[cell]
        for i in c.get("vx", []):
            self.msg_vx[i] -= 1
            if not self.msg_vx[i]:
                del self.msg_vx[i]
        if key in self.msg_keys:
            for sk in c["segs"]:
                if sk[2] == 1:
                    self.msg_vseg[(sk[0], sk[1])] -= 1
                    if not self.msg_vseg[(sk[0], sk[1])]:
                        del self.msg_vseg[(sk[0], sk[1])]

    @staticmethod
    def _simplify(points):
        out = []
        for p in points:
            if out and out[-1] == p:
                continue
            if len(out) >= 2:
                a, b = out[-2], out[-1]
                if (a[0] == b[0] == p[0]) or (a[1] == b[1] == p[1]):
                    out[-1] = p
                    continue
            out.append(p)
        return out

    def _jobs(self):
        res = self.res
        jobs = []
        # straight same-row connections with no element between them go first, so
        # that they keep the straight line (LAY-01); then the rest in spec order
        cells = {}
        for eid in self.elems:
            cells[(self.unit[eid], self.row[eid], self._col_of(eid))] = eid
        straight, rest = [], []
        for f in self.flows:
            a, b = f["from"], f["to"]
            same = (self.unit[a] == self.unit[b] and self.row[a] == self.row[b] and self.col[b] > self.col[a]
                    and all((self.unit[a], self.row[a], c) not in cells for c in range(self.col[a] + 1, self.col[b])))
            (straight if same else rest).append(f)
        for f in straight + rest:
            jobs.append((f["id"], f["from"], f["to"], "seq", self.node_pool[f["from"]]))
        for mf in self.mflows:
            jobs.append((mf["id"], mf["from"], mf["to"], "message", None))
        for d in self.data:
            for a in d["assoc"]:
                key = ("assoc", d["id"], a["node"], a["dir"])
                if a["dir"] == "out":
                    jobs.append((key, a["node"], d["id"], "data", self.node_pool[a["node"]]))
                else:
                    jobs.append((key, d["id"], a["node"], "data", self.node_pool[a["node"]]))
        for t in self.annots:
            for ref in t["assoc"]:
                pool = self.node_pool[self._anchor_node(ref)]
                jobs.append((("annot", t["id"], ref), ref, t["id"], "data", pool))
        return jobs

    def _bounds(self, pool):
        res = self.res
        if pool is not None:
            pr = res.shapes[pool]
            return (self.content_x0 - 32, pr[1] + 4, right(pr) - 10, bottom(pr) - 4)
        top = res.shapes[res.pool_order[0]][1]
        last = res.shapes[res.pool_order[-1]]
        return (self.content_x0 - 32, top, POOL_X + self.pool_w - 10, bottom(last))

    def _add_obstacle(self, rect, owner, kind):
        """Add one obstacle after the grid was built (sequence flow labels)."""
        idx = len(self.obst)
        self.obst.append((rect, owner, kind))
        nx, ny = len(self.xs), len(self.ys)
        x0, y0, x1, y1 = rect[0], rect[1], right(rect), bottom(rect)
        j0, j1 = bisect_right(self.ys, y0), bisect_left(self.ys, y1)
        i0, i1 = max(0, bisect_right(self.xs, x0) - 1), bisect_left(self.xs, x1)
        for j in range(j0, j1):
            for i in range(i0, min(i1, nx - 1)):
                if self.xs[i] < x1 and self.xs[i + 1] > x0:
                    self.blocked.setdefault((i, j, 0), []).append(idx)
        i0b, i1b = bisect_right(self.xs, x0), bisect_left(self.xs, x1)
        j0b, j1b = max(0, bisect_right(self.ys, y0) - 1), bisect_left(self.ys, y1)
        for i in range(i0b, i1b):
            for j in range(j0b, min(j1b, ny - 1)):
                if self.ys[j] < y1 and self.ys[j + 1] > y0:
                    self.blocked.setdefault((i, j, 1), []).append(idx)

    def _route_set(self, jobs, passes):
        res = self.res
        for key, a, b, purpose, pool in jobs:
            st = self._route(a, b, purpose, self._bounds(pool), key)
            if st is None:
                res.warnings.append(f"edge {key}: no obstacle-free route, fallback used")
                continue
            self._commit(key, st)
        # rip-up and reroute passes: every edge is routed again with all others in place
        for _ in range(passes):
            for key, a, b, purpose, pool in jobs:
                if key not in self.committed:
                    continue
                old = self.committed[key]
                self._uncommit(key)
                st = self._route(a, b, purpose, self._bounds(pool), key)
                if st is None:
                    self._commit(key, [(c[0], c[1], d, 1) for c, d in zip(old["cells"], old["dirs"])])
                else:
                    self._commit(key, st)

    def _route_all(self):
        """Order: sequence flows (+ rip-up, pair swaps), their labels (then obstacles),
        message flows and data associations (+ rip-up), annotation associations."""
        self._build_grid()
        res = self.res
        all_jobs = self._jobs()
        seq = [j for j in all_jobs if j[3] == "seq"]
        late = [j for j in all_jobs if isinstance(j[0], tuple) and j[0][0] == "annot"]
        other = [j for j in all_jobs if j[3] != "seq" and j not in late]
        self._route_set(seq, 2)
        self._swap_crossing_pairs(seq)
        self._swap_crossing_pairs(seq)
        self._store_edges(seq)
        self.placed_labels = []
        self.placed_zones = []
        self._place_seq_labels()
        for fid, box in self.placed_labels:
            self._add_obstacle(inflate(box, 2), fid, "flabel")
        self._route_set(other, 2)
        self._route_set(late, 0)
        self._store_edges(all_jobs)
        res.stats["grid"] = [len(self.xs), len(self.ys)]

    def _store_edges(self, jobs):
        res = self.res
        for key, a, b, purpose, pool in jobs:
            c = self.committed.get(key)
            if c is None:
                res.edges[key] = self._fallback(a, b)
                continue
            pts = [(self.xs[i], self.ys[j]) for i, j in c["cells"]]
            pts = self._dock_diamond(a, pts, 0)
            pts = self._dock_diamond(b, pts, -1)
            res.edges[key] = self._simplify(pts)

    def _segs_of(self, key):
        c = self.committed.get(key)
        if not c:
            return []
        pts = self._simplify([(self.xs[i], self.ys[j]) for i, j in c["cells"]])
        return list(zip(pts, pts[1:]))

    def _cross_between(self, k1, k2):
        n = 0
        for a, b in self._segs_of(k1):
            for c, d in self._segs_of(k2):
                if a[1] == b[1] and c[0] == d[0]:
                    h, v = (a, b), (c, d)
                elif a[0] == b[0] and c[1] == d[1]:
                    h, v = (c, d), (a, b)
                else:
                    continue
                x0, x1 = sorted((h[0][0], h[1][0]))
                y0, y1 = sorted((v[0][1], v[1][1]))
                if x0 < v[0][0] < x1 and y0 < h[0][1] < y1:
                    n += 1
        return n

    def _cross_total(self, keys):
        allk = list(self.committed)
        n = 0
        for k in keys:
            for o in allk:
                if o != k:
                    n += self._cross_between(k, o)
        return n

    def _swap_crossing_pairs(self, jobs):
        """Flows that leave (or enter) the same node and cross each other: route the pair in
        the reverse order and keep the result if it has fewer crossings (port swap)."""
        by_key = {j[0]: j for j in jobs}
        groups = {}
        for key, a, b, purpose, pool in jobs:
            if purpose == "seq":
                groups.setdefault(("src", a), []).append(key)
                groups.setdefault(("tgt", b), []).append(key)
        for gkey in sorted(groups, key=lambda g: (g[0], g[1])):
            keys = groups[gkey]
            for x in range(len(keys)):
                for y in range(x + 1, len(keys)):
                    k1, k2 = keys[x], keys[y]
                    if k1 not in self.committed or k2 not in self.committed or not self._cross_between(k1, k2):
                        continue
                    before = self._cross_total([k1, k2])
                    old = {k: self.committed[k] for k in (k1, k2)}
                    self._uncommit(k1)
                    self._uncommit(k2)
                    ok = True
                    for k in (k2, k1):
                        _, a, b, purpose, pool = by_key[k]
                        st = self._route(a, b, purpose, self._bounds(pool), k)
                        if st is None:
                            ok = False
                            break
                        self._commit(k, st)
                    if ok and self._cross_total([k1, k2]) < before:
                        continue
                    for k in (k1, k2):
                        self._uncommit(k)
                    for k in (k1, k2):
                        o = old[k]
                        self._commit(k, [(c[0], c[1], d, 1) for c, d in zip(o["cells"], o["dirs"])])

    def _dock_diamond(self, ref, pts, k):
        """Move an endpoint on a gateway's bounding box top (off the vertex) onto the diamond edge."""
        if ref not in self.kind or self.kind[ref] != "gateway" or len(pts) < 2:
            return pts
        x, y, w, h = self.res.shapes[ref]
        cx, cy = center(self.res.shapes[ref])
        px, py = pts[k]
        if py == y and px != cx and abs(px - cx) <= w // 2:
            pts = list(pts)
            pts[k] = (px, cy - (h // 2 - abs(px - cx)))
        return pts

    def _fallback(self, a, b):
        ca = center(self.res.shapes[a]) if a in self.res.shapes else (0, 0)
        cb = center(self.res.shapes[b]) if b in self.res.shapes else ca
        mx = (ca[0] + cb[0]) // 2
        return [ca, (mx, ca[1]), (mx, cb[1]), cb]

    # ---------------------------------------------------------------- edge labels
    def _label_ok(self, box, extra_free=None):
        res = self.res
        for r, owner, kind in self.obst:
            if kind in ("halo", "flabel", "gborder"):
                continue
            rr = inflate(r, 2) if kind == "shape" else r
            if rects_overlap(box, rr) or (extra_free and rects_overlap(extra_free, rr)):
                return False
        for k, lr in self.placed_labels:
            if rects_overlap(box, inflate(lr, 2)) or (extra_free and rects_overlap(extra_free, lr)):
                return False
        for k, z in self.placed_zones:
            if rects_overlap(box, z) or (extra_free and rects_overlap(extra_free, z)):
                return False
        for k, pts in res.edges.items():
            for a, b in zip(pts, pts[1:]):
                if seg_hits_rect(a, b, inflate(box, 2)):
                    return False
                if extra_free and seg_hits_rect(a, b, extra_free):
                    return False
        return True

    def _crosses_border(self, box):
        for pid in self.res.pool_order:
            pr = self.res.shapes[pid]
            inside = box[0] >= pr[0] and right(box) <= right(pr) and box[1] >= pr[1] and bottom(box) <= bottom(pr)
            if rects_overlap(box, pr) and not inside:
                return True
        for u, ur in self.unit_rect.items():
            if u in self.pools:
                continue
            inside = box[1] >= ur[1] and bottom(box) <= bottom(ur)
            if rects_overlap(box, ur) and not inside:
                return True
        return False

    def _place_seq_labels(self):
        res = self.res
        for f in self.flows:
            if not f.get("label"):
                continue
            pts = res.edges.get(f["id"], [])
            box = None
            shapes_tried = []
            for widths in (EDGE_LABEL_WIDTHS, [150], [120], [90]):
                lw, lh, lines = ext_label_box(f["label"], widths)
                if (lw, lh) in shapes_tried:
                    continue
                shapes_tried.append((lw, lh))
                box = self._find_label(pts, lw, lh, need_zone=False)
                if box is not None:
                    break
            lw, lh = shapes_tried[0]
            if box is None:
                res.warnings.append(f"sequence flow {f['id']}: no free label position, least-conflict position used")
                box = self._least_bad_label(pts, lw, lh) or self._default_label(pts, lw, lh)
            res.labels[f["id"]] = box
            self.placed_labels.append((f["id"], box))

    def _place_edge_labels(self):
        """Message flow labels (sequence flow labels are placed during routing)."""
        res = self.res
        for mf in self.mflows:
            lw, lh = self.mlabel[mf["id"]]
            pts = res.edges.get(mf["id"], [])
            box = self._find_label(pts, lw, lh, need_zone=True, prefer_gaps=True)
            if box is None:
                self.failed_mlabels.append((mf["id"], self.mgaps.get(mf["id"], [])))
                box = self._find_label(pts, lw, lh, need_zone=False) or self._default_label(pts, lw, lh)
            res.labels[mf["id"]] = box
            self.placed_labels.append((mf["id"], box))
            zone = (box[0], bottom(box) + 4, OVERLAY_W, OVERLAY_H)
            res.zones[mf["id"]] = zone
            self.placed_zones.append((mf["id"], zone))

    def _candidates(self, pts, lw, lh, prefer_gaps):
        gap_c, other_c = [], []
        for a, b in zip(pts, pts[1:]):
            if a[1] == b[1]:
                x0, x1 = sorted((a[0], b[0]))
                y = a[1]
                xs = [x0 + 8, (x0 + x1) // 2 - lw // 2, x1 - 8 - lw] if a[0] < b[0] else [x1 - 8 - lw, (x0 + x1) // 2 - lw // 2, x0 + 8]
                for x in xs:
                    if x < x0 - lw or x > x1:
                        continue
                    other_c.append((x, y - 5 - lh, lw, lh))
                    other_c.append((x, y + 5, lw, lh))
            else:
                y0, y1 = sorted((a[1], b[1]))
                x = a[0]
                for g0, g1 in self.gaps:
                    pitch = lh + 4 + OVERLAY_H + ZONE_SLACK + 6
                    if y0 <= g0 and y1 >= g1:
                        yy = g0 + GAP_PAD
                        while yy + lh + 4 + OVERLAY_H + ZONE_SLACK <= g1 - 2 or yy == g0 + GAP_PAD:
                            gap_c.append((x + 6, yy, lw, lh))
                            gap_c.append((x - 6 - lw, yy, lw, lh))
                            yy += pitch
                    elif max(y0, g0) < min(y1, g1):
                        # the vertical covers part of the gap (the flow turns inside it)
                        lo, hi = max(y0, g0), min(y1, g1)
                        yy = max(lo, g0 + GAP_PAD)
                        while yy + lh + 4 + OVERLAY_H + ZONE_SLACK <= min(hi, g1 - 2):
                            gap_c.append((x + 6, yy, lw, lh))
                            gap_c.append((x - 6 - lw, yy, lw, lh))
                            yy += pitch
                ys = list(range(y0 + 8, max(y0 + 9, y1 - lh - 8), 20))
                if a[1] > b[1]:
                    ys = list(reversed(ys))
                for yy in ys:
                    other_c.append((x + 6, yy, lw, lh))
                    other_c.append((x - 6 - lw, yy, lw, lh))
        return (gap_c + other_c) if prefer_gaps else (other_c + gap_c)

    def _label_conflicts(self, box):
        """Weighted conflict count of a label position (fallback when no free spot exists)."""
        score = 0
        for r, owner, kind in self.obst:
            if kind not in ("halo", "flabel", "gborder") and rects_overlap(box, r):
                score += 100
        for k, lr in self.placed_labels:
            if rects_overlap(box, lr):
                score += 50
        for k, pts in self.res.edges.items():
            for a, b in zip(pts, pts[1:]):
                if seg_hits_rect(a, b, box):
                    score += 1
        if self._crosses_border(box):
            score += 100
        return score

    def _least_bad_label(self, pts, lw, lh):
        best = None
        for box in self._candidates(pts, lw, lh, False):
            sc = self._label_conflicts(box)
            if best is None or sc < best[0]:
                best = (sc, box)
        return best[1] if best else None

    def _find_label(self, pts, lw, lh, need_zone, prefer_gaps=False):
        if len(pts) < 2:
            return None
        for box in self._candidates(pts, lw, lh, prefer_gaps):
            zone = (box[0], bottom(box) + 4, OVERLAY_W, OVERLAY_H + ZONE_SLACK) if need_zone else None
            if self._crosses_border(box) or (zone and self._crosses_border(zone)):
                continue
            if box[0] < self.content_x0 - 40 or right(box) > POOL_X + self.pool_w - 4:
                continue
            if zone and right(zone) > POOL_X + self.pool_w - 4:
                continue
            if self._label_ok(box, zone):
                return box
        return None

    def _default_label(self, pts, lw, lh):
        if len(pts) < 2:
            return (0, 0, lw, lh)
        a, b = pts[0], pts[1]
        return ((a[0] + b[0]) // 2 + 6, (a[1] + b[1]) // 2 + 6, lw, lh)


def a_is_flow(ml, aid):
    t = next(a for a in ml.annots if a["id"] == aid)
    return t["assoc"][0] in ml.flow_by


def layout_model(spec, slots):
    return ModelLayout(spec, slots).run()
