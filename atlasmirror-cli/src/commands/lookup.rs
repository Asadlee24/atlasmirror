use colored::Colorize;
use serde_json::{json, Value};

fn load_catalog() -> Vec<Value> {
    let regions_bytes = include_bytes!("../../../metadata/regions.json");
    let catalog: Value = serde_json::from_slice(regions_bytes).unwrap_or(json!({}));
    catalog
        .get("regions")
        .and_then(|r| r.as_array())
        .cloned()
        .unwrap_or_default()
}

pub async fn execute_region(
    path: &str,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    // Query genuine on-chain LEZ registry
    if let Ok(on_chain_records) = crate::registry::query_on_chain_registry().await {
        if let Some(entry) = on_chain_records.iter().find(|e| e.region == path) {
            if json_output {
                println!("{}", serde_json::to_string_pretty(entry)?);
            } else {
                println!("On-Chain Record for {}:", path.bold());
                println!("  Level:       {}", entry.level);
                println!(
                    "  Parent:      {}",
                    entry.parent.as_deref().unwrap_or("None")
                );
                println!("  Storage CID: {}", entry.cid.cyan());
                println!("  Checksum:    {}", entry.checksum);
                println!("  Version:     {}", entry.version);
                println!("  Timestamp:   {}", entry.timestamp);
                println!("  Status:      {}", "HOSTED ON-CHAIN".green());
            }
            return Ok(());
        }
    }

    // Check predefined catalog if not hosted
    let catalog_regions = load_catalog();
    if let Some(cat) = catalog_regions
        .iter()
        .find(|r| r["path"].as_str() == Some(path))
    {
        let res = json!({
            "region": path,
            "level": cat["level"].as_str().unwrap_or("country"),
            "parent": cat.get("parent"),
            "source_url": cat["geofabrik_url"].as_str().unwrap_or(""),
            "status": "NOT_HOSTED"
        });
        if json_output {
            println!("{}", serde_json::to_string_pretty(&res)?);
        } else {
            println!("Catalog Record for {}:", path.bold());
            println!(
                "  Level:       {}",
                cat["level"].as_str().unwrap_or("country")
            );
            println!(
                "  Parent:      {}",
                cat["parent"].as_str().unwrap_or("None")
            );
            println!(
                "  Source URL:  {}",
                cat["geofabrik_url"].as_str().unwrap_or("")
            );
            println!("  Status:      {}", "NOT_HOSTED".yellow());
        }
        return Ok(());
    }

    eprintln!(
        "{} Region '{}' not found in predefined closed-set catalog.",
        "✖".red(),
        path
    );
    std::process::exit(1);
}

pub async fn execute_parent(
    parent: &str,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let mut children = Vec::new();
    if let Ok(on_chain_records) = crate::registry::query_on_chain_registry().await {
        for r in on_chain_records {
            if r.parent.as_deref() == Some(parent) {
                children.push(json!({
                    "region": r.region,
                    "level": r.level,
                    "cid": r.cid,
                    "checksum": r.checksum,
                    "version": r.version,
                    "hosted": true
                }));
            }
        }
    }

    if children.is_empty() {
        let catalog_regions = load_catalog();
        for r in catalog_regions {
            if r["parent"].as_str() == Some(parent) {
                children.push(json!({
                    "region": r["path"].as_str().unwrap_or(""),
                    "level": r["level"].as_str().unwrap_or("subregion"),
                    "hosted": false
                }));
            }
        }
    }

    if children.is_empty() {
        eprintln!(
            "{} No subregions found for parent '{}'.",
            "✖".yellow(),
            parent
        );
        std::process::exit(1);
    }

    if json_output {
        println!("{}", serde_json::to_string_pretty(&children)?);
    } else {
        println!("Subregions under {}:", parent.bold());
        for c in children {
            let status_badge = if c["hosted"].as_bool().unwrap_or(false) {
                "HOSTED".green()
            } else {
                "NOT_HOSTED".yellow()
            };
            println!(
                "  - {:<30} [{}]",
                c["region"].as_str().unwrap_or(""),
                status_badge
            );
        }
    }

    Ok(())
}

pub async fn execute_cid(cid: &str, json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let on_chain_records = crate::registry::query_on_chain_registry()
        .await
        .map_err(|e| format!("Failed to query on-chain registry for CID {}: {}", cid, e))?;

    if let Some(entry) = on_chain_records.iter().find(|e| e.cid == cid) {
        if json_output {
            println!("{}", serde_json::to_string_pretty(entry)?);
        } else {
            println!("On-Chain CID Lookup: {}", cid.cyan());
            println!("  Region:    {}", entry.region.bold());
            println!("  Level:     {}", entry.level);
            println!("  Parent:    {}", entry.parent.as_deref().unwrap_or("None"));
            println!("  Checksum:  {}", entry.checksum);
            println!("  Version:   {}", entry.version);
            println!("  Timestamp: {}", entry.timestamp);
            println!("  Status:    {}", "HOSTED ON-CHAIN".green());
        }
        return Ok(());
    }

    eprintln!(
        "{} Content Identifier '{}' not found in on-chain registry.",
        "✖".red(),
        cid
    );
    std::process::exit(1);
}
