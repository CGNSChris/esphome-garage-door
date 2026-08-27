#!/usr/bin/env python3
"""Fail if the S3 and C6 entry points have drifted apart.

The two variants must differ ONLY in the board block and their own filename
references. Everything else — pins, polarity, opener behaviour, travel
calibration, OTA settings — has to stay identical, because it describes the
same door on the same wiring harness. A silent divergence here means you
calibrate one variant and flash the other.

Run: py -3 scripts/check_variant_parity.py
"""

import re
import sys

# Keys allowed to differ between the two variants.
BOARD_KEYS = {"board", "chip_variant", "flash_size", "variant_yaml"}

SUB_RE = re.compile(r"^  ([a-z_]+):\s*(.*?)\s*(?:#.*)?$")


def read_subs(path):
    subs, in_block = {}, False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("substitutions:"):
                in_block = True
                continue
            if in_block:
                # any non-indented, non-blank, non-comment line ends the block
                if line and not line.startswith((" ", "#")):
                    break
                m = SUB_RE.match(line)
                if m:
                    subs[m.group(1)] = m.group(2)
    if not subs:
        sys.exit(f"{path}: no substitutions parsed — did the format change?")
    return subs


def main():
    a_path, b_path = "garage-door.yaml", "garage-door-c6.yaml"
    a, b = read_subs(a_path), read_subs(b_path)

    problems = []

    only_a = set(a) - set(b)
    only_b = set(b) - set(a)
    if only_a:
        problems.append(f"only in {a_path}: {sorted(only_a)}")
    if only_b:
        problems.append(f"only in {b_path}: {sorted(only_b)}")

    for key in sorted(set(a) & set(b)):
        if key in BOARD_KEYS:
            continue
        if a[key] != b[key]:
            problems.append(f"{key}: {a_path}={a[key]!r} but {b_path}={b[key]!r}")

    # The board keys must actually differ, or someone copied the wrong board in.
    for key in ("board", "chip_variant"):
        if a.get(key) == b.get(key):
            problems.append(f"{key} is identical ({a.get(key)!r}) — one variant "
                            f"is pointing at the wrong chip")

    if problems:
        print("Variant parity check FAILED:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    shared = len(set(a) & set(b)) - len(BOARD_KEYS & set(a))
    print(f"Variant parity OK: {shared} shared substitutions identical; "
          f"{a['board']} vs {b['board']}")


if __name__ == "__main__":
    main()
