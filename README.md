# LetPot for Home Assistant (watering system support)

A HACS custom integration that **replaces** Home Assistant core's `letpot` integration (same domain) and adds support for LetPot Automatic Watering Systems (ISE05 / DI-2, ISE06 / DI-3). Hydroponic gardens keep working as in core. Based on the core integration and [python-letpot](https://github.com/jpelgrom/python-letpot); the plan is to upstream this to core and the library.

> **Status: experimental.** Pump control follows the hardware-validated approach of [HSTEP's v1.0.1](https://github.com/HSTEP/letpot2.0-home-assistant/releases/tag/v1.0.1) (DI-3), but the extra number/select/switch entities here have not been tested on a device. Report results.

## Install
1. HACS -> Custom repositories -> add this repo as *Integration*, install, restart Home Assistant.
2. If core's LetPot is already configured, it is picked up as-is (same domain). Otherwise add it via Settings -> Devices & Services.

## Watering system entities
| Entity | Type |
|---|---|
| Pump | switch (manual on/off) |
| Cycle watering | switch (config) |
| Manual watering duration (min), Cycle frequency (h), Cycle duration (min), Cycle work/rest interval (s) | number (config) |
| Cycle mode (continuous / intermittent) | select (config) |
| Pump running, Low water | binary sensor |
| Next watering, Last watering, Watering ends | timestamp sensors (rounded to the minute) |
| Last watering reason | enum sensor (diagnostic) |

## Dry-run protection
A **Dry-run protection** config switch (per watering system, on by default) uses the device's low-water flag (the **Low water** binary sensor, now enabled by default):
- Turning on the pump or cycle switch is refused while low water is reported.
- If low water is reported while the pump is running, a stop is sent (and the cycle is switched off if the cycle started the run). This also covers runs started by the device's own cycle or schedule, but only once the status update arrives (about a second); it cannot prevent the firmware from starting them.
- If the low-water flag is unknown, nothing is blocked. Turn the switch off if your sensor misreports.

The low-water bit is reverse-engineered and unconfirmed across models/firmware; do not rely on it as your only protection.

## Known caveats
- **Do not override the library's write encoder.** An earlier community version did, which moved the duration bytes ahead of the cycle flag; a 3-minute write was stored as 768 minutes and the DI-3 stopped after 1-3 seconds. This integration uses the library's encoder as-is (guarded by `tests/test_protocol.py`).
- **Recovering a device already affected:** after installing this version and fully restarting Home Assistant, set the device's *Manual watering duration* (the number entity here, or the LetPot app) to the value you want. A Home Assistant helper does not change what is stored on the device.
- Setters use python-letpot private helpers (`_get_publish_status`, `_publish_status`) until the library has public ones.
- Cloud-dependent (LetPot MQTT servers); no offline/local control.
- Reports exist of the pump occasionally failing to start until the device is hard-reset.

## Tests
```bash
pip install letpot==0.7.0
python -I -m unittest discover tests
```

`tools/repair_manual_duration.py` (from HSTEP's fork) is a one-time terminal tool to inspect or restore a DI-3's stored manual duration; read-only unless `--apply` is given. See its `--help`.
