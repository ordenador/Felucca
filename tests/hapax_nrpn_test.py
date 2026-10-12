#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Validate the frozen NRPN API, Hapax syntax and read-only --check behavior."""
import contextlib
import hashlib
import importlib.util
import io
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nrpn_generator", ROOT / "tools/gen_hapax_nrpn.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def section(text, name):
    matches = re.findall(r"\[" + name + r"\]\n(.*?)\[/" + name + r"\]", text, re.S)
    if len(matches) != 1:
        raise ValueError("missing or repeated section: " + name)
    return [s for s in matches[0].splitlines() if s.strip()]


def validate(text, entries, drum):
    nrpn = []
    for line in section(text, "NRPN"):
        match = re.fullmatch(r"(\d+):(\d+):7 ([A-Za-z0-9 _+\-]+)", line)
        if not match:
            raise ValueError("invalid NRPN syntax")
        nrpn.append((int(match[1]), int(match[2]), match[3]))
    if nrpn != [(p, l, n) for p, l, _, n in entries] or len(set(nrpn)) != 90:
        raise ValueError("NRPN map mismatch or duplicates")
    cc = []
    for line in section(text, "CC"):
        match = re.fullmatch(r"(\d+) ([A-Za-z0-9 _+\-]+)", line)
        if not match:
            raise ValueError("invalid CC syntax")
        cc.append((int(match[1]), match[2]))
    if cc != list((gen.DRUM_CC if drum else gen.POLY_CC).items()):
        raise ValueError("CC compatibility map mismatch")
    expected = [f"{i}:NULL:4:{note} {name}" for i, (note, name) in enumerate(gen.LANES, 1)] if drum else []
    if section(text, "DRUMLANES") != expected:
        raise ValueError("drum notes/channels mismatch")
    if "DEFAULT" in text or "[ASSIGN]" in text or "[AUTOMATION]" in text:
        raise ValueError("unexpected default or automatic assignment")
    for key, value in {"VERSION": "1", "TYPE": "DRUM" if drum else "POLY", "OUTPORT": "NULL",
                       "OUTCHAN": "4" if drum else "NULL", "INPORT": "NULL", "INCHAN": "NULL",
                       "MAXRATE": "NULL"}.items():
        if len(re.findall(r"^" + key + " " + value + "$", text, re.M)) != 1:
            raise ValueError("invalid header " + key)
    tracknames = re.findall(r"^TRACKNAME (.*)$", text, re.M)
    if len(tracknames) != 1 or not gen.NAME.fullmatch(tracknames[0]):
        raise ValueError("invalid TRACKNAME")
    if any(not gen.NAME.fullmatch(line) for line in section(text, "COMMENT")):
        raise ValueError("invalid COMMENT characters")
    expected_pc = [f"{i} {n}" for i, n in enumerate(("STD", "80", "10", "66", "55", "77"), 1)] if drum else ["1 Primer sonido motor"]
    if section(text, "PC") != expected_pc:
        raise ValueError("PC numbering mismatch")


class HapaxNRPNTest(unittest.TestCase):
    def setUp(self):
        self.registry = gen.REGISTRY.read_text(encoding="utf-8")
        self.entries = gen.parse_registry(self.registry)

    def test_frozen_api(self):
        payload = "\n".join(f"{p}:{l}:{s}" for p, l, s, _ in self.entries).encode()
        self.assertEqual(hashlib.sha256(payload).hexdigest(),
                         "84c597d473ffb074b7ab26e6534375fecd2bf180f7712a85bb5288a6125ac462")
        anchors = {(p, l): s for p, l, s, _ in self.entries}
        for key, symbol in {(0, 0): "P_LEVEL", (0, 39): "P_PAN", (0, 96): "P_ITYPE",
                            (0, 102): "P_ESYNC", (1, 0): "P_E0", (1, 4): "P_E4", (1, 7): "P_E7"}.items():
            self.assertEqual(anchors[key], symbol)

    def test_definitions(self):
        for path, content in gen.generated_files(self.entries).items():
            self.assertEqual(path.read_bytes(), content.encode("utf-8"))
            validate(content, self.entries, path.name.endswith("drum.txt"))

    def test_detects_deliberate_corruption(self):
        with self.assertRaises(ValueError):
            gen.parse_registry(self.registry.replace('X(39, P_PAN,', 'X(38, P_PAN,'))
        with self.assertRaises(ValueError):
            gen.parse_registry(self.registry.replace('X(39, P_PAN,', 'X(103, P_PAN,'))
        good = gen.definition(self.entries)
        for bad in (good.replace('0:39:7 Panorama', '0:38:7 Panorama'),
                    good.replace('0:39:7 Panorama', '0:0:7 Nivel'),
                    good.replace('1:4:7', '1:4:14'), good.replace('7 Nivel', '7:DEFAULT=127 Nivel'),
                    good.replace('TRACKNAME Felucca NRPN Poly', 'TRACKNAME Felucca.NRPN'),
                    good.replace('90 destinos NRPN', '90 destinos NRPN:')):
            with self.assertRaises(ValueError):
                validate(bad, self.entries, False)

    def test_check_never_writes(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/gen_hapax_nrpn.py"), "--check"], check=False)
        self.assertEqual(result.returncode, 0)
        old_root, old_argv = gen.ROOT, sys.argv
        try:
            with tempfile.TemporaryDirectory() as folder:
                gen.ROOT = Path(folder)
                outputs = gen.generated_files(self.entries)
                for path, content in outputs.items():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((content + "# deliberate mismatch\n").encode())
                before = {p: p.read_bytes() for p in outputs}
                sys.argv = ["gen_hapax_nrpn.py", "--check"]
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(gen.main(), 1)
                self.assertEqual(before, {p: p.read_bytes() for p in outputs})
        finally:
            gen.ROOT, sys.argv = old_root, old_argv


if __name__ == "__main__":
    unittest.main()
