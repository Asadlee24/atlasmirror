use std::env;
use std::fs;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: compute_id <path_to_bin>");
        return Ok(());
    }
    let bytecode = fs::read(&args[1])?;
    let image_id: [u32; 8] = risc0_binfmt::compute_image_id(&bytecode)?.into();
    println!("{:?}", image_id);
    Ok(())
}
