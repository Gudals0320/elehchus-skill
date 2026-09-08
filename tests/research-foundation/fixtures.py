#!/usr/bin/env python3
"""Deterministic synthetic input bytes. No photo library or network dependency."""
from __future__ import annotations

import base64
import hashlib
import struct
import zlib

# 8x6 RGB gradient, encoded once with Pillow 12.3.0, JPEG quality 80,
# optimize=False, progressive=False. Generated test pixels, not a real photograph.
JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAGAAgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDF8IfD2z+TlPyooorow1SXJua5DmWK+qR/eM//2Q=="
)


def exif(orientation: int, date: str | None = None, offset: str | None = None) -> bytes:
    """Little-endian TIFF metadata with a proper Exif sub-IFD."""
    count = 2 if date else 1
    header = b"II*\x00" + struct.pack("<I", 8)
    entries = [struct.pack("<HHI", 274, 3, 1) + struct.pack("<H", orientation) + b"\0\0"]
    tail = b""
    if date:
        sub_at = 8 + 2 + count * 12 + 4
        entries.append(struct.pack("<HHII", 34665, 4, 1, sub_at))
        values = [(36867, date.encode("ascii") + b"\0")]
        if offset:
            values.append((36881, offset.encode("ascii") + b"\0"))
        data_at = sub_at + 2 + len(values) * 12 + 4
        sub_entries, payload = [], b""
        for tag, value in values:
            sub_entries.append(struct.pack("<HHII", tag, 2, len(value), data_at + len(payload)))
            payload += value
        tail = struct.pack("<H", len(values)) + b"".join(sub_entries) + b"\0" * 4 + payload
    return header + struct.pack("<H", count) + b"".join(entries) + b"\0" * 4 + tail


def jpeg_with_exif(orientation: int, date: str | None = None, offset: str | None = None) -> bytes:
    metadata = b"Exif\0\0" + exif(orientation, date, offset)
    return JPEG[:2] + b"\xff\xe1" + struct.pack(">H", len(metadata) + 2) + metadata + JPEG[2:]


def png() -> bytes:
    def chunk(kind, value):
        return struct.pack(">I", len(value)) + kind + value + struct.pack(">I", zlib.crc32(kind + value) & 0xFFFFFFFF)
    raw = b"".join(b"\0" + bytes(v for x in range(8) for v in (x * 28, y * 36, (x + y) * 17)) for y in range(6))
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 6, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def tiff() -> bytes:
    """Uncompressed 8x6 RGB TIFF with DateTime but no timezone."""
    tags = [(256, 4, 1, 8), (257, 4, 1, 6), (258, 3, 3, None), (259, 3, 1, 1),
            (262, 3, 1, 2), (273, 4, 1, None), (274, 3, 1, 8), (277, 3, 1, 3),
            (278, 4, 1, 6), (279, 4, 1, 8 * 6 * 3), (284, 3, 1, 1), (306, 2, 20, None)]
    extra_at = 8 + 2 + len(tags) * 12 + 4
    date = b"2024:07:15 10:20:30\0"
    extras = struct.pack("<HHH", 8, 8, 8) + date
    pointers = {258: extra_at, 306: extra_at + 6, 273: extra_at + len(extras)}
    entries = []
    for tag, kind, count, value in tags:
        value = pointers.get(tag, value)
        payload = struct.pack("<H", value) + b"\0\0" if kind == 3 and count == 1 else struct.pack("<I", value)
        entries.append(struct.pack("<HHI", tag, kind, count) + payload)
    pixels = bytes(v for y in range(6) for x in range(8) for v in (x * 28, y * 36, (x + y) * 17))
    return b"II*\x00" + struct.pack("<I", 8) + struct.pack("<H", len(tags)) + b"".join(entries) + b"\0" * 4 + extras + pixels


def photo_files() -> dict[str, bytes]:
    dated = jpeg_with_exif(1, "2024:07:15 10:20:30", "+09:00")
    return {
        "session A/dated.jpg": dated,
        "copies/duplicate.jpg": dated,
        "회전/rotated.jpg": jpeg_with_exif(6),
        "plain.png": png(),
        "formats/sample.tiff": tiff(),
        "broken/truncated.jpg": JPEG[:32],
        "notes.txt": b"Synthetic non-photo input.\n",
    }


def photo_expectations() -> dict:
    return {
        "provenance": "deterministic synthetic pixels and metadata; not user photos",
        "duplicates": [["copies/duplicate.jpg", "session A/dated.jpg"]],
        "date_original": {"session A/dated.jpg": "2024:07:15 10:20:30", "copies/duplicate.jpg": "2024:07:15 10:20:30"},
        "offset_time_original": {"session A/dated.jpg": "+09:00", "copies/duplicate.jpg": "+09:00"},
        "orientation": {"session A/dated.jpg": 1, "copies/duplicate.jpg": 1, "회전/rotated.jpg": 6, "formats/sample.tiff": 8},
        "tiff_datetime_without_timezone": {"formats/sample.tiff": "2024:07:15 10:20:30"},
        "no_embedded_capture_date": ["회전/rotated.jpg", "plain.png"],
        "invalid_image": ["broken/truncated.jpg"],
        "non_image": ["notes.txt"],
        "not_tested": ["camera fidelity", "HEIC", "RAW", "large-library performance"],
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(photo_files().items())},
    }
