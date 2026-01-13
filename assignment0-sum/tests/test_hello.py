#!/usr/bin/env python3
"""
Hello World test for assignment0-sum

Tests basic UART communication by sending a TEST_HELLO command.
This validates that the platform connection works correctly.
"""

import argparse
import os
import sys

try:
    from common.testing.platform_interface import get_platform
    from common.testing.command_protocol import CommandProtocol
except ModuleNotFoundError:  # pragma: no cover - fallback for ad-hoc execution
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from common.testing.platform_interface import get_platform
    from common.testing.command_protocol import CommandProtocol


def test_helloworld(protocol):
    """Test basic UART communication with TEST_HELLO command."""
    print("Testing UART communication...")

    res = protocol.send_command("TEST_HELLO Hello Nucleo!")

    if not res:
        print("ERROR: No response from platform")
        return False

    if res == "Hello host!":
        print(f"SUCCESS: Received expected response: '{res}'")
        return True
    else:
        print(f"ERROR: Unexpected response: '{res}'")
        print("       Expected: 'Hello host!'")
        return False


def main():
    """Main test entry point."""
    parser = argparse.ArgumentParser(description="Test UART communication")
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
        print("Usage: python test_hello.py --platform qemu --elf ../build/sum.elf")
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
        protocol = CommandProtocol(platform)

    except Exception as e:
        print(f"ERROR: Failed to create platform: {e}")
        sys.exit(1)

    # Run test
    with protocol:
        print(f"Connected to {args.platform}")
        print("=" * 60)
        print("Hello World Test")
        print("=" * 60)

        success = test_helloworld(protocol)

        print("=" * 60)
        if success:
            print("PASS: Hello world test passed!")
        else:
            print("FAIL: Hello world test failed!")
        print("=" * 60)

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
