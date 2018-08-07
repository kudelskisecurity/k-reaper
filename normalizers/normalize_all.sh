#!/usr/bin/env bash

set -x

basedir="$(dirname ${BASH_SOURCE[0]})"
echo "using basedir: ${basedir}"

scripts=(
github_ssh_normalize.py
gitlab_ssh_normalize.py
sks_pgp_normalize.py
keybase_pgp_normalize.py
github_pgp_normalize.py
)

for script in ${scripts[@]}; do
    time ${basedir}/${script}
done
