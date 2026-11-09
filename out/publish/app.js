/* iPD viewer - page logic (W1). Plain ES2019, no external requests, no dialogs, no window.open.
   Data: #ipd-data (citations.json), #ipd-bpmn (BPMN XML string), #ipd-moddle (ipd moddle descriptor). */
(function () {
  'use strict';

  var D = JSON.parse(document.getElementById('ipd-data').textContent);
  var XML = JSON.parse(document.getElementById('ipd-bpmn').textContent);
  var MODDLE = JSON.parse(document.getElementById('ipd-moddle').textContent);
  var EL = D.elements;
  var FIND = D.findings || {};
  // the page embeds REQ findings by id; resolve them once
  Object.keys(EL).forEach(function (id) {
    EL[id].reqs.forEach(function (r) {
      r.findings = r.findings.map(function (f) { return typeof f === 'string' ? (FIND[f] || { id: f, missing: true }) : f; });
    });
  });
  var DIAGRAMS = D.diagrams;
  var META = D.meta;
  var byHash = {}, byId = {};
  DIAGRAMS.forEach(function (d) { byHash[d.hash] = d; byId[d.id] = d; });
  var ROOT_D = DIAGRAMS.filter(function (d) { return d.level === 'L3'; })[0] || DIAGRAMS[0];
  var STORE_KEY = 'ipd-viewer-filters-v1';
  var BADGE_TEXT = {
    LAW: 'Binding law - regulation or statute (EU CTR, 21 CFR)',
    ICH: 'ICH guideline - binding through regional adoption; the route is shown in the side panel',
    GUIDANCE: 'Agency guidance - not legally binding',
    DRAFT: 'Rests (also) on draft guidance - shown next to the binding badge; draft guidance is never the only basis of a binding step',
    BP: 'Industry best practice or data standard',
    VERIFY: 'Binding class, numbering or content still to be verified'
  };
  var BINDING_BADGE = { 'binding-law': 'LAW', 'binding-ICH': 'ICH', 'guidance': 'GUIDANCE',
    'best-practice': 'BP', 'verify-binding': 'VERIFY' };

  var state = {
    diagram: null, selected: null, pendingSelect: null,
    filters: { binding: '', jur: '', keys: [], q: '' },
    chain: Promise.resolve(), chipsSkipped: [],
    view: null,          // default view applied on open: { mode: 'readable' | 'fit', fit, zoom, pool, start }
    minimapUser: null    // null until the user toggles the minimap; then the choice holds for all diagrams
  };

  function $(sel, root) { return (root || document).querySelector(sel); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function badge(b) { return '<span class="b b-' + esc(b) + '">' + esc(b) + '</span>'; }
  // MAY: every REQ of the element has modal 'may'. Own class (not .b): it is not a binding class.
  var MAY_TEXT = 'MAY - every requirement of this element is optional (modal "may"); not a binding class';
  function mayChip() { return '<span class="ipd-may" title="' + esc(MAY_TEXT) + '">MAY</span>'; }
  function badgesHtml(rec, sep) {
    // binding badge, the MAY chip right next to it, then DRAFT / VERIFY
    var out = rec.badges.map(badge), i = rec.badges.indexOf(BINDING_BADGE[rec.binding] || '-');
    if (rec.may_only) out.splice(i + 1, 0, mayChip());
    return out.join(sep || '');
  }
  function hasBadgeRow(rec) { return rec.badges.length > 0 || !!rec.may_only; }
  function uniq(a) { var o = []; a.forEach(function (x) { if (x && o.indexOf(x) < 0) o.push(x); }); return o; }
  function isHttp(u) { return /^https?:\/\/\S+$/.test(u || ''); }
  function link(u, text) {
    if (!isHttp(u)) return '';
    return '<a class="src-link" href="' + esc(u) + '" target="_blank" rel="noopener noreferrer">' + esc(text || u) + '</a>';
  }
  function verifyBox(t) { return '<div class="verify"><span class="vk">VERIFY</span>' + esc(String(t).replace(/^\[verify[^\]]*\]\s*/i, '')) + '</div>'; }
  function bindingText(b, draft) {
    if (!b) return 'not set on this element';
    var t = BINDING_BADGE[b] || '';
    return b + (t ? ' (' + t + ')' : '') + (draft ? ' - draft (DRAFT)' : '');
  }

  var HAS_MINIMAP = typeof window.DiagramJSMinimap === 'object' && !!window.DiagramJSMinimap;
  var viewer = new BpmnJS({ container: '#canvas', moddleExtensions: { ipd: MODDLE },
    additionalModules: HAS_MINIMAP ? [window.DiagramJSMinimap] : [], minimap: { open: false } });
  var canvas = viewer.get('canvas');
  var overlays = viewer.get('overlays');
  var registry = viewer.get('elementRegistry');
  var minimap = null;
  try { minimap = HAS_MINIMAP ? viewer.get('minimap') : null; } catch (e) { minimap = null; }

  /* ------------------------------------------------------------ routing */
  function hashName() {
    var h = (location.hash || '').replace(/^#/, '');
    return /^[a-z0-9-]+$/.test(h) ? h : '';
  }
  function setHash(d, replace) {
    if (hashName() === d.hash) return;
    try {
      if (replace) history.replaceState(null, '', '#' + d.hash);
      else location.hash = d.hash;
    } catch (e) {
      try { location.hash = d.hash; } catch (e2) { /* hash not writable: view still opens */ }
    }
  }
  function go(d, selectId) {
    if (!d) return state.chain;
    state.pendingSelect = selectId || null;
    if (hashName() !== d.hash) {
      setHash(d, false);
      // hashchange opens the view; open directly if the host blocks hash changes
      if (hashName() !== d.hash) return openDiagram(d);
      return state.chain;
    }
    return openDiagram(d);
  }
  function route() {
    var d = byHash[hashName()];
    if (!d) { d = ROOT_D; setHash(d, true); }
    return openDiagram(d);
  }

  function openDiagram(d) {
    state.chain = state.chain.then(function () {
      if (state.diagram && state.diagram.id === d.id) {
        if (state.pendingSelect) { var id = state.pendingSelect; state.pendingSelect = null; select(id, true); }
        return null;
      }
      return viewer.open(d.id).then(function () { afterOpen(d); });
    }).catch(fail);
    return state.chain;
  }

  function afterOpen(d) {
    state.diagram = d;
    state.selected = null;
    canvas.resized();
    defaultView();
    minimapForDiagram();
    addOverlays(d);
    markClickable(d);
    applyFilters(false);
    renderCrumbs(d);
    $('#back').disabled = d.id === ROOT_D.id;
    document.documentElement.setAttribute('data-diagram', d.id);
    if (state.pendingSelect && EL[state.pendingSelect] && EL[state.pendingSelect].diagram === d.id) {
      var id = state.pendingSelect; state.pendingSelect = null; select(id, true);
    } else {
      state.pendingSelect = null;
      renderPanel();
    }
  }

  function fail(err) {
    var m = $('#canvas-msg');
    m.hidden = false;
    m.textContent = 'The diagram could not be shown: ' + (err && err.message ? err.message : String(err));
    console.error(err);
  }

  /* ------------------------------------------------------------ default view and minimap */
  // Fit shows wide diagrams at 28-46 %, where labels and source boxes cannot be read. Below LEGIBLE the
  // diagram opens at READABLE_ZOOM instead: left edge (pool headers, process start event) at the left,
  // vertically centred on the Sponsor pool, shifted only as far as needed to keep the process start event and
  // its first step (with labels and source boxes) in view and to avoid an empty band above or below the diagram.
  // Drag or scroll to pan; Fit and 100% stay available.
  var LEGIBLE = 0.6, READABLE_ZOOM = 0.75, FOCUS_ZOOM = 1, EDGE = 20;
  function fitScale(vb) {
    var o = vb.outer, i = vb.inner;
    if (!i || !i.width || !i.height) return 1;
    return Math.min(1, o.width / i.width, o.height / i.height);
  }
  function inside(p, e) {
    var cx = e.x + e.width / 2, cy = e.y + e.height / 2;
    return cx >= p.x && cx <= p.x + p.width && cy >= p.y && cy <= p.y + p.height;
  }
  function bySize(a) {
    return a.slice().sort(function (x, y) { return (y.width * y.height - x.width * x.height) || (x.id < y.id ? -1 : 1); });
  }
  function leftmost(a) {
    return a.slice().sort(function (x, y) { return (x.x - y.x) || (x.y - y.y) || (x.id < y.id ? -1 : 1); })[0] || null;
  }
  function anchorElements() {
    // Sponsor pool: expanded pool named Sponsor (largest if several); else the pool of the leftmost start event;
    // else the largest expanded pool. Start event: leftmost start event in that pool, else leftmost overall.
    // Process start (first): leftmost start event of the diagram; at equal x the one in the Sponsor pool.
    var pools = registry.filter(function (e) { return e.type === 'bpmn:Participant' && e.businessObject && e.businessObject.processRef; });
    var starts = registry.filter(function (e) { return e.type === 'bpmn:StartEvent'; });
    var named = pools.filter(function (p) { return /(^|[^a-z])sponsor([^a-z]|$)/i.test(p.businessObject.name || ''); });
    var pool = bySize(named)[0] || null;
    if (!pool) { var s0 = leftmost(starts); pool = s0 ? (pools.filter(function (p) { return inside(p, s0); })[0] || null) : null; }
    if (!pool) pool = bySize(pools)[0] || null;
    var start = leftmost(pool ? starts.filter(function (s) { return inside(pool, s); }) : []) || leftmost(starts);
    var first = leftmost(starts);
    if (first && start && start !== first && Math.abs(start.x - first.x) < 1) first = start;
    return { pool: pool, start: start, first: first };
  }
  function spanOf(start) {
    // vertical extent of the start event and its direct successors, each with its external label and source box
    var els = [start].concat((start.outgoing || []).filter(function (c) { return c.type === 'bpmn:SequenceFlow' && c.target; })
      .map(function (c) { return c.target; }));
    var t = Infinity, b = -Infinity;
    els.forEach(function (el) {
      var z = EL[el.id] && EL[el.id].zone;
      t = Math.min(t, el.y); b = Math.max(b, el.y + el.height);
      if (el.label) { t = Math.min(t, el.label.y); b = Math.max(b, el.label.y + el.label.height); }
      if (z) { t = Math.min(t, z[1]); b = Math.max(b, z[1] + z[3]); }
    });
    return { top: t, bottom: b };
  }
  function defaultView() {
    canvas.zoom('fit-viewport', 'auto');
    var vb = canvas.viewbox(), fit = fitScale(vb);
    var view = { mode: 'fit', fit: fit, zoom: vb.scale, pool: null, start: null };
    if (fit < LEGIBLE) {
      var o = vb.outer, i = vb.inner, w = o.width / READABLE_ZOOM, h = o.height / READABLE_ZOOM, a = anchorElements();
      var x = i.x - EDGE;
      if (a.first && a.first.x + a.first.width + EDGE > x + w) x = a.first.x - 3 * EDGE;
      var cy = a.pool ? a.pool.y + a.pool.height / 2 : i.y + i.height / 2;
      var y = cy - h / 2;
      if (a.first) {
        var sp = spanOf(a.first);
        if (sp.top < y + EDGE) y = sp.top - EDGE;
        if (sp.bottom > y + h - EDGE) y = sp.bottom + EDGE - h;
      }
      var top = i.y - EDGE, bottom = i.y + i.height + EDGE - h;
      y = Math.max(Math.min(top, bottom), Math.min(Math.max(top, bottom), y));
      canvas.viewbox({ x: x, y: y, width: w, height: h });
      view = { mode: 'readable', fit: fit, zoom: canvas.zoom(), pool: a.pool ? a.pool.id : null, start: a.start ? a.start.id : null,
        first: a.first ? a.first.id : null, centred: Math.abs(y - (cy - h / 2)) < 0.5 };
    }
    state.view = view;
    document.documentElement.setAttribute('data-view', view.mode);
    zoomReadout();
  }
  function minimapForDiagram() {
    // closed by default on every diagram (V1 r2: an open minimap hides content in the default view);
    // once the user opens or closes it with the navigation-bar button, that choice holds for all diagrams
    if (!minimap) return;
    var vb = canvas.viewbox(), map = document.querySelector('#canvas .djs-minimap .map');
    if (map && vb.inner && vb.inner.width) {
      // map box follows the diagram's aspect ratio (the minimap pads 50 units on each side)
      var mw = Math.round(Math.min(320, Math.max(180, vb.outer.width * 0.27)));
      var mh = Math.round(Math.min(180, Math.max(60, mw * (vb.inner.height + 100) / (vb.inner.width + 100))));
      if (map.style.width !== mw + 'px' || map.style.height !== mh + 'px') {
        map.style.width = mw + 'px'; map.style.height = mh + 'px';
        canvas.resized();
      }
    }
    var wide = !!(vb.inner && vb.inner.width * vb.scale > vb.outer.width + 1);
    if (state.view) state.view.wide = wide;
    setMinimap(state.minimapUser === null ? false : state.minimapUser, false);
  }
  function setMinimap(open, byUser) {
    if (!minimap) return;
    if (byUser) state.minimapUser = !!open;
    if (open) minimap.open(); else minimap.close();
    syncMinimapButton();
  }
  function syncMinimapButton() {
    var b = $('#mm-toggle'), open = !!(minimap && minimap.isOpen());
    b.setAttribute('aria-pressed', open ? 'true' : 'false');
    b.textContent = open ? 'Hide minimap' : 'Show minimap';
    document.documentElement.setAttribute('data-minimap', open ? 'open' : 'closed');
  }
  if (minimap) {
    $('#mm-toggle').addEventListener('click', function () { setMinimap(!minimap.isOpen(), true); });
    viewer.on('minimap.toggle', syncMinimapButton);
  } else {
    $('#mm-toggle').hidden = true;
  }

  /* ------------------------------------------------------------ overlays */
  function origin(el) {
    if (el.waypoints) {
      return { x: Math.min.apply(null, el.waypoints.map(function (p) { return p.x; })),
               y: Math.min.apply(null, el.waypoints.map(function (p) { return p.y; })) };
    }
    return { x: el.x, y: el.y };
  }
  function fallbackZone(el) {
    if (el.waypoints) { var o = origin(el); return [o.x + 6, o.y + 6, 150, 70]; }
    var w = Math.max(150, el.width);
    return [el.x + el.width / 2 - w / 2, el.y + el.height + 6, w, 70];
  }
  function sourceLines(rec) {
    var seen = {}, out = [];
    rec.sources.forEach(function (s) {
      var k = s.key + ' ' + s.loc;
      if (!seen[k]) { seen[k] = 1; out.push([s.key, s.loc]); }
    });
    return out;
  }
  var IFC_TEXT = 'Interface - outside this model';
  function isInterface(rec) { return !!(rec && rec.calls && rec.calls.interface); }
  function overlayNode(rec, zone) {
    // wrapper = reserved zone width (no pointer events); inner box sized to its content,
    // centred under shapes, left-aligned with the label for message flows
    var wrap = document.createElement('div');
    wrap.className = 'ipd-ovw' + (rec.type === 'bpmn:MessageFlow' ? ' ipd-ovw-left' : '');
    wrap.style.width = zone[2] + 'px';
    var box = document.createElement('div');
    box.className = 'ipd-ov';
    box.setAttribute('data-ipd-el', rec.id);
    box.setAttribute('role', 'button');
    box.tabIndex = 0;
    box.style.maxWidth = zone[2] + 'px';
    box.style.maxHeight = zone[3] + 'px';
    var lines = sourceLines(rec);
    var all = lines.map(function (l) { return l.join(' '); });
    box.title = (rec.label || rec.type_label) + (isInterface(rec) ? '\n' + IFC_TEXT : '') + '\n' + rec.badges.join(' ') +
      (rec.may_only ? (rec.badges.length ? ' ' : '') + 'MAY (all requirements optional)' : '') +
      '\n' + all.join('\n') + '\nClick for full citation';
    box.setAttribute('aria-label', (isInterface(rec) ? IFC_TEXT + '. ' : '') + 'Sources of ' + (rec.label || rec.type_label) + ': ' +
      (rec.badges.length ? rec.badges.join(', ') + '; ' : '') + (rec.may_only ? 'MAY, all requirements optional; ' : '') + all.join('; '));
    box.setAttribute('data-max-lines', '3');
    fillOverlay(box, rec, 3);
    wrap.appendChild(box);
    return wrap;
  }
  function fillOverlay(box, rec, maxLines) {
    // at most maxLines source lines; when there are more sources, the last line reads "+n more"
    var lines = sourceLines(rec), shown = lines, more = 0;
    if (lines.length > maxLines) { shown = lines.slice(0, Math.max(0, maxLines - 1)); more = lines.length - shown.length; }
    var h = '';
    if (isInterface(rec)) h += '<div class="ipd-ifc">' + IFC_TEXT + '</div>';
    if (hasBadgeRow(rec)) h += '<div class="row">' + badgesHtml(rec) + '</div>';
    h += shown.map(srcLineHtml).join('');
    if (more) h += '<div class="src more">+' + more + (shown.length ? ' more' : ' sources') + '</div>';
    box.innerHTML = h;
    box.setAttribute('data-max-lines', String(maxLines));
  }
  function srcLineHtml(l) {
    // a location that already starts with its key (21CFR312.53(c)) is shown once: key in bold, then the rest
    if (l[1].indexOf(l[0]) === 0 && l[1].length > l[0].length) {
      return '<div class="src"><b>' + esc(l[0]) + '</b>' + esc(l[1].slice(l[0].length)) + '</div>';
    }
    return '<div class="src"><b>' + esc(l[0]) + '</b> ' + esc(l[1]) + '</div>';
  }
  function fitOverlay(box, rec) {
    // the badge row may wrap (binding + DRAFT + VERIFY); then show fewer source lines so the box fits its zone
    var max = parseFloat(box.style.maxHeight) || 70, n = 3;
    while (box.scrollHeight > max + 0.5 && n > 1) { n--; fillOverlay(box, rec, n); }
  }
  function rectsHit(a, b, m) {
    return a.x < b.x + b.width + m && b.x < a.x + a.width + m && a.y < b.y + b.height + m && b.y < a.y + a.height + m;
  }
  function segHitsRect(p, q, r) {
    // Liang-Barsky: does segment p-q touch rectangle r?
    var dx = q.x - p.x, dy = q.y - p.y, t0 = 0, t1 = 1;
    var P = [-dx, dx, -dy, dy], Q = [p.x - r.x, r.x + r.width - p.x, p.y - r.y, r.y + r.height - p.y];
    for (var i = 0; i < 4; i++) {
      if (P[i] === 0) { if (Q[i] < 0) return false; continue; }
      var t = Q[i] / P[i];
      if (P[i] < 0) { if (t > t1) return false; if (t > t0) t0 = t; } else { if (t < t0) return false; if (t < t1) t1 = t; }
    }
    return true;
  }
  function placeChip(shape) {
    // a tab on the bottom border of the call activity (ends above the 6 px gap to the source zone), else inside
    // the bottom or top row; scanned from the right edge to the left so it stays clear of the label text, the
    // markers, flows docking on the border and edge labels
    var W = 58, H = 15, P = 6, M = 2, gfx = registry.getGraphics(shape);
    var vis = gfx && gfx.querySelector('.djs-visual');
    var obstacles = [];
    if (vis) {
      Array.prototype.forEach.call(vis.children, function (c, i) {
        if (i === 0) return;
        try { var b = c.getBBox(); if (b.width > 0 && b.height > 0) obstacles.push(b); } catch (e) { /* not rendered */ }
      });
    }
    var near = { x: shape.x - W, y: shape.y - H, width: shape.width + 2 * W, height: shape.height + 2 * H };
    var segs = [];
    registry.forEach(function (e) {
      if (e.waypoints) {
        for (var i = 0; i + 1 < e.waypoints.length; i++) {
          var a = e.waypoints[i], b = e.waypoints[i + 1];
          if (segHitsRect(a, b, near)) segs.push([{ x: a.x - shape.x, y: a.y - shape.y }, { x: b.x - shape.x, y: b.y - shape.y }]);
        }
      } else if (e.type === 'label' && e.labelTarget !== shape && rectsHit(e, near, 0)) {
        obstacles.push({ x: e.x - shape.x, y: e.y - shape.y, width: e.width, height: e.height });
      }
    });
    var rows = [shape.height - 10, shape.height - P - H, P];
    for (var k = 0; k < rows.length; k++) {
      for (var x = shape.width - P - W; x >= P; x -= 2) {
        var r = { x: x, y: rows[k], width: W, height: H };
        var g = { x: x - M, y: rows[k] - M, width: W + 2 * M, height: H + 2 * M };
        if (obstacles.some(function (o) { return rectsHit(r, o, 1.5); })) continue;
        if (segs.some(function (sg) { return segHitsRect(sg[0], sg[1], g); })) continue;
        return r;
      }
    }
    return null;
  }
  function addOverlays(d) {
    overlays.remove({ type: 'ipd-src' });
    overlays.remove({ type: 'ipd-open' });
    overlays.remove({ type: 'ipd-ifc' });
    d.overlay_elements.forEach(function (id) {
      var rec = EL[id], el = registry.get(id);
      if (!rec || !el) return;
      var z = rec.zone || fallbackZone(el), o = origin(el), node = overlayNode(rec, z);
      overlays.add(id, 'ipd-src', { position: { left: z[0] - o.x, top: z[1] - o.y }, html: node });
      fitOverlay(node.firstChild, rec);
    });
    // interface placeholders without sources still get their chip in the zone below them
    d.call_targets.forEach(function (ct) {
      var rec = EL[ct.element_id], el = registry.get(ct.element_id);
      if (!ct.interface || !rec || !el || rec.overlay) return;
      var z = rec.zone || fallbackZone(el), o = origin(el);
      var w = document.createElement('div');
      w.className = 'ipd-ovw';
      w.style.width = z[2] + 'px';
      w.innerHTML = '<div class="ipd-ov" role="button" tabindex="0" data-ipd-el="' + esc(rec.id) + '"><div class="ipd-ifc">' + IFC_TEXT + '</div></div>';
      overlays.add(ct.element_id, 'ipd-ifc', { position: { left: z[0] - o.x, top: z[1] - o.y }, html: w });
    });
    state.chipsSkipped = [];
    d.call_targets.forEach(function (ct) {
      var el = registry.get(ct.element_id);
      if (!el || !ct.available) return;
      var r = placeChip(el);
      if (!r) { state.chipsSkipped.push(ct.element_id); return; }
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'ipd-chip';
      b.setAttribute('data-ipd-open', ct.diagram);
      b.textContent = 'Open L4';
      b.title = 'Open ' + ct.model + ' - ' + (byId[ct.diagram] ? byId[ct.diagram].title : '');
      b.setAttribute('aria-label', 'Open ' + ct.model + ' detail diagram');
      overlays.add(ct.element_id, 'ipd-open', { position: { left: r.x, top: r.y }, html: b });
    });
  }
  function markClickable(d) {
    d.elements.forEach(function (id) {
      var rec = EL[id];
      if (registry.get(id) && rec && rec.type !== 'bpmn:Lane' && rec.type !== 'bpmn:Participant') canvas.addMarker(id, 'ipd-click');
    });
  }
  function ovNode(id) {
    var n = document.querySelectorAll('.ipd-ov[data-ipd-el]');
    for (var i = 0; i < n.length; i++) if (n[i].getAttribute('data-ipd-el') === id) return n[i];
    return null;
  }
  function mark(id, cls, on) {
    var el = registry.get(id);
    if (!el) return;
    var targets = [el].concat(el.labels || (el.label ? [el.label] : []));
    targets.forEach(function (t) { if (on) canvas.addMarker(t, cls); else canvas.removeMarker(t, cls); });
    var ov = ovNode(id);
    if (ov) ov.classList.toggle(cls, !!on);
  }

  /* ------------------------------------------------------------ canvas events */
  viewer.on('element.click', function (e) {
    var el = e.element;
    if (el.labelTarget) el = el.labelTarget;
    if (!el.parent) { select(null); return; }
    var rec = EL[el.id];
    if (rec && rec.calls && rec.calls.available && !rec.calls.interface) { go(byId[rec.calls.diagram]); return; }
    if (el.type === 'bpmn:Lane' || (el.type === 'bpmn:Participant' && el.businessObject.processRef)) {
      // lanes and expanded pools: only the header strip selects them; clicks on the body clear the selection
      var oe = e.originalEvent, rect = $('#canvas').getBoundingClientRect(), vb = canvas.viewbox();
      var x = oe && typeof oe.clientX === 'number' ? vb.x + (oe.clientX - rect.left) / vb.scale : Infinity;
      if (x > el.x + 30) { select(null); return; }
    }
    if (rec) select(el.id); else select(null);
  });

  $('#canvas').addEventListener('click', function (ev) {
    var chip = ev.target.closest('[data-ipd-open]');
    if (chip) { ev.stopPropagation(); go(byId[chip.getAttribute('data-ipd-open')]); return; }
    var ov = ev.target.closest('[data-ipd-el]');
    if (ov) { ev.stopPropagation(); select(ov.getAttribute('data-ipd-el')); }
  });
  $('#canvas').addEventListener('keydown', function (ev) {
    if (ev.key !== 'Enter' && ev.key !== ' ') return;
    var ov = ev.target.closest && ev.target.closest('.ipd-ov[data-ipd-el]');
    if (ov) { ev.preventDefault(); select(ov.getAttribute('data-ipd-el')); }
  });

  function focusElement(el) {
    // overview zoom is too small to read source boxes: zoom to 100 % centred on the element and its source box
    var b = el.waypoints ? (function () {
      var xs = el.waypoints.map(function (p) { return p.x; }), ys = el.waypoints.map(function (p) { return p.y; });
      return { x: Math.min.apply(null, xs), y: Math.min.apply(null, ys), width: Math.max.apply(null, xs) - Math.min.apply(null, xs), height: Math.max.apply(null, ys) - Math.min.apply(null, ys) };
    })() : el;
    var outer = canvas.viewbox().outer, cx = b.x + b.width / 2, cy = b.y + b.height / 2 + 35;
    canvas.viewbox({ x: cx - outer.width / 2, y: cy - outer.height / 2, width: outer.width, height: outer.height });
  }
  function select(id, scroll) {
    if (state.selected) mark(state.selected, 'ipd-sel', false);
    state.selected = id && EL[id] && EL[id].diagram === (state.diagram && state.diagram.id) ? id : null;
    if (state.selected) {
      mark(state.selected, 'ipd-sel', true);
      var el = registry.get(state.selected);
      if (el && el.type !== 'bpmn:Participant' && el.type !== 'bpmn:Lane') {
        if (canvas.zoom() < FOCUS_ZOOM - 0.005) focusElement(el);
        else if (scroll) {
          try { canvas.scrollToElement(el, { top: 120, bottom: 160, left: 120, right: 120 }); } catch (e) { /* older API */ }
        }
      }
      openPanel(true);
    }
    renderPanel();
  }

  /* ------------------------------------------------------------ filters */
  function filtersActive() {
    var f = state.filters;
    return !!(f.binding || f.jur || f.keys.length || f.q.trim());
  }
  function matches(rec) {
    var f = state.filters;
    if (f.binding && rec.badges.indexOf(f.binding) < 0) return false;
    if (f.jur && rec.jurisdiction.indexOf(f.jur) < 0) return false;
    if (f.keys.length && !rec.sources.some(function (s) { return f.keys.indexOf(s.key) >= 0; })) return false;
    var q = f.q.trim().toLowerCase();
    if (q && rec.search.indexOf(q) < 0) return false;
    return true;
  }
  function applyFilters(persist) {
    var d = state.diagram;
    if (!d) return;
    var active = filtersActive(), n = 0, total = 0, all = 0;
    d.filterable.forEach(function (id) {
      if (!registry.get(id)) return;
      total++;
      var m = active && matches(EL[id]);
      mark(id, 'ipd-match', active && m);
      mark(id, 'ipd-dim', active && !m);
      if (m) n++;
    });
    registry.filter(function (e) {
      return /^bpmn:(SequenceFlow|DataInputAssociation|DataOutputAssociation|Association)$/.test(e.type);
    }).forEach(function (e) {
      [e].concat(e.labels || []).forEach(function (t) { if (active) canvas.addMarker(t, 'ipd-dim'); else canvas.removeMarker(t, 'ipd-dim'); });
    });
    DIAGRAMS.forEach(function (dg) { dg.filterable.forEach(function (id) { if (active && matches(EL[id])) all++; }); });
    var out = $('#match-count');
    out.setAttribute('data-count', active ? String(n) : '');
    out.setAttribute('data-total', String(total));
    out.setAttribute('data-all', active ? String(all) : '');
    out.textContent = active
      ? (n === 0 ? 'No element matches on this diagram' : n + ' of ' + total + ' elements match on this diagram') +
        ' (' + all + ' in all diagrams)'
      : total + ' elements on this diagram - no filter active';
    var ks = state.filters.keys;
    $('#f-keys-sum').textContent = 'Source keys: ' + (ks.length ? ks.length + ' selected' : 'all');
    if (persist) {
      try { localStorage.setItem(STORE_KEY, JSON.stringify(state.filters)); } catch (e) { /* storage blocked */ }
      if (!state.selected) renderPanel();
    }
  }
  function buildFilters() {
    var count = {};
    Object.keys(EL).forEach(function (id) {
      var rec = EL[id];
      if (!rec.filterable) return;
      uniq(rec.sources.map(function (s) { return s.key; })).forEach(function (k) { count[k] = (count[k] || 0) + 1; });
    });
    var keys = Object.keys(count).sort();
    $('#f-keys-list').innerHTML = keys.length ? keys.map(function (k) {
      return '<label><input type="checkbox" value="' + esc(k) + '"> ' + esc(k) + ' <span class="n">(' + count[k] + ')</span></label>';
    }).join('') : '<span class="muted">No source keys</span>';
    try {
      var saved = JSON.parse(localStorage.getItem(STORE_KEY) || 'null');
      if (saved && typeof saved === 'object') {
        state.filters.binding = typeof saved.binding === 'string' ? saved.binding : '';
        state.filters.jur = typeof saved.jur === 'string' ? saved.jur : '';
        state.filters.q = typeof saved.q === 'string' ? saved.q : '';
        state.filters.keys = Array.isArray(saved.keys) ? saved.keys.filter(function (k) { return count[k]; }) : [];
      }
    } catch (e) { /* storage blocked or invalid */ }
    syncFilterInputs();
    $('#f-binding').addEventListener('change', function (e) { state.filters.binding = e.target.value; applyFilters(true); });
    $('#f-jur').addEventListener('change', function (e) { state.filters.jur = e.target.value; applyFilters(true); });
    $('#f-q').addEventListener('input', function (e) { state.filters.q = e.target.value; applyFilters(true); });
    $('#f-keys-list').addEventListener('change', function () {
      state.filters.keys = Array.prototype.map.call(document.querySelectorAll('#f-keys-list input:checked'),
        function (i) { return i.value; });
      applyFilters(true);
    });
    $('#f-clear').addEventListener('click', function () {
      state.filters = { binding: '', jur: '', keys: [], q: '' };
      syncFilterInputs();
      applyFilters(true);
    });
  }
  function syncFilterInputs() {
    var f = state.filters;
    $('#f-binding').value = f.binding;
    $('#f-jur').value = f.jur;
    $('#f-q').value = f.q;
    Array.prototype.forEach.call(document.querySelectorAll('#f-keys-list input'), function (i) {
      i.checked = f.keys.indexOf(i.value) >= 0;
    });
  }

  /* ------------------------------------------------------------ panel */
  function openPanel(on) {
    var p = $('#panel');
    p.classList.toggle('open', !!on);
    $('#panel-toggle').setAttribute('aria-expanded', on ? 'true' : 'false');
    $('#panel-toggle').textContent = on ? 'Hide details' : 'Show details';
  }
  $('#panel-toggle').addEventListener('click', function () { openPanel(!$('#panel').classList.contains('open')); });

  function renderPanel() {
    var body = $('#panel-body');
    body.innerHTML = state.selected ? elementHtml(EL[state.selected]) : listHtml(state.diagram);
    body.scrollTop = 0;
    $('#panel').scrollTop = 0;
  }

  $('#panel-body').addEventListener('click', function (ev) {
    var t = ev.target.closest('[data-act],[data-select],[data-open],[data-goto]');
    if (!t) return;
    if (t.hasAttribute('data-act') && t.getAttribute('data-act') === 'list') { select(null); return; }
    if (t.hasAttribute('data-select')) { select(t.getAttribute('data-select'), true); return; }
    if (t.hasAttribute('data-open')) { go(byId[t.getAttribute('data-open')]); return; }
    if (t.hasAttribute('data-goto')) {
      var p = t.getAttribute('data-goto').split('|');
      go(byId[p[0]], p[1]);
    }
  });

  function traceNote() {
    if (!META.trace_only) return '';
    var miss = [];
    if (!META.findings_loaded) miss.push('findings');
    if (!META.requirements_loaded) miss.push('requirements');
    return '<p class="note">Trace data from the .bpmn only: ' + esc(miss.join(' and ')) +
      ' not yet merged, so requirement statements, paraphrases and quotes are not shown yet.</p>';
  }

  function reqLine(r) {
    if (r.found && r.statement) return '<b>' + esc(r.id) + '</b> ' + esc(r.statement);
    if (r.found) return '<b>' + esc(r.id) + '</b> <span class="muted">no statement in requirements.yaml</span>';
    return '<b>' + esc(r.id) + '</b> <span class="muted">statement not loaded</span>';
  }

  function reqList(reqs) {
    // first three requirements, the rest behind a disclosure; statements clamped to two lines (full text on selection)
    var li = function (q) { return '<li class="clamp">' + reqLine(q) + '</li>'; };
    var h = '<ul>' + reqs.slice(0, 3).map(li).join('') + '</ul>';
    if (reqs.length > 3) h += '<details class="more-reqs"><summary>+' + (reqs.length - 3) + ' more requirements</summary><ul>' + reqs.slice(3).map(li).join('') + '</ul></details>';
    return h;
  }
  function listHtml(d) {
    if (!d) return '';
    var active = filtersActive();
    var h = '<h2>' + esc(d.model) + ' - ' + esc(d.title) + '</h2>';
    h += '<p class="sub">Requirements on this diagram, grouped by element. Click an element on the canvas, its source box, or a heading below for the full citation.</p>';
    h += traceNote();
    if (d.parent) {
      var pr = EL[d.parent.element_id];
      h += '<div class="card"><div class="tag">Parent step on ' + esc(d.parent.model) + '</div>' +
        '<button type="button" class="grp-h" data-goto="' + esc(d.parent.diagram + '|' + d.parent.element_id) + '"><span class="lbl">' +
        esc(d.parent.label) + '</span>' + (pr ? badgesHtml(pr) : '') + '</button>' +
        (pr && pr.reqs.length ? reqList(pr.reqs) : '') + '</div>';
    }
    var notes = (d.model_doc || []).filter(function (f) { return f[0] === 'Open item' || f[0] === 'Rule exception'; });
    if (notes.length) {
      h += '<h3>Model notes</h3>';
      notes.forEach(function (f) {
        if (f[0] === 'Open item' && /\[verify/i.test(f[1])) h += verifyBox(f[1]);
        else h += '<p><b>' + esc(f[0]) + ':</b> ' + esc(f[1]) + '</p>';
      });
    }
    var ids = d.elements.filter(function (id) {
      var r = EL[id];
      return r.filterable && (r.reqs.length || r.sources.length) && (!active || matches(r));
    });
    h += '<h3>' + (active ? 'Matching elements (' + ids.length + ')' : 'Elements with trace data (' + ids.length + ')') + '</h3>';
    if (!ids.length) h += '<p class="muted">' + (active ? 'No element on this diagram matches the filter.' : 'No element on this diagram carries trace data.') + '</p>';
    ids.forEach(function (id) {
      var r = EL[id];
      h += '<section class="grp"><button type="button" class="grp-h" data-select="' + esc(id) + '"><span class="lbl">' +
        esc(r.label || r.type_label) + '</span>' + badgesHtml(r) + '</button>' +
        '<div class="tag">' + esc(r.type_label) + (r.performer ? ' | ' + esc(r.performer) : '') + '</div>';
      if (r.reqs.length) h += reqList(r.reqs);
      else h += '<p class="kv">No requirement linked. Sources: ' + esc(sourceLines(r).map(function (l) { return l.join(' '); }).join('; ')) + '</p>';
      h += '</section>';
    });
    var po = active ? [] : d.elements.filter(function (id) { return EL[id].panel_only; });
    if (po.length) {
      h += '<h3>Lanes and pools</h3><p class="sub">Sources of roles; shown here only, not on the canvas.</p>';
      po.forEach(function (id) {
        var r = EL[id];
        h += '<section class="grp"><button type="button" class="grp-h" data-select="' + esc(id) + '"><span class="lbl">' +
          esc(r.label) + '</span></button><div class="tag">' + esc(r.type_label) + '</div><p class="kv">' +
          esc(sourceLines(r).map(function (l) { return l.join(' '); }).join('; ')) + '</p></section>';
      });
    }
    return h;
  }

  function findingHtml(f) {
    if (!f || f.missing) return '<div class="find"><h4>' + esc(f ? f.id : '') + '</h4><p class="muted">Finding not in merged_findings.yaml.</p></div>';
    var b = BINDING_BADGE[f.binding];
    var h = '<div class="find"><h4>' + esc(f.id) + ' ' + (b ? badge(b) : '') + (f.draft ? ' ' + badge('DRAFT') : '') + '</h4>';
    h += '<p class="kv">' + esc([f.doc, f.loc + (f.loc_alt ? ' (other version: ' + f.loc_alt + ')' : ''), f.page ? 'page ' + f.page : ''].filter(Boolean).join(' | ')) + '</p>';
    if (f.paraphrase) h += '<p>' + esc(f.paraphrase) + '</p>';
    if (f.quote) h += '<blockquote class="quote">"' + esc(f.quote) + '"</blockquote>';
    var kv = [];
    if (f.binding) kv.push('Binding: ' + bindingText(f.binding, f.draft));
    if (f.binding_route) kv.push('Route: ' + f.binding_route);
    if (f.party) kv.push('Party: ' + f.party);
    if (f.deadline) kv.push('Deadline: ' + f.deadline);
    if (f.record) kv.push('Record: ' + f.record);
    if (kv.length) h += '<p class="kv">' + kv.map(esc).join('<br>') + '</p>';
    (f.verify || []).forEach(function (v) { h += verifyBox(v); });
    if (isHttp(f.url)) h += '<p>' + link(f.url) + '</p>';
    return h + '</div>';
  }

  function elementHtml(rec) {
    var h = '<div class="top"><div><h2>' + esc(rec.label || '(no label)') + '</h2>' +
      '<p class="sub">' + esc(rec.type_label) + ' | ' + esc(rec.model) + ' | ' + esc(rec.id) + '</p></div>' +
      '<button type="button" class="btn" data-act="list">All requirements</button></div>';
    if (hasBadgeRow(rec)) h += '<p class="badges">' + badgesHtml(rec, ' ') + '</p>';
    if (isInterface(rec)) {
      h += '<p class="note"><span class="ipd-ifc ipd-ifc-inline">' + IFC_TEXT + '</span> A neighbouring process that is not modelled here, so there is no drill-down. The requirements below are the hand-offs at this interface.</p>';
    } else if (rec.calls) {
      h += rec.calls.available
        ? '<p><button type="button" class="btn" data-open="' + esc(rec.calls.diagram) + '">Open ' + esc(rec.calls.model) + ' detail</button></p>'
        : '<p class="note">' + esc(rec.calls.model || 'The called model') + ' is not in this model file (called element ' + esc(rec.calls.called_element) + ').</p>';
    }
    var reqRecords = uniq(rec.reqs.map(function (r) { return r.record; }));
    var parties = uniq(rec.reqs.map(function (r) { return r.party; }));
    var deadlines = uniq(rec.reqs.map(function (r) { return r.deadline; }));
    var dl = [];
    dl.push(['Binding', esc(bindingText(rec.binding, rec.draft)) + (rec.req_draft && !rec.draft ? ' <span class="muted">- at least one requirement rests on draft guidance (DRAFT)</span>' : '')]);
    dl.push(['Binding route', rec.binding_routes.length ? (rec.binding_routes.length === 1 ? esc(rec.binding_routes[0]) :
      '<ul class="routes">' + rec.binding_routes.map(function (r) { return '<li>' + esc(r) + '</li>'; }).join('') + '</ul>') : '<span class="muted">' + (META.findings_loaded ? 'not stated in the linked findings' : 'available after the synthesis step') + '</span>']);
    if (META.modal_loaded && rec.reqs.length) {
      var mods = uniq(rec.reqs.map(function (r) { return r.found ? (r.modal || 'not stated') : 'not loaded'; }));
      dl.push(['Modal', esc(mods.join(', ')) + (rec.may_only ? ' <span class="muted">- every linked requirement is optional (MAY)</span>' : '')]);
    }
    dl.push(['Jurisdiction', rec.jurisdiction.length ? esc(rec.jurisdiction.join(', ')) : '<span class="muted">not set</span>']);
    dl.push(['Deadline', esc(rec.deadline || deadlines.join('; ')) || '<span class="muted">none stated</span>']);
    dl.push(['Record produced', esc(rec.record || reqRecords.join('; ')) || '<span class="muted">none stated</span>']);
    if (rec.message_flow) {
      dl.push(['From', esc(rec.message_flow.source_label) + ' <span class="muted">(' + esc(rec.message_flow.source_pool) + ')</span>']);
      dl.push(['To', esc(rec.message_flow.target_label) + ' <span class="muted">(' + esc(rec.message_flow.target_pool) + ')</span>']);
    } else {
      dl.push(['Performer', esc(rec.performer) || '<span class="muted">not set</span>']);
    }
    if (rec.party) dl.push(['Party', esc(rec.party)]);
    else dl.push(['Party (requirements)', parties.length ? esc(parties.join('; ')) : '<span class="muted">' + (META.requirements_loaded ? 'not stated' : 'available after the synthesis step') + '</span>']);
    h += '<dl>' + dl.map(function (x) { return '<dt>' + x[0] + '</dt><dd>' + x[1] + '</dd>'; }).join('') + '</dl>';

    var openVerify = rec.verify.slice();
    if (rec.binding === 'verify-binding') openVerify.unshift('Binding class to be verified');
    if (openVerify.length) { h += '<h3>Open verify items (' + openVerify.length + ')</h3>'; openVerify.forEach(function (v) { h += verifyBox(v); }); }

    h += '<h3>' + (isInterface(rec) ? 'Interface requirements' : 'Requirements') + ' (' + rec.reqs.length + ')</h3>';
    if (!rec.reqs.length) h += '<p class="muted">No requirement linked to this element.</p>';
    if (META.trace_only && rec.reqs.length) h += traceNote();
    rec.reqs.forEach(function (r) {
      var b = BINDING_BADGE[r.binding];
      h += '<div class="card req"><div><span class="k">' + esc(r.id) + '</span> ' + (b ? badge(b) : '') + (r.draft ? ' ' + badge('DRAFT') : '') +
        (r.scope ? ' <span class="tag">' + esc(r.scope) + '</span>' : '') + '</div>';
      h += r.found ? (r.statement ? '<p>' + esc(r.statement) + '</p>' : '<p class="muted">No statement in requirements.yaml.</p>')
        : '<p class="muted">Statement not loaded (requirements.yaml not available).</p>';
      var kv = [];
      if (r.modal) kv.push('Modal: ' + r.modal);
      else if (META.modal_loaded && r.found) kv.push('Modal: not stated in requirements.yaml');
      if (r.trigger) kv.push('Trigger: ' + r.trigger);
      if (r.action) kv.push('Action: ' + r.action);
      if (r.recipient) kv.push('Recipient: ' + r.recipient);
      if (r.binding) kv.push('Binding: ' + bindingText(r.binding, r.draft));
      if (r.binding_route) kv.push('Route: ' + r.binding_route);
      if (r.jurisdiction.length) kv.push('Jurisdiction: ' + r.jurisdiction.join(', '));
      if (r.deadline) kv.push('Deadline: ' + r.deadline);
      if (r.record) kv.push('Record: ' + r.record);
      if (r.party) kv.push('Party: ' + r.party);
      if (kv.length) h += '<p class="kv">' + kv.map(esc).join('<br>') + '</p>';
      (r.verify || []).forEach(function (v) { h += verifyBox(v); });
      if (r.findings.length) {
        h += '<details' + (r.findings.length <= 3 ? ' open' : '') + '><summary>Findings behind ' + esc(r.id) + ' (' + r.findings.length + ')</summary>' +
          r.findings.map(findingHtml).join('') + '</details>';
      }
      h += '</div>';
    });

    h += '<h3>Sources (' + rec.sources.length + ')</h3>';
    if (!rec.sources.length) h += '<p class="muted">No source on this element.</p>';
    rec.sources.forEach(function (s) {
      var b = BINDING_BADGE[s.binding_default];
      h += '<div class="card"><div><span class="k">' + esc(s.key) + '</span> ' + esc(s.loc) +
        (s.page ? ' <span class="kv">| page ' + esc(s.page) + '</span>' : '') + '</div>';
      h += '<p>' + (s.title ? esc(s.title) : '<span class="muted">Source key not in the registry.</span>') + '</p>';
      if (s.binding_default) h += '<p class="kv">Registry class: ' + esc(s.binding_default) + (b ? ' ' + badge(b) : '') + '</p>';
      var fl = s.findings.map(function (id) { return FIND[id]; }).filter(Boolean);
      if (fl.length) {
        if (s.findings_match === 'key') h += '<p class="kv">No finding at exactly this location; findings from ' + esc(s.key) + ' behind the linked requirements:</p>';
        fl.slice(0, 3).forEach(function (f) {
          h += '<div class="find"><div class="tag">' + esc(f.id) + ' | ' + esc(f.loc) + (f.page ? ' | page ' + esc(f.page) : '') + '</div>';
          if (f.paraphrase) h += '<p>' + esc(f.paraphrase) + '</p>';
          if (f.quote) h += '<blockquote class="quote">"' + esc(f.quote) + '"</blockquote>';
          (f.verify || []).forEach(function (v) { h += verifyBox(v); });
          h += '</div>';
        });
        if (fl.length > 3) h += '<p class="kv">+' + (fl.length - 3) + ' more findings at this location (see requirements above).</p>';
      } else {
        h += '<p class="muted">' + (META.findings_loaded ? 'No finding recorded at this location.' : 'Paraphrase and quote available after the synthesis step (findings not yet merged).') + '</p>';
      }
      if (isHttp(s.url)) {
        h += '<p>' + link(s.url, 'Open source document') + (s.url_from === 'registry' && s.url_status === 'seeded' ? ' <span class="kv">(registry URL, not yet confirmed)</span>' : '') + '</p>';
      } else {
        h += '<p class="kv">No confirmed URL.</p>';
      }
      h += '</div>';
    });
    if (rec.notes.length) {
      h += '<h3>Notes</h3>' + rec.notes.map(function (n) { return '<p>' + esc(n) + '</p>'; }).join('');
    }
    return h;
  }

  /* ------------------------------------------------------------ header, crumbs, legend */
  function renderCrumbs(d) {
    var path = [], cur = d, guard = 0;
    while (cur && guard++ < 10) { path.unshift(cur); cur = cur.parent ? byId[cur.parent.diagram] : null; }
    $('#crumbs').innerHTML = path.map(function (p, i) {
      var t = esc(p.model) + ' - ' + esc(p.title);
      return i === path.length - 1 ? '<li aria-current="page">' + t + '</li>'
        : '<li><button type="button" class="link" data-crumb="' + esc(p.id) + '">' + t + '</button></li>';
    }).join('');
  }
  $('#crumbs').addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-crumb]');
    if (b) go(byId[b.getAttribute('data-crumb')]);
  });
  $('#back').addEventListener('click', function () { go(ROOT_D); });

  var SYMBOLS = {
    'task': ['bpmn-icon-task', 'Task - a step performed by the role of its lane or pool'],
    'callActivity': ['bpmn-icon-call-activity', 'Call activity (thick border, + marker) - an L3 step; click it or its "Open L4" chip to open the L4 detail'],
    'callActivity:interface': ['bpmn-icon-call-activity', 'Interface placeholder (call activity with the chip "Interface - outside this model") - a neighbouring process not modelled here; no drill-down, the side panel shows its interface requirements'],
    'subProcess': ['bpmn-icon-subprocess-collapsed', 'Sub-process'],
    'startEvent': ['bpmn-icon-start-event-none', 'Start event - the trigger of a process'],
    'startEvent:message': ['bpmn-icon-start-event-message', 'Message start event - started by an incoming message'],
    'startEvent:timer': ['bpmn-icon-start-event-timer', 'Timer start event - started at a point in time'],
    'endEvent': ['bpmn-icon-end-event-none', 'End event - the outcome of a process'],
    'endEvent:message': ['bpmn-icon-end-event-message', 'Message end event - ends by sending a message'],
    'endEvent:terminate': ['bpmn-icon-end-event-terminate', 'Terminate end event'],
    'intermediateCatchEvent:message': ['bpmn-icon-intermediate-event-catch-message', 'Intermediate message catch event - waits for a message'],
    'intermediateThrowEvent:message': ['bpmn-icon-intermediate-event-throw-message', 'Intermediate message throw event - sends a message'],
    'intermediateCatchEvent:timer': ['bpmn-icon-intermediate-event-catch-timer', 'Intermediate timer event - waits for a time or deadline'],
    'exclusiveGateway': ['bpmn-icon-gateway-xor', 'Exclusive gateway (X marker) - exactly one path; the question is its label, the answers label the flows'],
    'parallelGateway': ['bpmn-icon-gateway-parallel', 'Parallel gateway (+ marker) - all paths run; the join waits for all'],
    'inclusiveGateway': ['bpmn-icon-gateway-or', 'Inclusive gateway (O marker) - one or more paths'],
    'eventBasedGateway': ['bpmn-icon-gateway-eventbased', 'Event-based gateway'],
    'dataObjectReference': ['bpmn-icon-data-object', 'Data object - a record produced or used by a step'],
    'dataStoreReference': ['bpmn-icon-data-store', 'Data store - a persistent record or system of record'],
    'participant': ['bpmn-icon-participant', 'Pool - a party; lanes inside a pool are roles'],
    'participant:collapsed': ['bpmn-icon-participant', 'Collapsed pool (thin band) - an external party shown only as a message partner'],
    'lane': ['bpmn-icon-lane', 'Lane - a role within a pool, named as in the source'],
    'group': ['bpmn-icon-group', 'Group (dash-dot frame) - related steps, for example one jurisdiction'],
    'textAnnotation': ['bpmn-icon-text-annotation', 'Text annotation (open bracket) - an explanatory note attached to an element']
  };
  var LINES = {
    sequenceFlow: ['<svg width="34" height="12" aria-hidden="true"><line x1="2" y1="6" x2="27" y2="6" stroke="#000" stroke-width="1.5"/><path d="M26 2 L33 6 L26 10 Z" fill="#000"/></svg>', 'Sequence flow - order of steps within one pool'],
    defaultFlow: ['<svg width="34" height="12" aria-hidden="true"><line x1="2" y1="6" x2="27" y2="6" stroke="#000" stroke-width="1.5"/><line x1="6" y1="2" x2="10" y2="10" stroke="#000" stroke-width="1.5"/><path d="M26 2 L33 6 L26 10 Z" fill="#000"/></svg>', 'Default flow (slash at the start) - taken when no other answer applies'],
    messageFlow: ['<svg width="34" height="12" aria-hidden="true"><circle cx="5" cy="6" r="3" fill="#fff" stroke="#000"/><line x1="8" y1="6" x2="27" y2="6" stroke="#000" stroke-width="1.5" stroke-dasharray="4 3"/><path d="M26 2 L33 6 L26 10 Z" fill="#fff" stroke="#000"/></svg>', 'Message flow (dashed) - a hand-off between pools'],
    association: ['<svg width="34" height="12" aria-hidden="true"><line x1="2" y1="6" x2="32" y2="6" stroke="#000" stroke-width="1.5" stroke-dasharray="1.5 3"/></svg>', 'Association (dotted, no arrow) - attaches a text annotation'],
    dataAssociation: ['<svg width="34" height="12" aria-hidden="true"><line x1="2" y1="6" x2="30" y2="6" stroke="#000" stroke-width="1.5" stroke-dasharray="1.5 3"/><path d="M26 2 L32 6 L26 10" fill="none" stroke="#000"/></svg>', 'Data association (dotted) - a step reads or writes a record']
  };

  function buildLegend() {
    $('#lg-badges').innerHTML = ['LAW', 'ICH', 'GUIDANCE', 'DRAFT', 'BP', 'VERIFY'].map(function (b) {
      return '<li>' + badge(b) + '<span>' + esc(BADGE_TEXT[b]) + '</span></li>';
    }).join('') + (META.modal_loaded ? '<li>' + mayChip() + '<span>Optional step - every requirement of the element has the modal "may"; ' +
      'shown next to the binding badge, which still gives the class of the source. Each requirement\'s modal is in the side panel.</span></li>' : '');
    var syms = META.symbols || [];
    var order = Object.keys(SYMBOLS).concat(Object.keys(LINES));
    var items = order.filter(function (k) { return syms.indexOf(k) >= 0; }).map(function (k) {
      if (SYMBOLS[k]) return '<li><span class="sym ' + SYMBOLS[k][0] + '" aria-hidden="true"></span><span>' + esc(SYMBOLS[k][1]) + '</span></li>';
      return '<li><span class="sym">' + LINES[k][0] + '</span><span>' + esc(LINES[k][1]) + '</span></li>';
    });
    $('#lg-symbols').innerHTML = items.join('');
    $('#lg-colours').innerHTML = [
      'Colour never carries meaning on its own: every badge has a text label, every highlight has a count or a label.',
      'Source box under an element: binding badge, then up to three source lines (source key and location); "+n more" when there are more. Click it for the full citation.',
      'Dark green outline: the element matches the active filter (count in the filter bar). Faded: it does not match.',
      'Yellow background: an open verify item, always labelled VERIFY.',
      'Lane and pool sources are shown in the side panel only (click the lane or pool header).',
      'Wide diagrams open at ' + Math.round(READABLE_ZOOM * 100) + '% at the left edge, centred on the Sponsor pool: drag or scroll to pan, ' +
        '"Fit" shows the whole diagram, "100%" the detail; clicking a step zooms to 100%.' +
        (minimap ? ' The minimap (top right of the canvas, "Show minimap" / "Hide minimap") shows the whole diagram; its dark green frame marks the visible part - click or drag in it to move the view.' : '')
    ].map(function (t) { return '<li><span>' + esc(t) + '</span></li>'; }).join('');
    var inp = META.inputs, b = [];
    b.push('Model file: ' + inp.bpmn.file + ' (sha256 ' + inp.bpmn.sha256.slice(0, 12) + ')');
    b.push(inp.findings ? 'Findings: ' + inp.findings.file + ' (' + inp.findings.records + ' records)' : 'Findings: not loaded - trace data from the .bpmn only');
    b.push(inp.requirements ? 'Requirements: ' + inp.requirements.file + ' (' + inp.requirements.records + ' records)' : 'Requirements: not loaded');
    b.push('Source registry: ' + inp.registry.file);
    b.push('Rendered with bpmn-js ' + (META.viewer ? META.viewer.bpmn_js : '') + ' (NavigatedViewer); the bpmn.io watermark stays visible as its licence requires.');
    if (META.viewer && META.viewer.minimap) b.push('Minimap: diagram-js-minimap ' + META.viewer.minimap + ' (MIT licence, notice kept in the page source).');
    b.push('Generated by ' + META.generator + '.');
    $('#lg-build').innerHTML = b.map(function (t) { return '<li>' + esc(t) + '</li>'; }).join('');
  }

  /* ------------------------------------------------------------ copy */
  $('#copy-xml').addEventListener('click', function () {
    var out = $('#copy-status'), ta = $('#copy-fallback');
    function done(ok) {
      if (ok) {
        out.textContent = 'BPMN XML copied to the clipboard (' + XML.length + ' characters).';
        ta.hidden = true;
      } else {
        out.textContent = 'The browser blocked the clipboard. The XML is shown below - select it and copy it manually.';
        ta.value = XML;
        ta.hidden = false;
      }
      out.setAttribute('data-ok', ok ? '1' : '0');
    }
    function fallback() {
      var ok = false;
      try {
        var t = document.createElement('textarea');
        t.value = XML; t.setAttribute('readonly', '');
        t.style.position = 'fixed'; t.style.left = '-9999px'; t.style.top = '0';
        document.body.appendChild(t); t.select();
        ok = document.execCommand('copy');
        document.body.removeChild(t);
      } catch (e) { ok = false; }
      done(ok);
    }
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(XML).then(function () { done(true); }, fallback);
      } else {
        fallback();
      }
    } catch (e) {
      fallback();
    }
  });

  /* ------------------------------------------------------------ zoom */
  $('#z-in').addEventListener('click', function () { canvas.zoom(canvas.zoom() * 1.25); });
  $('#z-out').addEventListener('click', function () { canvas.zoom(canvas.zoom() / 1.25); });
  $('#z-100').addEventListener('click', function () { canvas.zoom(1); });
  function zoomReadout(e) {
    var vb = (e && e.viewbox) || canvas.viewbox(), z = vb.scale, out = $('#z-level');
    var pan = !!(vb.inner && (vb.inner.width * z > vb.outer.width + 1 || vb.inner.height * z > vb.outer.height + 1));
    out.textContent = 'Zoom ' + Math.round(z * 100) + '%' + (z < LEGIBLE ? ' - overview: click a step to zoom in'
      : pan ? ' - drag to pan, Fit shows the whole diagram' : '');
    out.setAttribute('data-zoom', z.toFixed(3));
  }
  viewer.on('canvas.viewbox.changed', zoomReadout);
  $('#z-fit').addEventListener('click', function () { canvas.zoom('fit-viewport', 'auto'); });
  var resizeTimer = null;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () { canvas.resized(); }, 120);
  });

  /* ------------------------------------------------------------ init */
  $('#basis').textContent = META.source_basis_text ||
    ('Source basis: ' + META.source_basis_date + (META.source_basis_date === 'TBD' ? ' (' + META.source_basis_note + ')' : ''));
  $('#mode').textContent = META.trace_only ? 'Trace data from the .bpmn only (findings and requirements not yet merged)' : 'Findings and requirements merged';
  buildFilters();
  buildLegend();

  var start = byHash[hashName()] || ROOT_D;
  var ready = viewer.importXML(XML, start.id).then(function (res) {
    window.ipdImportWarnings = (res.warnings || []).map(function (w) { return w.message; });
    if (!hashName() || !byHash[hashName()]) setHash(start, true);
    afterOpen(start);
    window.addEventListener('hashchange', route);
    document.documentElement.setAttribute('data-ready', '1');
  }).catch(fail);
  state.chain = ready;

  // test and automation hook (read-only use by tools/test_viewer.mjs)
  window.ipdApp = {
    ready: ready, state: state, data: D, viewer: viewer, matches: matches, minimap: minimap,
    constants: { LEGIBLE: LEGIBLE, READABLE_ZOOM: READABLE_ZOOM, FOCUS_ZOOM: FOCUS_ZOOM, EDGE: EDGE },
    open: function (id) { return go(byId[id]); },
    select: function (id) { select(id, true); },
    idle: function () { return state.chain; }
  };
})();
