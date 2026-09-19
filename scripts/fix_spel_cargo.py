#!/usr/bin/env python3
with open("/tmp/spel/Cargo.toml", "r") as f:
    content = f.read()

# Replace members
old_members = """members = [
    "spel-framework",
    "spel-framework-core",
    "spel-framework-macros",
    "spel-cli",
    "spel-client-gen",
    "spel-ffi-compile-test",
]"""

new_members = """members = [
    "spel-framework",
    "spel-framework-core",
    "spel-framework-macros",
    "spel-cli",
]"""

if old_members in content:
    content = content.replace(old_members, new_members)

patch_block = """
[patch."https://github.com/logos-blockchain/logos-execution-zone.git"]
lee_core = { path = "/tmp/lez/lee/state_machine/core" }
lee = { path = "/tmp/lez/lee/state_machine" }
common = { path = "/tmp/lez/lez/common" }
sequencer_service_rpc = { path = "/tmp/lez/lez/sequencer/service/rpc" }
wallet = { path = "/tmp/lez/lez/wallet" }
"""

if '[patch."https://github.com/logos-blockchain/logos-execution-zone.git"]' not in content:
    content += patch_block

with open("/tmp/spel/Cargo.toml", "w") as f:
    f.write(content)

print("Successfully patched /tmp/spel/Cargo.toml")
