##############################################################################
# Assignment 2: Ecdh25519's Scalar Multiplication Implementation
##############################################################################

# Project configuration
TARGET ?= smult
SRC_DIR = src
BUILD_DIR = build
REPO_ROOT = ..
CT ?= yes

# Source files
SRCS = $(SRC_DIR)/main.c
SRCS += $(SRC_DIR)/smult.s  # Generated from Jasmin
SRCS += $(SRC_DIR)/fe25519_wrapper.s  # Generated from Jasmin
SRCS += $(SRC_DIR)/ge25519_wrapper.s  # Generated from Jasmin
SRCS += $(SRC_DIR)/rd32/fe25519_rd32_wrapper.s  # Generated from Jasmin

# Object files
OBJS = $(SRC_DIR)/main.o
OBJS += $(SRC_DIR)/smult.o
OBJS += $(SRC_DIR)/fe25519_wrapper.o
OBJS += $(SRC_DIR)/ge25519_wrapper.o
OBJS += $(SRC_DIR)/rd32/fe25519_rd32_wrapper.o

# Include common makefile
include $(REPO_ROOT)/common/Makefile.common

# Assignment-specific rules

# Jasmin compilation for fe25519_wrapper
$(SRC_DIR)/fe25519_wrapper.s: $(SRC_DIR)/fe25519_wrapper.jazz
	@echo "  JASMINC $<"
	@$(JASMINC) $(JASMINFLAGS) -o $@ $<

$(SRC_DIR)/rd32/fe25519_rd32_wrapper.s: $(SRC_DIR)/rd32/fe25519_rd32_wrapper.jazz
	@echo "  JASMINC $<"
	@$(JASMINC) $(JASMINFLAGS) -o $@ $<

# Jasmin compilation for ge25519_wrapper
$(SRC_DIR)/ge25519_wrapper.s: $(SRC_DIR)/ge25519_wrapper.jazz
	@echo "  JASMINC $<"
	@$(JASMINC) $(JASMINFLAGS) -o $@ $<

# Jasmin compilation for smult
ifeq ($(CT), yes)
    SMULT_SRC = $(SRC_DIR)/smult_ct.jazz
else
    SMULT_SRC = $(SRC_DIR)/smult.jazz
endif

$(SRC_DIR)/smult.s: $(SMULT_SRC)
	@echo "  JASMINC $<"
	@$(JASMINC) $(JASMINFLAGS) -auto-spill -o $@ $<

# Safety checking
.PHONY: check-safety

check-safety:
	@echo "Running Jasmin safety checker..."
ifeq ($(CT), yes)
	@echo "  Checking crypto_scalarmult_wrapper (constant-time version)..."
	@$(JASMINC) -arch=arm-m4 -slice=crypto_scalarmult_wrapper -checksafety -safetyconfig $(SRC_DIR)/checker_config_crypto_scalarmult_wrapper.json $(SRC_DIR)/smult_ct.jazz > /dev/null
else
	@echo "  Checking crypto_scalarmult_wrapper (non-constant-time version)..."
	@$(JASMINC) -arch=arm-m4 -slice=crypto_scalarmult_wrapper -checksafety -safetyconfig $(SRC_DIR)/checker_config_crypto_scalarmult_wrapper.json $(SRC_DIR)/smult.jazz > /dev/null
endif
	@echo "  ✓ crypto_scalarmult_wrapper passed"
	@echo "✓ All safety checks passed!"

# Python tests
.PHONY: test-reference test-board test-qemu bench-board

test-reference:
	@echo "Running reference implementation tests..."
	@cd $(REPO_ROOT) && python3 assignment2-ecdh25519/tests/test_selftest.py

test-board: flash
	@echo "Running board tests for $(TARGET)..."
	@cd $(REPO_ROOT) && python3 assignment2-ecdh25519/tests/test_smult.py --test $(TARGET)

bench-board: flash
	@echo "Running board benchmarks..."
	@cd $(REPO_ROOT) && python3 assignment2-ecdh25519/tests/test_bench-smult.py

test-qemu:
	@echo "Running QEMU tests..."
	@$(MAKE) PLATFORM=qemu clean all
	@cd $(REPO_ROOT) && python3 assignment2-ecdh25519/tests/test_smult.py --platform qemu \
	--elf assignment2-ecdh25519/$(BUILD_DIR)/$(TARGET).elf --test $(TARGET)

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
	@echo "Ecdh25519's Scalar Multiplication Assignment Makefile"
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
