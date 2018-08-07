#!/usr/bin/env python3

import base64
import datetime
import os
import struct
import subprocess
from unittest import mock

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_ssh_public_key

from ed25519 import *
from public_key_utils import generic_attributes
from public_key_utils import uuid_enrich, curve_enrich

here = os.path.dirname(__file__)
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def load_openssh_key(blob):
    """returns a list of keys"""
    splits = blob.split(" ")
    key_type = splits[0]
    key_blob = splits[1]

    keys = []
    if key_type == "ssh-ed25519":
        keys = [parse_ed25519(key_blob)]
    elif key_type.endswith("-cert-v01@openssh.com"):
        keys = parse_certkey(blob)
    else:
        keys = [parse_generic(blob)]

    # compute uuid and add as key dict entry
    for k in keys:
        uuid_enrich(k)
        curve_enrich(k)

    return keys


def parse_certkey(key_blob):
    try:
        command = [
            "go", "run",
            os.path.join(here, "parseCerts.go"),
            key_blob
        ]

        output = subprocess.check_output(command)
        output_lines = output.decode("utf-8", "ignore").split("\n")
        public_key = output_lines[0]
        signing_key = output_lines[1]
        principals = output_lines[2].split(";")

        raw_after = int(output_lines[3])
        raw_before = int(output_lines[4])

        # convert timestamps with larger precision
        max_timestamp_int_value = 2 ** 32 - 1

        while raw_after > max_timestamp_int_value:
            raw_after //= 10

        while raw_before > max_timestamp_int_value:
            raw_before //= 10

        valid_after = datetime.datetime.fromtimestamp(raw_after)
        valid_before = datetime.datetime.fromtimestamp(raw_before)

        try:
            valid_after = valid_after.strftime(DATETIME_FORMAT)
        except:
            print(valid_before)
            raise

        try:
            valid_before = valid_before.strftime(DATETIME_FORMAT)
        except:
            print(valid_before)
            raise

        parsed_key = load_openssh_key(public_key)[0]
        parsed_key["certkey_valid_principals"] = principals
        parsed_key["certkey_valid_after"] = valid_after
        parsed_key["certkey_valid_before"] = valid_before
        parsed_key["is_certkey"] = True

        parsed_signing_key = load_openssh_key(signing_key)[0]
        parsed_signing_key["signed_key_uuid"] = parsed_key["uuid"]
        return [parsed_key, parsed_signing_key]
    except:
        raise


def parse_generic(key_blob):
    with mock.patch("cryptography.hazmat.primitives.asymmetric.dsa._check_dsa_parameters"):
        public_key = None
        try:
            public_key = load_ssh_public_key(key_blob.encode("utf-8", "ignore"), default_backend())

            return generic_attributes(public_key)
        except AttributeError:
            print(public_key.__dict__)
            raise


def parse_ed25519(key_blob):
    b = base64.b64decode(key_blob)
    next_field_length_bytes = 4
    length = b[0:next_field_length_bytes]
    algo_name_length = struct.unpack(">I", length)[0]

    algo_name = b[next_field_length_bytes:next_field_length_bytes + algo_name_length].decode("utf-8", "ignore")

    if algo_name != "ssh-ed25519":
        raise Exception("Not an ssh-ed25519 public key: {}".format(algo_name))

    current_position = next_field_length_bytes + algo_name_length
    key_length = b[current_position:current_position + 4]
    key_length = struct.unpack(">I", key_length)[0]

    if key_length != 32:
        raise Exception("expecting ed25519 keys to be 32 bytes long")

    current_position += 4

    key_bytes = b[current_position:current_position + key_length]

    x, y, _, _ = decodepoint(key_bytes)
    key_attributes = {
        "key_size": 256,
        "curve": "Curve25519",
        "x": x,
        "y": y,
        "type": "ec",
    }
    return key_attributes
