# Validation and known limitations

## Hardware evidence

The development target was one REALFORCE R3S R3SC31 using stock A0.11 as its input firmware. On October 9, 2026, the user reported that the eight-key build worked well and accepted it as a completed local baseline. The report covers perceived operation; it is not an instrumented measurement.

The locally accepted eight-key, all-enabled `1 / 1` artifact has SHA-256:

```text
1a502cea7eba942c82cef4efaa89b4f3e9c025b6d1760bd69c9ef9f7276782ca
```

This identifies the saved local artifact. The installed firmware was not read back from the keyboard, so the exact flashed hash was not independently verified. That artifact and its stock input are not included in the public repository.

## Software evidence

The earlier local application had 68 passing Python tests, together with native synthetic instruction-path tests used during eight-key development. This is historical evidence about that development baseline, not an automatic test result for every revision of this public repository.

Current public-source checks should be run from a clean checkout and reported with the tested commit. They must verify local stock-file validation, profile handling, firmware construction, and relevant native behavior. Reproducing the accepted local output from the exact stock input is a useful byte-level comparison; it does not replace physical testing.

Synthetic tests used modeled device memory and selected peripheral behavior. They can detect many patching, state-isolation, and invalidation errors, but cannot establish real-world timing, electrical characteristics, or all interrupt interactions.

## Not established

The project does not claim validation of:

- Other R3 or R3S models, layouts, revisions, or firmware versions.
- Physical MCU identity or RAM capacity through board inspection.
- Millimeter-equivalent activation, release, or re-press distances.
- Measured input latency, polling rate improvements, or performance against commercial RT keyboards.
- Every USB reconnect, reboot, sleep/wake, or stock-application setting-change sequence.
- All rollover combinations or long-term reliability across multiple keyboards.
- Recovery from a failed update or a keyboard that no longer presents a working update interface.
- Compatibility with game rules, tournament policies, anti-cheat systems, or another product's firmware.

The four global APC selections in internal mode 1 / gain 0 are the intended supported settings. Individual APC modes are unsupported.

## Returning to stock

Keep your own original, supported stock file and the manufacturer's updater available locally. If the keyboard still has a functioning update path, the intended return method is a normal stock-firmware update using that tool. This project has not established a universal recovery method, a bootloader rescue sequence, or a hardware flashing procedure.

No original image, previous modified image, updater, or recovery backup is distributed here. The settings app does not perform device writes. A local output file or a successful software test alone does not mean it is safe to install on another device.

## Reports that help

Use the issue template to provide the exact keyboard model, stock-input hash, project commit, enabled keys, sensitivity levels, global APC selection, and reproducible behavior. Distinguish a fresh boot, USB reconnect, sleep/wake, and a settings change when relevant.

Do not attach `.rfb` files, full private development folders, serial numbers, or screenshots containing private paths. Maintainers should not ask you to upload manufacturer firmware. Plain-text hash values and a redacted profile are enough for file identity and configuration.
