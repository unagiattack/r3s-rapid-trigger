# RT behavior and sensitivity

## Initial press and subsequent movement

The first press uses the keyboard's stock APC behavior. Once RT is active, the firmware tracks movement relative to the recent extreme:

- While the key is down, sufficient upward movement from the recent deepest point releases it.
- While the key is up within the active RT cycle, sufficient downward movement from the recent highest point presses it again.

The same selected thresholds apply across the active travel range. Short re-presses do not require a return to the bottom. The implementation does not add a separate bottom-only re-press condition.

The eight supported physical keys are independent. A key disabled in the profile follows the stock input path. Key names refer to the original physical matrix positions; custom host mappings and remapped firmware layouts have not been validated.

## Levels are Raw sensor amounts

Release and re-press levels use the following base amounts:

| Level | Base amount in Raw units |
| --- | ---: |
| 1 | 48 |
| 2 | 72 |
| 3 | 120 |
| 4 | 160 |
| 5 | 240 |
| 6 | 320 |
| 7 | 480 |

A movement must be **strictly greater than the selected amount plus a 16-Raw deadband**. At level 1, for example, a 64-Raw movement is insufficient and a 65-Raw movement crosses that test.

These are internal sensor differences. They are not physical distances, measured noise specifications, or guaranteed equivalent settings across keys. No millimeter conversion has been validated. A profile described as `1 / 1` means release level 1 and re-press level 1.

## Top reset and rearming

Near the resting end of travel, RT resets when Raw is at or below the baseline plus 32. Rearming requires 32 valid quiet rest samples, with the rest-noise allowance of 16 Raw. This reduces reactivation from small changes near rest.

If a finger keeps making tiny movements near the top, the quiet-rest condition may not be reached. Release the key fully and let it settle. The number of samples is not a measured delay in milliseconds; no timing conversion or latency guarantee is provided.

RT also invalidates its state when acquisition is rejected, sample timing exceeds the 40-tick internal gap limit, or relevant configuration changes. Rejected state cannot be carried over as a valid press decision. The tick unit here belongs to the firmware's internal timing checks and should not be presented as a measured USB report interval.

## APC and manufacturer settings

The implementation supports the four global APC selections in internal mode 1 / gain 0. The initial press continues to use the stock APC decision. RT then uses the profile's Raw movement thresholds until a reset.

Individual APC modes are unsupported. The firmware checks mode, selection, gain, sample identity, and configuration generation before applying RT. Changing a relevant stock setting invalidates the current RT state, so fully releasing the key after a change is part of the expected workflow.

The settings app only describes the profile used to build an output file. It does not query the keyboard or prove that the displayed profile matches the installed firmware.
