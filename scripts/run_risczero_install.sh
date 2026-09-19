#!/usr/bin/env bash
export PATH="/root/.risc0/bin:/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:/usr/local/bin:$PATH"

echo "=== Installing rust component via rzup ==="
rzup install rust
