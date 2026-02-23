#!/usr/bin/env bash
set -e

SYSTEM=${1:-"tests/systems/generic"}
DIR=${2:-"vm-test-$(basename "$SYSTEM")"}

nix-scribe "$SYSTEM" -m 2 -o "$DIR" --confirm

cd "$DIR"
nixos-rebuild build-vm -I nixos-config="./configuration.nix"

exec ./result/bin/run-nixos-vm
