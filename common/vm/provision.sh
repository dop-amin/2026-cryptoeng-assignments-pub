#!/bin/bash
#
# Provisioning script for Cryptographic Engineering VM
# Installs Nix and essential VM utilities
#
# Note: Development tools (ARM GCC, OpenOCD, QEMU, Jasmin, Python packages)
# are provided by the Nix flake and not installed via apt.
#

set -e

echo "================================"
echo "Cryptographic Engineering VM Setup"
echo "================================"

# Update package list
echo "[1/6] Updating package list..."
apt-get update -qq

# Install essential VM utilities only
echo "[2/6] Installing essential VM utilities..."
apt-get install -y \
    build-essential \
    git \
    curl \
    wget \
    vim \
    minicom \
    screen \
    linux-image-$(uname -r) \
    linux-modules-$(uname -r) \
    linux-modules-extra-$(uname -r)



# Note: The following are provided by Nix flake (see flake.nix):
#   - Jasmin compiler
#   - ARM GCC toolchain (gcc-arm-embedded from nixos-24.05)
#   - OpenOCD (for flashing)
#   - QEMU (for emulation)
#   - Python 3 with pyserial, tqdm, pytest

# Install Nix package manager
echo "[3/6] Installing Nix package manager..."
if [ ! -d "/nix" ]; then
    # Install Nix in multi-user mode
    curl -L https://nixos.org/nix/install | sh -s -- --daemon

    # Source nix profile
    if [ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
        . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
    fi
else
    echo "Nix already installed, skipping..."
fi

# Enable Nix flakes
echo "Enabling Nix flakes..."
mkdir -p /etc/nix
cat > /etc/nix/nix.conf << 'EOF'
experimental-features = nix-command flakes
EOF

# Note: Jasmin and all development tools will be available via 'nix develop'
# No need to install them globally

# Install VS Code (optional, for GUI users)
echo "[4/6] Installing Visual Studio Code..."
if ! command -v code &> /dev/null; then
    # Import Microsoft GPG key
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
    install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg

    # Add VS Code repository
    echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list

    rm -f packages.microsoft.gpg

    # Install VS Code
    apt-get update -qq
    apt-get install -y code

    # Install useful VS Code extensions (as vagrant user)
    su - vagrant -c 'code --install-extension ms-vscode.cpptools' || true
    su - vagrant -c 'code --install-extension ms-python.python' || true
else
    echo "VS Code already installed, skipping..."
fi

# Clone the course repository into the VM
echo "[5/6] Cloning course repository..."
if [ ! -d "/home/vagrant/cryptoeng" ]; then
    echo "Cloning repository from GitHub..."
    su - vagrant -c "git clone -b no-solution-squashed https://github.com/dop-amin/2026-cryptoeng-assignments-pub.git /home/vagrant/cryptoeng"

    if [ $? -eq 0 ]; then
        echo "Repository cloned successfully"
    else
        echo "ERROR: Failed to clone repository from https://github.com/dop-amin/2026-cryptoeng-assignments-pub.git"
        echo "Please ensure the VM has internet connectivity"
        exit 1
    fi
else
    echo "Repository already exists at /home/vagrant/cryptoeng"
fi

# Clone and build libopencm3
echo "[6/6] Setting up libopencm3..."
# Check if libopencm3 is configured as a git submodule
if [ -f "/home/vagrant/cryptoeng/.gitmodules" ] && grep -q "libopencm3" "/home/vagrant/cryptoeng/.gitmodules"; then
    echo "Initializing libopencm3 as git submodule..."
    cd /home/vagrant/cryptoeng
    su - vagrant -c "cd /home/vagrant/cryptoeng && git submodule update --init common/libopencm3"
elif [ ! -d "/home/vagrant/cryptoeng/common/libopencm3" ] || [ -z "$(ls -A /home/vagrant/cryptoeng/common/libopencm3)" ]; then
    echo "Cloning libopencm3..."
    cd /home/vagrant/cryptoeng/common
    su - vagrant -c "cd /home/vagrant/cryptoeng/common && git clone https://github.com/libopencm3/libopencm3.git"
else
    echo "libopencm3 already exists..."
fi

# Build libopencm3
echo "Building libopencm3..."
cd /home/vagrant/cryptoeng/common/libopencm3
# Source Nix and build inside the development environment
su - vagrant -c "cd /home/vagrant/cryptoeng && source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh && nix develop --command make -C common/libopencm3 TARGETS=stm32/l4 -j\$(nproc)"

# Set up udev rules for STM32 devices
echo "Setting up udev rules for STM32 devices..."
cat > /etc/udev/rules.d/99-stm32.rules << 'EOF'
# STM32 Discovery and Nucleo boards
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3748", MODE="0666", GROUP="dialout"
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="374b", MODE="0666", GROUP="dialout"
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="374e", MODE="0666", GROUP="dialout"
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="374f", MODE="0666", GROUP="dialout"
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3752", MODE="0666", GROUP="dialout"
ATTRS{idVendor}=="0483", ATTRS{idProduct}=="3753", MODE="0666", GROUP="dialout"
EOF

udevadm control --reload-rules
udevadm trigger

# Enable ACM CDC kernel module for USB serial devices
echo "Enabling ACM CDC module for USB serial communication..."
modprobe cdc_acm || echo "Warning: Could not load cdc_acm module (may load on reboot)"

# Ensure ACM CDC module loads on boot
echo "cdc_acm" >> /etc/modules

# Set up environment for Nix
echo "Setting up Nix environment..."
cat >> /etc/profile.d/nix.sh << 'EOF'
# Nix
if [ -e /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
    . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi
EOF

# Clean up
echo "Cleaning up..."
apt-get autoremove -y
apt-get clean

echo "================================"
echo "VM provisioning complete!"
echo "================================"
echo ""
echo "Installed via apt:"
echo "  - Git: $(git --version)"
echo "  - Nix package manager: installed"
echo "  - VS Code: $(code --version | head -n1 || echo 'not installed')"
echo ""
echo "Development tools (via Nix flake):"
echo "  To activate the development environment, run:"
echo "    cd ~/cryptoeng"
echo "    nix develop"
echo ""
echo "  This provides:"
echo "    - Jasmin compiler (jasminc)"
echo "    - ARM GCC toolchain (arm-none-eabi-gcc)"
echo "    - OpenOCD (for flashing)"
echo "    - QEMU (for emulation)"
echo "    - Python 3 with pyserial, tqdm, pytest"
echo ""
echo "Repository location:"
echo "  - Working copy: /home/vagrant/cryptoeng"
echo ""
echo "Please reboot the VM to complete setup:"
echo "  vagrant reload"
echo ""
echo "After reboot, enter the development environment:"
echo "  cd ~/cryptoeng"
echo "  nix develop"
echo ""
