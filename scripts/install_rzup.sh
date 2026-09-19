#!/usr/bin/env bash
set -e
export PATH="/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:/usr/local/bin:$PATH"

echo "rustc is at: $(which rustc)"

echo "=== Installing rzup ==="
curl -L https://risczero.com/install | bash

export PATH="/root/.risc0/bin:$PATH"

which rzup
rzup --version
echo "=== Installing riscv32im-risc0-zkvm-elf toolchain ==="
rzup install
