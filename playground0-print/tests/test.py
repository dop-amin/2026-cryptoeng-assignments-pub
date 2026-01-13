#!/usr/bin/env python3
"""
Playground 0: Print Demo Test

This is a minimalistic demo that just reads and prints output from the board.
The board sends a fixed string over UART, and this script receives and displays it.
"""

import argparse
import os
import sys
import time

try:
    from common.testing.platform_interface import get_platform
except ModuleNotFoundError:
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from common.testing.platform_interface import get_platform


def read_board_output(platform, timeout=2.0):
    """
    Read output from the board until no more data is received.

    Args:
        platform: Platform instance (board or qemu)
        timeout: How long to wait for more data (seconds)

    Returns:
        List of output lines
    """
    lines = []

    if hasattr(platform, "serial") and platform.serial:
        # Board platform - read from serial
        platform.serial.timeout = timeout
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                line = (
                    platform.serial.readline().decode("ascii", errors="ignore").strip()
                )
                if line:
                    lines.append(line)
                    start_time = time.time()  # Reset timer when we get data
            except Exception as e:
                print(f"Error reading from serial: {e}")
                break

    elif hasattr(platform, "socket") and platform.socket:
        # QEMU platform - read from socket
        platform.socket.settimeout(0.1)
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                line_bytes = b""
                while True:
                    byte = platform.socket.recv(1)
                    if not byte:
                        break
                    if byte == b"\n":
                        break
                    line_bytes += byte

                line = line_bytes.decode("ascii", errors="ignore").strip()
                if line:
                    lines.append(line)
                    start_time = time.time()  # Reset timer when we get data

            except Exception:
                # Timeout or connection closed
                if time.time() - start_time >= timeout:
                    break

    return lines


def main():
    """Main test entry point."""
    parser = argparse.ArgumentParser(description="Playground 0: Print Demo")
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
        "--baudrate", type=int, default=38400, help="Baud rate (default: 38400)"
    )
    args = parser.parse_args()

    # Validate arguments
    if args.platform == "qemu" and not args.elf:
        print("ERROR: --elf required when using QEMU platform")
        print("Usage: python test.py --platform qemu --elf ../build/sum.elf")
        sys.exit(1)

    # Create platform connection
    try:
        kwargs = {}
        if args.platform == "board":
            if args.port:
                kwargs["port"] = args.port
            kwargs["baudrate"] = args.baudrate
        else:  # qemu
            kwargs["elf_path"] = args.elf

        platform = get_platform(args.platform, **kwargs)

    except Exception as e:
        print(f"ERROR: Failed to create platform: {e}")
        sys.exit(1)

    # Connect and read output
    if not platform.connect():
        print(f"ERROR: Failed to connect to {args.platform}")
        sys.exit(1)

    try:
        platform_name = "Board" if args.platform == "board" else "QEMU"
        print(f"Connected to {platform_name}")
        print("=" * 60)
        print("Reading output from board...")
        print("=" * 60)
        print()

        # Wait a moment for the board to initialize
        time.sleep(0.5)

        # Read all output
        lines = read_board_output(platform, timeout=2.0)

        if not lines:
            print("WARNING: No output received from board")
            sys.exit(1)

        # Print all received lines
        for line in lines:
            print(line)

        print()
        print("=" * 60)
        print("PASS: Successfully received output from board!")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    finally:
        platform.disconnect()


if __name__ == "__main__":
    main()
