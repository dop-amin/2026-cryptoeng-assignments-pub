##############################################################################
# Assignment 1: ChaCha20 Implementation
##############################################################################

# Project configuration
TARGET = chacha20
SRC_DIR = src
BUILD_DIR = build
REPO_ROOT = ..

# Source files
SRCS = $(SRC_DIR)/main.c
SRCS += $(SRC_DIR)/chacha20.s  # Generated from Jasmin

# Object files
OBJS = $(SRC_DIR)/main.o
OBJS += $(SRC_DIR)/chacha20.o

# Include common makefile
include $(REPO_ROOT)/common/Makefile.common

# Assignment-specific rules

# Jasmin compilation for chacha20
$(SRC_DIR)/chacha20.s: $(SRC_DIR)/chacha20.jazz
	@echo "  JASMINC $<"
	@$(JASMINC) $(JASMINFLAGS) -o $@ $<

# Safety checking
.PHONY: check-safety

check-safety:
	@echo "Running Jasmin safety checker..."
	@echo "  Checking crypto_stream_chacha20_ietf..."
	@$(JASMINC) -arch=arm-m4 -slice=crypto_stream_chacha20_ietf -checksafety -safetyconfig $(SRC_DIR)/checker_config_crypto_stream_chacha20_ietf.json $(SRC_DIR)/chacha20.jazz > /dev/null
	@echo "  ✓ crypto_stream_chacha20_ietf passed"
	@echo "  Checking test_chacha20_encrypt_bytes..."
	@$(JASMINC) -arch=arm-m4 -slice=test_chacha20_encrypt_bytes -checksafety -safetyconfig $(SRC_DIR)/checker_config_test_chacha20_encrypt_bytes.json $(SRC_DIR)/chacha20.jazz > /dev/null
	@echo "  ✓ test_chacha20_encrypt_bytes passed"
	@echo "✓ All safety checks passed!"

# Python tests
.PHONY: test-reference test-board test-qemu bench-board

test-reference:
	@echo "Running reference implementation tests..."
	@cd $(REPO_ROOT) && python3 -m pytest assignment1-chacha20/tests/test_selftest.py -v

test-board: flash
	@echo "Running board tests..."
	@cd $(REPO_ROOT) && python3 assignment1-chacha20/tests/test_chacha20.py

bench-board: flash
	@echo "Running board benchmarks..."
	@cd $(REPO_ROOT) && python3 assignment1-chacha20/tests/test_bench-chacha20.py

test-qemu:
	@echo "Running QEMU tests..."
	@$(MAKE) PLATFORM=qemu clean all
	@cd $(REPO_ROOT) && python3 assignment1-chacha20/tests/test_chacha20.py --platform qemu --elf assignment1-chacha20/$(BUILD_DIR)/$(TARGET).elf

# Submission
.PHONY: check-submission

check-submission:
	@echo "Checking submission requirements..."
	@echo "✓ Checking if code builds..."
	@$(MAKE) clean
	@$(MAKE) all
	@echo "✓ Build successful!"
	@echo "✓ Running tests..."
	@$(MAKE) test-reference
	@$(MAKE) test-board
	@echo "✓ Running safety checks..."
	@$(MAKE) check-safety
	@echo "✓ All checks passed!"

# Help
help-assignment:
	@echo "ChaCha20 Assignment Makefile"
	@echo ""
	@echo "Common targets:"
	@echo "  make                    - Build firmware for board"
	@echo "  make flash              - Flash to Nucleo board"
	@echo "  make test-reference     - Run Python reference tests"
	@echo "  make test-board         - Test on actual board"
	@echo "  make test-qemu          - Test on QEMU (fast, no hardware needed)"
	@echo "  make bench-board        - Flash and run benchmarks"
	@echo "  make clean              - Clean build files"
	@echo ""
	@echo "Development targets:"
	@echo "  make monitor      - Open serial monitor"
	@echo "  make debug        - Start debugging session"
