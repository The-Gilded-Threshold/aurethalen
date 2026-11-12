#!/usr/bin/env bash
set -euo pipefail
python "$(dirname "$0")/build.py" "$@"
