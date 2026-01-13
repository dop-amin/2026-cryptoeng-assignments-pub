##############################################################################
# Playground 2: Jasmin Demo
##############################################################################

# Project configuration
TARGET = jasmin-demo
SRC_DIR = src
BUILD_DIR = build
REPO_ROOT = ..

# Source files
SRCS = $(SRC_DIR)/main.c
SRCS += $(SRC_DIR)/myjasmin.s  # Generated from Jasmin

# Object files
OBJS = $(SRC_DIR)/main.o
OBJS += $(SRC_DIR)/myjasmin.o

# Include common makefile
include $(REPO_ROOT)/common/Makefile.common

# Jasmin compilation
$(SRC_DIR)/myjasmin.s: $(SRC_DIR)/myjasmin.jazz
	@echo "  JASMINC $<"
	@$(JASMINC) $(JASMINFLAGS) -o $@ $<

# Python tests
.PHONY: test-board test-qemu

test-board: flash
	@echo "Running board test..."
	@cd $(REPO_ROOT) && python3 playground2-jasmin/tests/test_jasmin.py

test-qemu:
	@echo "Running QEMU test..."
	@$(MAKE) PLATFORM=qemu clean all
	@cd $(REPO_ROOT) && python3 playground2-jasmin/tests/test_jasmin.py --platform qemu --elf playground2-jasmin/$(BUILD_DIR)/$(TARGET).elf

# Help
help-playground:
	@echo "Playground 2: Jasmin Demo"
	@echo ""
	@echo "This demo shows how to integrate a Jasmin function and benchmark it."
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
