#!/usr/bin/env python3

import datetime
import os

import requests
from bs4 import BeautifulSoup

from downloads_utils import get_config

load_more_followers_base_url = "https://keybase.io/_/api/1.0/user/load_more_followers.json"
date_format = "%Y%m%d-%H%M%S"
config = get_config()

traversed_uids = {}

output_file = "{}/collector-cache/keybase.io/keybase_users.csv".format(config["basedir"])
keybase_users_path = "{}/collector-cache/keybase.io/users".format(config["basedir"])


def main():
    os.makedirs(keybase_users_path, exist_ok=True)

    # populate backlog to start
    num_wanted = 100

    backlog_uids = set()

    init_backlog_uids = [
        "c6d0b3ba5ff0c7145cb370afc18a3400",  # hdm
        "8c7c57995cd14780e351fc90ca7dc819",
        "08abe80bd2da8984534b2d8f7b12c700",
        "673a740cd20fb4bd348738b16d228219",
        "e0b4166c9c839275cf5633ff65c3e819",
        "23260c2ce19420f97b58d7d95b68ca00",
        "237e85db5d939fbd4b84999331638200",
        "d95f137b3b4a3600bc9e39350adba819",
        "1563ec26dc20fd162a4f783551141200",
        "41b1f75fb55046d370608425a3208100",
        "4c230ae8d2f922dc2ccc1d2f94890700",
        "dbb165b7879fe7b1174df73bed0b9500",
        "95e88f2087e480cae28f08d81554bc00",
        "9403ede05906b942fd7361f40a679500",
        "eb08cb06e608ea41bd893946445d7919",
        "ebbe1d99410ab70123262cf8dfc87900",
        "ef2e49961eddaa77094b45ed635cfc00",
        "69da56f622a2ac750b8e590c3658a700"
    ]

    for uid in init_backlog_uids:
        backlog_uids.add(uid)

    max_outer_requests = None
    max_users = None

    current_date = datetime.datetime.utcnow().strftime(date_format)
    output_filepath = "{}/keybase.io_users_{}.csv".format(keybase_users_path, current_date)

    i = 0
    while len(backlog_uids) > 0:
        uid = backlog_uids.pop()
        print("fetching uid:", uid)
        backlog_uids = collect_followers(uid, backlog_uids, num_wanted, 0, output_filepath)
        print("traversed size:", len(traversed_uids))
        backlog_uids = collect_followers(uid, backlog_uids, num_wanted, 1, output_filepath)
        print("after followings:", len(traversed_uids))
        print("backlog size:", len(backlog_uids))
        i += 1

        if max_outer_requests is not None and i >= max_outer_requests:
            break

        if max_users is not None and len(traversed_uids) >= max_users:
            break


def collect_followers(uid, backlog_uids, num_wanted, reverse, output_filepath):
    last_uid = uid

    new_entries = []

    continue_chain = 0
    while True:
        url = "{}?reverse={}&uid={}&num_wanted={}".format(load_more_followers_base_url, reverse, uid, num_wanted)
        if last_uid is not None:
            url += "&last_uid={}".format(last_uid)
        # collect followers for uid
        snippet = ""
        try:
            response = requests.get(url)
            snippet = response.json()["snippet"]
            continue_chain = 0
        except Exception as e:
            print("error on HTTP GET")
            print(e)
            continue_chain += 1

            if continue_chain >= 5:
                break
            continue

        parser = "lxml"
        soup = BeautifulSoup(snippet, parser)

        request_entries = []
        for tr in soup.find_all("tr"):
            user_uid = tr.get("data-uid")
            request_entries.append(user_uid)
            if user_uid is not None:
                for a in tr.find_all("a"):
                    username = a.text

                # found new user uid and username to add to backlog
                if user_uid not in traversed_uids:
                    backlog_uids.add(user_uid)
                    traversed_uids[user_uid] = username
                    new_entries.append((user_uid, username))

                last_uid = user_uid
        if len(request_entries) <= 0:
            break
    # end while True

    with open(output_filepath, "a+") as fout:
        for uid, username in new_entries:
            print("{};{}".format(uid, username), file=fout)

    return backlog_uids


if __name__ == '__main__':
    main()
