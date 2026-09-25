#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
MANIFEST="$ROOT/al1scan/Cargo.toml"
RELEASE="$ROOT/al1scan/target/release/al1scan"

if [[ -x "$RELEASE" ]]; then
    exec "$RELEASE" "$@"
fi

if ! command -v cargo >/dev/null 2>&1; then
    printf '%s\n' 'Cargo is required to run al1scan. Install/enable Rust or build the release binary first.' >&2
    exit 127
fi

exec cargo run --quiet --manifest-path "$MANIFEST" -- "$@"
