#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文本清洗模块 - 处理OCR提取的文本
专门处理字间空格、标点规范化、段落合并等问题

MIT License

Copyright (c) 2025 ClaudeAgent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional


def normalize_text(text: str) -> str:
    """
    规范化文本：去除字间空格、统一标点、合并断行
    
    Args:
        text: 原始文本（可能包含字间空格）
    
    Returns:
        规范化后的文本
    """
    # 1. 去除所有空白字符（空格、换行、制表符等）
    cleaned = re.sub(r'\s+', '', text.strip())
    
     # 2. 统一标点符号（全角转半角，或统一为全角）
    # 保留中文标点，统一使用全角
    punctuation_map = {
        ',': '，',
        '.': '。',
        '!': '！',
        '?': '？',
        ':': '：',
        ';': '；',
        '(': '（',
        ')': '）',
    }
    
    for half, full in punctuation_map.items():
        cleaned = cleaned.replace(half, full)
    
    return cleaned


def split_into_sentences(text: str) -> List[str]:
    """
    将文本按句子分割
    
    Args:
        text: 规范化后的文本（无空格）
    
    Returns:
        句子列表
    """
    # 按中文标点符号分句
    sentences = re.split(r'[。！？；]', text)
    
    # 过滤空句子，保留有效内容
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    
    return sentences


def split_into_paragraphs(text: str, min_length: int = 50) -> List[str]:
    """
    将文本按段落分割（适用于已去空格的文本）
    
    Args:
        text: 规范化后的文本
        min_length: 最小段落长度
    
    Returns:
        段落列表
    """
    # 先按句子分割
    sentences = split_into_sentences(text)
    
    # 合并短句为段落
    paragraphs = []
    current_para = ""
    
    for sentence in sentences:
        if len(current_para) + len(sentence) < 500:  # 单段落不超过500字
            current_para += sentence + "。"
        else:
            if len(current_para) >= min_length:
                paragraphs.append(current_para)
            current_para = sentence + "。"
    
    # 添加最后一段
    if len(current_para) >= min_length:
        paragraphs.append(current_para)
    
    return paragraphs


def extract_metadata_from_filename(filename: str) -> Dict[str, str]:
    """
    从文件名提取元数据
    
    Args:
        filename: 文件名，如 "A股4000拉锯要不要买黄金_20251126102506_11_342.txt"
    
    Returns:
        元数据字典 {title, date, page_info}
    """
    # 移除扩展名
    name_without_ext = Path(filename).stem
    
    # 尝试按下划线分割
    parts = name_without_ext.split('_')
    
    metadata = {
        "title": "",
        "date": "",
        "page_info": ""
    }
    
    if len(parts) >= 1:
        metadata["title"] = parts[0]
    
    if len(parts) >= 2:
        # 尝试解析日期（格式：20251126102506）
        date_str = parts[1]
        if len(date_str) >= 8 and date_str[:8].isdigit():
            # 转换为 YYYY-MM-DD 格式
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:8]
            metadata["date"] = f"{year}-{month}-{day}"
    
    if len(parts) >= 3:
        metadata["page_info"] = "_".join(parts[2:])
    
    return metadata


def clean_ocr_text_file(input_path: str, output_path: Optional[str] = None) -> Dict:
    """
    清洗OCR文本文件
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径（可选，默认为输入文件名_cleaned.txt）
    
    Returns:
        清洗结果字典
    """
    input_file = Path(input_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"文件不存在: {input_path}")
    
    # 读取原始文本
    with open(input_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()
    
    # 提取元数据
    metadata = extract_metadata_from_filename(input_file.name)
    
    # 文本清洗
    normalized_text = normalize_text(raw_text)
    
    # 分句
    sentences = split_into_sentences(normalized_text)
    
    # 分段
    paragraphs = split_into_paragraphs(normalized_text)
    
    # 统计信息
    stats = {
        "original_length": len(raw_text),
        "cleaned_length": len(normalized_text),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "compression_ratio": f"{(1 - len(normalized_text) / len(raw_text)) * 100:.2f}%"
    }
    
    # 生成输出路径
    if output_path is None:
        output_path = input_file.with_stem(f"{input_file.stem}_cleaned").with_suffix('.txt')
    
    # 保存清洗后的文本（按段落输出，便于阅读）
    with open(output_path, 'w', encoding='utf-8') as f:
        # 写入元数据头
        f.write(f"# 标题: {metadata['title']}\n")
        f.write(f"# 日期: {metadata['date']}\n")
        f.write(f"# 页面信息: {metadata['page_info']}\n")
        f.write(f"# 原始长度: {stats['original_length']} 字符\n")
        f.write(f"# 清洗后长度: {stats['cleaned_length']} 字符\n")
        f.write(f"# 压缩率: {stats['compression_ratio']}\n")
        f.write("\n" + "=" * 60 + "\n\n")
        
        # 写入段落（每段落后空一行）
        for i, para in enumerate(paragraphs, 1):
            f.write(f"{para}\n\n")
    
    result = {
        "metadata": metadata,
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "sentences": sentences,
        "paragraphs": paragraphs,
        "stats": stats,
        "output_file": str(output_path)
    }
    
    return result


def batch_clean_directory(input_dir: str, output_dir: Optional[str] = None, 
                         file_pattern: str = "*.txt") -> List[Dict]:
    """
    批量清洗目录中的文本文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录（可选）
        file_pattern: 文件匹配模式
    
    Returns:
        清洗结果列表
    """
    input_path = Path(input_dir)
    
    if not input_path.is_dir():
        raise NotADirectoryError(f"不是目录: {input_dir}")
    
    # 创建输出目录
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    else:
        output_path = input_path / "cleaned"
        output_path.mkdir(exist_ok=True)
    
    # 查找所有匹配的文件
    files = list(input_path.glob(file_pattern))
    
    if not files:
        print(f"⚠️  未找到匹配的文件: {file_pattern}")
        return []
    
    print(f"📁 找到 {len(files)} 个文件")
    print("=" * 60)
    
    results = []
    
    for idx, file_path in enumerate(files, 1):
        print(f"\n[{idx}/{len(files)}] 处理: {file_path.name}")
        
        try:
            # 生成输出文件路径
            output_file = output_path / f"{file_path.stem}_cleaned.txt"
            
            # 清洗文件
            result = clean_ocr_text_file(str(file_path), str(output_file))
            results.append(result)
            
            # 显示统计
            stats = result['stats']
            print(f"  ✅ 完成")
            print(f"     原始: {stats['original_length']} 字符")
            print(f"     清洗: {stats['cleaned_length']} 字符")
            print(f"     压缩: {stats['compression_ratio']}")
            print(f"     句子: {stats['sentence_count']} 个")
            print(f"     段落: {stats['paragraph_count']} 个")
            print(f"     输出: {result['output_file']}")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ 批量处理完成: 成功 {len(results)}/{len(files)}")
    
    return results


# 命令行使用
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="OCR文本清洗工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 清洗单个文件
  python text_cleaner.py A股4000拉锯要不要买黄金_20251126102506_11_342.txt
  
  # 清洗单个文件并指定输出路径
  python text_cleaner.py input.txt -o output.txt
  
  # 批量清洗目录中的所有txt文件
  python text_cleaner.py /path/to/directory -d
  
  # 批量清洗并指定输出目录
  python text_cleaner.py /path/to/input -d -o /path/to/output
        """
    )
    
    parser.add_argument(
        'input',
        help='输入文件或目录路径'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='输出文件或目录路径'
    )
    
    parser.add_argument(
        '-d', '--directory',
        action='store_true',
        help='批量处理目录模式'
    )
    
    parser.add_argument(
        '-p', '--pattern',
        default='*.txt',
        help='文件匹配模式（批量模式下使用，默认: *.txt）'
    )
    
    args = parser.parse_args()
    
    try:
        if args.directory:
            # 批量处理模式
            results = batch_clean_directory(
                args.input,
                args.output,
                args.pattern
            )
        else:
            # 单文件处理模式
            print("🚀 开始清洗文本文件")
            print("=" * 60)
            
            result = clean_ocr_text_file(args.input, args.output)
            
            print("\n✅ 清洗完成!")
            print("=" * 60)
            print(f"📋 元数据:")
            print(f"  标题: {result['metadata']['title']}")
            print(f"  日期: {result['metadata']['date']}")
            print(f"  页面: {result['metadata']['page_info']}")
            
            print(f"\n📊 统计信息:")
            for key, value in result['stats'].items():
                print(f"  {key}: {value}")
            
            print(f"\n💾 输出文件: {result['output_file']}")
            
            print("\n📝 清洗后文本预览（前200字符）:")
            print("-" * 60)
            print(result['normalized_text'][:200])
            print("-" * 60)
            
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
