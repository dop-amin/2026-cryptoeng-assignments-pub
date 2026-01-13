import argparse
import os
import sys
import time

try:
    from common.testing.platform_interface import get_platform
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from common.testing.platform_interface import get_platform

try:
    from ecdh25519_protocol import Ecdh25519Protocol
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    TESTS_DIR = os.path.dirname(__file__)
    if TESTS_DIR not in sys.path:
        sys.path.insert(0, TESTS_DIR)
    from ecdh25519_protocol import Ecdh25519Protocol


def clear_buffers(uart, delay: float = 0.1):
    """Clear UART buffers with optional delay."""
    time.sleep(delay)
    # Only clear buffers if serial port exists (board platform)
    if hasattr(uart, "serial") and uart.serial:
        uart.serial.reset_input_buffer()
        uart.serial.reset_output_buffer()


def bench_crypto_scalarmult_base(uart, num_tests: int = 100):
    """Benchmark crypto_scalarmult_base function."""
    print(f"\nBenchmarking {num_tests} crypto_scalarmult_base...")
    clear_buffers(uart)

    # Send to board
    uart_out = uart.benchmark_crypto_scalarmult_base(num_tests)

    if uart_out is None:
        assert False, f"Error occurred: {uart_out}"

    cycles_per_block = uart_out / num_tests
    print(f"Total cycles: {uart_out}")
    print(f"Cycles per block: {cycles_per_block:.2f}")


def bench_fe25519_add_rd32(uart, num_tests: int = 100):
    """Benchmark fe25519_add_rd32 function."""
    print(f"\nBenchmarking {num_tests} fe25519_add_rd32...")
    clear_buffers(uart)

    # Send to board
    uart_out = uart.benchmark_fe25519_add_rd32(num_tests)

    if uart_out is None:
        assert False, f"Error occurred: {uart_out}"

    cycles_per_block = uart_out / num_tests
    print(f"Total cycles: {uart_out}")
    print(f"Cycles per block: {cycles_per_block:.2f}")


def bench_fe25519_mul_rd32(uart, num_tests: int = 100):
    """Benchmark fe25519_mul_rd32 function."""
    print(f"\nBenchmarking {num_tests} fe25519_mul_rd32...")
    clear_buffers(uart)

    # Send to board
    uart_out = uart.benchmark_fe25519_mul_rd32(num_tests)

    if uart_out is None:
        assert False, f"Error occurred: {uart_out}"

    cycles_per_block = uart_out / num_tests
    print(f"Total cycles: {uart_out}")
    print(f"Cycles per block: {cycles_per_block:.2f}")


def bench_fe25519_add_wrapper(uart, num_tests: int = 100):
    """Benchmark fe25519_add_wrapper function."""
    print(f"\nBenchmarking {num_tests} fe25519_add_wrapper...")
    clear_buffers(uart)

    # Send to board
    uart_out = uart.benchmark_fe25519_add_wrapper(num_tests)

    if uart_out is None:
        assert False, f"Error occurred: {uart_out}"

    cycles_per_block = uart_out / num_tests
    print(f"Total cycles: {uart_out}")
    print(f"Cycles per block: {cycles_per_block:.2f}")


def bench_fe25519_mul_wrapper(uart, num_tests: int = 100):
    """Benchmark fe25519_mul_wrapper function."""
    print(f"\nBenchmarking {num_tests} fe25519_mul_wrapper...")
    clear_buffers(uart)

    # Send to board
    uart_out = uart.benchmark_fe25519_mul_wrapper(num_tests)

    if uart_out is None:
        assert False, f"Error occurred: {uart_out}"

    cycles_per_block = uart_out / num_tests
    print(f"Total cycles: {uart_out}")
    print(f"Cycles per block: {cycles_per_block:.2f}")


def main():
    """Main benchmark entry point."""
    parser = argparse.ArgumentParser(
        description="Run Ecdh25519' smult benchmarks on board"
    )
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument(
        "--baudrate", type=int, default=38400, help="Baud rate (default: 38400)"
    )
    args = parser.parse_args()

    # Create platform connection (board only for benchmarking)
    try:
        platform = get_platform("board", port=args.port, baudrate=args.baudrate)
        uart = Ecdh25519Protocol(platform)
    except Exception as e:
        print(f"ERROR: Failed to create platform: {e}")
        return

    if not uart.connect():
        print("ERROR: Failed to connect to board")
        return

    print("Connected to board")
    clear_buffers(uart, delay=1.0)

    print("=" * 60)
    print("Ecdh25519's Scalar Multiplication Board Benchmark")
    print("=" * 60)

    try:
        print("\n--- crypto_scalarmult_base benchmark ---")
        bench_crypto_scalarmult_base(uart, num_tests=100)
        print("\n--- fe25519_add_rd32 benchmark ---")
        bench_fe25519_add_rd32(uart, num_tests=100)
        print("\n--- fe25519_mul_rd32 benchmark ---")
        bench_fe25519_mul_rd32(uart, num_tests=100)
        print("\n--- fe25519_add_wrapper benchmark ---")
        bench_fe25519_add_wrapper(uart, num_tests=100)
        print("\n--- fe25519_mul_wrapper benchmark ---")
        bench_fe25519_mul_wrapper(uart, num_tests=100)

        print("\n" + "=" * 60)
        print("PASS: All benchmarks completed successfully!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\nFAIL: Benchmark failed: {e}")
    finally:
        uart.disconnect()


if __name__ == "__main__":
    main()
