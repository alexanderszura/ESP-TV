"""
Converts animations/<name>/<frame>.png into compressed bitmaps for the ESP32.

Output:
    ESP32-TV/src/bitmaps.h    - extern declarations (ANIM_<NAME>)
    ESP32-TV/src/bitmaps.cpp  - palette + compressed frame data

Compression (lossless):
    1. Every animation gets one shared RGB565 palette.
       Frames store palette indices (1 byte if <= 256 colours, else 2 bytes).
    2. The index stream of each frame is PackBits run-length encoded:
         header 0x00..0x7F -> run:     repeat the next index (header + 1) times
         header 0x80..0xFF -> literal: the next (header - 0x7F) indices are copied as-is
       Runs continue across rows, the decoder splits them back into rows.

The script decodes everything again and checks it matches the source pixels exactly.
"""

from pathlib import Path
from PIL import Image

ANIMATIONS_DIR = Path("animations")
OUT_H = Path("ESP32-TV/src/bitmaps.h")
OUT_CPP = Path("ESP32-TV/src/bitmaps.cpp")

# Milliseconds each frame stays on screen, per animation folder
FRAME_MS = {
    "sunny": 250,
    "partial_cloud": 300,
    "cloud": 400,
    "drizzle": 140,
    "rain": 100,
    "snow": 180,
    "thunder": 110,
}
DEFAULT_FRAME_MS = 150

MAX_RUN = 128


def to_rgb565(r, g, b):
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)


def load_frame(path):
    """Returns (width, height, [rgb565, ...]). Transparent pixels are blended onto black."""
    img = Image.open(path).convert("RGBA")
    background = Image.new("RGBA", img.size, (0, 0, 0, 255))
    img = Image.alpha_composite(background, img).convert("RGB")
    pixels = [to_rgb565(*p) for p in img.get_flattened_data()]
    return img.width, img.height, pixels


def packbits(indices):
    out = []  # list of (is_run, [indices])
    i = 0
    n = len(indices)
    literal = []

    def flush_literal():
        while literal:
            out.append((False, literal[:MAX_RUN]))
            del literal[:MAX_RUN]

    while i < n:
        run = 1
        while i + run < n and run < MAX_RUN and indices[i + run] == indices[i]:
            run += 1

        if run >= 2:
            flush_literal()
            out.append((True, [indices[i]] * run))
            i += run
        else:
            literal.append(indices[i])
            i += 1

    flush_literal()
    return out


def encode_frame(indices, index_bytes):
    data = bytearray()

    def put_index(v):
        data.append(v & 0xFF)
        if index_bytes == 2:
            data.append(v >> 8)

    for is_run, chunk in packbits(indices):
        if is_run:
            data.append(len(chunk) - 1)
            put_index(chunk[0])
        else:
            data.append(0x7F + len(chunk))
            for v in chunk:
                put_index(v)
    return data


def decode_frame(data, pixel_count, index_bytes):
    """Python mirror of the C++ decoder, used to verify the output."""
    out = []
    pos = 0

    def get_index():
        nonlocal pos
        v = data[pos]
        if index_bytes == 2:
            v |= data[pos + 1] << 8
        pos += index_bytes
        return v

    while len(out) < pixel_count:
        header = data[pos]
        pos += 1
        if header < 0x80:
            out.extend([get_index()] * (header + 1))
        else:
            for _ in range(header - 0x7F):
                out.append(get_index())
    return out


def find_frames(folder):
    frames = []
    i = 0
    while (folder / f"{i}.png").is_file():
        frames.append(folder / f"{i}.png")
        i += 1
    return frames


def c_array(values, fmt, per_line=16):
    lines = []
    for i in range(0, len(values), per_line):
        lines.append("\t" + ", ".join(fmt.format(v) for v in values[i:i + per_line]))
    return ",\n".join(lines)


def convert_animation(folder):
    name = folder.name
    paths = find_frames(folder)
    if not paths:
        return None

    frames = [load_frame(p) for p in paths]
    width, height = frames[0][0], frames[0][1]
    for p, (w, h, _) in zip(paths, frames):
        if (w, h) != (width, height):
            raise ValueError(f"{p} is {w}x{h}, expected {width}x{height}")

    palette = []
    lookup = {}
    for _, _, pixels in frames:
        for c in pixels:
            if c not in lookup:
                lookup[c] = len(palette)
                palette.append(c)

    index_bytes = 1 if len(palette) <= 256 else 2

    data = bytearray()
    offsets = []
    for _, _, pixels in frames:
        indices = [lookup[c] for c in pixels]
        offsets.append(len(data))
        encoded = encode_frame(indices, index_bytes)

        # Verify lossless round trip
        decoded = decode_frame(encoded, width * height, index_bytes)
        assert [palette[i] for i in decoded] == pixels, f"{name}: round trip mismatch"

        data += encoded

    raw_size = len(frames) * width * height * 2
    packed_size = len(data) + len(palette) * 2 + len(offsets) * 4
    print(f"{name:14} {len(frames)} frames  {len(palette):4} colours  "
          f"{raw_size:6} B -> {packed_size:5} B  ({100 * packed_size / raw_size:4.1f}%)")

    ident = name.lower()
    cpp = []
    cpp.append(f"// ---- {name}: {len(frames)} frames, {width}x{height}, {len(palette)} colours\n")
    cpp.append(f"static const uint16_t {ident}_palette[] PROGMEM = {{\n{c_array(palette, '0x{:04x}')}\n}};\n\n")
    cpp.append(f"static const uint8_t {ident}_data[] PROGMEM = {{\n{c_array(list(data), '0x{:02x}', 24)}\n}};\n\n")
    cpp.append(f"static const uint32_t {ident}_offsets[] PROGMEM = {{ {', '.join(map(str, offsets))} }};\n\n")
    cpp.append(
        f"const Animation ANIM_{name.upper()} = {{\n"
        f"\t{width}, {height}, {len(frames)}, {FRAME_MS.get(name, DEFAULT_FRAME_MS)}, {index_bytes},\n"
        f"\t{ident}_palette, {ident}_data, {ident}_offsets\n"
        f"}};\n\n"
    )
    return name.upper(), "".join(cpp), raw_size, packed_size


if __name__ == "__main__":
    folders = sorted(p for p in ANIMATIONS_DIR.iterdir() if p.is_dir())

    results = [r for r in (convert_animation(f) for f in folders) if r]

    total_raw = sum(r[2] for r in results)
    total_packed = sum(r[3] for r in results)
    print(f"{'total':14} {total_raw} B -> {total_packed} B ({100 * total_packed / total_raw:.1f}%)")

    header = "// Generated by image_convert.py - do not edit by hand\n#pragma once\n\n#include \"animation.h\"\n\n"
    header += "".join(f"extern const Animation ANIM_{name};\n" for name, *_ in results)
    OUT_H.write_text(header)

    source = "// Generated by image_convert.py - do not edit by hand\n#include \"bitmaps.h\"\n\n"
    source += "".join(cpp for _, cpp, *_ in results)
    OUT_CPP.write_text(source)
