# Architecture and local generation

## Host-side tools

The Python application provides a settings window, profile files, a command-line interface, and a focused-window key-event test. Its normal runtime uses the Python standard library and Tk. It does not open HID devices, read firmware from the keyboard, send configuration requests, or flash an update.

The builder accepts one exact stock file, verifies its length and SHA-256, and generates a modified file locally. It checks the firmware structure and patch boundaries, applies the project-authored payload and hooks, and updates the required checksums. A generated file is a local build artifact and must not be redistributed through this repository.

One compatibility routine contains device-specific instructions derived from the user's own stock image during generation. The repository supplies the reconstruction recipe rather than the extracted manufacturer routine. This separation avoids bundling that routine or a complete stock image; it is not a legal guarantee about every jurisdiction or firmware license.

Prebuilt project-authored payload data supports normal local generation. Rebuilding that native payload is a separate development task using Ghidra and the included native source. Ghidra is not required merely to use the settings app or build from the supplied payload data.

## Firmware-side flow

The implementation hooks selected points in the original scan and input path. It preserves the stock initial APC decision and applies RT only to the eight configured physical sensor positions.

1. Acquire a frame that records the sensor, timing, configuration generation, and relevant stock settings.
2. Reject a frame if its identity or settings changed during acquisition, or if mode, gain, timing, or sensor values are invalid.
3. Prepare the selected key's candidate RT state from the consistent frame.
4. Recheck the configuration and sample identity before staging the decision.
5. Run the original input-state path and commit the staged state only under the expected conditions.

Per-key committed state is separate for W, A, S, D, Q, E, Left Shift, and Space. A shared staging area has an owner check, so one key cannot commit another key's pending state. Configuration-generation checks invalidate stale work. Unsupported or disabled keys retain the stock path.

The firmware also observes relevant settings writers and reload paths so state can be invalidated after a change. This should not be read as proof of every reconnect, sleep/wake, or error-recovery path; those require separate hardware tests.

## Why the target is exact

Hooks, addresses, sensor positions, state layout, and available code/RAM space depend on the accepted firmware and hardware assumptions. A related product name or a newer firmware version does not establish equivalence. The builder therefore pins the original file identity rather than guessing compatibility from a filename.

The development setup assumed a common R3-family layout and sufficient RAM for the compact eight-key state. Physical MCU markings and RAM capacity were not inspected. Host-side memory-boundary tests check the assumed layout, but cannot prove the hardware identity or eliminate stack and interrupt behavior outside the exercised model.

## Validation layers

- Host application tests cover profile handling, settings, local generation, and validation failures.
- Native synthetic tests exercise the patched instruction path, including key separation and rejected transactions, against modeled device state.
- Hardware feedback covers the user's reported behavior on one R3SC31 keyboard.

These layers answer different questions. Synthetic execution does not measure real sensor noise, USB timing, interrupt interactions, or recovery after a failed update. See [validation and limitations](validation.md) for the public support boundary.
