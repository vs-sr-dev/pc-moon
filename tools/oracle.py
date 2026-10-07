"""Moon in melonDS, driven from here: the oracle for what the port shows and does.

    python tools/oracle.py [--at SECONDS:WHAT,...] [--out DIR] [--quit SECONDS] [--fresh]
    python tools/oracle.py --peek STATE.ml1 ADDR:LEN [ADDR:LEN ...]

Boots the cartridge (the .nds in the repository's root or in rom/) in a
copy of melonDS kept for this (ORACLE_DIR, with its own melonDS.toml: no
DLDI card, the keys mapped; its save and state paths are pointed at DIR
before every launch) and, at each time given (seconds since the launch,
wall clock), does WHAT:

    shot                 the window's two screens, saved as DIR/t<SECONDS>.png
    state                a savestate (melonDS's Shift+F1), kept as DIR/t<SECONDS>.ml1
    peek:ADDR:LEN        a savestate, then LEN bytes at ADDR (hex) printed from it
    START / A+B / ...    press these buttons for 0.15 s (DS names: A B X Y L R
                         START SELECT UP DOWN LEFT RIGHT), through the keyboard
    tap:X:Y              touch the lower screen at (X, Y) in its 256x192 pixels
    drag:X0:Y0:X1:Y1     the stylus slid on the lower screen from one point to the other (0.5 s)
    frames:N[:BUTTONS]   pause, hold BUTTONS (and DRAG: the stylus sliding on the
                         lower screen), step N frames, a picture after each
                         (DIR/t<SECONDS>_fNN.png), and print how many pixels of
                         the upper screen changed at each step
    framesv:N[:BUTTONS]  the same, with a savestate after each step to read the
                         SDK's VBlank count (0x027FFC3C) of every picture

The game's memory is read from melonDS's savestates (`State`): the whole
machine at that moment, in sections. Checked on this build: main RAM is
the "NDSG" section's data from 0x14 on (the file's offset 0x24), the ITCM
the "CP15" section's from 0x1C on, the DTCM right after it. melonDS's GDB
stub would be the live alternative, but on this build (Windows, 2025-11)
it drops the connection at the first packet.

The game's own save (its backup memory) is DIR/<rom>.sav and lasts from
run to run; --fresh deletes it first, for a run from a new cartridge.

Keys and taps go to the melonDS window as the user's own input would
(SendInput, the window brought to the front first), so do not type into
other windows while a run is going. The times are wall-clock times, so two
runs differ by a few frames.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import glob
import os
import re
import shutil
import struct
import subprocess
import sys
import time

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
ORACLE_DIR = r"D:\Tools\melonDS-oracle"

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

VK = {"A": 0x58, "B": 0x5A, "X": 0x53, "Y": 0x41, "L": 0x51, "R": 0x57, "START": 0x0D,
      "SELECT": 0x08, "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28}
VK_SHIFT, VK_F1, VK_P, VK_N = 0x10, 0x70, 0x50, 0x4E


def find_rom():
    for pat in ("*.nds", "rom/*.nds"):
        hits = sorted(glob.glob(os.path.join(ROOT, pat)))
        if hits:
            return hits[0]
    sys.exit("no .nds in the repository root or in rom/")


class State:
    """A melonDS savestate: its sections, and the ARM9's memory read from them."""

    def __init__(self, path):
        with open(path, "rb") as f:
            self.data = f.read()
        if self.data[:4] != b"MELN":
            raise ValueError("not a melonDS savestate")
        self.sections = {}
        i = 0x10
        while i + 16 <= len(self.data):
            magic, length = self.data[i:i + 4].decode("latin1"), struct.unpack_from("<I", self.data, i + 4)[0]
            if length < 16:
                break
            self.sections[magic] = (i, length)
            i += length
        g = self.sections["NDSG"][0] + 0x14
        c = self.sections["CP15"][0] + 0x1C
        self.main = self.data[g:g + 0x400000]
        self.itcm = self.data[c:c + 0x8000]
        self.dtcm = self.data[c + 0x8000:c + 0xC000]

    def read(self, addr, n, dtcm_base=0x027E0000):
        if dtcm_base <= addr < dtcm_base + 0x4000:
            return self.dtcm[addr - dtcm_base:addr - dtcm_base + n]
        if 0x02000000 <= addr < 0x03000000:
            o = addr & 0x3FFFFF
            return self.main[o:o + n]
        if addr < 0x02000000:
            o = addr & 0x7FFF
            return self.itcm[o:o + n]
        raise ValueError("%08X: not in main RAM, ITCM or DTCM" % addr)

    def u32(self, addr):
        return struct.unpack("<I", self.read(addr, 4))[0]


def prepare(out, rom, fresh):
    """Point the oracle's melonDS at DIR for the game's save and the states."""
    cfg = os.path.join(ORACLE_DIR, "melonDS.toml")
    with open(cfg, encoding="utf-8") as f:
        t = f.read()
    fwd = out.replace("\\", "/")
    t = re.sub(r'(?m)^SaveFilePath = ".*"$', 'SaveFilePath = "%s"' % fwd, t, count=1)
    t = re.sub(r'(?m)^SavestatePath = ".*"$', 'SavestatePath = "%s"' % fwd, t, count=1)
    with open(cfg, "w", encoding="utf-8") as f:
        f.write(t)
    base = os.path.splitext(os.path.basename(rom))[0]
    if fresh and os.path.exists(os.path.join(out, base + ".sav")):
        os.remove(os.path.join(out, base + ".sav"))
    return os.path.join(out, base + ".ml1")


def windows_of(pid):
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd):
            r = wt.RECT()
            user32.GetClientRect(hwnd, ctypes.byref(r))
            found.append((r.right * r.bottom, hwnd))
        return True
    user32.EnumWindows(cb, 0)
    return [h for _, h in sorted(found, reverse=True)]


def client_box(hwnd):
    r = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, pt.x + r.right, pt.y + r.bottom


def screens(hwnd):
    """(x, y, scale, client image): the top screen inside the client area, the bottom one under it.

    melonDS's default layout: the two screens stacked, no gap, scaled to fit
    the panel under the menu bar and centred. A window at its own size is the
    menu bar over exactly 2:3 of screens; otherwise the panel is taken to
    start at the first row whose leftmost pixel is black.
    """
    from PIL import ImageGrab
    x0, y0, x1, y1 = client_box(hwnd)
    img = ImageGrab.grab((x0, y0, x1, y1), all_screens=True).convert("RGB")
    w, h = img.size
    if 0 < h - 1.5 * w < 80:
        top = h - round(1.5 * w)
    else:
        top = next((y for y in range(h) if img.getpixel((0, y)) == (0, 0, 0)), 0)
    ph = h - top
    s = min(w / 256, ph / 384)
    return (w - 256 * s) / 2, top + (ph - 384 * s) / 2, s, img


def shot(hwnd, path):
    ox, oy, s, img = screens(hwnd)
    img.crop((round(ox), round(oy), round(ox + 256 * s), round(oy + 384 * s))).save(path)


class INPUT(ctypes.Structure):
    class _U(ctypes.Union):
        class KI(ctypes.Structure):
            _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                        ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]

        class MI(ctypes.Structure):
            _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                        ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ctypes.c_size_t)]
        _fields_ = [("ki", KI), ("mi", MI)]
    _fields_ = [("type", wt.DWORD), ("u", _U)]


def _send(*inputs):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


def _key(vk, up):
    i = INPUT(type=1)
    i.u.ki.wVk = vk
    i.u.ki.wScan = user32.MapVirtualKeyW(vk, 0)
    i.u.ki.dwFlags = (2 if up else 0) | (1 if vk in (0x25, 0x26, 0x27, 0x28) else 0)
    return i


def keys(hwnd, vks, hold=0.15):
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.05)
    _send(*[_key(v, False) for v in vks])
    time.sleep(hold)
    _send(*[_key(v, True) for v in reversed(vks)])


def tap(hwnd, x, y, hold=0.15):
    ox, oy, s, _ = screens(hwnd)
    cx, cy, _, _ = client_box(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetCursorPos(int(cx + ox + (x + 0.5) * s), int(cy + oy + (192 + y + 0.5) * s))
    time.sleep(0.05)
    for flag in (0x0002, 0x0004):          # left down, left up
        m = INPUT(type=0)
        m.u.mi.dwFlags = flag
        _send(m)
        time.sleep(hold if flag == 0x0002 else 0)


def drag(hwnd, x0, y0, x1, y1, seconds=0.5):
    """The stylus down at (x0, y0) on the lower screen, slid to (x1, y1), lifted."""
    ox, oy, s, _ = screens(hwnd)
    cx, cy, _, _ = client_box(hwnd)

    def at(x, y):
        user32.SetCursorPos(int(cx + ox + (x + 0.5) * s), int(cy + oy + (192 + y + 0.5) * s))
    user32.SetForegroundWindow(hwnd)
    at(x0, y0)
    time.sleep(0.05)
    m = INPUT(type=0)
    m.u.mi.dwFlags = 0x0002
    _send(m)
    steps = max(1, int(seconds / 0.02))
    for k in range(1, steps + 1):
        at(x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps)
        time.sleep(seconds / steps)
    m = INPUT(type=0)
    m.u.mi.dwFlags = 0x0004
    _send(m)


def frames(hwnd, n, held, out, tag, slot=None):
    """Pause, hold `held` (DS buttons, and DRAG: the stylus sliding right on the
    lower screen), step n frames with a screenshot after each, let go, resume.
    melonDS's pause and frame step are P and N in the oracle's settings."""
    keys(hwnd, [VK_P], hold=0.05)
    time.sleep(0.2)
    vks = [VK[b] for b in held if b in VK]
    drag = "DRAG" in held
    _send(*[_key(v, False) for v in vks])
    ox, oy, s, _ = screens(hwnd)
    cx, cy, _, _ = client_box(hwnd)
    x0, y0 = cx + ox + 64 * s, cy + oy + (192 + 96) * s
    if drag:
        user32.SetCursorPos(int(x0), int(y0))
        m = INPUT(type=0)
        m.u.mi.dwFlags = 0x0002
        _send(m)
    paths = []
    vbl = []
    for i in range(n):
        if drag:
            user32.SetCursorPos(int(x0 + (i + 1) * 3 * s), int(y0))
        time.sleep(0.05)
        keys(hwnd, [VK_N], hold=0.03)
        time.sleep(0.15)
        p = os.path.join(out, "%s_f%02d.png" % (tag, i))
        shot(hwnd, p)
        paths.append(p)
        if slot:                                # the VBlank count of this picture
            st = save_state(hwnd, slot, os.path.join(out, "step.ml1"))
            vbl.append(State(st).u32(0x027FFC3C) if st else None)
    if drag:
        m = INPUT(type=0)
        m.u.mi.dwFlags = 0x0004
        _send(m)
    _send(*[_key(v, True) for v in reversed(vks)])
    keys(hwnd, [VK_P], hold=0.05)
    return paths, vbl


def changes(paths):
    """For consecutive pictures: how many pixels of the upper screen differ."""
    from PIL import Image, ImageChops
    out = []
    prev = None
    for p in paths:
        im = Image.open(p).convert("RGB")
        w, h = im.size
        top = im.crop((0, 0, w, h // 2))
        if prev is not None:
            diff = ImageChops.difference(top, prev).convert("L").point(lambda v: 255 if v > 8 else 0)
            out.append(sum(1 for v in diff.getdata() if v))
        prev = top
    return out


def save_state(hwnd, slot_path, dest):
    """melonDS's Shift+F1, then the slot's file moved to dest once it is complete."""
    if os.path.exists(slot_path):
        os.remove(slot_path)
    keys(hwnd, [VK_SHIFT, VK_F1], hold=0.1)
    last = -1
    for _ in range(100):
        time.sleep(0.1)
        if os.path.exists(slot_path):
            n = os.path.getsize(slot_path)
            if n == last and n > 0:
                shutil.move(slot_path, dest)
                return dest
            last = n
    return None


def launch(rom):
    proc = subprocess.Popen([os.path.join(ORACLE_DIR, "melonDS.exe"), rom], cwd=ORACLE_DIR)
    for _ in range(100):
        time.sleep(0.1)
        w = windows_of(proc.pid)
        if w:
            return proc, w[0]
    proc.kill()
    sys.exit("melonDS did not open a window")


def peek(state, spec):
    addr, n = (int(x, 16) for x in spec.split(":"))
    return "%08X: %s" % (addr, state.read(addr, n).hex())


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--at", default="", help="SECONDS:WHAT,... (see the docstring)")
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "oracle"))
    ap.add_argument("--quit", type=float, default=None, help="quit at this time (default: after the last event)")
    ap.add_argument("--fresh", action="store_true", help="delete the game's save first")
    ap.add_argument("--peek", nargs="+", metavar=("STATE", "ADDR:LEN"), help="read a saved state, no run")
    a = ap.parse_args(argv)
    if a.peek:
        st = State(a.peek[0])
        for spec in a.peek[1:]:
            print(peek(st, spec))
        return
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    rom = find_rom()
    slot = prepare(out, rom, a.fresh)
    events = sorted((float(t), w) for t, w in (item.split(":", 1) for item in filter(None, a.at.split(","))))
    proc, hwnd = launch(rom)
    t0 = time.time()
    try:
        for t, what in events:
            time.sleep(max(0.0, t0 + t - time.time()))
            hwnd = (windows_of(proc.pid) or [hwnd])[0]
            if what == "shot":
                path = os.path.join(out, "t%g.png" % t)
                shot(hwnd, path)
                print("%6.1f shot %s" % (t, path))
            elif what == "state" or what.startswith("peek:"):
                dest = save_state(hwnd, slot, os.path.join(out, "t%g.ml1" % t))
                if not dest:
                    print("%6.1f no state written" % t)
                elif what == "state":
                    print("%6.1f state %s" % (t, dest))
                else:
                    print("%6.1f peek %s" % (t, peek(State(dest), what[5:])))
            elif what.startswith("frames:") or what.startswith("framesv:"):
                parts = what.split(":")
                held = parts[2].upper().split("+") if len(parts) > 2 and parts[2] else []
                paths, vbl = frames(hwnd, int(parts[1]), held, out, "t%g" % t,
                                    slot if what.startswith("framesv:") else None)
                print("%6.1f frames %s: upper-screen pixels changed per step %s" % (t, what, changes(paths)))
                if vbl:
                    print("       VBlank count at each picture %s" % vbl)
            elif what.startswith("drag:"):
                x0, y0, x1, y1 = (int(v) for v in what.split(":")[1:5])
                drag(hwnd, x0, y0, x1, y1)
                print("%6.1f drag %d,%d -> %d,%d" % (t, x0, y0, x1, y1))
            elif what.startswith("tap:"):
                _, x, y = what.split(":")
                tap(hwnd, int(x), int(y))
                print("%6.1f tap %s,%s" % (t, x, y))
            else:
                keys(hwnd, [VK[b] for b in what.upper().split("+")])
                print("%6.1f press %s" % (t, what))
        end = a.quit if a.quit is not None else (events[-1][0] + 1 if events else 10)
        time.sleep(max(0.0, t0 + end - time.time()))
    finally:
        proc.terminate()


if __name__ == "__main__":
    main()
