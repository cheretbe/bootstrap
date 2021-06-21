# bootstrap


setup_venv.py
```bash
#!/bin/bash

set -euo pipefail

script_dir="$( cd "$( /usr/bin/dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# [!] Change env_name to actual venv name
if [ ! -d ${HOME}/.cache/venv/env_name ]; then
  curl -s https://raw.githubusercontent.com/cheretbe/bootstrap/master/setup_venv.py?flush_cache=True
    | /usr/bin/python3 - env_name --requirement ${script_dir}/requirements.txt --batch-mode
fi

"${HOME}/.cache/venv/env_name/bin/python3" ${script_dir}/script.py "$@"

```
