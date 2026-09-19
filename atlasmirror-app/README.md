# AtlasMirror Basecamp Application

Native Logos Basecamp desktop GUI module for decentralized OpenStreetMap snapshot distribution.

Built with `logos-module-builder` using `mkLogosQmlModule` (`type: "ui_qml"`).

## Features

- **Regions View**: Filterable discovery table for the 72 predefined non-overlapping regions.
- **Hosting Queue**: Granular pipeline state machine tracking downloads, MD5 verification, Logos Storage uploads, and LEZ registration.
- **Downloads View**: Monitor active and completed local snapshot downloads.
- **Registry View**: Direct inspector for on-chain LEZ SPEL queries by region, parent, or CID.
- **Settings View**: Network endpoints and concurrency configuration. Zero telemetry by default.
- **About View**: Official licensing, ODbL attribution, and Logos ecosystem metadata.

## Development & Run

```bash
# Run in standalone app mode
nix run .

# Or build the .lgx package
nix build .#lgx
```
