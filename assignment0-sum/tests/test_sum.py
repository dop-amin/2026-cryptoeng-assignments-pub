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
    from sum_protocol import SumProtocol, simple_prng
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    TESTS_DIR = os.path.dirname(__file__)
    if TESTS_DIR not in sys.path:
        sys.path.insert(0, TESTS_DIR)
    from sum_protocol import SumProtocol, simple_prng

NTESTS = 10
NINT = 1000


# Helper functions
def clear_buffers(uart, delay: float = 0.1):
    """Clear UART buffers with optional delay."""
    time.sleep(delay)
    # Only clear buffers if serial port exists (board platform)
    if hasattr(uart, "serial") and uart.serial:
        uart.serial.reset_input_buffer()
        uart.serial.reset_output_buffer()


def test_sum(uart, mode: str, num_tests: int = 1):
    """Test Sum operations using PRNG-generated data."""
    print(f"\nTesting {num_tests} {mode} operations...")

    for test_num in tqdm(range(num_tests)):
        if test_num > 0:
            clear_buffers(uart, delay=0.01)

        # Generate random seed
        seed = random.randint(1, 0xFFFFFFFF)

        # Use mod to prevent overflow: with NINT=1000 and mod=2^16,
        # max sum = 1000 * 65535 = 65,535,000 < 2^32
        mod = 2**16

        # Generate integers using PRNG with mod
        integers = simple_prng(seed, NINT, mod=mod)

        # Calculate expected sum (no overflow possible with this mod)
        expected_sum = sum(integers)

        # Send to board (seed + count + mod)
        uart_out = uart.test_sum(mode, seed, NINT, mod)

        assert (
            uart_out and len(uart_out) == 4
        ), f"{mode} test {test_num + 1}: Invalid response: {uart_out}"

        # Parse and verify
        result_sum = int.from_bytes(uart_out, "big")

        if result_sum != expected_sum:
            print(f"\n  FAIL: {mode} test {test_num + 1}")
            print(f"    Seed:     {seed:#010x}")
            print(f"    Count:    {NINT}")
            print(f"    Expected: {expected_sum:#010x}")
            print(f"    Got:      {result_sum:#010x}")
            assert False, f"{mode} test {test_num + 1} failed"


def run_test_suite(uart):
    """Run the complete test suite."""
    tests = [
        (
            "Sum C",
            [
                lambda: test_sum(uart, "SUM_C", num_tests=NTESTS),
            ],
        ),
        (
            "Sum Jasmin",
            [
                lambda: test_sum(uart, "SUM_JASMIN", num_tests=NTESTS),
            ],
        ),
        (
            "Sum Jasmin Fast",
            [
                lambda: test_sum(uart, "SUM_JASMIN_FAST", num_tests=NTESTS),
            ],
        ),
    ]

    for section_name, test_funcs in tests:
        print(f"\n--- {section_name} ---")
        for test_func in test_funcs:
            test_func()
            clear_buffers(uart, delay=0.5)


def main():
    """Main test entry point."""
    parser = argparse.ArgumentParser(description="Run Sum tests on board or QEMU")
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
        print("Usage: python test_sum.py --platform qemu --elf ../build/sum.elf")
        return

    # Create platform connection
    try:
        if args.platform == "board":
            platform = get_platform("board", port=args.port, baudrate=38400)
        else:  # qemu
            platform = get_platform("qemu", elf_path=args.elf)

        # Wrap platform in Sum-specific protocol
        uart = SumProtocol(platform)

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
    print(f"Sum {platform_name} Tests")
    print("=" * 60)

    try:
        run_test_suite(uart)

        print("\n" + "=" * 60)
        print("PASS: All tests passed!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\nFAIL: Test suite failed: {e}")
    finally:
        uart.disconnect()


if __name__ == "__main__":
    main()
