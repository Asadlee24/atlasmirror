mod commands;
mod geofabrik;
pub mod registry;
mod storage;

use clap::{Args, Parser, Subcommand};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "atlasmirror")]
#[command(about = "Decentralized OpenStreetMap snapshot distribution system on Logos", long_about = None)]
#[command(version = "0.1.0")]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// Output results in JSON format for scripting and automation
    #[arg(long, global = true)]
    json: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// Browse and inspect predefined OpenStreetMap regions
    Regions(RegionsArgs),

    /// Host a region snapshot to Logos Storage and register on LEZ
    Host(HostArgs),

    /// Download a verified snapshot by region path (Logos Storage or fallback)
    Download(DownloadArgs),

    /// Look up on-chain registry records by region, parent, or CID
    Lookup(LookupArgs),

    /// Check for newer upstream Geofabrik snapshots
    Updates(UpdatesArgs),

    /// Inspect LEZ on-chain registry configuration and raw state
    Registry(RegistryArgs),

    /// Diagnose system, toolchain, and network dependencies
    Doctor,
}

#[derive(Args)]
struct RegionsArgs {
    #[command(subcommand)]
    subcommand: RegionsSubcommand,
}

#[derive(Subcommand)]
enum RegionsSubcommand {
    /// List all predefined regions
    List {
        /// Filter by status: all, hosted, unhosted, updates
        #[arg(long)]
        filter: Option<String>,
    },
    /// Show detailed metadata for a specific region path
    Show {
        /// Canonical region path (e.g. "asia/pakistan")
        path: String,
    },
}

#[derive(Args)]
struct HostArgs {
    /// Single canonical region path to host
    #[arg(conflicts_with = "many")]
    region: Option<String>,

    /// Host multiple regions in batch
    #[arg(long, alias = "batch", num_args = 1..)]
    many: Option<Vec<String>>,

    /// Host a local .osm.pbf file after import-time checksum verification
    #[arg(long, num_args = 1..=2)]
    file: Option<Vec<String>>,

    /// Calculate estimated download size and simulate without transferring data
    #[arg(long)]
    dry_run: bool,
}

#[derive(Args)]
struct DownloadArgs {
    /// Canonical region path to download (e.g. "asia/pakistan")
    region: String,

    /// Output destination file path
    #[arg(long, default_value = "./snapshot.osm.pbf")]
    output: PathBuf,
}

#[derive(Args)]
struct LookupArgs {
    #[command(subcommand)]
    subcommand: Option<LookupSubcommand>,

    /// Look up on-chain record by canonical region path
    #[arg(long)]
    region: Option<String>,

    /// Look up all subregions for a decomposed parent country (e.g. "us")
    #[arg(long)]
    parent: Option<String>,

    /// Look up region record by Logos Storage CID
    #[arg(long)]
    cid: Option<String>,
}

#[derive(Subcommand)]
enum LookupSubcommand {
    /// Look up on-chain record by canonical region path
    Region { path: String },
    /// Look up all subregions for a decomposed parent country (e.g. "us")
    Parent { parent: String },
    /// Look up region record by Logos Storage CID
    Cid { cid: String },
}

#[derive(Args)]
struct UpdatesArgs {
    #[command(subcommand)]
    subcommand: Option<UpdatesSubcommand>,

    /// Optional specific region path to check
    region: Option<String>,
}

#[derive(Subcommand)]
enum UpdatesSubcommand {
    /// Check updates for a specific region
    Check { region: String },
}

#[derive(Args)]
struct RegistryArgs {
    #[command(subcommand)]
    subcommand: RegistrySubcommand,
}

#[derive(Subcommand)]
enum RegistrySubcommand {
    /// Display the deployed LEZ OSM Registry program ID
    ProgramId,
    /// Inspect raw on-chain state for a specific region
    Raw { region: String },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Regions(args) => match args.subcommand {
            RegionsSubcommand::List { filter } => {
                commands::regions::execute_list(filter.as_deref(), cli.json)?;
            }
            RegionsSubcommand::Show { path } => {
                commands::regions::execute_show(&path, cli.json)?;
            }
        },
        Commands::Host(args) => {
            if let Some(ref file_args) = args.file {
                let (region, path) = if file_args.len() == 2 {
                    (file_args[0].clone(), PathBuf::from(&file_args[1]))
                } else if file_args.len() == 1 {
                    if let Some(ref reg) = args.region {
                        (reg.clone(), PathBuf::from(&file_args[0]))
                    } else {
                        eprintln!(
                            "Error: Region path must be specified: atlasmirror-cli host <region> --file <path>"
                        );
                        std::process::exit(1);
                    }
                } else {
                    eprintln!("Error: Invalid arguments for --file");
                    std::process::exit(1);
                };
                commands::host::execute_host_file(&region, &path, cli.json).await?;
            } else if let Some(ref many) = args.many {
                commands::host::execute_host_many(many, args.dry_run, cli.json).await?;
            } else if let Some(ref region) = args.region {
                commands::host::execute_host_single(region, args.dry_run, cli.json).await?;
            } else {
                eprintln!(
                    "Error: Specify a region, --many <regions...>, or --file <region> <file>"
                );
                std::process::exit(1);
            }
        }
        Commands::Download(args) => {
            commands::download::execute(&args.region, &args.output, cli.json).await?;
        }
        Commands::Lookup(args) => {
            if let Some(sub) = args.subcommand {
                match sub {
                    LookupSubcommand::Region { path } => {
                        commands::lookup::execute_region(&path, cli.json)?;
                    }
                    LookupSubcommand::Parent { parent } => {
                        commands::lookup::execute_parent(&parent, cli.json)?;
                    }
                    LookupSubcommand::Cid { cid } => {
                        commands::lookup::execute_cid(&cid, cli.json)?;
                    }
                }
            } else if let Some(path) = args.region {
                commands::lookup::execute_region(&path, cli.json)?;
            } else if let Some(parent) = args.parent {
                commands::lookup::execute_parent(&parent, cli.json)?;
            } else if let Some(cid) = args.cid {
                commands::lookup::execute_cid(&cid, cli.json)?;
            } else {
                eprintln!("Error: Specify lookup target (region, parent, or cid)");
                std::process::exit(1);
            }
        }
        Commands::Updates(args) => {
            let target_region = match args.subcommand {
                Some(UpdatesSubcommand::Check { region }) => Some(region),
                None => args.region.filter(|r| r != "check"),
            };
            commands::updates::execute(target_region.as_deref(), cli.json).await?;
        }
        Commands::Registry(args) => match args.subcommand {
            RegistrySubcommand::ProgramId => {
                commands::registry::execute_program_id(cli.json)?;
            }
            RegistrySubcommand::Raw { region } => {
                commands::registry::execute_raw(&region, cli.json)?;
            }
        },
        Commands::Doctor => {
            commands::doctor::execute(cli.json).await?;
        }
    }

    Ok(())
}
