"""
ChaCha20 Reference Implementation Package

This package provides complete, correct implementations of ChaCha20
for students to use as reference when developing their Jasmin implementations.
"""

from .chacha20 import ChaCha20, chacha20_encrypt, chacha20_decrypt
from .chacha20_primitives import (
    add32,
    xor32,
    rotl32,
    quarterround,
    quarterround_line,
    bytes_to_u32_le,
    u32_to_bytes_le,
    u32_array_to_bytes,
    bytes_to_u32_array,
)
from .test_vectors import (
    QUARTERROUND_TEST,
    BLOCK_TEST,
    ENCRYPTION_TEST,
    get_test_vector,
    print_test_vector,
)

__all__ = [
    # Main cipher
    "ChaCha20",
    "chacha20_encrypt",
    "chacha20_decrypt",
    # Primitives
    "add32",
    "xor32",
    "rotl32",
    "quarterround",
    "quarterround_line",
    "bytes_to_u32_le",
    "u32_to_bytes_le",
    "u32_array_to_bytes",
    "bytes_to_u32_array",
    # Test vectors
    "QUARTERROUND_TEST",
    "BLOCK_TEST",
    "ENCRYPTION_TEST",
    "get_test_vector",
    "print_test_vector",
    # Debug tools
    "ChaCha20Debugger",
    "format_state_matrix",
    "print_state",
    "compare_states",
    "hex_dump",
    "compare_hex",
]

__version__ = "1.0.0"
