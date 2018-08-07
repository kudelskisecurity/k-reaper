#!/usr/bin/env python3

import datetime
import glob
import os
import subprocess
import time

import requests

from downloaders_utils import get_config

config = get_config()

users_flat_file = "{}/collector-cache/github.com/github.com_users.csv".format(config["basedir"])
users_path = "{}/collector-cache/github.com/users".format(config["basedir"])
date_format = "%Y%m%d-%H%M%S"


def load_oauth_token():
    config["github_oauth_token"]


def date_from_filename(filename):
    fn = os.path.basename(filename)
    fn = fn.replace("github.com_users_", "")
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
        return users_flat_file


def main():
    GITHUB_ROOT = "https://api.github.com/"
    api_endpoint = GITHUB_ROOT + "users"

    os.makedirs(users_path, exist_ok=True)
    current_date = datetime.datetime.utcnow().strftime(date_format)

    latest_users_flat_file = find_latest_file(users_path)
    new_users_flat_file = "{}/github.com_users_{}.csv".format(users_path, current_date)
    max_requests = None

    request_count = 1
    oauth_token = load_oauth_token()
    headers = {
        "Authorization": "token " + oauth_token
    }

    limits = requests.get("https://api.github.com/rate_limit", headers=headers)
    print(limits.json())

    since = None
    try:
        command = [
            "tail",
            "-n", "1",
            latest_users_flat_file
        ]

        output = subprocess.check_output(command)
        last_line = output.decode("utf-8").strip()
        latest_user_id = last_line.split(";")[0]
        print("latest user id: {}".format(latest_user_id))
        since = int(latest_user_id)
    except:
        pass

    while True:
        url = api_endpoint
        if since is not None:
            url = api_endpoint + "?since=" + str(since)

        try:
            req_start_time = datetime.datetime.now()
            response = requests.get(url, headers=headers)
            jso = response.json()
            req_end_time = datetime.datetime.now()
            request_duration = req_end_time - req_start_time
            print("Request time: ", request_duration)
        except Exception as e:
            print("Exception occured while decoding JSON")
            print(e)
            time.sleep(60)
            continue

        if response.status_code == 403:
            print(jso["message"])
            print(response.headers)
            rate_limit_reset_timestamp = response.headers["X-RateLimit-Reset"]
            reset_date = datetime.datetime.fromtimestamp(int(rate_limit_reset_timestamp))
            current_date = datetime.datetime.now()

            print("Current date:", current_date)
            print("Reset date:", reset_date)
            time_until_reset = reset_date - current_date
            print("Time until reset:", time_until_reset)
            seconds_until_reset = time_until_reset.total_seconds()
            print("Seconds until reset:", seconds_until_reset)

            sleep_time = 60
            print("retrying in %s seconds..." % (sleep_time,))
            time.sleep(sleep_time)

            continue

        if len(jso) == 0:
            print("reached end of users list")
            break

        since = jso[-1]["id"]
        print("Since=" + str(since))

        # save current users to file and progress
        with open(new_users_flat_file, "a+") as fout:
            for user in jso:
                login = user["login"]
                user_id = user["id"]
                user_type = user["type"]
                site_admin = user["site_admin"]
                separator = ";"
                fields = [user_id, login, user_type, site_admin]
                fields = [str(x) for x in fields]
                fout.write(separator.join(fields) + "\n")

                request_count += 1

        if max_requests is not None and request_count >= max_requests:
            break


if __name__ == '__main__':
    main()
