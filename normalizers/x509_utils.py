#!/usr/bin/env python3

import datetime
import os
import subprocess
import sys
import tempfile
import textwrap
from unittest import mock

import cryptography
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.backends.openssl.decode_asn1 import _asn1_string_to_ascii
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from public_key_utils import generic_attributes, curve_enrich

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def parse_cert(raw_enc):
    begin_cert = "-----BEGIN CERTIFICATE-----"
    end_cert = "-----END CERTIFICATE-----"
    raw_enc = raw_enc.replace(begin_cert, "")
    raw_enc = raw_enc.replace(end_cert, "")

    raw_enc = raw_enc.replace(r'\n', "\n").replace("\n", "").strip()
    raw_enc = "\n".join(textwrap.wrap(raw_enc, 64))
    raw_enc = "{}\n{}\n{}\n\n".format(begin_cert, raw_enc, end_cert)

    cert_encoded = raw_enc.encode("utf-8", "ignore")

    try:
        cert = x509.load_pem_x509_certificate(cert_encoded, default_backend())
        return cert
    except Exception:
        print("Error decoding cert:", file=sys.stderr)
        print(raw_enc, file=sys.stderr)
        raise SyntaxError("unable to load certificate")


def get_generalized_time(backend, generalized_time):
    """Note: Overwrites cryptography module parsing of asn1 dates for some badly encoded certificates
    """
    time = _asn1_string_to_ascii(
        backend, backend._ffi.cast("ASN1_STRING *", generalized_time)
    )
    try:
        return datetime.datetime.strptime(time, "%Y%m%d%H%M%SZ")
    except ValueError:
        try:
            return datetime.datetime.strptime(time, "%Y%m%d%H%M%S%z")
        except ValueError:
            return datetime.datetime.fromtimestamp(0)


def x509_infos(cert):
    with mock.patch("cryptography.hazmat.backends.openssl.decode_asn1._parse_asn1_generalized_time",
                    side_effect=get_generalized_time):
        cert_dict = {
            "not_valid_before": None,
            "not_valid_after": None,
            "signature_hash_algorithm": None,
            "serial_number": cert.serial_number,
            "issuer_common_name": None,
            "issuer_organization_name": None,
            "issuer_country": None,
            "subject_common_name": None
        }

        try:
            cert_dict["signature_hash_algorithm"] = str(cert.signature_hash_algorithm.name)
        except cryptography.exceptions.UnsupportedAlgorithm as e:
            oid = cert.signature_algorithm_oid._dotted_string
            print("Unknown signature hash algorithm. OID: {}".format(oid))
            cert_dict["signature_algorithm_oid"] = str(oid)

        try:
            cert_dict["not_valid_before"] = str(cert.not_valid_before.strftime(DATETIME_FORMAT))
        except cryptography.exceptions.InternalError as e:
            print("[Warning] Failed to parse notBefore")
            cert_dict["invalid_format"] = True
        try:
            cert_dict["not_valid_after"] = str(cert.not_valid_after.strftime(DATETIME_FORMAT))
        except cryptography.exceptions.InternalError:
            print("[Warning] Failed to parse notAfter")
            cert_dict["invalid_format"] = True

        # Note: some attributes may not be present so we cannot expect values to be there
        try:
            cert_dict["issuer_common_name"] = str(cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value)
        except:
            pass

        try:
            cert_dict["issuer_organization_name"] = str(
                cert.issuer.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value)
        except:
            pass

        try:
            cert_dict["issuer_country"] = str(cert.issuer.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value)
        except:
            pass

        try:
            cert_dict["subject_common_name"] = str(cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value)
        except:
            pass

        try:
            pk = cert.public_key()
            pk_attributes = generic_attributes(pk)
            cert_dict.update(pk_attributes)
        except ValueError as e:
            print("Unsupported public key (?)")
            print(e)
            # Workaround: call openssl directly to get more info
            cert_dict["unsupported_algorithm"] = True
            # dump public bytes to tempfile
            cert_dict["type"] = "unknown"
            fd, path = tempfile.mkstemp("x509_tmp")
            try:
                with open(path, "w+") as fout:
                    pem_cert = cert.public_bytes(cryptography.hazmat.primitives.serialization.Encoding.PEM).decode(
                        "utf-8", "ignore")
                    cert_dict["raw_container"] = pem_cert
                    print(pem_cert, file=fout)
                os.close(fd)

                # call openssl on temp file and extract public key algorithm name
                openssl_command = [
                    "openssl", "x509",
                    "-in", path,
                    "-text"
                ]

                output = subprocess.check_output(openssl_command)
                decoded_output = output.decode("utf-8", "ignore")
                output_lines = decoded_output.split("\n")
                pka = "Public Key Algorithm: "
                public_key_algo_line = [line for line in output_lines if pka in line][0]

                public_key_algo_name = public_key_algo_line.strip().replace(pka, "")

                cert_dict["type"] = public_key_algo_name
            except:
                raise
            finally:
                # delete tempfile
                os.remove(path)

        return cert_dict
