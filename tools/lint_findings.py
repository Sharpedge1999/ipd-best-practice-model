#!/usr/bin/env python3
"""Lint research findings files against the S0 contract.

Usage:
    python -I tools/lint_findings.py <file.yaml> [<file.yaml> ...]
        [--registry contracts/source_registry.yaml]
        [--notes-dir DIR] [--any-stem]

Checks (rule tags in brackets):
    [YAML]      file parses as YAML
    [SCHEMA]    contracts/findings.schema.json (draft 2020-12)
    [STEM]      file name R<n>_<slug>.yaml; id prefix equals the file stem;
                R9 only for files in a directory named fixtures/
    [DUP]       unique ids
    [ORDER]     ids sorted ascending
    [QUOTE]     quote has fewer than 15 words
    [LOC]       loc / loc_alt follow the grammar (decisions.md S0-02)
    [SRC]       src key in the registry or listed under "New source keys"
                in the matching R<n>_notes.md; new keys UPPER-CASE
    [ICH]       binding-law never for ICH sources
    [DRAFT]     draft: true requires binding: guidance
    [PAGE]      binding-law / binding-ICH need page or a verify item
    warnings:   [THEME] [DRAFT-SRC] [CHARS]

Exit codes: 0 no errors, 1 errors found, 2 usage or contract-load error.
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "contracts" / "findings.schema.json"
REGISTRY_PATH = ROOT / "contracts" / "source_registry.yaml"

QUOTE_MAX_WORDS = 14  # "fewer than 15 words"
FIXTURE_STEM = 9
VALID_STEMS = {1, 2, 3, 4, 5, 6}
CANONICAL_THEMES = ["CtQ", "RBQM", "safety", "data"]
BINDING_STRONG = {"binding-law", "binding-ICH"}
FORBIDDEN_CHARS = {"\u2014": "em dash", "\u00b7": "middle dot"}

# --- loc grammar (decisions.md S0-02) --------------------------------------
_PAREN = r"(?:\([A-Za-z0-9]+\))*(?:-\([A-Za-z0-9]+\))?"
_SEC = r"[A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*" + _PAREN
_LOC_FORMS = [
    r"P\d+(?:\.\d+)*" + _PAREN,                                   # principle
    r"GL:[A-Za-z0-9](?:[A-Za-z0-9 ()/',-]*[A-Za-z0-9)])?",        # glossary
    r"(?:A1|A2|AppB|AppC)-" + _SEC,                               # annex / appendix
    r"Art\. ?\d+[a-z]?" + _PAREN,                                 # article
    r"21CFR\d+\.\d+[a-z]?" + _PAREN,                              # 21 CFR
    r"S[A-Za-z0-9]+(?:[.-][A-Za-z0-9]+)*" + _PAREN,               # section as printed
]
LOC_RE = re.compile(r"^(?:" + "|".join(_LOC_FORMS) + r")(?: \[verify[^\]]*\])?$")

FILE_RE = re.compile(r"^R(\d)_[A-Za-z0-9_-]+\.ya?ml$")
ID_RE = re.compile(r"^R(\d)-\d{3}$")
KEY_RE = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
NEW_KEY_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*$")
ICH_KEY_RE = re.compile(r"^[EM]\d")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


class Report:
    def __init__(self):
        self.errors = 0
        self.warnings = 0

    def error(self, rule, rid, path, msg):
        self.errors += 1
        print(f"ERROR [{rule}] {rid or '-'} ({path}): {msg}")

    def warn(self, rule, rid, path, msg):
        self.warnings += 1
        print(f"WARN [{rule}] {rid or '-'} ({path}): {msg}")


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        schema = json.load(fh)
    Draft202012Validator.check_schema(schema)
    return schema


def fixture_schema(schema):
    """Same schema, but finding ids may carry the fixture stem R9."""
    patched = copy.deepcopy(schema)
    patched["$defs"]["finding"]["properties"]["id"]["pattern"] = r"^R[1-69]-\d{3}$"
    return patched


def load_registry(path):
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list):
        raise ValueError("registry must be a mapping with a 'sources' list")
    registry = {}
    for rec in data["sources"]:
        if not isinstance(rec, dict) or not isinstance(rec.get("key"), str):
            raise ValueError(f"registry record without key: {rec!r}")
        if rec["key"] in registry:
            raise ValueError(f"duplicate registry key {rec['key']}")
        registry[rec["key"]] = rec
    return registry


def strip_md(token):
    token = token.strip().strip("`*_").strip()
    token = token.rstrip(":,;")
    return token.strip("`*_").strip()


def parse_new_keys(notes_path):
    """Keys listed under a 'New source keys' heading (list items or table rows)."""
    keys = {}
    if not notes_path.is_file():
        return keys
    in_section = False
    section_level = 7
    for raw in notes_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        heading = HEADING_RE.match(line)
        if heading:
            level, title = len(heading.group(1)), heading.group(2)
            if re.match(r"(?i)new source keys\b", strip_md(title)):
                in_section, section_level = True, level
                continue
            if in_section and level <= section_level:
                in_section = False
            continue
        if re.match(r"(?i)^\s*(\*\*)?new source keys\b", line):
            in_section, section_level = True, 7
            continue
        if not in_section:
            continue
        stripped = line.strip()
        token = None
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if cells and not re.fullmatch(r":?-{2,}:?", cells[0]):
                token = strip_md(cells[0])
        else:
            item = re.match(r"^(?:[-*+]|\d+[.)])\s+(.*)$", stripped)
            if item:
                rest = item.group(1).strip()
                first = re.split(r"\s|:|\|", strip_md(rest), maxsplit=1)[0]
                token = strip_md(first)
        if token and KEY_RE.match(token) and token.lower() not in ("key", "keys"):
            keys[token] = line
    return keys


def word_count(text):
    return len(text.split())


def iter_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for value in obj.values():
            yield from iter_strings(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_strings(value)


def is_ich(rec, registry):
    src = rec.get("src") if isinstance(rec.get("src"), str) else ""
    reg = registry.get(src, {})
    return (
        rec.get("jurisdiction") == "ICH"
        or bool(ICH_KEY_RE.match(src))
        or reg.get("binding_default") == "binding-ICH"
        or reg.get("jurisdiction") == "ICH"
    )


def lint_file(path, schema, registry, args, rep):
    path = Path(path)
    shown = str(path)
    errors_before = rep.errors
    warnings_before = rep.warnings

    if not path.is_file():
        rep.error("IO", None, shown, "file not found")
        return

    # --- stem from file name ---------------------------------------------
    file_stem = None
    in_fixtures = path.resolve().parent.name == "fixtures"
    m = FILE_RE.match(path.name)
    if m:
        file_stem = int(m.group(1))
        if file_stem == FIXTURE_STEM and not in_fixtures:
            rep.error("STEM", None, shown, "stem R9 is reserved for test fixtures under fixtures/")
        elif file_stem not in VALID_STEMS and file_stem != FIXTURE_STEM:
            rep.error("STEM", None, shown, f"stem R{file_stem} is not a research stem (R1-R6)")
    elif not args.any_stem:
        rep.error("STEM", None, shown, "file name must be R<n>_<slug>.yaml (or use --any-stem)")

    # --- YAML --------------------------------------------------------------
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        rep.error("YAML", None, shown, f"does not parse: {exc}")
        return
    if data is None:
        data = []

    # --- schema ------------------------------------------------------------
    use_fixture_schema = in_fixtures and (file_stem == FIXTURE_STEM or args.any_stem)
    validator = Draft202012Validator(fixture_schema(schema) if use_fixture_schema else schema)

    def rec_id(index):
        if isinstance(data, list) and isinstance(index, int) and index < len(data):
            rec = data[index]
            if isinstance(rec, dict) and isinstance(rec.get("id"), str):
                return rec["id"]
            return f"#{index}"
        return None

    for err in sorted(validator.iter_errors(data), key=lambda e: [str(p) for p in e.absolute_path]):
        p = list(err.absolute_path)
        rid = rec_id(p[0]) if p else None
        where = "/".join(str(x) for x in p[1:]) or "(record)"
        rep.error("SCHEMA", rid, shown, f"{where}: {err.message}")

    if not isinstance(data, list):
        return

    notes_dir = Path(args.notes_dir) if args.notes_dir else path.parent
    notes_cache = {}

    def new_keys_for(stem):
        if stem not in notes_cache:
            notes_cache[stem] = parse_new_keys(notes_dir / f"R{stem}_notes.md")
        return notes_cache[stem]

    seen = {}
    ids_in_order = []
    for index, rec in enumerate(data):
        if not isinstance(rec, dict):
            continue
        rid = rec.get("id") if isinstance(rec.get("id"), str) else f"#{index}"

        # DUP / STEM / ORDER
        id_match = ID_RE.match(rid) if isinstance(rec.get("id"), str) else None
        if isinstance(rec.get("id"), str):
            if rid in seen:
                rep.error("DUP", rid, shown, f"duplicate id (records #{seen[rid]} and #{index})")
            else:
                seen[rid] = index
            ids_in_order.append(rid)
        id_stem = int(id_match.group(1)) if id_match else None
        if id_match and not args.any_stem and file_stem is not None and id_stem != file_stem:
            rep.error("STEM", rid, shown, f"id prefix R{id_stem} does not match file stem R{file_stem}")
        if id_stem == FIXTURE_STEM and not in_fixtures:
            rep.error("STEM", rid, shown, "R9 ids are reserved for test fixtures under fixtures/")

        # QUOTE
        quote = rec.get("quote")
        if isinstance(quote, str) and quote.strip():
            n = word_count(quote)
            if n > QUOTE_MAX_WORDS:
                rep.error("QUOTE", rid, shown, f"quote has {n} words; must be fewer than 15 - paraphrase instead")

        # LOC
        for field in ("loc", "loc_alt"):
            value = rec.get(field)
            if isinstance(value, str) and value.strip() and not LOC_RE.match(value):
                rep.error("LOC", rid, shown, f"{field} '{value}' does not follow the loc grammar (decisions.md S0-02)")

        # SRC
        src = rec.get("src")
        if isinstance(src, str):
            stem_for_notes = id_stem if (args.any_stem or file_stem is None) else file_stem
            if src not in registry:
                listed = new_keys_for(stem_for_notes) if stem_for_notes is not None else {}
                if src not in listed:
                    rep.error("SRC", rid, shown,
                              f"src '{src}' is not in the registry and not listed under 'New source keys' "
                              f"in R{stem_for_notes}_notes.md")
                elif not NEW_KEY_RE.match(src):
                    rep.error("SRC", rid, shown, f"new source key '{src}' must be UPPER-CASE with hyphens")
                elif "http" not in listed[src] and "[verify" not in listed[src]:
                    rep.warn("SRC", rid, shown, f"new source key '{src}' is listed without URL or [verify]")

        binding = rec.get("binding")

        # ICH
        if binding == "binding-law" and is_ich(rec, registry):
            rep.error("ICH", rid, shown, "ICH sources are never binding-law; use binding-ICH and record binding_route")

        # DRAFT
        if rec.get("draft") is True and binding != "guidance":
            rep.error("DRAFT", rid, shown, f"draft: true requires binding: guidance (found {binding!r})")
        reg = registry.get(src) if isinstance(src, str) else None
        if reg and reg.get("draft") is True and rec.get("draft") is not True:
            rep.warn("DRAFT-SRC", rid, shown, f"source {src} is a draft in the registry but draft is not true")

        # PAGE
        if binding in BINDING_STRONG:
            page = rec.get("page")
            verify = rec.get("verify")
            has_page = isinstance(page, str) and page.strip() != ""
            has_verify = isinstance(verify, list) and len(verify) > 0
            if not has_page and not has_verify:
                rep.error("PAGE", rid, shown, f"{binding} finding needs a page or a verify item")

        # THEME (warning)
        themes = rec.get("themes")
        if isinstance(themes, list):
            for theme in themes:
                if not isinstance(theme, str):
                    continue
                for canon in CANONICAL_THEMES:
                    if theme != canon and theme.lower() == canon.lower():
                        rep.warn("THEME", rid, shown, f"theme '{theme}' should be spelled '{canon}'")

        # CHARS (warning in findings)
        for text in iter_strings(rec):
            for ch, name in FORBIDDEN_CHARS.items():
                if ch in text:
                    rep.warn("CHARS", rid, shown, f"contains {name}; use '-' outside verbatim quotes")
                    break

    # ORDER
    unique_ids = [i for i in ids_in_order if ID_RE.match(i)]
    for prev, cur in zip(unique_ids, unique_ids[1:]):
        if cur < prev:
            rep.error("ORDER", cur, shown, f"ids not sorted: {cur} follows {prev}")
            break

    n_err = rep.errors - errors_before
    n_warn = rep.warnings - warnings_before
    status = "OK" if n_err == 0 else "FAIL"
    print(f"{shown}: {status} ({len(data)} findings, {n_err} errors, {n_warn} warnings)")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lint research findings YAML files (contract S0).")
    parser.add_argument("files", nargs="+", help="findings files, e.g. research/R3_eu.yaml")
    parser.add_argument("--registry", default=str(REGISTRY_PATH), help="source registry YAML")
    parser.add_argument("--notes-dir", default=None,
                        help="directory holding R<n>_notes.md (default: directory of each file)")
    parser.add_argument("--any-stem", action="store_true",
                        help="merged files: skip the file-stem rule; notes looked up per id stem")
    args = parser.parse_args(argv)

    try:
        schema = load_schema()
        registry = load_registry(args.registry)
    except (OSError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"ERROR [CONTRACT] - ({args.registry}): cannot load contracts: {exc}")
        return 2
    except Exception as exc:  # schema itself invalid
        print(f"ERROR [CONTRACT] - ({SCHEMA_PATH}): {exc}")
        return 2

    rep = Report()
    for f in args.files:
        lint_file(f, schema, registry, args, rep)
    print(f"TOTAL: {rep.errors} errors, {rep.warnings} warnings in {len(args.files)} file(s)")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())
