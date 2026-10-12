#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate Hapax definitions from the stable C NRPN registry (stdlib only)."""
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "firmware/src/midi_nrpn_map.h"
NAME = re.compile(r"[A-Za-z0-9 _+\-]+")
POLY_CC = {
    1: "Mod Wheel Matriz", 5: "Portamento", 6: "Data Entry NRPN RPN",
    7: "Nivel", 10: "Panorama", 11: "Expresion Matriz", 38: "RPN Bend Cents",
    64: "Pedal Sustain", 71: "Resonancia Motor", 72: "ENV Liberacion",
    73: "ENV Ataque", 74: "Brillo Motor", 75: "ENV Decaimiento",
    91: "Envio Reverb", 93: "Envio Chorus", 94: "Envio Delay",
    98: "NRPN LSB", 99: "NRPN MSB", 100: "RPN LSB", 101: "RPN MSB",
    120: "All Sound Off", 121: "Reset Controllers", 123: "All Notes Off",
}
DRUM_CC = {k: POLY_CC[k] for k in (1, 7, 10, 11, 74, 91, 93, 94, 120, 121, 123)}
LANES = [(36, "Bombo"), (38, "Caja"), (39, "Palmas"), (42, "Hat cerrado"),
         (46, "Hat abierto"), (45, "Tom"), (37, "Aro"), (56, "Campana")]


def parse_registry(text):
    entries = []
    for page, section in enumerate(("COMMON", "ENGINE")):
        match = re.search(r"#define MIDI_NRPN_" + section + r"\(X\)(.*?)(?:\n\n)", text, re.S)
        if not match:
            raise ValueError("missing registry page: " + section)
        entries.extend((page, int(lsb), symbol, name) for lsb, symbol, name in
                       re.findall(r'X\((\d+), (P_\w+), "([^"]+)"\)', match[1]))
    expected = {(0, i) for i in range(103) if i != 8 and not 61 <= i <= 80}
    expected |= {(1, i) for i in range(8)}
    if len(entries) != 90 or {(p, l) for p, l, _, _ in entries} != expected:
        raise ValueError("registry must contain exactly the 90 published addresses")
    if len({s for _, _, s, _ in entries}) != 90 or len({n for _, _, _, n in entries}) != 90:
        raise ValueError("duplicate symbol or name")
    if any(not NAME.fullmatch(n) for _, _, _, n in entries):
        raise ValueError("invalid ASCII name")
    return entries


def definition(entries, drum=False):
    lines = ["# Felucca fork NRPN v1 - requiere firmware modificado",
             "VERSION 1", "TRACKNAME Felucca NRPN" + (" Drum" if drum else " Poly"),
             "TYPE " + ("DRUM" if drum else "POLY"), "OUTPORT NULL",
             "OUTCHAN " + ("4" if drum else "NULL"), "INPORT NULL", "INCHAN NULL",
             "MAXRATE NULL", "", "[DRUMLANES]"]
    if drum:
        lines += [f"{row}:NULL:4:{note} {name}" for row, (note, name) in enumerate(LANES, 1)]
    lines += ["[/DRUMLANES]", "", "[CC]"]
    lines += [f"{cc} {name}" for cc, name in (DRUM_CC if drum else POLY_CC).items()]
    lines += ["[/CC]", "", "[PC]"]
    lines += ([f"{i} {name}" for i, name in enumerate(("STD", "80", "10", "66", "55", "77"), 1)]
              if drum else ["1 Primer sonido motor"])
    lines += ["[/PC]", "", "[NRPN]"]
    lines += [f"{page}:{lsb}:7 {name}" for page, lsb, _, name in entries]
    lines += ["[/NRPN]", "", "[COMMENT]",
              "90 destinos NRPN sin consumir MIDI LEARN. Valores de 7 bits.",
              "Crear lanes manualmente. E1-E8 dependen del motor actual.",
              "Los CC aprendidos conservan prioridad sobre los CC fijos.",
              "Mod Wheel y Expresion requieren destinos en la matriz.",
              "ADSR comun no afecta FM6 ni DRUM. Brillo y resonancia dependen del motor.",
              "CC6 y CC38 conservan Data Entry de RPN0 al seleccionar RPN0.",
              "Segundo equipo CH5-8: bateria OUTCHAN8 y canales de todas las lanes a 8."
              if drum else "Elegir OUTCHAN segun ROUT del equipo: CH1-4 o CH5-8.",
              "Sin Bank Select ni control individual de operadores FM6.",
              "Ver documento MIDI NRPN antes de configurar.", "[/COMMENT]", ""]
    start = lines.index("[COMMENT]") + 1
    end = lines.index("[/COMMENT]")
    lines[start:end] = [re.sub(r" +", " ", re.sub(r"[^A-Za-z0-9 _+\-]", " ", line)).strip() for line in lines[start:end]]
    return "\n".join(lines)


def generated_files(entries):
    return {ROOT / "docs/hapax/felucca-nrpn-poly.txt": definition(entries),
            ROOT / "docs/hapax/felucca-nrpn-drum.txt": definition(entries, True)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare only; never write")
    args = parser.parse_args()
    try:
        outputs = generated_files(parse_registry(REGISTRY.read_text(encoding="utf-8")))
    except ValueError as error:
        parser.error(str(error))
    different = []
    for path, content in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes() != content.encode("utf-8"):
                different.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
    if different:
        print("Outdated Hapax definitions: " + ", ".join(different), file=sys.stderr)
        return 1
    print("Hapax NRPN definitions " + ("match registry" if args.check else "generated"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
