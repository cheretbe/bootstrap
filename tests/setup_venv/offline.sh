#!/bin/bash

set -euo pipefail

project_dir="$( cd "$( /usr/bin/dirname "${BASH_SOURCE[0]}" )/../.." >/dev/null 2>&1 && pwd )"

if [ ! -d ${HOME}/.cache/venv/test_env ]; then
  cat ${project_dir}/setup_venv.py | /usr/bin/python3 - test_env \
    --requirement ${project_dir}/tests/setup_venv/requirements.txt "$@"
fi
