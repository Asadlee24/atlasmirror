use colored::Colorize;
use serde_json::json;

pub fn execute(
    region_opt: Option<&str>,
    json_output: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let check_list = match region_opt {
        Some(r) => vec![r],
        None => vec![
            "asia/pakistan",
            "europe/germany",
            "us/california",
            "us/texas",
        ],
    };

    let mut results = Vec::new();

    for r in check_list {
        let (status, current_ver, upstream_ver) = match r {
            "asia/pakistan" => ("UP_TO_DATE", "2026-09-19", "2026-09-19"),
            "europe/germany" => ("UPDATE_AVAILABLE", "2026-09-17", "2026-09-19"),
            "us/california" => ("UP_TO_DATE", "2026-09-19", "2026-09-19"),
            "us/texas" => ("NOT_HOSTED", "—", "2026-09-19"),
            _ => ("UP_TO_DATE", "2026-09-19", "2026-09-19"),
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
