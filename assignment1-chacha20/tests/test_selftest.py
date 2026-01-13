#!/usr/bin/env python3
"""
Test the ChaCha20 reference implementation against RFC 8439 test vectors.

This ensures our Python reference implementation is correct.
"""

import os
import random
import sys
from tqdm import tqdm

try:
    from reference.chacha20_primitives import quarterround
    from reference.chacha20 import ChaCha20
    from reference.test_vectors import BLOCK_TEST, ENCRYPTION_TEST, QUARTERROUND_TEST
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    ASSIGNMENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if ASSIGNMENT_ROOT not in sys.path:
        sys.path.insert(0, ASSIGNMENT_ROOT)
    from reference.chacha20_primitives import quarterround
    from reference.chacha20 import ChaCha20
    from reference.test_vectors import BLOCK_TEST, ENCRYPTION_TEST, QUARTERROUND_TEST


def test_quarterround():
    """Test quarter round against RFC 8439 Section 2.1.1."""
    print("Testing quarter round...")

    a, b, c, d = QUARTERROUND_TEST["input"]
    expected_a, expected_b, expected_c, expected_d = QUARTERROUND_TEST["output"]

    result_a, result_b, result_c, result_d = quarterround(a, b, c, d)

    assert (
        result_a == expected_a
    ), f"Quarter round a mismatch: {result_a:08x} != {expected_a:08x}"
    assert (
        result_b == expected_b
    ), f"Quarter round b mismatch: {result_b:08x} != {expected_b:08x}"
    assert (
        result_c == expected_c
    ), f"Quarter round c mismatch: {result_c:08x} != {expected_c:08x}"
    assert (
        result_d == expected_d
    ), f"Quarter round d mismatch: {result_d:08x} != {expected_d:08x}"

    print("  PASS: Quarter round test")


def test_chacha20_block():
    """Test ChaCha20 block function against RFC 8439 Section 2.3.2."""
    print("Testing ChaCha20 block function...")

    key = BLOCK_TEST["key"]
    nonce = BLOCK_TEST["nonce"]
    counter = BLOCK_TEST["counter"]
    expected_keystream = BLOCK_TEST["keystream"]

    cipher = ChaCha20(key, nonce, counter)
    keystream = cipher.chacha20_block(counter)

    assert keystream == expected_keystream, (
        "ChaCha20 block mismatch:\n"
        f"Got:      {keystream.hex()}\n"
        f"Expected: {expected_keystream.hex()}"
    )

    print("  PASS: ChaCha20 block test")
    print(f"    Keystream (first 32 bytes): {keystream[:32].hex()}")


def test_chacha20_encryption():
    """Test ChaCha20 encryption against RFC 8439 Section 2.4.2."""
    print("Testing ChaCha20 encryption...")

    key = ENCRYPTION_TEST["key"]
    nonce = ENCRYPTION_TEST["nonce"]
    counter = ENCRYPTION_TEST["counter"]
    plaintext = ENCRYPTION_TEST["plaintext"]
    expected_ciphertext = ENCRYPTION_TEST["ciphertext"]

    cipher = ChaCha20(key, nonce, counter)
    ciphertext = cipher.encrypt(plaintext)

    assert ciphertext == expected_ciphertext, (
        "ChaCha20 encryption mismatch:\n"
        f"Got:      {ciphertext.hex()}\n"
        f"Expected: {expected_ciphertext.hex()}"
    )

    print("  PASS: ChaCha20 encryption test")
    print(f"    Plaintext:  {plaintext[:40]}...")
    print(f"    Ciphertext (first 32 bytes): {ciphertext[:32].hex()}")

    # Test decryption
    decrypted = cipher.decrypt(ciphertext)
    assert decrypted == plaintext, "Decryption failed"
    print("  PASS: ChaCha20 decryption verified")


def test_pycryptodome_compatibility(num_tests: int = 10000):
    """Test against PyCryptodome library if available."""
    try:
        from Crypto.Cipher import ChaCha20 as CryptoChaCha20
    except ImportError:
        print("  SKIP: PyCryptodome not installed, skipping compatibility test")
        return

    print("Testing against PyCryptodome library...")

    for _ in tqdm(range(num_tests)):
        # Use a simple test with counter=0 since PyCryptodome starts at 0
        key = bytes([random.randint(0, 255) for _ in range(32)])
        nonce = bytes([random.randint(0, 255) for _ in range(12)])
        plaintext = bytes([random.randint(0, 255) for _ in range(32)])

        # Our implementation with counter=0
        our_cipher = ChaCha20(key, nonce, counter=0)
        our_ciphertext = our_cipher.encrypt(plaintext)

        # PyCryptodome - starts at counter 0 by default
        pycrypto_cipher = CryptoChaCha20.new(key=key, nonce=nonce)
        pycrypto_ciphertext = pycrypto_cipher.encrypt(plaintext)

        assert our_ciphertext == pycrypto_ciphertext, (
            f"Mismatch with PyCryptodome:\nOurs:  {our_ciphertext.hex()}"
            f"\nTheirs: {pycrypto_ciphertext.hex()}"
        )

    print("  PASS: Matches PyCryptodome implementation")


def main():
    print("=" * 60)
    print("ChaCha20 Reference Implementation Tests")
    print("=" * 60)
    print()

    try:
        test_quarterround()
        print()

        test_chacha20_block()
        print()

        test_chacha20_encryption()
        print()

        test_pycryptodome_compatibility()
        print()

        print("=" * 60)
        print("PASS: All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"FAIL: Test failed: {e}")
        print("=" * 60)
        return 1
    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
