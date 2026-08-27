#!/usr/bin/env python3
"""Write the OTA update manifest ESPHome's `update: platform: http_request`
component expects, next to the firmware the build action produced.

Usage: make_ota_manifest.py <site_dir> <version>

The site layout is:
    site/manifest.json          <- written here (the OTA manifest)
    site/firmware/*.ota.bin     <- built by esphome/build-action
    site/firmware/manifest.json <- esp-web-tools manifest (initial USB flash)

`path` in the OTA manifest is relative to the manifest's own URL, hence the
firmware/ prefix. chipFamily, md5 and path are required; summary and
release_url are optional.
"""

import hashlib
import json
import pathlib
import sys


def main() -> None:
    site = pathlib.Path(sys.argv[1])
    version = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else "dev"

    ota_bins = sorted((site / "firmware").glob("*.ota.bin"))
    if not ota_bins:
        sys.exit("No *.ota.bin found under %s/firmware" % site)
    ota = ota_bins[0]

    manifest = {
        "name": "Garage Door Controller",
        "version": version,
        "builds": [
            {
                "chipFamily": "ESP32-C6",
                "ota": {
                    "md5": hashlib.md5(ota.read_bytes()).hexdigest(),
                    "path": f"firmware/{ota.name}",
                    "summary": f"Self-hosted build {version}",
                    "release_url": "https://github.com/CGNSChris/esphome-garage-door",
                },
            }
        ],
    }

    out = site / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {out}:\n{out.read_text()}")


if __name__ == "__main__":
    main()
