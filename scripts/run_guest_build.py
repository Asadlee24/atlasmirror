import subprocess
import sys

def main():
    cmd = [
        "wsl", "-u", "root", "bash", "-c",
        """
        export PATH="/root/.risc0/toolchains/v1.97.0-rust-x86_64-unknown-linux-gnu/bin:/usr/bin:/bin:$PATH"
        export RUSTFLAGS='--cfg getrandom_backend="unsupported"'
        echo "=== PATH: $PATH ==="
        which cargo
        which rustc
        cd /mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry
        cargo build --manifest-path methods/guest/Cargo.toml --target riscv32im-risc0-zkvm-elf --release
        """
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:")
    print(res.stdout)
    print("STDERR:")
    print(res.stderr)
    print("RETURNCODE:", res.returncode)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
