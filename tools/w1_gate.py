#!/usr/bin/env python3
"""W1 gate: build the viewer twice (sha256 must match), check size and self-containment,
run the headless test suite (tools/test_viewer.mjs). Re-runnable by V1 (layer L5).

Usage:
  python -I tools/w1_gate.py --bpmn <file> --report <report.json> [--findings <yaml>]
         [--requirements <yaml>] --registry <yaml> --out <html> [--citations-out <json>]
         --screens <dir> [--test-json <file>] [--source-date YYYY-MM-DD] [--source-basis <text>]
         [--expect-may <id,id>]   (element ids that must carry the MAY chip; self-test only)
Exit code 0 = gate passed, 1 = failed, 2 = usage error.
"""
import argparse
import hashlib
import html.parser
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_BYTES = 5 * 1024 * 1024


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class AttrScan(html.parser.HTMLParser):
    """Collects URL-bearing attributes of the static markup (script and style bodies are raw text)."""
    URL_ATTRS = {"src", "href", "srcset", "action", "poster", "data", "formaction", "background"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k.lower() in self.URL_ATTRS and v is not None:
                self.urls.append((tag, k, v))
            if k.lower() == "style" and v and "url(" in v:
                self.urls.append((tag, k, v))


def main():
    ap = argparse.ArgumentParser()
    for a in ("--bpmn", "--report", "--registry", "--out", "--screens"):
        ap.add_argument(a, required=True)
    for a in ("--findings", "--requirements", "--citations-out", "--test-json", "--source-date", "--source-basis",
              "--expect-may"):
        ap.add_argument(a)
    args = ap.parse_args()
    cit = args.citations_out or os.path.join(os.path.dirname(os.path.abspath(args.out)), "citations.json")
    cmd = [sys.executable, "-I", os.path.join(ROOT, "tools", "build_viewer.py"), "--bpmn", args.bpmn,
           "--report", args.report, "--registry", args.registry, "--out", args.out, "--citations-out", cit]
    for k in ("findings", "requirements", "source_date", "source_basis"):
        v = getattr(args, k)
        if v:
            cmd += ["--" + k.replace("_", "-"), v]

    ok = True
    hashes = []
    for run in (1, 2):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print("FAIL build run %d: %s" % (run, r.stderr.strip()))
            return 1
        if run == 1:
            print(r.stdout.strip())
        hashes.append((sha(args.out), sha(cit)))
    det = hashes[0] == hashes[1]
    ok &= det
    print("%s determinism: html sha256 %s, citations sha256 %s (run 1 = run 2: %s)"
          % ("PASS" if det else "FAIL", hashes[1][0], hashes[1][1], det))

    size = os.path.getsize(args.out)
    ok &= size < MAX_BYTES
    print("%s size: %d bytes (limit %d)" % ("PASS" if size < MAX_BYTES else "FAIL", size, MAX_BYTES))

    text = open(args.out, encoding="utf-8").read()
    p = AttrScan()
    p.feed(text)
    ext = [u for u in p.urls if not re.match(r"^(data:|blob:|#)", u[2].strip(), re.I)]
    ok &= not ext
    print("%s static markup: %d URL attributes, %d external %s" % ("PASS" if not ext else "FAIL", len(p.urls), len(ext),
                                                                 ext[:5] if ext else ""))
    styles = "\n".join(re.findall(r"<style\b[^>]*>(.*?)</style>", text, flags=re.S | re.I))
    css_ext = [u for u in re.findall(r"url\(\s*['\"]?([^'\")]+)", styles) if not u.startswith(("data:", "#"))]
    ok &= not css_ext
    print("%s static CSS: external url() %d" % ("PASS" if not css_ext else "FAIL", len(css_ext)))

    test = ["node", os.path.join(ROOT, "tools", "test_viewer.mjs"), "--html", args.out, "--citations", cit,
            "--screens", args.screens]
    if args.test_json:
        test += ["--json-out", args.test_json]
    if args.expect_may:
        test += ["--expect-may", args.expect_may]
    r = subprocess.run(test, capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    for line in lines:
        if line.startswith(("FAIL", "NOTE")):
            print("  " + line)
    print("%s headless test: %s" % ("PASS" if r.returncode == 0 else "FAIL", lines[-1] if lines else r.stderr.strip()))
    ok &= r.returncode == 0
    print("W1 GATE %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
