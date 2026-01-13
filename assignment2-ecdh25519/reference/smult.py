"""Implement scalar multiplication on the twisted Edwards curve:
-x^2 + y^2 = 1 + dx^2y^2."""

from .ge25519 import Ge25519


def crypto_scalarmult(sk: bytes, pk: bytes) -> bytes:
    """Compute k*p where k is a secret scalar in GL(P) and p is a point on
    Ecdh25519 curve. More specifically:
        - Alice has a keypair (kA, pA)
        - Bob has a keypair (kB, pB)
        - Alice sends pA to Bob
        - Bob sends pB to Alice
        - Alice computes shared key as K = kA*pB
        - Bob computes shared key as K = kB*pA
    In both sides, we need to compute sk*pk where sk is a secret scalar.
    """
    t = bytearray(sk)

    # "Clamp" the scalar as follows:
    #     - The secret key is a b-bit string s where b = 255
    #     - Then the user compute: H(s) = (h_0, ..., h_2*255-1)
    #     - The secret scalar k is k = 2_b-2 + sum_3^b-3 (2^i*h_i)
    # This explains that the three LSBs of k are zero and the 253th bit is
    # always set.
    # The last three LSBs are zero.
    t[0] &= 248
    # The most significant byte is < 128 since the scalar is less than 2^255.
    t[31] &= 127
    # The 253th bit is always 1.
    t[31] |= 64

    # Decode the the field element pk into a point in p3 representation
    # on the twisted Edwards curve.
    p = Ge25519.unpack(pk)

    # Montgomery ladder for scalar multiplication. This is not constant-time
    # since it depends on the size of the scalar, and thus not secure against
    # side-channel attacks.
    k = p
    bit_start = 5
    for i in range(31, -1, -1):
        for j in range(bit_start, -1, -1):
            k = Ge25519.double(k)
            if (t[i] >> j) & 1:
                k = Ge25519.add(k, p)

        bit_start = 7

    # Encode the resulting point back to the byte array.
    ss = k.pack()
    return ss


def crypto_scalarmult_base(sk: bytes) -> bytes:
    """Compute k*B where k is a secret scalar in GL(P) and B is the base point
    of Ecdh25519 curve."""
    base = Ge25519.base()
    t = base.pack()
    return crypto_scalarmult(sk, t)
