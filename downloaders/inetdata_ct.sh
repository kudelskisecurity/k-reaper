#!/usr/bin/env bash

config_path="/etc/k-reaper/config.json"
inetdata_bin_path=$(cat ${config_path} | jq -r .inetdata_bin_path)

${inetdata_bin_path}/daily_ct.sh
${inetdata_bin_path}/normalize.sh -s ct
