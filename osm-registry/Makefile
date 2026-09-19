# SPEL OSM Registry Makefile
# Reference: https://github.com/logos-co/spel

SEQUENCER_URL ?= http://127.0.0.1:9944
KEYPAIR ?= ~/.logos/dev-keypair.json

.PHONY: all build idl deploy cli clean

all: build idl

build:
	@echo "Building SPEL OSM Registry guest binary..."
	cargo build --release

idl:
	@echo "Generating SPEL IDL..."
	cargo run --bin generate_idl
	@echo "SPEL IDL generated at idl/osm_registry.json"

deploy:
	@echo "Deploying OSM Registry to LEZ Sequencer at $(SEQUENCER_URL)..."
	@if ! command -v spel >/dev/null 2>&1 && ! command -v spel-cli >/dev/null 2>&1; then \
		echo "[BLOCKED] 'spel' CLI not found. Please install from https://github.com/logos-co/spel"; \
		exit 2; \
	fi
	spel deploy --sequencer-url $(SEQUENCER_URL) --keypair $(KEYPAIR)

cli:
	@if ! command -v spel >/dev/null 2>&1 && ! command -v spel-cli >/dev/null 2>&1; then \
		echo "[BLOCKED] 'spel' CLI not found. Please install from https://github.com/logos-co/spel"; \
		exit 2; \
	fi
	spel --idl idl/osm_registry.json $(ARGS)

clean:
	cargo clean
