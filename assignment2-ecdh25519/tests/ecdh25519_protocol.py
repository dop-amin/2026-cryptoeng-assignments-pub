"""
Arithmetic in GL(P) test protocol: Fe25519.

Provides test methods for main arithmetic computation in the field GL(P).
Inherits from CommandProtocol to leverage common command handling logic.

This module contains all Fe25519-specific test commands, keeping the
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

N = 32
N_P3 = N * 4


class Ecdh25519Protocol(CommandProtocol):
    """
    Test protocol for all functions used for Ecdh25519's scalar multiplication.

    """

    def test_fe25519_cmov(self, x: bytes, y: bytes, cond: bytes) -> Optional[bytes]:
        """
        Test fe25519_cmov.

        Args:
            x: in GL(P)
            y: in GL(P)
            cond: condition for conditional move

        Returns:
            r = x mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_CMOV {x.hex()} {y.hex()} {cond.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_freeze(self, x: bytes) -> Optional[bytes]:
        """
        Test fe25519_freeze.

        Args:
            x: in GL(P)

        Returns:
            r = x mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_FREEZE {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_iseq(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_iseq.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            b = 1 if x == y. b = 0 if x != y or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_ISEQ {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=4)

    def test_fe25519_isnegative(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_isnegative.

        Args:
            x: in GL(P)

        Returns:
            b = 1 if LSB(x) == 1. b = 0 if LSB(x) != 1 or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_ISNEGATIVE {x.hex()}"
        return self._send_test_command(command, expected_length=4)

    def test_fe25519_add(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_add.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            r = (x + y) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_ADD {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_add_rx(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_add_rx.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            x = (x + y) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_ADD_RX {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_double(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_double.

        Args:
            x: in GL(P)

        Returns:
            r = (x + x) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_DOUBLE {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_double_inplace(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_double.

        Args:
            x: in GL(P)

        Returns:
            x = (x + x) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_DOUBLE_INPLACE {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_sub(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_sub.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            r = (x - y) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_SUB {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_sub_rx(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_sub_rx.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            x = (x - y) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_SUB_RX {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_neg(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_neg.

        Args:
            x: in GL(P)

        Returns:
            r = (-x) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_NEG {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_neg_inplace(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_neg_inplace.

        Args:
            x: in GL(P)

        Returns:
            x = (-x) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_NEG_INPLACE {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_mul(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_mul.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            r = (x * y) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_MUL {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_mul_rx(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_mul_rx.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            x = (x * y) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_MUL_RX {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_square(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_square.

        Args:
            x: in GL(P)

        Returns:
            r = (x^2) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_SQUARE {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_square_inplace(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_square_inplace.

        Args:
            x: in GL(P)

        Returns:
            x = (x^2) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_SQUARE_INPLACE {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_pow2523(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_pow2523.

        Args:
            x: in GL(P)

        Returns:
            r = (x^(2^252-3)) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_POW2523 {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_invsqrt(self, x: bytes) -> Optional[int]:
        """
        Test fe25519_invsqrt.

        Args:
            x: in GL(P)

        Returns:
            r in GL(P) s.t (r^2) * x = 1 mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_INVSQRT {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_ge25519_unpack(self, p: bytes) -> Optional[bytes]:
        """
        Test ge25519_unpack.

        Args:
            p: an encoded point on Ecdh25519 (of N bytes)

        Returns:
            r = ge25519_unpack(p) on Ecdh25519 (of N_P3 bytes) or None on error
        """
        if len(p) != N:
            raise ValueError("Encoded point must be N bytes")

        command = f"TEST_GE25519_UNPACK {p.hex()}"
        return self._send_test_command(command, expected_length=N_P3)

    def test_ge25519_pack(self, p: bytes) -> Optional[bytes]:
        """
        Test ge25519_pack.

        Args:
            p: a point on Ecdh25519 in extended Twisted Edwards coordinates
               (of N_P3 bytes)

        Returns:
            r = ge25519_pack(x) on Ecdh25519 (of N bytes) or None on error
        """
        if len(p) != N_P3:
            raise ValueError("Point must be N_P3 bytes")

        command = f"TEST_GE25519_PACK {p.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_ge25519_add(self, p: bytes, q: bytes) -> Optional[bytes]:
        """
        Test ge25519_add.

        Args:
            p: a point on Ecdh25519 (of N_P3 bytes)
            q: a point on Ecdh25519 (of N_P3 bytes)

        Returns:
            r = p + q on Ecdh25519 (of N_P3 bytes) or None on error
        """
        if len(p) != N_P3:
            raise ValueError("Point must be N_P3 bytes")
        if len(q) != N_P3:
            raise ValueError("Point must be N_P3 bytes")

        command = f"TEST_GE25519_ADD {p.hex()} {q.hex()}"
        return self._send_test_command(command, expected_length=N_P3)

    def test_ge25519_add_rp(self, p: bytes, q: bytes) -> Optional[bytes]:
        """
        Test ge25519_add_rp.

        Args:
            p: a point on Ecdh25519 (of N_P3 bytes)
            q: a point on Ecdh25519 (of N_P3 bytes)

        Returns:
            p = p + q on Ecdh25519 (of N_P3 bytes) or None on error
        """
        if len(p) != N_P3:
            raise ValueError("Point must be N_P3 bytes")
        if len(q) != N_P3:
            raise ValueError("Point must be N_P3 bytes")

        command = f"TEST_GE25519_ADD_RP {p.hex()} {q.hex()}"
        return self._send_test_command(command, expected_length=N_P3)

    def test_ge25519_double_inplace(self, p: bytes) -> Optional[bytes]:
        """
        Test ge25519_double_inplace.

        Args:
            p: a point on Ecdh25519 (of N_P3 bytes)

        Returns:
            p = 2 * p on Ecdh25519 or None on error
        """
        if len(p) != N_P3:
            raise ValueError("Point must be N_P3 bytes")

        command = f"TEST_GE25519_DOUBLE_INPLACE {p.hex()}"
        return self._send_test_command(command, expected_length=N_P3)

    def test_crypto_scalarmult_base(self, x: bytes) -> Optional[bytes]:
        """
        Test crypto_scalarmult_base.

        Args:
            x: in GL(P)

        Returns:
            r = x * B on Ecdh25519 (of N bytes) or None on error
        """
        if len(x) != N:
            raise ValueError("Scalar must be N bytes")

        command = f"TEST_CRYPTO_SCALARMULT_BASE {x.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_crypto_scalarmult(self, x: bytes, p: bytes) -> Optional[bytes]:
        """
        Test crypto_scalarmult.

        Args:
            x: in GL(P)
            p: an encoded point on Ecdh25519 (of N bytes)

        Returns:
            r = x * p on Ecdh25519 (of N bytes) or None on error
        """
        if len(x) != N:
            raise ValueError("Scalar must be N bytes")
        if len(p) != N:
            raise ValueError("Encoded point must be N bytes")

        command = f"TEST_CRYPTO_SCALARMULT {x.hex()} {p.hex()}"
        return self._send_test_command(command, expected_length=N)

    def benchmark_crypto_scalarmult_base(self, iterations: int) -> Optional[int]:
        """
        Benchmark crypto_scalarmult_base function performance.

        Args:
            iterations: number of iterations to run

        Return:
            Total CPU cycles or None on error
        """
        command = f"BENCHMARK_CRYPTO_SCALARMULT_BASE {iterations}"
        return self._send_benchmark_command(command)

    # Test protocols for radix-2^32 field arithmetic
    def test_fe25519_add_rd32(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_add_rd32.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            r = (x + y) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_ADD_RD32 {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=N)

    def test_fe25519_mul_rd32(self, x: bytes, y: bytes) -> Optional[int]:
        """
        Test fe25519_mul_rd32.

        Args:
            x: in GL(P)
            y: in GL(P)

        Returns:
            r = (x * y) mod P or None on error
        """
        if len(x) != N:
            raise ValueError("Field element must be N bytes")
        if len(y) != N:
            raise ValueError("Field element must be N bytes")

        command = f"TEST_FE25519_MUL_RD32 {x.hex()} {y.hex()}"
        return self._send_test_command(command, expected_length=N)

    def benchmark_fe25519_add_rd32(self, iterations: int) -> Optional[int]:
        """
        Benchmark fe25519_add_rd32 function performance.

        Args:
            iterations: number of iterations to run

        Return:
            Total CPU cycles or None on error
        """
        command = f"BENCHMARK_FE25519_ADD_RD32 {iterations}"
        return self._send_benchmark_command(command)

    def benchmark_fe25519_mul_rd32(self, iterations: int) -> Optional[int]:
        """
        Benchmark fe25519_mul_rd32 function performance.

        Args:
            iterations: number of iterations to run

        Return:
            Total CPU cycles or None on error
        """
        command = f"BENCHMARK_FE25519_MUL_RD32 {iterations}"
        return self._send_benchmark_command(command)

    def benchmark_fe25519_add_wrapper(self, iterations: int) -> Optional[int]:
        """
        Benchmark fe25519_add_wrapper function performance.

        Args:
            iterations: number of iterations to run

        Return:
            Total CPU cycles or None on error
        """
        command = f"BENCHMARK_FE25519_ADD_WRAPPER {iterations}"
        return self._send_benchmark_command(command)

    def benchmark_fe25519_mul_wrapper(self, iterations: int) -> Optional[int]:
        """
        Benchmark fe25519_mul_wrapper function performance.

        Args:
            iterations: number of iterations to run

        Return:
            Total CPU cycles or None on error
        """
        command = f"BENCHMARK_FE25519_MUL_WRAPPER {iterations}"
        return self._send_benchmark_command(command)
