# Opener compatibility

A garage opener has **one** momentary input. What a press does depends on the
opener's internal state, and there are two common behaviours:

- **Type A — reverse:** a press while moving immediately reverses direction.
- **Type B — stop-then-reverse:** a press while moving stops the door; the
  *next* press moves it the opposite way (the classic
  open → stop → close → stop → open cycle).

Set `opener_cycle_mode` accordingly: `reverse` or `stop_then_reverse`
(default, fails safe — see docs/calibration.md).

## Pulse sequences the firmware sends

`relay_pulse_width` (default 500 ms) per pulse, `inter_pulse_gap`
(default 600 ms) between pulses.

| From → To | Type A (`reverse`) | Type B (`stop_then_reverse`) |
|---|---|---|
| CLOSED → OPENING | 1 | 1 |
| OPEN → CLOSING | 1 | 1 |
| OPENING → CLOSING | 1 | 2 (stop, go) |
| CLOSING → OPENING | 1 | 2 (stop, go) |
| moving → STOPPED_PARTIAL | 1 | 1 |
| STOPPED → opposite of last travel | 1 | 1 |
| STOPPED → same as last travel | 1 | **3** (wrong way, stop, right way) |

### Why 3, not 2 (deviation from the original design brief)

The handover specified 2 pulses for the last row. But on a Type B opener, two
presses from stopped are *move-the-wrong-way, stop* — the door ends up
stopped again, not travelling in the requested direction, and the firmware
would sit in OPENING/CLOSING until the travel timeout faulted. Completing the
cycle takes three presses. The brief wrong-direction nudge (~1 s given the
pulse timing) is inherent to how Type B openers cycle; no pulse count avoids
it.

### After a fault or reboot, direction is unknown

If the controller has never seen the door move (fresh boot mid-travel, or a
just-cleared fault), it cannot know what the opener's next press will do. It
sends **1 pulse**, assumes the requested direction, and lets the endstops
correct it: reaching either endstop always snaps the state machine to that
endstop's state, and reaching no endstop within the timeout faults. This is
logged as a warning when it happens.

## Check this first: is your wall button a dry contact?

The relay works by shorting the opener's two wall-button terminals, in parallel
with the existing switch (see [wiring.md](wiring.md)). That only works if the
wall button is a **plain momentary dry contact** — two wires, shorted together
to trigger. Most openers are.

Some newer openers instead use a **digital wall console** that talks a serial
protocol over those two wires (Chamberlain/LiftMaster "Security+ 2.0" is the
common one, often a multi-button console with a light switch and an LED).
**Shorting those terminals does nothing, or confuses the console.** No relay
wiring will fix that; those openers need either an adapter that speaks the
protocol or a connection at a different point.

How to tell, before you buy anything:

1. Look at the wall console. One plain momentary button on two wires is almost
   always a dry contact. A console with several buttons, a light control, an
   LED, or a lock function is a strong hint it's digital.
2. Meter the two terminals with the door idle. A dry-contact opener shows a
   steady low DC voltage (commonly 5–24 V) that collapses to ~0 V while the
   button is held. A digital console shows an unsteady reading that doesn't
   behave like a clean short.
3. Definitive test: briefly bridge the two terminals with a wire link. If the
   door moves, a relay across them will work. If nothing happens, it's digital.

Everything else in this project — the dual endstops, the state machine, the
fault handling — is independent of this. Only the relay output depends on it.

> **This install:** confirmed 2026-08-27 — a plain momentary dry-contact wall
> switch. The relay-in-parallel approach applies as designed, and no adapter or
> protocol work is needed.

## Detecting movement you didn't command

Worth being explicit, because it's a consequence of sensing the door rather
than the button: **the controller cannot see the wall switch or the RF handset
being pressed.** It doesn't need to. The reed endstops watch the door, so:

- Door leaves the closed endstop with no command from us → the firmware logs
  *external control* and adopts `OPENING`. Same in reverse from `OPEN`.
- Arriving at either endstop always snaps the state to that endstop, whoever
  caused the movement, and clears any outstanding fault.

The one gap: if someone presses the **wall switch mid-travel** — stopping or
reversing the door partway — the controller keeps believing the original
direction until the travel timer expires, then reports `FAULT_TIMEOUT`. That is
safe (position is honestly reported as unknown, commands are refused) and it
**self-heals**: the next time the door reaches either endstop, the fault clears
and the state is correct again. Closing that gap properly would mean wiring an
opto-isolated sense input across the button terminals so the controller can see
every pulse including its own — worth doing only if mixed mid-travel control
turns out to be common in practice.

## Openers this cannot model

- Openers whose stopped-state behaviour is "always close" rather than
  "reverse of last travel" will occasionally get the 3-pulse sequence wrong.
  The endstops and travel timeout still bound the failure (wrong direction →
  wrong endstop → state corrected, or timeout → fault), but if you have one
  of these, use `reverse` mode and test carefully.
- Openers with separate open/close/stop inputs don't need this firmware's
  pulse logic at all — ESPHome's built-in `feedback` cover platform models
  them natively.
