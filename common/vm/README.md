# Virtual Machine Setup

## For Instructors

Build and export VM for students:
```bash
vagrant up
vagrant halt
./export-vm.sh
```

Output: `vm-export/` directory with OVA and documentation.

## For Students

VirtualBox > File > Import Appliance

Login: `vagrant` / `vagrant`

First time setup:
```bash
cd ~/cryptoeng
nix develop
```

### Connecting through SSH
1. Run the `allow_ssh.sh` script *inside the VM* using `sudo ./allow_ssh.sh`.
2. Add the content of `ssh_conf.sample` to your local SSH config, commonly under
   `~/.ssh/config`.
3. Connect to the VM using `ssh vagrant-local` or open it as a remote host in VS
   Code. 

---

## Development Setup (Detailed)

This directory contains the Vagrant configuration for setting up a development
environment for the Cryptographic Engineering assignments.

## Prerequisites

Before starting, you need to install:

1. **VirtualBox**: Download from [virtualbox.org](https://www.virtualbox.org/wiki/Downloads)
   - Version 7 or later recommended
   - **IMPORTANT**: Add your user to the `vboxusers` group for USB passthrough:
     ```bash
     # Linux/Mac
     sudo usermod -a -G vboxusers $USER

     # Then logout and login again for changes to take effect
     ```
     On Windows, USB passthrough requires VirtualBox Extension Pack only.

2. **Vagrant**: Download from [vagrantup.com](https://www.vagrantup.com/downloads)
   - Version 2.2 or later recommended

## Quick Start

### 1. Initial Setup

From the root of the repository:

```bash
cd common/vm
vagrant up
```

This will:
- Download Ubuntu 22.04 base box (~600 MB)
- Copy the repository into the VM (from shared folder to native filesystem)
- Create and configure the VM
- Install all required tools (takes 15-30 minutes)

### 2. First Boot

After provisioning completes:

```bash
vagrant reload
```

This reboot is necessary for:
- USB device permissions
- Nix environment setup
- Group membership changes

### 3. Access the VM

SSH access:
```bash
vagrant ssh
```

GUI access:
- VirtualBox will open a window with Ubuntu desktop
- Login: `vagrant` / `vagrant`

### 4. Verify Installation

After logging in, verify all tools are installed:

```bash
# Check ARM toolchain
arm-none-eabi-gcc --version

# Check Jasmin compiler
jasminc --version

# Check OpenOCD
openocd --version

# Check Python packages
python3 -c "import serial; print('PySerial OK')"
```

## Connecting the Nucleo Board

### 1. Physical Connection

1. Connect Nucleo-L4R5ZI board to your host computer via USB
2. The board should appear as `/dev/ttyACM0` (Linux) or `COM3` (Windows)

### 2. USB Passthrough to VM

#### Option A: Automatic (Pre-configured)

The Vagrantfile includes a USB filter for STMicroelectronics devices. The board should automatically connect when plugged in while the VM is running.

#### Option B: VirtualBox GUI (Alternative)

1. Start the VM
2. In VirtualBox menu: **Devices** → **USB** → **STM32 Nucleo**
3. The device will now appear in the VM

### 3. Verify Connection

In the VM:

```bash
# Check if device is present
ls -l /dev/ttyACM0

# You should see it's accessible by dialout group
# crw-rw---- 1 root dialout ... /dev/ttyACM0

# Verify you're in dialout group
groups | grep dialout
```

If the device isn't accessible, log out and log back in for group changes to take effect.

## Working with the Repository

**Important**: The repository is **cloned inside the VM** at `/home/vagrant/cryptoeng` for proper file permissions. This is separate from the host repository.

### Repository Locations

- **Working copy** (inside VM): `/home/vagrant/cryptoeng` - **Use this for all development**
- **Shared folder** (host mount): `/vagrant_shared` - For file transfer only

### Why This Setup?

VirtualBox shared folders don't preserve Unix execute permissions, which breaks
build scripts (especially libopencm3 compilation). 

### Navigation

```bash
# Go to repository root
cd ~/cryptoeng

# Or use the aliases
cryptoeng        # Go to repository root
assignment0      # Go to Sum (warmup) assignment
assignment1      # Go to ChaCha20 assignment
assignment2      # Go to Ecdh25519 assignment
```

### Syncing Changes

**Option 1: Manual Copy via Shared Folder**:
```bash
# From host to VM:
# Files are automatically visible in /vagrant_shared
# Copy specific files or directories:
cp -r /vagrant_shared/assignment1-chacha20/src ~/cryptoeng/assignment1-chacha20/

# From VM to host:
# In VM, copy to shared folder:
cp -r ~/cryptoeng/assignment1-chacha20/build /vagrant_shared/assignment1-chacha20/

# Files appear immediately in host repository
```

**Option 2: Rsync for Bulk Sync**:
```bash
# From host to VM (in VM):
rsync -av --delete /vagrant_shared/ ~/cryptoeng/ --exclude='.git'

# From VM to host (in VM):
rsync -av ~/cryptoeng/ /vagrant_shared/ --exclude='.git'
```

## VS Code

VS Code is pre-installed with useful extensions:

```bash
# Open project in VS Code
cd ~/cryptoeng
code .
```

Installed extensions:
- C/C++ (Microsoft)
- Python (Microsoft)
- CMake Tools

## Useful Vagrant Commands

```bash
# Start VM
vagrant up

# SSH into VM
vagrant ssh

# Stop VM
vagrant halt

# Restart VM
vagrant reload

# Delete VM (keeps Vagrantfile)
vagrant destroy

# Check VM status
vagrant status

# Update VM (re-run provisioning)
vagrant provision
```

## Troubleshooting

### USB device not detected by host/VM

**Symptom**: Nucleo board doesn't appear in VirtualBox USB menu, or can't be passed through to VM.

**Solution**:
1. Ensure you're in the `vboxusers` group on the host:
   ```bash
   # Check current groups
   groups

   # If vboxusers is missing, add it:
   sudo usermod -a -G vboxusers $USER

   # IMPORTANT: Logout and login again (or reboot)
   ```

2. Verify VirtualBox Extension Pack is installed:
   ```bash
   VBoxManage list extpacks
   # Should show "Oracle VM VirtualBox Extension Pack"
   ```

3. Check USB device is recognized by host:
   ```bash
   # Linux/Mac
   lsusb | grep STMicro

   # Should show something like:
   # Bus 001 Device 005: ID 0483:374e STMicroelectronics ST-LINK/V2.1
   ```

### Jasmin compiler not found

If `jasminc` is not in your PATH after reboot:

```bash
# Source Nix profile
source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh

# Reinstall Jasmin
nix-env -iA nixpkgs.jasmin-compiler

# Add to your .bashrc
echo 'source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh' >> ~/.bashrc
```

### USB device not accessible inside VM

**Symptom**: `/dev/ttyACM0` doesn't exist or shows permission denied inside VM.

**Solution**:
```bash
# Inside VM: Check device permissions
ls -l /dev/ttyACM0

# Add yourself to dialout group if not already
sudo usermod -a -G dialout $USER

# Log out and log back in
exit
vagrant ssh

# Verify dialout group membership
groups | grep dialout
```

If device still doesn't appear, check host-side USB passthrough (see above).

### Board not detected by OpenOCD

```bash
# List USB devices
lsusb

# You should see something like:
# Bus 001 Device 003: ID 0483:374e STMicroelectronics ST-LINK/V2.1

# Test OpenOCD connection
openocd -f board/st_nucleo_l4.cfg

# Should see "Info : Listening on port 3333 for gdb connections"
# Press Ctrl+C to exit
```

### Build errors

```bash
# Clean and rebuild
make clean
make

# Check libopencm3
cd ~/cryptoeng/common/libopencm3
make TARGETS=stm32/l4
```

### libopencm3 compilation fails with "Permission denied" or "cannot execute"

This usually means you're trying to build from the shared folder (`/vagrant_shared`).

**Solution**:
1. Make sure you're in the VM's local copy:
   ```bash
   cd ~/cryptoeng  # NOT /vagrant_shared
   ```

2. If libopencm3 was corrupted, rebuild it:
   ```bash
   cd ~/cryptoeng/common/libopencm3
   make clean
   make TARGETS=stm32/l4 -j$(nproc)
   ```

3. If still failing, re-clone the repository inside the VM:
   ```bash
   cd ~
   rm -rf cryptoeng
   git clone <your-repo-url> cryptoeng
   cd cryptoeng/common/libopencm3
   make TARGETS=stm32/l4 -j$(nproc)
   ```

## Additional Resources

- [Vagrant Documentation](https://www.vagrantup.com/docs)
- [VirtualBox Manual](https://www.virtualbox.org/manual/)
- [ARM GCC Toolchain](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain)
- [OpenOCD User's Guide](http://openocd.org/doc/html/index.html)
- [Jasmin Documentation](https://github.com/jasmin-lang/jasmin)
