use colored::Colorize;
use serde_json::json;

pub fn execute_list(
    _filter: Option<&str>,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    // 72 predefined regions (sample display in CLI)
    let regions = vec![
        (
            "asia/pakistan",
            "Pakistan",
            "country",
            true,
            "bafybeic7vj2k...",
            "2026-09-19",
        ),
        (
            "europe/germany",
            "Germany",
            "country",
            true,
            "bafybeih4nm3q...",
            "2026-09-19",
        ),
        (
            "europe/france",
            "France",
            "country",
            true,
            "bafybeig5tl2x...",
            "2026-09-19",
        ),
        (
            "europe/great-britain",
            "United Kingdom",
            "country",
            true,
            "bafybeid3ko9p...",
            "2026-09-19",
        ),
        (
            "us/california",
            "California",
            "subregion",
            true,
            "bafybeid6xk1m...",
            "2026-09-19",
        ),
        ("us/texas", "Texas", "subregion", false, "—", "2026-09-19"),
        (
            "india/northern-zone",
            "Northern Zone",
            "subregion",
            true,
            "bafybeif2mk7w...",
            "2026-09-19",
        ),
        (
            "china/guangdong",
            "Guangdong",
            "subregion",
            false,
            "—",
            "2026-09-19",
        ),
        (
            "russia/central-fed-district",
            "Central Fed District",
            "subregion",
            true,
            "bafybeid5mk2v...",
            "2026-09-19",
        ),
    ];

    if json_output {
        let list: Vec<_> = regions
            .iter()
            .map(|(path, name, level, hosted, cid, ver)| {
                json!({
                    "path": path,
                    "name": name,
                    "level": level,
                    "hosted": hosted,
                    "cid": if *hosted { *cid } else { "" },
                    "version": ver
                })
            })
            .collect();
        println!("{}", serde_json::to_string_pretty(&list)?);
        return Ok(());
    }

    println!(
        "{:<30} {:<12} {:<10} {:<12} CID",
        "REGION", "LEVEL", "VERSION", "STATUS"
    );
    println!("{}", "-".repeat(85));

    for (path, _name, level, hosted, cid, ver) in regions {
        let status = if hosted {
            "Hosted".green()
        } else {
            "Not hosted".yellow()
        };
        println!(
            "{:<30} {:<12} {:<10} {:<12} {}",
            path, level, ver, status, cid
        );
    }

    Ok(())
}

pub fn execute_show(path: &str, json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let details = json!({
        "path": path,
        "name": path.split('/').next_back().unwrap_or(path),
        "level": if path.contains('/') && (path.starts_with("us/") || path.starts_with("india/") || path.starts_with("china/") || path.starts_with("russia/")) { "subregion" } else { "country" },
        "parent": if path.contains('/') { Some(path.split('/').next().unwrap()) } else { None },
        "geofabrik_url": format!("https://download.geofabrik.de/{}-latest.osm.pbf", path),
        "md5_url": format!("https://download.geofabrik.de/{}-latest.osm.pbf.md5", path),
        "hosted": true,
        "cid": "bafybeic7vj2k...4q",
        "checksum": "378df25f824177ebcbe9aa11d88bbd6b",
        "version": "2026-09-19"
    });

    if json_output {
        println!("{}", serde_json::to_string_pretty(&details)?);
    } else {
        println!(
            "Region:        {}",
            details["path"].as_str().unwrap().bold()
        );
        println!("Level:         {}", details["level"].as_str().unwrap());
        println!(
            "Parent:        {}",
            details["parent"].as_str().unwrap_or("None")
        );
        println!(
            "Status:        {}",
            if details["hosted"].as_bool().unwrap() {
                "Hosted".green()
            } else {
                "Not hosted".yellow()
            }
        );
        println!("Storage CID:   {}", details["cid"].as_str().unwrap().cyan());
        println!("Checksum:      {}", details["checksum"].as_str().unwrap());
        println!("Version:       {}", details["version"].as_str().unwrap());
        println!(
            "Source URL:    {}",
            details["geofabrik_url"].as_str().unwrap()
        );
    }

    Ok(())
}
