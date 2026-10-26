#!/usr/bin/env python3
"""The reFrozen dmg: reFrozen.app, an Applications shortcut and the Finder
window of assets/dmg (the Icegate background, 660 x 400 points, the two icons
at 128 points with their label plates).

  /usr/bin/python3 -I scripts/release/make_dmg.py <repo> <reFrozen.app> <out.dmg>

The window lives in the volume's .DS_Store, written with ds_store and
mac_alias (pinned by hash, from DMG_PYTHON, never shipped) on the read-write
image mounted at /Volumes/reFrozen, where players' Macs mount it: the
background's alias records the volume, its mount path and the file's ID, so
it must not name the build machine (game-port-knowledge,
general/macos-dmg-finder-layout.md). The dmg is then compressed and checked
read-only: its contents, the app's signature, and no build path in the
.DS_Store.
"""
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile

REPO, APP, DMG = sys.argv[1:4]
DMG_PYTHON = os.environ.get("DMG_PYTHON", os.path.expanduser("~/rf-release/dmg-python"))
VOLUME = "reFrozen"
MOUNT = f"/Volumes/{VOLUME}"
WINDOW, TITLE_BAR, ORIGIN = (660, 400), 32, (200, 120)
ICON_SIZE = 128
ICONS = {"reFrozen.app": (185, 250), "Applications": (475, 250)}
BACKGROUND = ".background/background.tiff"


def run(*cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        raise SystemExit(f"make_dmg: {' '.join(cmd)} failed: {r.stderr.strip()[:500]}")
    return r.stdout


def finder_layout(volume):
    sys.path.insert(0, DMG_PYTHON)
    import ds_store
    import mac_alias
    background = os.path.join(volume, BACKGROUND)
    (x, y), (w, h) = ORIGIN, (WINDOW[0], WINDOW[1] + TITLE_BAR)
    with ds_store.DSStore.open(os.path.join(volume, ".DS_Store"), "w+") as d:
        d["."]["vSrn"] = ("long", 1)
        d["."]["icvl"] = ("type", b"icnv")
        d["."]["vstl"] = ("type", b"icnv")
        d["."]["bwsp"] = {
            "WindowBounds": f"{{{{{x}, {y}}}, {{{w}, {h}}}}}", "ShowToolbar": False, "ShowSidebar": False,
            "ContainerShowSidebar": False, "ShowPathbar": False, "ShowStatusBar": False, "ShowTabView": False,
            "PreviewPaneVisibility": False, "SidebarWidth": 0,
        }
        d["."]["icvp"] = {
            "viewOptionsVersion": 1, "backgroundType": 2,
            "backgroundImageAlias": mac_alias.Alias.for_file(background).to_bytes(),
            "backgroundColorRed": 0.02, "backgroundColorGreen": 0.031, "backgroundColorBlue": 0.055,  # abyss #05080e
            "iconSize": float(ICON_SIZE), "textSize": 13.0, "labelOnBottom": True, "arrangeBy": "none",
            "gridSpacing": 100.0, "gridOffsetX": 0.0, "gridOffsetY": 0.0, "showIconPreview": False,
            "showItemInfo": False, "scrollPositionX": 0.0, "scrollPositionY": 0.0,
        }
        d["."]["pBBk"] = mac_alias.Bookmark.for_file(background)
        for name, position in ICONS.items():
            d[name]["Iloc"] = position


def main():
    if os.path.exists(MOUNT):
        raise SystemExit(f"make_dmg: {MOUNT} is in use (the layout must be written where players mount the dmg)")
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "art")
        run("/opt/homebrew/bin/node", os.path.join(REPO, "assets", "dmg", "render.mjs"), "--out", art)
        stage = os.path.join(tmp, "stage")
        os.makedirs(os.path.join(stage, ".background"))
        run("ditto", APP, os.path.join(stage, "reFrozen.app"))
        os.symlink("/Applications", os.path.join(stage, "Applications"))
        shutil.copy(os.path.join(art, "dmg-background.tiff"), os.path.join(stage, BACKGROUND))
        rw = os.path.join(tmp, "rw.dmg")
        run("hdiutil", "create", "-quiet", "-volname", VOLUME, "-srcfolder", stage, "-fs", "HFS+", "-format", "UDRW",
            "-ov", rw)
        info = plistlib.loads(run("hdiutil", "attach", "-plist", "-nobrowse", "-noautoopen", rw).encode())
        mnt = next(e["mount-point"] for e in info["system-entities"] if e.get("mount-point"))
        try:
            if mnt != MOUNT:
                raise SystemExit(f"make_dmg: mounted at {mnt}, not {MOUNT}")
            finder_layout(mnt)
            shutil.rmtree(os.path.join(mnt, ".fseventsd"), ignore_errors=True)
        finally:
            run("hdiutil", "detach", "-quiet", mnt)
        if os.path.exists(DMG):
            os.remove(DMG)
        run("hdiutil", "convert", "-quiet", rw, "-format", "UDZO", "-imagekey", "zlib-level=9", "-o", DMG)

        # Read back: contents, signature, layout without build paths.
        check = os.path.join(tmp, "check")
        os.makedirs(check)
        run("hdiutil", "attach", "-quiet", "-readonly", "-nobrowse", "-noautoopen", "-mountpoint", check, DMG)
        try:
            top = sorted(n for n in os.listdir(check) if n not in (".fseventsd", ".Trashes"))
            want = sorted([".DS_Store", ".background", "Applications", "reFrozen.app"])
            assert top == want, f"dmg holds {top}, not {want}"
            assert os.readlink(os.path.join(check, "Applications")) == "/Applications"
            run("codesign", "--verify", "--deep", "--strict", os.path.join(check, "reFrozen.app"))
            raw = open(os.path.join(check, ".DS_Store"), "rb").read()
            for p in ("/private/", "/var/folders/", "/tmp/", "/Users/"):
                assert p.encode() not in raw and p.encode("utf-16-be") not in raw, f".DS_Store names {p}"
            assert MOUNT.encode() in raw or MOUNT.encode("utf-16-be") in raw, ".DS_Store does not name /Volumes/reFrozen"
        finally:
            run("hdiutil", "detach", "-quiet", check)
    print(f"dmg: {DMG} ({os.path.getsize(DMG) >> 20} MB): app, Applications, Finder layout; read back ok")


if __name__ == "__main__":
    main()
