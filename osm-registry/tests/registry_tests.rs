use borsh::to_vec;
use osm_registry_core::{
    process_instruction, BatchRegisterArgs, GlobalRegistryState, RegionLevel, RegionRecord,
    RegisterRegionArgs, RegistryError, RegistryInstruction, MAX_BATCH_SIZE,
};

#[test]
fn test_initialize_instruction() {
    let mut state = GlobalRegistryState {
        total_regions: 99,
        last_updated: 99,
    };
    let mut records = Vec::new();

    let init_data = to_vec(&RegistryInstruction::Initialize).unwrap();
    let res = process_instruction(&init_data, &mut state, &mut records);

    assert!(res.is_ok());
    assert_eq!(state.total_regions, 0);
    assert_eq!(state.last_updated, 0);
}

#[test]
fn test_register_and_lookup_country() {
    let mut state = GlobalRegistryState::default();
    let mut records = Vec::new();

    let args = RegisterRegionArgs {
        region: "asia/pakistan".to_string(),
        parent: None,
        level: RegionLevel::Country,
        cid: "bafybeic7vj2k...".to_string(),
        source_url: "https://download.geofabrik.de/asia/pakistan-latest.osm.pbf".to_string(),
        checksum: "378df25f824177ebcbe9aa11d88bbd6b".to_string(),
        version: "2026-09-19".to_string(),
        hosted: true,
        timestamp: 1726747200,
    };

    let data = to_vec(&RegistryInstruction::RegisterRegion(args.clone())).unwrap();
    let res = process_instruction(&data, &mut state, &mut records);

    assert!(res.is_ok());
    assert_eq!(state.total_regions, 1);
    assert_eq!(state.last_updated, 1726747200);

    // Lookup by region
    let found = records.iter().find(|r| r.region == "asia/pakistan");
    assert!(found.is_some());
    let r = found.unwrap();
    assert_eq!(r.level, RegionLevel::Country);
    assert_eq!(r.parent, None);
    assert_eq!(r.cid, "bafybeic7vj2k...");

    // Lookup by CID
    let found_by_cid = records.iter().find(|r| r.cid == "bafybeic7vj2k...");
    assert!(found_by_cid.is_some());
    assert_eq!(found_by_cid.unwrap().region, "asia/pakistan");
}

#[test]
fn test_register_subregion_and_lookup_by_parent() {
    let mut state = GlobalRegistryState::default();
    let mut records = Vec::new();

    let cal = RegisterRegionArgs {
        region: "us/california".to_string(),
        parent: Some("us".to_string()),
        level: RegionLevel::Subregion,
        cid: "bafybeid6xk1m...".to_string(),
        source_url: "https://download.geofabrik.de/north-america/us/california-latest.osm.pbf"
            .to_string(),
        checksum: "0123456789abcdef0123456789abcdef".to_string(),
        version: "2026-09-19".to_string(),
        hosted: true,
        timestamp: 1726747201,
    };

    let tex = RegisterRegionArgs {
        region: "us/texas".to_string(),
        parent: Some("us".to_string()),
        level: RegionLevel::Subregion,
        cid: "bafybeie4mk2p...".to_string(),
        source_url: "https://download.geofabrik.de/north-america/us/texas-latest.osm.pbf"
            .to_string(),
        checksum: "11223344556677889900aabbccddeeff".to_string(),
        version: "2026-09-19".to_string(),
        hosted: true,
        timestamp: 1726747202,
    };

    let d1 = to_vec(&RegistryInstruction::RegisterRegion(cal)).unwrap();
    let d2 = to_vec(&RegistryInstruction::RegisterRegion(tex)).unwrap();

    assert!(process_instruction(&d1, &mut state, &mut records).is_ok());
    assert!(process_instruction(&d2, &mut state, &mut records).is_ok());

    assert_eq!(state.total_regions, 2);

    // Lookup all subregions for parent "us"
    let us_children: Vec<&RegionRecord> = records
        .iter()
        .filter(|r| r.parent.as_deref() == Some("us"))
        .collect();
    assert_eq!(us_children.len(), 2);
    assert!(us_children.iter().any(|r| r.region == "us/california"));
    assert!(us_children.iter().any(|r| r.region == "us/texas"));
}

#[test]
fn test_update_region_and_timestamp_ordering() {
    let mut state = GlobalRegistryState::default();
    let mut records = Vec::new();

    let initial = RegisterRegionArgs {
        region: "europe/germany".to_string(),
        parent: None,
        level: RegionLevel::Country,
        cid: "cid_v1".to_string(),
        source_url: "https://download.geofabrik.de/europe/germany-latest.osm.pbf".to_string(),
        checksum: "e9c0c1b7a2d61d87e025b9059f131a42".to_string(),
        version: "2026-09-18".to_string(),
        hosted: true,
        timestamp: 1000,
    };

    let d_init = to_vec(&RegistryInstruction::RegisterRegion(initial)).unwrap();
    assert!(process_instruction(&d_init, &mut state, &mut records).is_ok());

    // Regression timestamp update should fail
    let regression = RegisterRegionArgs {
        region: "europe/germany".to_string(),
        parent: None,
        level: RegionLevel::Country,
        cid: "cid_v2".to_string(),
        source_url: "https://download.geofabrik.de/europe/germany-latest.osm.pbf".to_string(),
        checksum: "e9c0c1b7a2d61d87e025b9059f131a42".to_string(),
        version: "2026-09-17".to_string(),
        hosted: true,
        timestamp: 900, // Older timestamp
    };
    let d_reg = to_vec(&RegistryInstruction::RegisterRegion(regression)).unwrap();
    let err = process_instruction(&d_reg, &mut state, &mut records);
    assert_eq!(
        err,
        Err(RegistryError::TimestampRegression {
            existing_ts: 1000,
            new_ts: 900
        })
    );

    // Valid forward timestamp update should succeed
    let forward = RegisterRegionArgs {
        region: "europe/germany".to_string(),
        parent: None,
        level: RegionLevel::Country,
        cid: "cid_v2".to_string(),
        source_url: "https://download.geofabrik.de/europe/germany-latest.osm.pbf".to_string(),
        checksum: "e9c0c1b7a2d61d87e025b9059f131a42".to_string(),
        version: "2026-09-20".to_string(),
        hosted: true,
        timestamp: 1100, // Newer timestamp
    };
    let d_fwd = to_vec(&RegistryInstruction::RegisterRegion(forward)).unwrap();
    assert!(process_instruction(&d_fwd, &mut state, &mut records).is_ok());
    assert_eq!(state.total_regions, 1); // Total regions unchanged
    assert_eq!(records[0].cid, "cid_v2");
    assert_eq!(records[0].timestamp, 1100);
}

#[test]
fn test_batch_register_success_and_limits() {
    let mut state = GlobalRegistryState::default();
    let mut records = Vec::new();

    let mut batch_records = Vec::new();
    for (i, (path, level, parent)) in osm_registry_core::CLOSED_SET_REGIONS
        .iter()
        .take(25)
        .enumerate()
    {
        batch_records.push(RegisterRegionArgs {
            region: path.to_string(),
            parent: parent.map(|s| s.to_string()),
            level: *level,
            cid: format!("cid_{}", i),
            source_url: format!("https://download.geofabrik.de/{}-latest.osm.pbf", path),
            checksum: "0123456789abcdef0123456789abcdef".to_string(),
            version: "2026-09-19".to_string(),
            hosted: true,
            timestamp: 1000 + i as u64,
        });
    }

    let batch = BatchRegisterArgs {
        records: batch_records,
    };
    let data = to_vec(&RegistryInstruction::BatchRegister(batch)).unwrap();

    assert!(process_instruction(&data, &mut state, &mut records).is_ok());
    assert_eq!(state.total_regions, 25);
    assert_eq!(state.last_updated, 1024);

    // Over maximum batch size fails
    let valid_proto = RegisterRegionArgs {
        region: "europe/germany".to_string(),
        parent: None,
        level: RegionLevel::Country,
        cid: "cid".to_string(),
        source_url: "https://download.geofabrik.de/europe/germany-latest.osm.pbf".to_string(),
        checksum: "0123456789abcdef0123456789abcdef".to_string(),
        version: "2026-09-19".to_string(),
        hosted: true,
        timestamp: 2000,
    };
    let too_big = BatchRegisterArgs {
        records: vec![valid_proto; MAX_BATCH_SIZE + 1],
    };
    let data_big = to_vec(&RegistryInstruction::BatchRegister(too_big)).unwrap();
    assert_eq!(
        process_instruction(&data_big, &mut state, &mut records),
        Err(RegistryError::BatchTooLarge(MAX_BATCH_SIZE + 1))
    );
}

#[test]
fn test_arbitrary_test_records_disallowed() {
    let mut state = GlobalRegistryState::default();
    let mut records = Vec::new();

    let args = RegisterRegionArgs {
        region: "test/arbitrary_region".to_string(),
        parent: None,
        level: RegionLevel::Country,
        cid: "bafybeic7vj2k...".to_string(),
        source_url: "https://example.com/test.osm.pbf".to_string(),
        checksum: "378df25f824177ebcbe9aa11d88bbd6b".to_string(),
        version: "2026-09-19".to_string(),
        hosted: true,
        timestamp: 1726747200,
    };

    let data = to_vec(&RegistryInstruction::RegisterRegion(args)).unwrap();
    let res = process_instruction(&data, &mut state, &mut records);
    assert_eq!(
        res,
        Err(RegistryError::DisallowedRegion(
            "test/arbitrary_region".to_string()
        ))
    );
}
