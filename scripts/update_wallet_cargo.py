with open("/root/lez-testnet-compatible/lez/wallet/Cargo.toml", "r") as f:
    content = f.read()

if "risc0-binfmt" not in content:
    content = content.replace("[dependencies]\n", '[dependencies]\nrisc0-binfmt = "3.0.2"\nrisc0-zkos-v1compat = "2.2.3"\n')
    with open("/root/lez-testnet-compatible/lez/wallet/Cargo.toml", "w") as f:
        f.write(content)
    print("Updated wallet Cargo.toml with risc0-binfmt and risc0-zkos-v1compat")
else:
    print("Dependencies already present")
