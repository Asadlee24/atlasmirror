#!/usr/bin/env bash
set -euo pipefail

echo "Starting AtlasMirror Development Shell..."
if command -v nix >/dev/null 2>&1; then
    nix develop
else
    echo "Nix not found. Running in standard shell mode."
    $SHELL
fi
