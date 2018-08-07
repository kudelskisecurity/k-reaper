#!/bin/bash

config_path="/etc/k-reaper/config.json"

basedir=$(cat ${config_path} | jq -r .basedir)
dump_url="http://keys.niif.hu/keydump/"
curdate=$(date +%Y%m%d-%H%M%S)
outdir="${basedir}/collector-cache/pgp/pgp-${curdate}"

echo creating output directory ${outdir}
mkdir -p ${outdir}

cd ${outdir}

wget -c -r -p -e robots=off -N -l1 --cut-dirs=3 -nH ${dump_url}