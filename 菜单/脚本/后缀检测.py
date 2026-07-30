#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动检测无后缀文件类型并重命名
依据文件头部十六进制魔数(Magic Number)进行识别
"""

import os
import sys
import argparse
from pathlib import Path

# 固定的工作根目录
ROOT_DIR = "/storage/emulated/0/termux"

# ============================================================
# 文件签名数据库 (按头部长度从长到短排列，优先匹配更精确的签名)
# 格式: (hex_signature, offset, extension)
# ============================================================
FILE_SIGNATURES = [
    # 图片格式
    ("89504E470D0A1A0A", 0, ".png"),       # PNG
    ("FFD8FFE0",         0, ".jpg"),       # JPEG (JFIF)
    ("FFD8FFE1",         0, ".jpg"),       # JPEG (EXIF)
    ("FFD8FFE2",         0, ".jpg"),       # JPEG (SPIFF)
    ("FFD8FFE3",         0, ".jpg"),       # JPEG
    ("FFD8FFE8",         0, ".jpg"),       # JPEG
    ("FFD8FFDB",         0, ".jpg"),       # JPEG
    ("474946383961",     0, ".gif"),       # GIF89a
    ("474946383761",     0, ".gif"),       # GIF87a
    ("424D",             0, ".bmp"),       # BMP
    ("52494646",         0, ".webp_check"),# WEBP/AVI/WAV (需二次检查)
    ("00000100",         0, ".ico"),       # ICO
    ("49492A00",         0, ".tiff"),      # TIFF (little-endian)
    ("4D4D002A",         0, ".tiff"),      # TIFF (big-endian)
    ("66747970",         4, ".mp4"),       # MP4/MOV (ftyp at offset 4)
    ("0000000C6A50",     0, ".jp2"),       # JPEG 2000

    # 文档格式
    ("25504446",         0, ".pdf"),       # PDF
    ("D0CF11E0A1B11AE1", 0, ".doc"),      # OLE2 (doc/xls/ppt)
    ("504B0304",         0, ".zip_check"), # ZIP/DOCX/XLSX/PPTX/JAR/APK
    ("7F454C46",         0, ".elf"),       # ELF executable
    ("CAFEBABE",         0, ".class"),     # Java class

    # 压缩/归档格式
    ("526172211A0700",   0, ".rar"),       # RAR v1.5+
    ("526172211A070100", 0, ".rar"),       # RAR v5.0
    ("377ABCAF271C",     0, ".7z"),        # 7-Zip
    ("1F8B08",           0, ".gz"),        # GZIP
    ("425A68",           0, ".bz2"),       # BZIP2
    ("FD377A585A00",     0, ".xz"),        # XZ
    ("504B0506",         0, ".zip"),       # Empty ZIP archive
    ("504B0708",         0, ".zip"),       # Spanned ZIP archive

    # 音视频格式
    ("494433",           0, ".mp3"),       # MP3 (ID3v2)
    ("FFFB",             0, ".mp3"),       # MP3 (no ID3)
    ("FFF3",             0, ".mp3"),       # MP3
    ("FFF2",             0, ".mp3"),       # MP3
    ("664C6143",         0, ".flac"),      # FLAC
    ("4F676753",         0, ".ogg"),       # OGG
    ("52494646",         0, ".wav_check"), # WAV (RIFF....WAVE)
    ("1A45DFA3",         0, ".mkv"),       # MKV/WebM
    ("0000001866747970", 0, ".mov"),       # MOV (some variants)
    ("3026B2758E66CF11", 0, ".wmv"),       # WMV/WMA
]


def build_signature_tree():
    """构建签名查找表，提高匹配效率"""
    sigs = []
    for hex_sig, offset, ext in FILE_SIGNATURES:
        try:
            byte_sig = bytes.fromhex(hex_sig)
            sigs.append((byte_sig, offset, ext))
        except ValueError as e:
            print(f"[警告] 无效签名 '{hex_sig}': {e}")
    # 按 (offset + len) 降序排列，确保更长/更精确的签名优先匹配
    sigs.sort(key=lambda x: x[1] + len(x[0]), reverse=True)
    return sigs


SIGNATURES = build_signature_tree()


def detect_file_type(filepath: str, read_size: int = 512) -> str | None:
    """
    通过读取文件头部字节，匹配魔数来检测文件类型
    返回扩展名(如 '.png')或 None
    """
    try:
        with open(filepath, 'rb') as f:
            header = f.read(read_size)
    except (IOError, PermissionError) as e:
        print(f"  [错误] 无法读取: {filepath} ({e})")
        return None

    if len(header) < 2:
        return None

    for byte_sig, offset, ext in SIGNATURES:
        end = offset + len(byte_sig)
        if len(header) >= end and header[offset:end] == byte_sig:
            # 特殊二次检查
            if ext == ".webp_check":
                # RIFF????WEBP
                if len(header) >= 12 and header[8:12] == b'WEBP':
                    return ".webp"
                elif len(header) >= 12 and header[8:12] == b'AVI ':
                    return ".avi"
                elif len(header) >= 12 and header[8:12] == b'WAVE':
                    return ".wav"
                continue
            if ext == ".wav_check":
                if len(header) >= 12 and header[8:12] == b'WAVE':
                    return ".wav"
                continue
            if ext == ".zip_check":
                # PK\x03\x04 可能是 zip/docx/xlsx/apk 等
                # 简单策略：统一标记为 .zip，用户可后续手动区分 Office 文件
                # 如需区分 docx/xlsx，可进一步解析 ZIP 内部结构
                return ".zip"
            return ext

    return None


def safe_rename(src: Path, ext: str) -> Path:
    """安全重命名，避免覆盖已有文件"""
    dst = src.with_suffix(ext)
    if not dst.exists():
        return dst
    counter = 1
    while True:
        dst = src.parent / f"{src.name}_{counter}{ext}"
        if not dst.exists():
            return dst
        counter += 1


def scan_and_rename(root_dir: str, dry_run: bool = False, recursive: bool = True):
    """扫描目录并重命名无后缀文件"""
    root = Path(root_dir).resolve()
    stats = {"scanned": 0, "renamed": 0, "skipped": 0, "unknown": 0, "errors": 0}

    iterator = root.rglob("*") if recursive else root.glob("*")

    for filepath in sorted(iterator):
        if not filepath.is_file():
            continue

        stats["scanned"] += 1

        # 跳过已有后缀的文件
        if filepath.suffix:
            stats["skipped"] += 1
            continue

        # 检测文件类型
        ext = detect_file_type(str(filepath))

        if ext is None:
            stats["unknown"] += 1
            print(f"  [未知] {filepath.relative_to(root)}")
            continue

        # 执行重命名
        new_path = safe_rename(filepath, ext)
        rel_old = filepath.relative_to(root)
        rel_new = new_path.relative_to(root)

        if dry_run:
            print(f"  [预览] {rel_old} → {rel_new}")
        else:
            try:
                filepath.rename(new_path)
                print(f"  [完成] {rel_old} → {rel_new}")
                stats["renamed"] += 1
            except OSError as e:
                print(f"  [失败] {rel_old}: {e}")
                stats["errors"] += 1
                continue

    # 打印统计
    print("\n" + "=" * 50)
    print(f"📊 统计结果:")
    print(f"   扫描文件: {stats['scanned']}")
    print(f"   成功重命名: {stats['renamed']}")
    print(f"   跳过(已有后缀): {stats['skipped']}")
    print(f"   未识别类型: {stats['unknown']}")
    print(f"   错误: {stats['errors']}")
    if dry_run:
        print("   ⚠️  以上为预览模式，未实际修改任何文件")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="根据文件头魔数自动检测无后缀文件类型并添加扩展名"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=ROOT_DIR,
        help=f"要扫描的目录路径 (默认: {ROOT_DIR})"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="预览模式，仅显示将要执行的操作而不实际重命名"
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="不递归扫描子目录"
    )

    args = parser.parse_args()

    # 检查根目录是否存在
    if not os.path.isdir(ROOT_DIR):
        print(f"[错误] 工作根目录不存在或无法访问: {ROOT_DIR}")
        sys.exit(1)

    # 解析目标目录：相对路径基于 ROOT_DIR
    if os.path.isabs(args.directory):
        target = Path(args.directory).resolve()
    else:
        target = (Path(ROOT_DIR) / args.directory).resolve()

    if not target.is_dir():
        print(f"[错误] 路径不存在或不是目录: {target}")
        sys.exit(1)

    mode = "预览模式" if args.dry_run else "执行模式"
    recurse = "递归" if not args.no_recursive else "仅当前目录"
    print(f"🔍 自动文件类型检测与重命名工具")
    print(f"   目录: {target}")
    print(f"   模式: {mode} | {recurse}")
    print("-" * 50)

    scan_and_rename(
        str(target),
        dry_run=args.dry_run,
        recursive=not args.no_recursive
    )


if __name__ == "__main__":
    main()