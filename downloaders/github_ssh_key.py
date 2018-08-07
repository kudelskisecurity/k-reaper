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

SSH_KEYS_PATH = "{}/collector-cache/github.com/github.com_ssh_keys.csv".format(config["basedir"])
USERS_PATH = "{}/collector-cache/github.com/github.com_users.csv".format(config["basedir"])
users_directory = "{}/collector-cache/github.com/users".format(config["basedir"])
date_format = "%Y%m%d-%H%M%S"
ssh_keys_directory = "{}/collector-cache/github.com/ssh-keys".format(config["basedir"])


def collect(user, retries=0):
    (user_id, username) = user
    try:
        url = "https://github.com/{}.keys".format(username)
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("HTTP error:" + str(response.status_code))

        user_keys = [line.strip() for line in response.text.split("\n") if len(line.strip()) > 0]
        return user_keys
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
    fn = fn.replace("github.com_ssh_keys_", "")
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
        return SSH_KEYS_PATH


def main():
    start_time = datetime.datetime.utcnow()
    total_keys = 0
    print("loading users list...")
    usernames = load_users_list()

    print("loaded usernames into memory")

    # block_size is used to reduce memory usage
    block_size = 4000

    index = 0

    latest_ssh_keys_file_path = find_latest_file(ssh_keys_directory)
    current_date = datetime.datetime.utcnow().strftime(date_format)
    new_ssh_keys_file_path = "{}/github.com_ssh_keys_{}.csv".format(ssh_keys_directory, current_date)

    os.makedirs(ssh_keys_directory, exist_ok=True)

    try:
        command = [
            "tail",
            "-n", "1",
            latest_ssh_keys_file_path
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

    processed_users = index
    users_count = len(usernames)
    while index < users_count:
        block_users = usernames[index:index + block_size]

        max_workers = 40
        executor = ThreadPoolExecutor(max_workers=max_workers)

        with open(new_ssh_keys_file_path, "a+") as fout:

            for user, user_keys in zip(block_users, executor.map(collect, block_users, chunksize=100)):
                (user_id, username) = user
                if user_keys is not None:
                    # write keys to disk
                    total_keys += len(user_keys)
                    for key in user_keys:
                        fout.write("{};{};{}\n".format(user_id, username, key))
                else:
                    print("WARNING: user_keys == None. username = {}".format(username))

                processed_users += 1

                if processed_users % 10000 == 0:
                    print("Total keys: ", total_keys)
                    print("Processed users:", processed_users)
                    print("User Index:", index)

        index += block_size

        executor.shutdown()


if __name__ == '__main__':
    main()
