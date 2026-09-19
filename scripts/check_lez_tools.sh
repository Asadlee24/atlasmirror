#!/usr/bin/env bash
export PATH="/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:$PATH"

echo "=== 1. Checking Docker ==="
which docker || echo "docker not in PATH"
docker --version 2>&1 || echo "docker failed"

echo "=== 2. Checking cargo-risczero ==="
which cargo-risczero || echo "cargo-risczero not in PATH"

echo "=== 3. Checking spel / spel-cli ==="
which spel || echo "spel not in PATH"
which spel-cli || echo "spel-cli not in PATH"

echo "=== 4. Checking wallet CLI ==="
which wallet || echo "wallet not in PATH"

echo "=== 5. Checking sequencer_service ==="
which sequencer_service || echo "sequencer_service not in PATH"

echo "=== 6. Checking Nix / Nix flakes for LEZ / SPEL ==="
find /nix/store -maxdepth 3 -name 'cargo-risczero*' 2>/dev/null | head -5
find /nix/store -maxdepth 3 -name 'spel*' 2>/dev/null | head -5
find /nix/store -maxdepth 3 -name 'sequencer*' 2>/dev/null | head -5
find /nix/store -maxdepth 3 -name 'wallet*' 2>/dev/null | head -5

echo "=== 7. Checking Docker daemon status ==="
docker ps 2>&1 || echo "docker daemon not running"
