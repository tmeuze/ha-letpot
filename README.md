# LetPot for Home Assistant

**A HACS integration that adds LetPot automatic watering systems (DI-2 and DI-3) to Home Assistant, with a guard that keeps the pump from running on an empty tank.**

> **Status: in testing.** On and off control of the pump is confirmed on the maintainer's own device. The cycle settings, timestamp sensors and dry-run guard are written and unit tested but have not been run on real hardware yet, so treat them as unproven.
> This project comes with no warranty or guarantee of fitness for any purpose. Use it at your own risk.
>
> **LLM use.** Built with substantial AI assistance (Claude Code). The maintainer tests it on a real device and decides what ships.

<p align="center">
  <img src="https://raw.githubusercontent.com/tmeuze/ha-letpot/main/docs/images/overview.svg" alt="Three layers: the watering system and LetPot cloud, this integration with its client, coordinator and entities, and the dry-run guard with its start check, stop check and switch." width="860">
</p>

## What it does

Home Assistant core already ships a `letpot` integration, but it only covers LetPot's hydroponic gardens. This repository is a copy of that integration, under the same `letpot` domain, with the watering systems added. HACS installs it over the built-in one, and an existing LetPot config entry keeps working.

It talks to LetPot's cloud (MQTT) through [python-letpot](https://github.com/jpelgrom/python-letpot). Each watering system becomes a device with a pump switch, its cycle settings as number and select entities, and sensors for the next and last watering.

## Use cases

**Reach for it when** you want to water from an automation, for example only when a soil moisture sensor reads dry and the forecast shows no rain, or when you'd rather change the cycle from a dashboard than from the LetPot app.

**Look elsewhere when** you need control without internet, because everything goes through LetPot's cloud. Also look elsewhere if you can't tolerate an experimental integration: the cycle controls and the dry-run guard haven't been tried on hardware.

## Getting started

1. In HACS, open the menu, choose **Custom repositories**, and add `https://github.com/tmeuze/ha-letpot` as an **Integration**.
2. Download it and restart Home Assistant fully. A reload isn't enough, because Home Assistant has to load the new code.
3. If the built-in LetPot integration is already set up, you're done. Otherwise go to **Settings, Devices & services, Add integration**, search for LetPot, and sign in with your LetPot app account.
4. Open the device page and check that the entities listed under Usage are there.

## Usage

Everything below appears on the device page, and you can use it in dashboards and automations like any other entity.

| Entity | Type | What it does |
|---|---|---|
| Pump | Switch | Start or stop watering by hand |
| Cycle watering | Switch (config) | Turn the repeating cycle on or off |
| Dry-run protection | Switch (config) | Turn the low-water guard on or off |
| Manual watering duration | Number, minutes | How long a manual run lasts |
| Cycle frequency | Number, hours | How often the cycle starts |
| Cycle duration | Number, minutes | How long each cycle run lasts |
| Cycle work interval, Cycle rest interval | Number, seconds | On and off times in intermittent mode |
| Cycle mode | Select | Continuous or intermittent |
| Pump running, Low water | Binary sensor | Whether the pump is on, and whether the tank is low |
| Next watering, Last watering, Watering ends at | Sensor, timestamp | Rounded to the minute |
| Last watering reason | Sensor (diagnostic) | Manual, cycle, scheduled, interrupted, or never run |

If a number or setting looks wrong, check it in the LetPot app. A change here is written to the device, so the app is a good second opinion.

## Configuration

There are no options to set at install time beyond signing in. The one setting you may touch is **Dry-run protection**, a switch on each watering system that is on by default.

While it's on, and the device reports low water:

- Turning on the pump or the cycle is refused, with a message that says why.
- A pump that is already running gets a stop command. If the cycle started that run, the cycle is also switched off, which is how the device interrupts a cycle run.
- A run the device starts by itself can't be prevented. It's stopped when the next status update arrives, usually within a second.

If the device doesn't report the low-water flag, nothing is blocked. If your sensor reports low water wrongly, turn the switch off. The flag comes from reverse engineering and hasn't been confirmed across models or firmware (VERIFY), so don't make it your only protection. Keep the intake submerged, and consider a float switch.

The settings stored on the device (durations, cycle, mode) belong to the device. This integration reads them and writes changes, and the LetPot app can change them too.

## How it works

The diagram at the top shows the layers. The integration subscribes to the device's status over MQTT, keeps the latest status in a coordinator, and turns it into entities. A change from Home Assistant sends the full device state with that one field replaced, then waits for the device to confirm it.

Two details are worth knowing. The integration uses python-letpot's write encoder unchanged. An older community version overrode it, which stored a 3 minute duration as 768 minutes on some devices, and a test now guards against that. If your device was affected, set the manual duration again from the number entity here or from the LetPot app, because a Home Assistant helper doesn't change what's stored on the device. And writing the cycle settings uses private helpers from python-letpot 0.7.0, because the library has no public setters for them yet.

Some users report the pump occasionally refusing to start until the device is hard reset. Nobody has found the cause yet.

## Documentation

| Read | For |
|---|---|
| [Where this got to](docs/STATE.md) | What works, what's untested, and what to try next |
| [Decisions](docs/decisions.md) | The choices behind the encoder, the guard, the layout and the dependency cooldown |
| [Credits](docs/credits.md) | Where the code comes from |
| [Changelog](CHANGELOG.md) | What changed and when |

## Development

The tests don't need Home Assistant or a device. They cover the write encoding, the dry-run policy and the repair tool.

```bash
pip install -r requirements-dev.txt
python -I -m unittest discover tests
```

[`tools/repair_manual_duration.py`](tools/repair_manual_duration.py) is a one-time terminal tool, from HSTEP's fork, for reading or restoring a DI-3's stored manual duration. It only reads unless you pass `--apply`, so run it with `--help` first.

Entity names and error messages follow conformIT's UI copy rules: plain words, and an error says what to try next. This integration has no interface of its own, so the accessibility rules don't apply beyond that.

## Licence

No licence file has been added yet (VERIFY which one applies). This started as [HSTEP's custom component](https://github.com/HSTEP/letpot2.0-home-assistant) for the DI-3, which is itself a fork of Home Assistant core's `letpot` integration by [@jpelgrom](https://github.com/jpelgrom), so the code derives from Apache 2.0 licensed work. The plan is to send this upstream, first to HSTEP and then to Home Assistant core and python-letpot. Home Assistant's [AI policy](https://developers.home-assistant.io/docs/ai_policy) applies to anything sent to core.
