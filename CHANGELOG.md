# Changelog

## 1.2.2

- Reordered the README to conformIT's standard layout and added the overview diagram.
- Added a Dependabot config with a 7 day cooldown (14 for major versions) and `requirements-dev.txt` for it to watch.
- Reworded the two communication error messages so they say what to try next.
- Updated `docs/STATE.md`.

## 1.2.1

- Rewrote the README and added the changelog, state, decisions and credits docs.
- Renamed the "Watering ends" sensor to "Watering ends at".

## 1.2.0

- Added dry-run protection for watering systems. Starting the pump or cycle is refused while the device reports low water, and a pump that is running when low water appears is stopped. A config switch turns it off.
- The Low water sensor is now enabled by default.
- Added HSTEP's `tools/repair_manual_duration.py` and its tests.

## 1.1.0

- Moved the files into `custom_components/letpot/` and added `hacs.json` and translations so HACS can install it.
- Added the cycle switch, the manual and cycle duration, frequency and interval numbers, the cycle mode select, and the timestamp and last-reason sensors.
- Removed an override of the library's write encoder. It put the duration bytes before the cycle flag and corrupted the stored manual duration on a DI-3. Added tests that guard the byte layout.
- Added the missing `Callable` and `Coroutine` imports in `switch.py`.
