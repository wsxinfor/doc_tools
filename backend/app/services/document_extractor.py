"""从 DOCX 提取结构化内容（文字、图片、表格）。"""

import logging
import re
import uuid
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

logger = logging.getLogger(__name__)

# 跳过原始文档中目录条目的样式前缀（兜底）
_TOC_STYLE_PREFIXES = ("TOC", "目录", "Table of Contents")

# 不应被识别为真实章节标题的文本（目录页标题）
_TOC_TITLES = {"目录", "table of contents", "目  录", "目   录"}

# 匹配图片说明（图N）的正则，用于检测原文是否已有图号
_CAPTION_RE = re.compile(r'^图\s*[\d一二三四五六七八九十百]+')

NS = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}


class DocumentExtractor:
    """从 DOCX 提取结构化内容，保持原有顺序。"""

    def __init__(self, docx_path: str, storage_dir: str = "storage/images"):
        self.docx_path = docx_path
        self.doc = Document(docx_path)
        self.sections = []
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def extract_all(self) -> list[dict]:
        """提取文档所有元素，保持原有顺序。

        返回：
            [
                {"level": 1, "text": "第一章...", "paragraph_type": "heading"},
                {"level": 0, "text": "正文...", "paragraph_type": "body"},
                {"level": 0, "text": "", "paragraph_type": "image", "image_path": "..."},
                {"level": 0, "text": "", "paragraph_type": "table", "table_data": {"rows": [...]}},
            ]
        """
        self._extract_body_elements()
        return self.sections

    def _find_body_start(self, elements: list) -> int:
        """按显式分页符切页，找第一个非封面/非目录页的起始 element index。

        兜底策略：
        - 如果没有检测到任何分页符，改用"内容密度"判断封面页
        - 封面特征：段落少、文本短、关键词（公司/项目/版本/日期）、无 Heading
        """
        # 按 w:br w:type="page" 切割成页面组
        pages: list = []
        cur: list = []
        for idx, el in enumerate(elements):
            cur.append((idx, el))
            if el.tag.split('}')[-1] == 'p':
                for br in el.findall('.//w:br', NS):
                    if br.get(qn('w:type')) == 'page':
                        pages.append(cur)
                        cur = []
                        break
        if cur:
            pages.append(cur)

        # 【兜底 1】如果没有检测到分页符，使用内容分析判断封面页范围
        if len(pages) <= 1:
            return self._find_body_start_by_content(elements)

        # 检查前 3 页，找第一个正文页
        for page in pages[:3]:
            if not self._is_cover_or_toc_page(page):
                return page[0][0]

        # 兜底：超过 3 页仍全是封面/目录，从第 4 页开始
        return pages[3][0][0] if len(pages) > 3 else 0

    def _find_body_start_by_content(self, elements: list) -> int:
        """无分页符时的兜底逻辑：基于内容密度判断封面页范围。

        判断逻辑：
        1. 扫描所有 element，找第一个 Heading 样式标题的位置
        2. 统计封面特征关键词的出现位置
        3. 找第一个"非封面特征"的元素作为正文起点

        返回：
            正文起始 element index
        """
        from docx.text.paragraph import Paragraph as _Paragraph  # noqa: PLC0415

        cover_keywords = {'公司', '名称', '项目', '版本', '日期', '时间', '年', '月', '日', 'V', 'v', 'doc', 'Doc', 'DOC'}
        cover_end_idx = 0  # 封面结束位置
        first_heading_idx = len(elements)  # 第一个标题位置（默认为末尾）
        has_cover_content = False

        for idx, el in enumerate(elements):
            tag = el.tag.split('}')[-1]

            if tag == 'p':
                para = _Paragraph(el, self.doc)
                style_name = para.style.name if para.style else ""
                text = para.text.strip()

                # 检测是否为标题（Heading 样式）
                if style_name.startswith(('标题', 'Heading', 'Head')) and text.lower() not in _TOC_TITLES:
                    first_heading_idx = min(first_heading_idx, idx)
                    # 找到第一个标题，前面就是封面范围
                    break

                # 检测封面特征内容
                if any(kw in text for kw in cover_keywords):
                    has_cover_content = True
                    cover_end_idx = idx

        # 如果有封面特征内容，封面范围到最后一个封面关键词位置
        if has_cover_content:
            return cover_end_idx + 1

        # 如果没有封面特征但找到了标题，从标题开始
        if first_heading_idx < len(elements):
            return first_heading_idx

        # 兜底：都没有找到，从第 1 个元素开始（假设没有封面）
        return 0

    def _is_cover_or_toc_page(self, page_items: list) -> bool:
        """判断该页面组是否为封面页或目录页。

        封面页特征：
        - 无 Heading 样式标题
        - 段落数 <= 30（原 15，放宽到 30 以支持多信息封面）
        - 或包含典型封面元素（公司名称、日期等）
        """
        from docx.text.paragraph import Paragraph as _Paragraph  # noqa: PLC0415

        has_toc = False
        heading_count = 0
        para_count = 0
        has_cover_elements = False  # 封面特征元素

        for _, el in page_items:
            tag = el.tag.split('}')[-1]
            if tag == 'sdt':
                has_toc = True
            elif tag == 'p':
                para_count += 1
                if any('TOC' in (t.text or '')
                       for t in el.findall('.//w:instrText', NS)):
                    has_toc = True
                para = _Paragraph(el, self.doc)
                sn = para.style.name if para.style else ""
                text = para.text.strip()
                if any(sn.startswith(p) for p in _TOC_STYLE_PREFIXES):
                    has_toc = True
                if text.lower().strip() in _TOC_TITLES:
                    has_toc = True
                if (sn.startswith(('标题', 'Heading', 'Head'))
                        and text.lower().strip() not in _TOC_TITLES):
                    heading_count += 1

                # 检测封面典型元素
                if any(keyword in text for keyword in
                       ['公司', '名称', '项目', '版本', '日期', '时间', '年', '月', '日', 'V', 'v']):
                    has_cover_elements = True

        if has_toc:
            return True

        # 封面判定放宽：满足以下任一条件即可
        # 1. 无 Heading 标题且段落 <= 30
        # 2. 有封面典型元素且无 Heading 标题（即使段落较多）
        if heading_count == 0:
            if para_count <= 30:
                return True
            if has_cover_elements and para_count <= 50:
                return True

        return False

    def _extract_body_elements(self):
        """遍历文档主体内容，跳过封面和目录页后提取正文。"""
        body = self.doc._element.body
        elements = list(body)
        start_idx = self._find_body_start(elements)

        # 从正文起点开始提取，跳过 sdt 和 TOC 字段内容
        in_toc_field = False
        for element in elements[start_idx:]:
            tag = element.tag.split('}')[-1]

            if tag == 'sdt':
                # 现代 Word TOC 内容控件，整体跳过
                continue

            if tag == 'p':
                instr_texts = element.findall('.//w:instrText', NS)
                fld_chars   = element.findall('.//w:fldChar',   NS)
                has_toc_instr = any('TOC' in (t.text or '') for t in instr_texts)
                fld_types = [fc.get(qn('w:fldCharType'), '') for fc in fld_chars]

                if not in_toc_field and 'begin' in fld_types and has_toc_instr:
                    in_toc_field = True

                if in_toc_field:
                    if 'end' in fld_types:
                        in_toc_field = False
                    continue

                self._process_paragraph(element)

            elif tag == 'tbl':
                if not in_toc_field:
                    self._process_table(element)

    def _process_paragraph(self, para_element):
        """处理段落元素。"""
        from docx.text.paragraph import Paragraph

        para = Paragraph(para_element, self.doc)
        text = para.text.strip()
        style_name = para.style.name if para.style else ""

        # 跳过原始文档中的目录条目段落
        if any(style_name.startswith(p) for p in _TOC_STYLE_PREFIXES):
            return

        # 1. 先检查段落是否包含图片（嵌入型）
        self._extract_images_from_paragraph(para)

        # 2. 如果本段文字是图片说明（图N...），给最近的 image 节点打标记并跳过
        if text and _CAPTION_RE.match(text):
            for s in reversed(self.sections):
                if s.get("paragraph_type") == "image":
                    s["has_caption"] = True
                    break
            return

        # 3. 判断段落类型并添加节点
        if self._is_heading(style_name, text, para):
            level = self._get_heading_level(style_name, text, para)
            self.sections.append({
                "level": level,
                "text": text,
                "paragraph_type": "heading",
                "children": []
            })
        elif text:
            # 非空正文：记录加粗/黑体特征供 AI 识别使用
            is_bold = False
            is_heiti = False
            if para.runs:
                non_empty_runs = [run for run in para.runs if run.text.strip()]
                if non_empty_runs:
                    is_bold = all(run.font.bold for run in non_empty_runs)
                    is_heiti = any(
                        run.font.name and ('Hei' in run.font.name or 'SimHei' in run.font.name)
                        for run in non_empty_runs
                    )

            self.sections.append({
                "level": 0,
                "text": text,
                "paragraph_type": "body",
                "children": [],
                "is_bold": is_bold,
                "is_heiti": is_heiti,
            })
        # 空段落忽略

    def _is_heading(self, style_name: str, text: str, para=None) -> bool:
        """判断是否为标题。

        判断依据：
        1. Word 样式是标题样式（标题 1, Heading 1 等）
        2. 文本符合标题模式（如"一、xxx"、"1.1 xxx"、"第 x 章 xxx"等）
        3. 【新增】格式检测：加粗/黑体 + 短句/编号 → 标题
        """
        # 1. 样式判断（同时要求不超过 20 字符）
        if style_name and style_name.startswith(('标题', 'Heading', 'Head')) and text and len(text) <= 20:
            return True

        # 2. 文本模式判断（针对样式不规范但内容是标题的情况）
        #    前提：不超过 20 字符
        if text and len(text) <= 20:
            # 中文编号：一、二、三、
            if re.match(r'^[一二三四五六七八九十]+、', text):
                return True
            # 章节编号：第 x 章、第 x 节
            if re.match(r'^第 [一二三四五六七八九十 0-9]+[章节点]', text):
                return True
            # 数字编号：1.1, 1.1.1, 1.2.3.4（不要求后面有空格）
            if re.match(r'^\d+(\.\d+)+', text):
                return True
            # 括号编号：（一）xxx, (1) xxx
            if re.match(r'^[（(][一二三四五六七八九十 0-9]+[)）]', text):
                return True

        # 3. 【新增】格式检测：加粗/黑体 + 短句/编号 → 标题
        if text and para is not None and hasattr(para, 'runs') and para.runs:
            # 检测是否整体加粗（所有非空白 run 都加粗）
            non_empty_runs = [run for run in para.runs if run.text.strip()]
            if non_empty_runs:
                is_bold = all(run.font.bold for run in non_empty_runs)
                # 检测是否使用黑体类字体
                is_heiti = any(
                    run.font.name and ('Hei' in run.font.name or 'SimHei' in run.font.name)
                    for run in non_empty_runs
                )
                # 短句：≤ 20 字符（用户要求：黑体/加粗 20 字以内识别为标题）
                is_short = len(text) <= 20
                # 编号前缀检测（数字、字母、中文数字）
                has_number_prefix = bool(re.match(
                    r'^('
                    r'[0-9]+[.．,、)）]'                    # 1. 1, 1、1) 1）
                    r'|[①-⑩⑪-⑳]'                        # ①②...⑳
                    r'|[（(][一二三四五六七八九十\\d]+[)）]'  # （一）(1)
                    r'|[a-zA-Z][.．,、)）]'                # a. A)
                    r')',
                    text
                ))

                # 判定为标题的条件（按优先级）
                if is_short:
                    # 1. 加粗 + 编号 → 标题（高优先级）
                    if is_bold and has_number_prefix:
                        return True
                    # 2. 黑体 + 编号 → 标题（高优先级）
                    if is_heiti and has_number_prefix:
                        return True
                    # 3. 加粗 + 黑体 → 标题
                    if is_bold and is_heiti:
                        return True
                    # 4. 加粗短句（无编号）→ 标题
                    if is_bold:
                        return True
                    # 5. 黑体短句（无编号）→ 标题
                    if is_heiti:
                        return True

        return False

    def _get_heading_level(self, style_name: str, text: str = "", para=None) -> int:
        """从样式名或文本内容提取标题层级 (1-4)。"""
        # 1. 优先从样式名提取
        if style_name:
            match = re.search(r'(\d)', style_name)
            if match:
                return min(int(match.group(1)), 4)

        # 2. 从文本模式判断
        if text:
            # level 1: 一、xxx, 第 x 章，阶段 X
            if re.match(r'^[一二三四五六七八九十]+、', text):
                return 1
            if re.match(r'^第 [一二三四五六七八九十 0-9]+ 章', text):
                return 1
            if re.match(r'^阶段 [一二三四五六七八九十 0-9]+', text):
                return 1
            if re.match(r'^第 [一二三四五六七八九十 0-9]+ 部分', text):
                return 1

            # level 2: 1.1, （一）, 第 x 节
            if re.match(r'^\d+\.\d+', text):
                return 2
            if re.match(r'^[（(][一二三四五六七八九十]+[)）]', text):
                return 2
            if re.match(r'^第 [一二三四五六七八九十 0-9]+ 节', text):
                return 2

            # level 3: 1.1.1, （1）
            if re.match(r'^\d+\.\d+\.\d+', text):
                return 3
            if re.match(r'^[（(]\d+[)）]', text):
                return 3

            # level 4: 1.1.1.1 或其他小标题
            if re.match(r'^\d+\.\d+\.\d+\.\d+', text):
                return 4

        # 3. 【新增】从格式推断层级（针对加粗/黑体但无编号前缀的短句）
        if para is not None and hasattr(para, 'runs') and para.runs:
            non_empty_runs = [run for run in para.runs if run.text.strip()]
            if non_empty_runs:
                is_bold = all(run.font.bold for run in non_empty_runs)
                is_heiti = any(
                    run.font.name and ('Hei' in run.font.name or 'SimHei' in run.font.name)
                    for run in non_empty_runs
                )
                # 加粗或黑体的短句，根据编号模式再判断一次层级
                if text:
                    if re.match(r'^\d+[.．,、)）]', text):
                        return 2  # 单个数字编号如 "1." 默认为 level 2
                    if re.match(r'^[a-zA-Z][.．,、)）]', text):
                        return 3  # 字母编号如 "a." 默认为 level 3
                # 加粗 + 黑体但无明确编号 → level 4（最小标题）
                if is_bold or is_heiti:
                    return 4

        return 1  # 默认 H1

    def _extract_images_from_paragraph(self, para) -> None:
        """从段落提取嵌入型图片，添加到 sections。"""
        for run in para.runs:
            # 查找 w:drawing 元素
            for drawing in run._element.findall('.//w:drawing', namespaces=NS):
                # 查找图片关系 ID
                blip = drawing.find('.//a:blip', namespaces=NS)
                if blip is not None:
                    embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    if embed_id:
                        # 获取图片二进制
                        image_part = para.part.related_parts.get(embed_id)
                        if image_part and image_part.content_type.startswith('image/'):
                            # 提取图片扩展名
                            content_type = image_part.content_type
                            ext = content_type.split('/')[-1]
                            if ext == 'jpeg':
                                ext = 'jpg'

                            img_path = self._save_image(
                                image_part.blob,
                                ext
                            )
                            self.sections.append({
                                "level": 0,
                                "text": "",
                                "paragraph_type": "image",
                                "image_path": img_path,
                                "children": []
                            })

    def _save_image(self, image_data: bytes, ext: str) -> str:
        """保存图片到 storage，返回相对路径。"""
        img_id = str(uuid.uuid4())
        img_filename = f"{img_id}.{ext}"

        img_path = self.storage_dir / img_filename
        img_path.write_bytes(image_data)

        # 返回相对路径（供后续渲染使用）
        return str(img_path)

    def _process_table(self, tbl_element):
        """处理表格元素。"""
        from docx.table import Table

        table = Table(tbl_element, self.doc)

        rows = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells]
            rows.append(row_data)

        self.sections.append({
            "level": 0,
            "text": "",
            "paragraph_type": "table",
            "table_data": {"rows": rows},
            "children": []
        })

    @staticmethod
    def extract_from_text(text: str, file_type: str) -> list[dict]:
        """从文本内容提取结构

        Args:
            text: MD 或纯文本内容
            file_type: "md" | "txt"

        Returns:
            sections 结构列表
        """
        if file_type == "md":
            from app.services.md_parser import MarkdownParser  # noqa: PLC0415
            parser = MarkdownParser()
            return parser.parse(text)
        else:
            # 纯文本：按空行分段
            return DocumentExtractor._parse_plain_text(text)

    @staticmethod
    def _parse_plain_text(text: str) -> list[dict]:
        """解析纯文本"""
        sections = []
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                sections.append({
                    "level": 0,
                    "text": para.strip(),
                    "paragraph_type": "body",
                    "children": []
                })
        return sections

    def extract_all_with_format_hints(self) -> tuple[list[dict], str]:
        """提取文档结构，同时返回带格式提示的文本（供 AI 识别标题使用）。

        Returns:
            tuple[list[dict], str]: (sections 列表，带格式标记的文本)
            格式标记示例："[B][H] 第一章 项目概述 [/H][/B]\n本项目旨在...\n"
        """
        # 重新初始化，确保 sections 为空
        self.sections = []
        self._extract_body_elements()

        # 构建带格式标记的文本
        format_hints_lines = []
        for sec in self.sections:
            if sec.get("paragraph_type") == "heading":
                # 标题已经识别，用 [H1]/[H2] 等标记
                level = sec.get("level", 1)
                text = sec.get("text", "")
                format_hints_lines.append(f"[H{level}]{text}[/H{level}]")
            elif sec.get("paragraph_type") == "body" and sec.get("text"):
                text = sec.get("text", "")
                # 检查是否有加粗/黑体特征（基于原始检测逻辑）
                if sec.get("is_bold"):
                    format_hints_lines.append(f"[B]{text}[/B]")
                elif sec.get("is_heiti"):
                    format_hints_lines.append(f"[H]{text}[/H]")
                else:
                    format_hints_lines.append(text)
            else:
                # 表格/图片/空段落，用占位符标记
                ptype = sec.get("paragraph_type")
                format_hints_lines.append(f"[{ptype.upper()}]")

        return self.sections, '\n'.join(format_hints_lines)

    @staticmethod
    def merge_ai_headings(sections: list[dict], ai_result: list[dict]) -> list[dict]:
        """将 AI 识别的标题信息合并到 sections。

        Args:
            sections: 原始 sections 列表（可能没有标题或标题很少）
            ai_result: AI 识别结果，每项包含 {index, is_heading, level, ...}

        Returns:
            合并后的 sections 列表
        """
        if not ai_result:
            return sections

        # 创建 index -> ai_result 映射
        ai_map = {item["index"]: item for item in ai_result if isinstance(item, dict)}

        result = []
        for i, sec in enumerate(sections):
            new_sec = dict(sec)  # 浅拷贝

            # 如果 AI 认为这是标题，更新段落类型和层级
            if i in ai_map:
                ai_item = ai_map[i]
                if ai_item.get("is_heading"):
                    new_sec["paragraph_type"] = "heading"
                    new_sec["level"] = ai_item.get("level", 1)
                    # 确保有 children 字段
                    if "children" not in new_sec:
                        new_sec["children"] = []
                else:
                    # AI 认为是正文，确保 paragraph_type 为 body
                    new_sec["paragraph_type"] = "body"
                    new_sec["level"] = 0

            result.append(new_sec)

        return result

    @staticmethod
    def has_insufficient_headings(sections: list[dict]) -> bool:
        """判断当前 sections 是否标题不足，需要 AI 介入。

        判断标准：
        1. 完全没有标题
        2. 标题数量 < 总段落数的 5%
        3. 标题数量 < 2 且文档长度 > 10 段
        """
        if not sections:
            return True

        heading_count = sum(1 for s in sections if s.get("paragraph_type") == "heading")
        total_count = len(sections)

        # 完全没有标题
        if heading_count == 0:
            return True

        # 标题比例过低
        if total_count > 10 and heading_count < total_count * 0.05:
            return True

        # 标题绝对数量过少但文档较长
        if heading_count < 2 and total_count > 20:
            return True

        return False
