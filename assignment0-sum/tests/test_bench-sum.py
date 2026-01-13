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
    from sum_protocol import SumProtocol
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    TESTS_DIR = os.path.dirname(__file__)
    if TESTS_DIR not in sys.path:
        sys.path.insert(0, TESTS_DIR)
    from sum_protocol import SumProtocol


def clear_buffers(uart, delay: float = 0.1):
    """Clear UART buffers with optional delay."""
    time.sleep(delay)
    # Only clear buffers if serial port exists (board platform)
    if hasattr(uart, "serial") and uart.serial:
        uart.serial.reset_input_buffer()
        uart.serial.reset_output_buffer()


def bench_sum(uart, mode: str, num_tests: int = 1000):
    """Benchmark sum function."""
    print(f"\nBenchmarking {num_tests} {mode} operations...")
    clear_buffers(uart)

    # Send to board
    uart_out = uart.benchmark_sum(mode, num_tests)

    if uart_out is None:
        assert False, f"Error occurred: {uart_out}"

    cycles_per_call = uart_out / num_tests
    print(f"Total cycles: {uart_out}")
    print(f"Cycles per sum call: {cycles_per_call:.2f}")


def main():
    """Main benchmark entry point."""
    parser = argparse.ArgumentParser(description="Run Sum benchmarks on board")
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument(
        "--baudrate", type=int, default=38400, help="Baud rate (default: 38400)"
    )
    args = parser.parse_args()

    # Create platform connection (board only for benchmarking)
    try:
        platform = get_platform("board", port=args.port, baudrate=args.baudrate)
        uart = SumProtocol(platform)
    except Exception as e:
        print(f"ERROR: Failed to create platform: {e}")
        return

    if not uart.connect():
        print("ERROR: Failed to connect to board")
        return

    print("Connected to board")
    clear_buffers(uart, delay=1.0)

    print("=" * 60)
    print("Sum Board Benchmark")
    print("=" * 60)

    try:
        # Benchmark SUM_C
        print("\n--- SUM_C Benchmark ---")
        bench_sum(uart, "SUM_C", num_tests=1000)

        # Benchmark SUM_JASMIN
        print("\n--- SUM_JASMIN Benchmark ---")
        bench_sum(uart, "SUM_JASMIN", num_tests=1000)

        # Benchmark SUM_JASMIN_FAST
        print("\n--- SUM_JASMIN_FAST Benchmark ---")
        bench_sum(uart, "SUM_JASMIN_FAST", num_tests=1000)

        print("\n" + "=" * 60)
        print("PASS: All benchmarks completed successfully!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\nFAIL: Benchmark failed: {e}")
    finally:
        uart.disconnect()


if __name__ == "__main__":
    main()
