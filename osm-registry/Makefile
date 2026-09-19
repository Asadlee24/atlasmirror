# SPEL OSM Registry Makefile
# Reference: https://github.com/logos-co/spel and official SPEL project scaffold

PROGRAM_BIN ?= target/riscv32im-risc0-zkvm-elf/release/osm_registry
SEQUENCER_URL ?= http://127.0.0.1:9944

.PHONY: all build idl deploy clean

all: build idl

build:
	@echo "Building RISC Zero guest binary via cargo risczero..."
	@if ! command -v cargo-risczero >/dev/null 2>&1; then \
		echo "[BLOCKED] 'cargo-risczero' not found. Install via: cargo install cargo-risczero"; \
		exit 2; \
	fi
	cargo risczero build --manifest-path methods/guest/Cargo.toml

idl:
	@echo "Generating SPEL IDL from annotated #[lez_program] source..."
	cargo run --bin generate_idl
	@echo "SPEL IDL generated at idl/osm_registry.json"

deploy:
	@echo "Deploying OSM Registry to LEZ Sequencer via wallet..."
	@if ! command -v wallet >/dev/null 2>&1; then \
		echo "[BLOCKED] 'wallet' CLI not found. Please install LEZ wallet tooling from https://github.com/logos-blockchain/logos-execution-zone"; \
		exit 2; \
	fi
	wallet deploy-program $(PROGRAM_BIN)

clean:
	cargo clean
