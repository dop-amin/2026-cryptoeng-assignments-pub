# Assignment 2 — ECDH with Curve25519

In this assignment you implement the scalar multiplication operation for
elliptic curve Diffie-Hellman (ECDH) key exchange using Ed25519 in Jasmin. The
goal is to gain experience with elliptic curve cryptography and constant-time
implementations to resist side-channel attacks.

## Learning Objectives

- Implement **non constant-time** scalar multiplication using **double-and-add**
- Implement **constant-time** scalar multiplication using **double-and-add-always**
- Verify correctness against the Python reference implementation

## Files You Will Modify

| Path | Purpose |
| --- | --- |
| `src/smult.jazz` | Scalar multiplication with double-and-add here. |
| `src/smult_ct.jazz` | Constant-time scalar multiplication with double-and-add-always here. |

## Other Files of Interest

| Path | Purpose |
| --- | --- |
| `src/smult_wrapper.h` | Function declarations for exported Jasmin functions. |
| `src/fe25519.jazz` | Field arithmetic (provided); operations in F_{2^255-19}. |
| `src/ge25519.jazz` | Group operations (provided); point addition and doubling on the twisted Edwards curve. |
| `tests/test_smult.py` | Test harness (mainly read-only; may modify for debugging). |
| `src/main.c` | Device firmware (mainly read-only; may modify for debugging). |
| `reference/` | Python model and helper utilities - use for understanding and cross-checking results. |

Shared infrastructure lives in `../common/`; you should not need to modify it.

## Deliverables

Your submission should include:

- Updated `src/smult.jazz` with a correct implementation. If your
  implementation does not fully work, please state which parts are expected to
  fail.
- A constant-time implementation in `src/smult_ct.jazz` that resists
  timing-based side-channel attacks (recommended).
- Annotated `crypto_scalarmult` and `crypto_scalarmult_base` for running
  Jasmin's constant-time checker.
- Cycle counts for your implementation.

## Working on the Assignment

The structure closely follows the one for assignment1-chacha20.

Your final goal is to implement the scalar multiplication operation inside the
following `if` branch of the function `crypto_scalarmult` in
`src/smult{_ct}.jazz`:
```rust
if (ret != -1) {
}
```

To check correctness of your implementation, do:
```bash
# Testing smult.jazz
make TARGET=smult CT=no test-{board,qemu}
# Testing smult_ct.jazz
make TARGET=smult CT=no test-{board,qemu}
```

Then you need to annotate the arguments of the functions `crypto_scalarmult` and
`crypto_scalarmult_base` in `src/smult{_ct}.jazz` as `public` or `secret` to run
the Jasmin's constant-time checker. Please refer to the Jasmin's documentation
on the CT checker
[here](https://jasmin-lang.readthedocs.io/en/stable/tools/ct.html#type-system).

To run the CT checker, do:
```bash
jasmin-ct --arch -arm-m4 FILENAME.jazz
```

## Resources

- Peter's course:
  https://cryptojedi.org/peter/teaching/engineering-crypto-software-2025.shtml
- RFC 7748 - Elliptic Curves for Security (X25519 and Ed25519)
- RFC 8032, Section 5 - Ed25519 specification
- `reference/smult.py` - pure Python scalar multiplication (non-constant-time
  reference)
- `reference/fe25519.py` - pure Python field arithmetic implementation
- `reference/ge25519.py` - pure Python group operations
- `common/TESTING_GUIDE.md` - instructions for running the test suite on
  hardware and QEMU
- [Jasmin documentation](https://jasmin-lang.readthedocs.io/en/stable/index.html)
- Course slides on constant-time programming and side-channel attacks