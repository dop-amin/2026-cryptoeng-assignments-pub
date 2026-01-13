# Assignment 1 — ChaCha20 Stream Cipher

In this assignment you implement the IETF ChaCha20 stream cipher (RFC 8439) in
Jasmin and validate it on the course firmware stack. The goal is to gain
experience with ARX ciphers, the Jasmin language, and the testing harness used
throughout the course.

## Learning Objectives

- Translate the ChaCha20 specification into Jasmin 
- Structure code into reusable building blocks (it is your freedom to chose
  how).
- Verify correctness against the Python reference implementation and official
  RFC vectors.

## Files You Will Modify

| Path | Purpose |
| --- | --- |
| `src/chacha20.jazz` | Jasmin implementation; you provide the cipher routines here. |

## Other Files of Interest
| Path | Purpose |
| --- | --- |
| `src/chacha20_wrapper.h` | Function declarations for exported Jasmin functions. |
| `tests/test_chacha20.py` | Test harness (mainly read-only; may modify for debugging). |
| `src/main.c` | Device firmware (mainly read-only; may modify for debugging). |
| `reference/` | Python model and helper utilities - use for understanding and cross-checking results. |


Shared infrastructure lives in `../common/`; you should not need to modify it.

## Deliverables

Your submission should include:

- Updated `src/chacha20.jazz` with a correct, constant-time implementation. If
  your implementation does not fully work, please state which parts are expected
  to fail. 
- Cycle counts for your implementation. 

The factor that determines whether we count your solution as working is if the
test for `crypto_stream_chacha20_ietf` passes.

## Working on the Assignment

The structure closely follows the one for assignment0.

Your final goal is to implement 
```rust
// Export wrapper for crypto_stream_chacha20_ietf (highest-level API)
// ct_ptr: pointer to output ciphertext/input plaintext
// nonce_ptr: pointer to 12-byte nonce
// sk_ptr: pointer to 32-byte secret key
// ct_len: length of output in bytes
export fn crypto_stream_chacha20_ietf(reg u32 ct_ptr, reg ptr u8[12] nonce_ptr, reg ptr u8[32] sk_ptr, reg u32 ct_len)
```

On the way, you may implement the other functions we have written tests for in
`chacha20.jazz` as possible intermediate steps. However, you are free to choose
not to do so or only do so for some. This can be potentially useful for
performance optimization.

## Resources

- RFC 8439, Sections 2.1-2.4 - authoritative specification and reference
  vectors.  
- `reference/chacha20_primitives.py` — pure Python version of each round; useful
  for step-by-step comparison.  
- `common/TESTING_GUIDE.md` — instructions for running the test suite on
  hardware and QEMU.  
- Jasmin documentation (see repository root README) — language reference and
  tooling tips.
