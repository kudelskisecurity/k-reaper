#!/usr/bin/env python3

from hashlib import sha512

from cryptography.hazmat.primitives.asymmetric import rsa, dsa, ec


def uuid_enrich(key):
    try:
        key["uuid"] = uuid(key)
    except Exception as e:
        print(e)
        print("Could not generate uuid for key:")
        print(key)
        raise


def curve_enrich(key):
    if key["type"] == "ec":
        key["is_on_curve"] = is_on_curve(key, key["curve"])


def uuid(public_key):
    key_type = public_key["type"]

    concat = key_type
    JOINER = " "
    params = []

    if key_type == "rsa":
        n = public_key["n"]
        e = public_key["e"]
        params = [concat, n, e]
    elif key_type == "dsa":
        y = public_key["y"]
        p = public_key["p"]
        q = public_key["q"]
        g = public_key["g"]
        params = [concat, y, p, q, g]
    elif key_type == "ec":
        curve = public_key["curve"]
        x = public_key["x"]
        y = public_key["y"]
        params = [concat, curve, x, y]
    elif "raw_container" in public_key:
        params = [key_type, public_key["raw_container"]]
    else:
        raise Exception("Unsupported key type for uuid generation {}".format(key_type))

    params = [str(x) for x in params]
    concat = JOINER.join(params)
    concat = concat.encode("utf-8", "ignore")

    # hash concat to obtain something with a high probability of being unique
    h = sha512()
    h.update(concat)
    return h.hexdigest()


def is_on_curve(public_key, curve):
    x = public_key["x"]
    y = public_key["y"]

    if x is None or y is None:
        return "unknown"

    if curve == "Curve25519":
        return verify_ed25519_curve(x, y)
    elif curve == "secp112r1":
        return verify_secp112r1_curve(x, y)
    elif curve == "secp112r2":
        return verify_secp112r2_curve(x, y)
    elif curve == "secp128r1":
        return verify_secp128r1_curve(x, y)
    elif curve == "secp128r2":
        return verify_secp128r2_curve(x, y)
    elif curve == "secp160k1":
        return verify_secp160k1_curve(x, y)
    elif curve == "secp160r1":
        return verify_secp160r1_curve(x, y)
    elif curve == "secp160r2":
        return verify_secp160r2_curve(x, y)
    elif curve == "secp192k1":
        return verify_secp192k1_curve(x, y)
    elif curve == "secp192r1":
        return verify_secp192r1_curve(x, y)
    elif curve == "secp224k1":
        return verify_secp224k1_curve(x, y)
    elif curve == "secp224r1":
        return verify_secp224r1_curve(x, y)
    elif curve == "secp256k1":
        return verify_secp256k1_curve(x, y)
    elif curve == "secp256r1":
        return verify_secp256r1_curve(x, y)
    elif curve == "secp384r1":
        return verify_secp384r1_curve(x, y)
    elif curve == "secp521r1":
        return verify_secp521r1_curve(x, y)
    elif curve == "brainpoolP160r1":
        return verify_brainpoolP160r1(x, y)
    elif curve == "brainpoolP160t1":
        return verify_brainpoolP160t1(x, y)
    elif curve == "brainpoolP192r1":
        return verify_brainpoolP192r1(x, y)
    elif curve == "brainpoolP192t1":
        return verify_brainpoolP192t1(x, y)
    elif curve == "brainpoolP224r1":
        return verify_brainpoolP224r1(x, y)
    elif curve == "brainpoolP224t1":
        return verify_brainpoolP224t1(x, y)
    elif curve == "brainpoolP256r1":
        return verify_brainpoolP256r1(x, y)
    elif curve == "brainpoolP256t1":
        return verify_brainpoolP256t1(x, y)
    elif curve == "brainpoolP320r1":
        return verify_brainpoolP320r1(x, y)
    elif curve == "brainpoolP320t1":
        return verify_brainpoolP320t1(x, y)
    elif curve == "brainpoolP384r1":
        return verify_brainpoolP384r1(x, y)
    elif curve == "brainpoolP384t1":
        return verify_brainpoolP384t1(x, y)
    elif curve == "brainpoolP512r1":
        return verify_brainpoolP512r1(x, y)
    elif curve == "brainpoolP512t1":
        return verify_brainpoolP512t1(x, y)
    else:
        return "unknown"


def verify_ed25519_curve(x, y):
    p = 2 ** 255 - 19
    d = 37095705934669439343138083508754565189542113879843219016388785533085940283555
    a = -1

    left = (a * (x ** 2) + y ** 2) % p
    right = (1 + d * (x ** 2) * (y ** 2)) % p
    return left == right


def verify_weierstrass_curve(x, y, a, b, p):
    left = (y ** 2) % p
    right = (x ** 3 + a * x + b) % p
    return left == right


def verify_brainpool_curve(x, y, a, b, p):
    return verify_weierstrass_curve(x, y, a, b, p)


# brainpool curves

def verify_brainpoolP160r1(x, y):
    p = 0xE95E4A5F737059DC60DFC7AD95B3D8139515620F
    a = 0x340E7BE2A280EB74E2BE61BADA745D97E8F7C300
    b = 0x1E589A8595423412134FAA2DBDEC95C8D8675E58
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP160t1(x, y):
    p = 0xE95E4A5F737059DC60DFC7AD95B3D8139515620F
    a = 0xE95E4A5F737059DC60DFC7AD95B3D8139515620C
    b = 0x7A556B6DAE535B7B51ED2C4D7DAA7A0B5C55F380
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP192r1(x, y):
    p = 0xC302F41D932A36CDA7A3463093D18DB78FCE476DE1A86297
    a = 0x6A91174076B1E0E19C39C031FE8685C1CAE040E5C69A28EF
    b = 0x469A28EF7C28CCA3DC721D044F4496BCCA7EF4146FBF25C9
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP192t1(x, y):
    p = 0xC302F41D932A36CDA7A3463093D18DB78FCE476DE1A86297
    a = 0xC302F41D932A36CDA7A3463093D18DB78FCE476DE1A86294
    b = 0x13D56FFAEC78681E68F9DEB43B35BEC2FB68542E27897B79
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP224r1(x, y):
    p = 0xD7C134AA264366862A18302575D1D787B09F075797DA89F57EC8C0FF
    a = 0x68A5E62CA9CE6C1C299803A6C1530B514E182AD8B0042A59CAD29F43
    b = 0x2580F63CCFE44138870713B1A92369E33E2135D266DBB372386C400B
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP224t1(x, y):
    p = 0xD7C134AA264366862A18302575D1D787B09F075797DA89F57EC8C0FF
    a = 0xD7C134AA264366862A18302575D1D787B09F075797DA89F57EC8C0FC
    b = 0x4B337D934104CD7BEF271BF60CED1ED20DA14C08B3BB64F18A60888D
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP256r1(x, y):
    p = 0xA9FB57DBA1EEA9BC3E660A909D838D726E3BF623D52620282013481D1F6E5377
    a = 0x7D5A0975FC2C3057EEF67530417AFFE7FB8055C126DC5C6CE94A4B44F330B5D9
    b = 0x26DC5C6CE94A4B44F330B5D9BBD77CBF958416295CF7E1CE6BCCDC18FF8C07B6
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP256t1(x, y):
    p = 0xA9FB57DBA1EEA9BC3E660A909D838D726E3BF623D52620282013481D1F6E5377
    a = 0xA9FB57DBA1EEA9BC3E660A909D838D726E3BF623D52620282013481D1F6E5374
    b = 0x662C61C430D84EA4FE66A7733D0B76B7BF93EBC4AF2F49256AE58101FEE92B04
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP320r1(x, y):
    p = 0xD35E472036BC4FB7E13C785ED201E065F98FCFA6F6F40DEF4F92B9EC7893EC28FCD412B1F1B32E27
    a = 0x3EE30B568FBAB0F883CCEBD46D3F3BB8A2A73513F5EB79DA66190EB085FFA9F492F375A97D860EB4
    b = 0x520883949DFDBC42D3AD198640688A6FE13F41349554B49ACC31DCCD884539816F5EB4AC8FB1F1A6
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP320t1(x, y):
    p = 0xD35E472036BC4FB7E13C785ED201E065F98FCFA6F6F40DEF4F92B9EC7893EC28FCD412B1F1B32E27
    a = 0xD35E472036BC4FB7E13C785ED201E065F98FCFA6F6F40DEF4F92B9EC7893EC28FCD412B1F1B32E24
    b = 0xA7F561E038EB1ED560B3D147DB782013064C19F27ED27C6780AAF77FB8A547CEB5B4FEF422340353
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP384r1(x, y):
    p = 0x8CB91E82A3386D280F5D6F7E50E641DF152F7109ED5456B412B1DA197FB71123ACD3A729901D1A71874700133107EC53
    a = 0x7BC382C63D8C150C3C72080ACE05AFA0C2BEA28E4FB22787139165EFBA91F90F8AA5814A503AD4EB04A8C7DD22CE2826
    b = 0x04A8C7DD22CE28268B39B55416F0447C2FB77DE107DCD2A62E880EA53EEB62D57CB4390295DBC9943AB78696FA504C11
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP384t1(x, y):
    p = 0x8CB91E82A3386D280F5D6F7E50E641DF152F7109ED5456B412B1DA197FB71123ACD3A729901D1A71874700133107EC53
    a = 0x8CB91E82A3386D280F5D6F7E50E641DF152F7109ED5456B412B1DA197FB71123ACD3A729901D1A71874700133107EC50
    b = 0x7F519EADA7BDA81BD826DBA647910F8C4B9346ED8CCDC64E4B1ABD11756DCE1D2074AA263B88805CED70355A33B471EE
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP512r1(x, y):
    p = 0xAADD9DB8DBE9C48B3FD4E6AE33C9FC07CB308DB3B3C9D20ED6639CCA703308717D4D9B009BC66842AECDA12AE6A380E62881FF2F2D82C68528AA6056583A48F3
    a = 0x7830A3318B603B89E2327145AC234CC594CBDD8D3DF91610A83441CAEA9863BC2DED5D5AA8253AA10A2EF1C98B9AC8B57F1117A72BF2C7B9E7C1AC4D77FC94CA
    b = 0x3DF91610A83441CAEA9863BC2DED5D5AA8253AA10A2EF1C98B9AC8B57F1117A72BF2C7B9E7C1AC4D77FC94CADC083E67984050B75EBAE5DD2809BD638016F723
    return verify_brainpool_curve(x, y, a, b, p)


def verify_brainpoolP512t1(x, y):
    p = 0xAADD9DB8DBE9C48B3FD4E6AE33C9FC07CB308DB3B3C9D20ED6639CCA703308717D4D9B009BC66842AECDA12AE6A380E62881FF2F2D82C68528AA6056583A48F3
    a = 0xAADD9DB8DBE9C48B3FD4E6AE33C9FC07CB308DB3B3C9D20ED6639CCA703308717D4D9B009BC66842AECDA12AE6A380E62881FF2F2D82C68528AA6056583A48F0
    b = 0x7CBBBCF9441CFAB76E1890E46884EAE321F70C0BCB4981527897504BEC3E36A62BCDFA2304976540F6450085F2DAE145C22553B465763689180EA2571867423E
    return verify_brainpool_curve(x, y, a, b, p)


# secp curves

def verify_sec_curve(x, y, a, b, p):
    return verify_weierstrass_curve(x, y, a, b, p)


def verify_secp112r1_curve(x, y):
    p112r1 = 0xDB7C2ABF62E35E668076BEAD208B
    a112r1 = 0xDB7C2ABF62E35E668076BEAD2088
    b112r1 = 0x659EF8BA043916EEDE8911702B22
    return verify_sec_curve(x, y, a112r1, b112r1, p112r1)


def verify_secp112r2_curve(x, y):
    p112r2 = 0xDB7C2ABF62E35E668076BEAD208B
    a112r2 = 0x6127C24C05F38A0AAAF65C0EF02C
    b112r2 = 0x51DEF1815DB5ED74FCC34C85D709
    return verify_sec_curve(x, y, a112r2, b112r2, p112r2)


def verify_secp128r1_curve(x, y):
    p128r1 = 0xFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFF
    a128r1 = 0xFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFC
    b128r1 = 0xE87579C11079F43DD824993C2CEE5ED3
    return verify_sec_curve(x, y, a128r1, b128r1, p128r1)


def verify_secp128r2_curve(x, y):
    p128r2 = 0xFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFF
    a128r2 = 0xD6031998D1B3BBFEBF59CC9BBFF9AEE1
    b128r2 = 0x5EEEFCA380D02919DC2C6558BB6D8A5D
    return verify_sec_curve(x, y, a128r2, b128r2, p128r2)


def verify_secp160k1_curve(x, y):
    p160k1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73
    a160k1 = 0x0000000000000000000000000000000000000000
    b160k1 = 0x0000000000000000000000000000000000000007
    return verify_sec_curve(x, y, a160k1, b160k1, p160k1)


def verify_secp160r1_curve(x, y):
    p160r1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFF
    a160r1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7FFFFFFC
    b160r1 = 0x1C97BEFC54BD7A8B65ACF89F81D4D4ADC565FA45
    return verify_sec_curve(x, y, a160r1, b160r1, p160r1)


def verify_secp160r2_curve(x, y):
    p160r2 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC73
    a160r2 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFAC70
    b160r2 = 0xB4E134D3FB59EB8BAB57274904664D5AF50388BA
    return verify_sec_curve(x, y, a160r2, b160r2, p160r2)


def verify_secp192k1_curve(x, y):
    p192k1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFEE37
    a192k1 = 0x000000000000000000000000000000000000000000000000
    b192k1 = 0x000000000000000000000000000000000000000000000003
    return verify_sec_curve(x, y, a192k1, b192k1, p192k1)


def verify_secp192r1_curve(x, y):
    p192r1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFF
    a192r1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFC
    b192r1 = 0x64210519E59C80E70FA7E9AB72243049FEB8DEECC146B9B1
    return verify_sec_curve(x, y, a192r1, b192r1, p192r1)


def verify_secp224k1_curve(x, y):
    p224k1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFE56D
    a224k1 = 0x00000000000000000000000000000000000000000000000000000000
    b224k1 = 0x00000000000000000000000000000000000000000000000000000005
    return verify_sec_curve(x, y, a224k1, b224k1, p224k1)


def verify_secp224r1_curve(x, y):
    p224r1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF000000000000000000000001
    a224r1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFE
    b224r1 = 0xB4050A850C04B3ABF54132565044B0B7D7BFD8BA270B39432355FFB4
    return verify_sec_curve(x, y, a224r1, b224r1, p224r1)


def verify_secp256k1_curve(x, y):
    p256k1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    a256k1 = 0x0000000000000000000000000000000000000000000000000000000000000000
    b256k1 = 0x0000000000000000000000000000000000000000000000000000000000000007
    return verify_sec_curve(x, y, a256k1, b256k1, p256k1)


def verify_secp256r1_curve(x, y):
    p256r1 = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
    a256r1 = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC
    b256r1 = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
    return verify_sec_curve(x, y, a256r1, b256r1, p256r1)


def verify_secp384r1_curve(x, y):
    p384r1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFF0000000000000000FFFFFFFF
    a384r1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFFFF0000000000000000FFFFFFFC
    b384r1 = 0xB3312FA7E23EE7E4988E056BE3F82D19181D9C6EFE8141120314088F5013875AC656398D8A2ED19D2A85C8EDD3EC2AEF
    return verify_sec_curve(x, y, a384r1, b384r1, p384r1)


def verify_secp521r1_curve(x, y):
    p521r1 = 0x01FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
    a521r1 = 0x01FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC
    b521r1 = 0x0051953EB9618E1C9A1F929A21A0B68540EEA2DA725B99B315F3B8B489918EF109E156193951EC7E937B1652C0BD3BB1BF073573DF883D2C34F1EF451FD46B503F00
    return verify_sec_curve(x, y, a521r1, b521r1, p521r1)


def rsa_attributes(public_key):
    pn = public_key.public_numbers()

    return {
        "n": pn.n,
        "e": pn.e,
        "key_size": public_key.key_size,
        "type": "rsa"
    }


def dsa_attributes(public_key):
    pn = public_key.public_numbers()
    parameters = pn.parameter_numbers

    return {
        "key_size": public_key.key_size,
        "y": pn.y,
        "p": parameters.p,
        "q": parameters.q,
        "g": parameters.g,
        "type": "dsa"
    }


def ec_attributes(public_key):
    pn = public_key.public_numbers()

    return {
        "key_size": public_key.key_size,
        "curve": public_key.curve.name,
        "x": pn.x,
        "y": pn.y,
        "type": "ec"
    }


def key_type(public_key):
    t = "unknown"
    if isinstance(public_key, rsa.RSAPublicKey):
        t = "rsa"
    elif isinstance(public_key, dsa.DSAPublicKey):
        t = "dsa"
    elif isinstance(public_key, ec.EllipticCurvePublicKey):
        t = "ec"

    return t


def generic_attributes(public_key):
    kt = key_type(public_key)

    if kt == "rsa":
        return rsa_attributes(public_key)
    elif kt == "dsa":
        return dsa_attributes(public_key)
    elif kt == "ec":
        return ec_attributes(public_key)
    else:
        raise Exception("Unsupported generic key type")
