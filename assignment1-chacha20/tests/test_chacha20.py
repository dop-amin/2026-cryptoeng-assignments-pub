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
    from chacha20_protocol import ChaCha20Protocol
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    TESTS_DIR = os.path.dirname(__file__)
    if TESTS_DIR not in sys.path:
        sys.path.insert(0, TESTS_DIR)
    from chacha20_protocol import ChaCha20Protocol

try:
    from reference.chacha20_primitives import (
        column_round,
        diagonal_round,
        quarterround,
        u32_array_to_bytes,
    )
    from reference.chacha20 import ChaCha20
    from reference.test_vectors import BLOCK_TEST, QUARTERROUND_TEST
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    ASSIGNMENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if ASSIGNMENT_ROOT not in sys.path:
        sys.path.insert(0, ASSIGNMENT_ROOT)
    from reference.chacha20_primitives import (
        column_round,
        diagonal_round,
        quarterround,
        u32_array_to_bytes,
    )
    from reference.chacha20 import ChaCha20
    from reference.test_vectors import BLOCK_TEST, QUARTERROUND_TEST

NTESTS = 100
RFC8439_KEY = bytes.fromhex(
    "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"
)
RFC8439_NONCE = bytes.fromhex("000000090000004a00000000")


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


# Test functions
def test_quarterrounds(uart, num_tests: int = 1, rfc_mode: bool = False):
    """Test quarterround operations.

    Returns:
        True if all tests passed, False otherwise
    """
    print(f"\nTesting {num_tests} quarterround operations...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        if rfc_mode:
            a, b, c, d = QUARTERROUND_TEST["input"]
            expected_a, expected_b, expected_c, expected_d = QUARTERROUND_TEST["output"]
        else:
            a, b, c, d = (random.randint(0, 0xFFFFFFFF) for _ in range(4))
            expected_a, expected_b, expected_c, expected_d = quarterround(a, b, c, d)

        # Send to board
        uart_out = uart.test_quarterround(a, b, c, d)

        assert (
            uart_out and len(uart_out) == 16
        ), f"Quarterround test {test_num + 1}: Invalid response"

        # Parse and verify
        result = tuple(
            int.from_bytes(uart_out[i : i + 4], "little") for i in range(0, 16, 4)
        )
        expected = (expected_a, expected_b, expected_c, expected_d)

        if result != expected:
            print(f"\n  FAIL: Quarterround test {test_num + 1}")
            print(f"    Input:    {a:08x} {b:08x} {c:08x} {d:08x}")
            print(
                (
                    f"    Expected: {expected_a:08x} {expected_b:08x}"
                    f"{expected_c:08x} {expected_d:08x}"
                )
            )
            print(
                "    Got:      "
                f"{result[0]:08x} {result[1]:08x} "
                f"{result[2]:08x} {result[3]:08x}"
            )
            return False

    return True


def test_chacha20_blocks(uart, num_tests: int = 1, rfc_mode: bool = False):
    """Test ChaCha20 block function.

    Returns:
        True if all tests passed, False otherwise
    """
    print(f"\nTesting {num_tests} ChaCha20 blocks...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        if rfc_mode:
            key, nonce, counter = (
                BLOCK_TEST["key"],
                BLOCK_TEST["nonce"],
                BLOCK_TEST["counter"],
            )
            expected_keystream = BLOCK_TEST["keystream"]
            cipher = ChaCha20(key, nonce, counter)
            input_state = cipher._setup_state(counter)
        else:
            key = bytes([random.randint(0, 255) for _ in range(32)])
            nonce = bytes([random.randint(0, 255) for _ in range(12)])
            counter = random.randint(0, 0xFFFFFFFF)
            cipher = ChaCha20(key, nonce, counter)
            input_state = cipher._setup_state(counter)
            expected_keystream = cipher.chacha20_block(counter)

        # Convert input state to bytes (little-endian for transmission)
        input_bytes = b"".join(word.to_bytes(4, "little") for word in input_state)
        uart_out = uart.test_block(input_bytes)

        assert (
            uart_out and len(uart_out) == 64
        ), f"Block test {test_num + 1}: Invalid response"

        if uart_out != expected_keystream:
            print(f"\n  FAIL: Block test {test_num + 1}")
            print(f"    Key:      {key.hex()}")
            print(f"    Nonce:    {nonce.hex()}")
            print(f"    Counter:  {counter:08x}")
            print(f"    Expected: {expected_keystream.hex()}")
            print(f"    Got:      {uart_out.hex()}")
            show_mismatch(expected_keystream, uart_out)
            return False

    return True


def test_keystream_generation(uart, num_tests: int = 1, block_len: int = 64):
    """Test ChaCha20 IETF keystream generation.

    Returns:
        True if all tests passed, False otherwise
    """
    print(
        f"\nTesting {num_tests} ChaCha20 IETF keystream generations "
        f"({block_len} bytes each)..."
    )

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        key = bytes([random.randint(0, 255) for _ in range(32)])
        nonce = bytes([random.randint(0, 255) for _ in range(12)])

        cipher = ChaCha20(key, nonce, counter=0)
        expected_keystream = cipher.crypt(b"\x00" * block_len)
        uart_out = uart.test_keystream(key, nonce, block_len)

        assert uart_out is not None, f"Keystream test {test_num + 1}: No response"
        assert (
            len(uart_out) == block_len
        ), f"Keystream test {test_num + 1}: Wrong length"

        if uart_out != expected_keystream:
            print(f"\n  FAIL: Keystream test {test_num + 1}")
            print(f"    Key:      {key.hex()}")
            print(f"    Nonce:    {nonce.hex()}")
            print(f"    Expected: {expected_keystream.hex()}")
            print(f"    Got:      {uart_out.hex()}")
            show_mismatch(expected_keystream, uart_out, block_len)
            return False

    return True


def test_component_keysetup(uart):
    """Test chacha20_keysetup component function.

    Returns:
        True if test passed, False otherwise
    """
    print("\n--- Testing chacha20_keysetup ---")

    result = uart.test_keysetup(RFC8439_KEY)
    assert result and len(result) == 64, "Keysetup: Invalid response"

    # Build expected state: constants + key + zeros
    expected = bytearray()
    for const in [0x61707865, 0x3320646E, 0x79622D32, 0x6B206574]:
        expected.extend(const.to_bytes(4, "little"))
    expected.extend(RFC8439_KEY)  # Key already in correct byte order
    expected.extend(bytes(16))  # Counter and nonce positions

    if result == bytes(expected):
        print("  PASS: keysetup test")
        return True
    else:
        print("\n  FAIL: keysetup test")
        print(f"    Result:   {result.hex()}")
        print(f"    Expected: {expected.hex()}")
        return False


def test_component_ivsetup(uart):
    """Test chacha20_ietf_ivsetup component function.

    Returns:
        True if test passed, False otherwise
    """
    print("\n--- Testing chacha20_ietf_ivsetup ---")

    state = uart.test_keysetup(RFC8439_KEY)
    assert state, "Keysetup failed in ivsetup test"

    clear_buffers(uart)
    result = uart.test_ivsetup(state, RFC8439_NONCE)
    assert result and len(result) == 64, "Ivsetup: Invalid response"

    # Expected: state[0:48] unchanged, state[48:52]=0 (counter), state[52:64]=nonce
    expected = bytearray(state)
    expected[48:52] = (0).to_bytes(4, "little")
    expected[52:64] = RFC8439_NONCE

    if result == bytes(expected):
        print("  PASS: ivsetup test")
        return True
    else:
        print("\n  FAIL: ivsetup test")
        print(f"    Result:   {result.hex()}")
        print(f"    Expected: {expected.hex()}")
        return False


def test_component_encrypt_bytes(uart, length: int = 64):
    """Test chacha20_encrypt_bytes component function.

    Returns:
        True if test passed, False otherwise
    """
    print(f"\nTesting chacha20_encrypt_bytes ({length} bytes)...")

    # Build complete state
    state = uart.test_keysetup(RFC8439_KEY)
    assert state, "Keysetup failed in encrypt_bytes test"

    clear_buffers(uart)
    state = uart.test_ivsetup(state, RFC8439_NONCE)
    assert state, "Ivsetup failed in encrypt_bytes test"

    clear_buffers(uart)
    result = uart.test_encrypt_bytes(state, length)
    assert (
        result and len(result) == length
    ), f"Encrypt_bytes: Invalid response for {length} bytes"

    # Get expected keystream
    cipher = ChaCha20(RFC8439_KEY, RFC8439_NONCE, counter=0)
    expected = cipher.crypt(b"\x00" * length)

    if result == expected:
        print(f"  PASS: encrypt_bytes test ({length} bytes)")
        return True
    else:
        print(f"\n  FAIL: encrypt_bytes test ({length} bytes)")
        print(f"    Result:   {result.hex()[:80]}...")
        print(f"    Expected: {expected.hex()[:80]}...")
        show_mismatch(expected, result, length)
        return False


def test_column_round(uart, num_tests: int = 1):
    """Test column_round function.

    Returns:
        True if all tests passed, False otherwise
    """
    print(f"\nTesting {num_tests} column round operations...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate random state
        state = [random.randint(0, 0xFFFFFFFF) for _ in range(16)]
        state_bytes = u32_array_to_bytes(state)

        # Get expected result
        expected_state = column_round(state)
        expected_bytes = u32_array_to_bytes(expected_state)

        # Send to board
        uart_out = uart.test_column_round(state_bytes)
        assert (
            uart_out and len(uart_out) == 64
        ), f"Column round test {test_num + 1}: Invalid response"

        if uart_out != expected_bytes:
            print(f"\n  FAIL: Column round test {test_num + 1}")
            print(f"    Input state:    {state_bytes.hex()}")
            print(f"    Expected state: {expected_bytes.hex()}")
            print(f"    Got state:      {uart_out.hex()}")
            show_mismatch(expected_bytes, uart_out)
            return False

    return True


def test_diagonal_round(uart, num_tests: int = 1):
    """Test diagonal_round function.

    Returns:
        True if all tests passed, False otherwise
    """
    print(f"\nTesting {num_tests} diagonal round operations...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate random state
        state = [random.randint(0, 0xFFFFFFFF) for _ in range(16)]
        state_bytes = u32_array_to_bytes(state)

        # Get expected result
        expected_state = diagonal_round(state)
        expected_bytes = u32_array_to_bytes(expected_state)

        # Send to board
        uart_out = uart.test_diagonal_round(state_bytes)
        assert (
            uart_out and len(uart_out) == 64
        ), f"Diagonal round test {test_num + 1}: Invalid response"

        if uart_out != expected_bytes:
            print(f"\n  FAIL: Diagonal round test {test_num + 1}")
            print(f"    Input state:    {state_bytes.hex()}")
            print(f"    Expected state: {expected_bytes.hex()}")
            print(f"    Got state:      {uart_out.hex()}")
            show_mismatch(expected_bytes, uart_out)
            return False

    return True


def run_test_suite(uart):
    """Run the complete test suite.

    Tests are ordered from most elementary to most complex for easier debugging:
    1. Quarterround - most basic primitive operation
    2. Column/Diagonal rounds - use quarterround
    3. ChaCha20 block - uses column/diagonal rounds
    4. Component functions - keysetup, ivsetup (simple state setup)
    5. Encrypt_bytes - uses chacha20_block
    6. Keystream generation - complete end-to-end functionality (MANDATORY)

    Returns:
        dict: Test results with 'sections' (list of section results) and
              'final_test_passed' (bool)
    """
    tests = [
        (
            "Quarterround Tests (RFC 8439)",
            [
                lambda: test_quarterrounds(uart, rfc_mode=True),
            ],
            False,  # Not mandatory
        ),
        (
            "Quarterround Tests (Random)",
            [
                lambda: test_quarterrounds(uart, num_tests=NTESTS),
            ],
            False,  # Not mandatory
        ),
        (
            "Round Function Tests",
            [
                lambda: test_column_round(uart, num_tests=10),
                lambda: test_diagonal_round(uart, num_tests=10),
            ],
            False,  # Not mandatory
        ),
        (
            "ChaCha20 Block Tests (RFC 8439)",
            [
                lambda: test_chacha20_blocks(uart, rfc_mode=True),
            ],
            False,  # Not mandatory
        ),
        (
            "ChaCha20 Block Tests (Random)",
            [
                lambda: test_chacha20_blocks(uart, num_tests=NTESTS),
            ],
            False,  # Not mandatory
        ),
        (
            "Component Function Tests",
            [
                lambda: test_component_keysetup(uart),
                lambda: test_component_ivsetup(uart),
            ]
            + [
                lambda len=length: test_component_encrypt_bytes(uart, len)
                for length in [64, 128, 192, 256]
            ],
            False,  # Not mandatory
        ),
        (
            "Keystream Generation Tests",
            [
                lambda: test_keystream_generation(uart, num_tests=NTESTS, block_len=64),
                lambda: test_keystream_generation(
                    uart, num_tests=NTESTS, block_len=140
                ),
            ],
            True,  # MANDATORY - this is the final comprehensive test
        ),
    ]

    results = {"sections": [], "final_test_passed": False}

    for section_name, test_funcs, is_mandatory in tests:
        print(f"\n--- {section_name} ---")
        section_passed = True

        for test_func in test_funcs:
            try:
                test_passed = test_func()
                if not test_passed:
                    section_passed = False
            except Exception as e:
                print(f"ERROR: Test function raised exception: {e}")
                section_passed = False
            clear_buffers(uart, delay=0.5)

        results["sections"].append(
            {"name": section_name, "passed": section_passed, "mandatory": is_mandatory}
        )

        if is_mandatory:
            results["final_test_passed"] = section_passed

    return results


def main():
    """Main test entry point."""
    parser = argparse.ArgumentParser(description="Run ChaCha20 tests on board or QEMU")
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
    args = parser.parse_args()

    # Validate arguments
    if args.platform == "qemu" and not args.elf:
        print("ERROR: --elf required when using QEMU platform")
        print(
            "Usage: python test_chacha20.py --platform qemu --elf ../build/chacha20.elf"
        )
        return

    # Create platform connection
    try:
        if args.platform == "board":
            platform = get_platform("board", port=args.port, baudrate=38400)
        else:  # qemu
            platform = get_platform("qemu", elf_path=args.elf)

        # Wrap platform in ChaCha20-specific protocol
        uart = ChaCha20Protocol(platform)

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
    print(f"ChaCha20 {platform_name} Tests")
    print("=" * 60)

    try:
        results = run_test_suite(uart)

        # Print summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        # Show intermediate test results as warnings if they failed
        intermediate_failures = []
        for section in results["sections"]:
            if not section["mandatory"]:
                if section["passed"]:
                    print(f"  {section['name']}: PASS")
                else:
                    print(f"  {section['name']}: WARNING - Failed (optional)")
                    intermediate_failures.append(section["name"])

        # Show final mandatory test result
        for section in results["sections"]:
            if section["mandatory"]:
                if section["passed"]:
                    print(f"  {section['name']}: PASS (mandatory)")
                else:
                    print(f"  {section['name']}: FAIL (mandatory)")

        print("=" * 60)

        # Determine overall result based on final test
        if results["final_test_passed"]:
            print("\n" + "=" * 60)
            print("OVERALL: PASS")
            print("=" * 60)
            print("\nThe final comprehensive test (Keystream Generation) passed!")
            print("Your ChaCha20 implementation produces correct output.\n")

            if intermediate_failures:
                print("Note: Some intermediate tests failed, but these are optional.")
                print("The intermediate tests help guide implementation, but the final")
                print("keystream generation test is what matters for correctness.\n")
                print("Failed intermediate tests:")
                for failure in intermediate_failures:
                    print(f"  - {failure}")
                print()

            print("=" * 60)
            sys.exit(0)  # Success exit code
        else:
            print("\n" + "=" * 60)
            print("OVERALL: FAIL")
            print("=" * 60)
            print("\nThe final comprehensive test (Keystream Generation) failed.")
            print("Your implementation does not produce correct ChaCha20 output.\n")

            if not intermediate_failures:
                print("All intermediate tests passed, but the final test failed.")
                print("This suggests an issue in keystream generation logic.\n")
            else:
                print("Some intermediate tests also failed:")
                for failure in intermediate_failures:
                    print(f"  - {failure}")
                print("\nConsider fixing these components to help debug the issue.\n")

            print("=" * 60)
            sys.exit(1)  # Failure exit code

    except AssertionError as e:
        print(f"\nFAIL: Test suite failed with assertion error: {e}")
        print("This indicates a communication or protocol error with the device.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFAIL: Test suite failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        uart.disconnect()


if __name__ == "__main__":
    main()
