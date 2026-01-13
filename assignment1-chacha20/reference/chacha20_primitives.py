"""
ChaCha20 Primitive Operations

This module provides the lowest-level operations for ChaCha20, allowing
students to test individual components of their implementation.

Each function is designed to match what students would implement in Jasmin.
"""


def add32(a: int, b: int) -> int:
    """
    Add two 32-bit unsigned integers with wraparound.

    Args:
        a: First operand (32-bit)
        b: Second operand (32-bit)

    Returns:
        Sum modulo 2^32
    """
    return (a + b) & 0xFFFFFFFF


def xor32(a: int, b: int) -> int:
    """
    XOR two 32-bit unsigned integers.

    Args:
        a: First operand (32-bit)
        b: Second operand (32-bit)

    Returns:
        XOR result
    """
    return a ^ b


def rotl32(x: int, n: int) -> int:
    """
    Rotate left (circular shift) a 32-bit unsigned integer.

    Args:
        x: Value to rotate (32-bit)
        n: Number of bits to rotate (0-31)

    Returns:
        x rotated left by n bits
    """
    n = n & 31  # Ensure n is in range 0-31
    x = x & 0xFFFFFFFF
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def quarterround_line(
    a: int, b: int, c: int, d: int, rot: int
) -> tuple[int, int, int, int]:
    """
    Execute one line of the ChaCha20 quarter round.

    Performs: a += b; d ^= a; d <<<= rot

    Args:
        a, b, c, d: State values (32-bit each)
        rot: Rotation amount (16, 12, 8, or 7)

    Returns:
        Tuple of updated (a, b, c, d) values
    """
    a = add32(a, b)
    d = xor32(d, a)
    d = rotl32(d, rot)
    return (a, b, c, d)


def quarterround_line_alt(
    a: int, b: int, c: int, d: int, rot: int
) -> tuple[int, int, int, int]:
    """
    Alternative quarter round line: c += d; b ^= c; b <<<= rot

    Args:
        a, b, c, d: State values (32-bit each)
        rot: Rotation amount

    Returns:
        Tuple of updated (a, b, c, d) values
    """
    c = add32(c, d)
    b = xor32(b, c)
    b = rotl32(b, rot)
    return (a, b, c, d)


def quarterround(a: int, b: int, c: int, d: int) -> tuple[int, int, int, int]:
    """
    Complete ChaCha20 quarter round operation.

    Performs the four operations:
    1. a += b; d ^= a; d <<<= 16
    2. c += d; b ^= c; b <<<= 12
    3. a += b; d ^= a; d <<<= 8
    4. c += d; b ^= c; b <<<= 7

    Args:
        a, b, c, d: Input values (32-bit each)

    Returns:
        Tuple of updated (a, b, c, d) values
    """
    # Line 1
    a, b, c, d = quarterround_line(a, b, c, d, 16)

    # Line 2
    a, b, c, d = quarterround_line_alt(a, b, c, d, 12)

    # Line 3
    a, b, c, d = quarterround_line(a, b, c, d, 8)

    # Line 4
    a, b, c, d = quarterround_line_alt(a, b, c, d, 7)

    return (a, b, c, d)


def bytes_to_u32_le(data: bytes, offset: int = 0) -> int:
    """
    Convert 4 bytes to 32-bit unsigned integer (little-endian).

    Args:
        data: Byte array
        offset: Starting offset

    Returns:
        32-bit unsigned integer
    """
    return (
        data[offset]
        | (data[offset + 1] << 8)
        | (data[offset + 2] << 16)
        | (data[offset + 3] << 24)
    )


def u32_to_bytes_le(value: int) -> bytes:
    """
    Convert 32-bit unsigned integer to 4 bytes (little-endian).

    Args:
        value: 32-bit unsigned integer

    Returns:
        4-byte array
    """
    value = value & 0xFFFFFFFF
    return bytes(
        [value & 0xFF, (value >> 8) & 0xFF, (value >> 16) & 0xFF, (value >> 24) & 0xFF]
    )


def u32_array_to_bytes(words: list[int]) -> bytes:
    """
    Convert array of 32-bit words to bytes (little-endian).

    Args:
        words: List of 32-bit unsigned integers

    Returns:
        Byte array
    """
    result = bytearray()
    for word in words:
        result.extend(u32_to_bytes_le(word))
    return bytes(result)


def bytes_to_u32_array(data: bytes) -> list[int]:
    """
    Convert bytes to array of 32-bit words (little-endian).

    Args:
        data: Byte array (must be multiple of 4)

    Returns:
        List of 32-bit unsigned integers
    """
    if len(data) % 4 != 0:
        raise ValueError("Data length must be multiple of 4")

    words = []
    for i in range(0, len(data), 4):
        words.append(bytes_to_u32_le(data, i))
    return words


def column_round(state: list[int]) -> list[int]:
    """
    Apply ChaCha20 column round to state.

    Performs quarterround on all 4 columns:
    - Column 0: (0, 4, 8, 12)
    - Column 1: (1, 5, 9, 13)
    - Column 2: (2, 6, 10, 14)
    - Column 3: (3, 7, 11, 15)

    Args:
        state: 16-element state array (will be modified in place)

    Returns:
        Modified state array
    """
    if len(state) != 16:
        raise ValueError("State must have 16 elements")

    # Make a copy to avoid modifying input
    state = list(state)

    # Column 0
    state[0], state[4], state[8], state[12] = quarterround(
        state[0], state[4], state[8], state[12]
    )

    # Column 1
    state[1], state[5], state[9], state[13] = quarterround(
        state[1], state[5], state[9], state[13]
    )

    # Column 2
    state[2], state[6], state[10], state[14] = quarterround(
        state[2], state[6], state[10], state[14]
    )

    # Column 3
    state[3], state[7], state[11], state[15] = quarterround(
        state[3], state[7], state[11], state[15]
    )

    return state


def diagonal_round(state: list[int]) -> list[int]:
    """
    Apply ChaCha20 diagonal round to state.

    Performs quarterround on all 4 diagonals:
    - Diagonal 0: (0, 5, 10, 15)
    - Diagonal 1: (1, 6, 11, 12)
    - Diagonal 2: (2, 7, 8, 13)
    - Diagonal 3: (3, 4, 9, 14)

    Args:
        state: 16-element state array (will be modified in place)

    Returns:
        Modified state array
    """
    if len(state) != 16:
        raise ValueError("State must have 16 elements")

    # Make a copy to avoid modifying input
    state = list(state)

    # Diagonal 0
    state[0], state[5], state[10], state[15] = quarterround(
        state[0], state[5], state[10], state[15]
    )

    # Diagonal 1
    state[1], state[6], state[11], state[12] = quarterround(
        state[1], state[6], state[11], state[12]
    )

    # Diagonal 2
    state[2], state[7], state[8], state[13] = quarterround(
        state[2], state[7], state[8], state[13]
    )

    # Diagonal 3
    state[3], state[4], state[9], state[14] = quarterround(
        state[3], state[4], state[9], state[14]
    )

    return state
