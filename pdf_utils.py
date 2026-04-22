#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF工具集：读取PDF内容、导出PDF文件（支持中文表格）
依赖：pip install PyMuPDF reportlab markdown
"""

from __future__ import annotations
import os
import re
import sys
from pathlib import Path
from typing import List, Optional


# ============================================================
# 工具1：读取PDF文件内容
# ============================================================
def read_pdf(pdf_path: str, pages: Optional[List[int]] = None) -> str:
    """
    读取PDF文件的文本内容
    
    Args:
        pdf_path: PDF文件路径
        pages: 指定要读取的页码列表（从1开始），None表示读取全部
        
    Returns:
        PDF的文本内容
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("错误: 未安装 PyMuPDF，请运行: pip install PyMuPDF")
        sys.exit(1)
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    text_parts = []
    
    if pages is None:
        page_range = range(len(doc))
    else:
        page_range = [p - 1 for p in pages if 0 < p <= len(doc)]
    
    for page_num in page_range:
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            text_parts.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
    
    doc.close()
    return "\n\n".join(text_parts)


def read_pdf_metadata(pdf_path: str) -> dict:
    """读取PDF文件的元数据"""
    try:
        import fitz
    except ImportError:
        print("错误: 未安装 PyMuPDF")
        sys.exit(1)
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"文件不存在: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    metadata = {
        "文件名": os.path.basename(pdf_path),
        "页数": len(doc),
        "标题": doc.metadata.get("title", ""),
        "作者": doc.metadata.get("author", ""),
    }
    doc.close()
    return metadata


# ============================================================
# 工具2：导出PDF文件（支持表格）
# ============================================================

# 雅黑字体路径（macOS）
FONT_PATHS = {
    "regular": [
        "/Users/admin/Library/Fonts/MSYH.TTC",
        "/System/Library/Fonts/Supplemental/Microsoft YaHei.ttf",
        "C:/Windows/Fonts/msyh.ttf",
    ],
    "bold": [
        "/Users/admin/Library/Fonts/msyhbd.ttf",
        "/Users/admin/Library/Fonts/MSYHBD.TTC",
        "C:/Windows/Fonts/msyhbd.ttf",
    ],
}


def find_font(variant: str = "regular") -> Optional[str]:
    """查找雅黑字体文件"""
    for path in FONT_PATHS.get(variant, []):
        if os.path.exists(path):
            return path
    return None


def export_pdf_from_markdown(
    md_path: str,
    output_path: Optional[str] = None,
    font_regular: Optional[str] = None,
    font_bold: Optional[str] = None,
) -> str:
    """
    将Markdown文件导出为PDF（支持表格、标题层级、列表）
    
    Args:
        md_path: Markdown文件路径
        output_path: 输出PDF路径（默认与md同名）
        font_regular: 常规字体路径
        font_bold: 粗体字体路径
        
    Returns:
        输出文件路径
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.colors import HexColor
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, KeepTogether, ListFlowable, ListItem
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
    except ImportError as e:
        print(f"错误: 无法导入 reportlab: {e}")
        sys.exit(1)
    
    # 读取markdown
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # 输出路径
    if output_path is None:
        output_path = str(Path(md_path).with_suffix(".pdf"))
    
    # 提取标题
    title = ""
    for line in md_content.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break
    
    # 注册字体
    font_reg = font_regular or find_font("regular")
    font_bld = font_bold or find_font("bold")

    if not font_reg:
        print("警告: 未找到雅黑常规字体，尝试使用苹方")
        font_reg = "/System/Library/Fonts/PingFang.ttc"

    font_name_reg = "YaHeiRegular"
    font_name_bold = "YaHeiBold"

    try:
        pdfmetrics.registerFont(TTFont(font_name_reg, font_reg))
        if font_bld and os.path.exists(font_bld):
            pdfmetrics.registerFont(TTFont(font_name_bold, font_bld))
        else:
            font_name_bold = font_name_reg  # fallback
    except Exception as e:
        print(f"错误: 无法注册字体: {e}")
        sys.exit(1)

    # Emoji 替换方案：将彩色 emoji 替换为简单文本符号
    # Apple Color Emoji 在 reportlab TTFont 中渲染异常（映射到错误字形）
    EMOJI_REPLACEMENTS = {
        '📞': 'Tel:',       # 电话
        '✉️': 'Email:',     # 邮件（含变体选择符）
        '✉': 'Email:',     # 邮件
        '🎂': '',           # 年龄（删除）
        '📍': '',           # 位置（删除）
        '🎓': '',           # 教育（删除）
        '💼': '',           # 经验（删除）
    }

    def replace_emoji(text):
        """将 emoji 替换为文本符号"""
        for emoji, replacement in EMOJI_REPLACEMENTS.items():
            text = text.replace(emoji, replacement)
            # 也处理带变体选择符的版本
            text = text.replace(emoji + '\uFE0F', replacement)
        return text

    def process_markdown(text):
        """处理 Markdown 语法（加粗/斜体/代码/emoji）"""
        text = replace_emoji(text)
        # 加粗 **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # 斜体 *text*
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        # 行内代码 `code`
        text = re.sub(r'`(.+?)`', r'<font color="#e74c3c" face="' + font_name_reg + r'">\1</font>', text)
        return text
    
    # 创建文档
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    
    # 定义样式
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name="DocTitle",
        parent=styles["Title"],
        fontName=font_name_bold,
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=8,
        textColor=HexColor("#1a1a1a"),
        leading=28,
    ))
    
    styles.add(ParagraphStyle(
        name="H1",
        parent=styles["Heading1"],
        fontName=font_name_bold,
        fontSize=15,
        spaceBefore=18,
        spaceAfter=10,
        textColor=HexColor("#1a5276"),
        leading=22,
    ))
    
    styles.add(ParagraphStyle(
        name="H2",
        parent=styles["Heading2"],
        fontName=font_name_bold,
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
        textColor=HexColor("#2c3e50"),
        leading=19,
    ))
    
    styles.add(ParagraphStyle(
        name="H3",
        parent=styles["Heading3"],
        fontName=font_name_bold,
        fontSize=11,
        spaceBefore=10,
        spaceAfter=6,
        textColor=HexColor("#34495e"),
        leading=16,
    ))
    
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontName=font_name_reg,
        fontSize=10,
        alignment=TA_LEFT,
        spaceAfter=5,
        leading=16,
    ))
    
    styles.add(ParagraphStyle(
        name="BulletItem",
        parent=styles["Normal"],
        fontName=font_name_reg,
        fontSize=10,
        leftIndent=18,
        bulletIndent=6,
        spaceAfter=4,
        leading=15,
    ))
    
    styles.add(ParagraphStyle(
        name="TableHeader",
        parent=styles["Normal"],
        fontName=font_name_bold,
        fontSize=9,
        alignment=TA_CENTER,
        textColor=HexColor("#ffffff"),
        leading=14,
    ))
    
    styles.add(ParagraphStyle(
        name="TableCell",
        parent=styles["Normal"],
        fontName=font_name_reg,
        fontSize=9,
        alignment=TA_LEFT,
        leading=13,
    ))
    
    styles.add(ParagraphStyle(
        name="MetaInfo",
        parent=styles["Normal"],
        fontName=font_name_reg,
        fontSize=10,
        spaceAfter=3,
        leading=16,
    ))
    
    # 解析Markdown内容
    story = []
    lines = md_content.split("\n")
    i = 0
    para_buffer = []  # 累积普通段落行

    def process_paragraph(buffer):
        """处理累积的普通段落文本"""
        if not buffer:
            return
        # 合并多行为一个段落
        para_text = " ".join(buffer)
        # Markdown 处理（emoji/加粗/斜体/代码）
        para_text = process_markdown(para_text)
        # 修复中英文混合断行问题：英文单词和中文之间去掉空格
        para_text = re.sub(r'([A-Za-z0-9]+)\s+([\u4e00-\u9fff])', r'\1\2', para_text)
        story.append(Paragraph(para_text, styles["Body"]))

    while i < len(lines):
        line = lines[i]

        # 空行 → 刷新段落缓冲
        if not line.strip():
            process_paragraph(para_buffer)
            para_buffer.clear()
            story.append(Spacer(1, 6))
            i += 1
            continue

        # 水平分隔线 → 刷新缓冲
        if re.match(r'^-{3,}$', line.strip()) or re.match(r'^\*{3,}$', line.strip()):
            process_paragraph(para_buffer)
            para_buffer.clear()
            story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#bdc3c7"), spaceAfter=10))
            i += 1
            continue

        # 标题 # → 刷新缓冲
        if line.startswith("# ") and not line.startswith("##"):
            process_paragraph(para_buffer)
            para_buffer.clear()
            story.append(Paragraph(line[2:].strip(), styles["DocTitle"]))
            i += 1
            continue

        # 标题 ## → 刷新缓冲
        if line.startswith("## ") and not line.startswith("###"):
            process_paragraph(para_buffer)
            para_buffer.clear()
            story.append(Paragraph(line[3:].strip(), styles["H1"]))
            i += 1
            continue

        # 标题 ### → 刷新缓冲
        if line.startswith("### "):
            process_paragraph(para_buffer)
            para_buffer.clear()
            story.append(Paragraph(line[4:].strip(), styles["H2"]))
            i += 1
            continue

        # 引用块 → 刷新缓冲
        if line.startswith("> "):
            process_paragraph(para_buffer)
            para_buffer.clear()
            quote_text = line[2:].strip()
            story.append(Paragraph(f'<i>{quote_text}</i>', styles["Body"]))
            i += 1
            continue

        # 表格解析 → 刷新缓冲
        if "|" in line and i + 1 < len(lines) and re.match(r'^\s*\|?[\s\-:|]+\|', lines[i + 1]):
            process_paragraph(para_buffer)
            para_buffer.clear()
            # 收集表格所有行
            table_lines = []
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1

            # 解析表格数据
            table_data = []
            for tline in table_lines:
                # 跳过分隔行
                if re.match(r'^\s*\|?[\s\-:|]+\|', tline):
                    continue
                cells = [c.strip() for c in tline.split("|")]
                # 去除首尾空单元格
                if cells and cells[0] == "":
                    cells = cells[1:]
                if cells and cells[-1] == "":
                    cells = cells[:-1]
                # Markdown 处理（表格单元格）
                cells = [process_markdown(c) for c in cells]
                if cells:
                    table_data.append(cells)

            if table_data:
                # 构建表格
                header_row = table_data[0]
                body_rows = table_data[1:]

                # 表头（处理 Markdown 语法）
                header_cells = [Paragraph(process_markdown(cell), styles["TableHeader"]) for cell in header_row]

                # 数据行（处理 Markdown 语法）
                grid_data = [header_cells]
                for row in body_rows:
                    # 补齐列数
                    while len(row) < len(header_row):
                        row.append("")
                    row_cells = [Paragraph(process_markdown(cell), styles["TableCell"]) for cell in row[:len(header_row)]]
                    grid_data.append(row_cells)

                # 创建表格（智能列宽）
                col_count = len(header_row)
                table_width = A4[0] - 40 * mm

                # 判断是否为"技术栈全景"表格（第一列窄，第二列宽）
                if col_count == 2 and header_row[0].strip() == "领域":
                    col_widths = [table_width * 0.33, table_width * 0.67]
                else:
                    col_widths = [table_width / col_count] * col_count

                tbl = Table(grid_data, colWidths=col_widths, repeatRows=1)

                # 表格样式
                tbl_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor("#2c3e50")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), HexColor("#ffffff")),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), HexColor("#f8f9fa")),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#dee2e6")),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 6),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ]

                # 交替行颜色
                for idx in range(1, len(grid_data)):
                    if idx % 2 == 0:
                        tbl_style.append(('BACKGROUND', (0, idx), (-1, idx), HexColor("#ffffff")))

                tbl.setStyle(TableStyle(tbl_style))
                story.append(tbl)
                story.append(Spacer(1, 8))
            continue

        # 列表项 → 刷新缓冲
        if re.match(r'^[\s]*[-*•] ', line):
            process_paragraph(para_buffer)
            para_buffer.clear()
            bullet_text = re.sub(r'^[\s]*[-*•] ', '', line)
            # Markdown 处理
            bullet_text = process_markdown(bullet_text)
            # 修复中英文混合断行问题
            bullet_text = re.sub(r'([A-Za-z0-9]+)\s+([\u4e00-\u9fff])', r'\1\2', bullet_text)
            story.append(Paragraph(f"• {bullet_text}", styles["BulletItem"]))
            i += 1
            continue

        # 普通段落 → 累积到缓冲
        para_buffer.append(line.strip())
        i += 1

    # 刷新剩余缓冲
    process_paragraph(para_buffer)
    
    # 构建PDF
    doc.build(story)
    print(f"✅ PDF已导出: {output_path}")
    return output_path


# ============================================================
# CLI 命令行入口
# ============================================================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="PDF工具集：读取/导出PDF")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # 读取PDF
    read_parser = subparsers.add_parser("read", help="读取PDF内容")
    read_parser.add_argument("input", help="输入的PDF文件路径")
    read_parser.add_argument("-p", "--pages", type=int, nargs="+", help="指定页码")
    read_parser.add_argument("-m", "--metadata", action="store_true", help="显示元数据")
    
    # 导出PDF
    export_parser = subparsers.add_parser("export", help="导出PDF文件")
    export_parser.add_argument("input", help="输入的Markdown文件路径")
    export_parser.add_argument("-o", "--output", help="输出的PDF文件路径")
    export_parser.add_argument("-fr", "--font-regular", help="常规字体路径")
    export_parser.add_argument("-fb", "--font-bold", help="粗体字体路径")
    
    args = parser.parse_args()
    
    if args.command == "read":
        if args.metadata:
            meta = read_pdf_metadata(args.input)
            for k, v in meta.items():
                print(f"{k}: {v}")
        else:
            content = read_pdf(args.input, args.pages)
            print(content)
    
    elif args.command == "export":
        export_pdf_from_markdown(
            args.input,
            args.output,
            args.font_regular,
            args.font_bold,
        )
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
