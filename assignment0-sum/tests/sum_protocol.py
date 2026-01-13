"""
Sum-Specific Test Protocol
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


def simple_prng(seed: int, count: int, mod: int = 0xFFFFFFFF) -> list[int]:
    """
    Simple PRNG using xorshift32 algorithm.
    Generates count uint32 values from seed.

    This must match the firmware implementation exactly.
    """
    state = seed & 0xFFFFFFFF
    result = []

    for _ in range(count):
        # xorshift32 algorithm
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= (state >> 17) & 0xFFFFFFFF
        state ^= (state << 5) & 0xFFFFFFFF
        result.append(state % mod)

    return result


class SumProtocol(CommandProtocol):
    """
    Test protocol for sum implementation.

    Provides methods to test:
    - SUM_C (naive C implementation, provided by us)
    - SUM_JASMIN (Jasmin implementation)
    - SUM_JASMIN_FAST (Jasmin implementation, speed optimized)
    """

    def test_sum(self, mode: str, seed: int, count: int, mod: int) -> Optional[bytes]:
        """
        Test sum function with PRNG-generated data.

        Args:
            mode: Sum implementation mode (SUM_C, SUM_JASMIN, SUM_JASMIN_FAST)
            seed: Seed for PRNG (32-bit unsigned)
            count: Number of integers to generate

        Returns:
            4 bytes containing sum result (big-endian) or None on error
        """
        assert mode in ["SUM_C", "SUM_JASMIN", "SUM_JASMIN_FAST"], "Unknown sum mode."

        # Send seed (4 bytes) and count (4 bytes) concatenated
        seed_bytes = (seed & 0xFFFFFFFF).to_bytes(4, "big")
        count_bytes = count.to_bytes(4, "big")
        mod_bytes = mod.to_bytes(4, "big")

        command = f"TEST_{mode} {seed_bytes.hex()}{count_bytes.hex()}{mod_bytes.hex()}"
        return self._send_test_command(command, expected_length=4)

    def benchmark_sum(self, mode: str, iterations: int) -> Optional[int]:
        """
        Benchmark sum function performance.

        Args:
            mode: Sum implementation mode (SUM_C, SUM_JASMIN, SUM_JASMIN_FAST)
            iterations: Number of iterations to run

        Returns:
            Total CPU cycles or None on error
        """
        assert mode in ["SUM_C", "SUM_JASMIN", "SUM_JASMIN_FAST"], "Unknown sum mode."
        command = f"BENCHMARK_{mode} {iterations}"
        return self._send_benchmark_command(command)
