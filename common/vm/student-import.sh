#!/bin/bash
#
# Student VM Import Helper Script
# Helps verify VirtualBox installation and guides through import process
#

set -e

echo "========================================="
echo "Cryptographic Engineering VM"
echo "Student Import Helper"
echo "========================================="
echo ""

# Check if VirtualBox is installed
if ! command -v VBoxManage &> /dev/null; then
    echo "ERROR: VirtualBox is not installed or not in PATH"
    echo ""
    echo "Please install VirtualBox first:"
    echo "  1. Visit: https://www.virtualbox.org/wiki/Downloads"
    echo "  2. Download VirtualBox for your operating system"
    echo "  3. Install VirtualBox"
    echo "  4. Install the VirtualBox Extension Pack (same download page)"
    echo "  5. Run this script again"
    echo ""
    exit 1
fi

VBOX_VERSION=$(VBoxManage --version | cut -d'r' -f1)
echo "[OK] VirtualBox is installed (version: ${VBOX_VERSION})"

# Check if Extension Pack is installed
EXTPACK_COUNT=$(VBoxManage list extpacks | grep -c "Oracle VM VirtualBox Extension Pack" || echo "0")
if [ "${EXTPACK_COUNT}" -eq "0" ]; then
    echo "[WARNING] VirtualBox Extension Pack is NOT installed"
    echo ""
    echo "The Extension Pack is required for USB device support (Nucleo board)."
    echo ""
    echo "To install:"
    echo "  1. Download from: https://www.virtualbox.org/wiki/Downloads"
    echo "  2. Double-click the downloaded file, OR"
    echo "  3. VirtualBox > Preferences > Extensions > Add button"
    echo ""
    echo "You can continue without it, but USB won't work."
    echo ""
else
    echo "[OK] VirtualBox Extension Pack is installed"
fi

echo ""
echo "System check:"
echo "  CPU cores: $(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 'unknown')"
echo "  Available RAM: $(free -h 2>/dev/null | grep Mem | awk '{print $7}' || echo 'unknown')"
echo ""

# Find .ova files in current directory
OVA_FILES=$(find . -maxdepth 1 -name "*.ova" -type f 2>/dev/null)
OVA_COUNT=$(echo "$OVA_FILES" | grep -c ".ova" || echo "0")

if [ "${OVA_COUNT}" -eq "0" ]; then
    echo "No .ova file found in current directory."
    echo ""
    echo "Please:"
    echo "  1. Download the CryptoEngineering-VM-*.ova file"
    echo "  2. Place it in the same directory as this script"
    echo "  3. Run this script again"
    echo ""
    exit 1
elif [ "${OVA_COUNT}" -eq "1" ]; then
    OVA_FILE=$(echo "$OVA_FILES" | head -n1)
    echo "Found VM file: $(basename $OVA_FILE)"

    # Get file size
    FILE_SIZE=$(du -h "$OVA_FILE" | cut -f1)
    echo "  Size: ${FILE_SIZE}"

    # Check if checksum file exists
    if [ -f "${OVA_FILE}.sha256" ]; then
        echo ""
        echo "Verifying checksum..."
        if shasum -a 256 -c "${OVA_FILE}.sha256" 2>/dev/null; then
            echo "[OK] Checksum verified successfully"
        else
            echo "[WARNING] Checksum verification failed!"
            echo "The file may be corrupted. Consider re-downloading."
            echo ""
            read -p "Continue anyway? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    echo ""
    echo "Ready to import!"
    echo ""
    echo "Choose import method:"
    echo "  1. Automatic import (recommended)"
    echo "  2. Manual import (open VirtualBox GUI)"
    echo "  3. Exit"
    echo ""
    read -p "Enter choice (1-3): " choice

    case $choice in
        1)
            echo ""
            echo "Starting automatic import..."
            echo "This may take 5-15 minutes."
            echo ""

            VBoxManage import "$OVA_FILE" --vsys 0 --vmname "Cryptographic Engineering VM"

            if [ $? -eq 0 ]; then
                echo ""
                echo "Import successful!"
                echo ""
                echo "Next: Start VM in VirtualBox"
                echo "Login: vagrant / vagrant"
                echo "First time: cd ~/cryptoeng && nix develop"
                echo ""
            else
                echo ""
                echo "Import failed. Try manual import instead."
                exit 1
            fi
            ;;
        2)
            echo ""
            echo "Manual: VirtualBox > File > Import Appliance > Select OVA"
            echo "After import: Start VM, login vagrant/vagrant"
            echo "First time: cd ~/cryptoeng && nix develop"
            echo ""
            ;;
        3)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid choice."
            exit 1
            ;;
    esac
else
    echo "Multiple .ova files found:"
    echo "$OVA_FILES"
    echo ""
    echo "Please keep only one .ova file in this directory and run again."
    exit 1
fi
