# Upstream Snapshot — AtlasMirror for Logos LP-0018

This document records the exact upstream repository commit SHAs, tags, and dependencies checked at the start of implementation, ensuring reproducibility and alignment with official Logos tooling.

| Component / Resource | Repository | Checked Commit SHA | Date Checked | Status / Notes |
|---|---|---|---|---|
| **LP-0018 Specification** | `logos-co/lambda-prize` | `43c72fd59ef9b1ef148e1629a8e7981bee401de5` | 2026-09-17 | Authoritative prize spec; Status: `Open` |
| **Logos Module Builder** | `logos-co/logos-module-builder` | `0c5b062fd11b20f85cc7c0720ddcac1cbbb46c4c` | 2026-09-18 | `mkLogosModule` and `mkLogosQmlModule` builders |
| **SPEL Framework** | `logos-co/spel` | `512e95912a4e374686435601d6614b60a179a183` | 2026-09-18 | Anchor-like framework for LEZ programs |
| **Logos Execution Zone (LEZ)** | `logos-blockchain/logos-execution-zone` | `dc73d55bec27b8b2f0166318bc176db5f62a78f8` | 2026-09-18 | Dev branch, LEZ execution engine & `cycle_bench` |
| **Logos Basecamp** | `logos-co/logos-basecamp` | `0157a66386899d9a7627e52f59e03ffe6ca13a51` | 2026-09-18 | Logos desktop shell & plugin host |
| **Module Catalog Base** | `logos-co/logos-modules-release-base` | `ab881acb342b0802a08649cf0bc475fa7b8dfd87` | 2026-09-18 | Catalog template for `logos-repo.json` releases |
| **Module Release Action** | `logos-co/logos-modules-release-action` | `master` | 2026-09-18 | GitHub Action for publishing .lgx releases |
| **Logos Storage Module** | `logos-storage-docs` | `v0.2.0` | 2026-09-18 | Content-addressed CID storage & retrieval |
| **LP-0017 Reference** | `aegonmyy/logoz` | `365273d` | 2026-09-18 | Whistleblower storage + SPEL registry reference |
| **Geofabrik Machine Index** | `download.geofabrik.de` | `index-v1-nogeom.json` | 2026-09-19 | 555 features; canonical snapshot source |

---

## Toolchain & Environment Matrix

- **Rust**: 1.80+ (stable) / RISC0 toolchain for SPEL guest compilation
- **Nix**: Flakes-enabled (`nix 2.18+`)
- **CMake**: 3.22+
- **Qt / QML**: Qt 6.5+ (Qt Quick, Qt Quick Controls 2, Qt Remote Objects)
- **Target OS**: Linux x86_64 (Ubuntu 22.04 LTS / 24.04 LTS), macOS Apple Silicon (Darwin arm64)
- **Development Fallback**: Windows Subsystem for Linux (WSL2 with Ubuntu)
