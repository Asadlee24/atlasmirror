use std::fs;
use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Generating SPEL IDL for osm_registry...");

    let idl = serde_json::json!({
        "version": "0.1.0",
        "name": "osm_registry",
        "instructions": [
            {
                "name": "initialize",
                "discriminator": [175, 175, 109, 31, 13, 152, 155, 237],
                "execution": "public",
                "accounts": [
                    {
                        "name": "state",
                        "is_mut": true,
                        "is_signer": false,
                        "pda": {
                            "seeds": ["literal:state"]
                        }
                    },
                    {
                        "name": "owner",
                        "is_mut": false,
                        "is_signer": true
                    }
                ],
                "args": []
            },
            {
                "name": "register_region",
                "discriminator": [211, 8, 232, 43, 249, 138, 241, 117],
                "execution": "public",
                "accounts": [
                    {
                        "name": "state",
                        "is_mut": true,
                        "is_signer": false,
                        "pda": {
                            "seeds": ["literal:state"]
                        }
                    },
                    {
                        "name": "region_account",
                        "is_mut": true,
                        "is_signer": false,
                        "pda": {
                            "seeds": ["literal:region", "arg:region"]
                        }
                    },
                    {
                        "name": "cid_account",
                        "is_mut": true,
                        "is_signer": false,
                        "pda": {
                            "seeds": ["literal:cid", "arg:cid"]
                        }
                    },
                    {
                        "name": "signer",
                        "is_mut": false,
                        "is_signer": true
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
                ]
            },
            {
                "name": "batch_register",
                "discriminator": [92, 144, 215, 68, 12, 88, 102, 194],
                "execution": "public",
                "accounts": [
                    {
                        "name": "state",
                        "is_mut": true,
                        "is_signer": false,
                        "pda": {
                            "seeds": ["literal:state"]
                        }
                    },
                    {
                        "name": "signer",
                        "is_mut": false,
                        "is_signer": true
                    }
                ],
                "args": [
                    {
                        "name": "records",
                        "type": {
                            "vec": { "defined": "RegisterRegionArgs" }
                        }
                    }
                ]
            }
        ],
        "accounts": [
            {
                "name": "GlobalRegistryState",
                "type": {
                    "kind": "struct",
                    "fields": [
                        { "name": "total_regions", "type": "u64" },
                        { "name": "last_updated", "type": "u64" }
                    ]
                }
            },
            {
                "name": "RegionRecord",
                "type": {
                    "kind": "struct",
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
                    ]
                }
            }
        ],
        "types": [
            {
                "name": "RegionLevel",
                "type": {
                    "kind": "enum",
                    "variants": [
                        { "name": "Country" },
                        { "name": "Subregion" }
                    ]
                }
            },
            {
                "name": "RegisterRegionArgs",
                "type": {
                    "kind": "struct",
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
                    ]
                }
            }
        ]
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
