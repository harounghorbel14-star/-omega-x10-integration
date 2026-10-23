#!/usr/bin/env bash
# Wrapper: the helper ships inside the omega-core plugin so installed copies have it too.
exec "$(cd "$(dirname "$0")/.." && pwd)/plugins/omega-core/scripts/install-plugin-deps.sh" "$@"
