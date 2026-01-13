"""Constants used in group arithmetic on the twisted Edwards curve:
-x^2 + y^2 = 1 + dx^2y^2."""

from dataclasses import dataclass

from .fe25519 import Fe25519


@dataclass
class Ge25519:
    """Extended twisted Edwards coordinate of a point on the twisted Edwards
    curve. Also referred to as p3 representation. The map to affine
    representation is:
        (X, Y, Z, T) -> (X/Z, Y/Z, 1, XY/Z)
    """

    x: Fe25519
    y: Fe25519
    z: Fe25519
    t: Fe25519

    def __post_init__(self):
        if self.z == 0:
            raise ValueError("Z must be non-zero")

    @classmethod
    def identity(cls) -> "Ge25519":
        """Return the identity point of Ecdh25519."""
        zero = Fe25519.zero()
        one = Fe25519.one()
        return cls(zero, one, one, zero)

    @classmethod
    def base(cls) -> "Ge25519":
        """Return the base point of Ecdh25519."""
        x = Fe25519(
            [
                0x1A,
                0xD5,
                0x25,
                0x8F,
                0x60,
                0x2D,
                0x56,
                0xC9,
                0xB2,
                0xA7,
                0x25,
                0x95,
                0x60,
                0xC7,
                0x2C,
                0x69,
                0x5C,
                0xDC,
                0xD6,
                0xFD,
                0x31,
                0xE2,
                0xA4,
                0xC0,
                0xFE,
                0x53,
                0x6E,
                0xCD,
                0xD3,
                0x36,
                0x69,
                0x21,
            ]
        )
        y = Fe25519(
            [
                0x58,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
                0x66,
            ]
        )
        z = Fe25519(
            [
                0x01,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            ]
        )
        t = Fe25519(
            [
                0xA3,
                0xDD,
                0xB7,
                0xA5,
                0xB3,
                0x8A,
                0xDE,
                0x6D,
                0xF5,
                0x52,
                0x51,
                0x77,
                0x80,
                0x9F,
                0xF0,
                0x20,
                0x7D,
                0xE3,
                0xAB,
                0x64,
                0x8E,
                0x4E,
                0xEA,
                0x66,
                0x65,
                0x76,
                0x8B,
                0xD7,
                0x0F,
                0x5F,
                0x87,
                0x67,
            ]
        )
        return cls(x, y, z, t)

    @staticmethod
    def _add_p1p1(p: "Ge25519", q: "Ge25519") -> "Ge25519P1P1":
        """Given two points p and q in p3 representation, compute p + q.
        The output is in p1p1 representation.
        """
        # A = (Y1 - X1) * (Y2 - X2)
        a = Fe25519.sub(p.y, p.x)
        t = Fe25519.sub(q.y, q.x)
        a = Fe25519.mul(a, t)

        # B = (Y1 + X1) * (Y2 + X2)
        b = Fe25519.add(p.y, p.x)
        t = Fe25519.add(q.y, q.x)
        b = Fe25519.mul(b, t)

        # C = (2 * d) * (T1 * T2)
        c = Fe25519.mul(p.t, q.t)
        ec2d = Fe25519.ec2d()
        c = Fe25519.mul(c, ec2d)

        # D = 2 * Z1 * Z2
        d = Fe25519.mul(p.z, q.z)
        d = Fe25519.double(d)

        e = Fe25519.sub(b, a)  # E = B - A
        f = Fe25519.sub(d, c)  # F = D - C
        g = Fe25519.add(d, c)  # G = D + C
        h = Fe25519.add(b, a)  # H = B + A

        return Ge25519P1P1(e, h, g, f)

    @classmethod
    def unpack(cls, x: bytes) -> "Ge25519":
        """Decode a byte-string into a point on the twisted Edwards curve,
        using Hamburg's "risetto" approach.
        Appendix A.2 in https://eprint.iacr.org/2015/673.pdf.
        Implementation and comments follows the algorithm defined in:
            https://ristretto.group/formulas/decoding.html
        with reference to the implementation in:
            https://cryptojedi.org/peter/teaching/engineering-crypto-software-2025.shtml
        """

        s = Fe25519.unpack(x)

        # Abort if s is non-negative.
        if Fe25519.isnegative(s):
            raise ValueError("s is negative")

        # u1 = 1 + a*s^2; u2 = 1 - a*s^2, where a = -1.
        s2 = Fe25519.square(s)
        one = Fe25519.one()
        u1 = Fe25519.sub(one, s2)
        u2 = Fe25519.add(one, s2)

        # v = a*d*u1^2 - u2^2, where a = -1.
        v = Fe25519.square(u1)
        u2_2 = Fe25519.square(u2)
        ecd = Fe25519.ecd()
        v = Fe25519.mul(v, ecd)
        v = Fe25519.add(v, u2_2)
        v = Fe25519.neg(v)

        # isr = invsqrt(v*u2^2).
        t = Fe25519.mul(v, u2_2)
        isr = Fe25519.invsqrt(t)

        #  Abort if the square root does not exist.
        chk = Fe25519.square(isr)
        chk = Fe25519.mul(chk, t)
        if not Fe25519.iseq(chk, one):
            raise ValueError("Square root does not exist")

        # dx = isr*u2
        # dy = isr*dx*v
        dx = Fe25519.mul(isr, u2)
        dy = Fe25519.mul(dx, isr)
        dy = Fe25519.mul(dy, v)

        # x = |2*s*dx|. Compute x = 2*s*dx and negate if it is negative.
        x = Fe25519.mul(s, dx)
        x = Fe25519.double(x)
        if Fe25519.isnegative(x):
            x = Fe25519.neg(x)

        # y = u1*dy
        y = Fe25519.mul(u1, dy)

        # z = 1
        z = one

        # t = x*y
        t = Fe25519.mul(x, y)

        # If t is negative or y == 0, abort.
        if Fe25519.isnegative(t):
            raise ValueError("t is negative")
        zero = Fe25519.zero()
        if Fe25519.iseq(y, zero):
            raise ValueError("y is zero")

        return cls(x, y, z, t)

    def pack(self) -> bytes:
        """Encode a Risetto point in extended coordinates to a byte-string,
        using Hamburg's "risetto" approach.
        Appendix A.1 in https://eprint.iacr.org/2015/673.pdf.
        Implementation and comments follows the algorithm defined in:
            https://ristretto.group/formulas/encoding.html
        with reference to the implementation in:
            https://cryptojedi.org/peter/teaching/engineering-crypto-software-2025.shtml
        """
        # u1 = (z + y)*(z - y)
        d = Fe25519.add(self.z, self.y)
        u1 = Fe25519.sub(self.z, self.y)
        u1 = Fe25519.mul(d, u1)

        # u2 = x*y
        u2 = Fe25519.mul(self.x, self.y)

        # isr = invsqrt(u1*u2^2)
        isr = Fe25519.square(u2)
        isr = Fe25519.mul(u1, isr)
        isr = Fe25519.invsqrt(isr)

        # d1 = u1*isr
        # d2 = u2*isr
        d1 = Fe25519.mul(u1, isr)
        d2 = Fe25519.mul(u2, isr)

        # zinv = d1*d2*t
        zinv = Fe25519.mul(d1, d2)
        zinv = Fe25519.mul(zinv, self.t)

        # If zinv*t0 is negative, do:
        #     (x', y') = (y*sqrt(-1), x*sqrt(-1))
        #     d = d1/sqrt(-1 - d)
        # Otherwise, do:
        #     (x', y') = (x, y)
        #     d = d2
        t = Fe25519.mul(zinv, self.t)
        b = Fe25519.isnegative(t)
        if b:
            sqrtm1 = Fe25519.sqrtm1()
            magic = Fe25519.magic()
            xprime = Fe25519.mul(self.y, sqrtm1)
            yprime = Fe25519.mul(self.x, sqrtm1)
            d = Fe25519.mul(d1, magic)
        else:
            xprime = self.x
            yprime = self.y
            d = d2

        # If x'*zinv is negative, y' = -y'.
        t = Fe25519.mul(xprime, zinv)
        b = Fe25519.isnegative(t)
        if b:
            yprime = Fe25519.neg(yprime)

        # s = |(z - y)*d|
        s = Fe25519.sub(self.z, yprime)
        s = Fe25519.mul(s, d)
        b = Fe25519.isnegative(s)
        if b:
            s = Fe25519.neg(s)

        r = Fe25519.pack(s)
        return r

    @classmethod
    def add(cls, p: "Ge25519", q: "Ge25519") -> "Ge25519":
        """Compute x + y where x and y are two points in p3 representation on the
        twisted Edwards curve. Output is also in p3 representation.
        """
        t = cls._add_p1p1(p, q)
        r = t.to_p3()
        return r

    @classmethod
    def double(cls, p: "Ge25519") -> "Ge25519":
        """Compute 2*x where x is a point in p3 representation on the
        twisted Edwards curve. Output is also in p3 representation.
        """
        t = Ge25519P2(p.x, p.y, p.z)
        t = Ge25519P2.double_p1p1(t)
        r = t.to_p3()
        return r


@dataclass
class Ge25519P1P1:
    """Extended twisted Edwards coordinate of a sum of two points in p3
    representation on the twisted Edwards curve. Since after addition or
    doubling, the resulting point does not satisfy the condition: Z*T = X*Y, we
    use this p1p1 representation to hold the result, and convert it back to p3.
    """

    x: Fe25519
    y: Fe25519
    z: Fe25519
    t: Fe25519

    def __post_init__(self):
        if self.z == 0:
            raise ValueError("Z must be non-zero")

    def to_p2(self) -> "Ge25519P2":
        """Convert p1p1 point representation to p2 point representation:
        (x=X, y=Y, z=Z, t=T) --> (x=X*T, y=Y*Z, z=Z*T)
        """
        x = Fe25519.mul(self.x, self.t)
        y = Fe25519.mul(self.y, self.z)
        z = Fe25519.mul(self.z, self.t)

        return Ge25519P2(x, y, z)

    def to_p3(self) -> "Ge25519":
        """Convert p1p1 point representation to p3 point representation.
        (x=X, y=Y, z=Z, t=T) --> (x=X*T, y=Y*Z, z=Z*T, t=X*Y)
        """
        r = self.to_p2()
        t = Fe25519.mul(self.x, self.y)

        return Ge25519(r.x, r.y, r.z, t)


@dataclass
class Ge25519P2:
    """Projective coordinates of a group element on the twisted Edwards curve.
    Referred to as p2 representation. The map to affine representation is:
        (X, Y, Z) -> (X/Z, Y/Z)
    """

    x: Fe25519
    y: Fe25519
    z: Fe25519

    def __post_init__(self):
        if self.z == 0:
            raise ValueError("Z must be non-zero")

    @classmethod
    def double_p1p1(cls, p: "Ge25519P2") -> "Ge25519P1P1":
        """Double the point p in p2 representation.
        The output is in p1p1 representation.

        This follows Section 3.3, Dedicated Doubling in E^e in [TEC-revisited].
        """
        a = Fe25519.square(p.x)  # A = X1^2
        b = Fe25519.square(p.y)  # B = Y1^2

        # C = 2 * (Z1)^2
        c = Fe25519.square(p.z)
        c = Fe25519.double(c)

        # D = -A
        d = Fe25519.neg(a)

        # E = (X1 + Y1)^2 - A - B
        e = Fe25519.add(p.x, p.y)
        e = Fe25519.square(e)
        e = Fe25519.sub(e, a)
        e = Fe25519.sub(e, b)

        g = Fe25519.add(d, b)  # G = D + B
        f = Fe25519.sub(g, c)  # F = G - C
        h = Fe25519.sub(d, b)  # H = D - B

        return Ge25519P1P1(e, h, g, f)
