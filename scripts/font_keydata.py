#!/usr/bin/env python3
"""The cipher of Warcraft III's installed key files (font\\font.gid, .exp,
.clh, .ccd inside the MPQs), as game.dll 1.26a reads them.

Reverse-engineered from game.dll (addresses are game.dll 1.26a VAs):

  6F553AA0  load a font\\font.* file (Storm SFileLoadFile) and decode it
  6F555630  decode: 8-byte trailer after N 64-byte blocks
  6F555450  cipher setup; 6F5559A0 the 19-byte key string
  6F555A10  SHA-1 compression with SHA-0's message schedule and rotations
            built with arithmetic shifts (Battle.net's "broken SHA-1"),
            words loaded little-endian, no padding: the raw state is used
  6F556170, 6F5561F0, 6F556370, 6F5560D0, 6F556100
            IDEA (PGP's reference: expandKey, invertKey, cipher, mul, mulInv)
            on little-endian 16-bit words

The encoder is the exact inverse of the decoder; the installer's
<encrypt> step must produce what this encoder produces (checked against the
official installer's output: tests/test_font_keydata.py).
"""

M32 = 0xFFFFFFFF


class MsvcRand:
    """msvcr80 srand/rand."""

    def __init__(self, seed):
        self.s = seed & M32

    def __call__(self):
        self.s = (self.s * 214013 + 2531011) & M32
        return (self.s >> 16) & 0x7FFF


def _rol(x, n):
    # (x << n) | (x >> (32 - n)) with an arithmetic right shift (6F555A10).
    sx = x - (1 << 32) if x & 0x80000000 else x
    return ((x << n) | ((sx >> (32 - n)) & M32)) & M32


IV = (0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0)


def compress(state, block):
    """6F555A10: one 64-byte block into a 5-word state."""
    w = [int.from_bytes(block[4 * i:4 * i + 4], "little") for i in range(16)]
    for t in range(16, 80):
        w.append(w[t - 3] ^ w[t - 8] ^ w[t - 14] ^ w[t - 16])
    a, b, c, d, e = state
    for t in range(80):
        if t < 20:
            f, k = (b & c) | (~b & d), 0x5A827999
        elif t < 40:
            f, k = b ^ c ^ d, 0x6ED9EBA1
        elif t < 60:
            f, k = (b & c) | (b & d) | (c & d), 0x8F1BBCDC
        else:
            f, k = b ^ c ^ d, 0xCA62C1D6
        a, b, c, d, e = (_rol(a, 5) + (f & M32) + e + w[t] + k) & M32, a, _rol(b, 30), c, d
    return tuple((x + y) & M32 for x, y in zip(state, (a, b, c, d, e)))


def state_bytes(state):
    return b"".join(x.to_bytes(4, "little") for x in state)


# ---- IDEA (16-bit words, little-endian in memory) ---------------------------

def _mul(a, b):
    """6F5560D0: multiplication modulo 65537, 0 standing for 65536."""
    if a == 0:
        return (1 - b) & 0xFFFF
    if b == 0:
        return (1 - a) & 0xFFFF
    p = a * b
    lo, hi = p & 0xFFFF, p >> 16
    return (lo - hi + (lo < hi)) & 0xFFFF


def _mul_inv(x):
    if x <= 1:
        return x
    return pow(x, 65535, 65537) & 0xFFFF  # x^-1 mod 65537 (prime)


def expand_key(key16):
    """6F556170: the 52 encryption subkeys."""
    z = [int.from_bytes(key16[2 * i:2 * i + 2], "little") for i in range(8)]
    while len(z) < 52:
        base = len(z) // 8 * 8 - 8
        i = len(z) % 8
        z.append(((z[base + (i + 1) % 8] << 9) | (z[base + (i + 2) % 8] >> 7)) & 0xFFFF)
    return z


def invert_key(ek):
    """6F5561F0: decryption subkeys."""
    dk = [0] * 52
    p = 0
    t1, t2, t3, t4 = _mul_inv(ek[p]), -ek[p + 1] & 0xFFFF, -ek[p + 2] & 0xFFFF, _mul_inv(ek[p + 3])
    p += 4
    q = 52
    q -= 4
    dk[q:q + 4] = [t1, t2, t3, t4]
    for r in range(7):
        t1, t2 = ek[p], ek[p + 1]
        p += 2
        q -= 2
        dk[q:q + 2] = [t1, t2]
        t1, t2, t3, t4 = _mul_inv(ek[p]), -ek[p + 1] & 0xFFFF, -ek[p + 2] & 0xFFFF, _mul_inv(ek[p + 3])
        p += 4
        q -= 4
        dk[q:q + 4] = [t1, t3, t2, t4]
    t1, t2 = ek[p], ek[p + 1]
    p += 2
    q -= 2
    dk[q:q + 2] = [t1, t2]
    t1, t2, t3, t4 = _mul_inv(ek[p]), -ek[p + 1] & 0xFFFF, -ek[p + 2] & 0xFFFF, _mul_inv(ek[p + 3])
    q -= 4
    dk[q:q + 4] = [t1, t2, t3, t4]
    return dk


def idea(block8, k):
    """6F556370: one 8-byte block with subkeys k."""
    x1, x2, x3, x4 = (int.from_bytes(block8[2 * i:2 * i + 2], "little") for i in range(4))
    p = 0
    for _ in range(8):
        x1 = _mul(x1, k[p])
        x2 = (x2 + k[p + 1]) & 0xFFFF
        x3 = (x3 + k[p + 2]) & 0xFFFF
        x4 = _mul(x4, k[p + 3])
        s3 = x3
        x3 = _mul(x3 ^ x1, k[p + 4])
        s2 = x2
        x2 = _mul(((x2 ^ x4) + x3) & 0xFFFF, k[p + 5])
        x3 = (x3 + x2) & 0xFFFF
        x1 ^= x2
        x4 ^= x3
        x2 ^= s3
        x3 ^= s2
        p += 6
    out = (_mul(x1, k[p]), (x3 + k[p + 1]) & 0xFFFF, (x2 + k[p + 2]) & 0xFFFF, _mul(x4, k[p + 3]))
    return b"".join(v.to_bytes(2, "little") for v in out)


# ---- the file format ---------------------------------------------------------

def key_string():
    """6F5559A0(buf, 0x14): 19 non-zero rand() bytes after srand(0x150B)."""
    r, out = MsvcRand(0x150B), bytearray()
    while len(out) < 19:
        b = r() & 0xFF
        if b:
            out.append(b)
    return bytes(out)


def _setup(encrypt):
    """6F555450: (IDEA subkeys of context 0, SHA state of context 0)."""
    r = MsvcRand(0x4FA7)
    buf = bytearray(r() & 0xFF for _ in range(0x70))
    ks = key_string()
    d = state_bytes(compress(IV, bytes(ks[n % len(ks)] for n in range(64))))
    for n in range(0x70):
        buf[n] ^= d[n % 20]
    ek = expand_key(bytes(buf[0:16]))
    return (ek if encrypt else invert_key(ek)), compress(IV, bytes(buf[0x30:0x70]))


def decode(data):
    """6F555630 + 6F553A70: the plaintext, or None where the game rejects it."""
    if len(data) <= 8 or (len(data) - 8) % 64:
        return None
    k, h = _setup(False)
    out = bytearray()
    for i in range((len(data) - 8) // 64):
        t = data[64 * i:64 * i + 64]
        hb = state_bytes(h)
        u = b"".join(idea(t[j:j + 8], k) for j in range(0, 64, 8)) if i % 8 == 0 else t
        v = bytes((u[p] - hb[(63 - p) % 20]) & 0xFF for p in range(64))
        if i % 16 == 0:
            h = compress(h, v)
        out += v
    trailer = data[-8:]
    if trailer[4] != 0 or int.from_bytes(trailer[0:4], "little") != h[0]:
        return None
    n = len(data) - 8 - 64 + trailer[5]
    if n <= 0 or n >= len(data):  # 6F553A70: 0 < length < buffer size
        return None
    return bytes(out[:n])


def encode(plain, pad, tail=b"\0\0"):
    """Inverse of decode for one 64-byte block: `pad` fills the block after
    the plaintext (and its NUL), `tail` is trailer bytes 6-7."""
    assert 0 < len(plain) < 64 and len(pad) == 64 - len(plain) and len(tail) == 2
    k, h = _setup(True)
    v = plain + pad
    hb = state_bytes(h)
    u = bytes((v[p] + hb[(63 - p) % 20]) & 0xFF for p in range(64))
    t = b"".join(idea(u[j:j + 8], k) for j in range(0, 64, 8))
    h = compress(h, v)
    return t + h[0].to_bytes(4, "little") + bytes([0, len(plain)]) + tail
