#!/usr/bin/env bash
set -e
export PATH="/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:$PATH"

cd /tmp/spel
echo "=== Building SPEL CLI ==="
cargo build --release -p spel
cp /tmp/spel/target/release/spel /usr/local/bin/spel
chmod +x /usr/local/bin/spel
/usr/local/bin/spel --help
echo "=== SPEL CLI built and installed successfully ==="
