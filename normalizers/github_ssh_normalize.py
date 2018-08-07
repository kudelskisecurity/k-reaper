#!/usr/bin/env python3

import datetime
import glob
import json
import os
import sys

import cryptography

from openssh_loader import load_openssh_key
from normalizers_utils import get_config

config = get_config()

base_path = "{}/collector-cache/github.com/ssh-keys"
github_ssh_baseline_path = "{}/collector-cache/github.com/github.com_ssh_keys.csv"
PARSED_BASE_PATH = "{}/collector-parsed/github.com/ssh-keys"
date_format = "%Y%m%d-%H%M%S"
tz_date_format = "%Y-%m-%dT%H:%M:%S%z"


def main(parsed_base_path=PARSED_BASE_PATH):
    unparsed_files = []
    unparsed_files.append(github_ssh_baseline_path)
    globs = glob.glob("{}/*.csv".format(base_path))
    unparsed_files += list(globs)

    for path in unparsed_files:
        output_path = os.path.basename(path)
        output_path = "{}/{}.out.json".format(PARSED_BASE_PATH, output_path)

        if not os.path.exists(output_path):
            print("parsing file: {}".format(path))
            normalize_unparsed_file(path, parsed_base_path=parsed_base_path)
        else:
            print("File already normalized, skipping: {}".format(output_path))


def normalize_unparsed_file(input_path, parsed_base_path=PARSED_BASE_PATH):
    # normalize output file
    input_filename = os.path.basename(input_path)
    os.makedirs(parsed_base_path, exist_ok=True)
    output_path = "{}/{}.out.json".format(parsed_base_path, input_filename)

    key_error_keys = 0
    value_error_keys = 0
    unsupported_algorithm_keys = 0
    index_error_keys = 0
    unsplittable_line_keys = 0
    timestamp = None

    if "/ssh-keys/" in input_path:
        date_part = input_filename.replace("github.com_ssh_keys_", "")
        date_part = date_part.replace(".csv", "")
        timestamp = datetime.datetime.strptime(date_part, date_format)
        # convert datetime to common format across all key types
        timestamp = timestamp.strftime(tz_date_format)

    tmp_output_dir = parsed_base_path + "-tmp"
    os.makedirs(tmp_output_dir, exist_ok=True)
    tmp_output_path = "{}/{}.out.json".format(tmp_output_dir, input_filename) + ".tmp"
    with open(input_path) as f:
        with open(tmp_output_path, "w+") as fout:
            line_count = 0
            for line in f:
                line_count += 1

                try:
                    user_id, username, key_raw = line.strip().split(";")
                except:
                    print("Failed to split line:")
                    print(line)
                    unsplittable_line_keys += 1
                    continue

                algorithm = key_raw.split(" ")[0]

                try:
                    keys = load_openssh_key(key_raw)

                    for key in keys:
                        output_key(fout, key, timestamp, user_id, username)
                except IndexError as e:
                    # happens when line contains raw key without a space (usually html tags instead of a key)
                    index_error_keys += 1
                except KeyError:
                    key_error_keys += 1
                except ValueError as e:
                    # happens when DSA keys are not of size 1024, 2048 or 3072
                    # mocked with mock module
                    value_error_keys += 1
                except cryptography.exceptions.UnsupportedAlgorithm:
                    print("algo: {}".format(algorithm))

                    unsupported_algorithm_keys += 1
                except:
                    raise

        print("lines processed: {}".format(line_count))

    print("ValueError keys: {}".format(value_error_keys))
    print("UnsupportedAlgorithm keys: {}".format(unsupported_algorithm_keys))
    print("KeyError keys: {}".format(key_error_keys))
    print("IndexError keys: {}".format(index_error_keys))
    print("Unsplittable line keys: {}".format(unsplittable_line_keys))

    print("Moving .tmp file to final destination:")
    print("{} -> {}".format(tmp_output_path, output_path))
    os.rename(tmp_output_path, output_path)


def output_key(fout, openssh_key, timestamp, user_id, username):
    output_line = {
        "source": "github.com",
        "container_type": "openssh",
        "timestamp": timestamp,
        "username": username,
        "user_id": user_id
    }
    # prepare output format
    output_line.update(openssh_key)
    # print to file in normalized format
    print("{}".format(json.dumps(output_line)), file=fout)


if __name__ == '__main__':
    main()
