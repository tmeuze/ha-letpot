# Where this got to

Last updated 2026-11-24.

## Works

- On and off control of the pump, confirmed on the maintainer's device (model VERIFY).
- Offline tests pass for the write encoding, the dry-run policy and the repair tool.

## Written but not yet run on hardware

- The cycle switch, the duration, frequency and interval numbers, and the cycle mode select. The main risk is a write that changes a field it shouldn't, so check each value in the LetPot app after changing it.
- The timestamp sensors. They are worked out from "seconds from now" in each status message, so expect small drift.
- Dry-run protection, in particular whether the low-water flag follows the real tank level.

## Open questions

- Does switching the cycle off really stop a run the cycle started? The device reports that as "cycle disabled while running", but this is untested.
- Is the low-water flag the same on the DI-2 and DI-3?

## Next steps

- Run the checks above on a device and record what happened here.
- Tag a release so HACS can offer version updates. There are no GitHub releases yet.
- Decide on a licence and add a `LICENSE` file.
- Send the dry-run guard and the extra entities upstream, as separate pull requests.
