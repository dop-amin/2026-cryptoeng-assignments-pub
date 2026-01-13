"""
ChaCha20 Test Vectors from RFC 8439

These test vectors are the official ones from RFC 8439 and can be used
to verify correctness of implementations.
"""

from typing import Dict, Any


# Test vector 1: Quarter round
QUARTERROUND_TEST = {
    "input": (0x11111111, 0x01020304, 0x9B8D6F43, 0x01234567),
    "output": (0xEA2A92F4, 0xCB1CF8CE, 0x4581472E, 0x5881C4BB),
    "description": "RFC 8439 Section 2.1.1 - Quarter Round Test",
}

# Test vector 2: ChaCha20 Block Function
BLOCK_TEST = {
    "key": bytes(
        [
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0x0C,
            0x0D,
            0x0E,
            0x0F,
            0x10,
            0x11,
            0x12,
            0x13,
            0x14,
            0x15,
            0x16,
            0x17,
            0x18,
            0x19,
            0x1A,
            0x1B,
            0x1C,
            0x1D,
            0x1E,
            0x1F,
        ]
    ),
    "nonce": bytes(
        [0x00, 0x00, 0x00, 0x09, 0x00, 0x00, 0x00, 0x4A, 0x00, 0x00, 0x00, 0x00]
    ),
    "counter": 1,
    "keystream": bytes(
        [
            0x10,
            0xF1,
            0xE7,
            0xE4,
            0xD1,
            0x3B,
            0x59,
            0x15,
            0x50,
            0x0F,
            0xDD,
            0x1F,
            0xA3,
            0x20,
            0x71,
            0xC4,
            0xC7,
            0xD1,
            0xF4,
            0xC7,
            0x33,
            0xC0,
            0x68,
            0x03,
            0x04,
            0x22,
            0xAA,
            0x9A,
            0xC3,
            0xD4,
            0x6C,
            0x4E,
            0xD2,
            0x82,
            0x64,
            0x46,
            0x07,
            0x9F,
            0xAA,
            0x09,
            0x14,
            0xC2,
            0xD7,
            0x05,
            0xD9,
            0x8B,
            0x02,
            0xA2,
            0xB5,
            0x12,
            0x9C,
            0xD1,
            0xDE,
            0x16,
            0x4E,
            0xB9,
            0xCB,
            0xD0,
            0x83,
            0xE8,
            0xA2,
            0x50,
            0x3C,
            0x4E,
        ]
    ),
    "description": "RFC 8439 Section 2.3.2 - ChaCha20 Block Test",
}

# Test vector 3: ChaCha20 Encryption
ENCRYPTION_TEST = {
    "key": bytes(
        [
            0x00,
            0x01,
            0x02,
            0x03,
            0x04,
            0x05,
            0x06,
            0x07,
            0x08,
            0x09,
            0x0A,
            0x0B,
            0x0C,
            0x0D,
            0x0E,
            0x0F,
            0x10,
            0x11,
            0x12,
            0x13,
            0x14,
            0x15,
            0x16,
            0x17,
            0x18,
            0x19,
            0x1A,
            0x1B,
            0x1C,
            0x1D,
            0x1E,
            0x1F,
        ]
    ),
    "nonce": bytes(
        [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x4A, 0x00, 0x00, 0x00, 0x00]
    ),
    "counter": 1,
    "plaintext": (
        b"Ladies and Gentlemen of the class of '99: If I could offer "
        b"you only one tip for the future, sunscreen would be it."
    ),
    "ciphertext": bytes(
        [
            0x6E,
            0x2E,
            0x35,
            0x9A,
            0x25,
            0x68,
            0xF9,
            0x80,
            0x41,
            0xBA,
            0x07,
            0x28,
            0xDD,
            0x0D,
            0x69,
            0x81,
            0xE9,
            0x7E,
            0x7A,
            0xEC,
            0x1D,
            0x43,
            0x60,
            0xC2,
            0x0A,
            0x27,
            0xAF,
            0xCC,
            0xFD,
            0x9F,
            0xAE,
            0x0B,
            0xF9,
            0x1B,
            0x65,
            0xC5,
            0x52,
            0x47,
            0x33,
            0xAB,
            0x8F,
            0x59,
            0x3D,
            0xAB,
            0xCD,
            0x62,
            0xB3,
            0x57,
            0x16,
            0x39,
            0xD6,
            0x24,
            0xE6,
            0x51,
            0x52,
            0xAB,
            0x8F,
            0x53,
            0x0C,
            0x35,
            0x9F,
            0x08,
            0x61,
            0xD8,
            0x07,
            0xCA,
            0x0D,
            0xBF,
            0x50,
            0x0D,
            0x6A,
            0x61,
            0x56,
            0xA3,
            0x8E,
            0x08,
            0x8A,
            0x22,
            0xB6,
            0x5E,
            0x52,
            0xBC,
            0x51,
            0x4D,
            0x16,
            0xCC,
            0xF8,
            0x06,
            0x81,
            0x8C,
            0xE9,
            0x1A,
            0xB7,
            0x79,
            0x37,
            0x36,
            0x5A,
            0xF9,
            0x0B,
            0xBF,
            0x74,
            0xA3,
            0x5B,
            0xE6,
            0xB4,
            0x0B,
            0x8E,
            0xED,
            0xF2,
            0x78,
            0x5E,
            0x42,
            0x87,
            0x4D,
        ]
    ),
    "description": "RFC 8439 Section 2.4.2 - ChaCha20 Encryption Test",
}

# All test vectors
ALL_TESTS = [QUARTERROUND_TEST, BLOCK_TEST, ENCRYPTION_TEST]


def get_test_vector(name: str) -> Dict[str, Any]:
    """
    Get a specific test vector by name.

    Args:
        name: Test name ('quarterround', 'block', 'encryption')

    Returns:
        Test vector dictionary
    """
    vectors = {
        "quarterround": QUARTERROUND_TEST,
        "block": BLOCK_TEST,
        "encryption": ENCRYPTION_TEST,
    }

    if name not in vectors:
        raise ValueError(f"Unknown test vector: {name}")

    return vectors[name]


def print_test_vector(test: Dict[str, Any]) -> None:
    """
    Print a test vector in a readable format.

    Args:
        test: Test vector dictionary
    """
    print("=" * 60)
    print(test.get("description", "Test Vector"))
    print("=" * 60)

    for key, value in test.items():
        if key == "description":
            continue

        if isinstance(value, bytes):
            print(f"{key}:")
            print(f"  {value.hex()}")
        elif isinstance(value, tuple):
            print(f"{key}:")
            for i, v in enumerate(value):
                print(f"  [{i}] = 0x{v:08x}")
        else:
            print(f"{key}: {value}")

    print()


def print_all_test_vectors() -> None:
    """Print all test vectors."""
    for test in ALL_TESTS:
        print_test_vector(test)


if __name__ == "__main__":
    print_all_test_vectors()
