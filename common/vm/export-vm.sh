#!/bin/bash
#
# VM Export Script for Course Instructors
# Exports the provisioned VirtualBox VM to OVA format for student distribution
#
# This script is designed to work with the VM created by Vagrantfile
# Based on: ubuntu/jammy64 box with VirtualBox provider
#

set -e

# Configuration - must match Vagrantfile
VM_NAME="Cryptographic Engineering VM"
OUTPUT_DIR="$(pwd)/vm-export"
TIMESTAMP=$(date +%Y%m%d)
OUTPUT_FILE="CryptoEngineering-VM-v${TIMESTAMP}.ova"

# VM specifications from Vagrantfile
VM_MEMORY="4096"
VM_CPUS="2"
VM_BASE_BOX="ubuntu/jammy64"

echo "========================================"
echo "VM Export Script (For Instructors)"
echo "========================================"
echo ""
echo "VM Configuration:"
echo "  Name: ${VM_NAME}"
echo "  Base: ${VM_BASE_BOX}"
echo "  Memory: ${VM_MEMORY} MB"
echo "  CPUs: ${VM_CPUS}"
echo ""

# Check if VBoxManage is available
if ! command -v VBoxManage &> /dev/null; then
    echo "ERROR: VBoxManage not found. Please install VirtualBox."
    exit 1
fi

# Check if VM exists
if ! VBoxManage list vms | grep -q "\"${VM_NAME}\""; then
    echo "ERROR: VM '${VM_NAME}' not found in VirtualBox."
    echo ""
    echo "Available VMs:"
    VBoxManage list vms
    echo ""
    echo "Please ensure the VM is created and provisioned first:"
    echo "  cd common/vm"
    echo "  vagrant up"
    echo "  vagrant halt"
    exit 1
fi

# Get VM state
echo "Checking VM state..."
VM_STATE=$(VBoxManage showvminfo "${VM_NAME}" --machinereadable | grep "VMState=" | cut -d'"' -f2)
echo "Current VM state: ${VM_STATE}"

# Ensure VM is powered off
if [ "${VM_STATE}" != "poweroff" ]; then
    echo ""
    echo "WARNING: VM must be powered off before export."
    echo "Current state: ${VM_STATE}"
    echo ""
    read -p "Shut down the VM now? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Shutting down VM gracefully..."
        VBoxManage controlvm "${VM_NAME}" acpipowerbutton 2>/dev/null || true
        echo "Waiting for shutdown (max 60 seconds)..."

        for i in {1..12}; do
            sleep 5
            VM_STATE=$(VBoxManage showvminfo "${VM_NAME}" --machinereadable | grep "VMState=" | cut -d'"' -f2)
            if [ "${VM_STATE}" = "poweroff" ]; then
                echo "VM shut down successfully."
                break
            fi
            echo "  Still waiting... (${i}/12)"
        done

        # Force power off if still running
        VM_STATE=$(VBoxManage showvminfo "${VM_NAME}" --machinereadable | grep "VMState=" | cut -d'"' -f2)
        if [ "${VM_STATE}" != "poweroff" ]; then
            echo "Forcing power off..."
            VBoxManage controlvm "${VM_NAME}" poweroff
            sleep 3
        fi
    else
        echo "Please shut down the VM manually:"
        echo "  vagrant halt"
        echo "Then run this script again."
        exit 1
    fi
fi

# Create output directory
mkdir -p "${OUTPUT_DIR}"

echo ""
echo "===> Step 1: Detecting VM configuration and optimizing disk"
echo ""

# Get VM information
VM_INFO=$(VBoxManage showvminfo "${VM_NAME}" --machinereadable)
VM_UUID=$(echo "$VM_INFO" | grep "^UUID=" | head -n1 | cut -d'"' -f2)

# Find storage controllers and their attached disks
echo "Detecting storage controllers..."
STORAGE_CONTROLLERS=$(echo "$VM_INFO" | grep "^storagecontrollername" | cut -d'"' -f2)

if [ -z "$STORAGE_CONTROLLERS" ]; then
    echo "  WARNING: No storage controllers found"
else
    while IFS= read -r controller; do
        echo "  Found controller: $controller"
    done <<< "$STORAGE_CONTROLLERS"
fi

# Find all attached disks (ubuntu/jammy64 typically uses SCSI)
# Pattern matches: "SCSI-0-0", "SATA-0-0", "IDE-0-0", etc.
echo ""
echo "Detecting attached disks..."
DISK_LINES=$(echo "$VM_INFO" | grep -E "(SCSI|SATA|IDE)-[0-9]+-[0-9]+" | grep -v "none")

if [ -z "$DISK_LINES" ]; then
    echo "  WARNING: No disks found attached to VM"
    echo "  Skipping disk optimization"
else
    # Get first disk
    FIRST_DISK=$(echo "$DISK_LINES" | head -n1)
    DISK_UUID=$(echo "$FIRST_DISK" | cut -d'"' -f2)
    CONTROLLER_INFO=$(echo "$FIRST_DISK" | cut -d'=' -f1)

    echo "  Primary disk: $DISK_UUID"
    echo "  Controller port: $CONTROLLER_INFO"

    # Attempt to compact disk (only works for VDI format)
    echo ""
    echo "Attempting to compact disk..."
    echo "  Note: This only works for VDI format disks"
    echo "  VMDK disks will show an error (this is normal)"
    echo ""

    if VBoxManage modifymedium disk "${DISK_UUID}" --compact; then
        echo "  SUCCESS: Disk compacted"
    else
        echo "  INFO: Disk compacting not supported (likely VMDK format)"
        echo "  This is expected for Vagrant boxes - continuing..."
    fi
fi

echo ""
echo "===> Step 2: Exporting VM to OVA format"
echo ""
echo "Output file: ${OUTPUT_DIR}/${OUTPUT_FILE}"
echo ""
echo "This may take 5-15 minutes depending on VM size..."
echo "Progress will be shown by VBoxManage..."
echo ""

# Export the VM with metadata matching the Vagrantfile configuration
# OVF 2.0 format for better compatibility
VBoxManage export "${VM_NAME}" \
    --output "${OUTPUT_DIR}/${OUTPUT_FILE}" \
    --ovf20 \
    --manifest \
    --vsys 0 \
    --product "Cryptographic Engineering VM" \
    --vendor "Cryptographic Engineering Course" \
    --version "1.0-${TIMESTAMP}" \
    --description "Pre-configured Ubuntu 22.04 VM for Cryptographic Engineering course. Includes Nix package manager, Jasmin compiler, ARM GCC toolchain, OpenOCD, QEMU, Python tools, and libopencm3. Ready for ChaCha20 and Ecdh25519 assignments on STM32 Nucleo-L4R5ZI. Login: vagrant/vagrant. First time: cd ~/cryptoeng && nix develop"

EXPORT_STATUS=$?
if [ $EXPORT_STATUS -ne 0 ]; then
    echo ""
    echo "ERROR: Export failed with status code ${EXPORT_STATUS}"
    echo ""
    echo "Common causes:"
    echo "  - Not enough disk space in ${OUTPUT_DIR}"
    echo "  - VM is locked by another process"
    echo "  - Insufficient permissions"
    exit 1
fi

echo ""
echo "Export completed successfully!"

# Get file info
FILE_SIZE=$(du -h "${OUTPUT_DIR}/${OUTPUT_FILE}" | cut -f1)
FILE_SIZE_BYTES=$(stat -f%z "${OUTPUT_DIR}/${OUTPUT_FILE}" 2>/dev/null || stat -c%s "${OUTPUT_DIR}/${OUTPUT_FILE}" 2>/dev/null)

echo ""
echo "===> Step 3: Creating checksums"
echo ""

# Create SHA256 checksum
cd "${OUTPUT_DIR}"
shasum -a 256 "${OUTPUT_FILE}" > "${OUTPUT_FILE}.sha256"
echo "Created: ${OUTPUT_FILE}.sha256"

# Create MD5 checksum (for compatibility)
md5sum "${OUTPUT_FILE}" > "${OUTPUT_FILE}.md5" 2>/dev/null || md5 -r "${OUTPUT_FILE}" | awk '{print $1 "  " $2}' > "${OUTPUT_FILE}.md5"
echo "Created: ${OUTPUT_FILE}.md5"

cd - > /dev/null

echo ""
echo "===> Step 4: Creating student documentation"
echo ""

# Create import instructions
cat > "${OUTPUT_DIR}/IMPORT-INSTRUCTIONS.txt" << 'EOF'
================================================================================
CRYPTOGRAPHIC ENGINEERING VM - IMPORT INSTRUCTIONS
================================================================================

REQUIREMENTS
------------
- VirtualBox 6.1+ with Extension Pack: https://www.virtualbox.org/wiki/Downloads
- 8GB RAM (VM uses 4GB), 20GB disk space
- Host user must be in 'vboxusers' group (Linux/Mac):
    sudo usermod -a -G vboxusers $USER
    (logout and login for changes to take effect)

IMPORT
------
VirtualBox > File > Import Appliance > Select .ova file

LOGIN
-----
Username: vagrant
Password: vagrant

FIRST TIME
----------
cd ~/cryptoeng
nix develop

USB (for Nucleo board)
----------------------
Devices > USB > STMicroelectronics STM32 STLink

See README files in ~/cryptoeng for detailed instructions and troubleshooting.

================================================================================
EOF

echo "Created: ${OUTPUT_DIR}/IMPORT-INSTRUCTIONS.txt"

# Create quick reference card
cat > "${OUTPUT_DIR}/QUICK-REFERENCE.txt" << 'EOF'
================================================================================
QUICK REFERENCE
================================================================================

Login: vagrant / vagrant

First time:
  cd ~/cryptoeng && nix develop

Build & flash:
  make clean && make
  make flash
  python3 board_test.py

USB: Devices > USB > STMicroelectronics STM32 STLink

See README.md files in repository for full documentation.

================================================================================
EOF

echo "Created: ${OUTPUT_DIR}/QUICK-REFERENCE.txt"

# Create release notes
cat > "${OUTPUT_DIR}/RELEASE-NOTES.txt" << EOF
================================================================================
CRYPTOGRAPHIC ENGINEERING VM - RELEASE NOTES
================================================================================

Version: ${TIMESTAMP}
Build Date: $(date +"%Y-%m-%d %H:%M:%S")

CONTENTS
--------
This VM includes:
- Ubuntu 22.04 LTS (Jammy Jellyfish)
- Nix package manager with development flake
- Jasmin compiler (latest)
- ARM GCC toolchain (arm-none-eabi-gcc)
- OpenOCD (for flashing STM32 boards)
- QEMU (for ARM emulation)
- Python 3 with pyserial, tqdm, pytest
- libopencm3 (pre-built for STM32L4)
- Course assignments repository

VM SPECIFICATIONS
-----------------
- Memory: 4GB RAM (adjustable)
- CPUs: 2 cores (adjustable)
- Disk: ~15-20GB (dynamically allocated)
- USB: Enabled with STM32 filters configured
- GUI: Enabled
- Clipboard: Bidirectional sharing enabled

CREDENTIALS
-----------
Username: vagrant
Password: vagrant
(user has sudo access)

FILE STRUCTURE
--------------
/home/vagrant/cryptoeng/          - Course repository
  ├── assignment0-sum/            - Warmup assignment (integer summation)
  ├── assignment1-chacha20/       - ChaCha20 implementation
  ├── assignment2-ecdh25519/      - Ecdh25519 implementation
  └── common/
      ├── libopencm3/             - Pre-built ARM library
      └── target/                 - Board configuration

DISTRIBUTION FILES
------------------
$(basename ${OUTPUT_FILE})         - Main VM image (OVA format)
$(basename ${OUTPUT_FILE}).sha256  - SHA256 checksum
$(basename ${OUTPUT_FILE}).md5     - MD5 checksum
QUICK-REFERENCE.txt                - Command reference
RELEASE-NOTES.txt                  - This file

FILE SIZE
---------
$(basename ${OUTPUT_FILE}): ${FILE_SIZE}

CHECKSUM (SHA256)
-----------------
$(cat "${OUTPUT_DIR}/${OUTPUT_FILE}.sha256")

TESTING CHECKLIST FOR INSTRUCTORS
----------------------------------
Before distributing to students, verify:
[ ] VM boots successfully
[ ] Login works (vagrant/vagrant)
[ ] nix develop activates successfully
[ ] jasminc command works
[ ] arm-none-eabi-gcc command works
[ ] Can build assignment1: make clean && make
[ ] USB pass-through works with Nucleo board
[ ] make flash successfully programs board
[ ] Python test scripts run correctly
[ ] Serial communication works

================================================================================
Generated: $(date)
================================================================================
EOF

echo "Created: ${OUTPUT_DIR}/RELEASE-NOTES.txt"

echo ""
echo "========================================"
echo "Export Complete!"
echo "========================================"
echo ""
echo "Distribution package: ${OUTPUT_DIR}/"
echo ""
echo "Files created:"
echo "  $(basename ${OUTPUT_FILE}) (${FILE_SIZE})"
echo "  $(basename ${OUTPUT_FILE}).sha256"
echo "  $(basename ${OUTPUT_FILE}).md5"
echo "  IMPORT-INSTRUCTIONS.txt"
echo "  QUICK-REFERENCE.txt"
echo "  RELEASE-NOTES.txt"
echo ""
echo "Next steps:"
echo "  1. Test: Import OVA and verify (see RELEASE-NOTES.txt checklist)"
echo "  2. Verify checksum: cd ${OUTPUT_DIR} && shasum -a 256 -c $(basename ${OUTPUT_FILE}).sha256"
echo "  3. Distribute: Upload to file sharing service"
echo ""
echo "Students need:"
echo "  - VirtualBox 6.1+ with Extension Pack"
echo "  - User in 'vboxusers' group (Linux/Mac)"
echo "  - IMPORT-INSTRUCTIONS.txt file"
echo ""
