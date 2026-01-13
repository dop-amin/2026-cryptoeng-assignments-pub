"""
ChaCha20-Specific Test Protocol

Provides test methods for ChaCha20 algorithm components and operations.
Inherits from CommandProtocol to leverage common command handling logic.

This module contains all ChaCha20-specific test commands, keeping the
common testing infrastructure generic and reusable.
"""

import os
import sys
from typing import Optional

try:
    from common.testing.command_protocol import CommandProtocol
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from common.testing.command_protocol import CommandProtocol


class ChaCha20Protocol(CommandProtocol):
    """
    Test protocol for ChaCha20 cipher implementation.

    Provides methods to test:
    - Primitive operations (quarterround)
    - Block function
    - Component functions (keysetup, ivsetup, encrypt_bytes)
    - Round functions (column, diagonal)
    - Keystream generation
    - Performance benchmarks
    """

    def test_quarterround(self, a: int, b: int, c: int, d: int) -> Optional[bytes]:
        """
        Test ChaCha20 quarterround primitive.

        Args:
            a, b, c, d: Four 32-bit unsigned integers

        Returns:
            16 bytes containing four 32-bit results (little-endian) or None on error
        """
        input_data = (
            a.to_bytes(4, "little")
            + b.to_bytes(4, "little")
            + c.to_bytes(4, "little")
            + d.to_bytes(4, "little")
        )
        command = f"TEST_PRIMITIVE 3 {input_data.hex()}"
        return self._send_test_command(command, expected_length=16)

    def test_block(self, input_state: bytes) -> Optional[bytes]:
        """
        Test ChaCha20 block function (20 rounds).

        Args:
            input_state: 64-byte state array (16 x 32-bit words)

        Returns:
            64-byte keystream block or None on error
        """
        if len(input_state) != 64:
            raise ValueError("Input state must be 64 bytes")

        command = f"TEST_FULL {input_state.hex()}"
        return self._send_test_command(command, expected_length=64)

    def test_keystream(self, key: bytes, nonce: bytes, length: int) -> Optional[bytes]:
        """
        Test ChaCha20 IETF keystream generation.

        Generates a keystream of specified length using ChaCha20-IETF variant
        (32-byte key, 12-byte nonce, 32-bit counter starting at 0).

        Args:
            key: 32-byte key
            nonce: 12-byte nonce (IETF variant)
            length: Number of keystream bytes to generate (1-256)

        Returns:
            Keystream bytes or None on error
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")
        if len(nonce) != 12:
            raise ValueError("Nonce must be 12 bytes (IETF variant)")
        if length <= 0 or length > 256:
            raise ValueError("Length must be between 1 and 256")

        command = f"TEST_KEYSTREAM {key.hex()} {nonce.hex()} {length}"
        return self._send_test_command(command, expected_length=length)

    def test_keysetup(self, key: bytes) -> Optional[bytes]:
        """
        Test ChaCha20 keysetup component function.

        Sets up the initial state with constants and key, leaving counter
        and nonce positions zeroed.

        Args:
            key: 32-byte key

        Returns:
            64-byte state array or None on error
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")

        command = f"TEST_KEYSETUP {key.hex()}"
        return self._send_test_command(command, expected_length=64)

    def test_ivsetup(self, state: bytes, nonce: bytes) -> Optional[bytes]:
        """
        Test ChaCha20 IETF IV setup component function.

        Sets the counter to 0 and nonce in the state array.

        Args:
            state: 64-byte state array (from keysetup)
            nonce: 12-byte nonce (IETF variant)

        Returns:
            64-byte updated state array or None on error
        """
        if len(state) != 64:
            raise ValueError("State must be 64 bytes")
        if len(nonce) != 12:
            raise ValueError("Nonce must be 12 bytes (IETF variant)")

        command = f"TEST_IVSETUP {state.hex()} {nonce.hex()}"
        return self._send_test_command(command, expected_length=64)

    def test_encrypt_bytes(self, state: bytes, length: int) -> Optional[bytes]:
        """
        Test ChaCha20 encrypt_bytes component function.

        Generates keystream bytes from the current state, incrementing
        the counter for each block.

        Args:
            state: 64-byte state array
            length: Number of keystream bytes to generate (1-256)

        Returns:
            Keystream bytes or None on error
        """
        if len(state) != 64:
            raise ValueError("State must be 64 bytes")
        if length <= 0 or length > 256:
            raise ValueError("Length must be between 1 and 256")

        command = f"TEST_ENCRYPT {state.hex()} {length}"
        return self._send_test_command(command, expected_length=length)

    def test_column_round(self, state: bytes) -> Optional[bytes]:
        """
        Test ChaCha20 column round function.

        Applies quarterround to all four columns of the state.

        Args:
            state: 64-byte state array

        Returns:
            64-byte updated state array or None on error
        """
        if len(state) != 64:
            raise ValueError("State must be 64 bytes")

        command = f"TEST_COLUMN_ROUND {state.hex()}"
        return self._send_test_command(command, expected_length=64)

    def test_diagonal_round(self, state: bytes) -> Optional[bytes]:
        """
        Test ChaCha20 diagonal round function.

        Applies quarterround to all four diagonals of the state.

        Args:
            state: 64-byte state array

        Returns:
            64-byte updated state array or None on error
        """
        if len(state) != 64:
            raise ValueError("State must be 64 bytes")

        command = f"TEST_DIAGONAL_ROUND {state.hex()}"
        return self._send_test_command(command, expected_length=64)

    def benchmark_block(self, iterations: int) -> Optional[int]:
        """
        Benchmark ChaCha20 block function performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            Total CPU cycles or None on error
        """
        command = f"BENCHMARK {iterations}"
        return self._send_benchmark_command(command)

    def benchmark_keystream(self, iterations: int, length: int) -> Optional[int]:
        """
        Benchmark ChaCha20 IETF keystream generation performance.

        Args:
            iterations: Number of iterations to run
            length: Number of keystream bytes per iteration

        Returns:
            Total CPU cycles or None on error
        """
        command = f"BENCHMARK_KEYSTREAM {iterations} {length}"
        return self._send_benchmark_command(command)

    def benchmark_quarterround(self, iterations: int) -> Optional[int]:
        """
        Benchmark quarterround function performance.

        Args:
            iterations: Number of iterations to run

        Returns:
            Total CPU cycles or None on error
        """
        command = f"BENCHMARK_QUARTERROUND {iterations}"
        return self._send_benchmark_command(command)
