# Bill of materials

For the **v2 dual-endstop design**, on either supported chip. This supersedes
the C3-era BOM the project started from, which was written against the
single-sensor upstream config and is wrong in two ways that matter: it targets
the C3, and it lists the second reed switch as *optional*. In this design the
second endstop is the entire premise.

Prices are indicative AliExpress listings in USD and will drift. Search terms
are what actually returns the right part.

**Relay module — the requirement, and two verified candidates.** Needs a
**3 V / 3.3 V coil** and an **H/L trigger jumper**. Two boards checked against
photos on 2026-08-27, either acceptable:

| Board | Coil marking | Jumper | Note |
|---|---|---|---|
| SONGLE `SRD-03VDC-SL-C` | 3 V, confirmed in photo | present, unlabelled | identify H/L by bench test |
| BESTEP 1-channel, **3.3 V variant** | select at checkout | **`S1` silkscreened High/Low** | dual opto, status LEDs, screw terminals both sides |

> **Multi-variant listings are the trap here.** The BESTEP board ships in 3.3 V,
> 5 V, 12 V and 24 V coil versions from one listing, and the product photo may
> show any of them — a `JQC3F-12VDC-C` cube in the picture is the **12 V** part,
> which will not energise from 3.3 V at all. **Select the 3.3 V option
> explicitly**; do not assume the pictured item is what you get.

Either way, wiring is three screw terminals: `DC+`/`VCC` → 3V3, `DC-`/`GND` →
GND, `IN` → GPIO7, jumper to **High**. Boards whose input side is a screw
terminal need only **two** KF301 blocks (one per endstop run).

Ignore any "even if the control line is broken the relay will not move" claim
as a reason to skip the 10 kΩ pull-down. A severed wire is not the same case as
a GPIO floating during power-on while still connected, and the resistor is the
layer the whole boot-safety argument rests on.

**Compatibility confirmed:** the target opener has a plain momentary
dry-contact wall button (checked 2026-08-27), so the relay-across-the-terminals
approach in item 2 applies as designed. If you are reusing this BOM on a
different opener, run the check in
[opener-compatibility.md](opener-compatibility.md#check-this-first-is-your-wall-button-a-dry-contact)
first — on a digital wall console no relay wiring works at all.

---

## Quick order list

Everything, in one place, for pasting into a cart. Detail and reasoning below.

- [ ] 2 × ESP32-S3-DevKitC-1 **N16R8** *(or* ESP32-C6-DevKitC-1 N8*)*
- [ ] 1 × 1-channel relay module, opto-isolated, **H/L trigger jumper**; 3 V coil preferred (5 V fine — needs the JD-VCC split)
- [ ] 4 × MC-38 reed switch + magnet
- [ ] 1 × 3 mm LED assortment
- [ ] 1 × ¼ W resistor assortment (must contain 10 kΩ, 1 kΩ, 4.7 kΩ)
- [ ] 1 × double-sided perfboard 5×7 cm
- [ ] 2 × KF301-2P screw terminal block
- [ ] 1 × 2.54 mm female pin header strip
- [ ] 1 × 22 AWG silicone hookup wire kit
- [ ] 1 × non-metallic ABS project box, IP-rated
- [ ] 3 × PG7 cable gland
- [ ] 3M VHB pads + cable ties
- [ ] **Locally:** 20–30 m 2-core alarm cable 0.5 mm²
- [ ] **Locally:** 5 V 1 A USB-C supply (if you don't have a spare)

**Indicative total: ~USD 40–65** for the imported items, plus local cable and
power supply. The two dev boards are roughly a third of it.

---

## 1. The controller

| # | Qty | Item | Search term | ≈USD | Notes |
|---|---|---|---|---|---|
| 1 | **2** | Dev board — **either** chip | `ESP32-S3-DevKitC-1 N16R8` **or** `ESP32-C6-DevKitC-1 N8` | 6–10 ea | Firmware ships for both; see §4 to choose. On the S3 **the `R8` suffix is the point** — that is the 8 MB octal PSRAM. Buy two of whichever you pick: DOA rate is real, and the bench tests involve waving magnets at a rig you don't want to be the installed unit. |
| 2 | 1 | Relay module, 1 channel | `1 channel relay module optocoupler H L trigger` | 1–2 | **Check you don't already have one — a stepper-driver project won't have supplied it.** **Best: a 3 V coil with an H/L trigger jumper** — three wires (VCC→3V3, GND, IN→GPIO7), jumper to **H** (active-high, matching the shipped default), nothing else. **Verify the coil voltage from the relay cube's marking in the photos, not the description**: `SRD-03VDC-SL-C` or `HK4100F-DC3V` = 3 V and correct; `SRD-05VDC-SL-C` = 5 V, which is equally usable but needs the VCC–JD-VCC jumper removed and JD-VCC fed from 5 V. Both paths in [wiring.md](wiring.md#which-relay-module-to-buy-and-how-to-power-it). |
| 3 | **4** | Reed switch + magnet | `MC-38 wired door window magnetic sensor` | 1–2 ea | Two installed, two spare/bench. Prefer a **≥15 mm sensing gap** — see §3. |
| 4 | 1 | LED, 3 mm | `3mm LED assorted kit` | 2 /100 | Optional but useful — `status_led` shows WiFi/API state, which is the fastest way to diagnose a controller that has gone quiet. |
| 5 | 1 | Resistor kit, ¼ W | `1/4W metal film resistor assortment kit` | 3–5 | Needs 10 kΩ (**mandatory** relay pull-down), 1 kΩ (LED series), and 4.7 kΩ if either endstop run is over ~10 m. A kit beats buying three values. |

## 2. Assembly

| # | Qty | Item | Search term | ≈USD | Notes |
|---|---|---|---|---|---|
| 6 | 1 | Perfboard | `double sided prototype PCB 5x7cm` | 3 /10 | Solder it down. Dupont jumpers will not survive a garage. |
| 7 | 2 | Screw terminal block | `KF301-2P 5.08mm PCB screw terminal` | 2 /20 | One per endstop run. The chosen relay module has its own input screw terminal, so no third block is needed. |
| 8 | 1 | Pin header / socket strip | `2.54mm female pin header strip` | 2 /50 | Socket the dev board rather than soldering it — swapping it shouldn't mean desoldering. Note the S3-DevKitC-1 is **wider** than a C3/C6 DevKit; check your socket spacing against the actual board. |
| 9 | 1 | Hookup wire, 22 AWG | `22AWG silicone wire kit 6 colours` | 5–7 | Silicone stranded is far easier than solid-core PVC. |
| 10 | 1 | ABS enclosure | `ABS project box 100x60x25 waterproof` | 2–4 | **Non-metallic** — a metal box kills WiFi and the BLE proxy. IP-rated is worth it in a garage. |
| 11 | 3 | Cable gland, PG7 | `PG7 cable gland nylon` | 2 /20 | Two endstop runs plus the relay output. |
| 12 | — | Fixings | `3M VHB pads`, `cable ties` | 3–5 | VHB for the reeds — see the note in [wiring.md](wiring.md) about keeping the *open* endstop adjustable. |

## 3. Buy locally

| # | Qty | Item | Why local |
|---|---|---|---|
| 13 | 20–30 m | 2-core alarm cable, 0.5 mm² | Bulk cable is heavy; shipping wipes out the saving and lead time is weeks. **Two runs now, not one** — closed endstop at the door, open endstop up the track. Jaycar, Bunnings, or an electrical wholesaler. |
| 14 | 1 | 5 V 1 A USB-C supply | Correct plug type and actual electrical compliance on something powered 24/7. Don't buy an unbranded charger for this. Use a spare you trust if you have one. |

### On arrival, before building

- **Buzz out both reeds with a multimeter.** MC-38-class listings sell N/O and
  N/C and mislabel them constantly. Set `endstop_closed_inverted` and
  `endstop_open_inverted` to match what actually turned up — they are separate
  substitutions precisely because the two sensors may not agree.
- **Check the dev board's module marking**, not the listing title (see §4).
- **Set the H/L jumper to H.** Then check the relay cube's marking: a 3 V coil
  (`SRD-03VDC-SL-C` / `HK4100F-DC3V`) wires VCC straight to 3V3. A 5 V coil
  (`SRD-05VDC-SL-C`) needs the VCC–JD-VCC jumper removed and JD-VCC from 5 V —
  driven straight from 3.3 V it often fails to *release* rather than to close.
- **Determine whether the module is active-high or active-low** before wiring
  anything, and set the resistor direction and `relay_inverted` to match. This
  is the single most consequential check on the list — see
  [wiring.md](wiring.md#relay-trigger-polarity--get-this-right-before-powering-up).

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

### Considered and rejected: Seeed XIAO ESP32S3

Checked 2026-08-27 and **not adopted** — it works, but buys nothing here.

It is a real ESP32-S3 with PSRAM and an external antenna, and GPIO1/2/6/7 are
free on the XIAO, the S3-DevKitC and the C6 alike (all three validated), so a
shared pin map was available. Two reasons not to bother:

1. **No cost saving** at the prices actually available.
2. **The antenna advantage is moot** — there is a WiFi AP in the garage, so
   signal strength was never the constraint the external antenna would fix.

Against that it would have cost a pin remap, `logger: hardware_uart: USB_CDC`
(no UART bridge on the XIAO), and care with the relay coil on its smaller 3V3
regulator. Also worth knowing for any future S3 board: **esp-web-tools cannot
distinguish two ESP32-S3 boards** — they share a `chipFamily`, so a second S3
variant cannot be served alongside the DevKitC one. `make_manifests.py` refuses
duplicate families outright rather than mis-serving, so this fails in CI, loudly.

### Choosing the C6 instead

Entirely defensible. The C6 is a perfectly adequate host for this design —
nothing in Tier 1 is remotely stressed by either chip, and the BLE proxy works
on a C6 with the tuned scan window. You give up the second core and PSRAM, and
you gain an 802.15.4 radio and WiFi 6. Use `garage-door-c6.yaml`; it omits the
`psram:` package, which is the only functional difference between the two
configs.

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
- **No pushbutton.** The controller has no button of its own — your opener's
  existing wall switch already provides control independent of this device, and
  wired straight to the opener it survives the controller being unplugged.
- **No second set of wiring.** The four signal pins are drawn from the GPIOs
  free on *both* chips (see [wiring.md](wiring.md)), so the harness does not
  care which board you bought.
- **No buzzer or beacon.** Those belong to unattended auto-close, which is
  deliberately out of scope for v1 — it needs an audible and visual warning
  sequence before movement, which is a safety design conversation and not a
  firmware toggle.
- **No mains-rated relay, contactor or SSR.** The relay only closes a
  low-voltage dry contact. Anything heavier is wasted money and a bigger box.
