#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <region_path>"
    echo "Example: $0 asia/pakistan"
    exit 1
fi

REGION="$1"
echo "Hosting region: ${REGION}"

cargo run --manifest-path atlasmirror-cli/Cargo.toml -- host "${REGION}"
