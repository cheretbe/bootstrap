#!/bin/bash

set -euo pipefail

batch_mode=""
while getopts ":b" opt; do
  case ${opt} in
    b ) batch_mode="--batch-mode"
      ;;
    \? ) echo "Usage: offline.sh [-b]"
      ;;
  esac
done

project_dir="$( cd "$( /usr/bin/dirname "${BASH_SOURCE[0]}" )/../.." >/dev/null 2>&1 && pwd )"

if [ ! -d ${HOME}/.cache/venv/test_env ]; then
  cat ${project_dir}/setup_venv.py | /usr/bin/python3 - test_env \
    --requirement ${project_dir}/tests/setup_venv/requirements.txt ${batch_mode}
fi
