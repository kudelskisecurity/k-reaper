#!/usr/bin/env bash

config_path="/etc/k-reaper/config.json"
inetdata_data_path=$(cat ${config_path} | jq -r .inetdata_data_path)
tmp_dir=$(cat ${config_path} | jq -r .tmp_dir)

ct_cache_directory="${inetdata_data_path}/cache/ct"
ct2hostnames="/usr/local/bin/inetdata-ct2hostnames"
hostnames_dir="${ct_cache_directory}/hostnames"


cd ${ct_cache_directory}

# only process files that changed since last run
# no need to redo all of them if no changes since last time
# e.g. if hostname file already exists and corresponding .json file is older than hostname file,
# then it means the baseline file has not changed since so we don't need to recompute for that file.
for f in *.json *.gz; do
    doit=1
    if [ -f ${hostnames_dir}/"${f}" ]; then
        # hostfile already exists, let's check whether it is older than the base .json file
        basefile_date=$(date +%s -r "${f}")
        hostfile_date=$(date +%s -r ${hostnames_dir}/"${f}")

        if (( basefile_date <= hostfile_date )); then
            doit=0 # basefile didn't change since last run
            echo "Skipping file ${f}"
        fi
    fi

    if (( doit == 1 )); then
        echo "processing ${f}"
        echo "outputting to ${hostnames_dir}/${f}"

        # if gz file, => use zcat
        if echo ${f} | grep '.gz$'; then
            # filename ends with .gz
            echo "using zcat..."
            zcat "${f}" | ${ct2hostnames} > ${hostnames_dir}/"${f}" 2> ${hostnames_dir}/"${f}".log
        else
            echo "using cat..."
            cat "${f}" | ${ct2hostnames} > ${hostnames_dir}/"${f}" 2> ${hostnames_dir}/"${f}".log
        fi
    fi
done

echo "writing base hostname file: ${hostnames_file} ..."
cd ${hostnames_dir}
hostnames_file="uniq_hostnames"
cat *.json *.gz | sort -S 80% --parallel 8 -T ${tmp_dir} | uniq > ${hostnames_file}

echo "writing cleaned file: ${cleaned_hostnames_file} ..."
# clean hostnames file
curdate=$(date +%Y%m%d-%H%M%S)
cleaned_hostnames_file="final_uniq_ct_hostnames-${curdate}"
cat ${hostnames_file} \
 | tr -d '\000' \
 | sed -r 's/\*\.//g' \
 | tr -d '*' \
 | sort -S 80% --parallel 8 -T ${tmp_dir} \
 | uniq > ${cleaned_hostnames_file}
