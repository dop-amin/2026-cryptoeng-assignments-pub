# Playground 0 - Print Demo

This is a minimalistic demo to help you get started with the development environment and quickly test output. It demonstrates the most basic UART communication - perfect for printf-style debugging.

## What This Demo Does

The board firmware sends a simple fixed string over UART, and the Python script on your computer receives and displays it. That's it! No commands, no complex protocol - just basic one-way communication. Use this to quickly test that your setup works and to print debug messages from your code.

## Learning Objectives

- Verify that your development board is connected and working
- Test that the toolchain is properly set up
- Understand basic UART communication
- Get familiar with the build and test workflow

## Files in This Playground

| Path | Description |
| --- | --- |
| `src/main.c` | Simple firmware that sends a greeting message |
| `tests/test.py` | Python script that reads and prints the board output |
| `Makefile` | Build system for compiling and testing |

## Running the Demo

### Quick Start

```bash
make test-qemu
```

This builds everything and tests in QEMU (no hardware needed).

### Step 1: Build and Flash (for Board)

First, build the firmware and flash it to your board:

```bash
make
make flash
```

### Step 2: Test on Board

Run the test to see the output from your board:

```bash
make test-board
```

You should see output like:

```
Connected to Board
============================================================
Reading output from board...
============================================================

====================================
Playground 0: Print Demo
====================================

Hello from the Nucleo board!
This is a simple demo of UART communication.

============================================================
PASS: Successfully received output from board!
============================================================
```

### Alternative: Test with QEMU

If you don't have the physical board connected, you can test with QEMU emulation:

```bash
make test-qemu
```

## Using This for Quick Testing

This playground is perfect for printf-style debugging:

1. **Edit `src/main.c`**: Add your own `hal_send_str()` calls to print debug info
2. **Run `make test-qemu`**: See your output immediately
3. **Iterate quickly**: Test small changes without modifying assignment code

This is faster than working in assignments and great for:
- Verifying your development environment works
- Testing simple C code snippets
- Printing debug information
- Understanding the build workflow

## Getting Help

If you run into issues:

1. Make sure your board is connected via USB
2. Check that you're in the `playground0-print` directory
3. Try `make clean` and rebuild
4. See `../common/TESTING_GUIDE.md` for more troubleshooting tips

## Additional Commands

- `make help-playground` - Show all available commands
- `make monitor` - Open a serial monitor to see raw UART output
- `make clean` - Clean build files
