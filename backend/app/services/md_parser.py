"""Markdown 解析器 - 将 MD 转换为结构化 sections."""

import re
from typing import Any


class MarkdownParser:
    """解析 Markdown 内容为结构化数据"""

    def parse(self, text: str) -> list[dict]:
        """
        解析 MD 文本，返回 sections 结构

        Args:
            text: Markdown 文本内容

        Returns:
            sections 列表，每项包含：
            - level: 标题层级 (1-6)，正文为 0
            - text: 文本内容
            - paragraph_type: "heading" | "body" | "table"
            - children: 子节点列表
            - table_data: 表格数据（仅 table 类型）
        """
        sections = []
        lines = text.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # 1. 检测标题 (# 到 ######)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                sections.append({
                    "level": level,
                    "text": heading_match.group(2).strip(),
                    "paragraph_type": "heading",
                    "children": []
                })
                i += 1
                continue

            # 2. 检测表格（| 开头）
            if line.strip().startswith('|') and '|' in line.strip()[1:]:
                table_data, consumed = self._parse_table(lines, i)
                if table_data and len(table_data.get("rows", [])) > 0:
                    sections.append({
                        "level": 0,
                        "text": "",
                        "paragraph_type": "table",
                        "table_data": table_data,
                        "children": []
                    })
                i += consumed
                continue

            # 3. 检测图片 ![alt](url) - 忽略
            if re.match(r'^!\[.*\]\(.*\)$', line.strip()):
                i += 1
                continue

            # 4. 检测代码块 ``` - 作为普通段落处理
            if line.strip().startswith('```'):
                i += 1
                # 跳过代码块内容
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    i += 1
                i += 1
                continue

            # 5. 普通段落（非空行）
            if line.strip():
                sections.append({
                    "level": 0,
                    "text": line.strip(),
                    "paragraph_type": "body",
                    "children": []
                })

            i += 1

        return sections

    def _parse_table(self, lines: list, start: int) -> tuple[dict, int]:
        """
        解析 MD 表格

        MD 表格格式：
        | 表头 1 | 表头 2 |
        |---|---|
        | 内容 1 | 内容 2 |

        Args:
            lines: 所有行
            start: 表格起始行索引

        Returns:
            (table_data, consumed_lines)
            table_data: {"rows": [[cell1, cell2], ...]}
            consumed_lines: 消耗的行数
        """
        rows = []
        i = start

        # 收集所有表格行
        while i < len(lines):
            line = lines[i].strip()

            # 检查是否为表格行（以 | 开头且包含 |）
            if not (line.startswith('|') and '|' in line[1:]):
                break

            # 检查是否为分隔行 |---|---|
            if re.match(r'^\|?[\s\-:|]+\|?$', line):
                i += 1
                continue

            # 解析单元格：去掉首尾 |，分割，去空格
            cells = [cell.strip() for cell in line.split('|')]
            # 去掉空的首尾单元格（因为 | A | B | 会分割出 ['', 'A', 'B', '']）
            if cells and cells[0] == '':
                cells = cells[1:]
            if cells and cells[-1] == '':
                cells = cells[:-1]

            if cells:  # 非空行
                rows.append(cells)

            i += 1

        consumed = i - start
        return {"rows": rows}, max(consumed, 1)


def detect_markdown(text: str) -> bool:
    """
    检测文本是否为 Markdown 格式

    检测特征：
    - 有 # 标题语法
    - 有 **粗体** 或 *斜体*
    - 有 [链接](url) 语法
    - 有 | 表格语法
    - 有 ``` 代码块
    - 有 - 或 * 列表
    - 有 > 引用

    Args:
        text: 待检测文本

    Returns:
        bool: 是否为 Markdown 格式
    """
    if len(text) < 10:
        return False

    patterns = [
        r'^#{1,6}\s+',           # 标题 # ##
        r'\*\*.*?\*\*',          # 粗体 **text**
        r'\*.*?\*',              # 斜体 *text*
        r'\[.*?\]\(.*?\)',       # 链接 [text](url)
        r'^\|.*\|',              # 表格 | row |
        r'^```',                 # 代码块
        r'^[\-\*]\s+',           # 无序列表 - item
        r'^\d+\.\s+',            # 有序列表 1. item
        r'^>\s+',                # 引用 > quote
    ]

    for pattern in patterns:
        if re.search(pattern, text, re.MULTILINE):
            return True

    return False
