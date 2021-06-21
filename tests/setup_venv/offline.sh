#!/bin/bash

set -euo pipefail

script_dir="$( cd "$( /usr/bin/dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cat /bootstrap/setup_venv.py | /usr/bin/python3 - test_env --requirement ${script_dir}/requirements.txt --batch-mode
