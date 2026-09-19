import re

with open("/tmp/spel/spel-cli/Cargo.toml", "r") as f:
    content = f.read()

# Replace git dependencies with local paths
content = re.sub(
    r'nssa_core\s*=\s*\{[^}]+\}',
    'nssa_core = { path = "/tmp/lez/lee/state_machine/core", package = "lee_core", features = ["host"] }',
    content
)
content = re.sub(
    r'nssa\s*=\s*\{[^}]+\}',
    'nssa = { path = "/tmp/lez/lee/state_machine", package = "lee" }',
    content
)
content = re.sub(
    r'common\s*=\s*\{[^}]+\}',
    'common = { path = "/tmp/lez/lez/common" }',
    content
)
content = re.sub(
    r'sequencer_service_rpc\s*=\s*\{[^}]+\}',
    'sequencer_service_rpc = { path = "/tmp/lez/lez/sequencer/service/rpc", features = ["client"] }',
    content
)
content = re.sub(
    r'wallet\s*=\s*\{[^}]+\}',
    'wallet = { path = "/tmp/lez/lez/wallet" }',
    content
)

with open("/tmp/spel/spel-cli/Cargo.toml", "w") as f:
    f.write(content)

print("SUCCESS: spel-cli Cargo.toml patched to local paths")
