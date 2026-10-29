# Setup and input checks

## Before generating a file

Use the exact stock firmware identified in the [README](../README.md). Keep the original file unchanged in a private local folder. The builder's identity check is mandatory; changing the expected hash does not make another keyboard compatible.

Install Python and the app as described in the README. The settings app edits local settings and files. It does not read the keyboard's installed firmware or current settings, and it cannot confirm which firmware is currently flashed.

Keep another keyboard available for the update workflow. The only described return path is another update through the manufacturer's working updater. An unresponsive device, a failed update, or an unavailable update interface may require a different recovery method that this project has not verified.

## Choose a profile

Each supported physical key has three settings:

| Setting | Meaning |
| --- | --- |
| RT enabled | Apply RT to this key; when disabled, use the stock input path |
| Release level | Upward movement required to release a held key |
| Re-press level | Downward movement required to press it again |

Both levels range from 1 to 7. A smaller number responds to smaller movement. The default is enabled, release 1, re-press 1 for all eight keys. If that is too sensitive for your use, increase the release or re-press level independently.

These settings are expressed in sensor units. They are not millimeters and cannot be compared directly with another keyboard's millimeter settings. This project does not provide professional-player presets or a physical travel calibration.

Saving a profile creates a local settings file. Generating firmware creates a separate file from the selected stock input and profile. Neither operation changes the keyboard. Use the output from the current generation when updating, so an older file is not mistaken for the new settings.

## Update separately

Use the manufacturer updater through its normal workflow with the generated file. This repository does not redistribute that updater or automate flashing.

After a successful update, release all keys fully and allow them to settle. Start with simple input checks before using the keyboard in a game. If the current keyboard already contains the accepted local baseline and behaves correctly, installing this app alone does not require flashing again.

## Check the eight keys

Open the app's local input test, or run:

```powershell
python -m r3s_rt key-test
```

Click **Start 20-second check** to begin recording, then keep the test window focused. Start another check if you need more time for the steps below.

The test observes normal key events only while its window is focused. It stops after 20 seconds, or when focus is lost, and saves its result in your local user data. It distinguishes Left Shift from Right Shift and ignores ordinary key-repeat events. It cannot identify which physical keyboard generated an event, measure Raw sensor movement or latency, or prove the installed firmware's identity.

1. Press and release W, A, S, D, Q, E, Left Shift, and Space individually. Confirm ordinary key-down and key-up behavior.
2. Hold a supported key below its stock APC activation point. Raise it slightly, then press it down slightly. Confirm release and re-press without returning fully to the top.
3. Repeat at several depths, including away from the bottom. Do not expect the same physical distance at every depth; thresholds are in Raw units.
4. Try combinations used in your applications, such as W + Left Shift and W + Space. Confirm that releasing one key does not release the others.
5. In a separate text editor, confirm ordinary typing and keys outside the supported group. The input test records only the eight supported keys; Right Shift is not one of the RT keys.
6. If you change a profile, generate and install a new file, then repeat the relevant checks.

USB reconnect, reboot, sleep/wake, and stock-application configuration changes should be tested separately on your setup. They were not all individually confirmed in the eight-key user report.

## If RT seems inactive

- Let the affected key return fully to rest and remain still. RT needs 32 valid quiet samples to rearm after a reset.
- Confirm that the generated profile enables that physical key.
- Confirm that the manufacturer application uses one of the four global APC selections in the supported mode. Individual APC modes are unsupported.
- Check that the updater actually used the newly generated file. The settings app cannot read back the installed firmware.

If the behavior remains wrong, stop using that build and return to your own original stock firmware through the working manufacturer updater, if available. Include your model, profile, and reproducible steps in a report, but **do not upload firmware files, serial numbers, or private paths**.
