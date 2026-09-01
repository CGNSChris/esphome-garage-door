# Wiring

MCU: **either** an ESP32-S3-DevKitC-1-N16R8 or an ESP32-C6-DevKitC-1-N8.
Framework: esp-idf on both. See [bom.md](bom.md) for the trade-off and what to
order.

**The wiring is identical for both boards.** The pin map below is drawn from the
intersection of the two chips' usable GPIOs specifically so one harness fits
either, and swapping boards needs no rewiring. Pick your entry point:

| Board | Config | Notes |
|---|---|---|
| ESP32-S3-DevKitC-1-N16R8 | `garage-door.yaml` | Dual core + 8 MB PSRAM; better BLE proxy host |
| ESP32-C6-DevKitC-1-N8 | `garage-door-c6.yaml` | Single core, no PSRAM; adds Thread/Zigbee radio |

![Wiring diagram: two reed endstops switch to ground on GPIO18 and GPIO10 with internal pull-ups; GPIO7 drives an opto-isolated relay and carries a mandatory 10 kΩ resistor; the relay's dry contact parallels the opener's existing wall switch across the same two terminals](wiring.svg)

The two reed switches share a common ground with the controller. The relay's
contacts do **not** — the contacts are mechanically separate from the coil
inside the relay, so the opener side shares no ground with the ESP32 at all.
(The optocoupler isolates the *input* side; the contact isolation is the
relay's own construction, and would hold even without it.)

**Your existing wall switch stays connected.** The relay contact and the wall
switch bridge the *same two* opener terminals, so they sit in parallel and
either one operates the door. Nothing is removed and nothing is intercepted;
the opener still sees exactly the momentary short it has always seen. Before
wiring anything, confirm your wall button really is a dry contact and not a
digital console — see
[opener-compatibility.md](opener-compatibility.md#check-this-first-is-your-wall-button-a-dry-contact).

**Position sensing is independent of all of that.** The controller has no idea
whether a press came from us, the wall switch, or the RF handset — it watches
the *door* through the two reeds. So the state stays correct however the door
was operated, which is exactly why this design needs the reeds rather than
tapping the button circuit.

## Pin map (defaults — change via substitutions, never in packages/)

| Function | Substitution | Default | Notes |
|---|---|---|---|
| Closed endstop reed | `pin_endstop_closed` | GPIO18 | `INPUT_PULLUP`, polarity via `endstop_closed_inverted` |
| Open endstop reed | `pin_endstop_open` | GPIO10 | `INPUT_PULLUP`, polarity via `endstop_open_inverted` |
| Relay trigger | `pin_relay` | GPIO7 | `restore_mode: ALWAYS_OFF`, polarity via `relay_inverted`, + the mandatory 10 kΩ — see below |
| Status LED | `pin_status_led` | GPIO2 | 1 kΩ series resistor |

### Why these four

Each chip reserves a different set of pins, so the defaults are taken from the
intersection of what both leave free:

| Reserved on | Pins | Why |
|---|---|---|
| S3 | GPIO19, GPIO20 | Native USB D−/D+ |
| S3 | GPIO0, GPIO3, GPIO45, GPIO46 | Strapping |
| S3 | GPIO43, GPIO44 | UART0 — the logger |
| S3 | GPIO26–GPIO32 | SPI flash |
| S3 | GPIO33–GPIO37 | Octal PSRAM (every "R8" board) |
| C6 | GPIO12, GPIO13 | Native USB-Serial-JTAG D−/D+ |
| C6 | GPIO4, GPIO5, GPIO8, GPIO9, GPIO15 | Strapping |
| C6 | GPIO16, GPIO17 | UART0 — the logger |
| C6 | GPIO24–GPIO30 | SPI flash |

**Free on both: GPIO1, 2, 6, 7, 10, 11, 14, 18, 21.** The four defaults come
from that list, which is why the harness is portable. Both configs are
validated in CI, and ESPHome checks pin numbers against the board definition —
so an illegal pin fails the build rather than the door.

This is the trap that bit the upstream config (its W2): Athom put the door
contact on GPIO18, which is a USB pin on the C3. It worked only because their
board carries a CH340 bridge and doesn't use native USB. Never inherit pin
numbers across chip families without re-checking them.

## Which relay module to buy, and how to power it

**Best case: a 1-channel module with a 3 V coil and an H/L trigger jumper.**
That combination needs no tricks — three wires and one jumper setting — and it
is what the diagram shows.

| Pin | Connect to |
|---|---|
| `VCC` | **3V3** |
| `GND` | GND |
| `IN` | `GPIO7` |

Set the **H/L jumper to H** (active-high), which matches the shipped
`relay_inverted: "false"` and the 10 kΩ pull-down. Done.

### Verify the coil voltage from the photos, not the description

Listing copy is templated and frequently wrong. The claim that matters is the
coil voltage, and the truth is printed on the relay cube itself:

| Marking on the cube | Coil | Verdict |
|---|---|---|
| `SRD-03VDC-SL-C` | 3 V | correct — wire as above |
| `HK4100F-DC3V` | 3 V | correct — wire as above |
| `SRD-05VDC-SL-C` | 5 V | the copy was wrong — use the 5 V path below |

This is the same failure mode as the ESP32 module marking: read the silkscreen,
not the title.

### If you end up with a 5 V-coil module

Perfectly usable, and these are the easiest to source — but a 5 V-coil module
driven straight from 3.3 V logic is unreliable. On the usual input topology the
opto LED sits between VCC (5 V) and IN, so a 3.3 V "high" still leaves ~1.7 V
across it — often enough to keep it partly conducting, and **the relay never
cleanly releases.** The classic "my 5 V relay module won't switch off" fault.

Most such modules carry a **3-pin GND / VCC / JD-VCC header with a jumper**,
which exists precisely to fix this. Remove it and the supplies split:

| Pin | Connect to | Feeds |
|---|---|---|
| `JD-VCC` | **5 V** (the dev board's 5 V pin, from USB) | the relay coil |
| `VCC` | **3V3** | the optocoupler input side |
| `IN` | `GPIO7` | — |
| `GND` | GND | — |

The opto then sees real 3.3 V logic while the coil gets its 5 V — and as a
bonus the coil's ~70 mA comes off the USB 5 V rail rather than the board's
3.3 V regulator. No JD-VCC pin? Feed `VCC` from 5 V, keep H/L on **H**, and
confirm on the bench that the relay both closes *and fully releases*.

### Powering a 3 V coil from the 3V3 rail

Fine on a DevKitC — its regulator is fed from USB and rated well above the
~70 mA coil plus the chip's ~350 mA WiFi peaks. Fit a bulk capacitor (~470 µF)
on the 3V3 rail near the module as cheap insurance, and treat bench test 1
(power-cycle plus a deliberately browned-out supply) as the check that it holds.

### If it is a 10 A module, the rating is irrelevant — and slightly imperfect

The contacts only bridge the opener's low-voltage button terminals, so 10 A is
enormously over-spec. Harmless, and these modules are cheap and everywhere.

The one real caveat: heavy silver-alloy contacts are designed to carry current,
and switching only a few milliamps can eventually leave an oxide film that a
low-current circuit cannot burn through. In practice these modules run garage
openers for years without trouble, and the relay cycles only a handful of times
a day. But if, months in, the door starts ignoring occasional commands while
the wall switch still works, suspect contact oxidation — the fix is a signal
relay with gold-plated contacts, not more firmware.

## Relay trigger polarity — get this right before powering up

Coil voltage is not the risk — the section above covers powering it.
**Whether the module is active-high or active-low is**, because it decides what
the relay does during the power-on window before firmware boots. Setting the
H/L jumper to **H** puts you in the safe first row and is why that module is
recommended.

| Module | Resistor | IN during boot | Relay | |
|---|---|---|---|---|
| **Active-HIGH** | 10 kΩ pull-**down** to GND | LOW | off | **safe — shipped default** |
| Active-LOW | 10 kΩ pull-**down** to GND | LOW | **on** | **dangerous** |
| Active-LOW | 10 kΩ pull-**up** to 3.3 V | HIGH | off | safe |

The middle row is the trap. An active-low module on a pull-down sees a LOW
input for the entire time between applying power and the firmware taking
control — so the relay closes and **the door moves on every power-up, every
brownout and every reboot.** That is the exact failure the resistor exists to
prevent, inverted into the thing it was meant to stop.

### If your module is active-low

Two changes, and they must be made **together**:

1. Hardware: fit the 10 kΩ as a **pull-up to 3.3 V**, not a pull-down.
2. Firmware: set `relay_inverted: "true"` in your entry point.

One without the other is worse than neither. With the resistor changed but not
the firmware, the relay is energised whenever the door is idle; with the
firmware changed but not the resistor, you are back to the dangerous row.

**Easiest path:** many 1-channel modules have an **H/L trigger jumper.** Set it
to **H**, keep the pull-down, and leave `relay_inverted: "false"`.

### How to tell which you have

- Read the silkscreen. "Low level trigger" / "LOW trigger" means active-low.
- Or bench it, **with nothing connected to the opener**: power the module, leave
  IN unconnected but pulled down through the 10 kΩ, and listen. If the relay
  clicks in and stays closed, it is active-low. Confirm with a multimeter across
  COM/NO — continuity at rest means active-low.

This check is part of bench test 1, and it is the reason that test comes before
anything is wired to the opener.

## Your wall switch is not wired to the controller

There is **no button on the ESP32 at all.** The controller has exactly four
signals: two reed inputs, one relay output, one status LED.

Your opener's existing wall switch stays wired to the *opener's* own terminals
and is **never connected to the ESP32**. You do not rewire it, extend it, or
tap it. The relay contact simply lands across those same two terminals, in
parallel, so both work independently and the opener sees the same momentary
short it always has.

That switch is also what gives you control when the network is down. It is
wired straight to the opener, so it works even if this controller is unplugged,
crashed, or removed entirely — which is a stronger guarantee than any button
on the ESP32 could offer.

## Required external components

1. **10 kΩ resistor on the relay GPIO — MANDATORY. Its direction depends on
   your relay module — see *Relay trigger polarity* above before fitting it.**
   For the default active-high module it is a **pull-DOWN to GND**.
   The GPIO floats between power-on and firmware boot. A relay module with a
   floating input can latch on, and on a garage door that means the door moves
   with nobody there. `restore_mode: ALWAYS_OFF` and the 3-second boot
   suppression in firmware are the second and third layers; the resistor is
   the first.
2. **1 kΩ series resistor** on the status LED.
3. **Opto-isolated relay module**, 1 channel, with an H/L trigger jumper and a
   JD-VCC pin — see *Which relay module to buy* above for the jumper settings
   and supply arrangement. Contacts wire in parallel with the opener's
   wall-button terminals.
4. **Two reed switches** (MC-38 class) with magnets, on 2-core alarm cable:
   - *Closed* endstop: magnet on the door, switch on the frame, aligned when
     the door is fully closed.
   - *Open* endstop: switch positioned so it activates only at full open
     (usually on the track near the motor head).
   Reed wiring: one core to the GPIO, the other to GND. The firmware enables
   the internal pull-up.
5. **4.7 kΩ pull-up to 3.3 V per endstop — only if that cable run exceeds
   ~10 m.** The ESP32's internal pull-up is weak (~45 kΩ). Against the
   capacitance of a long 2-core run that gives slow edges and more noise
   pickup. An external 4.7 kΩ at the *board* end stiffens the line
   considerably. It needs no firmware change — the internal pull-up simply
   gets helped — and the resistor kit in [bom.md](bom.md) already covers it.
   Short runs don't need it.

Mount the **open** endstop on something adjustable (VHB pad or a slotted
bracket). The closed position is defined by the door meeting the frame and
repeats precisely; where the door stops on the horizontal track varies by
several mm, so you'll want to tune that trigger point after watching the door
stop a few times. Prefer reeds with a sensing gap of **≥15 mm** for the same
reason.

## Polarity check

After flashing, watch the two `Closed Endstop` / `Open Endstop` diagnostic
entities. Each must be **on** exactly when the door is at that end. If one
reads inverted, flip its `endstop_*_inverted` substitution — they are separate
on purpose; do not assume the two reeds behave the same.

If both ever read on at the same time, the firmware latches `FAULT_SENSOR`
and refuses commands: that combination is physically impossible and means a
wiring or sensor failure.

## What a broken endstop cable looks like

Worth knowing, because it is a genuine benefit of having two sensors plus a
travel timeout. A severed reed cable leaves the pin pulled high and reading
"not at this endstop". If the door was closed at the time, the firmware sees
the closed endstop release with no command, assumes OPENING (§3.3), and then
faults on the travel timeout because no endstop ever arrives — surfacing as
`FAULT_TIMEOUT` with the `Fault` sensor on and commands refused.

So a broken sensor wire announces itself within one timeout period instead of
silently reporting a position the door was never in. The single-sensor upstream
design could not do this.
