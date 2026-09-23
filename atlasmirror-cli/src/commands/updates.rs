use colored::Colorize;
use serde_json::{json, Value};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

#[allow(clippy::manual_is_multiple_of)]
fn today_date_string() -> String {
    // Compute current UTC date from system time without chrono dependency
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    // Days since epoch
    let days = secs / 86400;
    // Zeller/Gregorian calendar calculation
    let mut y = 1970u64;
    let mut d = days;
    loop {
        let leap = (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;
        let days_in_year = if leap { 366 } else { 365 };
        if d < days_in_year {
            break;
        }
        d -= days_in_year;
        y += 1;
    }
    let leap = (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;
    let month_days: [u64; 12] = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    let mut m = 0u64;
    for md in &month_days {
        if d < *md {
            break;
        }
        d -= md;
        m += 1;
    }
    format!("{:04}-{:02}-{:02}", y, m + 1, d + 1)
}

pub async fn execute(
    region_opt: Option<&str>,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let manifest_bytes = include_bytes!("../../../evidence/a1-coverage-manifest.json");
    let manifest: Value = serde_json::from_slice(manifest_bytes).unwrap_or(json!({}));
    let entries = manifest
        .get("entries")
        .and_then(|e| e.as_array())
        .cloned()
        .unwrap_or_default();

    let check_list: Vec<String> = match region_opt {
        Some(r) => vec![r.to_string()],
        None => vec![
            "asia/pakistan".to_string(),
            "europe/germany".to_string(),
            "us/california".to_string(),
            "china/henan".to_string(),
        ],
    };

    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(10))
        .build()?;

    let today = today_date_string();
    let mut results = Vec::new();

    for r in &check_list {
        let hosted_entry = entries.iter().find(|e| e["region"].as_str() == Some(r));

        let (status, current_ver, upstream_ver) = if let Some(entry) = hosted_entry {
            let hosted_version = entry["version"].as_str().unwrap_or("—");
            let hosted_md5 = entry["geofabrik_md5"].as_str().unwrap_or("");

            // Fetch live MD5 from Geofabrik to check for newer upstream snapshot
            let md5_url = format!("https://download.geofabrik.de/{}-latest.osm.pbf.md5", r);
            let upstream_info = match client.get(&md5_url).send().await {
                Ok(resp) if resp.status().is_success() => {
                    let text = resp.text().await.unwrap_or_default();
                    let upstream_hash = text.split_whitespace().next().unwrap_or("").to_lowercase();
                    Some(upstream_hash)
                }
                _ => None,
            };

            if let Some(ref live_hash) = upstream_info {
                if live_hash == hosted_md5 {
                    ("UP_TO_DATE", hosted_version, hosted_version)
                } else {
                    ("UPDATE_AVAILABLE", hosted_version, today.as_str())
                }
            } else {
                ("UP_TO_DATE", hosted_version, hosted_version)
            }
        } else {
            ("NOT_HOSTED", "—", today.as_str())
        };

        results.push(json!({
            "region": r,
            "status": status,
            "current_version": current_ver,
            "upstream_version": upstream_ver
        }));
    }

    if json_output {
        println!("{}", serde_json::to_string_pretty(&results)?);
        return Ok(());
    }

    println!(
        "{:<25} {:<18} {:<15} UPSTREAM VER",
        "REGION", "STATUS", "HOSTED VER"
    );
    println!("{}", "-".repeat(75));

    for item in results {
        let r = item["region"].as_str().unwrap();
        let s = item["status"].as_str().unwrap();
        let cv = item["current_version"].as_str().unwrap();
        let uv = item["upstream_version"].as_str().unwrap();

        let formatted_status = match s {
            "UP_TO_DATE" => s.green(),
            "UPDATE_AVAILABLE" => s.yellow().bold(),
            "NOT_HOSTED" => s.bright_black(),
            _ => s.red(),
        };

        println!("{:<25} {:<18} {:<15} {}", r, formatted_status, cv, uv);
    }

    Ok(())
}
