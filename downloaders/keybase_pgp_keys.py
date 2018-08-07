#!/usr/bin/env python3

import datetime
import glob
import os
import sys

import requests

from downloaders_utils import get_config

config = get_config()

base_output_file = "{}/collector-cache/keybase.io/keybase_pgp_keys.csv".format(config["basedir"])
keybase_pgp_keys_directory = "{}/collector-cache/keybase.io/pgp-keys".format(config["basedir"])
keybase_users_path = "{}/collector-cache/keybase.io/users".format(config["basedir"])
date_format = "%Y%m%d-%H%M%S"

total_keys = 0
total_users = 0


def date_from_filename(filename):
    fn = os.path.basename(filename)
    fn = fn.replace("gitlab.com_ssh_keys_", "")
    fn = fn.replace(".csv", "")
    d = datetime.datetime.strptime(fn, date_format)
    return d


def find_latest_file(directory):
    gl = "{}/*".format(directory)
    files = glob.glob(gl)
    sorted_files = sorted(files, key=date_from_filename, reverse=True)

    if len(sorted_files) > 0:
        return sorted_files[0]
    else:
        return base_output_file


def load_users_list():
    usernames = []

    for user_file in glob.glob("{}/*".format(keybase_users_path)):
        print("loading from: {}".format(user_file))
        with open(user_file) as f:
            for line in f:
                splits = line.strip().split(";")
                try:
                    user_id = splits[0]
                    username = ";".join(splits[1:])
                    usernames.append((user_id, username))
                except IndexError as e:
                    print("detected empty line in file {}:".format(user_file))
                    print(line)
                    continue

    return list(set(usernames))  # remove duplicates


def fetch_ppg_keys(usernames, output_file):
    api_root_url = "https://keybase.io/_/api/1.0/user/lookup.json"

    url = "{}?usernames={}".format(api_root_url, ",".join(usernames))
    print(url)

    # check that response.json()["status"]["code"] == 0
    response = requests.get(url)
    jso = response.json()

    if jso["status"]["code"] != 0:
        print("ERROR: response status.code != 0")

    users = jso["them"]

    global total_keys
    global total_users

    with open(output_file, "a+") as fout:
        for user in users:

            # find PGP keys for user
            # save PGP keys to output file
            if user is None:
                print("WARNING: None user detected")
                continue

            pgp_public_keys = user["public_keys"]["pgp_public_keys"]
            username = user["basics"]["username"]
            total_keys += len(pgp_public_keys)

            for key in pgp_public_keys:
                key_flat = key.replace("\n", "\\n")
                print("{};{}".format(username, key_flat), file=fout)

    # update count of currently collected keys
    total_users += len(users)

    # print status info
    print("Total users fetched:", total_users)
    print("Total keys collected:", total_keys)


def main():
    os.makedirs(keybase_pgp_keys_directory, exist_ok=True)
    current_date = datetime.datetime.utcnow().strftime(date_format)
    new_pgp_keys_file_path = "{}/keybase.io_pgp_keys_{}.csv".format(keybase_pgp_keys_directory, current_date)

    batch_size = 50

    users = load_users_list()
    print("total users to collect pgp keys for: {}".format(len(users)))

    batch_users = []
    start_offset = None

    if len(sys.argv) > 1:
        start_offset = int(sys.argv[1])

    i = 0
    for uid, username in users:
        i += 1
        if start_offset is not None and i <= start_offset:
            continue

        if len(batch_users) < batch_size:
            batch_users.append(username)

        if len(batch_users) >= batch_size:
            fetch_ppg_keys(batch_users, new_pgp_keys_file_path)
            batch_users.clear()


if __name__ == '__main__':
    main()
