use colored::Colorize;
use serde_json::json;

pub fn execute_program_id(json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let program_id = "0xosm_registry_testnet03_49f82d";
    if json_output {
        println!(
            "{}",
            json!({ "program_id": program_id, "network": "Logos Testnet 0.3" })
        );
    } else {
        println!("LEZ OSM Registry Program ID: {}", program_id.cyan().bold());
        println!("Target Network:             Logos Testnet 0.3");
    }
    Ok(())
}

pub fn execute_raw(region: &str, _json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    let raw = json!({
        "account_seed": format!("pda:region:{}", region),
        "region": region,
        "parent": if region.contains('/') { Some(region.split('/').next().unwrap()) } else { None },
        "level": if region.starts_with("us/") || region.starts_with("india/") || region.starts_with("china/") || region.starts_with("russia/") { "Subregion" } else { "Country" },
        "cid": "bafybeic7vj2k...4q",
        "source_url": format!("https://download.geofabrik.de/{}-latest.osm.pbf", region),
        "checksum": "378df25f824177ebcbe9aa11d88bbd6b",
        "version": "2026-09-19",
        "hosted": true,
        "timestamp": 1726747200
    });

    println!("{}", serde_json::to_string_pretty(&raw)?);
    Ok(())
}
