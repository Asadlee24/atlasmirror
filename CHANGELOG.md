# Changelog

All notable changes to AtlasMirror will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Authoritative upstream snapshot and LP-0018 verification matrix.
- Predefined closed region catalog with 72 non-overlapping entries (48 countries + 24 subregions).
- SPEL on-chain LEZ registry program (`osm-registry`) with single and batch registration.
- SPEL-generated JSON IDL at `osm-registry/idl/osm_registry.json`.
- Logos Core SDK module (`atlasmirror-sdk`) with universal interface for Basecamp apps.
- Logos Basecamp QML desktop application (`atlasmirror-app`) with dark/light sober design.
- Multi-functional CLI (`atlasmirror-cli`) supporting discovery, hosting, downloading, local import, and `doctor`.
- Third-party consumer example module (`examples/consumer-module`).
- Full end-to-end test runner and local sequencer demo script (`scripts/demo.sh`).
- Continuous Integration workflows for Linux x86_64 and macOS Apple Silicon.
