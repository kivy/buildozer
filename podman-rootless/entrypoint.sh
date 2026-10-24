#!/bin/bash
set -euo pipefail

. ~/.venv/bin/activate
buildozer "$@"
