#!/usr/bin/env python3

import datetime
import glob
import json
import os

from pgp_utils import parse_pgp_ascii_blob, DATETIME_FORMAT
from normalizers_utils import get_config

config = get_config()
base_path = "{}/collector-cache/keybase.io/pgp-keys".format(config["basedir"])
PARSED_BASE_PATH = "{}/collector-parsed/keybase.io".format(config["basedir"])
filename_date_format = "%Y%m%d-%H%M%S"


def normalize_path(filepath, parsed_base_path=PARSED_BASE_PATH):
    filename = os.path.basename(filepath)
    output_path = os.path.join(parsed_base_path, filename) + ".out.json"
    tmp_output_dir = parsed_base_path + "-tmp"
    os.makedirs(tmp_output_dir, exist_ok=True)

    tmp_output_path = os.path.join(tmp_output_dir, filename) + ".out.json.tmp"

    # example filename: keybase.io_pgp_keys_20180702-100003.csv
    timestamp = filename.replace("keybase.io_pgp_keys_", "").replace(".csv", "")
    timestamp_datetime = datetime.datetime.strptime(timestamp, filename_date_format)
    timestamp = timestamp_datetime.strftime(DATETIME_FORMAT)

    if os.path.exists(output_path):
        print("Skipping normalization of path: {}".format(filepath))
        return

    with open(tmp_output_path, "w+") as fout:
        with open(filepath) as f:
            for line in f:
                username = None
                try:
                    splits = line.strip().split(";")
                    username = splits[0]
                    pgp_blob = ";".join(splits[1:])
                except:
                    print("failed to split line")

                try:
                    keys = parse_pgp_ascii_blob(pgp_blob)
                    for key in keys:
                        output_key(fout, key, timestamp, username)
                except Exception as e:
                    print("Failed to parse line:")
                    print(line)
                    print(e)

    # mv tmp to destination
    print("moving .tmp file to destination:")
    print("{} -> {}".format(tmp_output_path, output_path))
    os.rename(tmp_output_path, output_path)


def output_key(fout, key, timestamp, username):
    key["source"] = "keybase.io"
    key["username"] = username
    key["timestamp"] = timestamp
    print(json.dumps(key), file=fout)


def main():
    os.makedirs(PARSED_BASE_PATH, exist_ok=True)
    unparsed_files = glob.glob("{}/*".format(base_path))

    for filepath in unparsed_files:
        normalize_path(filepath)


if __name__ == '__main__':
    main()
