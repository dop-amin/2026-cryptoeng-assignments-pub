##############################################################################
# Assignment 0: Sum Implementation
##############################################################################

# Project configuration
TARGET = sum
SRC_DIR = src
BUILD_DIR = build
REPO_ROOT = ..

# Source files
SRCS = $(SRC_DIR)/main.c
SRCS += $(SRC_DIR)/sum_c.c
SRCS += $(SRC_DIR)/sum.s  # Generated from Jasmin

# Object files
OBJS = $(SRC_DIR)/main.o
OBJS += $(SRC_DIR)/sum_c.o
OBJS += $(SRC_DIR)/sum.o

# Include common makefile
include $(REPO_ROOT)/common/Makefile.common

# Assignment-specific rules

# Jasmin compilation for sum
$(SRC_DIR)/sum.s: $(SRC_DIR)/sum.jazz
	@echo "  JASMINC $<"
	@$(JASMINC) $(JASMINFLAGS) -o $@ $<

# Safety checking
.PHONY: check-safety

check-safety:
	@echo "Running Jasmin safety checker..."
	@echo "  Checking sum_jasmin..."
	@$(JASMINC) -arch=arm-m4 -slice=sum_jasmin -checksafety -safetyconfig $(SRC_DIR)/checker_config_sum_jasmin.json $(SRC_DIR)/sum.jazz > /dev/null
	@echo "  ✓ sum_jasmin passed"
	@echo "  Checking sum_jasmin_fast..."
	@$(JASMINC) -arch=arm-m4 -slice=sum_jasmin_fast -checksafety -safetyconfig $(SRC_DIR)/checker_config_sum_jasmin_fast.json $(SRC_DIR)/sum.jazz > /dev/null
	@echo "  ✓ sum_jasmin_fast passed"
	@echo "✓ All safety checks passed!"

# Python tests
.PHONY: test-board test-board-hello test-qemu bench-board

test-board-hello: flash
	@echo "Waiting for board..."
	@sleep 1
	@echo "Running hello world test on board..."
	@cd $(REPO_ROOT) && python3 assignment0-sum/tests/test_hello.py

test-board: flash
	@echo "Running board tests..."
	@cd $(REPO_ROOT) && python3 assignment0-sum/tests/test_sum.py

bench-board: flash
	@echo "Running board benchmarks..."
	@cd $(REPO_ROOT) && python3 assignment0-sum/tests/test_bench-sum.py

test-qemu:
	@echo "Running QEMU tests..."
	@$(MAKE) PLATFORM=qemu clean all
	@cd $(REPO_ROOT) && python3 assignment0-sum/tests/test_sum.py --platform qemu --elf assignment0-sum/$(BUILD_DIR)/$(TARGET).elf

# Submission
.PHONY: check-submission

check-submission:
	@echo "Checking submission requirements..."
	@echo "✓ Checking if code builds..."
	@$(MAKE) clean
	@$(MAKE) all
	@echo "✓ Build successful!"
	@echo "✓ Running tests..."
	@$(MAKE) test-board
	@echo "✓ Running safety checks..."
	@$(MAKE) check-safety
	@echo "✓ All checks passed!"

# Help
help-assignment:
	@echo "Sum Assignment Makefile"
	@echo ""
	@echo "Common targets:"
	@echo "  make                    - Build firmware for board"
	@echo "  make flash              - Flash to Nucleo board"
	@echo "  make test-board-hello   - Test communication"
	@echo "  make test-board         - Test on actual board"
	@echo "  make test-qemu          - Test on QEMU (fast, no hardware needed)"
	@echo "  make bench-board        - Flash and run benchmarks"
	@echo "  make clean              - Clean build files"
	@echo ""
	@echo "Development targets:"
	@echo "  make monitor      - Open serial monitor"
	@echo "  make debug        - Start debugging session"
