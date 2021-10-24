# bootstrap


### setup_venv.py
```bash
/usr/bin/curl -s https://raw.githubusercontent.com/cheretbe/bootstrap/master/setup_venv.py?flush_cache=True \
  | /usr/bin/python3 - env_name
```
Script usage
```bash
#!/bin/bash

set -euo pipefail

script_dir="$( cd "$( /usr/bin/dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# [!] Change env_name to actual venv name
if [ ! -d ${HOME}/.cache/venv/env_name ]; then
  /usr/bin/curl -s https://raw.githubusercontent.com/cheretbe/bootstrap/master/setup_venv.py?flush_cache=True \
    | /usr/bin/python3 - env_name --requirement ${script_dir}/requirements.txt --batch-mode
fi

"${HOME}/.cache/venv/env_name/bin/python3" ${script_dir}/script.py "$@"

```

### enable_winrm_over_https.ps1

```batch
powershell "Invoke-Command -ScriptBlock ([Scriptblock]::Create(((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/cheretbe/bootstrap/master/enable_winrm_over_https.ps1?flush_cache=True'))))"
```

<details>
  <summary>:warning: "-KeepHTTP" can't be passed as switch when using Invoke-Command</summary>

  * https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/invoke-command?view=powershell-5.1
  **Note to -ScriptBlock:**<br>
  Parameters for the scriptblock can only be passed in from ArgumentList by
  position. Switch parameters cannot be passed by position. If you need a
  parameter that behaves like a SwitchParameter type, use a Boolean type instead.
</details>

```batch
:: Keeping default HTTP listener (useful when debugging)
powershell "Invoke-Command -ScriptBlock ([Scriptblock]::Create(((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/cheretbe/bootstrap/master/enable_winrm_over_https.ps1?flush_cache=True')))) -ArgumentList @($TRUE)"
```
