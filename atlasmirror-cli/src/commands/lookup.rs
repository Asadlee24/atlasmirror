use colored::Colorize;
use serde_json::{json, Value};

fn load_data() -> (Vec<Value>, Vec<Value>) {
    let manifest_bytes = include_bytes!("../../../evidence/a1-coverage-manifest.json");
    let manifest: Value = serde_json::from_slice(manifest_bytes).unwrap_or(json!({}));
    let entries = manifest.get("entries").and_then(|e| e.as_array()).cloned().unwrap_or_default();

    let regions_bytes = include_bytes!("../../../metadata/regions.json");
    let catalog: Value = serde_json::from_slice(regions_bytes).unwrap_or(json!({}));
    let catalog_regions = catalog.get("regions").and_then(|r| r.as_array()).cloned().unwrap_or_default();

    (entries, catalog_regions)
}

pub fn execute_region(path: &str, json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let (entries, catalog_regions) = load_data();

    // Check if hosted on-chain in verified manifest
    if let Some(entry) = entries.iter().find(|e| e["region"].as_str() == Some(path)) {
        if json_output {
            println!("{}", serde_json::to_string_pretty(entry)?);
        } else {
            println!("On-Chain Record for {}:", path.bold());
            println!("  Level:       {}", entry["level"].as_str().unwrap_or("unknown"));
            println!("  Parent:      {}", entry["parent"].as_str().unwrap_or("None"));
            println!("  Storage CID: {}", entry["cid"].as_str().unwrap_or("").cyan());
            println!("  Checksum:    {}", entry["geofabrik_md5"].as_str().unwrap_or(""));
            println!("  Version:     {}", entry["version"].as_str().unwrap_or(""));
            println!("  Timestamp:   {}", entry["timestamp"]);
            println!("  Tx Hash:     {}", entry["registry_tx"].as_str().unwrap_or(""));
            println!("  Status:      {}", "HOSTED & VERIFIED".green());
        }
        return Ok(());
    }

    // Check if in predefined catalog but not yet hosted
    if let Some(cat) = catalog_regions.iter().find(|r| r["path"].as_str() == Some(path)) {
        let res = json!({
            "region": path,
            "level": cat["level"].as_str().unwrap_or("country"),
            "parent": cat["parent"].as_str(),
            "hosted": false,
            "source_url": cat["geofabrik_url"].as_str().unwrap_or(""),
            "status": "NOT_HOSTED"
        });
        if json_output {
            println!("{}", serde_json::to_string_pretty(&res)?);
        } else {
            println!("Catalog Record for {}:", path.bold());
            println!("  Level:       {}", cat["level"].as_str().unwrap_or("country"));
            println!("  Parent:      {}", cat["parent"].as_str().unwrap_or("None"));
            println!("  Source URL:  {}", cat["geofabrik_url"].as_str().unwrap_or(""));
            println!("  Status:      {}", "NOT_HOSTED".yellow());
        }
        return Ok(());
    }

    eprintln!("{} Region '{}' not found in predefined closed-set catalog.", "✖".red(), path);
    std::process::exit(1);
}

pub fn execute_parent(parent: &str, json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let (_entries, catalog_regions) = load_data();

    let mut children = Vec::new();
    for r in &catalog_regions {
        if r["parent"].as_str() == Some(parent) {
            if let Some(p) = r["path"].as_str() {
                children.push(p.to_string());
            }
        }
    }

    if children.is_empty() {
        eprintln!("{} No subregions found for parent '{}'.", "✖".yellow(), parent);
        std::process::exit(1);
    }

    if json_output {
        println!("{}", json!({ "parent": parent, "children": children }));
    } else {
        println!("Subregions for parent {}:", parent.bold());
        for c in children {
            println!("  - {}", c.cyan());
        }
    }
    Ok(())
}

pub fn execute_cid(cid: &str, json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let (entries, _catalog_regions) = load_data();

    if let Some(entry) = entries.iter().find(|e| e["cid"].as_str() == Some(cid)) {
        if json_output {
            println!("{}", serde_json::to_string_pretty(entry)?);
        } else {
            println!("CID Lookup: {}", cid.cyan());
            println!("  Region:    {}", entry["region"].as_str().unwrap_or("").bold());
            println!("  Level:     {}", entry["level"].as_str().unwrap_or(""));
            println!("  Parent:    {}", entry["parent"].as_str().unwrap_or("None"));
            println!("  Version:   {}", entry["version"].as_str().unwrap_or(""));
            println!("  Checksum:  {}", entry["geofabrik_md5"].as_str().unwrap_or(""));
            println!("  Timestamp: {}", entry["timestamp"]);
            println!("  Tx Hash:   {}", entry["registry_tx"].as_str().unwrap_or(""));
        }
        return Ok(());
    }

    eprintln!("{} CID '{}' not found in on-chain registry.", "✖".red(), cid);
    std::process::exit(1);
}
