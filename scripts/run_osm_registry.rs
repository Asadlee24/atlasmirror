use common::transaction::LeeTransaction;
use lee::{
    AccountId, ProgramShardSelector, PublicTransaction, FeeDeclaration,
    program::Program,
    public_transaction::{Message, WitnessSet},
};
use borsh::{BorshDeserialize, BorshSerialize};
use sequencer_service_rpc::RpcClient as _;
use wallet::WalletCore;

#[derive(BorshSerialize, BorshDeserialize, Clone, Copy, Debug, PartialEq, Eq)]
pub enum RegionLevel {
    Country,
    Subregion,
}

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq, Eq)]
pub struct RegionRecord {
    pub region: String,
    pub parent: Option<String>,
    pub level: RegionLevel,
    pub cid: String,
    pub source_url: String,
    pub checksum: String,
    pub version: String,
    pub hosted: bool,
    pub timestamp: u64,
}

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq, Eq, Default)]
pub struct RegistryState {
    pub total_regions: u64,
    pub last_updated: u64,
    pub records: Vec<RegionRecord>,
}

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq, Eq)]
pub struct RegisterRegionArgs {
    pub region: String,
    pub parent: Option<String>,
    pub level: RegionLevel,
    pub cid: String,
    pub source_url: String,
    pub checksum: String,
    pub version: String,
    pub hosted: bool,
    pub timestamp: u64,
}

#[derive(BorshSerialize, BorshDeserialize, Clone, Debug, PartialEq, Eq)]
pub enum RegistryInstruction {
    Initialize,
    RegisterRegion(RegisterRegionArgs),
    BatchRegister(Vec<RegisterRegionArgs>),
}

#[tokio::main]
async fn main() {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 4 {
        eprintln!(
            "Usage: run_osm_registry program_path account_id initialize|register|query args"
        );
        std::process::exit(1);
    }

    let program_path = &args[1];
    let account_id: AccountId = args[2].parse().expect("Invalid account ID");
    let action = &args[3];

    // Initialize wallet
    let wallet_core = WalletCore::from_env().await.unwrap();

    // Load the program
    let bytecode: Vec<u8> = std::fs::read(program_path).unwrap();
    let program = Program::new(bytecode.into()).unwrap();
    let program_id = program.id();
    println!("Program ID: {:?}", program_id);

    if action == "query" {
        println!("Querying program account ID: {}", account_id);
        let shard_selector = ProgramShardSelector::new(account_id, account_id);
        let account_view = wallet_core
            .helm_owned()
            .get_account_view(shard_selector)
            .await
            .expect("Failed to get account view");
        println!("Account view: {:?}", account_view);

        let shard_bytes = account_view.data.shard(account_id).as_ref();
        println!("Shard bytes len: {}", shard_bytes.len());
        if !shard_bytes.is_empty() {
            let state: RegistryState = borsh::from_slice(shard_bytes).expect("Failed to deserialize state");
            println!("Decoded Registry State: {:?}", state);
            println!("Total regions: {}", state.total_regions);
            for r in &state.records {
                println!("REGION_MATCH: region={}, cid={}, url={}, checksum={}", r.region, r.cid, r.source_url, r.checksum);
            }
        } else {
            println!("Shard is empty!");
        }
        return;
    }

    // Build instruction
    let instruction: RegistryInstruction = match action.as_str() {
        "initialize" => {
            println!("Building Initialize instruction...");
            RegistryInstruction::Initialize
        }
        "register" => {
            if args.len() < 10 {
                eprintln!("Usage for register: run_osm_registry prog account register region cid checksum source_url version timestamp");
                std::process::exit(1);
            }
            let region = args[4].clone();
            let cid = args[5].clone();
            let checksum = args[6].clone();
            let source_url = args[7].clone();
            let version = args[8].clone();
            let timestamp: u64 = args[9].parse().expect("Invalid timestamp");

            let reg_args = RegisterRegionArgs {
                region,
                parent: None,
                level: RegionLevel::Country,
                cid,
                source_url,
                checksum,
                version,
                hosted: true,
                timestamp,
            };
            println!("Building RegisterRegion instruction for region: {}", reg_args.region);
            RegistryInstruction::RegisterRegion(reg_args)
        }
        other => panic!("Unknown action: {}", other),
    };

    let payer_id: AccountId = "6iArKUXxhUJqS7kCaPNhwMWt3ro71PDyBj7jwAyE2VQV"
        .parse()
        .expect("Invalid payer account ID");

    let payer_key = wallet_core
        .storage()
        .key_chain()
        .pub_account_signing_key(payer_id)
        .expect("Payer signing key should be in wallet")
        .clone();

    // Query nonces for payer_id
    let payer_nonces = wallet_core
        .get_accounts_nonces(&[payer_id])
        .await
        .expect("Failed to get payer account nonce from node");

    let nonces = vec![payer_nonces[0]];
    let fee = FeeDeclaration::new(payer_id, 2_000_000, 0, 134_400_000);

    // program_account_id is the header account where the program was deployed
    let message = Message::try_new_with_fees(
        account_id,
        vec![ProgramShardSelector::new(account_id, account_id)],
        nonces,
        instruction,
        fee,
    )
    .expect("Failed to create message");

    let signing_keys = [&payer_key];
    let witness_set = WitnessSet::for_message(&message, &signing_keys);
    let tx = PublicTransaction::new(message, witness_set);

    println!("Submitting transaction to LEZ sequencer...");
    let response = wallet_core
        .helm_owned()
        .send_transaction(LeeTransaction::Public(tx))
        .await
        .expect("Failed to send transaction");

    println!("Transaction confirmed! Response: {:?}", response);
}
