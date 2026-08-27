# Wiring

MCU: **ESP32-C6-DevKitC-1** (8 MB flash). Framework: esp-idf.

## Pin map (defaults — change via substitutions, never in packages/)

| Function | Substitution | Default | Notes |
|---|---|---|---|
| Closed endstop reed | `pin_endstop_closed` | GPIO18 | `INPUT_PULLUP`, polarity via `endstop_closed_inverted` |
| Open endstop reed | `pin_endstop_open` | GPIO19 | `INPUT_PULLUP`, polarity via `endstop_open_inverted` |
| Relay trigger | `pin_relay` | GPIO7 | `restore_mode: ALWAYS_OFF` + hardware pull-down |
| Local button | `pin_button` | GPIO3 | `INPUT_PULLUP`, active low |
| Status LED | `pin_status_led` | GPIO2 | 1 kΩ series resistor |

**Never use GPIO12/GPIO13** — they are the C6's native USB-Serial-JTAG D−/D+.
(The Athom config used GPIO18 for the contact input on the C3, where GPIO18 is
a USB pin; it only worked because their board has a CH340 bridge. On the C6,
GPIO18/19 are ordinary IO — but 12/13 are not.)

**Avoid GPIO4, GPIO5, GPIO8, GPIO9, GPIO15** — strapping pins.

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
   the internal pull-up; no external resistor needed on the reeds.

## Polarity check

After flashing, watch the two `Closed Endstop` / `Open Endstop` diagnostic
entities. Each must be **on** exactly when the door is at that end. If one
reads inverted, flip its `endstop_*_inverted` substitution — they are separate
on purpose; do not assume the two reeds behave the same.

If both ever read on at the same time, the firmware latches `FAULT_SENSOR`
and refuses commands: that combination is physically impossible and means a
wiring or sensor failure.
