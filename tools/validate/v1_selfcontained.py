#!/usr/bin/env python3
"""V1 layer L5: static self-containment check of the viewer HTML (whole file, scripts included).

- markup: no src/href/srcset/action/poster/data attribute with an external URL; no <link rel=stylesheet>, no <script src>
- CSS: url() only data:, no @import
- script and data bodies: every http(s) URL is classified as XML namespace / schema identifier, bpmn.io watermark,
  panel source link (occurs in citations.json), or 'other' (reported)
- embedded payloads equal the artefacts: ipd-bpmn == out/ipd_best_practice.bpmn, ipd-data == out/citations.json,
  ipd-moddle == contracts/ipd_moddle.json

Usage: python -I tools/validate/v1_selfcontained.py --html <copy.html> --out <json>
"""
import argparse
import hashlib
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NS_PREFIXES = ("http://www.w3.org/", "http://www.omg.org/spec/", "http://bpmn.io/schema/", "https://www.w3.org/", "http://tempuri.org",
               "http://camunda.org/schema/", "http://www.omg.org/")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    html = open(a.html, encoding="utf-8").read()
    errors, passed = [], []

    def E(rule, el, msg, sev="MUST"):
        errors.append(dict(rule_id=rule, layer="L5", model="viewer", element=el, message=msg, severity=sev, owner="W1", status="open"))

    def P(check, count, note=""):
        passed.append(dict(layer="L5", check=check, count=count, note=note))
    scripts = re.findall(r"<script\b([^>]*)>([\s\S]*?)</script>", html, re.I)
    styles = re.findall(r"<style\b[^>]*>([\s\S]*?)</style>", html, re.I)
    markup = re.sub(r"<script\b[^>]*>[\s\S]*?</script>", "<script></script>", html, flags=re.I)
    markup = re.sub(r"<style\b[^>]*>[\s\S]*?</style>", "<style></style>", markup, flags=re.I)
    attrs = re.findall(r"\s(src|href|srcset|action|poster|data)\s*=\s*[\"']?([^\"'\s>]+)", markup, re.I)
    ext = [v for k, v in attrs if not re.match(r"^(data:|blob:|#)", v, re.I)]
    if ext:
        E("VIEW-SELFCONTAINED", "markup", "external URLs in markup attributes: %s" % ext[:5])
    else:
        P("static: no external URL in markup src/href/srcset/action/poster/data attributes", len(attrs))
    if any(re.search(r"\ssrc\s*=", at, re.I) for at, _ in scripts) or re.search(r"<link\b[^>]*rel=[\"']?stylesheet", markup, re.I):
        E("VIEW-SELFCONTAINED", "markup", "external script or stylesheet tag")
    else:
        P("static: all %d scripts and %d style blocks inline (no <script src>, no <link rel=stylesheet>)" % (len(scripts), len(styles)), len(scripts) + len(styles))
    css = "\n".join(styles)
    cu = [u for u in re.findall(r"url\(\s*['\"]?([^'\")]+)", css) if not u.startswith(("data:", "#"))]
    if cu or re.search(r"@import", css):
        E("VIEW-SELFCONTAINED", "css", "CSS url() outside data: or @import: %s" % cu[:5])
    else:
        P("static: CSS url() only data: URIs, no @import", len(re.findall(r"url\(", css)))
    # payloads
    payload = {}
    for at, body in scripts:
        m = re.search(r"id=[\"']([^\"']+)", at)
        if m:
            payload[m.group(1)] = body
    checks = [("ipd-bpmn", os.path.join(ROOT, "out", "ipd_best_practice.bpmn"), "xmlstring"),
              ("ipd-data", os.path.join(ROOT, "out", "citations.json"), "json"),
              ("ipd-moddle", os.path.join(ROOT, "contracts", "ipd_moddle.json"), "json")]
    for pid, path, kind in checks:
        if pid not in payload:
            E("VIEW-PAYLOAD", pid, "embedded payload %s missing" % pid)
            continue
        emb = json.loads(payload[pid].replace("<\\/", "</"))
        ref = open(path, encoding="utf-8").read()
        if pid == "ipd-data" and emb.get("page_compact"):
            # the page embeds REQ findings by id (build_viewer.py, embed form); denormalise before comparing
            fnd = emb.get("findings", {})
            for el in emb.get("elements", {}).values():
                for rq in el.get("reqs", []):
                    rq["findings"] = [fnd.get(f, f) if isinstance(f, str) else f for f in rq.get("findings", [])]
            emb.pop("page_compact")
        same = (emb == ref) if kind == "xmlstring" else (emb == json.loads(ref))
        if not same:
            E("VIEW-PAYLOAD", pid, "embedded %s differs from %s" % (pid, os.path.relpath(path, ROOT)))
        else:
            P("embedded %s equals %s" % (pid, os.path.relpath(path, ROOT)), 1,
              "sha256 %s" % hashlib.sha256(ref.encode("utf-8")).hexdigest()[:16])
    # URLs inside scripts
    cit = open(os.path.join(ROOT, "out", "citations.json"), encoding="utf-8").read()
    cit_urls = set(re.findall(r"https?://[^\"\s\\]+", cit))
    code = "\n".join(b for at, b in scripts if not re.search(r"id=[\"'](ipd-bpmn|ipd-data|ipd-moddle)", at))
    urls = re.findall(r"https?://[^\s\"'`<>)\\,;]+", code)
    cls = Counter()
    other = Counter()
    for u in urls:
        if u.startswith(NS_PREFIXES):
            cls["namespace/schema identifier"] += 1
        elif re.match(r"^https?://bpmn\.io/?$", u) or u.startswith(("https://bpmn.io/license", "http://bpmn.io/license")):
            cls["bpmn.io watermark / licence"] += 1
        elif u in cit_urls:
            cls["source link (in citations.json)"] += 1
        else:
            other[u] += 1
    for u, n in sorted(other.items()):
        if re.match(r"^https?://(github\.com|www\.npmjs\.com|npmjs\.com|tools\.ietf\.org|developer\.mozilla\.org|opensource\.org|feross\.org|mths\.be|fb\.me|reactjs\.org|bit\.ly|jsperf\.com|stackoverflow\.com|www\.ecma-international\.org|bugs\.|crbug\.com|html\.spec\.whatwg\.org)", u):
            cls["URL in a library comment or string (never fetched)"] += n
        else:
            cls["other"] += n
    P("static: http(s) URLs in script code classified: %s" % ", ".join("%s %d" % kv for kv in sorted(cls.items())), len(urls),
      ("unclassified: %s" % sorted(u for u in other if not re.match(r"^https?://(github\.com|www\.npmjs\.com|npmjs\.com|tools\.ietf\.org|developer\.mozilla\.org|opensource\.org|feross\.org|mths\.be|fb\.me|reactjs\.org|bit\.ly|jsperf\.com|stackoverflow\.com|www\.ecma-international\.org|bugs\.|crbug\.com|html\.spec\.whatwg\.org)", u))[:8]) if cls.get("other") else "")
    # fetch-capable APIs anywhere in non-library app code: checked at runtime by the network log (v1_render.mjs)
    json.dump(dict(errors=errors, passed=passed, inputs=[a.html, "out/citations.json", "out/ipd_best_practice.bpmn", "contracts/ipd_moddle.json"]),
              open(a.out, "w"), indent=1)
    print("v1_selfcontained: %d errors, %d passed" % (len(errors), len(passed)))


if __name__ == "__main__":
    main()
