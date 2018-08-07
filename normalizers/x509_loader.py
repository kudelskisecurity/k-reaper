#!/usr/bin/env python3

from ed25519 import *
from public_key_utils import uuid_enrich, curve_enrich
from x509_utils import parse_cert, x509_infos


def load_x509_key(blob):
    """returns a list of keys"""

    c = parse_cert(blob)
    parsed_cert = x509_infos(c)
    keys = [parsed_cert]

    # compute uuid and add as key dict entry
    for k in keys:
        uuid_enrich(k)
        curve_enrich(k)

    return keys
