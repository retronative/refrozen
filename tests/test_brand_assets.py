"""Brand asset checks: the app icon, the website icons and the DMG background render.

Stdlib only. Needs macOS (sips, iconutil) for the regeneration checks; the DMG check also needs
Google Chrome and Node 22+ and is skipped with a message when they are missing.

    /opt/homebrew/bin/python3 -I tests/test_brand_assets.py
"""
import hashlib
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON = os.path.join(ROOT, 'assets', 'icon')
MASTER = os.path.join(ICON, 'refrozen-app-icon-master.png')
SMALL = os.path.join(ICON, 'refrozen-icon-small.svg')
ICNS = os.path.join(ICON, 'reFrozen.icns')
PUBLIC = os.path.join(ROOT, '.website', 'public')
MASTER_SHA256 = 'e55ffc5921936bb2038ab2b9638805760664b29f44ff2414954fa19003c92aa0'
WEB_FILES = ['favicon.ico', 'favicon-32.png', 'icon-192.png', 'icon-512.png', 'apple-touch-icon.png',
             'brand/mark-96.png', 'brand/mark-144.png']
# iconutil's element types for an iconset with 16-512 pt at 1x and 2x (Apple's icns format):
# ic04/ic05 are 16/32 px ARGB, the rest PNG with the pixel size given here.
ICNS_PNG = {b'ic11': 32, b'ic12': 64, b'ic07': 128, b'ic13': 256, b'ic08': 256, b'ic14': 512,
            b'ic09': 512, b'ic10': 1024}
ICNS_ARGB = {b'ic04', b'ic05'}
CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')


def png_size(blob):
    assert blob[:8] == b'\x89PNG\r\n\x1a\n', 'not a PNG'
    return struct.unpack('>II', blob[16:24])


def png_chunks(blob):
    p = 8
    while p < len(blob):
        n, kind = struct.unpack('>I4s', blob[p:p + 8])
        yield kind, blob[p + 8:p + 8 + n]
        p += 12 + n


def png_dpi(blob):
    for kind, data in png_chunks(blob):
        if kind == b'pHYs':
            x, y, unit = struct.unpack('>IIB', data)
            return (round(x * 0.0254), round(y * 0.0254)) if unit == 1 else None
    return (72, 72)  # no pHYs: viewers assume 72 dpi


def png_pixels(blob):
    """Decoded RGBA rows of an 8-bit RGBA, non-interlaced PNG."""
    w, h = png_size(blob)
    ihdr = dict(png_chunks(blob))[b'IHDR']
    assert ihdr[8] == 8 and ihdr[9] == 6 and ihdr[12] == 0, 'expected 8-bit RGBA, not interlaced'
    raw = zlib.decompress(b''.join(d for k, d in png_chunks(blob) if k == b'IDAT'))
    stride, prev, rows = w * 4, bytearray(w * 4), []
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for x in range(stride):
            a = line[x - 4] if x >= 4 else 0
            b, c = prev[x], prev[x - 4] if x >= 4 else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + ((a + b) >> 1)) & 255
            elif f == 4:
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(bytes(line))
        prev = line
    return rows


def png_alpha_bbox(blob, threshold):
    """Bounding box [x0, y0, x1, y1] of pixels with alpha >= threshold."""
    box = [1 << 30, 1 << 30, -1, -1]
    for y, line in enumerate(png_pixels(blob)):
        for x in range(len(line) // 4):
            if line[x * 4 + 3] >= threshold:
                box = [min(box[0], x), min(box[1], y), max(box[2], x), max(box[3], y)]
    return box


def icns_elements(blob):
    assert blob[:4] == b'icns' and struct.unpack('>I', blob[4:8])[0] == len(blob), 'bad icns header'
    p, out = 8, {}
    while p < len(blob):
        kind, n = struct.unpack('>4sI', blob[p:p + 8])
        out[kind] = blob[p + 8:p + n]
        p += n
    return out


def read(path):
    with open(path, 'rb') as f:
        return f.read()


@unittest.skipUnless(sys.platform == 'darwin' and shutil.which('sips') and shutil.which('iconutil'),
                     'needs macOS sips and iconutil')
class IconAssets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='refrozen-icons-')
        subprocess.run([os.path.join(ROOT, 'scripts', 'make_icons.sh'), '--out-dir', cls.tmp],
                       check=True, stdout=subprocess.DEVNULL)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_master_unchanged(self):
        self.assertEqual(hashlib.sha256(read(MASTER)).hexdigest(), MASTER_SHA256)

    def test_committed_icns_matches_fresh_generation(self):
        self.assertEqual(read(ICNS), read(os.path.join(self.tmp, 'reFrozen.icns')),
                         'assets/icon/reFrozen.icns is stale: run scripts/make_icons.sh')

    def test_committed_web_icons_match_fresh_generation(self):
        for name in WEB_FILES:
            with self.subTest(name=name):
                self.assertEqual(read(os.path.join(PUBLIC, name)), read(os.path.join(self.tmp, 'web', name)),
                                 f'.website/public/{name} is stale: run scripts/make_icons.sh')

    def test_icns_contents_and_sizes(self):
        elements = icns_elements(read(ICNS))
        self.assertTrue(set(ICNS_PNG) | ICNS_ARGB <= set(elements), sorted(elements))
        for kind, px in ICNS_PNG.items():
            with self.subTest(kind=kind):
                self.assertEqual(png_size(elements[kind]), (px, px))
        for kind in ICNS_ARGB:
            self.assertEqual(elements[kind][:4], b'ARGB', kind)

    def test_small_sizes_come_from_the_small_drawing(self):
        # icon_16x16@2x (ic11, 32 px) is the small drawing at 28 px on a 32 px canvas; 32@2x (ic12,
        # 64 px) and up come from the master.
        inner, canvas = os.path.join(self.tmp, 'inner.png'), os.path.join(self.tmp, 'small-32.png')
        subprocess.run(['sips', '-s', 'format', 'png', '-z', '28', '28', SMALL, '--out', inner], check=True, stdout=subprocess.DEVNULL)
        subprocess.run(['sips', '-p', '32', '32', inner, '--out', canvas], check=True, stdout=subprocess.DEVNULL)
        elements = icns_elements(read(ICNS))
        # iconutil re-encodes the PNG, so compare decoded pixels, not bytes.
        self.assertEqual(png_pixels(elements[b'ic11']), png_pixels(read(canvas)))
        self.assertNotEqual(png_pixels(elements[b'ic12'])[:32], png_pixels(read(canvas)))
        self.assertEqual(png_alpha_bbox(elements[b'ic11'], 128), [2, 2, 29, 29])

    def test_large_sizes_sit_on_apples_grid(self):
        # Apple's macOS template: an 824 px body centred on 1024 px.
        x0, y0, x1, y1 = png_alpha_bbox(icns_elements(read(ICNS))[b'ic10'], 250)
        self.assertTrue(818 <= x1 - x0 + 1 <= 830, (x0, x1))
        self.assertLessEqual(abs((x0 + x1) / 2 - 511.5), 2)
        self.assertLessEqual(abs((y0 + y1) / 2 - 511.5), 2)

    def test_favicon_set_and_touch_icon(self):
        ico = read(os.path.join(PUBLIC, 'favicon.ico'))
        reserved, kind, count = struct.unpack('<HHH', ico[:6])
        self.assertEqual((reserved, kind, count), (0, 1, 3))
        sizes = []
        for i in range(count):
            w, h, _, _, _, _, n, off = struct.unpack('<BBBBHHII', ico[6 + 16 * i:22 + 16 * i])
            self.assertEqual(png_size(ico[off:off + n]), (w, h))
            sizes.append(w)
        self.assertEqual(sizes, [16, 32, 48])
        expected = {'favicon-32.png': 32, 'icon-192.png': 192, 'icon-512.png': 512,
                    'apple-touch-icon.png': 180, 'brand/mark-96.png': 96, 'brand/mark-144.png': 144}
        for name, px in expected.items():
            with self.subTest(name=name):
                self.assertEqual(png_size(read(os.path.join(PUBLIC, name))), (px, px))
        manifest = json.loads(read(os.path.join(PUBLIC, 'site.webmanifest')))
        for icon in manifest['icons']:
            px = int(icon['sizes'].split('x')[0])
            self.assertEqual(png_size(read(os.path.join(PUBLIC, icon['src']))), (px, px))


class DmgBackground(unittest.TestCase):
    def test_render_matches_spec(self):
        node = shutil.which('node')
        if not (sys.platform == 'darwin' and node and os.path.exists(CHROME) and shutil.which('tiffutil')):
            self.skipTest('DMG render check skipped: needs macOS, Node 22+, tiffutil and Google Chrome '
                          f'(set CHROME to its binary; looked for {CHROME})')
        out = tempfile.mkdtemp(prefix='refrozen-dmg-test-')
        try:
            run = subprocess.run([node, os.path.join(ROOT, 'assets', 'dmg', 'render.mjs'), '--out', out],
                                 capture_output=True, text=True, timeout=180)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)  # includes the label contrast gate
            one, two = read(os.path.join(out, 'dmg-background.png')), read(os.path.join(out, 'dmg-background@2x.png'))
            self.assertEqual(png_size(one), (660, 400))
            self.assertEqual(png_dpi(one), (72, 72))
            self.assertEqual(png_size(two), (1320, 800))
            self.assertEqual(png_dpi(two), (144, 144))
            self.assertIn(read(os.path.join(out, 'dmg-background.tiff'))[:2], (b'MM', b'II'))
            self.assertIn('white text', run.stdout)
        finally:
            shutil.rmtree(out, ignore_errors=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
