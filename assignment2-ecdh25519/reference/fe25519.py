"""
Implement field arithemetic of field GL(P) where P = 2^255 - 19.
This implementation follows the one in:
    https://cryptojedi.org/peter/teaching/engineering-crypto-software-2025.shtml
"""

from dataclasses import dataclass

P = (1 << 255) - 19
N = 32


@dataclass
class Fe25519:
    """Class represents a field element as a 32-byte array.
    Assume that the field element is always canonical in GL(P).
    """

    v: bytearray

    def __post_init__(self):
        if len(self.v) > N:
            raise ValueError(
                f"A field element must be {N} bytes long maximum, "
                f"got {len(self.v)} bytes"
            )
        if len(self.v) < N:
            # Pad with zeros if less than 32 bytes.
            self.v.extend([0] * (N - len(self.v)))

    def __getitem__(self, i):
        return self.v[i]

    def __setitem__(self, i, value):
        if i != (N - 1):
            self.v[i] = value & 0xFF
        else:
            self.v[i] = value & 0x7F

    @classmethod
    def zero(cls) -> "Fe25519":
        """Return the neutral element."""
        x = [0] * N
        return cls(x)

    @classmethod
    def one(cls) -> "Fe25519":
        """Return 1 in GL(P)."""
        x = [0] * N
        x[0] = 1
        return cls(x)

    @classmethod
    def sqrtm1(cls) -> "Fe25519":
        """Return sqrt(-1)"""
        x = [
            0xB0,
            0xA0,
            0x0E,
            0x4A,
            0x27,
            0x1B,
            0xEE,
            0xC4,
            0x78,
            0xE4,
            0x2F,
            0xAD,
            0x06,
            0x18,
            0x43,
            0x2F,
            0xA7,
            0xD7,
            0xFB,
            0x3D,
            0x99,
            0x00,
            0x4D,
            0x2B,
            0x0B,
            0xDF,
            0xC1,
            0x4F,
            0x80,
            0x24,
            0x83,
            0x2B,
        ]
        return cls(x)

    @classmethod
    def msqrtm1(cls) -> "Fe25519":
        """Return -1sqrt(-1)."""
        x = [
            0x3D,
            0x5F,
            0xF1,
            0xB5,
            0xD8,
            0xE4,
            0x11,
            0x3B,
            0x87,
            0x1B,
            0xD0,
            0x52,
            0xF9,
            0xE7,
            0xBC,
            0xD0,
            0x58,
            0x28,
            0x04,
            0xC2,
            0x66,
            0xFF,
            0xB2,
            0xD4,
            0xF4,
            0x20,
            0x3E,
            0xB0,
            0x7F,
            0xDB,
            0x7C,
            0x54,
        ]
        return cls(x)

    @classmethod
    def ecd(cls) -> "Fe25519":
        """Return the constant d."""
        x = [
            0xA3,
            0x78,
            0x59,
            0x13,
            0xCA,
            0x4D,
            0xEB,
            0x75,
            0xAB,
            0xD8,
            0x41,
            0x41,
            0x4D,
            0x0A,
            0x70,
            0x00,
            0x98,
            0xE8,
            0x79,
            0x77,
            0x79,
            0x40,
            0xC7,
            0x8C,
            0x73,
            0xFE,
            0x6F,
            0x2B,
            0xEE,
            0x6C,
            0x03,
            0x52,
        ]
        return cls(x)

    @classmethod
    def ec2d(cls) -> "Fe25519":
        """Return the constant d."""
        x = [
            0x59,
            0xF1,
            0xB2,
            0x26,
            0x94,
            0x9B,
            0xD6,
            0xEB,
            0x56,
            0xB1,
            0x83,
            0x82,
            0x9A,
            0x14,
            0xE0,
            0x00,
            0x30,
            0xD1,
            0xF3,
            0xEE,
            0xF2,
            0x80,
            0x8E,
            0x19,
            0xE7,
            0xFC,
            0xDF,
            0x56,
            0xDC,
            0xD9,
            0x06,
            0x24,
        ]
        return cls(x)

    @classmethod
    def magic(cls) -> "Fe25519":
        """Return the constant magic = 1/sqrt(-1-d)."""
        x = [
            0x03,
            0xBF,
            0xA2,
            0x7F,
            0x55,
            0x02,
            0x37,
            0x66,
            0x41,
            0x8D,
            0xBE,
            0xA5,
            0xE8,
            0xE9,
            0xD0,
            0x62,
            0xBF,
            0x27,
            0xFE,
            0x01,
            0x6E,
            0x84,
            0x3D,
            0xE9,
            0x5D,
            0x03,
            0x50,
            0x30,
            0xFA,
            0x76,
            0x93,
            0x07,
        ]
        return cls(x)

    def pack(self) -> bytes:
        """Serialize an element to bytes of length 32."""
        r = Fe25519.freeze(self)
        return bytes(r.v)

    @classmethod
    def unpack(cls, b: bytes) -> "Fe25519":
        """Create an element from bytes of length 32."""
        if len(b) != N:
            raise ValueError("Input must be 32 bytes")
        r = list(b)
        r[N - 1] &= 127
        return cls(r)

    def _to_int(self) -> int:
        """Pack a field element as 32B array into an integer."""
        r = int.from_bytes(self.v, byteorder="little")
        return r

    @classmethod
    def _from_int(cls, x: int) -> "Fe25519":
        """Unpack an integer into a field element represented as 32B array.
        Assume that input x is canonical in GL(P).
        """
        r = x.to_bytes(N, byteorder="little")
        return cls(r)

    @classmethod
    def _reduce_add_sub(cls, x: "Fe25519") -> "Fe25519":
        """Reduce raw sum of an addition in GL(P)."""
        for _ in range(2):
            t = x.v[N - 1] >> 7
            x.v[N - 1] &= 127
            t *= 19
            x.v[0] += t
            for i in range(N - 1):
                t = x.v[i] >> 8
                x.v[i + 1] += t
                x.v[i] &= 255
        return x

    @classmethod
    def _reduce_mul(cls, x: "Fe25519") -> "Fe25519":
        """Reduce raw product of a multiplication in GL(P)."""
        for _ in range(3):
            t = x.v[N - 1] >> 7
            x.v[N - 1] &= 127
            t *= 19
            x.v[0] += t
            for i in range(N - 1):
                t = x.v[i] >> 8
                x.v[i + 1] += t
                x.v[i] &= 255
        return x

    @classmethod
    def add(cls, x: "Fe25519", y: "Fe25519") -> "Fe25519":
        """Compute (x + y) mod P."""
        r = cls([0] * N)
        for i in range(N):
            r.v[i] = x.v[i] + y.v[i]
        r = cls._reduce_add_sub(r)
        return r

    @classmethod
    def sub(cls, x: "Fe25519", y: "Fe25519") -> "Fe25519":
        """Compute (x - y) mod P."""
        r = cls([0] * N)
        r.v[0] = x.v[0] + 0x1DA - y.v[0]
        r.v[N - 1] = x.v[N - 1] + 0xFE - y.v[N - 1]
        for i in range(1, N - 1):
            r.v[i] = x.v[i] + 0x1FE - y.v[i]
        r = cls._reduce_add_sub(r)
        return r

    @classmethod
    def neg(cls, x: "Fe25519") -> "Fe25519":
        """Compute (-x) mod P."""
        fe25519_zero = cls.zero()
        r = cls.sub(fe25519_zero, x)
        return r

    @classmethod
    def double(cls, x: "Fe25519") -> "Fe25519":
        """Compute 2*x mod P."""
        r = cls.add(x, x)
        return r

    @classmethod
    def mul(cls, x: "Fe25519", y: "Fe25519") -> "Fe25519":
        """Compute (x * y) mod P."""
        t = [0] * (2 * N - 1)

        for i in range(N):
            for j in range(N):
                t[i + j] += x.v[i] * y.v[j]

        r = cls([0] * N)
        for i in range(N, 2 * N - 1):
            r.v[i - N] = t[i - N] + t[i] * 38
        r.v[N - 1] = t[N - 1]

        r = cls._reduce_mul(r)
        return r

    @classmethod
    def square(cls, x: "Fe25519") -> "Fe25519":
        """Compute (x^2) mod P."""
        r = cls.mul(x, x)
        return r

    @classmethod
    def freeze(cls, x: "Fe25519") -> "Fe25519":
        """Compute x mod P, given that x < 2^255."""
        m = x.v[N - 1] == 127
        for i in range(N - 2, 0, -1):
            m &= x.v[i] == 255
        m &= x.v[0] >= 237
        m = -m
        x.v[N - 1] -= m & 127
        for i in range(N - 2, 0, -1):
            x.v[i] -= m & 255
        x.v[0] -= m & 237
        return x

    @classmethod
    def isnegative(cls, x: "Fe25519") -> bool:
        """Return true if x has LSB set."""
        r = cls.freeze(x)
        return bool(r[0] & 1)

    @classmethod
    def iseq(cls, x: "Fe25519", y: "Fe25519") -> bool:
        """Return true if x == y."""
        x = cls.freeze(x)
        y = cls.freeze(y)

        for i in range(N):
            if x[i] != y[i]:
                return False
        return True

    @classmethod
    def pow2523(cls, x: "Fe25519") -> "Fe25519":
        """Compute x^(2^252 - 3) mod P."""
        # Compute exp = 2.
        x2 = cls.square(x)
        # Compute exp = 4.
        x4 = cls.square(x2)
        # Compute exp = 8.
        x8 = cls.square(x4)
        # Compute exp = 9 = 8 + 1.
        x9 = cls.mul(x8, x)
        # Compute exp = 11 = 9 + 2.
        x11 = cls.mul(x9, x2)
        # Compute exp = 22 = 11*2.
        x22 = cls.square(x11)
        # Compute exp = 31 = 2^5 - 1.
        x2_5 = cls.mul(x22, x9)

        # Compute exp = 2*(2^5 - 1) = 2^6 - 2.
        r = cls.square(x2_5)
        # Compute exp = 2^4*(2^6 - 2) = 2^10 - 2^5.
        for _ in range(4):
            r = cls.square(r)
        # Compute exp = (2^10 - 2^5) + (2^5 - 1) = (2^10 - 1).
        x2_10 = cls.mul(r, x2_5)

        # Compute exp = 2*(2^10 - 1) = 2^11 - 2.
        r = cls.square(x2_10)
        # Compute exp = 2^9*(2^11 - 2) = 2^20 - 2^10.
        for _ in range(9):
            r = cls.square(r)
        # Compute exp = (2^20 - 2^10) + (2^10 - 1) = 2^20 - 1.
        x2_20 = cls.mul(r, x2_10)

        # Compute exp = 2*(2^20 - 1) = 2^21 - 2.
        r = cls.square(x2_20)
        # Compute exp = 2^19*(2^21 - 2) = 2^40 - 2^20.
        for _ in range(19):
            r = cls.square(r)
        # Compute exp = (2^40 - 2^20) + (2^20 - 1) = 2^40 - 1.
        x2_40 = cls.mul(r, x2_20)

        # Compute exp = 2*(2^40 - 1) = 2^41 - 2.
        r = cls.square(x2_40)
        # Compute exp = 2^9*(2^41 - 2) = 2^50 - 2^10.
        for _ in range(9):
            r = cls.square(r)
        # Compute exp = (2^50 - 2^10) + (2^10 - 1) = 2^50 - 1.
        x2_50 = cls.mul(r, x2_10)

        # Compute exp = 2*(2^50 - 1) = 2^51 - 2.
        r = cls.square(x2_50)
        # Compute exp = 2^49*(2^51 - 2) = 2^100 - 2^50.
        for _ in range(49):
            r = cls.square(r)
        # Compute exp = (2^100 - 2^50) + (2^50 - 1) = 2^100 - 1.
        x2_100 = cls.mul(r, x2_50)

        # Compute exp = 2*(2^100 - 1) = 2^101 - 2.
        r = cls.square(x2_100)
        # Compute exp = 2^99*(2^101 - 2) = 2^200 - 2^100.
        for _ in range(99):
            r = cls.square(r)
        # Compute exp = (2^200 - 2^100) + (2^100 - 1) = 2^200 - 1.
        x2_200 = cls.mul(r, x2_100)

        # Compute exp = 2*(2^200 - 1) = 2^201 - 2.
        r = cls.square(x2_200)
        # Compute exp = 2^49*(2^201 - 2) = 2^250 - 2^50.
        for _ in range(49):
            r = cls.square(r)
        # Compute exp = (2^250 - 2^50) + (2^50 - 1) = 2^250 - 1.
        x2_250 = cls.mul(r, x2_50)

        # Compute exp = 2*(2^250 - 1) = 2^251 - 2.
        r = cls.square(x2_250)
        # Compute exp = 2*(2^251 - 2) = 2^252 - 4.
        r = cls.square(r)
        # Compute exp = (2^252 - 4) + 1 = 2^252 - 3.
        r = cls.mul(r, x)

        return r

    @classmethod
    def invsqrt(cls, x: "Fe25519") -> "Fe25519":
        """Given x in GL(P), compute the inverse square root of x, i.e.,
        r such that r^2 * x = +-1 mod P (1) (as -1 is also q square in GL(P)).
        Note that this is equivalent to r^2 = a mod P (2) where a = x^-1 mod P.

        As P = 5 mod 8, r = +- a^(q+3)/8 is a solution of (2). Then, we have:
            r = +- (x^-1)^(q+3)/8 = +- x^[(q-1)-(q+3)/8] = +- (x^7)^(q-5)/8 * x3
        where (q-5)/8 = 2^252 - 3.

        Thus, we proceed as follows:
            (1) Compute r = (x^7)^(q-5)/8 * x3
            (2) Compute chk = r^2 * x
            (3) Compute r2 = r * sqrt(-1)
            (4) Check if chk = r^2 * x = 1. If yes, return r.
                Else, return r2 = r * sqrt(-1).
        """

        # Compute x^7.
        x2 = cls.square(x)
        x3 = cls.mul(x2, x)
        x4 = cls.square(x2)
        x7 = cls.mul(x4, x3)

        # Compute (x^7)^(2^252 - 3) * x^3.
        r = cls.pow2523(x7)
        r = cls.mul(r, x3)

        # Compute chk = r^2 * x.
        chk = cls.square(r)
        chk = cls.mul(chk, x)

        # Compute r2 = r * sqrt(-1).
        sqrtm1 = cls.sqrtm1()
        r2 = cls.mul(r, sqrtm1)

        # Check if r^2 * x = 1 or r^2 * x = -1.
        one = cls.one()
        if cls.iseq(chk, one):
            return r
        else:
            return r2
