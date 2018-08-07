#!/usr/bin/env python2

import textwrap

from pgpdump_patched.data import BinaryData, AsciiData
from pgpdump_patched.packet import PublicKeyPacket, PublicSubkeyPacket
from pgpdump_patched.utils import PgpdumpException
from public_key_utils import uuid_enrich, curve_enrich

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_pgp_ascii_blob(pgp_ascii):
    pgp_ascii = pgp_ascii.replace("\\n", "\n")
    orig = pgp_ascii
    pgp_ascii = pgp_ascii.split("-----")[2]

    try:
        lines = pgp_ascii.split("\n")
        good_lines = [line for line in lines if not ":" in line and len(line) > 0]
        pgp_ascii = "\n".join(good_lines)
        pgp_ascii = pgp_ascii.replace("\n", "")
        pgp_ascii = "\n".join(textwrap.wrap(pgp_ascii, 64))

    except:
        print(pgp_ascii)

    try:
        data = AsciiData(pgp_ascii)
    except:
        print(orig)
        print("-------------------")
        print("pgp ascii")
        print(pgp_ascii)
        print("ORIG---")
        print(orig)
        raise

    return parse_pgp_data(data)


def parse_pgp_binary_blob(pgp_blob):
    data = BinaryData(pgp_blob)
    return parse_pgp_data(data)


def parse_pgp_data(data):
    """Note this is a generator"""
    blobs = 0
    error_blobs = 0
    dump_exceptions = 0
    for p in data.packets():
        blobs += 1
        try:
            is_pk = isinstance(p, PublicKeyPacket)
            is_psk = isinstance(p, PublicSubkeyPacket)

            if is_pk or is_psk:
                algo = p.pub_algorithm_type

                key = {}

                key["pgp_pub_algorithm_type"] = algo

                if algo == "rsa":
                    key["type"] = "rsa"
                    key["n"] = p.modulus
                    key["e"] = p.exponent
                    key["key_size"] = p.modulus_bitlen
                elif algo == "dsa":
                    key["type"] = "dsa"
                    key["p"] = p.prime
                    key["q"] = p.group_order
                    key["g"] = p.group_gen
                    key["y"] = p.key_value
                    key["key_size"] = p.key_size
                elif algo == "eddsa" or algo == "ecdh" or algo == "ecdsa":
                    # curve, x, y, key_size
                    key["type"] = "ec"
                    key["curve"] = p.curve
                    key["key_size"] = p.key_size
                    key["x"] = p.x
                    key["y"] = p.y
                elif algo is not None:
                    key["type"] = algo
                    key["raw_container"] = "\\x".join([hex(b).replace("0x", "") for b in p.data])
                    try:
                        key["key_size"] = p.key_size
                    except:
                        pass
                else:
                    raw_algo = "pgp_{}".format(p.raw_pub_algorithm)
                    key["type"] = raw_algo
                    key["raw_container"] = "\\x".join([hex(b).replace("0x", "") for b in p.data])

                key["container_type"] = "pgp"
                key["is_subkey"] = is_psk
                uuid_enrich(key)
                curve_enrich(key)

                yield key
        except PgpdumpException as e:
            dump_exceptions += 1
        except IndexError as e:
            print(e)
            print("Error decoding binary pgp key:")
            error_blobs += 1
