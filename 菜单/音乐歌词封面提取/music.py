#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频封面与歌词提取脚本（集中输出）
支持格式：.mp3, .flac
封面保存到 output_jpg/原文件名.jpg
歌词保存到 output_txt/原文件名.txt
"""

import os
import sys
from mutagen import File
from mutagen.id3 import ID3, USLT
from mutagen.flac import FLAC, Picture

# 输出目录配置
COVER_DIR = "output_jpg"
LYRICS_DIR = "output_txt"

def ensure_dir(directory):
    """确保输出目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def extract_cover_and_lyrics(file_path):
    """
    从音频文件中提取封面图片和未同步歌词，保存到指定输出目录
    """
    # 确保输出目录存在
    ensure_dir(COVER_DIR)
    ensure_dir(LYRICS_DIR)

    base_name = os.path.splitext(os.path.basename(file_path))[0]  # 去掉路径和扩展名
    cover_path = os.path.join(COVER_DIR, base_name + ".jpg")
    lyrics_path = os.path.join(LYRICS_DIR, base_name + ".txt")

    # 加载音频文件
    audio = File(file_path)
    if audio is None:
        print(f"无法解析文件: {file_path}")
        return

    # ----- 提取封面图片 -----
    cover_extracted = False
    try:
        # MP3 处理 (ID3 标签中的 APIC 帧)
        if isinstance(audio, ID3) or (hasattr(audio, 'tags') and audio.tags is not None):
            tags = audio if isinstance(audio, ID3) else audio.tags
            if isinstance(tags, ID3):
                for tag in tags.values():
                    if tag.FrameID == 'APIC':  # 图片帧
                        image_data = tag.data
                        with open(cover_path, 'wb') as f:
                            f.write(image_data)
                        print(f"封面已提取: {cover_path}")
                        cover_extracted = True
                        break

        # FLAC 处理 (PICTURE 块)
        if isinstance(audio, FLAC) and audio.pictures:
            picture = audio.pictures[0]
            image_data = picture.data
            with open(cover_path, 'wb') as f:
                f.write(image_data)
            print(f"封面已提取: {cover_path}")
            cover_extracted = True

        if not cover_extracted:
            print(f"未找到封面: {file_path}")

    except Exception as e:
        print(f"提取封面时出错 {file_path}: {e}")

    # ----- 提取歌词 -----
    lyrics_extracted = False
    try:
        # MP3 中的未同步歌词 (USLT 帧)
        if isinstance(audio, ID3) or (hasattr(audio, 'tags') and isinstance(audio.tags, ID3)):
            tags = audio if isinstance(audio, ID3) else audio.tags
            uslt_frames = [t for t in tags.values() if isinstance(t, USLT)]
            if uslt_frames:
                lyrics_text = uslt_frames[0].text
                with open(lyrics_path, 'w', encoding='utf-8') as f:
                    f.write(lyrics_text)
                print(f"歌词已提取: {lyrics_path}")
                lyrics_extracted = True

        # FLAC 中的歌词 (Vorbis 注释的 LYRICS 字段)
        elif isinstance(audio, FLAC):
            if 'LYRICS' in audio:
                lyrics_text = '\n'.join(audio['LYRICS'])
                with open(lyrics_path, 'w', encoding='utf-8') as f:
                    f.write(lyrics_text)
                print(f"歌词已提取: {lyrics_path}")
                lyrics_extracted = True

        if not lyrics_extracted:
            print(f"未找到歌词: {file_path}")

    except Exception as e:
        print(f"提取歌词时出错 {file_path}: {e}")

def main():
    # 如果没有提供命令行参数，则处理当前目录下所有 .mp3 和 .flac 文件
    if len(sys.argv) > 1:
        targets = sys.argv[1:]
    else:
        targets = ['.']

    # 收集所有要处理的文件
    files_to_process = []
    for target in targets:
        if os.path.isfile(target):
            ext = os.path.splitext(target)[1].lower()
            if ext in ['.mp3', '.flac']:
                files_to_process.append(target)
            else:
                print(f"跳过非音频文件: {target}")
        elif os.path.isdir(target):
            # 递归查找所有 .mp3 和 .flac 文件
            for root, dirs, files in os.walk(target):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in ['.mp3', '.flac']:
                        files_to_process.append(os.path.join(root, file))
        else:
            print(f"无效路径: {target}")

    if not files_to_process:
        print("未找到任何 .mp3 或 .flac 文件。")
        return

    print(f"找到 {len(files_to_process)} 个音频文件，开始处理...")
    for file_path in files_to_process:
        extract_cover_and_lyrics(file_path)

if __name__ == "__main__":
    main()