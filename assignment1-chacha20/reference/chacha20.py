"""
ChaCha20 Stream Cipher - Reference Implementation

This module provides a complete, correct implementation of ChaCha20
according to RFC 8439. Students can use this as a reference to test
their Jasmin implementations.

ChaCha20 is a stream cipher that generates a keystream from a 256-bit key,
a 96-bit nonce, and a 32-bit counter.
"""

from typing import List
from .chacha20_primitives import (
    add32,
    u32_array_to_bytes,
    bytes_to_u32_array,
    column_round,
    diagonal_round,
)


class ChaCha20:
    """ChaCha20 stream cipher."""

    # ChaCha20 constants "expand 32-byte k"
    CONSTANTS = [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]

    def __init__(self, key: bytes, nonce: bytes, counter: int = 0):
        """
        Initialize ChaCha20 cipher.

        Args:
            key: 256-bit (32 bytes) key
            nonce: 96-bit (12 bytes) nonce
            counter: Initial counter value (default: 0)

        Raises:
            ValueError: If key or nonce has incorrect length
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")
        if len(nonce) != 12:
            raise ValueError("Nonce must be 12 bytes")

        self.key = key
        self.nonce = nonce
        self.counter = counter

    def _setup_state(self, counter: int) -> List[int]:
        """
        Set up the initial ChaCha20 state.

        State layout (16 words):
        cccc  cccc  cccc  cccc
        kkkk  kkkk  kkkk  kkkk
        kkkk  kkkk  kkkk  kkkk
        bbbb  nnnn  nnnn  nnnn

        Where:
        c = constant ("expand 32-byte k")
        k = key
        b = block counter
        n = nonce

        Args:
            counter: Block counter value

        Returns:
            List of 16 32-bit words representing initial state
        """
        state = []

        # Constants (4 words)
        state.extend(self.CONSTANTS)

        # Key (8 words)
        key_words = bytes_to_u32_array(self.key)
        state.extend(key_words)

        # Counter (1 word)
        state.append(counter & 0xFFFFFFFF)

        # Nonce (3 words)
        nonce_words = bytes_to_u32_array(self.nonce)
        state.extend(nonce_words)

        return state

    def _double_round(self, state: List[int]) -> List[int]:
        """
        Apply one double round (column round + diagonal round).

        Args:
            state: State array

        Returns:
            Modified state array
        """
        state = column_round(state)
        state = diagonal_round(state)
        return state

    def chacha20_block(self, counter: int) -> bytes:
        """
        Generate one ChaCha20 block (64 bytes).

        Args:
            counter: Block counter

        Returns:
            64-byte keystream block
        """
        # Initialize state
        state = self._setup_state(counter)
        initial_state = state.copy()

        # Perform 20 rounds (10 double rounds)
        for _ in range(10):
            state = self._double_round(state)

        # Add initial state
        for i in range(16):
            state[i] = add32(state[i], initial_state[i])

        # Convert to bytes
        return u32_array_to_bytes(state)

    def encrypt(self, plaintext: bytes) -> bytes:
        """
        Encrypt plaintext using ChaCha20.

        Args:
            plaintext: Data to encrypt

        Returns:
            Ciphertext (same length as plaintext)
        """
        return self.crypt(plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        """
        Decrypt ciphertext using ChaCha20.

        Args:
            ciphertext: Data to decrypt

        Returns:
            Plaintext (same length as ciphertext)
        """
        return self.crypt(ciphertext)

    def crypt(self, data: bytes) -> bytes:
        """
        Encrypt or decrypt data (ChaCha20 is symmetric).

        Args:
            data: Input data

        Returns:
            Output data (XORed with keystream)
        """
        result = bytearray()
        counter = self.counter

        # Process complete blocks
        for i in range(0, len(data), 64):
            keystream = self.chacha20_block(counter)
            block_size = min(64, len(data) - i)

            # XOR data with keystream
            for j in range(block_size):
                result.append(data[i + j] ^ keystream[j])

            counter += 1

        return bytes(result)


def chacha20_encrypt(key: bytes, nonce: bytes, counter: int, plaintext: bytes) -> bytes:
    """
    Convenience function for ChaCha20 encryption.

    Args:
        key: 256-bit key
        nonce: 96-bit nonce
        counter: Initial counter
        plaintext: Data to encrypt

    Returns:
        Ciphertext
    """
    cipher = ChaCha20(key, nonce, counter)
    return cipher.encrypt(plaintext)


def chacha20_decrypt(
    key: bytes, nonce: bytes, counter: int, ciphertext: bytes
) -> bytes:
    """
    Convenience function for ChaCha20 decryption.

    Args:
        key: 256-bit key
        nonce: 96-bit nonce
        counter: Initial counter
        ciphertext: Data to decrypt

    Returns:
        Plaintext
    """
    cipher = ChaCha20(key, nonce, counter)
    return cipher.decrypt(ciphertext)
