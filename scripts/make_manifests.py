#!/usr/bin/env python3
"""Build the two manifests the Pages site serves, covering every chip variant.

Usage:
    make_manifests.py <site_dir> <version> <slug>:<ChipFamily> [<slug>:... ]
    e.g. make_manifests.py site 2026.8.1 s3:ESP32-S3 c6:ESP32-C6

Expects each variant's esphome/build-action output already copied to
<site_dir>/firmware/<slug>/ and writes:

  <site>/firmware/manifest.json   esp-web-tools manifest, ONE builds array
                                  covering every chip. esp-web-tools probes
                                  the connected board over serial and picks
                                  the matching entry itself — that is what
                                  makes the web flasher chip-agnostic.

  <site>/manifest.json            OTA manifest for ESPHome's
                                  `update: platform: http_request`. Also one
                                  builds array; each device matches its own
                                  chipFamily, so a single URL serves both
                                  variants and neither can pull the other's
                                  firmware.

chipFamily is read from the build-action manifest where present, so the two
manifests can never disagree about what a binary is for; the command-line
value is only a fallback.
"""

import hashlib
import json
import pathlib
import sys


def one_variant(fw_root, slug, fallback_family):
    """Return (webtools_build, ota_build) for a single chip variant."""
    d = fw_root / slug
    if not d.is_dir():
        sys.exit(f"missing build directory: {d}")

    family = fallback_family
    parts = None

    bam = d / "manifest.json"
    if bam.is_file():
        data = json.loads(bam.read_text())
        builds = data.get("builds") or []
        if builds:
            family = builds[0].get("chipFamily", fallback_family)
            # Re-root each part path under this variant's subdirectory.
            parts = [
                {**p, "path": f"{slug}/{p['path']}"}
                for p in builds[0].get("parts", [])
            ]

    if not parts:
        # Fall back to the factory image at offset 0.
        factory = sorted(d.glob("*.factory.bin"))
        if not factory:
            sys.exit(f"no *.factory.bin and no usable manifest in {d}")
        parts = [{"path": f"{slug}/{factory[0].name}", "offset": 0}]

    ota_bins = sorted(d.glob("*.ota.bin"))
    if not ota_bins:
        sys.exit(f"no *.ota.bin in {d}")
    ota = ota_bins[0]

    webtools_build = {"chipFamily": family, "parts": parts}
    ota_build = {
        "chipFamily": family,
        "ota": {
            "md5": hashlib.md5(ota.read_bytes()).hexdigest(),
            "path": f"firmware/{slug}/{ota.name}",
            "summary": f"Self-hosted build {{version}} ({family})",
            "release_url": "https://github.com/CGNSChris/esphome-garage-door",
        },
    }
    return webtools_build, ota_build


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)

    site = pathlib.Path(sys.argv[1])
    version = sys.argv[2] or "dev"
    specs = sys.argv[3:]

    fw_root = site / "firmware"
    webtools_builds, ota_builds = [], []

    for spec in specs:
        slug, _, family = spec.partition(":")
        if not slug or not family:
            sys.exit(f"bad spec {spec!r}, want <slug>:<ChipFamily>")
        wb, ob = one_variant(fw_root, slug, family)
        ob["ota"]["summary"] = ob["ota"]["summary"].format(version=version)
        webtools_builds.append(wb)
        ota_builds.append(ob)

    families = [b["chipFamily"] for b in webtools_builds]
    if len(set(families)) != len(families):
        sys.exit(f"duplicate chipFamily across variants: {families} — a device "
                 f"would not be able to tell which firmware is its own")

    name = "Garage Door Controller"

    webtools = {
        "name": name,
        "version": version,
        "home_assistant_domain": "esphome",
        "new_install_prompt_erase": True,
        "builds": webtools_builds,
    }
    (fw_root / "manifest.json").write_text(json.dumps(webtools, indent=2) + "\n")

    ota = {"name": name, "version": version, "builds": ota_builds}
    (site / "manifest.json").write_text(json.dumps(ota, indent=2) + "\n")

    print(f"wrote manifests for {', '.join(families)}")
    print((site / "manifest.json").read_text())


if __name__ == "__main__":
    main()
