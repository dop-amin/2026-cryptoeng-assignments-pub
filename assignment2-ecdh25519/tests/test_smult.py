import argparse
import os
import random
import sys
import time

from tqdm import tqdm

try:
    from common.testing.platform_interface import get_platform
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from common.testing.platform_interface import get_platform

try:
    from ecdh25519_protocol import Ecdh25519Protocol, N, N_P3
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    TESTS_DIR = os.path.dirname(__file__)
    if TESTS_DIR not in sys.path:
        sys.path.insert(0, TESTS_DIR)
    from ecdh25519_protocol import Ecdh25519Protocol, N, N_P3

try:
    from reference.fe25519 import Fe25519, P
    from reference.ge25519 import Ge25519
    from reference.smult import crypto_scalarmult, crypto_scalarmult_base
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    ASSIGNMENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if ASSIGNMENT_ROOT not in sys.path:
        sys.path.insert(0, ASSIGNMENT_ROOT)
    from reference.fe25519 import Fe25519, P
    from reference.ge25519 import Ge25519
    from reference.smult import crypto_scalarmult, crypto_scalarmult_base

NTESTS = 50

L = 2**252 + 27742317777372353535851937790883648493


# Helper functions
def clear_buffers(uart, delay: float = 0.1):
    """Clear UART buffers with optional delay."""
    time.sleep(delay)
    # Only clear buffers if serial port exists (board platform)
    if hasattr(uart, "serial") and uart.serial:
        uart.serial.reset_input_buffer()
        uart.serial.reset_output_buffer()


def show_mismatch(expected: bytes, got: bytes, max_len: int = None):
    """Show first mismatch between expected and got bytes."""
    length = min(len(expected), len(got)) if max_len is None else max_len
    for i in range(length):
        if expected[i] != got[i]:
            print(
                (
                    f"    First mismatch at byte {i}: got {got[i]:02x},"
                    f"expected {expected[i]:02x}"
                )
            )
            return
    if len(expected) != len(got):
        print(
            f"    Length mismatch: got {len(got)} bytes, expected {len(expected)} bytes"
        )


# Test for field arithmetic fe25519
def test_fe25519_cmov(uart, num_tests: int = 1):
    """Test fe25519_cmov."""
    print(f"\nTesting {num_tests} fe25519_cmov...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, (1 << 255) - 1)
        y = random.randint(0, (1 << 255) - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        cond = random.randint(0, 1)
        cond_byte = cond.to_bytes(4, byteorder="little")
        x = y if cond else x
        exp = x

        # Send to board
        uart_out = uart.test_fe25519_cmov(x, y, cond_byte)
        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_cmov test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_cmov test {test_num + 1}")
            print(f"    Input x:    {x.hex()}")
            print(f"    Input y:    {y.hex()}")
            print(f"    Input cond: {cond}")
            print(f"    Expected:   {exp.hex()}")
            print(f"    Got:        {act.hex()}")
            assert False, f"fe25519_cmov test {test_num + 1} failed"


def test_fe25519_freeze(uart, num_tests: int = 1):
    """Test fe25519_freeze."""
    print(f"\nTesting {num_tests} fe25519_freeze...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, (1 << 255) - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        r = Fe25519.freeze(r)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_freeze(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_freeze test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_freeze test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_freeze test {test_num + 1} failed"


def test_fe25519_iseq(uart, num_tests: int = 1):
    """Test fe25519_iseq."""
    print(f"\nTesting {num_tests} fe25519_iseq...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        exp = Fe25519.iseq(r1, r2)

        # Send to board
        uart_out = uart.test_fe25519_iseq(x, y)

        assert (
            uart_out and len(uart_out) == 4
        ), f"fe25519_iseq test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:4])
        act = int.from_bytes(act, byteorder="big")

        if act != exp:
            print(f"\n  FAIL: fe25519_iseq test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Input:    {y.hex()}")
            print(f"    Expected: {exp}")
            print(f"    Got:      {act}")
            assert False, f"fe25519_iseq test {test_num + 1} failed"


def test_fe25519_isnegative(uart, num_tests: int = 1):
    """Test fe25519_isnegative."""
    print(f"\nTesting {num_tests} fe25519_isnegative...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        exp = Fe25519.isnegative(r)

        # Send to board
        uart_out = uart.test_fe25519_isnegative(x)

        assert (
            uart_out and len(uart_out) == 4
        ), f"fe25519_isnegative test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:4])
        act = int.from_bytes(act, byteorder="big")

        if act != exp:
            print(f"\n  FAIL: fe25519_isnegative test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp}")
            print(f"    Got:      {act}")
            assert False, f"fe25519_isnegative test {test_num + 1} failed"


def test_fe25519_add(uart, num_tests: int = 1):
    """Test fe25519_add."""
    print(f"\nTesting {num_tests} fe25519_add...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        r = Fe25519.add(r1, r2)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_add(x, y)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_add test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_add test {test_num + 1}")
            print(f"    Input x:  {x.hex()}")
            print(f"    Input y:  {y.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_add test {test_num + 1} failed"


def test_fe25519_add_rx(uart, num_tests: int = 1):
    """Test fe25519_add_rx."""
    print(f"\nTesting {num_tests} fe25519_add_rx...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        r = Fe25519.add(r1, r2)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_add_rx(x, y)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_add_rx test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_add_rx test {test_num + 1}")
            print(f"    Input x:  {x.hex()}")
            print(f"    Input y:  {y.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_add_rx test {test_num + 1} failed"


def test_fe25519_double(uart, num_tests: int = 1):
    """Test fe25519_double."""
    print(f"\nTesting {num_tests} fe25519_double...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        r = Fe25519.double(r)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_double(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_double test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_double test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_double test {test_num + 1} failed"


def test_fe25519_double_inplace(uart, num_tests: int = 1):
    """Test fe25519_double_inplace."""
    print(f"\nTesting {num_tests} fe25519_double_inplace...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        r = Fe25519.double(r)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_double_inplace(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_double_inplace test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_double_inplace test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_double_inplace test {test_num + 1} failed"


def test_fe25519_sub(uart, num_tests: int = 1):
    """Test fe25519_sub."""
    print(f"\nTesting {num_tests} fe25519_sub...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        r = Fe25519.sub(r1, r2)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_sub(x, y)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_sub test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_sub test {test_num + 1}")
            print(f"    Input x:  {x.hex()}")
            print(f"    Input y:  {y.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_sub test {test_num + 1} failed"


def test_fe25519_sub_rx(uart, num_tests: int = 1):
    """Test fe25519_sub_rx."""
    print(f"\nTesting {num_tests} fe25519_sub_rx...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        r = Fe25519.sub(r1, r2)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_sub_rx(x, y)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_sub_rx test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_sub_rx test {test_num + 1}")
            print(f"    Input x:  {x.hex()}")
            print(f"    Input y:  {y.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_sub_rx test {test_num + 1} failed"


def test_fe25519_neg(uart, num_tests: int = 1):
    """Test fe25519_neg."""
    print(f"\nTesting {num_tests} fe25519_neg...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        r = Fe25519.neg(r)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_neg(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_neg test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_neg test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_neg test {test_num + 1} failed"


def test_fe25519_neg_inplace(uart, num_tests: int = 1):
    """Test fe25519_neg_inplace."""
    print(f"\nTesting {num_tests} fe25519_neg_inplace...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        r = Fe25519.neg(r)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_neg_inplace(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_neg_inplace test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_neg_inplace test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_neg_inplace test {test_num + 1} failed"


def test_fe25519_mul(uart, num_tests: int = 1):
    """Test fe25519_mul."""
    print(f"\nTesting {num_tests} fe25519_mul...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        r = Fe25519.mul(r1, r2)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_mul(x, y)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_mul test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_mul test {test_num + 1}")
            print(f"    Input x:  {x.hex()}")
            print(f"    Input y:  {y.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_mul test {test_num + 1} failed"


def test_fe25519_mul_rx(uart, num_tests: int = 1):
    """Test fe25519_mul_rx."""
    print(f"\nTesting {num_tests} fe25519_mul_rx...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        r = Fe25519.mul(r1, r2)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_mul_rx(x, y)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_mul_rx test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_mul_rx test {test_num + 1}")
            print(f"    Input x:  {x.hex()}")
            print(f"    Input y:  {y.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_mul_rx test {test_num + 1} failed"


def test_fe25519_square(uart, num_tests: int = 1):
    """Test fe25519_square."""
    print(f"\nTesting {num_tests} fe25519_square...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        r = Fe25519.square(r)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_square(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_square test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_square test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_square test {test_num + 1} failed"


def test_fe25519_square_inplace(uart, num_tests: int = 1):
    """Test fe25519_square_inplace."""
    print(f"\nTesting {num_tests} fe25519_square_inplace...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        r = Fe25519.square(r)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_square_inplace(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_square_inplace test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_square_inplace test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_square_inplace test {test_num + 1} failed"


def test_fe25519_pow2523(uart, num_tests: int = 1):
    """Test fe25519_pow2523."""
    print(f"\nTesting {num_tests} fe25519_pow2523...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        r = Fe25519(list(x))
        r = Fe25519.pow2523(r)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_pow2523(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_pow2523 test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_pow2523 test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_pow2523 test {test_num + 1} failed"


def test_fe25519_invsqrt(uart, num_tests: int = 1):
    """Test fe25519_invsqrt."""
    print(f"\nTesting {num_tests} fe25519_invsqrt...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # x = (1/25 mod P).
        x = 2315841784746323908471419700173758157065399693312811280789151680158262592798
        x = x.to_bytes(N, byteorder="little")
        t = Fe25519(list(x))
        xinv = Fe25519.invsqrt(t)
        exp = bytes(xinv.v)

        # Send to board
        uart_out = uart.test_fe25519_invsqrt(x)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_invsqrt test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_invsqrt test {test_num + 1}")
            print(f"    Input:    {x.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_invsqrt test {test_num + 1} failed"


# Test for group arithemtic ge25519
def test_ge25519_unpack(uart, num_tests: int = 1):
    """Test ge25519_unpack_wrapper."""
    print(f"\nTesting {num_tests} ge25519_unpack_wrapper...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate a random scalar
        s = random.randint(0, L - 1)
        s = s.to_bytes(N, byteorder="little")
        # Generate random points
        p = crypto_scalarmult_base(s)
        # Unpack them to add
        p_unpack = Ge25519.unpack(p)
        x = bytes(p_unpack.x.v)
        y = bytes(p_unpack.y.v)
        z = bytes(p_unpack.z.v)
        t = bytes(p_unpack.t.v)
        exp = x + y + z + t

        # Send to board
        uart_out = uart.test_ge25519_unpack(p)

        assert (
            uart_out and len(uart_out) == N_P3
        ), f"ge25519_unpack_wrapper test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N_P3])

        if act != exp:
            print(f"\n  FAIL: ge25519_unpack_wrapper test {test_num + 1}")
            print(f"    Packed point:   {p.hex()}")
            print(f"    Expected:       {exp.hex()}")
            print(f"    Got:            {act.hex()}")
            assert False, f"ge25519_unpack_wrapper test {test_num + 1} failed"


def test_ge25519_pack(uart, num_tests: int = 1):
    """Test ge25519_pack_wrapper."""
    print(f"\nTesting {num_tests} ge25519_pack_wrapper...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate a random scalar
        s = random.randint(0, L - 1)
        s = s.to_bytes(N, byteorder="little")
        # Generate random points
        exp = crypto_scalarmult_base(s)
        # Unpack them for packing
        p_unpack = Ge25519.unpack(exp)
        x = bytes(p_unpack.x.v)
        y = bytes(p_unpack.y.v)
        z = bytes(p_unpack.z.v)
        t = bytes(p_unpack.t.v)
        p = x + y + z + t

        # Send to board
        uart_out = uart.test_ge25519_pack(p)

        assert (
            uart_out and len(uart_out) == N
        ), f"ge25519_pack_wrapper test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: ge25519_pack_wrapper test {test_num + 1}")
            print(f"    Unpacked point:   {p.hex()}")
            print(f"    Expected:         {exp.hex()}")
            print(f"    Got:              {act.hex()}")
            assert False, f"ge25519_pack_wrapper test {test_num + 1} failed"


def test_ge25519_add(uart, num_tests: int = 1):
    """Test ge25519_add_wrapper."""
    print(f"\nTesting {num_tests} ge25519_add_wrapper...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate a random scalar
        s1 = random.randint(0, L - 1)
        s2 = random.randint(0, L - 1)
        s1 = s1.to_bytes(N, byteorder="little")
        s2 = s2.to_bytes(N, byteorder="little")
        # Generate random points
        p = crypto_scalarmult_base(s1)
        q = crypto_scalarmult_base(s2)
        # Unpack them to add
        p_unpack = Ge25519.unpack(p)
        q_unpack = Ge25519.unpack(q)
        r_unpack = Ge25519.add(p_unpack, q_unpack)
        # Pack the result
        x = bytes(r_unpack.x.v)
        y = bytes(r_unpack.y.v)
        z = bytes(r_unpack.z.v)
        t = bytes(r_unpack.t.v)
        exp = x + y + z + t

        # Prepare the inputs before sending them to the board
        x = bytes(p_unpack.x.v)
        y = bytes(p_unpack.y.v)
        z = bytes(p_unpack.z.v)
        t = bytes(p_unpack.t.v)
        pp = x + y + z + t
        x = bytes(q_unpack.x.v)
        y = bytes(q_unpack.y.v)
        z = bytes(q_unpack.z.v)
        t = bytes(q_unpack.t.v)
        pq = x + y + z + t

        # Send to board
        uart_out = uart.test_ge25519_add(pp, pq)

        assert (
            uart_out and len(uart_out) == N_P3
        ), f"ge25519_add_wrapper test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N_P3])

        if act != exp:
            print(f"\n  FAIL: ge25519_add_wrapper test {test_num + 1}")
            print(f"    Point p:  {pp.hex()}")
            print(f"    Point q:  {pq.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"ge25519_add_wrapper test {test_num + 1} failed"


def test_ge25519_add_rp(uart, num_tests: int = 1):
    """Test ge25519_add_rp_wrapper."""
    print(f"\nTesting {num_tests} ge25519_add_rp_wrapper...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate a random scalar
        s1 = random.randint(0, L - 1)
        s2 = random.randint(0, L - 1)
        s1 = s1.to_bytes(N, byteorder="little")
        s2 = s2.to_bytes(N, byteorder="little")
        # Generate random points
        p = crypto_scalarmult_base(s1)
        q = crypto_scalarmult_base(s2)
        # Unpack them to add
        p_unpack = Ge25519.unpack(p)
        q_unpack = Ge25519.unpack(q)
        r_unpack = Ge25519.add(p_unpack, q_unpack)
        # Pack the result
        x = bytes(r_unpack.x.v)
        y = bytes(r_unpack.y.v)
        z = bytes(r_unpack.z.v)
        t = bytes(r_unpack.t.v)
        exp = x + y + z + t

        # Prepare the inputs before sending them to the board
        x = bytes(p_unpack.x.v)
        y = bytes(p_unpack.y.v)
        z = bytes(p_unpack.z.v)
        t = bytes(p_unpack.t.v)
        pp = x + y + z + t
        x = bytes(q_unpack.x.v)
        y = bytes(q_unpack.y.v)
        z = bytes(q_unpack.z.v)
        t = bytes(q_unpack.t.v)
        pq = x + y + z + t

        # Send to board
        uart_out = uart.test_ge25519_add_rp(pp, pq)

        assert (
            uart_out and len(uart_out) == N_P3
        ), f"ge25519_add_rp_wrapper test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N_P3])

        if act != exp:
            print(f"\n  FAIL: ge25519_add_rp_wrapper test {test_num + 1}")
            print(f"    Point p:  {pp.hex()}")
            print(f"    Point q:  {pq.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"ge25519_add_rp_wrapper test {test_num + 1} failed"


def test_ge25519_double_inplace(uart, num_tests: int = 1):
    """Test ge25519_double_inplace_wrapper."""
    print(f"\nTesting {num_tests} ge25519_double_inplace_wrapper...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate a random scalar
        s = random.randint(0, L - 1)
        s = s.to_bytes(N, byteorder="little")
        # Generate random points
        p = crypto_scalarmult_base(s)
        # Unpack them to add
        p_unpack = Ge25519.unpack(p)
        r_unpack = Ge25519.double(p_unpack)
        # Pack the result
        x = bytes(r_unpack.x.v)
        y = bytes(r_unpack.y.v)
        z = bytes(r_unpack.z.v)
        t = bytes(r_unpack.t.v)
        exp = x + y + z + t

        # Prepare the inputs before sending them to the board
        x = bytes(p_unpack.x.v)
        y = bytes(p_unpack.y.v)
        z = bytes(p_unpack.z.v)
        t = bytes(p_unpack.t.v)
        pp = x + y + z + t

        # Send to board
        uart_out = uart.test_ge25519_double_inplace(pp)

        assert (
            uart_out and len(uart_out) == N_P3
        ), f"ge25519_double_inplace_wrapper test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N_P3])

        if act != exp:
            print(f"\n  FAIL: ge25519_double_inplace_wrapper test {test_num + 1}")
            print(f"    Point:    {pp.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"ge25519_double_inplace_wrapper test {test_num + 1} failed"


# Tests for scalar multiplication functions
def test_crypto_scalarmult_base(uart, num_tests: int = 1):
    """Test crypto_scalarmult_base."""
    print(f"\nTesting {num_tests} crypto_scalarmult_base...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate a random scalar
        s = random.randint(0, L - 1)
        s = s.to_bytes(N, byteorder="little")
        exp = crypto_scalarmult_base(s)

        # Send to board
        uart_out = uart.test_crypto_scalarmult_base(s)

        assert (
            uart_out and len(uart_out) == N
        ), f"crypto_scalarmult_base test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: crypto_scalarmult_base test {test_num + 1}")
            print(f"    Scalar:   {s.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"crypto_scalarmult_base test {test_num + 1} failed"


def test_crypto_scalarmult(uart, num_tests: int = 1):
    """Test crypto_scalarmult."""
    print(f"\nTesting {num_tests} crypto_scalarmult...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate a random scalar
        s1 = random.randint(0, L - 1)
        s1 = s1.to_bytes(N, byteorder="little")
        p = crypto_scalarmult_base(s1)
        s2 = random.randint(0, L - 1)
        s2 = s2.to_bytes(N, byteorder="little")
        exp = crypto_scalarmult(s2, p)

        # Send to board
        uart_out = uart.test_crypto_scalarmult(s2, p)

        assert (
            uart_out and len(uart_out) == N
        ), f"crypto_scalarmult test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: crypto_scalarmult test {test_num + 1}")
            print(f"    Scalar:   {s2.hex()}")
            print(f"    Point:    {p.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"crypto_scalarmult test {test_num + 1} failed"


# Test for field arithmetic with radix-2^32 fe25519_rd32
def test_fe25519_add_rd32(uart, num_tests: int = 1):
    """Test fe25519_add_rd32."""
    print(f"\nTesting {num_tests} fe25519_add_rd32...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        r = Fe25519.add(r1, r2)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_add_rd32(x, y)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_add_rd32 test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_add_rd32 test {test_num + 1}")
            print(f"    Input x:  {x.hex()}")
            print(f"    Input y:  {y.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_add_rd32 test {test_num + 1} failed"


def test_fe25519_mul_rd32(uart, num_tests: int = 1):
    """Test fe25519_mul_rd32."""
    print(f"\nTesting {num_tests} fe25519_mul_rd32...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        x = random.randint(0, P - 1)
        y = random.randint(0, P - 1)
        x = x.to_bytes(N, byteorder="little")
        y = y.to_bytes(N, byteorder="little")
        r1 = Fe25519(list(x))
        r2 = Fe25519(list(y))
        r = Fe25519.mul(r1, r2)
        exp = bytes(r.v)

        # Send to board
        uart_out = uart.test_fe25519_mul_rd32(x, y)

        assert (
            uart_out and len(uart_out) == N
        ), f"fe25519_mul_rd32 test {test_num + 1}: Invalid response"

        # Parse and verify
        act = bytes(uart_out[0:N])

        if act != exp:
            print(f"\n  FAIL: fe25519_mul_rd32 test {test_num + 1}")
            print(f"    Input x:  {x.hex()}")
            print(f"    Input y:  {y.hex()}")
            print(f"    Expected: {exp.hex()}")
            print(f"    Got:      {act.hex()}")
            assert False, f"fe25519_mul_rd32 test {test_num + 1} failed"


def run_fe25519_test_suite(uart):
    """Run the fe25519 test suite."""
    tests = [
        (
            "Tests: fe25519_cmov",
            [
                lambda: test_fe25519_cmov(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_freeze",
            [
                lambda: test_fe25519_freeze(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_iseq",
            [
                lambda: test_fe25519_iseq(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_isnegative",
            [
                lambda: test_fe25519_isnegative(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_add",
            [
                lambda: test_fe25519_add(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_add_rx",
            [
                lambda: test_fe25519_add_rx(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_double",
            [
                lambda: test_fe25519_double(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_double_inplace",
            [
                lambda: test_fe25519_double_inplace(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_sub",
            [
                lambda: test_fe25519_sub(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_sub_rx",
            [
                lambda: test_fe25519_sub_rx(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_neg",
            [
                lambda: test_fe25519_neg(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_neg_inplace",
            [
                lambda: test_fe25519_neg_inplace(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_mul",
            [
                lambda: test_fe25519_mul(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_mul_rx",
            [
                lambda: test_fe25519_mul_rx(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_square",
            [
                lambda: test_fe25519_square(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_square_inplace",
            [
                lambda: test_fe25519_square_inplace(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_pow2523",
            [
                lambda: test_fe25519_pow2523(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: fe25519_invsqrt",
            [
                lambda: test_fe25519_invsqrt(uart, num_tests=1),
            ],
        ),
    ]

    for section_name, test_funcs in tests:
        print(f"\n--- {section_name} ---")
        for test_func in test_funcs:
            test_func()
            clear_buffers(uart, delay=0.5)


def run_ge25519_test_suite(uart):
    """Run the ge25519 test suite."""
    tests = [
        (
            "Tests: test_ge25519_unpack",
            [
                lambda: test_ge25519_unpack(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: test_ge25519_pack",
            [
                lambda: test_ge25519_pack(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: test_ge25519_add",
            [
                lambda: test_ge25519_add(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: test_ge25519_add_rp",
            [
                lambda: test_ge25519_add_rp(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: test_ge25519_double_inplace",
            [
                lambda: test_ge25519_double_inplace(uart, num_tests=NTESTS),
            ],
        ),
    ]

    for section_name, test_funcs in tests:
        print(f"\n--- {section_name} ---")
        for test_func in test_funcs:
            test_func()
            clear_buffers(uart, delay=0.5)


def run_smult_test_suite(uart):
    """Run the smult test suite."""
    tests = [
        (
            "Tests: test_crypto_scalarmult_base",
            [
                lambda: test_crypto_scalarmult_base(uart, num_tests=NTESTS),
            ],
        ),
        (
            "Tests: test_crypto_scalarmult",
            [
                lambda: test_crypto_scalarmult(uart, num_tests=NTESTS),
            ],
        ),
    ]

    for section_name, test_funcs in tests:
        print(f"\n--- {section_name} ---")
        for test_func in test_funcs:
            test_func()
            clear_buffers(uart, delay=0.5)


def run_fe25519_rd32_test_suite(uart):
    """Run the fe25519_rd32 test suite."""
    tests = [
        (
            "Tests: test_fe25519_add_rd32",
            [
                lambda: test_fe25519_add_rd32(uart, num_tests=500),
            ],
        ),
        (
            "Tests: test_fe25519_mul_rd32",
            [
                lambda: test_fe25519_mul_rd32(uart, num_tests=500),
            ],
        ),
    ]

    for section_name, test_funcs in tests:
        print(f"\n--- {section_name} ---")
        for test_func in test_funcs:
            test_func()
            clear_buffers(uart, delay=0.5)


def run_test_suite(uart):
    """Run the complete test suite."""
    run_fe25519_test_suite(uart)
    run_ge25519_test_suite(uart)
    run_smult_test_suite(uart)
    run_fe25519_rd32_test_suite(uart)


def main():
    """Main test entry point."""
    parser = argparse.ArgumentParser(
        description="Run GL(P) field arithmetic tests on board or QEMU"
    )
    parser.add_argument(
        "--platform",
        choices=["board", "qemu"],
        default="board",
        help="Platform to test on (default: board)",
    )
    parser.add_argument("--elf", help="Path to ELF file (required for QEMU)")
    parser.add_argument(
        "--port", help="Serial port (for board, auto-detect if not specified)"
    )
    parser.add_argument(
        "--test",
        choices=["fe25519", "fe25519_rd32", "ge25519", "smult", "all"],
        default="all",
        help="Choose which test suite to run",
    )
    args = parser.parse_args()

    # Validate arguments
    if args.platform == "qemu" and not args.elf:
        print("ERROR: --elf required when using QEMU platform")
        print(
            "Usage: python test_fe25519.py --platform qemu --elf ../build/fe25519.elf"
        )
        return

    # Create platform connection
    try:
        if args.platform == "board":
            platform = get_platform("board", port=args.port, baudrate=38400)
        else:  # qemu
            platform = get_platform("qemu", elf_path=args.elf)

        # Wrap platform in ChaCha20-specific protocol
        uart = Ecdh25519Protocol(platform)

    except Exception as e:
        print(f"ERROR: Failed to create platform: {e}")
        return

    if not uart.connect():
        print(f"ERROR: Failed to connect to {args.platform}")
        return

    platform_name = "Board" if args.platform == "board" else "QEMU"
    print(f"Connected to {platform_name}")
    clear_buffers(uart, delay=1.0)

    print("=" * 60)
    print(f"GL(P) Arithmetic {platform_name} Tests")
    print("=" * 60)

    try:
        if args.test == "fe25519":
            run_fe25519_test_suite(uart)

            print("\n" + "=" * 60)
            print("PASS: All tests passed!")
            print(f"  - {NTESTS} random fe25519_cmov")
            print(f"  - {NTESTS} random fe25519_freeze")
            print(f"  - {NTESTS} random fe25519_iseq")
            print(f"  - {NTESTS} random fe25519_isnegative")
            print(f"  - {NTESTS} random fe25519_add")
            print(f"  - {NTESTS} random fe25519_add_rx")
            print(f"  - {NTESTS} random fe25519_double")
            print(f"  - {NTESTS} random fe25519_double_inplace")
            print(f"  - {NTESTS} random fe25519_sub")
            print(f"  - {NTESTS} random fe25519_sub_rx")
            print(f"  - {NTESTS} random fe25519_neg")
            print(f"  - {NTESTS} random fe25519_neg_inplace")
            print(f"  - {NTESTS} random fe25519_mul")
            print(f"  - {NTESTS} random fe25519_mul_rx")
            print(f"  - {NTESTS} random fe25519_square")
            print(f"  - {NTESTS} random fe25519_square_inplace")
            print(f"  - {NTESTS} random fe25519_pow2523")
            print("  - 1 fix fe25519_invsqrt")

        if args.test == "fe25519_rd32":
            run_fe25519_rd32_test_suite(uart)

            print("\n" + "=" * 60)
            print("PASS: All tests passed!")
            print("  - 500 random fe25519_add_rd32")
            print("  - 500 random fe25519_mul_rd32")

        if args.test == "ge25519":
            run_ge25519_test_suite(uart)

            print("\n" + "=" * 60)
            print("PASS: All tests passed!")
            print(f"  - {NTESTS} random ge25519_pack")
            print(f"  - {NTESTS} random ge25519_unpack")
            print(f"  - {NTESTS} random ge25519_add")
            print(f"  - {NTESTS} random ge25519_add_rp")
            print(f"  - {NTESTS} random ge25519_double_inplace")

        if args.test == "smult":
            run_smult_test_suite(uart)

            print("\n" + "=" * 60)
            print("PASS: All tests passed!")
            print(f"  - {NTESTS} random crypto_scalarmult_base")
            print(f"  - {NTESTS} random crypto_scalarmult")

        if args.test == "all":
            run_test_suite(uart)

            print("\n" + "=" * 60)
            print("PASS: All tests passed!")
            print(f"  - {NTESTS} random fe25519_cmov")
            print(f"  - {NTESTS} random fe25519_freeze")
            print(f"  - {NTESTS} random fe25519_iseq")
            print(f"  - {NTESTS} random fe25519_isnegative")
            print(f"  - {NTESTS} random fe25519_add")
            print(f"  - {NTESTS} random fe25519_add_rx")
            print(f"  - {NTESTS} random fe25519_double")
            print(f"  - {NTESTS} random fe25519_double_inplace")
            print(f"  - {NTESTS} random fe25519_sub")
            print(f"  - {NTESTS} random fe25519_sub_rx")
            print(f"  - {NTESTS} random fe25519_neg")
            print(f"  - {NTESTS} random fe25519_neg_inplace")
            print(f"  - {NTESTS} random fe25519_mul")
            print(f"  - {NTESTS} random fe25519_mul_rx")
            print(f"  - {NTESTS} random fe25519_square")
            print(f"  - {NTESTS} random fe25519_square_inplace")
            print(f"  - {NTESTS} random fe25519_pow2523")
            print("  - 1 fix fe25519_invsqrt")
            print(f"  - {NTESTS} random ge25519_pack")
            print(f"  - {NTESTS} random ge25519_unpack")
            print(f"  - {NTESTS} random ge25519_add")
            print(f"  - {NTESTS} random ge25519_add_rp")
            print(f"  - {NTESTS} random ge25519_double_inplace")
            print(f"  - {NTESTS} random crypto_scalarmult_base")
            print(f"  - {NTESTS} random crypto_scalarmult")

        print("=" * 60)
    except AssertionError as e:
        print(f"\nFAIL: Test suite failed: {e}")
    finally:
        uart.disconnect()


if __name__ == "__main__":
    main()
