##############################################################################
# Playground 0: Print
##############################################################################

# Project configuration
TARGET = print-demo
SRC_DIR = src
BUILD_DIR = build
REPO_ROOT = ..

# Source files
SRCS = $(SRC_DIR)/main.c

# Object files
OBJS = $(SRC_DIR)/main.o

# Include common makefile
include $(REPO_ROOT)/common/Makefile.common

# Python tests
.PHONY: test-board test-qemu

test-board: flash
	@echo "Running board test..."
	@cd $(REPO_ROOT) && python3 playground0-print/tests/test.py

test-qemu:
	@echo "Running QEMU test..."
	@$(MAKE) PLATFORM=qemu clean all
	@cd $(REPO_ROOT) && python3 playground0-print/tests/test.py --platform qemu --elf playground0-print/$(BUILD_DIR)/$(TARGET).elf

# Help
help-playground:
	@echo "Playground 0: Print Demo"
	@echo ""
	@echo "This is a minimalistic demo that shows basic UART communication."
	@echo "The board sends a fixed string, and the Python script receives it."
	@echo ""
	@echo "Common targets:"
	@echo "  make                    - Build firmware for board"
	@echo "  make flash              - Flash to Nucleo board"
	@echo "  make test-board         - Test on actual board"
	@echo "  make test-qemu          - Test on QEMU (fast, no hardware needed)"
	@echo "  make clean              - Clean build files"
	@echo ""
	@echo "Development targets:"
	@echo "  make monitor            - Open serial monitor"
	@echo "  make debug              - Start debugging session"
