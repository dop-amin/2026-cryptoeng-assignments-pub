# Playground 1 - Benchmark Demo

This is a simple demo to help you quickly benchmark code. It shows how to measure performance using the cycle counter - perfect for testing different implementations and optimizations.

## What This Demo Does

The board firmware runs a simple function in a loop, measures the total cycles taken, and prints the results. Use this to quickly test the performance of your own C functions.

## Learning Objectives

- Understand how to use the cycle counter on the Cortex-M4
- Learn to measure performance of your code
- Get familiar with the `hal_get_time()` function
- See how to calculate cycles per iteration

## Files in This Playground

| Path | Description |
| --- | --- |
| `src/main.c` | Firmware that runs a benchmark and prints results |
| `tests/test_bench.py` | Python script that reads and displays the benchmark output |
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

Run the test to see the benchmark output from your board:

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
Playground 1: Bench Demo
====================================

Took 5000 cycles (5 per iteration)

============================================================
PASS: Successfully received output from board!
============================================================
```

### Alternative: Test with QEMU

If you don't have the physical board connected, you can test with QEMU emulation:

```bash
make test-qemu
```

## Understanding the Code

In `src/main.c`, the firmware:

1. Calls `hal_get_time()` to start the timer
2. Runs a simple function 1000 times in a loop
3. Calls `hal_get_time()` again to stop the timer
4. Calculates total cycles and cycles per iteration
5. Prints the results

The key functions are:
- `hal_get_time()`: Returns the current cycle count (64-bit value)
- `volatile`: Prevents the compiler from optimizing away the computation

## Using This as a Testing Ground

This playground is designed for quick performance testing:

1. **Edit `src/main.c`**: Replace `placeholder_function` with your own C function
2. **Adjust iterations**: Change the loop count to suit your function's complexity
3. **Run `make test-qemu`**: See cycle counts immediately

This is faster than modifying assignment code and perfect for:
- Comparing different C implementations
- Measuring cycle counts before writing Jasmin
- Testing optimization ideas
- Understanding performance characteristics

## Getting Help

If you run into issues:

1. Make sure your board is connected via USB
2. Check that you're in the `playground1-bench` directory
3. Try `make clean` and rebuild
4. See `../common/TESTING_GUIDE.md` for more troubleshooting tips

## Additional Commands

- `make help-playground` - Show all available commands
- `make monitor` - Open a serial monitor to see raw UART output
- `make clean` - Clean build files
