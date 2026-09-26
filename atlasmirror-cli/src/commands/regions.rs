use colored::Colorize;
use serde::{Deserialize, Serialize};
use serde_json::json;

#[derive(Deserialize, Serialize, Clone, Debug)]
struct CatalogRegion {
    path: String,
    name: String,
    parent: Option<String>,
    level: String,
    geofabrik_url: String,
    md5_url: String,
}

#[derive(Deserialize, Debug)]
struct CatalogFile {
    regions: Vec<CatalogRegion>,
}

fn load_catalog() -> Vec<CatalogRegion> {
    const CATALOG_JSON: &str = include_str!("../../../metadata/regions.json");
    serde_json::from_str::<CatalogFile>(CATALOG_JSON)
        .map(|c| c.regions)
        .unwrap_or_default()
}

pub async fn execute_list(
    filter: Option<&str>,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let catalog = load_catalog();
    let onchain_records = crate::registry::query_on_chain_registry()
        .await
        .unwrap_or_default();

    let mut display_rows = Vec::new();

    for cat_item in &catalog {
        let onchain = onchain_records.iter().find(|r| r.region == cat_item.path);
        let hosted = onchain.is_some() && onchain.map(|o| o.hosted).unwrap_or(false);
        let cid = onchain.map(|o| o.cid.as_str()).unwrap_or("—");
        let version = onchain.map(|o| o.version.as_str()).unwrap_or("—");

        // Apply filter if specified
        if let Some(f) = filter {
            let f_lower = f.to_lowercase();
            let matches = cat_item.path.to_lowercase().contains(&f_lower)
                || cat_item.name.to_lowercase().contains(&f_lower)
                || cat_item.level.to_lowercase() == f_lower
                || (f_lower == "hosted" && hosted)
                || (f_lower == "unhosted" && !hosted);

            if !matches {
                continue;
            }
        }

        display_rows.push((
            cat_item.path.clone(),
            cat_item.name.clone(),
            cat_item.level.clone(),
            hosted,
            cid.to_string(),
            version.to_string(),
        ));
    }

    if json_output {
        let list: Vec<_> = display_rows
            .iter()
            .map(|(path, name, level, hosted, cid, ver)| {
                json!({
                    "path": path,
                    "name": name,
                    "level": level,
                    "hosted": hosted,
                    "cid": if *hosted { cid.as_str() } else { "" },
                    "version": ver
                })
            })
            .collect();
        println!("{}", serde_json::to_string_pretty(&list)?);
        return Ok(());
    }

    println!(
        "{:<35} {:<12} {:<12} {:<12} CID",
        "REGION", "LEVEL", "VERSION", "STATUS"
    );
    println!("{}", "-".repeat(95));

    for (path, _name, level, hosted, cid, ver) in &display_rows {
        let status = if *hosted {
            "Hosted".green()
        } else {
            "Not hosted".yellow()
        };
        println!(
            "{:<35} {:<12} {:<12} {:<12} {}",
            path, level, ver, status, cid
        );
    }

    println!("\nTotal regions displayed: {}", display_rows.len());
    Ok(())
}

pub async fn execute_show(path: &str, json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let catalog = load_catalog();
    let cat_item = catalog.iter().find(|r| r.path == path);

    if cat_item.is_none() {
        return Err(format!(
            "Region '{}' is not in the predefined LP-0018 closed catalog.",
            path
        )
        .into());
    }
    let cat_item = cat_item.unwrap();

    let onchain_records = crate::registry::query_on_chain_registry()
        .await
        .unwrap_or_default();
    let onchain = onchain_records.iter().find(|r| r.region == path);

    let hosted = onchain.is_some() && onchain.map(|o| o.hosted).unwrap_or(false);
    let cid = onchain.map(|o| o.cid.as_str()).unwrap_or("—");
    let checksum = onchain.map(|o| o.checksum.as_str()).unwrap_or("—");
    let version = onchain.map(|o| o.version.as_str()).unwrap_or("—");

    let details = json!({
        "path": cat_item.path,
        "name": cat_item.name,
        "level": cat_item.level,
        "parent": cat_item.parent,
        "geofabrik_url": cat_item.geofabrik_url,
        "md5_url": cat_item.md5_url,
        "hosted": hosted,
        "cid": cid,
        "checksum": checksum,
        "version": version
    });

    if json_output {
        println!("{}", serde_json::to_string_pretty(&details)?);
    } else {
        println!("Region:        {}", cat_item.path.bold());
        println!("Name:          {}", cat_item.name);
        println!("Level:         {}", cat_item.level);
        println!(
            "Parent:        {}",
            cat_item.parent.as_deref().unwrap_or("None")
        );
        println!(
            "Status:        {}",
            if hosted {
                "Hosted".green()
            } else {
                "Not hosted".yellow()
            }
        );
        println!(
            "Storage CID:   {}",
            if hosted { cid.cyan() } else { cid.normal() }
        );
        println!("Checksum:      {}", checksum);
        println!("Version:       {}", version);
        println!("Source URL:    {}", cat_item.geofabrik_url);
    }

    Ok(())
}
