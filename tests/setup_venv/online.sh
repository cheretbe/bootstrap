#!/bin/bash

set -euo pipefail

script_dir="$( cd "$( /usr/bin/dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

curl -s https://raw.githubusercontent.com/cheretbe/bootstrap/develop/setup_venv.py?flush_cache=True | /usr/bin/python3 - test_env --requirement ${script_dir}/requirements.txt --batch-mode
