# Assignment 0 — Summing up 1000 integers

In this assignment you will write a small program that takes an array of 32-bit
integers and the length of this array as its input and sums these integers up.
Doing so, you will start writing a simple Jasmin function that is not tuned for
performance. After succeeding to do so, you will try to provide a second version
of this function that will be as fast as possible. 

## Learning Objectives

- Establish and test connection to our development board.
- Familiarize yourself with the Jasmin language. 
- Explore performance characteristics of the Arm Cortex-M4 CPU.
- Outperform the C implementation in the benchmarks (hint: you can be more than
  2x faster)

## Files You Will Modify

| Path | Purpose |
| --- | --- |
| `src/sum.jazz` | Jasmin implementation; you provide the summation routines here. |

## Other Files of Interest
| Path | Purpose |
| --- | --- |
| `src/sum_wrapper.h` | Function declarations for exported Jasmin functions. |
| `tests/test_sum.py` | Test harness (mainly read-only; may modify for debugging). |
| `src/sum_c.c` | Simple summation routine written in C (read-only). |
| `src/main.c` | Device firmware (mainly read-only; may modify for debugging). |

Shared infrastructure lives in `../common/`; you should not need to modify it.

Export the required entry points so that the firmware can call into your Jasmin
code:

- `sum_jasmin`  
- `sum_jasmin_fast`

## Deliverables

Your submission should include:

- Updated `src/sum.jazz` with a correct implementation. If your implementation
  does not fully work, please state which parts are expected to fail. 
- Cycle counts for your implementation. 

## Working on the Assignment
Your interaction with the assignment consists of editing the above-mentioned
source file as well as executing different tests and benchmarks through the
Makefile. *Please read the following instructions carefully, as the operation
will be highly similar for all the following assignments*. 

You can always obtain help on the available tests and benchmarks you can run by executing:

```
make help-assignment
```

### Verifying the Setup
To make sure the board is connected successfully, the toolchain is properly set
up, and that you are able to receive messages over UART from the board, run the
following command:

```
make test-board-hello
```

Running this command will execute multiple steps in a row:
- Build device firmware: This comprises an interface to send and receive UART
  messages and to call into the Jasmin functions you will write.
- Flash the firmware onto the device.
- Run a Python script on your computer, that initiates the communication with
  the firmware on the target device. This script will send a "Hello
  World"-message to the board, and the board will reply with a greeting as well
  if everything works properly.  

### Testing Your Implementation
In order to test your implementation, we provide two different Makefile targets.
These tests will also build the firmware (including your Jasmin source code),
and execute test cases to verify correct operation. 

The most important command is
```
make test-board
```
which will run the code on your development board.

An alternative command in case you are having issues with the physical setup using the development board or do not have it at hand invokes an emulator (qemu):
```
make test-qemu
```

Both of the commands can be used for testing the functionality of your code and
will initially fail as no correct solution is implemented within the sum.jazz
file (your task).

However, mind that some types of memory bugs may cause crashes/no replies from
the board, while not causing issues using qemu. 

### Benchmarking Your Implementation

In order to obtain information on the performance of your implementation, we
provide a way to run a benchmark that will yield cycle counts for all three implementations of the sum functions individually. 

```
make bench-board
```

Some notes on benchmarks on the Arm Cortex-M4:
- Counting the cycles in your source code by hand will not yield the exact
  result you obtain using the benchmark. This is because there are several
  overheads: Calling into the function, returning from the function, reading the
  cycle counter, ...
- Do not worry if your un-optimized Jasmin implementation is slower than the C
  implementation provided by us. The compiler is surprisingly good at optimizing
  common tasks -- but there is a lot of potential to uncover from inside Jasmin. 

### Implementation Done?

Check the completeness and correctness of your submission using:

```
make check-submission
```

## Resources

- C implementation in `src/sum_c.c`
- `common/TESTING_GUIDE.md` — instructions for running the test suite on
  hardware and QEMU.  
- Jasmin documentation (see repository root README) — language reference and
  tooling tips.
