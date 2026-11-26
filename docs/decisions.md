# Decisions

## 1. Use the library's write encoder as it is

An earlier community version replaced python-letpot's write message so the manual duration came before the cycle flag. On a DI-3 that stored a 3 minute duration as 768 minutes, and the pump stopped after a few seconds. We use the library's encoder and test the byte layout. The cost is that the exact layout still isn't confirmed against a packet capture beyond HSTEP's one device. We'd revisit this only if the library maintainer changes the layout.

## 2. Override core's `letpot` domain instead of using a new one

Keeping the domain means an existing config entry keeps working, and HACS can replace the built-in integration without a second account setup. The cost is that this copy has to follow core's changes by hand. Rejected: a separate domain, which would mean two LetPot integrations fighting over the same account.

## 3. Dry-run guard acts in two places

Starts are refused in the switch, and a running pump is stopped from the coordinator when a status update shows low water. The first catches mistakes from Home Assistant, the second also catches runs the device starts by itself. The cost is that it relies on one reverse-engineered flag. If the flag is unknown, the guard does nothing, because blocking watering on missing data seemed worse than not blocking it. We'd revisit this if the flag turns out to be unreliable on real devices.

## 4. Switching the cycle off after a dry stop

When the cycle started the run, the guard also turns the cycle off, since that's the only way the device interrupts a cycle run (VERIFY). This changes a setting the user chose. It's done only after a dry run is detected, and it's logged.

## 5. Private helpers for writing settings

python-letpot 0.7.0 has no public setters for the cycle fields, so writes call its private publish helpers. The alternative was a second encoder in this repo, which is the thing decision 1 avoids. We'll switch to public setters when the library adds them.

## 6. Interface wording follows conformIT's UI copy rules

The integration has no screen of its own, so the accessibility rules don't apply, but the entity names, config labels and error messages are the only words a user reads. They follow conformIT's `ui-copy.md`: plain words, one term per concept, and every error ends with a next step. The communication and unknown errors still show the library's exception text inside a sentence, because the cause helps when asking for help. The low-water error says to refill the tank or turn the guard off.

## 7. Dependency cooldown, with a limit

Dependabot is configured for pip with a 7 day cooldown and 14 days for major versions, per conformIT decision 26. Dependabot can't read the `requirements` list in `manifest.json`, which is the pin that actually ships, so the same version is listed in `requirements-dev.txt` for it to watch. The cooldown does not delay security updates, which is automatic on GitHub. What it can't do is update the real pin: a bump in `requirements-dev.txt` leaves `manifest.json` as it was, and changing the library version needs a manual, tested change anyway because decision 1 depends on its byte layout. Security updates also have to be switched on in the repository settings, which no file here controls.
