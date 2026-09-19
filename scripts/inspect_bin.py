import subprocess
import json

def main():
    cmd = [
        "wsl", "-u", "root", "bash", "-c",
        """
        export PATH="/nix/store/95k9rsn1zsw1yvir8mj824ldhf90i4qw-gcc-wrapper-14.3.0/bin:/nix/store/x3x6f60rbnd0h6zpsysna0p31ghic7ap-rust-default-1.96.0/bin:$PATH"
        cat << 'EOF' > /tmp/inspect.rs
use std::fs;
use risc0_binfmt::ProgramBinary;

fn main() {
    let path = "/mnt/c/Users/Aftab/Desktop/atlasmirror/osm-registry/target/riscv32im-risc0-zkvm-elf/release/osm_registry.bin";
    let bytes = fs::read(path).unwrap();
    let bin = ProgramBinary::decode(&bytes).unwrap();
    let user_elf_len = bin.user_elf.len();
    let max_seg = 96 * 1024;
    let num_segs = (user_elf_len + max_seg - 1) / max_seg;
    println!("USER_ELF_LEN: {}", user_elf_len);
    println!("NUM_SEGMENTS: {}", num_segs);
    let image_id = bin.compute_image_id().unwrap();
    println!("COMPUTED_IMAGE_ID: {}", image_id);
}
EOF
        rustc --edition=2021 -L /tmp/lez/target/debug/deps --extern risc0_binfmt=/tmp/lez/target/debug/deps/librisc0_binfmt-*.rlib /tmp/inspect.rs -o /tmp/inspect 2>/dev/null || true
        if [ -f /tmp/inspect ]; then
            /tmp/inspect
        else
            echo "Could not build rust inspect, using file size estimate"
        fi
        """
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    print(res.stderr)

if __name__ == "__main__":
    main()
