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
    from chacha20_protocol import ChaCha20Protocol
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    TESTS_DIR = os.path.dirname(__file__)
    if TESTS_DIR not in sys.path:
        sys.path.insert(0, TESTS_DIR)
    from chacha20_protocol import ChaCha20Protocol


def clear_buffers(uart, delay: float = 0.1):
    """Clear UART buffers with optional delay."""
    time.sleep(delay)
    # Only clear buffers if serial port exists (board platform)
    if hasattr(uart, "serial") and uart.serial:
        uart.serial.reset_input_buffer()
        uart.serial.reset_output_buffer()


def bench_chacha20_block(uart, num_tests: int = 100):
    """Benchmark ChaCha20 block function."""
    print(f"\nBenchmarking {num_tests} ChaCha20 blocks...")
    clear_buffers(uart)

    # Send to board
    uart_out = uart.benchmark_block(num_tests)

    if uart_out is None:
        assert False, f"Error occurred: {uart_out}"

    cycles_per_block = uart_out / num_tests
    print(f"Total cycles: {uart_out}")
    print(f"Cycles per block: {cycles_per_block:.2f}")


def bench_chacha20_keystream(uart, num_tests: int = 100, length: int = 64):
    """Benchmark ChaCha20 IETF keystream generation."""
    print(f"\nBenchmarking {num_tests} keystream generations ({length} bytes each)...")
    clear_buffers(uart)

    # Send to board
    uart_out = uart.benchmark_keystream(num_tests, length)

    if uart_out is None:
        assert False, f"Error occurred: {uart_out}"

    cycles_per_call = uart_out / num_tests
    blocks_needed = (length + 63) // 64  # Round up to nearest block
    print(f"Total cycles: {uart_out}")
    print(f"Cycles per keystream call: {cycles_per_call:.2f}")
    print(f"Blocks needed per call: {blocks_needed}")
    if blocks_needed > 0:
        print(f"Cycles per block (estimated): {cycles_per_call / blocks_needed:.2f}")


def main():
    """Main benchmark entry point."""
    parser = argparse.ArgumentParser(description="Run ChaCha20 benchmarks on board")
    parser.add_argument("--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument(
        "--baudrate", type=int, default=38400, help="Baud rate (default: 38400)"
    )
    args = parser.parse_args()

    # Create platform connection (board only for benchmarking)
    try:
        platform = get_platform("board", port=args.port, baudrate=args.baudrate)
        uart = ChaCha20Protocol(platform)
    except Exception as e:
        print(f"ERROR: Failed to create platform: {e}")
        return

    if not uart.connect():
        print("ERROR: Failed to connect to board")
        return

    print("Connected to board")
    clear_buffers(uart, delay=1.0)

    print("=" * 60)
    print("ChaCha20 Board Benchmark")
    print("=" * 60)

    try:
        # Benchmark ChaCha20 block function
        print("\n--- ChaCha20 Block Benchmark ---")
        bench_chacha20_block(uart, num_tests=100)

        # Benchmark keystream generation with different lengths
        print("\n--- Keystream Generation Benchmarks ---")
        bench_chacha20_keystream(uart, num_tests=100, length=64)  # 1 block
        bench_chacha20_keystream(uart, num_tests=100, length=128)  # 2 blocks
        bench_chacha20_keystream(uart, num_tests=100, length=256)  # 4 blocks

        print("\n" + "=" * 60)
        print("PASS: All benchmarks completed successfully!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\nFAIL: Benchmark failed: {e}")
    finally:
        uart.disconnect()


if __name__ == "__main__":
    main()
