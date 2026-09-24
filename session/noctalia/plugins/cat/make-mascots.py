#!/usr/bin/python3
"""Maskoti LatteOS pre lištu — vlastná pixel-art (nie prevzatý bongocat), PNG bez závislostí.

  python3 make-mascots.py <výstupný priečinok>

Z ASCII predlôh nižšie vyrobí <maskot>-<snímka>.png (mierka 2). Snímky:
  sedi   obe labky na stole          lapka-l / lapka-p   ťukanie ľavou / pravou (hudba hrá)
  zmurk  zažmúrenie                  spi                 spánok (noc)            hlad    pohladkanie (klik)
  odchod-1..3  maskot odchádza z ostrova (posun doľava)   prazdny  iba stôl (maskot je na prechádzke)
  chapadla-1/2 (iba Ktulu) z hrany stola = lišty vyrastú chápadlá a vlnia sa
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


def png(path, grid, pal):
    w, h = W * SCALE, H * SCALE
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            ch = grid[y // SCALE][x // SCALE]
            if ch == ".":
                raw += b"\x00\x00\x00\x00"
            else:
                raw += bytes.fromhex(pal[ch]) + b"\xff"

    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b""))


def main(out):
    os.makedirs(out, exist_ok=True)
    for kind, pal in PALETTES.items():
        for name, kw in list(FRAMES.items()) + (list(KTULU_ONLY.items()) if kind == "ktulu" else []):
            png(os.path.join(out, "%s-%s.png" % (kind, name)), frame(kind, **kw), pal)
    print("maskoti:", ", ".join(PALETTES), "·", len(FRAMES), "snímok →", out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "mascots")
