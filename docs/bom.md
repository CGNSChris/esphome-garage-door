# Bill of materials

For the **v2 dual-endstop design** on an ESP32-S3. This supersedes the
C3-era BOM the project started from, which was written against the
single-sensor upstream config and is wrong in two ways that matter: it targets
the C3, and it lists the second reed switch as *optional*. In this design the
second endstop is the entire premise.

Prices are indicative AliExpress listings in USD and will drift. Search terms
are what actually returns the right part.

---

## 1. The controller

| # | Qty | Item | Search term | ≈USD | Notes |
|---|---|---|---|---|---|
| 1 | **2** | Dev board — **either** chip | `ESP32-S3-DevKitC-1 N16R8` **or** `ESP32-C6-DevKitC-1 N8` | 6–10 ea | Firmware ships for both; see §4 to choose. On the S3 **the `R8` suffix is the point** — that is the 8 MB octal PSRAM. Buy two of whichever you pick: DOA rate is real, and the bench tests involve waving magnets at a rig you don't want to be the installed unit. |
| 2 | 1 | Relay module, 1 channel | `1 channel relay module 3V optocoupler` | 1–2 | **Check you don't already have one — a stepper-driver project won't have supplied it.** Wants an explicit PC817 optocoupler and a 3 V coil (`SRD-03VDC-SL-C` or `HK4100F-DC3V`). Contacts only bridge the opener's low-voltage button terminals, so a signal relay is ample; you do not need a 10 A mains relay. |
| 3 | **4** | Reed switch + magnet | `MC-38 wired door window magnetic sensor` | 1–2 ea | Two installed, two spare/bench. Prefer a **≥15 mm sensing gap**. See §3. |
| 4 | 1 | Momentary pushbutton | `panel mount momentary push button N/O` | 1–2 | Panel-mount is nicer than a tactile switch here since it is the control you actually press. Factory reset is *not* on this button, so it needn't be recessed. |
| 5 | 1 | LED, 3 mm | `3mm LED assorted kit` | 2 /100 | Optional but useful — `status_led` shows WiFi/API state, which is the fastest way to diagnose a controller that has gone quiet. |
| 6 | 1 | Resistor kit, ¼ W | `1/4W metal film resistor assortment kit` | 3–5 | Needs 10 kΩ (**mandatory** relay pull-down), 1 kΩ (LED series), and 4.7 kΩ if either endstop run is over ~10 m. A kit beats buying three values. |

## 2. Assembly

| # | Qty | Item | Search term | ≈USD | Notes |
|---|---|---|---|---|---|
| 7 | 1 | Perfboard | `double sided prototype PCB 5x7cm` | 3 /10 | Solder it down. Dupont jumpers will not survive a garage. |
| 8 | 3 | Screw terminal block | `KF301-2P 5.08mm PCB screw terminal` | 2 /20 | One per endstop run, one for the relay output. Field wiring stays serviceable. |
| 9 | 1 | Pin header / socket strip | `2.54mm female pin header strip` | 2 /50 | Socket the dev board rather than soldering it — swapping it shouldn't mean desoldering. Note the S3-DevKitC-1 is **wider** than a C3/C6 DevKit; check your socket spacing against the actual board. |
| 10 | 1 | Hookup wire, 22 AWG | `22AWG silicone wire kit 6 colours` | 5–7 | Silicone stranded is far easier than solid-core PVC. |
| 11 | 1 | ABS enclosure | `ABS project box 100x60x25 waterproof` | 2–4 | **Non-metallic** — a metal box kills WiFi and the BLE proxy. IP-rated is worth it in a garage. |
| 12 | 3 | Cable gland, PG7 | `PG7 cable gland nylon` | 2 /20 | Two endstop runs plus the relay output. |
| 13 | — | Fixings | `3M VHB pads`, `cable ties` | 3–5 | VHB for the reeds — see the note in [wiring.md](wiring.md) about keeping the *open* endstop adjustable. |

## 3. Buy locally

| # | Qty | Item | Why local |
|---|---|---|---|
| 14 | 20–30 m | 2-core alarm cable, 0.5 mm² | Bulk cable is heavy; shipping wipes out the saving and lead time is weeks. **Two runs now, not one** — closed endstop at the door, open endstop up the track. Jaycar, Bunnings, or an electrical wholesaler. |
| 15 | 1 | 5 V 1 A USB-C supply | Correct plug type and actual electrical compliance on something powered 24/7. Don't buy an unbranded charger for this. |

---

## 4. On the board choice

**Firmware is built and published for both chips, so this decision can wait
until you actually order** — buy whichever is available and cheaper on the day.
`garage-door.yaml` is the S3, `garage-door-c6.yaml` is the C6, the wiring is
identical, and the web flasher detects which board you plugged in.

If you have no reason to prefer one: **take the S3.** The reasoning, so nobody
has to redo it:

- **Dual core is the real difference.** S3 is dual-core Xtensa LX7 at 240 MHz;
  the C6 is a single 160 MHz RISC-V core. Tier 1 (endstops, state machine,
  relay) doesn't care in the slightest. It matters only for the BLE proxy,
  which is the one demanding workload in the design.
- **PSRAM matters more.** The C6 supports none at all. BLE proxy + WiFi + API
  + web server is heap-hungry, and the extra headroom is also what makes
  `ota_verify_ssl: "true"` a realistic option later (see `packages/core.yaml`).
- **The S3 does not fix radio coexistence.** Both parts have a single 2.4 GHz
  RF chain with time-division WiFi/BLE. The second core relieves the CPU-side
  half of the problem only; the scan duty cycle in `packages/ble-proxy.yaml`
  is what addresses the airtime half, and it stays tuned down regardless.
- **What you give up:** the C6's 802.15.4 radio (Thread/Zigbee/Matter) and
  WiFi 6. Neither is used here — this design is committed to ESPHome over
  WiFi — so the cost is future optionality, not function.

### Choosing the C6 instead

Entirely defensible. The C6 is a perfectly adequate host for this design —
nothing in Tier 1 (endstops, state machine, relay) is remotely stressed by
either chip, and the BLE proxy works on a C6 with the tuned scan window. You
give up the second core and PSRAM, and you gain an 802.15.4 radio and WiFi 6.
Use `garage-door-c6.yaml`; it omits the `psram:` package, which is the only
functional difference between the two configs.

### If you take the S3

**Verify the marking on the module can itself** (`ESP32-S3-WROOM-1-N16R8`), not
the seller's listing title. Clones frequently advertise "DevKitC-1" and ship a
plain N16 with no PSRAM, which throws away the main reason for choosing it. If
you do end up with a non-PSRAM board, delete the `psram:` line from
`garage-door.yaml`; if you get an `N8R2`, change its mode to `quad`. Getting
that wrong is a boot failure, not a warning.

## 5. Not needed

- **No CH340/USB-UART bridge.** That was only ever a workaround for keeping the
  door contact on GPIO18 the way upstream does. The pin map here avoids both
  chips' USB pins outright, which is the simpler fix.
- **No second set of wiring.** The five signal pins are drawn from the GPIOs
  free on *both* chips (see [wiring.md](wiring.md)), so the harness does not
  care which board you bought.
- **No buzzer or beacon.** Those belong to unattended auto-close, which is
  deliberately out of scope for v1 — it needs an audible and visual warning
  sequence before movement, which is a safety design conversation and not a
  firmware toggle.
