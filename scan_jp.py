#!/usr/bin/env python3
"""扫描文件或目录中的 UTF-8 日文字符串(字节级)。

用法: python3 scan_jp.py <文件或目录> [输出.txt]
输出: 文件路径 | 偏移 | 文本(按字节长度降序)
"""
import os
import re
import sys

# 一个日文字符的 UTF-8 字节模式:
#   E3 80-83 xx = ぁ-ん/ァ-ン/、。「」
#   E4-E9 xx xx = CJK 汉字
JP_CHAR = rb"(?:\xE3[\x80-\x83][\x80-\xBF]|[\xE4-\xE9][\x80-\xBF]{2})"
JP_RUN = re.compile(JP_CHAR + rb"+")


def count_jp(s: bytes) -> int:
    return len(JP_RUN.findall(s))


def scan_file(path: str, base: str, found: dict) -> None:
    chunk = 32 * 1024 * 1024
    tail = b""
    off = 0
    with open(path, "rb") as f:
        while True:
            data = tail + f.read(chunk)
            if not data:
                break
            tail = b"" if len(data) < chunk + 300 else data[-300:]
            for m in JP_RUN.finditer(data):
                start = m.start()
                i = start
                while i > 0 and data[i - 1:i] >= b" " and data[i - 1:i] <= b"~":
                    i -= 1
                j = m.end()
                while j < len(data):
                    c = data[j:j + 1]
                    mm = JP_RUN.match(data, j)
                    if mm:
                        j += len(mm.group(0))
                    elif c >= b" " and c <= b"~":
                        j += 1
                    else:
                        break
                s = data[i:j]
                if 4 <= len(s) <= 300 and count_jp(s) >= 2:
                    found.setdefault(s, []).append((os.path.relpath(path, base), off + i))
            off += len(data) - len(tail)


def main():
    target = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "jp_strings.txt"
    found: dict = {}
    if os.path.isdir(target):
        base = target
        for dirpath, _dirs, files in os.walk(target):
            for fn in sorted(files):
                p = os.path.join(dirpath, fn)
                try:
                    if os.path.getsize(p) < 1024:
                        continue
                except OSError:
                    continue
                try:
                    scan_file(p, base, found)
                except OSError:
                    continue
    else:
        scan_file(target, os.path.dirname(target), found)

    lines = []
    for s, locs in sorted(found.items(), key=lambda kv: -len(kv[0])):
        try:
            t = s.decode("utf-8")
        except Exception:
            continue
        p, off = locs[0]
        lines.append(f"{p}\t{off}\t{t}")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"{len(lines)} 个唯一日文串 -> {out}")


if __name__ == "__main__":
    main()
