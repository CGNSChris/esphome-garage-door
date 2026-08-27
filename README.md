# esphome-garage-door

Self-hosted ESPHome firmware for an **ESP32-C6** garage door controller with
**two endstop sensors** and a real state machine. A fork-in-spirit of Athom's
`athom-garage-door.yaml`, rebuilt to remove its weaknesses:

| Upstream weakness | Fix here |
|---|---|
| One reed switch → cover is binary, never OPENING/CLOSING/partial | Two endstops + 7-state machine |
| Contact input on the USB D− pin | Pin map avoids USB and strapping pins |
| `update:` points at Athom's manifest → updates silently revert your config | Self-hosted build + manifest (GitHub Actions → Pages) |
| No travel timeout → jammed door reports a state that never happened | Timeout → explicit `FAULT_TIMEOUT`, commands refused until cleared |
| Floating contact input | Explicit `INPUT_PULLUP`, both edges debounced 50 ms |
| Relay GPIO floats during boot | Hardware 10 kΩ pull-down **and** 3 s boot suppression |
| `stop_action` blindly pulses (reverses many openers) | Opener cycle modelled explicitly (`opener_cycle_mode`) |
| BLE proxy at ~94 % RX duty cycle starves WiFi | 9 % duty cycle, scan gated on API connection, optional package |
| Factory reset = 4 s hold of the door button | Factory reset is an HA config entity only |

## Governing design principle

**The door must work with the network down.**

- **Tier 1 — must never fail:** endstop sensing, state machine, local button,
  relay pulse. Entirely on-device; no WiFi/API/DNS dependency.
- **Tier 2 — should work:** HA cover entity, diagnostics, OTA.
- **Tier 3 — disposable:** the BLE proxy. First to degrade, last to get
  resources. Delete one line in `garage-door.yaml` to drop it.

## Hardware

ESP32-C6-DevKitC-1 (8 MB), opto-isolated 3 V relay module, two reed switches,
**mandatory 10 kΩ pull-down on the relay GPIO**. Full details and the pin map:
[docs/wiring.md](docs/wiring.md).

## Install

1. Copy `garage-door.yaml`, set the substitutions (WiFi, pins, polarity).
2. First flash by USB: `esphome run garage-door.yaml`, or use the hosted
   web flasher once Pages is live.
3. Calibrate: [docs/calibration.md](docs/calibration.md) — determines
   `opener_cycle_mode`, `open_duration`, `close_duration`.
4. **Run the bench acceptance tests below before wiring the relay to the
   opener.**

Adopting via the ESPHome dashboard uses `dashboard_import` pointing at
**this** repo, never upstream.

## The state machine

States: `CLOSED, OPEN, OPENING, CLOSING, STOPPED_PARTIAL, FAULT_TIMEOUT,
FAULT_SENSOR` (+ boot-time `UNKNOWN`). Exposed as a position-capable template
cover, a `Door State` text sensor, and a `Fault` binary sensor
(`device_class: problem`) with a `Clear Fault` button. Position between the
endstops is a time-based estimate that snaps to exactly 0/1 at each endstop.

Faults refuse commands — the firmware never retries into a jam.

### Why not the built-in `endstop` or `feedback` cover platforms

Both were evaluated. **Do not "simplify" back to them:**

- **`endstop`** automatically fires `stop_action` on arrival at an endstop.
  On a one-button opener `stop_action` is "press the button" — so arriving at
  open would press again and start the door closing. Actively harmful.
- **`feedback`** (`has_built_in_endstop: true`) avoids that trap but assumes
  independently commandable open/close actions, which a single momentary
  button is not.

Neither models the ambiguity of a mid-travel command on a one-button opener.
See [docs/opener-compatibility.md](docs/opener-compatibility.md) for the
pulse-count logic (including one deliberate deviation from the original
design brief, documented there).

## OTA / self-hosting

GitHub Actions builds every push to `main` with `esphome/build-action@v8.0.0`
and publishes to GitHub Pages:

- `/index.html` — esp-web-tools USB flasher
- `/firmware/` — factory + OTA binaries, web-tools manifest
- `/manifest.json` — OTA manifest for ESPHome's `update` component
  (served from Pages, not Releases, because Releases redirects overflow the
  http_request buffer)

`verify_ssl: false` is deliberate and documented inline in
`packages/core.yaml`: integrity is gated by the manifest MD5, and the
manifest source is this repo. Do not point `ota_update_url` at anything you
do not control.

**Repo setup:** Settings → Pages → Source = *GitHub Actions*.

## Home Assistant extras

`ha/automations.yaml` — left-open alert and a prominent fault alert.
`ha/dashboard.yaml` — a status card.

**Auto-close is deliberately out of scope for v1.** Unattended closing
requires an audible + visual warning sequence before movement — a hardware
change (buzzer + beacon) and a safety design conversation, not a firmware
toggle.

## Bench acceptance tests

Nothing gets wired to the opener until all of these pass. Multimeter on the
relay contacts for 1.

1. Power-cycle 10× (plus a browned-out supply): the relay must never close.
2. Boot with no endstop active → cover position unknown, `IDLE`, no guessed state.
3. Boot with both endstops active → `FAULT_SENSOR`, `Fault` on, commands refused.
4. Simulated open cycle (move the magnet by hand): CLOSED → open command →
   OPENING with interpolating position → open endstop → OPEN, position 1.0.
5. Simulated close cycle: mirror, position 0.0.
6. Auto-reverse: while CLOSING, trigger the *open* endstop → OPEN, not a fault.
7. Timeout: command open, never trigger an endstop → `FAULT_TIMEOUT`, `Fault`
   on, further commands refused until cleared.
8. Mid-travel reverse: while OPENING, command close; count relay clicks
   against the table in docs/opener-compatibility.md.
9. **Network down (the Tier 1 test):** WiFi disabled entirely — the local
   button must still cycle the door and the state machine must still track
   endstops.
10. OTA: publish a build, confirm the update entity appears, installs, and
    comes back with pins intact.
11. `esphome config garage-door.yaml` validates clean and CI is green before
    any hardware is involved.
