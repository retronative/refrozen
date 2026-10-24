#!/usr/bin/env python3
"""Tests for scripts/font_keydata.py, the cipher of the installed key files.

  /opt/homebrew/bin/python3 -I tests/test_font_keydata.py

Expected values are independent of the code under test:
- published vectors: MSVC rand() after srand(1); IDEA's reference test vector
  (Lai, key 0001..0008, plaintext 0000 0001 0002 0003 -> 11FB ED2B 0198 6DE5);
  multiplication modulo 65537 from its definition;
- x86 semantics (Intel SDM): shl/sar rotations as game.dll 6F555A10 builds them;
- the official installer's output (the Wine oracle install, made with the test
  keys of the player's readme): it must decode with valid checksums, give
  exactly those keys, and re-encode byte for byte.
Key material is compared, never printed (check_secret).

Needs game data for the oracle part: game/wine-oracle (REFROZEN_ORACLE) and the
readme (REFROZEN_KEY_README); without them those checks are reported SKIPPED
and the run fails, so a gate never passes on missing data.
"""
import os
import re
import sys

ROOT = os.environ.get("REFROZEN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.environ.get("REFROZEN_SCRIPTS", os.path.join(ROOT, "scripts"))  # tests/mutate.py
sys.path.insert(0, SCRIPTS)
import font_keydata as fk  # noqa: E402

ORACLE = os.environ.get("REFROZEN_ORACLE", os.path.join(ROOT, "game", "wine-oracle"))
README = os.environ.get("REFROZEN_KEY_README", os.path.join(
    os.path.dirname(ROOT), "DOTA", "ICC Game client install", "Readme_for_real_you_need_this.txt"))
failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + ("" if ok else f": got {got!r}, want {want!r}"))


def check_secret(name, ok):
    global failures
    failures += not ok
    print(f"{'ok  ' if ok else 'FAIL'} {name}")


def words_le(*w):
    return b"".join(x.to_bytes(2, "little") for x in w)


def test_vectors():
    r = fk.MsvcRand(1)
    check("MSVC rand after srand(1)", [r() for _ in range(5)], [41, 18467, 6334, 26500, 19169])
    k = fk.expand_key(words_le(1, 2, 3, 4, 5, 6, 7, 8))
    ct = fk.idea(words_le(0, 1, 2, 3), k)
    check("IDEA reference vector", ct, words_le(0x11FB, 0xED2B, 0x0198, 0x6DE5))
    check("IDEA decryption subkeys invert it", fk.idea(ct, fk.invert_key(k)), words_le(0, 1, 2, 3))
    bad = [(a, b) for a in range(0, 65536, 251) for b in range(0, 65536, 257)
           if fk._mul(a, b) != ((a or 65536) * (b or 65536) % 65537) % 65536]
    check("IDEA multiplication modulo 65537", bad, [])
    # shl 5 | sar 27 of 0x80000000: 0 | FFFFFFF0; of 0x40000000: 0 | 00000008.
    check("rotations use an arithmetic shift", (fk._rol(0x80000000, 5), fk._rol(0x40000000, 5)),
          (0xFFFFFFF0, 0x00000008))


def oracle_files():
    sys.path.insert(0, SCRIPTS)
    import native_install as ni
    out = {}
    for mpq, names in (("war3.mpq", ("font\\font.gid", "font\\font.clh", "font\\font.ccd")),
                       ("War3x.mpq", ("font\\font.exp", "font\\font.ccd"))):
        m = ni.Mpq(os.path.join(ORACLE, mpq))
        for n in names:
            out[(mpq, n)] = m.read(n)
        m.close()
    return out


def readme_keys():
    keys = []
    for line in open(README, encoding="latin-1"):
        keys += re.findall(r"[A-Z0-9]{26}", re.sub(r"[\s-]", "", line).upper())
    return keys


def test_oracle():
    if not (os.path.isdir(ORACLE) and os.path.isfile(README)):
        global failures
        failures += 1
        print("SKIPPED oracle checks: game/wine-oracle or the readme is missing")
        return
    f = oracle_files()
    keys = readme_keys()
    for (mpq, name), product in ((("war3.mpq", "font\\font.gid"), "RoC"), (("War3x.mpq", "font\\font.exp"), "TFT")):
        data = f[(mpq, name)]
        plain = fk.decode(data)
        check_secret(f"{product} key file decodes, checksum valid", plain is not None)
        if plain is None:
            continue
        check_secret(f"{product} key file holds a readme key + NUL",
                     plain.endswith(b"\0") and plain[:-1].decode("latin-1") in keys)
        check_secret(f"{product} key file re-encodes byte for byte",
                     fk.encode(plain, b"\0" * (64 - len(plain))) == data)
        tampered = bytearray(data)
        tampered[17] ^= 0x01
        check(f"{product} key file with one bit flipped is rejected", fk.decode(bytes(tampered)), None)
    clh = f[("war3.mpq", "font\\font.clh")]
    name = fk.decode(clh)
    check_secret("user name file decodes, checksum valid", name is not None)
    if name is not None:
        check_secret("user name file re-encodes byte for byte",
                     fk.encode(name, b"\0" * (64 - len(name))) == clh)
    for mpq in ("war3.mpq", "War3x.mpq"):
        # cdkey1encode output is not in this cipher: game.dll's decoder rejects it.
        check(f"{mpq} font.ccd is rejected by the decoder", fk.decode(f[(mpq, "font\\font.ccd")]), None)


def test_installer_keys():
    # The installer's key step (scripts/native_install.py): a key as typed
    # (dashes, spaces, lower case) is stored as 26 characters of the
    # Warcraft III key alphabet; anything else is refused. The stored file
    # decodes back to the key and its NUL.
    sys.path.insert(0, SCRIPTS)
    import native_install as ni
    key = "2468-BCDF-GHJK-MNPR-TVWX-YZ2468".replace("-", "")[:26]
    check("key: dashes, spaces and case normalised",
          ni.normalise_key(" " + "-".join(key[i:i + 5] for i in range(0, 26, 5)).lower() + "\n"), key)
    check("key: 25 characters refused", ni.normalise_key(key[:25]), None)
    check("key: a character outside the alphabet refused", ni.normalise_key(key[:25] + "A"), None)
    check("key: '1' and 'O' are not key characters", (ni.normalise_key(key[:25] + "1"), ni.normalise_key(key[:25] + "O")),
          (None, None))
    data = ni.keyfile(key.encode() + b"\0")
    check("key file: 72 bytes", len(data), 72)
    check("key file decodes to the key and its NUL", fk.decode(data), key.encode() + b"\0")


def main():
    test_vectors()
    test_installer_keys()
    test_oracle()
    print("font keydata: ok" if not failures else f"font keydata: {failures} FAILED")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
