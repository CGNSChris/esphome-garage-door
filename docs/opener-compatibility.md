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

## Openers this cannot model

- Openers whose stopped-state behaviour is "always close" rather than
  "reverse of last travel" will occasionally get the 3-pulse sequence wrong.
  The endstops and travel timeout still bound the failure (wrong direction →
  wrong endstop → state corrected, or timeout → fault), but if you have one
  of these, use `reverse` mode and test carefully.
- Openers with separate open/close/stop inputs don't need this firmware's
  pulse logic at all — ESPHome's built-in `feedback` cover platform models
  them natively.
