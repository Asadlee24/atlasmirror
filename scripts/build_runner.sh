#!/usr/bin/env bash
set -e
export PATH="/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
cd /root/lez-testnet-compatible/examples/program_deployment
cargo build --bin run_osm_registry
