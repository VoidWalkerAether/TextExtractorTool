# TextExtractorTool
# Tesseract OCR 文本提取工具

这是一个基于 Tesseract OCR 引擎的文本提取工具，支持从 PDF 文件和图片中提取中文文本。该工具专为 macOS 和 Python 3.13 环境设计，具备自动清洗 OCR 提取文本的功能。

## 功能特点

- 支持 PDF 文件和多种图片格式（PNG, JPG, JPEG, BMP, TIFF, WEBP）的文本提取
- 使用 Tesseract OCR 引擎进行中文文本识别
- 自动处理长文档切片识别，确保文本完整性
- 内置文本清洗功能，去除字间空格、规范化标点符号、合并断行
- 支持单文件处理和批量目录处理模式
- 命令行界面，易于集成到自动化流程中

## 环境要求

- macOS 系统
- Python 3.13
- Tesseract OCR 5.5.1+
- 中文语言包 (chi_sim.traineddata)

## 安装配置

### 1. 安装 Tesseract OCR

在 macOS 上安装 Tesseract OCR：

```bash
# 使用 Homebrew 安装 Tesseract
brew install tesseract

# 安装中文语言包
brew install tesseract-lang
```


### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

所需依赖包：
- pytesseract
- PyMuPDF (fitz)
- Pillow

## 使用方法

### 命令行参数

```bash
python ocr_tesseract.py [选项] [文件/目录路径]
```

#### 基本参数

- `path`：PDF/图片文件路径或目录路径（默认：当前目录）
- `-d`, `--directory`：处理整个目录中的所有 PDF 和图片文件
- `-q`, `--quiet`：静默模式，不显示详细进度信息
- `-c`, `--clean`：OCR处理完成后自动调用text_cleaner.py清洗生成的文本文件

### 使用示例

#### 1. 处理单个 PDF 文件

```bash
# 基本文本提取
python ocr_tesseract.py document.pdf

# 提取并自动清洗文本
python ocr_tesseract.py document.pdf -c
```

#### 2. 处理单个图片文件

```bash
# 处理图片文件
python ocr_tesseract.py image.png
python ocr_tesseract.py photo.jpg

# 处理并自动清洗文本
python ocr_tesseract.py image.png -c
```

#### 3. 批量处理目录中的文件

```bash
# 处理目录中的所有支持文件
python ocr_tesseract.py /path/to/directory -d

# 批量处理并自动清洗文本
python ocr_tesseract.py /path/to/directory -d -c

# 静默模式批量处理
python ocr_tesseract.py /path/to/directory -d -q
```

### 文本清洗工具

OCR 提取的文本可能存在以下问题：
- 字间空格（如：你 好 世 界）
- 标点符号不统一
- 断行影响阅读

使用 `text_cleaner.py` 可以清洗这些问题：

```bash
# 清洗单个文件
python text_cleaner.py input.txt

# 清洗并指定输出路径
python text_cleaner.py input.txt -o output.txt

# 批量清洗目录中的所有txt文件
python text_cleaner.py /path/to/directory -d

# 批量清洗并指定输出目录
python text_cleaner.py /path/to/input -d -o /path/to/output
```

## 输出文件

- OCR 工具会生成与源文件同名但扩展名为 `.txt` 的文本文件
- 如果启用了自动清洗功能，生成的文本文件会被进一步处理并覆盖原文件
- 文本清洗工具会在文件名后添加 `_cleaned` 后缀（除非指定了输出路径）

## 技术细节

### OCR 处理流程

1. 对于 PDF 文件：
   - 将页面切片为 1500 像素高的区域，保留 100 像素重叠
   - 使用 3 倍缩放提高识别精度
   - 合并所有切片识别结果

2. 对于图片文件：
   - 直接使用 Tesseract 进行 OCR 识别
   - 自动检测可用语言包（优先使用中文+英文）

3. 乱码过滤：
   - 基于字符统计过滤明显乱码内容
   - 移除连续特殊字符

### 文本清洗功能

1. 规范化处理：
   - 去除字间空格和其他多余空白字符
   - 统一标点符号为全角中文标点

2. 文本结构化：
   - 按句子分割文本
   - 合并短句为段落（每段不超过 500 字符）

3. 元数据提取：
   - 从文件名提取标题、日期等信息
   - 生成处理统计信息（压缩率、字符数等）

## 注意事项

1. 确保 Tesseract OCR 和中文语言包已正确安装
2. 对于包含大量图片的 PDF 文件，处理时间可能会较长
3. 自动清洗功能会覆盖原文件，请谨慎使用
4. 支持的文件格式：PDF, PNG, JPG, JPEG, BMP, TIFF, WEBP
5. 当图片中包含非文字内容（如图表、图像等）时，可能会出现少量乱码现象，需要人工处理
## 故障排除

### Tesseract 未找到

如果遇到 "tesseract: command not found" 错误，请检查：

```bash
# 检查 Tesseract 是否安装
which tesseract

# 检查语言包是否安装
ls /usr/local/share/tessdata/
```

### 中文识别问题

如果中文识别效果不佳：

1. 确认 chi_sim.traineddata 文件存在于 Tesseract 的 tessdata 目录中
2. 尝试使用不同的 PSM 模式（在代码中修改 --psm 参数）
3. 检查图片质量，低分辨率图片会影响识别准确率

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个工具。