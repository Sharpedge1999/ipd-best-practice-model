/* iPD viewer - loader of the publish variant (W1, tools/build_viewer.py --publish-dir). Plain ES2019.
   The single-file page embeds the model and citations; the publish variant keeps them as own files.
   This loader fetches them by relative path (names in #ipd-publish), puts them where app.js reads them
   (#ipd-data: citations JSON, #ipd-bpmn: the BPMN XML as a JSON string), then loads app.js by relative
   path, so app.js is the same file as in the single-file page. No dialogs; failures show on the canvas. */
(function () {
  'use strict';

  function fail(msg) {
    var m = document.getElementById('canvas-msg');
    if (m) { m.hidden = false; m.textContent = msg; }
    console.error(msg);
  }
  function relative(u) {
    // own files only: plain relative paths below the page (no scheme, no leading slash, no '..')
    return typeof u === 'string' && /^[A-Za-z0-9_][A-Za-z0-9_./-]*$/.test(u) && u.indexOf('..') < 0;
  }
  function get(url) {
    return fetch(url, { credentials: 'same-origin', cache: 'no-cache' }).then(function (r) {
      if (!r.ok) throw new Error(url + ': HTTP ' + r.status);
      return r.text();
    });
  }
  function put(id, text) {
    var s = document.createElement('script');
    s.type = 'application/json';
    s.id = id;
    s.textContent = text;
    document.body.appendChild(s);
  }

  var cfg;
  try { cfg = JSON.parse(document.getElementById('ipd-publish').textContent); } catch (e) { cfg = null; }
  if (!cfg || !relative(cfg.bpmn) || !relative(cfg.citations) || !relative(cfg.app)) {
    fail('The page configuration (#ipd-publish) is missing or invalid.');
    return;
  }
  if (typeof window.BpmnJS !== 'function') {
    fail('The diagram library (bpmn-js) could not be loaded from the CDN, or its integrity check failed.');
    return;
  }
  Promise.all([get(cfg.citations), get(cfg.bpmn)]).then(function (res) {
    JSON.parse(res[0]);
    put('ipd-data', res[0]);
    put('ipd-bpmn', JSON.stringify(res[1]));
    var s = document.createElement('script');
    s.src = cfg.app;
    s.onerror = function () { fail(cfg.app + ' could not be loaded.'); };
    document.body.appendChild(s);
  }).catch(function (e) {
    fail('The model data could not be loaded (' + (e && e.message ? e.message : String(e)) +
      '). Open the page from a web server; browsers block these requests for local files.');
  });
})();
