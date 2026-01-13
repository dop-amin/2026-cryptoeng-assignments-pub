#!/bin/bash
set -e

REQUIRED_HOSTNAME="cryptoeng-vm"
CURRENT_HOSTNAME="$(hostname)"

if [ "$CURRENT_HOSTNAME" != "$REQUIRED_HOSTNAME" ]; then
    echo "Hostname is '$CURRENT_HOSTNAME' — expected '$REQUIRED_HOSTNAME'."
    echo "Exiting without making SSH changes."
    exit 0
fi

SSHD_CONFIG="/etc/ssh/sshd_config"
SSHD_CONFIG_D="/etc/ssh/sshd_config.d"

enable_settings() {
    local file="$1"

    echo "Updating $file"

    # PasswordAuthentication yes
    if grep -qE '^\s*PasswordAuthentication' "$file"; then
        sed -i 's/^\s*PasswordAuthentication.*/PasswordAuthentication yes/' "$file"
    else
        echo "PasswordAuthentication yes" >> "$file"
    fi

    # PermitRootLogin yes
    if grep -qE '^\s*PermitRootLogin' "$file"; then
        sed -i 's/^\s*PermitRootLogin.*/PermitRootLogin yes/' "$file"
    else
        echo "PermitRootLogin yes" >> "$file"
    fi
}

# Main sshd_config
enable_settings "$SSHD_CONFIG"

# sshd_config.d/*
if [ -d "$SSHD_CONFIG_D" ]; then
    for file in "$SSHD_CONFIG_D"/*.conf; do
        [ -e "$file" ] || continue
        enable_settings "$file"
    done
fi

# Reload SSH service
if systemctl is-active --quiet sshd; then
    systemctl reload sshd
elif systemctl is-active --quiet ssh; then
    systemctl reload ssh
fi

echo "SSH configuration updated on $REQUIRED_HOSTNAME."
