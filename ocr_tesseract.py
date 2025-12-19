#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Tesseract OCR 提取 PDF/图片 中的中文文本
适配 macOS + Python 3.13 环境
支持批量处理目录中的所有 PDF 和图片文件
支持的图片格式: .png, .jpg, .jpeg, .bmp, .tiff, .webp

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

import os
import sys
import argparse
import glob
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import subprocess

def ocr_image_with_tesseract(image_path, output_file=None, show_progress=True):
    """
    使用 Tesseract OCR 识别图片中的中文文本
    
    Args:
        image_path: 图片文件路径
        output_file: 可选，保存结果的文本文件路径（如果为None，自动生成）
        show_progress: 是否显示详细进度信息
    
    Returns:
        tuple: (是否成功, 识别出的文本内容或错误信息)
    """
    if show_progress:
        print("-" * 50)
        print("正在使用 Tesseract OCR 引擎处理图片...")
        print(f"图片文件: {image_path}")
        print("-" * 50)
    
    # 检查图片文件是否存在
    if not os.path.exists(image_path):
        error_msg = f"找不到图片文件: {image_path}"
        return (False, error_msg)
    
    # 如果未指定输出文件，自动生成
    if output_file is None:
        image_path_obj = Path(image_path)
        output_file = image_path_obj.with_suffix('.txt')
        output_file = str(output_file)
    
    try:
        # 打开图片
        img = Image.open(image_path)
        
        if show_progress:
            print(f"图片尺寸: {img.width} x {img.height}")
        
        # 检查可用语言
        available_langs = pytesseract.get_languages()
        if show_progress:
            print(f"可用语言包: {available_langs}")
        
        # 选择语言
        if 'chi_sim' in available_langs:
            lang = 'chi_sim+eng'
            if show_progress:
                print(f"使用语言: 中文简体 + 英文")
        else:
            lang = 'eng'
            if show_progress:
                print(f"[警告] 未找到中文语言包，仅使用英文识别")
        
        # 使用 Tesseract 识别
        text = pytesseract.image_to_string(
            img,
            lang=lang,
            config='--psm 6'
        )
        
        # 过滤掉明显是乱码的内容（基于简单的启发式规则）
        text = filter_garbled_text(text)
        
        # 清理识别结果
        result = text.strip()
        
        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        
        if show_progress:
            print(f"\n✓ 结果已保存到: {output_file}")
            print(f"  总字符数: {len(result)}")
            print(f"  总行数: {len(result.splitlines())}")
        
        return (True, result)
        
    except Exception as e:
        error_msg = f"处理图片失败: {e}"
        return (False, error_msg)


def ocr_pdf_with_tesseract(pdf_path, output_file=None, tessdata_dir=None, show_progress=True):
    """
    使用 Tesseract OCR 识别 PDF 中的中文文本
    
    Args:
        pdf_path: PDF 文件路径
        output_file: 可选，保存结果的文本文件路径（如果为None，自动生成）
        tessdata_dir: 可选，Tesseract 语言包目录
        show_progress: 是否显示详细进度信息
    
    Returns:
        tuple: (是否成功, 识别出的文本内容或错误信息)
    """
    if show_progress:
        print("-" * 50)
        print("正在使用 Tesseract OCR 引擎处理 PDF...")
        print(f"PDF 文件: {pdf_path}")
        print("-" * 50)
    
    # 检查 PDF 文件是否存在
    if not os.path.exists(pdf_path):
        error_msg = f"找不到 PDF 文件: {pdf_path}"
        return (False, error_msg)
    
    # 如果未指定输出文件，自动生成（与PDF同名但扩展名为.txt）
    if output_file is None:
        pdf_path_obj = Path(pdf_path)
        output_file = pdf_path_obj.with_suffix('.txt')
        output_file = str(output_file)
    
    # 打开 PDF 文档
    doc = fitz.open(pdf_path)
    full_content = []
    
    # 临时图片文件（使用唯一名称避免冲突）
    pdf_basename = os.path.splitext(os.path.basename(pdf_path))[0]
    temp_img_path = f"temp_tesseract_{pdf_basename}.png"
    
    try:
        # 遍历每一页
        for page_idx, page in enumerate(doc):
            if show_progress:
                print(f"\n>>> 正在处理第 {page_idx + 1} 页 (共 {len(doc)} 页)...")
            
            page_rect = page.rect
            page_h = page_rect.height
            page_w = page_rect.width
            
            if show_progress:
                print(f"    页面尺寸: {page_w:.0f} x {page_h:.0f}")
            
            # --- 切片参数 ---
            chunk_h = 1500  # 每次切片高度（继承原策略）
            overlap = 100   # 重叠区域（继承原策略）
            zoom = 3.0      # 放大3倍，保证清晰度
            
            mat = fitz.Matrix(zoom, zoom)
            
            y = 0
            slice_idx = 0
            
            while y < page_h:
                slice_idx += 1
                
                # 1. 截取区域
                clip_rect = fitz.Rect(0, y, page_w, min(y + chunk_h, page_h))
                
                if show_progress:
                    print(f"    - 切片 {slice_idx}: y={y:.0f} ~ {clip_rect.y1:.0f}")
                
                # 2. 渲染切片为图片
                pix = page.get_pixmap(matrix=mat, clip=clip_rect)
                
                # 3. 保存为临时文件（文件中转模式，避免内存问题）
                pix.save(temp_img_path)
                
                # 4. 使用 Tesseract 识别
                try:
                    # 不设置 TESSDATA_PREFIX，让 Tesseract 使用系统默认路径
                    # （通常是 /usr/local/share/tessdata/）
                    
                    # 在第一次切片时检查可用语言
                    if slice_idx == 1 and page_idx == 0:
                        available_langs = pytesseract.get_languages()
                        if show_progress:
                            print(f"      可用语言包: {available_langs}")
                        
                        # 选择语言
                        if 'chi_sim' in available_langs:
                            lang = 'chi_sim+eng'  # 中文简体 + 英文
                            if show_progress:
                                print(f"      使用语言: 中文简体 + 英文")
                        else:
                            lang = 'eng'  # 只使用英文
                            if show_progress:
                                print(f"      [警告] 未找到中文语言包，仅使用英文识别")
                    else:
                        # 后续切片直接使用已确定的语言
                        available_langs = pytesseract.get_languages()
                        lang = 'chi_sim+eng' if 'chi_sim' in available_langs else 'eng'
                    
                    # 使用 Tesseract 识别
                    text = pytesseract.image_to_string(
                        Image.open(temp_img_path),
                        lang=lang,
                        config='--psm 6'  # PSM 6: 假设文本为单个文本块
                    )
                    
                    # 过滤掉明显是乱码的内容
                    text = filter_garbled_text(text)
                    
                    # 清理识别结果
                    text = text.strip()
                    
                    if text:
                        full_content.append(text)
                        # 显示识别到的文本预览（前100个字符）
                        if show_progress:
                            preview = text.replace('\n', ' ')[:100]
                            print(f"      识别到文本: {preview}...")
                    else:
                        if show_progress:
                            print(f"      (本切片未识别到文本)")
                        
                except Exception as e:
                    if show_progress:
                        print(f"      [警告] 切片识别出错: {e}")
                
                # 移动窗口
                if clip_rect.y1 >= page_h:
                    break
                y += (chunk_h - overlap)
            
            if show_progress:
                print(f"    ✓ 第 {page_idx + 1} 页处理完成")
            
    finally:
        # 清理临时文件
        if os.path.exists(temp_img_path):
            try:
                os.remove(temp_img_path)
            except:
                pass  # 忽略删除失败
        
        doc.close()
    
    # 合并所有文本
    result = "\n\n".join(full_content)
    
    # 保存到文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result)
        if show_progress:
            print(f"\n✓ 结果已保存到: {output_file}")
        return (True, result)
    except Exception as e:
        error_msg = f"保存文件失败: {e}"
        return (False, error_msg)


def process_single_file(file_path, show_progress=True, auto_clean=False):
    """
    处理单个文件（PDF 或图片）
    
    Args:
        file_path: 文件路径
        show_progress: 是否显示详细进度
        auto_clean: 是否自动清洗生成的文本文件
    
    Returns:
        bool: 是否处理成功
    """
    # 判断文件类型
    file_ext = Path(file_path).suffix.lower()
    image_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp']
    
    output_file = None
    if file_ext == '.pdf':
        success, result = ocr_pdf_with_tesseract(file_path, None, None, show_progress)
        # 获取输出文件路径用于后续清洗
        if success:
            pdf_path_obj = Path(file_path)
            output_file = str(pdf_path_obj.with_suffix('.txt'))
    elif file_ext in image_extensions:
        success, result = ocr_image_with_tesseract(file_path, None, show_progress)
        # 获取输出文件路径用于后续清洗
        if success:
            image_path_obj = Path(file_path)
            output_file = str(image_path_obj.with_suffix('.txt'))
    else:
        print(f"\n✗ 不支持的文件格式: {file_ext}")
        print(f"  支持的格式: PDF, PNG, JPG, JPEG, BMP, TIFF, WEBP")
        return False
    
    if success:
        if show_progress:
            # 显示结果统计
            print(f"\n✓ 处理成功")
            print(f"  总字符数: {len(result)}")
            print(f"  总行数: {len(result.splitlines())}")
        
        # 如果启用了自动清洗功能，则调用text_cleaner.py
        if auto_clean and output_file:
            try:
                if show_progress:
                    print(f"\n🔄 正在清洗文本文件...")
                
                # 获取text_cleaner.py的路径
                cleaner_path = os.path.join(os.path.dirname(__file__), 'text_cleaner.py')
                
                # 调用text_cleaner.py清洗文件
                subprocess.run([sys.executable, cleaner_path, output_file, '-o', output_file], 
                              check=True, capture_output=True)
                
                if show_progress:
                    print(f"✓ 文本清洗完成")
            except subprocess.CalledProcessError as e:
                if show_progress:
                    print(f"⚠️ 文本清洗失败: {e}")
            except FileNotFoundError:
                if show_progress:
                    print(f"⚠️ 未找到text_cleaner.py，跳过文本清洗步骤")
    else:
        print(f"\n✗ 处理失败: {result}")
    
    return success


def process_directory(dir_path, show_progress=True, auto_clean=False):
    """
    处理目录中的所有 PDF 和图片文件
    
    Args:
        dir_path: 目录路径
        show_progress: 是否显示详细进度
        auto_clean: 是否自动清洗生成的文本文件
    
    Returns:
        tuple: (成功数量, 失败数量, 总数量)
    """
    # 检查目录是否存在
    if not os.path.isdir(dir_path):
        print(f"❌ 错误：目录不存在: {dir_path}")
        return (0, 0, 0)
    
    # 查找所有支持的文件（PDF + 图片）
    supported_patterns = [
        "*.pdf",
        "*.png", "*.PNG",
        "*.jpg", "*.JPG", "*.jpeg", "*.JPEG",
        "*.bmp", "*.BMP",
        "*.tiff", "*.TIFF", "*.tif", "*.TIF",
        "*.webp", "*.WEBP"
    ]
    
    all_files = []
    for pattern in supported_patterns:
        file_pattern = os.path.join(dir_path, pattern)
        all_files.extend(glob.glob(file_pattern))
    
    if not all_files:
        print(f"❌ 错误：目录中没有找到支持的文件: {dir_path}")
        print(f"  支持的格式: PDF, PNG, JPG, JPEG, BMP, TIFF, WEBP")
        return (0, 0, 0)
    
    total = len(all_files)
    success_count = 0
    fail_count = 0
    
    print("=" * 60)
    print(f"  批量处理文件 (PDF + 图片)")
    print("=" * 60)
    print(f"目录: {dir_path}")
    print(f"找到 {total} 个文件\n")
    
    # 处理每个文件
    for idx, file_path in enumerate(all_files, 1):
        print("=" * 60)
        print(f"[{idx}/{total}] 处理文件: {os.path.basename(file_path)}")
        print("=" * 60)
        
        success = process_single_file(file_path, show_progress, auto_clean)
        
        if success:
            success_count += 1
        else:
            fail_count += 1
        
        print()  # 空行分隔
    
    # 显示总结
    print("=" * 60)
    print("  批量处理完成")
    print("=" * 60)
    print(f"总文件数: {total}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print("=" * 60)
    
    return (success_count, fail_count, total)


def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description='使用 Tesseract OCR 提取 PDF/图片文件中的文本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例用法:
  # 处理单个 PDF 文件
  python ocr_tesseract.py document.pdf
  
  # 处理单个图片文件
  python ocr_tesseract.py image.png
  python ocr_tesseract.py photo.jpg
  
  # 处理目录中的所有 PDF 和图片文件
  python ocr_tesseract.py /path/to/directory -d
  
  # 处理目录，不显示详细进度
  python ocr_tesseract.py /path/to/directory -d -q
  
  # 处理文件并自动清洗生成的文本
  python ocr_tesseract.py document.pdf -c
  
支持的图片格式: PNG, JPG, JPEG, BMP, TIFF, WEBP
        ''')
    
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='PDF/图片文件路径或目录路径（默认：当前目录）'
    )
    
    parser.add_argument(
        '-d', '--directory',
        action='store_true',
        help='处理整个目录中的所有 PDF 和图片文件'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='静默模式，不显示详细进度信息'
    )
    
    parser.add_argument(
        '-c', '--clean',
        action='store_true',
        help='OCR处理完成后自动调用text_cleaner.py清洗生成的文本文件'
    )
    
    args = parser.parse_args()
    
    show_progress = not args.quiet
    auto_clean = args.clean
    
    try:
        if args.directory:
            # 批量处理目录
            success, fail, total = process_directory(args.path, show_progress, auto_clean)
            sys.exit(0 if fail == 0 else 1)
        else:
            # 处理单个文件
            if os.path.isfile(args.path):
                # 明确指定的文件
                print("=" * 60)
                print("  Tesseract OCR - 文本提取")
                print("=" * 60)
                success = process_single_file(args.path, show_progress, auto_clean)
                sys.exit(0 if success else 1)
            elif os.path.isdir(args.path):
                # 是目录但未指定 -d 参数
                print(f"提示: '{args.path}' 是一个目录")
                print(f"如需处理目录中的所有文件，请使用 -d 参数")
                print(f"示例: python ocr_tesseract.py {args.path} -d")
                sys.exit(1)
            else:
                print(f"❌ 错误：文件或目录不存在: {args.path}")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def filter_garbled_text(text):
    """
    过滤掉明显是乱码的文本内容
    """
    if not text.strip():
        return text
    
    # 按行处理
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        # 如果行为空，直接保留
        if not line.strip():
            filtered_lines.append(line)
            continue
        
        # 检查乱码特征
        # 1. 计算非中文、非英文、非数字字符的比例
        total_chars = len(line)
        if total_chars == 0:
            filtered_lines.append(line)
            continue
            
        # 统计正常字符（中文、英文、数字、常见标点）
        normal_chars = len(re.findall(r'[\u4e00-\u9fff\w\s\u3000-\u303f\uff00-\uffef\\\/\:\.\,\!\?\;\"\'\(\)\[\]\{\}\-\+=<>]', line))
        normal_ratio = normal_chars / total_chars
        
        # 如果正常字符比例低于阈值，则认为是乱码，跳过该行
        if normal_ratio < 0.4:  # 40%的阈值可以根据需要调整
            continue
        
        # 2. 检查连续的特殊字符
        if re.search(r'[\!\@\#\$\%\^\&\*\(\)\_\+\=\{\}\[\]\|\\:\;\"\'<>,\?\/]{10,}', line):
            continue
            
        filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)


if __name__ == "__main__":
    main()
