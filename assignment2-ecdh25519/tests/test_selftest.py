"""Test scalar multiplication implementation of Ecdh25519 curve."""

import os
import sys

try:
    from reference.smult import crypto_scalarmult, crypto_scalarmult_base
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    ASSIGNMENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if ASSIGNMENT_ROOT not in sys.path:
        sys.path.insert(0, ASSIGNMENT_ROOT)
    from reference.smult import crypto_scalarmult, crypto_scalarmult_base

SK0 = bytes(
    [
        0xB1,
        0x7A,
        0xA0,
        0x76,
        0x93,
        0xD7,
        0x8D,
        0x70,
        0xFB,
        0x44,
        0x3A,
        0x5B,
        0xF1,
        0xC6,
        0x90,
        0xE2,
        0xC3,
        0x79,
        0x39,
        0x6F,
        0x56,
        0xAC,
        0xC5,
        0x5F,
        0xB5,
        0xFC,
        0x1C,
        0xC5,
        0x58,
        0xA2,
        0xD9,
        0x85,
    ]
)

SK1 = bytes(
    [
        0xBA,
        0xDB,
        0xC5,
        0x8F,
        0xC7,
        0x97,
        0x18,
        0xC4,
        0x78,
        0x32,
        0x13,
        0x0A,
        0x94,
        0x2C,
        0x80,
        0xDB,
        0x77,
        0x84,
        0x34,
        0xDC,
        0x04,
        0xCE,
        0x19,
        0x16,
        0xDA,
        0xE4,
        0x16,
        0x36,
        0x06,
        0xCA,
        0xDD,
        0x30,
    ]
)

CMPPK0 = bytes(
    [
        0x54,
        0xBA,
        0x6E,
        0xF0,
        0x36,
        0xA4,
        0x11,
        0xC9,
        0xA5,
        0x29,
        0x4D,
        0xB9,
        0xBE,
        0x38,
        0x9F,
        0xBC,
        0x2C,
        0xE1,
        0x90,
        0xA1,
        0xF2,
        0x20,
        0x09,
        0xD1,
        0xD7,
        0x8F,
        0x9B,
        0x56,
        0xC0,
        0xA2,
        0x14,
        0x62,
    ]
)

CMPPK1 = bytes(
    [
        0x82,
        0xE3,
        0x9B,
        0x97,
        0xD6,
        0x73,
        0xB7,
        0x72,
        0xDF,
        0x34,
        0x79,
        0xBF,
        0xED,
        0x94,
        0x31,
        0x7F,
        0x59,
        0x83,
        0x48,
        0xD1,
        0xA5,
        0x29,
        0x14,
        0xFD,
        0xF7,
        0x67,
        0x7C,
        0x17,
        0x46,
        0xD0,
        0x59,
        0x6A,
    ]
)

CMPSS = bytes(
    [
        0xFE,
        0xB3,
        0xDD,
        0x58,
        0x73,
        0x4B,
        0x42,
        0xC8,
        0x86,
        0x0D,
        0x2B,
        0xB7,
        0x08,
        0xC0,
        0xAE,
        0x14,
        0x7A,
        0x21,
        0xDF,
        0x42,
        0xF8,
        0xC9,
        0xAF,
        0x4E,
        0x3C,
        0xC4,
        0xBE,
        0x8C,
        0x56,
        0xFC,
        0x88,
        0x3D,
    ]
)

SK = [SK0, SK1]
PK = [CMPPK0, CMPPK1]


def main() -> None:
    """Check scalar multiplication Python implementation."""
    # Compute the public keys as: p = sk*B.
    pk0 = crypto_scalarmult_base(SK0)
    pk1 = crypto_scalarmult_base(SK1)

    # Compute shared keys.
    ss0 = crypto_scalarmult(SK0, pk1)  # ss0 = sk0*sk1*B
    ss1 = crypto_scalarmult(SK1, pk0)  # ss1 = sk1*sk0*B

    # Check correctness.
    assert ss0 == ss1, "Shared keys do not match"
    assert pk0 == CMPPK0, "pk0 does not match CMPPK0"
    assert pk1 == CMPPK1, "pk1 does not match CMPPK1"
    assert ss0 == CMPSS, "Shared key does not match CMPSS"

    print("PASSED!")
    return 0


if __name__ == "__main__":
    main()
