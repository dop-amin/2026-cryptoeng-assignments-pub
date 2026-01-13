# Testing Guide (Board & QEMU)

Use this guide whenever you need to run the automated tests for an assignment.
The same Python harness talks to the firmware whether it is running on the STM32
board or inside QEMU.

## Prerequisites

- Build the assignment firmware (`make` inside the assignment directory).  
- Open a Nix development shell so Jasmin, the ARM toolchain, QEMU, and Python
  dependencies are available.  
- For hardware runs, connect the Nucleo-L4R5ZI and identify the serial device
  name.

## Running the Tests

We will give details about running the tests for chacha20 here but the same
principles apply to any other assignment.

### QEMU (fast feedback)

```bash
cd assignment1-chacha20
make test-qemu
```

This target rebuilds the firmware for `PLATFORM=qemu`, launches
`qemu-system-arm` (MPS2-AN386) with the UART exposed on TCP port 5555, and
executes `tests/test_chacha20.py --platform qemu --elf build/chacha20.elf`.

### Physical board

```bash
cd assignment1-chacha20
make clean flash          # build and program the STM32 firmware
make test-board           # runs tests/test_chacha20.py --platform board
```

If automatic port detection fails, supply the serial path explicitly (e.g.,
`--port /dev/ttyACM0` on Linux or `/dev/cu.usbmodem*` on macOS).

## Useful Script Flags

`tests/test_chacha20.py` accepts:

- `--platform board|qemu` - choose the transport.  
- `--elf <file>` - required for QEMU; ignored on hardware.  
- `--port <serial>` - override board auto-detection.  

Any failing test stops the run immediately and prints the mismatching inputs and outputs.

## Troubleshooting

| Symptom | Likely Cause | Suggested Action |
| --- | --- | --- |
| `Failed to connect to QEMU` | Port 5555 busy or QEMU crashed | `killall qemu-system-arm`, rerun `make test-qemu` |
| `QEMU communication timeout` | Firmware hung or asserted | Rebuild with `make PLATFORM=qemu clean all`, rerun to capture console output |
| `No board found` | Serial device not detected | List ports (`ls /dev/ttyACM*` / `ls /dev/cu.*`) and pass `--port` |
| `Permission denied: '/dev/ttyACM0'` | Missing serial permissions | Add your user to `dialout` (Linux) or use `sudo` temporarily |
| `ERR ...` responses from firmware | Malformed command or stale build | Confirm buffer lengths, clean and rebuild (`make clean` + `make`) |
| Any symptom | - | Re-connect USB cable  |

## Tips

- Iterate in QEMU first: it is deterministic and avoids flashing delays.  
- The same pattern applies to other assignments; only the directory and test
  script name change (for example, `assignment0-sum/tests/test_sum.py` or
  `assignment2-ecdh25519/tests/test_smult.py`).
