# PDF 工具集

读取PDF内容 / 导出PDF文件（支持中文表格）

## 安装依赖

```bash
python3 -m pip install PyMuPDF reportlab markdown
```

## 使用方式

### 1. 读取PDF

```bash
# 读取全部页面
python3 pdf_utils.py read resume.pdf

# 读取指定页面
python3 pdf_utils.py read resume.pdf -p 1 2 3

# 查看元数据
python3 pdf_utils.py read resume.pdf -m
```

### 2. 导出PDF（支持Markdown表格）

```bash
# 基本用法（自动查找雅黑字体）
python3 pdf_utils.py export 简历.md

# 指定输出路径
python3 pdf_utils.py export 简历.md -o 简历.pdf

# 指定字体（macOS雅黑）
python3 pdf_utils.py export 简历.md \
  -fr /Users/admin/Library/Fonts/MSYH.TTC \
  -fb /Users/admin/Library/Fonts/msyhbd.ttf
```

### 3. Python API调用

```python
from pdf_utils import read_pdf, export_pdf_from_markdown

# 读取PDF
content = read_pdf("resume.pdf")

# 导出PDF（自动查找雅黑字体）
export_pdf_from_markdown("简历.md", "简历.pdf")

# 指定字体
export_pdf_from_markdown("简历.md", "简历.pdf",
    font_regular="/Users/admin/Library/Fonts/MSYH.TTC",
    font_bold="/Users/admin/Library/Fonts/msyhbd.ttf")
```

## 支持的Markdown语法

| 语法 | 支持程度 | 说明 |
|------|---------|------|
| `# 标题` | ✅ 完整 | 三级标题（H1/H2/H3） |
| `**加粗**` | ✅ 完整 | 自动转粗体样式 |
| `- 列表` | ✅ 完整 | 带缩进的 bullet list |
| `> 引用` | ✅ 完整 | 斜体样式引用 |
| `\| 表格 \|` | ✅ 完整 | 带表头着色+交替行颜色 |
| `---` 分隔线 | ✅ 完整 | 水平线 |
| `` `代码` `` | ✅ 完整 | 红色等宽字体 |

## 表格渲染效果

- 表头：深色背景 + 白色文字 + 居中对齐
- 数据行：交替灰白背景 + 网格线
- 自动列宽均分

## 字体配置

### macOS 雅黑字体路径

| 变体 | 路径 |
|------|------|
| 常规 | `/Users/admin/Library/Fonts/MSYH.TTC` |
| 粗体 | `/Users/admin/Library/Fonts/msyhbd.ttf` |

### 其他可用中文字体

| 字体 | 路径 |
|------|------|
| 苹方 | `/System/Library/Fonts/PingFang.ttc` |
| 黑体 | `/System/Library/Fonts/STHeiti Light.ttc` |

## 输出规格

- 纸张：A4
- 页边距：上下 18mm，左右 20mm
- 正文字号：10pt
- 标题字号：H1=15pt, H2=13pt, H3=11pt
