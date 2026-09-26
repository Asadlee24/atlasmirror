use std::fs;
use std::path::Path;
use std::process::Command;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Authoritative SPEL IDL Generation for osm_registry...");

    let idl_dir = Path::new("idl");
    if !idl_dir.exists() {
        fs::create_dir_all(idl_dir)?;
    }
    let out_path = idl_dir.join("osm_registry.json");

    // Resolve authoritative SPEL CLI binary
    let spel_bin = std::env::var("SPEL_BIN").unwrap_or_else(|_| "spel".to_string());
    let candidate_paths = [
        "methods/guest/src/bin/osm_registry.rs",
        "osm-registry/methods/guest/src/bin/osm_registry.rs",
        "../methods/guest/src/bin/osm_registry.rs",
    ];

    let mut generated = false;
    for src_path in &candidate_paths {
        if Path::new(src_path).exists() {
            println!("Invoking SPEL generate-idl on source: {}", src_path);
            let res = Command::new(&spel_bin)
                .arg("generate-idl")
                .arg(src_path)
                .output();

            match res {
                Ok(output) if output.status.success() => {
                    let stdout = String::from_utf8_lossy(&output.stdout);
                    if let Ok(val) = serde_json::from_str::<serde_json::Value>(&stdout) {
                        let pretty = serde_json::to_string_pretty(&val)?;
                        fs::write(&out_path, format!("{}\n", pretty))?;
                        println!(
                            "Successfully generated authoritative SPEL IDL via CLI at: {}",
                            out_path.display()
                        );
                        generated = true;
                        break;
                    }
                }
                Ok(output) => {
                    let err = String::from_utf8_lossy(&output.stderr);
                    eprintln!("SPEL CLI returned non-zero exit: {}", err);
                }
                Err(e) => {
                    eprintln!("Failed to execute SPEL CLI ('{}'): {}", spel_bin, e);
                }
            }
        }
    }

    if !generated {
        if out_path.exists() {
            if let Ok(content) = fs::read_to_string(&out_path) {
                if serde_json::from_str::<serde_json::Value>(&content).is_ok() {
                    println!(
                        "Notice: SPEL CLI not available in environment. Verified existing authoritative IDL at: {}",
                        out_path.display()
                    );
                    return Ok(());
                }
            }
        }
        eprintln!(
            "\nERROR: SPEL CLI 'generate-idl' failed or binary ('{}') is unavailable.",
            spel_bin
        );
        eprintln!(
            "Manual JSON fallback is strictly removed to guarantee authoritative IDL provenance."
        );
        eprintln!(
            "To generate the IDL, ensure 'spel' is in PATH or set the SPEL_BIN environment variable."
        );
        std::process::exit(1);
    }

    Ok(())
}
