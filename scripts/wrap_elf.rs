use std::env;
use std::fs;

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: wrap_elf input_elf output_bin");
        std::process::exit(1);
    }
    let input_elf = fs::read(&args[1]).expect("read input elf");
    let binary = risc0_binfmt::ProgramBinary::new(&input_elf, risc0_zkos_v1compat::V1COMPAT_ELF).encode();
    fs::write(&args[2], &binary).expect("write output bin");
    println!("Successfully wrapped ELF ({} bytes) into ProgramBinary ({} bytes)", input_elf.len(), binary.len());
}
