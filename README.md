# LetPot for Home Assistant (watering system support)

A HACS custom integration that **replaces** Home Assistant core's `letpot` integration (same domain) and adds support for LetPot Automatic Watering Systems (ISE05 / DI-2, ISE06 / DI-3). Hydroponic gardens keep working as in core. Based on the core integration and [python-letpot](https://github.com/jpelgrom/python-letpot); the plan is to upstream this to core and the library.

> **Status: experimental, untested on hardware by the author of this fork.** The device write-protocol byte order is unverified (see below). Report results.

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

## Known caveats
- `custom_components/letpot/watering.py` replaces the library's ISE write message (manual duration before the cycle flag, as in the earlier community fix). This is unverified against a packet capture; if the pump or settings misbehave, disable it via `apply_protocol_patch()` in `__init__.py`.
- Setters use python-letpot private helpers until the library has public ones.
- Cloud-dependent (LetPot MQTT servers); no offline/local control.
- Reports exist of the pump occasionally failing to start until the device is hard-reset.
