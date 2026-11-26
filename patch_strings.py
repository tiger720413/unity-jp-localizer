#!/usr/bin/env python3
"""等长字节替换补丁器:按翻译表把文件中的日文替换为中文(长度不变)。

用法: python3 patch_strings.py <目标文件> <翻译表.tsv> [--dry-run]

翻译表格式(TSV,每行 偏移\\t原文\\t译文;文本内的换行写作 \\n):
  715438	お気に入り	收藏
  717555	一番奥の個室…\\nノックは4回\\n…	最里面的单间…\\n敲门4下\\n…

规则:
  - 译文 UTF-8 字节数必须 <= 原文,不足用空格补齐
  - 替换前校验偏移处内容 == 原文(防错位)
  - 自动备份 <文件>.bak
"""
import shutil
import sys


def unesc(t: str) -> str:
    return t.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")


def main():
    path, table_path = sys.argv[1], sys.argv[2]
    dry = "--dry-run" in sys.argv

    rows = []
    for line in open(table_path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            raise SystemExit(f"翻译表行格式错误(需 3 列): {line[:60]}")
        rows.append((int(parts[0]), unesc(parts[1]), unesc(parts[2])))

    data = bytearray(open(path, "rb").read())
    orig_len = len(data)
    bad = []
    for off, jp, cn in rows:
        jb = jp.encode("utf-8")
        cb = cn.encode("utf-8")
        cur = bytes(data[off:off + len(jb)])
        if cur != jb:
            bad.append((off, jp, f"偏移处内容不符: {cur[:40]!r}"))
            continue
        if len(cb) > len(jb):
            bad.append((off, jp, f"译文太长: {len(cb)} > {len(jb)} 字节"))
            continue
        pad = b" " * (len(jb) - len(cb))
        data[off:off + len(jb)] = cb + pad

    if bad:
        for b in bad:
            print("FAIL:", b)
        sys.exit(1)
    assert len(data) == orig_len

    if not dry:
        shutil.copyfile(path, path + ".bak")
        with open(path, "wb") as f:
            f.write(bytes(data))
    print(f"{'[dry-run] ' if dry else ''}OK: {len(rows)} 条全部打补丁,文件长度不变 ({orig_len} bytes)")


if __name__ == "__main__":
    main()
