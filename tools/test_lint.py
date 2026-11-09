#!/usr/bin/env python3
"""Contract self-test for the S0 linters.

Usage: python -I tools/test_lint.py

Gate (workflow_plan S0): the valid sample and both spec fixtures pass; five
seeded findings faults are rejected (quote of 15+ words, bad enum, missing
loc, unknown src, duplicate id). Additional cases guard the other contract
rules. Linters run as subprocesses with `python -I`, as agents will run them.
"""

import copy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LINT_FINDINGS = ROOT / "tools" / "lint_findings.py"
LINT_SPEC = ROOT / "tools" / "lint_spec.py"
SAMPLE = ROOT / "fixtures" / "R9_sample.yaml"
L3_FIXTURE = ROOT / "fixtures" / "L3_fixture.yaml"
L4_FIXTURE = ROOT / "fixtures" / "L4_fixture.yaml"


def run(tool, *args):
    proc = subprocess.run([sys.executable, "-I", str(tool), *map(str, args)],
                          capture_output=True, text=True, cwd=str(ROOT))
    return proc.returncode, proc.stdout + proc.stderr


def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def dump(data, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return path


class ValidInputs(unittest.TestCase):
    def test_valid_sample_passes(self):
        code, out = run(LINT_FINDINGS, SAMPLE)
        self.assertEqual(code, 0, out)
        self.assertNotIn("ERROR", out, out)

    def test_l3_fixture_passes(self):
        code, out = run(LINT_SPEC, L3_FIXTURE)
        self.assertEqual(code, 0, out)

    def test_l4_fixture_passes_with_parent(self):
        code, out = run(LINT_SPEC, "--parent", L3_FIXTURE, L4_FIXTURE)
        self.assertEqual(code, 0, out)

    def test_fixtures_are_labelled(self):
        for path in (L3_FIXTURE, L4_FIXTURE):
            spec = load(path)
            self.assertTrue(spec["title"].startswith("FIXTURE - "), path)
            labelled = (spec.get("pools", []) + spec.get("lanes", []) + spec.get("nodes", [])
                        + spec.get("flows", []) + spec.get("message_flows", [])
                        + spec.get("data", []) + spec.get("groups", []))
            for el in labelled:
                for key in ("label", "name"):
                    if key in el:
                        self.assertTrue(el[key].startswith("FIXTURE - "), f"{path}: {el['id']}")
            for ta in spec.get("annotations", []):
                self.assertTrue(ta["text"].startswith("FIXTURE - "), f"{path}: {ta['id']}")
            for node in spec["nodes"]:
                if node["type"] in ("xor-split", "or-split"):
                    self.assertTrue(node["label"].endswith("?"), f"{path}: {node['id']}")
                for s in node.get("src", []):
                    self.assertEqual(s["loc"], "FIXTURE", f"{path}: {node['id']}")


class SeededFindingsFaults(unittest.TestCase):
    """Each case: mutate a copy of the valid sample, expect exit 1 and the rule tag."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "fixtures"
        self.base = load(SAMPLE)

    def tearDown(self):
        self.tmp.cleanup()

    def assert_rejected(self, name, data, rule, extra=None, where=None):
        path = dump(data, (where or self.dir) / f"R9_fault_{name}.yaml")
        code, out = run(LINT_FINDINGS, path)
        self.assertEqual(code, 1, f"{name}: expected rejection\n{out}")
        self.assertIn(f"[{rule}]", out, f"{name}: expected rule {rule}\n{out}")
        if extra:
            self.assertIn(extra, out, out)

    # --- the five gate faults ------------------------------------------------
    def test_fault_quote_15_words(self):
        data = copy.deepcopy(self.base)
        data[0]["quote"] = " ".join(["word"] * 15)
        self.assert_rejected("quote", data, "QUOTE")

    def test_fault_bad_enum(self):
        data = copy.deepcopy(self.base)
        data[1]["modal"] = "shall"
        self.assert_rejected("enum", data, "SCHEMA", extra="'shall' is not one of")

    def test_fault_missing_loc(self):
        data = copy.deepcopy(self.base)
        del data[2]["loc"]
        self.assert_rejected("loc", data, "SCHEMA", extra="'loc' is a required property")

    def test_fault_unknown_src(self):
        data = copy.deepcopy(self.base)
        data[3]["src"] = "UNKNOWN-KEY"
        self.assert_rejected("src", data, "SRC")

    def test_fault_duplicate_id(self):
        data = copy.deepcopy(self.base)
        data.append(copy.deepcopy(data[-1]))
        self.assert_rejected("dup", data, "DUP")

    # --- further contract rules ---------------------------------------------
    def test_fault_loc_grammar(self):
        data = copy.deepcopy(self.base)
        data[0]["loc"] = "Principle 7"
        self.assert_rejected("locgrammar", data, "LOC")

    def test_fault_ich_binding_law(self):
        data = copy.deepcopy(self.base)
        data[0]["binding"] = "binding-law"
        self.assert_rejected("ich", data, "ICH")

    def test_fault_draft_not_guidance(self):
        data = copy.deepcopy(self.base)
        data[5]["binding"] = "best-practice"
        self.assert_rejected("draft", data, "DRAFT")

    def test_fault_binding_without_page(self):
        data = copy.deepcopy(self.base)
        data[3]["page"] = ""
        self.assert_rejected("page", data, "PAGE")

    def test_fault_unsorted(self):
        data = copy.deepcopy(self.base)
        data[0], data[1] = data[1], data[0]
        self.assert_rejected("order", data, "ORDER")

    def test_fault_r9_outside_fixtures(self):
        self.assert_rejected("stem", copy.deepcopy(self.base), "STEM", where=Path(self.tmp.name) / "research")

    def test_new_key_from_notes_accepted(self):
        data = copy.deepcopy(self.base)
        data[6]["src"] = "NEW-KEY"
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "R9_notes.md").write_text(
            "# R9 notes\n\n## New source keys\n\n- `NEW-KEY` - FIXTURE title - [verify]\n\n## Gaps\n\n- none\n",
            encoding="utf-8")
        path = dump(data, self.dir / "R9_newkey.yaml")
        code, out = run(LINT_FINDINGS, path)
        self.assertEqual(code, 0, out)


class SeededSpecFaults(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = load(L4_FIXTURE)

    def tearDown(self):
        self.tmp.cleanup()

    def assert_rejected(self, name, data, rule):
        path = dump(data, Path(self.tmp.name) / f"{name}.yaml")
        code, out = run(LINT_SPEC, path)
        self.assertEqual(code, 1, f"{name}: expected rejection\n{out}")
        self.assertIn(f"[{rule}]", out, f"{name}: expected rule {rule}\n{out}")

    def test_unresolved_lane(self):
        data = copy.deepcopy(self.base)
        data["nodes"][1]["lane"] = "L_NOPE"
        self.assert_rejected("lane", data, "REF")

    def test_flow_endpoint_missing(self):
        data = copy.deepcopy(self.base)
        data["flows"][0]["to"] = "A99"
        self.assert_rejected("flow", data, "REF")

    def test_task_without_src(self):
        data = copy.deepcopy(self.base)
        data["nodes"][1]["src"] = []
        self.assert_rejected("nosrc", data, "SCHEMA")

    def test_sequence_flow_across_pools(self):
        data = copy.deepcopy(self.base)
        data["flows"][0]["to"] = "A4"
        self.assert_rejected("crosspool", data, "STRUCT")

    def test_group_member_missing(self):
        data = copy.deepcopy(self.base)
        data["groups"][0]["members"].append("A99")
        self.assert_rejected("group", data, "REF")

    # --- S0-18 ---------------------------------------------------------------
    def node(self, data, nid):
        return next(n for n in data["nodes"] if n["id"] == nid)

    def test_call_null_without_interface_flag(self):
        data = copy.deepcopy(self.base)
        del self.node(data, "A5")["interface"]
        self.assert_rejected("nointerface", data, "SCHEMA")

    def test_interface_flag_with_callee(self):
        data = copy.deepcopy(self.base)
        self.node(data, "A5")["calls"] = "L4-02"
        self.assert_rejected("interfacecallee", data, "SCHEMA")

    def test_interface_flag_on_task(self):
        data = copy.deepcopy(self.base)
        self.node(data, "A1")["interface"] = True
        self.assert_rejected("interfacetask", data, "SCHEMA")

    def test_annotation_assoc_missing(self):
        data = copy.deepcopy(self.base)
        data["annotations"][0]["assoc"].append("F99")
        self.assert_rejected("taref", data, "REF")

    def test_annotation_across_pools(self):
        data = copy.deepcopy(self.base)
        data["annotations"][0]["assoc"].append("A4")
        self.assert_rejected("tapools", data, "STRUCT")


if __name__ == "__main__":
    unittest.main(verbosity=2)
