# Contributing to AtlasMirror

Thank you for your interest in contributing to AtlasMirror. We welcome contributions adhering to the Logos architectural standards, rigorous code quality, and strict OpenStreetMap licensing principles.

## Development Principles

1. **Logos Native**: Use Logos protocols (Logos Storage, LEZ SPEL programs, Logos Module Builder).
2. **Deterministic Verification**: Never store or register unverified data. All PBF snapshots must have their MD5 checksum verified at import/host time against Geofabrik.
3. **No Central Reliance**: Geofabrik is only an external canonical snapshot provider and fallback. AtlasMirror must remain fully operational for discovering and downloading hosted snapshots without central external services.
4. **Clean Code & Tests**: All features must include comprehensive unit and integration tests. Default branch must remain green.

## Code Standards

- **Rust**: Follow standard `rustfmt` and `clippy`. No `unsafe` without explicit documented justification.
- **C++**: Modern C++17, formatted with `clang-format`.
- **QML**: Follow official Logos design guidelines: sober, high-contrast, #000000 / #FFFFFF, no Web3 clichés.

## Commit Message Guidelines

We follow Conventional Commits:

- `feat(registry): implement batch region registration`
- `feat(storage): add verified PBF upload`
- `feat(source): parse Geofabrik region index`
- `feat(app): add region discovery screen`
- `feat(cli): add host command`
- `test(registry): cover invalid region records`
- `docs: add LP-0018 compliance matrix`
- `fix(storage): resume interrupted upload`
- `chore: pin Logos module dependencies`

## Pull Request Process

1. Fork the repository and create your branch from `main`.
2. Ensure tests pass: `cargo test` and `bash scripts/test.sh`.
3. Submit a pull request following the PR template.
