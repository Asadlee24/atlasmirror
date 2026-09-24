use std::fs;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Generating SPEL IDL for osm_registry...");

    let idl = serde_json::json!({
        "accounts": [
            {
                "name": "GlobalRegistryState",
                "type": {
                    "fields": [
                        { "name": "total_regions", "type": "u64" },
                        { "name": "last_updated", "type": "u64" }
                    ],
                    "kind": "struct"
                }
            },
            {
                "name": "RegionRecord",
                "type": {
                    "fields": [
                        { "name": "region", "type": "string" },
                        { "name": "parent", "type": { "option": "string" } },
                        { "name": "level", "type": { "defined": "RegionLevel" } },
                        { "name": "cid", "type": "string" },
                        { "name": "source_url", "type": "string" },
                        { "name": "checksum", "type": "string" },
                        { "name": "version", "type": "string" },
                        { "name": "hosted", "type": "bool" },
                        { "name": "timestamp", "type": "u64" }
                    ],
                    "kind": "struct"
                }
            }
        ],
        "instructions": [
            {
                "accounts": [
                    {
                        "is_mut": true,
                        "is_signer": false,
                        "name": "state",
                        "pda": {
                            "seeds": [
                                { "kind": "const", "value": "state" }
                            ]
                        }
                    },
                    {
                        "is_mut": false,
                        "is_signer": true,
                        "name": "owner"
                    }
                ],
                "args": [],
                "discriminator": [175, 175, 109, 31, 13, 152, 155, 237],
                "execution": {
                    "public": true
                },
                "name": "initialize"
            },
            {
                "accounts": [
                    {
                        "is_mut": true,
                        "is_signer": false,
                        "name": "state",
                        "pda": {
                            "seeds": [
                                { "kind": "const", "value": "state" }
                            ]
                        }
                    },
                    {
                        "is_mut": false,
                        "is_signer": true,
                        "name": "signer"
                    }
                ],
                "args": [
                    { "name": "region", "type": "string" },
                    { "name": "parent", "type": { "option": "string" } },
                    { "name": "level", "type": { "defined": "RegionLevel" } },
                    { "name": "cid", "type": "string" },
                    { "name": "source_url", "type": "string" },
                    { "name": "checksum", "type": "string" },
                    { "name": "version", "type": "string" },
                    { "name": "hosted", "type": "bool" },
                    { "name": "timestamp", "type": "u64" }
                ],
                "discriminator": [211, 8, 232, 43, 249, 138, 241, 117],
                "execution": {
                    "public": true
                },
                "name": "register_region"
            },
            {
                "accounts": [
                    {
                        "is_mut": true,
                        "is_signer": false,
                        "name": "state",
                        "pda": {
                            "seeds": [
                                { "kind": "const", "value": "state" }
                            ]
                        }
                    },
                    {
                        "is_mut": false,
                        "is_signer": true,
                        "name": "signer"
                    }
                ],
                "args": [
                    {
                        "name": "records",
                        "type": {
                            "vec": { "defined": "RegisterRegionArgs" }
                        }
                    }
                ],
                "discriminator": [92, 144, 215, 68, 12, 88, 102, 194],
                "execution": {
                    "public": true
                },
                "name": "batch_register"
            }
        ],
        "name": "osm_registry",
        "types": [
            {
                "kind": "enum",
                "name": "RegionLevel",
                "variants": [
                    { "name": "Country" },
                    { "name": "Subregion" }
                ]
            },
            {
                "fields": [
                    { "name": "region", "type": "string" },
                    { "name": "parent", "type": { "option": "string" } },
                    { "name": "level", "type": { "defined": "RegionLevel" } },
                    { "name": "cid", "type": "string" },
                    { "name": "source_url", "type": "string" },
                    { "name": "checksum", "type": "string" },
                    { "name": "version", "type": "string" },
                    { "name": "hosted", "type": "bool" },
                    { "name": "timestamp", "type": "u64" }
                ],
                "kind": "struct",
                "name": "RegisterRegionArgs"
            }
        ],
        "version": "0.1.0"
    });

    let idl_dir = Path::new("idl");
    if !idl_dir.exists() {
        fs::create_dir_all(idl_dir)?;
    }

    let out_path = idl_dir.join("osm_registry.json");
    let json_str = format!("{}\n", serde_json::to_string_pretty(&idl)?);
    fs::write(&out_path, json_str)?;
    println!("Successfully generated IDL at: {}", out_path.display());

    Ok(())
}
