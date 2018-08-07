#!/usr/bin/env python3

import datetime
import glob
import json
import os
import subprocess

from pgp_utils import parse_pgp_binary_blob, DATETIME_FORMAT
from normalizers_utils import get_config

config = get_config()

base_path = "{}/collector-cache/pgp".format(config["basedir"])
parsed_base_path = "{}/collector-parsed/pgp".format(config["basedir"])
filename_date_format = "%Y%m%d-%H%M%S"


def main():
    directories = glob.glob("{}/*".format(base_path))

    for directory in directories:
        print(directory)
        bz2_files = glob.glob("{}/*.bz2".format(directory))
        for file in bz2_files:
            print(file)
            extracted_path = file.replace(".bz2", "")

            if os.path.exists(extracted_path):
                print("skipping extraction of: {}".format(file))
            else:
                print("extracting file: {}".format(file))
                extract_command = [
                    "bunzip2",
                    file
                ]
                subprocess.check_call(extract_command)

        extracted_files = glob.glob("{}/*.pgp".format(directory))
        parse_files(extracted_files)


def parse_files(extracted_files):
    total_files = len(extracted_files)
    if total_files <= 0:
        print("No files to process in this directory. Skipping.")
        return

    dirname = os.path.basename(os.path.dirname(extracted_files[0])) + ".out.json"
    output_path = os.path.join(parsed_base_path, dirname)

    if os.path.exists(output_path):
        print("skipping directory: {}".format(dirname))
        return

    os.makedirs(parsed_base_path, exist_ok=True)

    # get timestamp from filename
    # example path: {basedir}/collector-cache/pgp/pgp-20180311-000001/keydump-sks-0037.pgp
    timestamp = os.path.basename(os.path.dirname(extracted_files[0])).replace("pgp-", "")
    timestamp_date = datetime.datetime.strptime(timestamp, filename_date_format)
    timestamp = timestamp_date.strftime(DATETIME_FORMAT)

    print("parsing directory: {}".format(dirname))
    tmp_output_dir = parsed_base_path + "-tmp"
    os.makedirs(tmp_output_dir, exist_ok=True)
    tmp_output_path = os.path.join(tmp_output_dir, dirname)
    with open(tmp_output_path, "w+") as fout:
        parsed_files = 0
        for filepath in extracted_files:
            print("parsing file: {}".format(filepath))
            with open(filepath, "rb") as f:
                keys = parse_pgp_binary_blob(f.read())
                for key in keys:
                    output_key(fout, key, timestamp)
            parsed_files += 1
            print("Parsed {}/{} files".format(parsed_files, total_files))

    print("moving tmp file to final destination:")
    print("{} -> {}".format(tmp_output_path, output_path))
    os.rename(tmp_output_path, output_path)


def output_key(fout, key, timestamp):
    key["source"] = "sks-pgp"
    key["timestamp"] = timestamp
    print(json.dumps(key), file=fout)


if __name__ == '__main__':
    main()
