{
  description = "AtlasMirror: Decentralized OpenStreetMap Snapshot Distribution for Logos";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    rust-overlay = {
      url = "github:oxalica/rust-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    logos-module-builder = {
      url = "github:logos-co/logos-module-builder/0c5b062fd11b20f85cc7c0720ddcac1cbbb46c4c";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, rust-overlay, logos-module-builder, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        overlays = [ (import rust-overlay) ];
        pkgs = import nixpkgs {
          inherit system overlays;
        };
        rustToolchain = pkgs.rust-bin.stable.latest.default.override {
          extensions = [ "rust-src" "clippy" "rustfmt" ];
        };
      in
      {
        packages = {
          atlasmirror-cli = pkgs.rustPlatform.buildRustPackage {
            pname = "atlasmirror-cli";
            version = "0.1.0";
            src = ./atlasmirror-cli;
            cargoLock = {
              lockFile = ./atlasmirror-cli/Cargo.lock;
            };
            nativeBuildInputs = [ pkgs.pkg-config ];
            buildInputs = [ pkgs.openssl ];
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            rustToolchain
            cargo
            rustc
            cmake
            ninja
            pkg-config
            openssl
            curl
            jq
            qt6.qtbase
            qt6.qtdeclarative
            qt6.qtremoteobjects
          ];

          shellHook = ''
            export ATLASMIRROR_ROOT="$(pwd)"
            export RUST_BACKTRACE=1
            echo "AtlasMirror development environment active (Logos LP-0018)"
          '';
        };
      }
    );
}
