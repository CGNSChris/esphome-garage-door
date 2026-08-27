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

![Wiring diagram: two reed endstops and a wall button switch to ground on GPIO18/10/11 with internal pull-ups; GPIO7 drives an opto-isolated relay and carries a mandatory 10 kΩ pull-down; the relay's dry contacts parallel the opener's wall-button terminals](wiring.svg)

The reed switches and wall button share a common ground with the controller.
The relay's contacts do **not** — they are a dry contact on the far side of the
module's optocoupler, and wire in parallel with the opener's existing wall
button.

## Pin map (defaults — change via substitutions, never in packages/)

| Function | Substitution | Default | Notes |
|---|---|---|---|
| Closed endstop reed | `pin_endstop_closed` | GPIO18 | `INPUT_PULLUP`, polarity via `endstop_closed_inverted` |
| Open endstop reed | `pin_endstop_open` | GPIO10 | `INPUT_PULLUP`, polarity via `endstop_open_inverted` |
| Relay trigger | `pin_relay` | GPIO7 | `restore_mode: ALWAYS_OFF` + hardware pull-down |
| Local button | `pin_button` | GPIO11 | `INPUT_PULLUP`, active low |
| Status LED | `pin_status_led` | GPIO2 | 1 kΩ series resistor |

### Why these five

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

**Free on both: GPIO1, 2, 6, 7, 10, 11, 14, 18, 21.** The five defaults come
from that list, which is why the harness is portable. Both configs are
validated in CI, and ESPHome checks pin numbers against the board definition —
so an illegal pin fails the build rather than the door.

This is the trap that bit the upstream config (its W2): Athom put the door
contact on GPIO18, which is a USB pin on the C3. It worked only because their
board carries a CH340 bridge and doesn't use native USB. Never inherit pin
numbers across chip families without re-checking them.

## Required external components

1. **10 kΩ pull-down from the relay GPIO to GND — MANDATORY.**
   The GPIO floats between power-on and firmware boot. A relay module with a
   floating input can latch on, and on a garage door that means the door moves
   with nobody there. `restore_mode: ALWAYS_OFF` and the 3-second boot
   suppression in firmware are the second and third layers; the resistor is
   the first.
2. **1 kΩ series resistor** on the status LED.
3. **Opto-isolated relay module** with a 3 V coil, triggered from 3.3 V logic.
   Relay contacts wire in parallel with the opener's wall-button terminals.
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
