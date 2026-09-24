#!/usr/bin/python3
"""Maskoti LatteOS pre lištu — vlastná pixel-art (nie prevzatý bongocat), PNG bez závislostí.

  python3 make-mascots.py <výstupný priečinok>

Z ASCII predlôh nižšie vyrobí <maskot>-<snímka>.png (mierka 2). Snímky:
  sedi   obe labky na stole          lapka-l / lapka-p   ťukanie ľavou / pravou (hudba hrá)
  zmurk  zažmúrenie                  spi                 spánok (noc)            hlad    pohladkanie (klik)
  odchod-1..3  maskot odchádza z ostrova (posun doľava)   prazdny  iba stôl (maskot je na prechádzke)
  chapadla-1/2 (iba Ktulu) z hrany stola = lišty vyrastú chápadlá a vlnia sa
  chodza-1/2, chodza-1-r/2-r  chôdza mimo ostrova (režim WORLD/CHAOS, maskot.qml), doľava / doprava
Kolekcia (25. 9.): Homebrew (kávový sliz pod šálkou), Kávový drak, Líška, Mýval, Mini robot, Svetluška,
Kapybara, Void drak — voľné predlohy 22 × 16 nad stolom (PETS), rovnaké snímky ako mačky.
"""
import os, struct, sys, zlib

SCALE = 2
# paleta: . priehľadné, K obrys, W telo, C akcent (uši, pruhy), P nos/líčka, E oči, D stôl, d hrana stola, Z písmeno z
PALETTES = {
    "macka": {"K": "2A1E16", "W": "F3EBDD", "C": "E4B283", "P": "E07A5F", "E": "2A1E16", "D": "8A5A3C", "d": "6B4430", "Z": "E4B283"},
    "mokka": {"K": "0E0B09", "W": "3A2D24", "C": "E4B283", "P": "E07A5F", "E": "F2C94C", "D": "8A5A3C", "d": "6B4430", "Z": "E4B283"},
    "zrnko": {"K": "2A160C", "W": "7A4A2A", "C": "B07A50", "P": "E07A5F", "E": "F3EBDD", "D": "8A5A3C", "d": "6B4430", "Z": "E4B283"},
    # Ktulu: Cthulhu mačka — morská zeleň, žiariace oči, chápadlá pod bradou (T) a z hrany stola
    "ktulu": {"K": "10201A", "W": "4F8A6E", "C": "2F6450", "P": "8FD3B0", "E": "F2E14C", "D": "8A5A3C", "d": "6B4430", "Z": "8FD3B0", "T": "3E7A5E"},
}

PALETTES.update({
    "homebrew": {"K": "1E120A", "W": "6B3E1F", "C": "D9A066", "P": "E07A5F", "E": "F2C94C", "M": "F3EBDD", "S": "E9DDBE", "D": "8A5A3C", "d": "6B4430", "Z": "E4B283"},
    "drak":     {"K": "1E120A", "W": "8A5A34", "C": "5A3A22", "P": "E07A5F", "E": "F2C94C", "M": "F3EBDD", "D": "8A5A3C", "d": "6B4430", "Z": "E4B283"},
    "liska":    {"K": "2A140A", "W": "E8742E", "C": "F7EBDD", "P": "2A140A", "E": "2A140A", "D": "8A5A3C", "d": "6B4430", "Z": "E4B283"},
    "myval":    {"K": "1A1A1C", "W": "8C8C94", "C": "3A3A40", "P": "E6E1D8", "E": "F3EBDD", "D": "8A5A3C", "d": "6B4430", "Z": "E4B283"},
    "robot":    {"K": "1B1E26", "W": "F09A2A", "C": "1F4E7A", "P": "E0E0E0", "E": "8FE3FF", "D": "8A5A3C", "d": "6B4430", "Z": "8FE3FF"},
    "svetluska": {"K": "1A1608", "W": "FFE46B", "C": "6A5A20", "P": "CFE3F2", "E": "F3EBDD", "D": "8A5A3C", "d": "6B4430", "Z": "FFE46B"},
    "kapybara": {"K": "2A1A10", "W": "A0703E", "C": "6B4A2A", "P": "F2C94C", "E": "1A1008", "D": "8A5A3C", "d": "6B4430", "Z": "E4B283"},
    "void":     {"K": "12081C", "W": "7B3FB8", "C": "3A1A5C", "P": "E07AE0", "E": "FF5CF0", "D": "8A5A3C", "d": "6B4430", "Z": "E07AE0"},
})
NAMES = {"macka": "Latte mačka", "mokka": "Mokka", "zrnko": "Zrnko", "ktulu": "Ktulu", "homebrew": "Homebrew", "drak": "Kávový drak",
         "liska": "Líška", "myval": "Mýval", "robot": "Mini robot", "svetluska": "Svetluška", "kapybara": "Kapybara", "void": "Void drak"}
PETS = {
    "homebrew": ["", "", "........MMMMMM", "......MMMMMMMMMM..MM", ".....MMMMMMMMMMMM.M.M", "....MMKKKKKKKKKKMMM.M",
                 "....MMKWWWWWWWWKMM.MM", "....MKWWCWWWWCWWKM", "....MKWEEWWWWEEWKM...S", "....MKWEEWWWWEEWKM..S",
                 "....KWWWWWWWWWWWWK.S", "...KWWWWWKKKKWWWWWKS", "..KWWWWWWWWWWWWWWWWK", ".KWWCWWWWWWWWWWWCWWWK",
                 "KWWWWWWWKWWWWKWWWWWWWK", ".KK..KKK..KKKK..KK..KK"],
    "drak":     ["....K..........K", "...KCK........KCK", "..KCCK..KKKK..KCCK", ".KCCCK.KWWWWK.KCCCK", ".KCCK.KWWWWWWK.KCCK",
                 "..KK.KWEWWWWEWK.KK", ".....KWEWWWWEWK", ".....KWWWPPWWWK", "......KWWWWWWK", "...MMMMMMMMMMMMMMM",
                 "...MKKKKKKKKKKKKKM.MM", "...MMMMMMMMMMMMMMMM..M", "....MMMMMMMMMMMMMM..M", ".....MMMMMMMMMMMM.MM",
                 "......MMMMMMMMMM", "....KKKKKKKKKKKKKK"],
    "liska":    ["...K..........K", "..KWK........KWK", "..KWWK......KWWK", "..KWWWKKKKKKWWWK", ".KWWWWWWWWWWWWWWK",
                 ".KWWEWWWWWWWWEWWK", ".KWCEWWWWWWWWECWK", "..KCCCWWKKWWCCCK", "...KCCCCCCCCCCK", "....KWWWWWWWWK...KKK",
                 "...KWWCCCCCCWWK.KWWWK", "...KWWCCCCCCWWKKWWWWK", "...KWWCCCCCCWWWWWCCK", "...KWWWWWWWWWWWCCK",
                 "...KWK.KWWK.KWKKK", "...KK..KKK..KK"],
    "myval":    ["...KK........KK", "..KWWK......KWWK", "..KWWWKKKKKKWWWK", ".KWWWWWWWWWWWWWWK", ".KCCCCWWWWWWCCCCK",
                 ".KCCECCWWWWCCECCK", ".KCCCCPWWWWPCCCCK", "..KPPPPPKKPPPPPK", "...KPPPPPPPPPPK", "....KWWWWWWWWK",
                 "...KWWWPPPPWWWK.KCCK", "...KWWPPPPPPWWKKWWWK", "...KWWPPPPPPWWKCCCK", "...KWWWWWWWWWWWWWK",
                 "...KWK.KWWK.KWK", "...KK..KKK..KK"],
    "robot":    [".........K", ".........P", "......KKKKKKKK", ".....KWWWWWWWWK", "....KWCCCCCCCCWK", "....KWCEECCEECWK",
                 "....KWCEECCEECWK", "....KWCCCCCCCCWK", "....KWWWWWWWWWWK", ".....KKKKKKKKKK", "...KKWWWWWWWWWWKK",
                 "..KWKWWPWWWWPWWKWK", "..KWKWWWWWWWWWWKWK", "...K.KWWWWWWWWK.K", ".....KWK....KWK", ".....KKK....KKK"],
    "svetluska": ["", ".....KK......KK", "....KPPK....KPPK", "...KPPPPK..KPPPPK", "...KPPPPPKKPPPPPK", "....KPPPKCCKPPPK",
                  ".....KKKCCCCKKK", "......KCECCECK", "......KCECCECK", ".......KCCCCK", "......KWWWWWWK", ".....KWWWWWWWWK",
                  ".....KWWWWWWWWK", "......KWWWWWWK", ".......KKKKKK", ""],
    "kapybara": ["........KK", ".......KPPK", ".......KPPPK", "...KK...KKK..KK", "..KWWKKKKKKKKWWK", "..KWWWWWWWWWWWWWK",
                 ".KWWWWWWWWWWWWWWWK", ".KWWEWWWWWWWWEWWWWK", ".KWWWWWWWWWWWWWWWCCK", ".KWWWWWWWWWWWWWWCKKCK",
                 ".KWWWWWWWWWWWWWWWCCCK", "..KWWWWWWWWWWWWWWWWK", "..KWWWWWWWWWWWWWWWWK", "..KWWWWWWWWWWWWWWWWK",
                 "..KWWK.KWWK..KWWK.KWK", "..KKK..KKK...KKK..KK"],
    "void":     ["..K...............K", ".KCK.............KCK", ".KCCK...KKKKK...KCCK", "..KCCK.KWWWWWK.KCCK", "..KCCCKWWWWWWWKCCCK",
                 "...KCKWEWWWWWEWKCK", "....KWWEWWWWWEWWK", "....KWWWWPPWWWWWK", ".....KWWWWWWWWWK", "......KWWWWWWWK",
                 ".....KWWCCCCCWWK", "....KWWCCCCCCCWWK.KK", "....KWWCCCCCCCWWKKWK", "....KWWWWWWWWWWWWWK",
                 "....KWWK.KWK.KWWK", "....KKK..KKK..KKK"],
}


def pet_frame(kind, eyes="open", z=False, bounce=0, shift=0, empty=False, desk=True, step=0):
    """Snímka voľnej predlohy: 16 riadkov postavy nad stolom (2 riadky); bez stola pre chôdzu."""
    g = [["." for _ in range(W)] for _ in range(H)]
    rows = [(r + "." * W)[:W] for r in (PETS[kind] + [""] * 16)[:16]]
    off = 2 if not desk else 0                     # bez stola postava stojí na spodku plátna
    for y, row in enumerate(rows):
        yy = y + off - bounce
        if 0 <= yy < H:
            for x, ch in enumerate(row):
                if ch != ".":
                    g[yy][x] = ch
    eyes_at = [(x, y) for y in range(H) for x in range(W) if g[y][x] == "E"]
    if eyes != "open" and eyes_at:
        for x, y in eyes_at:
            g[y][x] = g[y][x - 1] if x > 0 and g[y][x - 1] not in ("E", ".") else "W"
        low = max(y for _, y in eyes_at)
        for x in sorted({x for x, _ in eyes_at}):
            g[low][x] = "K"
        if eyes == "happy":                        # ^ ^
            top_ = min(y for _, y in eyes_at)
            for x in sorted({x for x, _ in eyes_at}):
                g[top_][x] = "K"; g[low][x] = g[low][x - 1] if x > 0 else "W"
    if step and not desk:                          # chôdza: striedanie nôh (spodný riadok posunúť)
        last = g[H - 1][:]
        g[H - 1] = (["."] + last[:-1]) if step == 1 else (last[1:] + ["."])
    if z:
        for (x, y) in [(18, 0), (19, 0), (20, 0), (21, 0), (20, 1), (19, 2), (18, 3), (19, 3), (20, 3), (21, 3)]:
            g[y][x] = "Z"
    if desk:
        for i, row in enumerate(DESK):
            g[H - 2 + i] = list(row)
    if shift or empty:
        body = [row[:] for row in g[:H - 2]]
        for y in range(H - 2):
            for x in range(W):
                sx = x + shift
                g[y][x] = "." if empty or sx >= W else body[y][sx]
    return g


PET_FRAMES = {
    "sedi": dict(), "lapka-l": dict(bounce=1), "lapka-p": dict(), "zmurk": dict(eyes="closed"),
    "spi": dict(eyes="closed", z=True), "hlad": dict(eyes="happy", bounce=1), "smutny": dict(eyes="closed", bounce=-1),
    "odchod-1": dict(shift=6), "odchod-2": dict(shift=12), "odchod-3": dict(shift=18), "prazdny": dict(empty=True),
    "chodza-1": dict(desk=False, step=1), "chodza-2": dict(desk=False, step=2, bounce=1),
    "stoji": dict(desk=False), "spi-von": dict(desk=False, eyes="closed", z=True), "hlad-von": dict(desk=False, eyes="happy", bounce=1),
}


def mirror(g):
    return [row[::-1] for row in g]


def walk_cat(g):
    """Mačky (hlava + labky za stolom) mimo ostrova: stôl nahradia nôžky."""
    g = [row[:] for row in g]
    g[H - 2] = list("....KWWK......KWWK....")
    g[H - 1] = list("....KKKK......KKKK....")
    return g


HEADS = {
    # 22 × 10; hlava mačky (uši, oči E, nos P, ústa K)
    "macka": [
        "....K..........K......",
        "...KCK........KCK.....",
        "...KCWK......KWCK.....",
        "...KWWWKKKKKKWWWK.....",
        "..KWWWEWWWWWWEWWWK....",
        "..KWWWEWWWWWWEWWWK....",
        "..KWWPWWWPPWWWPWWK....",
        "..KWWWWWKWWKWWWWWK....",
        "..KWWWWWWWWWWWWWWK....",
        "...KKKKKKKKKKKKKK.....",
    ],
    # kávové zrnko s ryhou uprostred a malými rožkami
    "zrnko": [
        "......K........K......",
        ".....KCK......KCK.....",
        "......KKKKKKKKKK......",
        "....KKWWWWCWWWWWKK....",
        "...KWWWWWWCWWWWWWWK...",
        "...KWWEEWWCWWEEWWWK...",
        "...KWWEEWWCWWEEWWWK...",
        "...KWWWWWCWWWWWWWWK...",
        "....KKWWWCKKWWWWKK....",
        "......KKKKKKKKKK......",
    ],
}
HEADS["mokka"] = HEADS["macka"]
HEADS["ktulu"] = [
    "....K..........K......",
    "...KCK........KCK.....",
    "...KCWK......KWCK.....",
    "...KWWWKKKKKKWWWK.....",
    "..KWWWEWWWWWWEWWWK....",
    "..KWWWEWWWWWWEWWWK....",
    "..KWWWWWWPPWWWWWWK....",
    "..KWWTWWTWWTWWTWWK....",
    "..KWWTWWTWWTWWTWWK....",
    "...KKTKKTKKTKKTKKK....",
]
DESK = ["dddddddddddddddddddddd", "DDDDDDDDDDDDDDDDDDDDDD"]
PAW = ["KKKK", "KWWK", "KPPK"]      # labka s ružovými vankúšikmi (viditeľná aj na tmavej mačke)
W, H = 22, 18          # plátno: hlava (10), trup za stolom, labky, stôl (2)


def frame(kind, left_up, right_up, eyes="open", z=False, shift=0, empty=False, rise=0):
    g = [["." for _ in range(W)] for _ in range(H)]
    head = HEADS[kind]
    top = 1
    # trup za stolom (medzi bradou a stolom), labky ležia navrch
    for y in range(top + len(head) - 1, H - 2):
        for x in range(4, 17):
            g[y][x] = "K" if x in (4, 16) else "W"
    eyes_at = []
    for y, row in enumerate(head):
        for x, ch in enumerate(row):
            if ch != ".":
                if ch == "E":
                    eyes_at.append((x, y))
                    if eyes == "closed":
                        ch = "W"
                g[top + y][x] = ch
    if eyes == "closed":                          # zatvorené oči: vodorovná čiarka pod okom
        low = max(y for _, y in eyes_at)
        for x in sorted({x for x, _ in eyes_at}):
            for dx in (-1, 0, 1):
                if g[top + low][x + dx] == "W":
                    g[top + low][x + dx] = "K"
    if kind == "ktulu":                            # chápadlá pod bradou visia až na stôl (vlnka)
        for i, x0 in enumerate((5, 8, 11, 14)):
            for y in range(top + len(head), H - 2):
                x = x0 + (1 if (y + i) % 3 == 0 else 0)
                g[y][x] = "T"
                if y == H - 3:
                    g[y][x + 1] = "T"               # koniec chápadla sa stáča po stole
    for i, row in enumerate(DESK):
        g[H - 2 + i] = list(row)

    def paw(x0, up):
        y0 = (top + len(head) - 1) if up else (H - 5)     # hore: tesne pod bradou, dole: na stole
        for dy, row in enumerate(PAW):
            for dx, ch in enumerate(row):
                g[y0 + dy][x0 + dx] = ch
    paw(3, left_up)
    paw(14, right_up)
    if z:
        for (x, y) in [(18, 0), (19, 0), (20, 0), (21, 0), (20, 1), (19, 2), (18, 3), (19, 3), (20, 3), (21, 3)]:   # „z“ nad uchom
            g[y][x] = "Z"
    if rise:                                      # chápadlá vyrastajú z hrany stola (lišty) po stranách
        for side, x0 in ((0, 0), (1, 20)):
            for k in range(8):
                y = H - 3 - k
                wig = (1 if ((k + rise + side) % 4) < 2 else 0)
                x = x0 + (wig if side == 0 else -wig)
                g[y][x] = "T"; g[y][x + 1] = "T" if k < 6 else g[y][x + 1]
            g[H - 3 - 8][x0 + (1 if side == 0 else 0)] = "P"   # prísavka na špičke
    if shift or empty:                            # maskot odchádza: posun postavy doľava, stôl ostáva
        body = [row[:] for row in g[:H - 2]]
        for y in range(H - 2):
            for x in range(W):
                sx = x + shift
                g[y][x] = "." if empty or sx >= W else body[y][sx]
    return g


FRAMES = {
    "sedi":    dict(left_up=False, right_up=False),
    "lapka-l": dict(left_up=True, right_up=False),
    "lapka-p": dict(left_up=False, right_up=True),
    "zmurk":   dict(left_up=False, right_up=False, eyes="closed"),
    "spi":     dict(left_up=False, right_up=False, eyes="closed", z=True),
    "hlad":    dict(left_up=True, right_up=True, eyes="closed"),
    "odchod-1": dict(left_up=True, right_up=False, shift=6),
    "odchod-2": dict(left_up=False, right_up=True, shift=12),
    "odchod-3": dict(left_up=True, right_up=False, shift=18),
    "prazdny":  dict(left_up=False, right_up=False, empty=True),
}
KTULU_ONLY = {
    "chapadla-1": dict(left_up=False, right_up=False, rise=1),
    "chapadla-2": dict(left_up=False, right_up=False, rise=3),
}


def shade(hexc, f):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (0, 2, 4))
    if f >= 1:
        r, g, b = (int(c + (255 - c) * (f - 1)) for c in (r, g, b))
    else:
        r, g, b = (int(c * f) for c in (r, g, b))
    return bytes((r, g, b))


def scale2x(grid):
    """EPX/scale2x: zväčšenie na dvojnásobok so zaoblenými šikminami (podrobnejší obrys než kocky)."""
    h, w = len(grid), len(grid[0])
    out = [["."] * (w * 2) for _ in range(h * 2)]
    at = lambda y, x: grid[y][x] if 0 <= y < h and 0 <= x < w else "."
    for y in range(h):
        for x in range(w):
            p = grid[y][x]
            a, b, c, d = at(y - 1, x), at(y, x + 1), at(y, x - 1), at(y + 1, x)
            e = [p, p, p, p]
            if c == a and c != d and a != b: e[0] = a
            if a == b and a != c and b != d: e[1] = b
            if d == c and d != b and c != a: e[2] = c
            if b == d and b != a and d != c: e[3] = d
            out[2 * y][2 * x], out[2 * y][2 * x + 1], out[2 * y + 1][2 * x], out[2 * y + 1][2 * x + 1] = e
    return out


def png(path, grid, pal):
    """Pixel-art s tieňovaním: horná hrana farby svetlejšia, spodná tmavšia (objem), obrys K ostáva; potom scale2x."""
    g = scale2x(grid) if SCALE == 2 else grid
    h, w = len(g), len(g[0])
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            ch = g[y][x]
            if ch == ".":
                raw += b"\x00\x00\x00\x00"
                continue
            base = pal[ch]
            if ch in ("K", "E", "Z", "d"):
                raw += bytes.fromhex(base) + b"\xff"
                continue
            up = g[y - 1][x] if y > 0 else "."
            up2 = g[y - 2][x] if y > 1 else "."
            dn = g[y + 1][x] if y + 1 < h else "."
            dn2 = g[y + 2][x] if y + 2 < h else "."
            lf = g[y][x - 1] if x > 0 else "."
            if up != ch and up2 != ch:
                c = shade(base, 1.28)                 # odlesk na hornej hrane
            elif up != ch or lf != ch and lf in (".", "K"):
                c = shade(base, 1.12)
            elif dn != ch or dn2 != ch:
                c = shade(base, 0.78)                 # tieň pri spodku
            else:
                c = bytes.fromhex(base)
            raw += c + b"\xff"

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def main(out):
    os.makedirs(out, exist_ok=True)
    n = 0
    for kind, pal in PALETTES.items():
        if kind in PETS:
            frames = {name: pet_frame(kind, **kw) for name, kw in PET_FRAMES.items()}
        else:
            frames = {name: frame(kind, **kw) for name, kw in list(FRAMES.items()) + (list(KTULU_ONLY.items()) if kind == "ktulu" else [])}
            frames["smutny"] = frame(kind, left_up=False, right_up=False, eyes="closed")
            base = frame(kind, left_up=False, right_up=False)
            frames["stoji"] = walk_cat(base)
            frames["chodza-1"] = walk_cat(frame(kind, left_up=True, right_up=False))
            frames["chodza-2"] = walk_cat(frame(kind, left_up=False, right_up=True))
            frames["spi-von"] = walk_cat(frame(kind, left_up=False, right_up=False, eyes="closed", z=True))
            frames["hlad-von"] = walk_cat(frame(kind, left_up=True, right_up=True, eyes="closed"))
        for name in ("chodza-1", "chodza-2", "stoji"):
            frames[name + "-r"] = mirror(frames[name])
        for name, g in frames.items():
            png(os.path.join(out, "%s-%s.png" % (kind, name)), g, pal); n += 1
    with open(os.path.join(out, "mena.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join("%s=%s" % kv for kv in NAMES.items()) + "\n")
    print("maskoti:", ", ".join(PALETTES), "·", n, "snímok →", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mascots")
