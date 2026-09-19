#!/usr/bin/env bash
set -e
python3 /mnt/c/Users/Aftab/Desktop/atlasmirror/scripts/fix_spel_cargo.py

# Revert spel-cli/Cargo.toml so patch applies cleanly across the workspace
cd /tmp/spel
git checkout spel-cli/Cargo.toml

# Check what Cargo sees now
export PATH="/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:$PATH"
cargo metadata --no-deps --format-version 1 > /dev/null
echo "Cargo metadata succeeded with patch table!"
