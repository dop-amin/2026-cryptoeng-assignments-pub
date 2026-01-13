# Playground 2 - Jasmin Integration Demo

This is a minimal demo to help you quickly test Jasmin code. It shows how to integrate a Jasmin function into your firmware and benchmark it. Use this as a starting point to experiment with your own Jasmin functions.

## What This Demo Does

The board firmware calls a Jasmin function (`increment_jasmin`) in a loop, measures the total cycles taken, and prints the results. This is the simplest possible Jasmin integration - perfect for testing small code snippets.

## Learning Objectives

- Understand how to write a simple Jasmin function
- Learn how to integrate Jasmin code with C firmware
- See the Jasmin compilation process in action
- Quickly test and benchmark your own Jasmin code

## Files in This Playground

| Path | Description |
| --- | --- |
| `src/myjasmin.jazz` | Simple Jasmin function - edit this to test your own code |
| `src/myjasmin_wrapper.h` | Header file declaring the Jasmin function for C |
| `src/main.c` | Firmware that calls the Jasmin function and benchmarks it |
| `tests/test_jasmin.py` | Python script that reads and displays the benchmark output |
| `Makefile` | Build system that compiles Jasmin and links with C |

## Running the Demo

### Quick Start

```bash
make test-qemu
```

This builds everything and tests in QEMU (no hardware needed).

### Step 1: Build and Flash (for Board)

First, build the firmware (this will compile the Jasmin code):

```bash
make
```

You'll see the Jasmin compiler (`jasminc`) convert `myjasmin.jazz` to `myjasmin.s` assembly.

Then flash to your board:

```bash
make flash
```

### Step 2: Test on Board

Run the test to see the benchmark output:

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
Playground 2: Jasmin Demo
====================================

Jasmin increment called 1000 times
Result: 1000
Took 5000 cycles (5 per iteration)

============================================================
PASS: Successfully received output from board!
============================================================
```

### Alternative: Test with QEMU

You can also test with QEMU emulation:

```bash
make test-qemu
```

## Understanding the Code

### The Jasmin Function (`src/myjasmin.jazz`)

```jasmin
export fn increment_jasmin(reg u32 input) -> reg u32 {
    reg u32 result;
    result = input;
    result += 1;
    return result;
}
```

This is a minimal Jasmin function that:
- Takes a 32-bit unsigned integer as input
- Increments it by 1
- Returns the result
- Uses the `export` keyword to make it callable from C

### The C Integration (`src/main.c`)

The C code:
1. Includes `myjasmin_wrapper.h` which declares the Jasmin function
2. Calls `increment_jasmin()` just like any C function
3. Benchmarks the performance using `hal_get_time()`

### The Build Process

The Makefile shows the compilation steps:
1. `jasminc` compiles `myjasmin.jazz` to `myjasmin.s` (ARM assembly)
2. The ARM compiler assembles `myjasmin.s` to `myjasmin.o`
3. The linker combines everything into the final `.elf` file

## Using This as a Testing Ground

This playground is designed for quick experimentation:

1. **Edit `src/myjasmin.jazz`**: Replace the increment function with your own Jasmin code
2. **Update `src/myjasmin_wrapper.h`**: Adjust the function signature if needed
3. **Modify `src/main.c`**: Change how you call and test your function
4. **Run `make test-qemu`**: See your results immediately

This is faster than modifying assignment code and perfect for:
- Testing small Jasmin snippets
- Debugging register usage
- Measuring cycle counts of different approaches
- Learning Jasmin syntax and semantics

## Getting Help

If you run into issues:

1. Make sure the Jasmin compiler is installed
2. Check that you're in the `playground2-jasmin` directory
3. Try `make clean` and rebuild
4. See `../common/TESTING_GUIDE.md` for more troubleshooting tips

## Additional Commands

- `make help-playground` - Show all available commands
- `make monitor` - Open a serial monitor to see raw UART output
- `make clean` - Clean build files and generated assembly
