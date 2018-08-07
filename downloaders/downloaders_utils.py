#!/usr/bin/env python3

import json

CONFIG_DIR = "/etc/k-reaper"
CONFIG_PATH = "{}/config.json".format(CONFIG_DIR)


def get_config():
    with open(CONFIG_PATH) as f:
        return json.loads(f.read())
