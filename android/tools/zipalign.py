#!/usr/bin/env python3
"""zipalign equivalent: rewrites an APK so every uncompressed entry starts on a
4-byte boundary (.so files on 4096). Usage: zipalign.py in.apk out.apk"""
import sys, zipfile

src, dst = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(src) as zin, open(dst, "wb") as raw, zipfile.ZipFile(raw, "w") as zout:
    for info in zin.infolist():
        data = zin.read(info)
        ni = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        ni.compress_type = info.compress_type
        ni.external_attr = info.external_attr
        ni.create_system = info.create_system
        if info.compress_type == zipfile.ZIP_STORED:
            boundary = 4096 if info.filename.endswith(".so") else 4
            start = raw.tell() + 30 + len(info.filename.encode("utf-8"))
            pad = (-start) % boundary
            ni.extra = b"\0" * pad
        zout.writestr(ni, data)
print(f"aligned {dst}")
