with open('/tmp/spel/Cargo.toml', 'r') as f:
    content = f.read()

# Remove the [patch] section at the bottom
if '[patch."https://github.com/logos-blockchain/logos-execution-zone.git"]' in content:
    content = content.split('[patch."https://github.com/logos-blockchain/logos-execution-zone.git"]')[0]
    with open('/tmp/spel/Cargo.toml', 'w') as f:
        f.write(content)
    print("Patch removed from /tmp/spel/Cargo.toml")
else:
    print("No patch found")
