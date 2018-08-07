#!/usr/bin/env python3

import copy
import datetime
import glob
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

from downloaders_utils import get_config

config = get_config()

GITLAB_USERS_PATH = "{}/collector-cache/gitlab.com/gitlab.com_users.csv".format(config["basedir"])
users_path = "{}/collector-cache/gitlab.com/users".format(config["basedir"])
date_format = "%Y%m%d-%H%M%S"


def get_gitlab_private_token():
    return config["gitlab_private_token"]


def date_from_filename(filename):
    fn = os.path.basename(filename)
    fn = fn.replace("gitlab.com_users_", "")
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
        return GITLAB_USERS_PATH


def main():
    gitlab_private_token = get_gitlab_private_token()
    url = "https://gitlab.com/api/v4/users?page={}&per_page={}"

    headers = {
        "PRIVATE-TOKEN": gitlab_private_token
    }

    per_page = 100
    max_workers = 20
    batch_size = 20

    batch_futures = []

    tpe = ThreadPoolExecutor(max_workers=max_workers)

    total_users = 0
    page = 1
    #  setup incremental restart (get page number by loading file)
    os.makedirs(users_path, exist_ok=True)
    current_date = datetime.datetime.utcnow().strftime(date_format)
    latest_users_flat_file = find_latest_file(users_path)
    print("latest users flat file: {}".format(latest_users_flat_file))
    new_users_flat_file = "{}/gitlab.com_users_{}.csv".format(users_path, current_date)

    latest_known_users = []
    latest_known_user_id = 0

    if os.path.exists(latest_users_flat_file):
        try:
            with open(latest_users_flat_file) as f:
                line_counter = 0
                for line in f:
                    line_counter += 1

                    if line_counter > 2200:
                        break

                    user_id = line.split(";")[0]
                    latest_known_users.append(int(user_id))

            latest_known_user_id = sorted(latest_known_users)[-1]
        except:
            pass

    # find out whether base file is complete

    is_baseline_incomplete = False

    if os.path.exists(GITLAB_USERS_PATH):
        command = [
            "tail",
            "-n", "1",
            GITLAB_USERS_PATH
        ]

        last_line = subprocess.check_output(command).decode("utf-8").strip()
        smallest_known_user_id = int(last_line.split(";")[0])

        if smallest_known_user_id > 100:
            # we haven't collected the baseline file completely yet, let's do that
            # compute what page we should restart from
            response = requests.get(url.format(page, per_page), headers=headers)
            newest_user = response.json()[0]
            newest_user_id = int(newest_user["id"])

            # this is an estimation
            start_page = int((newest_user_id - smallest_known_user_id) / per_page)
            page = start_page

            print("smallest known user id: {}".format(smallest_known_user_id))
            print("resuming from page: {}".format(page))

            new_users_flat_file = GITLAB_USERS_PATH
            is_baseline_incomplete = True
    else:
        is_baseline_incomplete = True
        new_users_flat_file = GITLAB_USERS_PATH

    if len(sys.argv) > 1:
        page = int(sys.argv[1])
        print("starting from page: {}".format(page))

    batch_start_time = datetime.datetime.now()
    while True:
        def collect(page, retries=0):
            try:
                response = requests.get(url.format(page, per_page), headers=headers)

                try:
                    page_users = response.json()
                    return page_users
                except Exception as e:
                    print(response.text)
                    print(response.headers)
                    raise e
            except Exception as e:
                print("exception occured")
                print(e)

                if retries >= 2:
                    return None

                print("Retrying, page =", page, "retries =", retries)
                time.sleep(20)
                return collect(page, retries + 1)

        future = tpe.submit(collect, page)
        batch_futures.append(future)
        page += 1

        # process batch
        if len(batch_futures) >= batch_size:
            batch_users = []
            for future in batch_futures:
                future_users = future.result()
                if future_users is not None:
                    batch_users += future_users
                else:
                    print("WARNING: future.result() = None")
            batch_futures.clear()
            now = datetime.datetime.now()
            batch_duration = now - batch_start_time
            print("batch duration:", str(batch_duration))
            print("batch users:", len(batch_users))
            print("page: {}".format(page))
            batch_start_time = datetime.datetime.now()

            # write batch users to file
            with open(new_users_flat_file, "a+") as fout:
                total_users += len(batch_users)
                batch_users_copy = copy.deepcopy(batch_users)
                for user in batch_users:
                    try:
                        user_id = user["id"]
                        user_name = user["username"]
                        user_state = user["state"]
                        name = user["name"]
                        fout.write("{};{};{};{}\n".format(user_id, user_name, user_state, name))
                    except TypeError as e:
                        print("error occured while processing user:")
                        print(user)
                        print(e)
                        print("continuing to next user")
                        batch_users_copy.remove(user)
                        continue

            print("Total users: ", total_users)

            # if there is any user with user_id < latest_known_user_id
            # then we have already collected those users and should stop
            batch_user_ids = [int(u["id"]) for u in batch_users_copy]
            known_user_ids = [u for u in batch_user_ids if u <= latest_known_user_id]
            has_reached_known_users = len(known_user_ids) > 0

            if has_reached_known_users and not is_baseline_incomplete:
                break

            if len(batch_users) == 0:
                # reached start of user list
                break


if __name__ == '__main__':
    main()
