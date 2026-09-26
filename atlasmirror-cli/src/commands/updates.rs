use colored::Colorize;
use serde_json::json;
use std::time::Duration;

pub async fn execute(
    region_opt: Option<&str>,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let on_chain_records = crate::registry::query_on_chain_registry().await.ok();

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

    let mut results = Vec::new();
    let mut any_unavailable = false;

    for r in &check_list {
        let hosted_entry = on_chain_records
            .as_ref()
            .and_then(|recs| recs.iter().find(|e| e.region == *r));

        let live_upstream_ver = crate::geofabrik::fetch_snapshot_version(r).await;

        let md5_url = crate::geofabrik::resolve_md5_url(r);
        let upstream_info = match client.get(&md5_url).send().await {
            Ok(resp) if resp.status().is_success() => {
                let text = resp.text().await.unwrap_or_default();
                let upstream_hash = text.split_whitespace().next().unwrap_or("").to_lowercase();
                if upstream_hash.len() == 32 && upstream_hash.chars().all(|c| c.is_ascii_hexdigit())
                {
                    Some(upstream_hash)
                } else {
                    None
                }
            }
            _ => None,
        };

        let (status, current_ver, upstream_ver) = if let Some(entry) = hosted_entry {
            let hosted_version = entry.version.as_str();
            let hosted_md5 = entry.checksum.as_str();

            if let Some(ref live_hash) = upstream_info {
                if live_hash == hosted_md5 {
                    (
                        "UP_TO_DATE",
                        hosted_version.to_string(),
                        hosted_version.to_string(),
                    )
                } else {
                    (
                        "UPDATE_AVAILABLE",
                        hosted_version.to_string(),
                        live_upstream_ver,
                    )
                }
            } else {
                any_unavailable = true;
                (
                    "UNAVAILABLE",
                    hosted_version.to_string(),
                    "UNAVAILABLE".to_string(),
                )
            }
        } else {
            if upstream_info.is_some() {
                ("NOT_HOSTED", "—".to_string(), live_upstream_ver)
            } else {
                any_unavailable = true;
                ("UNAVAILABLE", "—".to_string(), "UNAVAILABLE".to_string())
            }
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
    } else {
        println!(
            "{:<25} {:<18} {:<15} {:<15}",
            "REGION", "STATUS", "HOSTED VER", "UPSTREAM VER"
        );
        println!("{}", "-".repeat(75));

        for res in &results {
            let status_badge = match res["status"].as_str().unwrap_or("") {
                "UP_TO_DATE" => "UP_TO_DATE".green(),
                "UPDATE_AVAILABLE" => "UPDATE_AVAILABLE".yellow(),
                "UNAVAILABLE" => "UNAVAILABLE".red(),
                _ => "NOT_HOSTED".dimmed(),
            };

            println!(
                "{:<25} {:<27} {:<15} {:<15}",
                res["region"].as_str().unwrap_or(""),
                status_badge,
                res["current_version"].as_str().unwrap_or(""),
                res["upstream_version"].as_str().unwrap_or("")
            );
        }
    }

    if region_opt.is_some() && any_unavailable {
        eprintln!(
            "{} Upstream update check failed: network unavailable or upstream returned non-success code",
            "✖".red()
        );
        std::process::exit(1);
    }

    Ok(())
}
