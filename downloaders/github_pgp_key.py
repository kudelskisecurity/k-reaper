#!/usr/bin/env python3

import datetime
import glob
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from downloaders_utils import get_config

config = get_config()

PGP_KEYS_PATH = "{}/collector-cache/github.com/github.com_pgp_keys.csv".format(config["basedir"])
USERS_PATH = "{}/collector-cache/github.com/github.com_users.csv".format(config["basedir"])
users_directory = "{}/collector-cache/github.com/users".format(config["basedir"])
date_format = "%Y%m%d-%H%M%S"
pgp_keys_directory = "{}/collector-cache/github.com/pgp-keys".format(config["basedir"])

"""
Here is an example user without any pgp keys:


-----BEGIN PGP PUBLIC KEY BLOCK-----
Note: This user hasn't uploaded any GPG keys.


=twTO
-----END PGP PUBLIC KEY BLOCK-----
"""

NO_PGP_KEYS = "This user hasn't uploaded any GPG keys"


def collect(user, retries=0):
    (user_id, username) = user
    try:
        url = "https://github.com/{}.gpg".format(username)
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("HTTP error:" + str(response.status_code))

        pgp_block = response.text.replace("\n", "\\n")

        return pgp_block
    except Exception as e:
        print("exception occured")
        print(e)
        if retries >= 2:
            return None
        time.sleep(2)
        return collect(user, retries=retries + 1)


def load_users_list():
    usernames = []

    with open(USERS_PATH) as f:
        print("loading file: {}".format(USERS_PATH))
        for line in f:
            user_id, username, user_type, state = line.strip().split(";")
            usernames.append((user_id, username))

    for user_file in glob.glob("{}/*".format(users_directory)):
        print("loading file: {}".format(user_file))
        with open(user_file) as f:
            for line in f:
                user_id, username, user_type, state = line.strip().split(";")
                usernames.append((user_id, username))

    return usernames


def date_from_filename(filename):
    fn = os.path.basename(filename)
    fn = fn.replace("github.com_pgp_keys_", "")
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
        return PGP_KEYS_PATH


def main():
    start_time = datetime.datetime.utcnow()
    total_users_with_keys = 0
    usernames = load_users_list()

    print("loaded usernames into memory")

    # block_size is used to reduce memory usage
    block_size = 4000
    index = 0

    latest_pgp_keys_file_path = find_latest_file(pgp_keys_directory)
    current_date = datetime.datetime.utcnow().strftime(date_format)
    new_pgp_keys_file_path = "{}/github.com_pgp_keys_{}.csv".format(pgp_keys_directory, current_date)

    os.makedirs(pgp_keys_directory, exist_ok=True)

    try:
        command = [
            "tail",
            "-n", "1",
            latest_pgp_keys_file_path
        ]
        output = subprocess.check_output(command)
        last_line = output.decode("utf-8").strip()
        latest_user_id = last_line.split(";")[0]
        print("latest user id: {}".format(latest_user_id))
        since = int(latest_user_id)
        users_before = len(usernames)
        usernames = [u for u in usernames if int(u[0]) > since]
        users_after = len(usernames)

        print("users total: {}, users after filtering (resume): {}".format(users_before, users_after))
    except:
        pass

    users_count = len(usernames)
    processed_users = index
    while index < users_count:
        block_users = usernames[index:index + block_size]

        max_workers = 40
        executor = ThreadPoolExecutor(max_workers=max_workers)

        with open(new_pgp_keys_file_path, "a+") as fout:

            for user, pgp_block in zip(block_users, executor.map(collect, block_users, chunksize=100)):
                (user_id, username) = user

                if pgp_block is not None and not NO_PGP_KEYS in pgp_block:
                    # write pgp keys to disk
                    total_users_with_keys += 1
                    fout.write("{};{};{}\n".format(user_id, username, pgp_block))

                processed_users += 1

                if processed_users % 10000 == 0:
                    print("Total users with keys: ", total_users_with_keys)
                    print("Processed users:", processed_users)
                    print("User Index:", index)

        index += block_size

        executor.shutdown()


if __name__ == '__main__':
    main()
