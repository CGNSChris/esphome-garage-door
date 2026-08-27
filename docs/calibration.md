# Calibration

Three numbers and one behaviour need to be measured on *your* opener before
the controller can be trusted: the opener's cycle type, the open travel time,
and the close travel time.

You can do this with the main firmware installed (watching the log), or with
the dedicated `calibration/calibrate.yaml` config, which adds a raw
**Pulse Relay** button and reports travel times as sensors.

## 1. Determine the cycle type

1. Start with the door fully **closed**.
2. Press the opener's wall button (or the Pulse Relay button) once.
   The door opens.
3. **Mid-travel, press once more.** Observe:
   - The door **immediately reverses** → **Type A**, set
     `opener_cycle_mode: reverse`.
   - The door **stops** (and a further press moves it the other way) →
     **Type B**, set `opener_cycle_mode: stop_then_reverse`.
4. Record the result in `garage-door.yaml`.

If you cannot test yet, leave the default `stop_then_reverse`: an extra pulse
on a Type A opener stops the door, whereas a missing pulse on a Type B opener
leaves it moving the wrong way. The default fails safe.

### Type B footnote — commanding the same direction twice

On a Type B opener the button cycle is open → stop → close → stop → open…
From a mid-travel stop, the next press always moves **opposite** to the last
travel. So when you command the *same* direction the door last travelled, the
firmware must send **three** pulses (wrong way, stop, right way) and the door
will visibly nudge the wrong way first. That is a property of the opener, not
a bug. See `docs/opener-compatibility.md` for the full pulse table.

## 2. Measure travel times

1. From fully closed, start the door and time it with a stopwatch until it
   reaches fully open. (With `calibrate.yaml` flashed, the **Last Open
   Duration** sensor reports it automatically from the endstops.)
2. Repeat for the close direction.
3. Write the values into `garage-door.yaml`:

```yaml
open_duration: "18.4"
close_duration: "17.9"
```

Times are in seconds, quoted, decimals allowed. The travel timeout is
`max(open, close) × travel_timeout_factor` (default 1.5); if the door is
slower in winter, raise the factor rather than padding the durations, because
the durations also drive the position estimate.

## 3. Verify

Run the bench acceptance tests in the README **before** wiring the relay to
the opener — in particular the power-cycle test with a multimeter across the
relay contacts.
