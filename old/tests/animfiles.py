"""Pomocník pre testy: zapíše animovaný GIF (bez závislostí), aby sa dali skúšať zdroje `file:`.

Každý snímok je jednofarebný (alebo dvojfarebný: ľavá polovica iná než pravá), čo stačí na overenie času,
orezania a zrkadlenia. Kompresia LZW je najjednoduchšia možná (CLEAR po každých 250 kódoch), ale platná.
"""
import struct


def _lzw(indices):
    codes, count = [], 0
    out = [256]                                            # CLEAR
    for value in indices:
        out.append(value)
        count += 1
        if count == 250:
            out.append(256)
            count = 0
    out.append(257)                                        # END
    bits, nbits, data = 0, 0, bytearray()
    for code in out:
        bits |= code << nbits
        nbits += 9
        while nbits >= 8:
            data.append(bits & 255)
            bits >>= 8
            nbits -= 8
    if nbits:
        data.append(bits & 255)
    del codes
    return bytes(data)


def _blocks(data):
    out = bytearray()
    for i in range(0, len(data), 255):
        chunk = data[i:i + 255]
        out += bytes([len(chunk)]) + chunk
    return bytes(out) + b"\x00"


def make_gif(path, frames, delays_cs, width=16, height=8, loop=True):
    """frames: [(r, g, b)] jednofarebné, [((r, g, b), (r, g, b))] ľavá a pravá polovica, alebo
    [[[(r, g, b), ...], ...]] celé riadky pixelov (height riadkov po width pixelov).
    delays_cs: oneskorenia v stotinách sekundy."""
    palette = []
    def index(color):
        if color not in palette:
            palette.append(color)
        return palette.index(color)
    pixel_rows = []
    for frame in frames:
        if isinstance(frame[0], list):
            pixel_rows.append([index(tuple(color)) for row in frame for color in row])
            continue
        left, right = (frame, frame) if isinstance(frame[0], int) else frame
        row = [index(left)] * (width // 2) + [index(right)] * (width - width // 2)
        pixel_rows.append(row * height)
    assert len(palette) <= 256
    table = b"".join(bytes(color) for color in palette) + b"\x00\x00\x00" * (256 - len(palette))
    out = bytearray(b"GIF89a" + struct.pack("<HHBBB", width, height, 0xF7, 0, 0) + table)
    if loop:
        out += b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00"
    for pixels, delay in zip(pixel_rows, delays_cs):
        out += b"\x21\xF9\x04\x00" + struct.pack("<H", delay) + b"\x00\x00"        # bez priehľadnosti, bez disposal
        out += b"\x2C" + struct.pack("<HHHHB", 0, 0, width, height, 0) + b"\x08" + _blocks(_lzw(pixels))
    out += b"\x3B"
    with open(path, "wb") as f:
        f.write(bytes(out))
