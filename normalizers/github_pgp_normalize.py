#!/usr/bin/env python3

import datetime
import glob
import json
import os

from pgp_utils import parse_pgp_ascii_blob, DATETIME_FORMAT
from normalizers_utils import get_config

config = get_config()

base_path = "{}/collector-cache/github.com/pgp-keys".format(config["basedir"])
PARSED_BASE_PATH = "{}/collector-parsed/github.com-pgp".format(config["basedir"])
filename_date_format = "%Y%m%d-%H%M%S"


def normalize_path(filepath, parsed_base_path=PARSED_BASE_PATH):
    filename = os.path.basename(filepath)
    output_path = os.path.join(parsed_base_path, filename) + ".out.json"
    tmp_output_dir = parsed_base_path + "-tmp"
    os.makedirs(tmp_output_dir, exist_ok=True)

    tmp_output_path = os.path.join(tmp_output_dir, filename) + ".out.json.tmp"

    timestamp = filename.replace("github.com_pgp_keys_", "").replace(".csv", "")
    timestamp_datetime = datetime.datetime.strptime(timestamp, filename_date_format)
    timestamp = timestamp_datetime.strftime(DATETIME_FORMAT)

    if os.path.exists(output_path):
        print("Skipping normalization of path: {}".format(output_path))
        return

    with open(tmp_output_path, "w+") as fout:
        with open(filepath) as f:
            for line in f:
                username = None
                try:
                    splits = line.strip().split(";")
                    user_id = splits[0]
                    username = splits[1]
                    pgp_blob = ";".join(splits[2:])
                except:
                    print("failed to split line")

                try:
                    keys = parse_pgp_ascii_blob(pgp_blob)
                    for key in keys:
                        output_key(fout, key, timestamp, username, user_id)
                except Exception as e:
                    print("Failed to parse line:")
                    print(line)
                    print(e)

    # mv tmp to destination
    print("moving .tmp file to destination:")
    print("{} -> {}".format(tmp_output_path, output_path))
    os.rename(tmp_output_path, output_path)


def output_key(fout, key, timestamp, username, user_id):
    key["source"] = "github.com-pgp"
    key["user_id"] = user_id
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
