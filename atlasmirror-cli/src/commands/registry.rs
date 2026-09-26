use colored::Colorize;
use serde_json::json;

pub const PROGRAM_ID: &str = "bcdc104271bd670da3b1afddcb758286c619de87365d6488c9c2f563947f8b4f";
pub const ACCOUNT_ID: &str = "T8T4nfBcLDNUycWNQ4SyrvsduRZZ8Uxk5XSzS2XMvci";

pub fn execute_program_id(json_output: bool) -> Result<(), Box<dyn std::error::Error>> {
    if json_output {
        println!(
            "{}",
            json!({
                "program_id": PROGRAM_ID,
                "account_id": ACCOUNT_ID,
                "network": "Logos Testnet 0.3"
            })
        );
    } else {
        println!("LEZ OSM Registry Program ID: {}", PROGRAM_ID.cyan().bold());
        println!("State Account:             {}", ACCOUNT_ID.green());
        println!("Target Network:             Logos Testnet 0.3");
    }
    Ok(())
}

pub async fn execute_raw(
    region: &str,
    _json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    // Try to get live on-chain record first
    if let Ok(records) = crate::registry::query_on_chain_registry().await {
        if let Some(r) = records.into_iter().find(|rec| rec.region == region) {
            println!("{}", serde_json::to_string_pretty(&r)?);
            return Ok(());
        }
    }

    let is_subregion = region.starts_with("us/")
        || region.starts_with("india/")
        || region.starts_with("china/")
        || region.starts_with("russia/");

    let parent = if is_subregion {
        region.split('/').next().map(|s| s.to_string())
    } else {
        None
    };

    let raw = json!({
        "account_seed": format!("pda:region:{}", region),
        "region": region,
        "parent": parent,
        "level": if is_subregion { "Subregion" } else { "Country" },
        "source_url": format!("https://download.geofabrik.de/{}-latest.osm.pbf", region),
        "hosted": false,
        "status": "not_yet_registered_or_queried"
    });

    println!("{}", serde_json::to_string_pretty(&raw)?);
    Ok(())
}
