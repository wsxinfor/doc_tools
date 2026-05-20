"""排版引擎核心服务（M5）。

执行步骤：
1. 解析 ai_structure 章节树
2. 创建 python-docx Document
3. 应用页面设置（A4 + 页边距）
4. 生成封面页
5. 分页符
6. 生成目录占位页
7. 分页符
8. 逐章节写入正文（h1/h2 前分页）
9. 设置页眉页脚
10. 保存 .docx
11. 生成 HTML 预览
12. 更新 RenderTask status=done
"""
import logging
import re
import uuid
from pathlib import Path
from typing import Any

import docx as _docx_module
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.render_task import RenderTask

logger = logging.getLogger(__name__)

_ALIGN_MAP = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
}


class HeadingNumberingGenerator:
    """标题编号生成器，维护各级别计数器。"""

    CHN_NUM = "零一二三四五六七八九"

    def __init__(self):
        self.counters = [0, 0, 0, 0, 0]  # 索引 0 不用，1-4 对应 H1-H4

    def reset_level(self, level: int) -> None:
        """重置某级别及所有子级别的计数器。"""
        for i in range(level, 5):
            self.counters[i] = 0

    def increment(self, level: int) -> None:
        """递增某级别计数器，并重置所有子级别。"""
        self.counters[level] += 1
        self.reset_level(level + 1)

    def get_numbering(self, level: int, style: str) -> str:
        """获取指定级别和样式的编号字符串（用于静态编号回退）。"""
        if level == 1:
            return self._get_h1_numbering(self.counters[1], style)
        elif style == "decimal":
            return self._get_decimal_numbering(level)
        return ""

    def _get_h1_numbering(self, num: int, style: str) -> str:
        """获取一级标题编号。"""
        if style == "chapter-arabic":
            return f"第{num}章"
        elif style == "chapter-chinese":
            return f"第{self._to_chinese(num)}章"
        elif style == "cn-number":
            return f"{self._to_chinese(num)}、"
        elif style == "arabic-number":
            return f"{num}、"
        return ""

    def _get_decimal_numbering(self, level: int) -> str:
        """获取十进制编号（如 1.1、1.1.1）。"""
        parts = [str(self.counters[i]) for i in range(1, level + 1)]
        return ".".join(parts)

    def _to_chinese(self, num: int) -> str:
        """将阿拉伯数字转为中文数字（1-99）。"""
        if num <= 10:
            return self.CHN_NUM[num]
        if num < 100:
            tens = num // 10
            ones = num % 10
            result = ""
            if tens > 1:
                result += self.CHN_NUM[tens] + "十"
            else:
                result = "十"
            if ones > 0:
                result += self.CHN_NUM[ones]
            return result
        return str(num)


def _create_multilevel_numbering(doc: Any, headings_cfg: dict) -> int:
    """在文档的 numbering.xml 中创建多级编号定义。

    创建一个包含 4 级（H1-H4）的层级式多级列表定义：
    - H1: 第1章, 第2章, ...
    - H2: 1.1, 1.2, 2.1, 2.2, ... (随 H1 重置)
    - H3: 1.1.1, 2.2.1, 3.2.1, ... (随 H2 重置)
    - H4: 1.1.1.1, ... (随 H3 重置)

    每个级别的编号字体、大小、颜色从 headings_cfg 中读取。
    Word 原生编号，用户删除/插入标题后自动重新编号。
    """
    numbering_el = doc.part.numbering_part.element  # type: ignore[attr-defined]
    # 清除 python-docx 默认的单级列表定义，避免冲突
    for child in list(numbering_el):
        numbering_el.remove(child)

    abstract_num = OxmlElement("w:abstractNum")
    abstract_num.set(qn("w:abstractNumId"), "0")

    # hybridMultilevel：自动在高层级变化时重新开始计数
    ml = OxmlElement("w:multiLevelType")
    ml.set(qn("w:val"), "hybridMultilevel")
    abstract_num.append(ml)

    lvl_configs = [
        # (ilvl, lvl_text, indent_left, h_key, heading_style)
        # 注意：pStyle 值必须与 python-docx add_heading() 使用的样式名完全一致（含空格）
        (0, "第%1章  ",      0, "h1", "Heading 1"),
        (1, "%1.%2.  ",      0, "h2", "Heading 2"),
        (2, "%1.%2.%3.  ",   0, "h3", "Heading 3"),
        (3, "%1.%2.%3.%4.  ", 0, "h4", "Heading 4"),
    ]

    for ilvl, lvl_text, indent, h_key, heading_style in lvl_configs:
        lvl = OxmlElement("w:lvl")
        lvl.set(qn("w:ilvl"), str(ilvl))

        start = OxmlElement("w:start")
        start.set(qn("w:val"), "1")
        lvl.append(start)

        num_fmt = OxmlElement("w:numFmt")
        num_fmt.set(qn("w:val"), "decimal")
        lvl.append(num_fmt)

        lt = OxmlElement("w:lvlText")
        lt.set(qn("w:val"), lvl_text)
        lvl.append(lt)

        jc = OxmlElement("w:lvlJc")
        jc.set(qn("w:val"), "left")
        lvl.append(jc)

        # 段落格式
        p_pr = OxmlElement("w:pPr")
        # 关键：将级别链接到对应的 Heading 样式，让 Word 识别层级关系
        p_style = OxmlElement("w:pStyle")
        p_style.set(qn("w:val"), heading_style)
        p_pr.append(p_style)
        tabs = OxmlElement("w:tabs")
        tab = OxmlElement("w:tab")
        tab.set(qn("w:val"), "num")
        tab.set(qn("w:pos"), str(indent))
        tabs.append(tab)
        p_pr.append(tabs)
        ind = OxmlElement("w:ind")
        ind.set(qn("w:left"), str(indent))
        if ilvl > 0:
            ind.set(qn("w:firstLine"), str(0))
        p_pr.append(ind)
        lvl.append(p_pr)

        # 编号的字体和颜色：与对应标题的字体配置一致
        h_cfg = headings_cfg.get(h_key, {})
        font_cfg = h_cfg.get("font", {})
        r_pr = OxmlElement("w:rPr")
        fonts = OxmlElement("w:rFonts")
        fonts.set(qn("w:ascii"), font_cfg.get("en_font", "Times New Roman"))
        fonts.set(qn("w:hAnsi"), font_cfg.get("en_font", "Times New Roman"))
        r_pr.append(fonts)
        sz_val = int(font_cfg.get("size", 16) * 2)  # pt → half-points
        sz = OxmlElement("w:sz")
        sz.set(qn("w:val"), str(sz_val))
        r_pr.append(sz)
        # 颜色
        color_hex = font_cfg.get("color", "#000000")
        color = OxmlElement("w:color")
        color.set(qn("w:val"), color_hex.lstrip("#").upper())
        r_pr.append(color)
        # 加粗
        if font_cfg.get("bold", False):
            b = OxmlElement("w:b")
            b.set(qn("w:val"), "true")
            r_pr.append(b)
        lvl.append(r_pr)

        abstract_num.append(lvl)

    numbering_el.append(abstract_num)

    # num 实例（numId=1）
    num_el = OxmlElement("w:num")
    num_el.set(qn("w:numId"), "1")
    abs_ref = OxmlElement("w:abstractNumId")
    abs_ref.set(qn("w:val"), "0")
    num_el.append(abs_ref)
    numbering_el.append(num_el)

    return 1


def _apply_native_numbering(paragraph: Any, ilvl: int, num_id: int) -> None:
    """为段落应用 Word 原生多级编号。

    Args:
        paragraph: python-docx Paragraph 对象
        ilvl: 级别索引（0=H1, 1=H2, 2=H3, 3=H4）
        num_id: 编号定义 ID（来自 _create_multilevel_numbering 的返回值）
    """
    p_pr = paragraph._p.get_or_add_pPr()  # noqa: SLF001

    num_pr = OxmlElement("w:numPr")

    ilvl_el = OxmlElement("w:ilvl")
    ilvl_el.set(qn("w:val"), str(ilvl))
    num_pr.append(ilvl_el)

    num_id_el = OxmlElement("w:numId")
    num_id_el.set(qn("w:val"), str(num_id))
    num_pr.append(num_id_el)

    p_pr.append(num_pr)


def _strip_existing_numbering(text: str) -> str:
    """去除标题文本中已有的编号前缀。"""
    # 注意：模式顺序很重要 - 更具体的长模式必须在前
    patterns = [
        # "第 X 章"、"第 X 节"、"第 X 条" - X 可以是阿拉伯数字或任何中文字符
        r"^第.+章\s*",
        r"^第.+节\s*",
        r"^第.+条\s*",
        r"^第.+條\s*",  # 繁体
        # 中文数字 + 顿号（一、二、三、）
        r"^[\u4e00-\u9fff]+、",
        # 多级数字编号（必须在单级之前）
        r"^\d+\.\d+\.\d+\.\d+",
        r"^\d+\.\d+\.\d+",
        r"^\d+\.\d+",
        # 单级数字 + 标点（阿拉伯数字 + 顿号/句点/逗号，全角或半角）
        # 顿号 Unicode 是 U+3001
        r"^\d+[\u3001,.,]",
        # "（一）"、"(1)" 等形式
        r"^[（(][\d\u4e00-\u9fff]+[)）]",
    ]
    for pattern in patterns:
        match = re.match(pattern, text)
        if match:
            return text[match.end():].strip()
    return text

# 页脚固定内容（照搬 1.docx）
_FOOTER_ADDRESS = "\u5317\u4eac\u5e02\u6000\u67d4\u533a\u4e50\u56ed\u897f\u5927\u885713\u53f7\u966228\u53f7\u697c1\u5c42"
_FOOTER_TEL = "Tel\uff1a010-82843001"
_FOOTER_BORDER_COLOR = "622423"
_LOGO_PATH = Path(__file__).parent.parent / "static" / "footer_logo.png"
# Logo 尺寸（照搬 1.docx 原始值，单位 EMU）
_LOGO_W = 485775
_LOGO_H = 385445

# 封面字体配置
_COVER_TITLE_FONT = {
    "cn_font": "SimHei",      # 黑体
    "en_font": "SimHei",
    "size": 24,               # 小初
    "color": "#000000",
    "bold": False,
}

_COVER_BODY_FONT = {
    "cn_font": "SimSun",      # 宋体
    "en_font": "SimSun",
    "size": 14,               # 四号
    "color": "#000000",
    "bold": False,
}

# 表格样式配置
_TABLE_HEADER_FONT = {
    "cn_font": "SimSun",      # 宋体
    "en_font": "Times New Roman",
    "size": 12,               # 小四
    "color": "#000000",
    "bold": False,
}

_TABLE_BODY_FONT = {
    "cn_font": "FangSong",    # 仿宋
    "en_font": "Times New Roman",
    "size": 12,               # 小四
    "color": "#000000",
    "bold": False,
}

_TABLE_HEADER_BG = "D6E7F5"   # 浅蓝色


def _hex_to_rgb(hex_color: str) -> RGBColor:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return RGBColor(r, g, b)


def _apply_font(run: Any, font_cfg: dict) -> None:
    run.font.name = font_cfg.get("en_font", "Times New Roman")
    run.font.size = Pt(font_cfg.get("size", 12))
    run.font.bold = font_cfg.get("bold", False)
    run.font.italic = font_cfg.get("italic", False)
    run.font.underline = font_cfg.get("underline", False)
    color_hex = font_cfg.get("color", "#000000")
    try:
        run.font.color.rgb = _hex_to_rgb(color_hex)
    except Exception:
        pass
    # 中文字体（East Asian font）
    cn_font = font_cfg.get("cn_font")
    if cn_font:
        rPr = run._r.get_or_add_rPr()  # noqa: SLF001
        rFonts = rPr.find(qn("w:rFonts"))
        if rFonts is None:
            rFonts = OxmlElement("w:rFonts")
            rPr.insert(0, rFonts)
        rFonts.set(qn("w:eastAsia"), cn_font)


def _apply_heading_style(p: Any, h_cfg: dict) -> None:
    """对标题段落应用模板中的字体和段落间距配置。"""
    font_cfg = h_cfg.get("font", {})
    for run in p.runs:
        _apply_font(run, font_cfg)
    # 段落间距
    spacing_cfg = h_cfg.get("spacing", {})
    if spacing_cfg:
        pPr = p._p.get_or_add_pPr()  # noqa: SLF001
        sp = OxmlElement("w:spacing")
        if "before" in spacing_cfg:
            sp.set(qn("w:before"), str(int(spacing_cfg["before"] * 20)))  # pt → twips
        if "after" in spacing_cfg:
            sp.set(qn("w:after"), str(int(spacing_cfg["after"] * 20)))
        if "line" in spacing_cfg:
            sp.set(qn("w:line"), str(int(spacing_cfg["line"] * 240)))  # 倍数 → twips
            sp.set(qn("w:lineRule"), "auto")
        pPr.append(sp)


def _add_page_break(doc: Any) -> None:
    p = doc.add_paragraph()
    run = p.add_run()
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run._r.append(br)  # noqa: SLF001


def _make_field_run(instr: str, bold: bool = False) -> Any:
    """创建包含 Word 字段的一组 XML runs（begin / instrText / separate / placeholder / end）。"""
    runs = []

    def _run_with(*children: Any, bold: bool = False) -> Any:
        r = OxmlElement("w:r")
        rPr = OxmlElement("w:rPr")
        lang = OxmlElement("w:lang")
        lang.set(qn("w:val"), "zh-CN")
        rPr.append(lang)
        if bold:
            b_el = OxmlElement("w:b")
            rPr.append(b_el)
        r.append(rPr)
        for child in children:
            r.append(child)
        return r

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    runs.append(_run_with(begin, bold=bold))

    instr_el = OxmlElement("w:instrText")
    instr_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instr_el.text = instr
    runs.append(_run_with(instr_el, bold=bold))

    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    runs.append(_run_with(sep, bold=bold))

    placeholder = OxmlElement("w:t")
    placeholder.text = "?"
    runs.append(_run_with(placeholder, bold=bold))

    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    runs.append(_run_with(end, bold=bold))

    return runs


def _add_footer_logo_floating(p: Any) -> None:
    """将 logo 作为浮动图片插入段落（照搬 1.docx 定位方式）。
    先用 add_picture 注册图片资源取得 rId，再把 inline 改为 anchor。
    """
    from lxml import etree  # noqa: PLC0415

    if not _LOGO_PATH.exists():
        return

    tmp_run = p.add_run()
    try:
        tmp_run.add_picture(str(_LOGO_PATH), width=Emu(_LOGO_W), height=Emu(_LOGO_H))
    except Exception:
        logger.warning("Footer logo insert failed")
        p._p.remove(tmp_run._r)  # noqa: SLF001
        return

    NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
    NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
    NS_R_ATTR = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"

    r_el = tmp_run._r  # noqa: SLF001
    drawing = next((c for c in r_el if etree.QName(c).localname == "drawing"), None)
    if drawing is None:
        return

    inline = drawing.find(f"{{{NS_WP}}}inline")
    if inline is None:
        return

    blip = inline.find(f".//{{{NS_A}}}blip")
    rId = blip.get(NS_R_ATTR) if blip is not None else ""

    graphic = inline.find(f"{{{NS_A}}}graphic")
    drawing.remove(inline)

    anchor_str = (
        f'<wp:anchor xmlns:wp="{NS_WP}"'
        ' distT="0" distB="0" distL="114300" distR="114300"'
        ' simplePos="0" relativeHeight="251659264" behindDoc="0"'
        ' locked="0" layoutInCell="1" allowOverlap="1">'
        "<wp:simplePos x=\"0\" y=\"0\"/>"
        '<wp:positionH relativeFrom="column">'
        "<wp:posOffset>142875</wp:posOffset></wp:positionH>"
        '<wp:positionV relativeFrom="paragraph">'
        "<wp:posOffset>78740</wp:posOffset></wp:positionV>"
        f'<wp:extent cx="{_LOGO_W}" cy="{_LOGO_H}"/>'
        '<wp:effectExtent l="0" t="0" r="9525" b="0"/>'
        "<wp:wrapNone/>"
        '<wp:docPr id="100" name="FooterLogo"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="{NS_A}" noChangeAspect="1"/>'
        "</wp:cNvGraphicFramePr>"
        "</wp:anchor>"
    )
    anchor = etree.fromstring(anchor_str)
    if graphic is not None:
        anchor.append(graphic)
    drawing.append(anchor)


def _set_para_spacing_zero(p: Any) -> None:
    """将段落段前段后间距设为 0，行距设为单倍。"""
    pPr = p._p.get_or_add_pPr()  # noqa: SLF001
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), "0")
    spacing.set(qn("w:after"), "0")
    spacing.set(qn("w:line"), "240")
    spacing.set(qn("w:lineRule"), "auto")
    pPr.append(spacing)


def _add_footer_top_border(p: Any, with_indent: bool = True) -> None:
    """为段落添加深红色上边框（照搬 1.docx 页脚样式）。
    with_indent=False 时只加边框，不加首行缩进（用于 logo 行）。
    """
    pPr = p._p.get_or_add_pPr()  # noqa: SLF001
    pBdr = OxmlElement("w:pBdr")
    top = OxmlElement("w:top")
    top.set(qn("w:val"), "thinThickSmallGap")
    top.set(qn("w:color"), _FOOTER_BORDER_COLOR)
    top.set(qn("w:sz"), "24")
    top.set(qn("w:space"), "1")
    pBdr.append(top)
    pPr.append(pBdr)
    if with_indent:
        ind = OxmlElement("w:ind")
        ind.set(qn("w:firstLine"), "1080")
        ind.set(qn("w:firstLineChars"), "600")
        pPr.append(ind)


def _add_paragraph_with_spacing(
    doc: Any,
    text: str = "",
    space_before_cm: float = 0,
    alignment: str = "center",
) -> Any:
    """添加段落，并设置段前间距（单位 cm）。"""
    p = doc.add_paragraph(text)
    p.alignment = _ALIGN_MAP.get(alignment, WD_ALIGN_PARAGRAPH.CENTER)
    if space_before_cm > 0:
        pPr = p._p.get_or_add_pPr()
        spacing = OxmlElement("w:spacing")
        # cm → twips: 1cm ≈ 567 twips
        spacing.set(qn("w:before"), str(int(space_before_cm * 567)))
        pPr.append(spacing)
    return p


def _add_table(doc: Any, table_data: list[list[str]], table_cfg: dict) -> None:
    """添加表格并应用样式。

    Args:
        doc: python-docx Document 对象
        table_data: 表格数据，二维数组
        table_cfg: 表格配置，来自模板
    """
    if not table_data or len(table_data) < 1:
        return

    num_rows = len(table_data)
    num_cols = max(len(row) for row in table_data) if table_data else 0
    if num_cols == 0:
        return

    table = doc.add_table(rows=num_rows, cols=num_cols)
    table.style = "Table Grid"

    # 设置表格外框（前端传 pt 单位，需转换为 1/8pt）
    border_color = table_cfg.get("border_color", "auto")
    border_outer_pt = table_cfg.get("border_width_outer", 1.5)  # 前端默认 1.5pt
    border_inner_pt = table_cfg.get("border_width_inner", 0.5)  # 前端默认 0.5pt
    border_outer = int(border_outer_pt * 8)  # 转换为 1/8pt 单位
    border_inner = int(border_inner_pt * 8)  # 转换为 1/8pt 单位
    _set_table_borders(table, border_color, border_outer, border_inner)

    # 判断第一行是否为表头：如果第一行有单元格文本超过 20 字符，则不是表头
    first_row = table_data[0] if table_data else []
    has_header = False
    if first_row:
        max_cell_len = max(len(str(cell)) for cell in first_row)
        has_header = (max_cell_len <= 20)

    # 标记首行为表头（跨页重复）
    if has_header and table_cfg.get("repeat_header", True):
        _mark_table_header(table.rows[0])

    # 填充数据并设置样式
    for i, row_data in enumerate(table_data):
        tbl_row = table.rows[i]
        is_header = (has_header and i == 0)
        for j, cell_text in enumerate(row_data):
            cell = tbl_row.cells[j]
            _set_cell_style(cell, cell_text=cell_text or "", is_header=is_header, is_first_col=(j == 0), table_cfg=table_cfg)


def _set_table_borders(table: Any, color: str = "auto", sz_outer: int = 12, sz_inner: int = 4) -> None:
    """设置表格边框。

    Args:
        table: python-docx Table 对象
        color: 边框颜色，"auto" 或 hex 色值
        sz_outer: 外框宽度（单位 1/8pt），默认 12 = 1.5pt
        sz_inner: 内框宽度（单位 1/8pt），默认 4 = 0.5pt
    """
    tbl_borders = OxmlElement("w:tblBorders")

    # 外边框
    for border_name in ["top", "left", "bottom", "right"]:
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), "single")
        border.set(qn("w:sz"), str(sz_outer))
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), color)
        tbl_borders.append(border)

    # 内部细线
    insideH = OxmlElement("w:insideH")
    insideH.set(qn("w:val"), "single")
    insideH.set(qn("w:sz"), str(sz_inner))
    insideH.set(qn("w:space"), "0")
    insideH.set(qn("w:color"), color)
    tbl_borders.append(insideH)

    insideV = OxmlElement("w:insideV")
    insideV.set(qn("w:val"), "single")
    insideV.set(qn("w:sz"), str(sz_inner))
    insideV.set(qn("w:space"), "0")
    insideV.set(qn("w:color"), color)
    tbl_borders.append(insideV)

    # 获取或创建 tblPr，然后插入 tblBorders
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)

    # 移除已有的 tblBorders（如果有）
    existing_borders = tblPr.find(".//w:tblBorders", namespaces={'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'})
    if existing_borders is not None:
        tblPr.remove(existing_borders)

    tblPr.append(tbl_borders)


def _mark_table_header(row: Any) -> None:
    """标记为表头行，实现跨页重复显示。"""
    tr_el = row._tr
    trPr = tr_el.get_or_add_trPr()

    # 添加 w:tblHeader 标记
    tblHeader = OxmlElement("w:tblHeader")
    trPr.append(tblHeader)


# 已有序号前缀的正则：匹配则不加小三角
_SEQUENTIAL_PREFIX_RE = re.compile(
    r'^('
    r'\d+[.．、\)）]'                               # 1. 1、1) 1）（含全角句点）
    r'|[①-⑩⑪-⑳]'                                # ①②...⑳
    r'|[（(][一二三四五六七八九十\d]+[)）]'          # （一）(1)
    r'|第[一二三四五六七八九十\d]+[条款项步点、]'    # 第一条 第1步 第一、
    r'|[a-zA-Z][.．）\)]'                           # a. b) A.
    r'|[-—·•►➢→▶▪◆]'                             # 符号 bullet
    r'|▶\s*\d+\s*[:：]'                            # ▶ 1: ▶ 2：这种组合编号
    r'|\d+\s*[:：\-．]\s*\S'                        # 数字 + 冒号/句点 + 内容（如 1: xxx 1. xxx）
    r'|\d+\s+\S'                                   # 数字 + 空格 + 内容（如 1 xxx 2 商超）
    r')'
)


_BULLET_SYMBOL_MAP = {
    "triangle": "\u25b6 ",
    "diamond": "\u25c6 ",
    "circle": "\u25cf ",
    "hollow_diamond": "\u25c7 ",
    "square": "\u25a0 ",
    "dot": "\u25aa ",
}


def _group_short_body_sections(sections: list, list_style: str = "none") -> list:
    """将同级 sections 按"连续短正文"分组。

    连续 3+ 个 paragraph_type==body 且 len(text)<=80 的段落归为 ('triangle', [...])，
    其余每项单独归为 ('normal', [item])。已有序号前缀的段落不参与 triangle 分组。
    当 list_style 为 "none" 时，不触发分组，所有段落按普通正文渲染。
    """
    if list_style == "none":
        return [("normal", [s]) for s in sections]

    groups: list = []
    i = 0
    while i < len(sections):
        sec = sections[i]
        text = sec.get("text", "")
        if (
            sec.get("paragraph_type") == "body"
            and len(text) <= 80
            and not _SEQUENTIAL_PREFIX_RE.match(text)
        ):
            run: list = []
            while (
                i < len(sections)
                and sections[i].get("paragraph_type") == "body"
                and len(sections[i].get("text", "")) <= 80
                and not _SEQUENTIAL_PREFIX_RE.match(sections[i].get("text", ""))
            ):
                run.append(sections[i])
                i += 1
            if len(run) >= 3:
                groups.append(("triangle", run))
            else:
                for s in run:
                    groups.append(("normal", [s]))
        else:
            groups.append(("normal", [sec]))
            i += 1
    return groups


def _add_bullet_paragraph(doc: Any, text: str, body_cfg: dict, symbol: str = "\u25b6 ") -> None:
    """添加列表符号段落（2字符悬挂缩进，0.5倍行距）。"""
    p = doc.add_paragraph(style="List Paragraph")
    font_cfg = body_cfg.get("font", {})
    bullet_run = p.add_run(symbol)
    _apply_font(bullet_run, font_cfg)
    text_run = p.add_run(text)
    _apply_font(text_run, font_cfg)

    pPr = p._p.get_or_add_pPr()

    # 2字符左缩进 + 悬挂缩进（字符单位，随字体大小自适应）
    ind = OxmlElement("w:ind")
    ind.set(qn("w:leftChars"), "200")
    ind.set(qn("w:left"), "480")
    ind.set(qn("w:hangingChars"), "200")
    ind.set(qn("w:hanging"), "480")
    pPr.append(ind)

    # 1.5倍行距
    sp = OxmlElement("w:spacing")
    sp.set(qn("w:line"), "360")
    sp.set(qn("w:lineRule"), "auto")
    pPr.append(sp)


def _add_image_caption(doc: Any, num: int, body_cfg: dict, figure_cfg: dict | None = None, current_chapter: int | None = None) -> None:
    """在图片下方添加居中编号标注。

    Args:
        doc: python-docx Document 对象
        num: 图片在当前章节内的序号
        body_cfg: 正文配置（用于字体）
        figure_cfg: 图表配置（可选）
        current_chapter: 当前章节号（可选，用于"图 X-Y"格式）
    """
    # 获取图片编号格式配置
    caption_style = figure_cfg.get("caption_style", "simple") if figure_cfg else "simple"

    # 生成编号文本
    if caption_style == "chapter-figure" and current_chapter is not None:
        # 图 X-Y 格式（带章节号）
        caption_text = f"图{current_chapter}-{num}"
    else:
        # 简单格式：图 N
        caption_text = f"图{num}"

    p = doc.add_paragraph(caption_text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if p.runs:
        run = p.runs[0]
        # 使用配置的说明文字体
        caption_font_cfg = figure_cfg.get("caption_font", {}) if figure_cfg else {}
        _apply_font(run, caption_font_cfg)
        # 默认五号字（10.5pt）
        if not caption_font_cfg.get("size"):
            run.font.size = Pt(10.5)


def _add_image_to_doc(doc: Any, image_path: str) -> None:
    """在文档中插入图片（居中，页面可用宽度的 85%，段前 0.5cm）。"""
    from pathlib import Path

    # 检查图片是否存在
    img_path = Path(image_path)
    if not img_path.exists():
        logging.warning("Image not found: %s", image_path)
        return

    # 添加图片段落
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Cm(0.5)

    # 计算可用宽度的 85%
    sec = doc.sections[0]
    usable_w = sec.page_width - sec.left_margin - sec.right_margin
    pic_width = int(usable_w * 0.85)

    run = p.add_run()
    try:
        run.add_picture(str(img_path), width=pic_width)
    except Exception as e:
        logging.error("Failed to add image %s: %s", image_path, e)


def _set_cell_style(cell: Any, cell_text: str, is_header: bool, is_first_col: bool, table_cfg: dict) -> None:
    """设置单元格样式。

    Args:
        cell: 单元格对象
        cell_text: 单元格文本
        is_header: 是否为表头行
        is_first_col: 是否为第一列
        table_cfg: 表格配置
    """
    # 获取段落
    p = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()

    # 清除段落原有 runs（通过 XML 删除）
    for run in list(p.runs):
        p._p.remove(run._r)

    # 添加文本 run
    run = p.add_run(cell_text)

    # 设置字体：根据表头/表体/首列选择配置
    if is_header:
        font_cfg = table_cfg.get("header_font", {})
    elif is_first_col:
        font_cfg = table_cfg.get("first_col_font", {}) or table_cfg.get("body_font", {})
    else:
        font_cfg = table_cfg.get("body_font", {})
    _apply_font(run, font_cfg)

    # 设置水平对齐
    if is_header:
        alignment = table_cfg.get("header_alignment", "center")
    elif is_first_col:
        alignment = table_cfg.get("first_col_alignment", "center")
    else:
        alignment = table_cfg.get("body_alignment", "left")
    p.alignment = _ALIGN_MAP.get(alignment, WD_ALIGN_PARAGRAPH.LEFT)

    # 设置垂直对齐
    v_alignment = table_cfg.get("header_v_alignment", "center") if is_header else table_cfg.get("body_v_alignment", "center")
    if v_alignment == "center":
        _set_cell_vcenter(cell)
    elif v_alignment == "top":
        _set_cell_valign(cell, "top")
    else:
        _set_cell_valign(cell, "bottom")

    # 设置表头背景色
    if is_header:
        bg_color = table_cfg.get("header_bg_color", "#D6E7F5")
        _set_cell_bg(cell, bg_color)

    # 自动换行（列宽自适应）
    _set_cell_autofit(cell)


def _set_cell_vcenter(cell: Any) -> None:
    """设置单元格垂直居中。"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    vAlign = OxmlElement("w:vAlign")
    vAlign.set(qn("w:val"), "center")
    tcPr.append(vAlign)


def _set_cell_valign(cell: Any, valign: str) -> None:
    """设置单元格垂直对齐（top/center/bottom）。"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    vAlign = OxmlElement("w:vAlign")
    vAlign.set(qn("w:val"), valign)
    tcPr.append(vAlign)


def _set_cell_bg(cell: Any, color_hex: str) -> None:
    """设置单元格背景色。"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tcPr.append(shd)


def _remove_first_line_indent(p: Any) -> None:
    """移除段落首行缩进。"""
    pPr = p._p.get_or_add_pPr()
    ind = pPr.find(qn("w:ind"))
    if ind is not None:
        # 删除首行缩进属性
        ind.set(qn("w:firstLine"), None)
        ind.set(qn("w:firstLineChars"), None)


def _set_cell_autofit(cell: Any) -> None:
    """设置单元格自动换行。"""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()

    # 设置列宽为 auto
    tcW = OxmlElement("w:tcW")
    tcW.set(qn("w:w"), "0")
    tcW.set(qn("w:type"), "auto")
    tcPr.append(tcW)


def _build_cover(doc: Any, cover_cfg: dict, render_params: dict) -> None:
    """生成封面页。

    布局：
    - 10% 处：客户名称（黑体 30pt）
    - 40% 处：项目名称（黑体 小初）
    - 首页底部：公司名称、日期、版本号（宋体 四号，行距 7pt）
    """
    from datetime import datetime  # noqa: PLC0415

    # 允许模板覆盖字体配置（补充方式）
    title_font_cfg = {**_COVER_TITLE_FONT}
    body_font_cfg = {**_COVER_BODY_FONT}

    cover_title_cfg = cover_cfg.get("title_font", {})
    if cover_title_cfg:
        title_font_cfg.update(cover_title_cfg)

    cover_body_cfg = cover_cfg.get("body_font", {})
    if cover_body_cfg:
        body_font_cfg.update(cover_body_cfg)

    # ── 第 1 行：客户名称（10% 处，距封面起始 2cm）────────
    client_name = render_params.get("client_name", "")
    p = _add_paragraph_with_spacing(doc, client_name, space_before_cm=2)
    run = p.runs[0] if p.runs else p.add_run()
    _apply_font(run, title_font_cfg)
    run.font.size = Pt(30)  # 客户名称单独使用 30pt

    # ── 第 2 行：项目名称（30% 处，再推 6cm）────────
    project_name = render_params.get("project_name", "")
    p = _add_paragraph_with_spacing(doc, project_name, space_before_cm=6)
    run = p.runs[0] if p.runs else p.add_run()
    _apply_font(run, title_font_cfg)
    run.font.size = Pt(30)  # 项目名称使用 30pt

    # ── 第 3 行：公司名称（首页底部，空一行后再推 6cm）────────
    doc.add_paragraph()  # 空一行
    p = _add_paragraph_with_spacing(doc, settings.DEFAULT_COMPANY_NAME, space_before_cm=6)
    _apply_font(p.runs[0] if p.runs else p.add_run(), body_font_cfg)

    # ── 第 4 行：日期（下一行，行距 7pt ≈ 0.25cm）────────
    date_str = datetime.now().strftime("%Y年%m月%d日")
    p = _add_paragraph_with_spacing(doc, date_str, space_before_cm=0.25)
    _apply_font(p.runs[0] if p.runs else p.add_run(), body_font_cfg)

    # ── 第 5 行：版本号（下一行，行距 7pt）────────
    version = render_params.get("doc_version", "").strip()
    if not version:
        version = "v1"
    p = _add_paragraph_with_spacing(doc, version, space_before_cm=0.25)
    _apply_font(p.runs[0] if p.runs else p.add_run(), body_font_cfg)


def _fill_toc_entries(doc: Any, sections: list, max_level: int) -> None:
    """在文档末尾追加目录条目段落（放在 TOC 字段 separate/end 之间）。"""
    for sec in sections:
        if sec.get("paragraph_type") != "heading":
            continue
        level = sec.get("level", 1)
        if level > max_level:
            continue
        text = sec.get("text", "").strip()
        if not text:
            continue

        p = doc.add_paragraph()
        indent_cm = (level - 1) * 0.4
        if indent_cm > 0:
            p.paragraph_format.left_indent = Cm(indent_cm)

        run_text = p.add_run(text)
        if level == 1:
            run_text.bold = True

        p.add_run("\t")
        run_page = p.add_run("...")
        run_page.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

        children = sec.get("children", [])
        if children:
            _fill_toc_entries(doc, children, max_level)


def _build_toc(doc: Any, toc_cfg: dict, sections: list) -> None:
    """插入 Word TOC 字段并预填充标题条目，打开文档后可直接看到目录。"""
    title_text = toc_cfg.get("title_text", "\u76ee  \u5f55")
    max_level = int(toc_cfg.get("max_level", 3))

    p_title = doc.add_paragraph(title_text)
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p = doc.add_paragraph()
    run = p.add_run()

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    begin.set(qn("w:dirty"), "true")
    run._r.append(begin)  # noqa: SLF001

    run2 = p.add_run()
    instr = OxmlElement("w:instrText")
    instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instr.text = f' TOC \\o "1-{max_level}" \\h \\z \\u '
    run2._r.append(instr)  # noqa: SLF001

    run3 = p.add_run()
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    run3._r.append(sep)  # noqa: SLF001

    # 预填充目录条目（独立段落），打开文档即可见
    _fill_toc_entries(doc, sections, max_level)

    # end fldChar 放在新段落
    p_end = doc.add_paragraph()
    run_end = p_end.add_run()
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run_end._r.append(end)  # noqa: SLF001


def _set_page_margins(doc: Any, margins: dict) -> None:
    section = doc.sections[0]
    section.top_margin = Cm(margins.get("top", 2.54))
    section.bottom_margin = Cm(margins.get("bottom", 2.54))
    section.left_margin = Cm(margins.get("left", 3.17))
    section.right_margin = Cm(margins.get("right", 3.17))


def _set_header_footer(doc: Any, hf_cfg: dict, render_params: dict, margins_cfg: dict | None = None) -> None:
    """设置页眉页脚。
    页眉：左=客户名称，右=项目名称（精确 tab stop，不超出页边距）。
    页脚：完全照搬 1.docx 格式（logo+公司名 / 地址+页码 / Tel）。
    """
    if margins_cfg is None:
        margins_cfg = {}
    section = doc.sections[0]
    section.different_first_page_header_footer = hf_cfg.get("first_page_hide", True)
    # 页脚向下偏移 0.5cm
    section.footer_distance = Cm(0.5)

    # ── 页眉 ──────────────────────────────────────────────────────
    client_name = render_params.get("client_name", "")
    project_name = render_params.get("project_name", "")

    hdr = section.header
    hdr_para = hdr.paragraphs[0] if hdr.paragraphs else hdr.add_paragraph()
    hdr_para.clear()
    # 必须先把段落样式改为 Normal，否则 Header 样式自带的居中 tab stop 仍然生效，
    # 导致 \t 落到居中位置而非我们设定的右对齐位置。
    try:
        hdr_para.style = doc.styles["Normal"]
    except KeyError:
        pass

    # 计算文本区宽度（twips），设单一右对齐 tab stop
    left_cm = margins_cfg.get("left", 3.17)
    right_cm = margins_cfg.get("right", 3.17)
    text_width_twips = int((21.0 - left_cm - right_cm) * 567)

    pPr = hdr_para._p.get_or_add_pPr()  # noqa: SLF001
    tabs_el = OxmlElement("w:tabs")
    tab_right = OxmlElement("w:tab")
    tab_right.set(qn("w:val"), "right")
    tab_right.set(qn("w:pos"), str(text_width_twips))
    tabs_el.append(tab_right)
    pPr.append(tabs_el)

    hdr_para.add_run(client_name)
    if project_name:
        hdr_para.add_run("\t")
        hdr_para.add_run(project_name)

    # 页眉下方横线（单线，默认粗细）
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "4")
    bottom.set(qn("w:space"), "0")
    bottom.set(qn("w:color"), "auto")
    pBdr.append(bottom)
    pPr.append(pBdr)

    # ── 页脚（照搬 1.docx）───────────────────────────────────────
    ftr = section.footer

    # 清空已有段落（保留第一个）
    existing = ftr.paragraphs
    for p in existing[1:]:
        p._p.getparent().remove(p._p)  # noqa: SLF001

    # 行1：浮动 logo（左侧固定位置）+ 公司名称（有缩进，与后续行对齐）
    p0 = existing[0]
    p0.clear()
    _add_footer_top_border(p0, with_indent=True)   # 恢复缩进，与行2/3对齐
    _set_para_spacing_zero(p0)
    _add_footer_logo_floating(p0)                   # logo 浮动在左边
    run_name = p0.add_run(settings.DEFAULT_COMPANY_NAME)
    run_name.font.name = "Cambria"

    # 行2：地址 + 空格 + PAGE / NUMPAGES（不加边框，只加与行1相同的首行缩进）
    p1 = ftr.add_paragraph()
    _set_para_spacing_zero(p1)
    pPr1 = p1._p.get_or_add_pPr()  # noqa: SLF001
    ind1 = OxmlElement("w:ind")
    ind1.set(qn("w:firstLine"), "1080")
    ind1.set(qn("w:firstLineChars"), "600")
    pPr1.append(ind1)
    run_addr = p1.add_run(f"{_FOOTER_ADDRESS}  ")
    run_addr.font.name = "Cambria"
    spaces_run = p1.add_run("                      ")
    spaces_run.font.name = "Cambria"
    for r in _make_field_run("PAGE  \\* Arabic  \\* MERGEFORMAT", bold=True):
        p1._p.append(r)  # noqa: SLF001
    sep_run = OxmlElement("w:r")
    sep_rPr = OxmlElement("w:rPr")
    sep_lang = OxmlElement("w:lang")
    sep_lang.set(qn("w:val"), "zh-CN")
    sep_rPr.append(sep_lang)
    sep_run.append(sep_rPr)
    sep_t = OxmlElement("w:t")
    sep_t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    sep_t.text = " / "
    sep_run.append(sep_t)
    p1._p.append(sep_run)  # noqa: SLF001
    for r in _make_field_run("NUMPAGES  \\* Arabic  \\* MERGEFORMAT", bold=True):
        p1._p.append(r)  # noqa: SLF001

    # 行3：Tel
    p2 = ftr.add_paragraph()
    _set_para_spacing_zero(p2)
    pPr2 = p2._p.get_or_add_pPr()  # noqa: SLF001
    ind2 = OxmlElement("w:ind")
    ind2.set(qn("w:firstLine"), "1080")
    ind2.set(qn("w:firstLineChars"), "600")
    pPr2.append(ind2)
    p2.add_run(_FOOTER_TEL)

    # 行4：空行
    p3 = ftr.add_paragraph()
    _set_para_spacing_zero(p3)
    pPr3 = p3._p.get_or_add_pPr()  # noqa: SLF001
    ind3 = OxmlElement("w:ind")
    ind3.set(qn("w:right"), "1260")
    pPr3.append(ind3)


def _apply_body_paragraph_format(p: Any, body_cfg: dict) -> None:
    """对正文段落应用首行缩进和行距等段落格式。"""
    pPr = p._p.get_or_add_pPr()  # noqa: SLF001

    # 首行缩进（单位：字符数 → firstLineChars）
    indent_chars = body_cfg.get("first_line_indent", 0)
    if indent_chars:
        ind = OxmlElement("w:ind")
        ind.set(qn("w:firstLineChars"), str(int(indent_chars * 100)))
        pPr.append(ind)

    # ���落间距
    spacing_cfg = body_cfg.get("spacing", {})
    if spacing_cfg:
        sp = OxmlElement("w:spacing")
        if "before" in spacing_cfg:
            sp.set(qn("w:before"), str(int(float(spacing_cfg["before"]) * 20)))
        if "after" in spacing_cfg:
            sp.set(qn("w:after"), str(int(float(spacing_cfg["after"]) * 20)))
        if "line" in spacing_cfg:
            sp.set(qn("w:line"), str(int(float(spacing_cfg["line"]) * 240)))
            sp.set(qn("w:lineRule"), "auto")
        pPr.append(sp)


def _write_body_text(doc: Any, text: str, body_cfg: dict) -> None:
    """将文��写为正文段落（有换行按行拆段，否则整段写入）��"""
    font_cfg = body_cfg.get("font", {})
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines and text.strip():
        lines = [text.strip()]
    for line in lines:
        p = doc.add_paragraph(line)
        for run in p.runs:
            _apply_font(run, font_cfg)
        _apply_body_paragraph_format(p, body_cfg)


def _write_document_text_first(
    doc: Any,
    clean_text: str,
    sections: list,
    headings_cfg: dict,
    body_cfg: dict,
) -> None:
    """以 clean_text 为主体写正文，用 ai_structure 的标题树确定标题层级和分隔位置。"""
    numbering_gen = HeadingNumberingGenerator()

    heading_map: dict[str, int] = {}

    def _collect(secs: list) -> None:
        for s in secs:
            if s.get("paragraph_type") == "heading":
                t = (s.get("text") or "").strip()
                if t:
                    heading_map[t] = int(s.get("level", 1))
            _collect(s.get("children", []))

    _collect(sections)

    if not heading_map:
        _write_body_text(doc, clean_text, body_cfg)
        return

    # 在 clean_text 中定位每个标题的起始/结束位置
    # 跳过目录条目：目录中标题后紧跟"空格+页码数字"，而正文中标题后是真实内容
    _toc_page_re = re.compile(r"^\d+(?:\s|$)")
    heading_positions: list[tuple[int, int, str, int]] = []
    for htext, hlevel in heading_map.items():
        search_from = 0
        while True:
            pos = clean_text.find(htext, search_from)
            if pos == -1:
                break
            after = clean_text[pos + len(htext) : pos + len(htext) + 15].lstrip()
            if _toc_page_re.match(after):
                # 目录条目，跳过，继续找下一个出现位置
                search_from = pos + len(htext)
                continue
            heading_positions.append((pos, pos + len(htext), htext, hlevel))
            break

    heading_positions.sort(key=lambda x: x[0])

    if not heading_positions:
        # 标题在文本中找不到，退回为全文正文
        _write_body_text(doc, clean_text, body_cfg)
        return

    # 标题前的内容
    pre_text = clean_text[: heading_positions[0][0]].strip()
    if pre_text:
        _write_body_text(doc, pre_text, body_cfg)

    # 逐标题写入（应用自动编号）
    for i, (start, end, htext, hlevel) in enumerate(heading_positions):
        h_key = f"h{hlevel}"
        h_cfg = headings_cfg.get(h_key, {})

        # 递增计数器并生成编号
        numbering_gen.increment(hlevel)
        numbering_style = h_cfg.get("numbering_style", "none")
        numbering = numbering_gen.get_numbering(hlevel, numbering_style)

        # 去除原始编号并合并
        clean_heading_text = _strip_existing_numbering(htext)
        final_text = f"{numbering} {clean_heading_text}" if numbering else clean_heading_text

        # 按模板配置决定是否分页
        if h_cfg.get("page_break_before", False):
            _add_page_break(doc)
        p = doc.add_heading(final_text, level=min(hlevel, 4))
        p.alignment = _ALIGN_MAP.get(h_cfg.get("alignment", "left"), WD_ALIGN_PARAGRAPH.LEFT)
        _apply_heading_style(p, h_cfg)

        next_start = heading_positions[i + 1][0] if i + 1 < len(heading_positions) else len(clean_text)
        body_segment = clean_text[end:next_start].strip()
        if body_segment:
            _write_body_text(doc, body_segment, body_cfg)


def _write_sections(
    doc: Any,
    sections: list,
    headings_cfg: dict,
    body_cfg: dict,
    figure_cfg: dict,
    _had_content: bool = True,
    _img_counter: list | None = None,
    _numbering_gen: HeadingNumberingGenerator | None = None,
    _num_id: int = 0,
) -> None:
    """渲染章节列表。

    Args:
        doc: python-docx Document 对象
        sections: 章节列表
        headings_cfg: 标题配置
        body_cfg: 正文配置
        figure_cfg: 图表配置（用于表格样式）
        _had_content: 调用前是否已写入过正文/表格/图片内容
        _img_counter: 图片计数器
        _numbering_gen: 标题编号生成器
        _num_id: Word 原生多级编号定义 ID（0=未设置，使用静态编号）
    """
    if _numbering_gen is None:
        _numbering_gen = HeadingNumberingGenerator()

    had_content = _had_content
    if _img_counter is None:
        _img_counter = [0]
    list_style = body_cfg.get("list_style", "none")
    bullet_symbol = _BULLET_SYMBOL_MAP.get(list_style, "\u25b6 ")
    for group_type, group_items in _group_short_body_sections(sections, list_style):
        if group_type == "triangle":
            for sec in group_items:
                _add_bullet_paragraph(doc, sec.get("text", ""), body_cfg, bullet_symbol)
            had_content = True
        else:
            sec = group_items[0]
            level = sec.get("level", 1)
            text = sec.get("text", "")
            para_type = sec.get("paragraph_type", "body")
            children = sec.get("children", [])

            if para_type == "heading":
                h_key = f"h{level}"
                h_cfg = headings_cfg.get(h_key, {})

                # 递增计数器并生成编号（用于静态编号回退）
                _numbering_gen.increment(level)
                numbering_style = h_cfg.get("numbering_style", "none")

                # 去除原始编号
                clean_text = _strip_existing_numbering(text)

                # 当启用原生编号（_num_id > 0）时，所有标题都使用 Word 原生多级编号
                # Word 自动管理计数器，删除/插入标题后自动重新编号
                use_native = _num_id > 0

                if use_native:
                    final_text = clean_text
                else:
                    # 静态文本编号回退
                    numbering = _numbering_gen.get_numbering(level, numbering_style)
                    final_text = f"{numbering} {clean_text}" if numbering else clean_text

                # 只有前面有实际内容时才分页，标题紧跟标题则不分页，且模板配置了分页
                if h_cfg.get("page_break_before", False) and had_content:
                    _add_page_break(doc)

                heading_level = min(level, 4)
                p = doc.add_heading(final_text, level=heading_level)
                alignment = h_cfg.get("alignment", "left")
                p.alignment = _ALIGN_MAP.get(alignment, WD_ALIGN_PARAGRAPH.LEFT)
                _apply_heading_style(p, h_cfg)

                # 应用 Word 原生多级编号
                if use_native:
                    _apply_native_numbering(p, level - 1, _num_id)

                had_content = False

                if children:
                    _write_sections(doc, children, headings_cfg, body_cfg, figure_cfg, _had_content=False, _img_counter=_img_counter, _numbering_gen=_numbering_gen, _num_id=_num_id)

            elif para_type == "table":
                table_data = sec.get("table_data", {}).get("rows", [])
                if table_data:
                    table_cfg = figure_cfg.get("table", {})
                    _add_table(doc, table_data, table_cfg)
                had_content = True

            elif para_type == "image":
                image_path = sec.get("image_path", "")
                if image_path:
                    _add_image_to_doc(doc, image_path)
                    if not sec.get("has_caption"):
                        _img_counter[0] += 1
                        # 使用当前章节号（从标题计数器获取）
                        chapter_num = _numbering_gen.counters[1] if _numbering_gen.counters[1] > 0 else None
                        _add_image_caption(doc, _img_counter[0], body_cfg, figure_cfg, chapter_num)
                had_content = True

            else:
                p = doc.add_paragraph(text)
                font_cfg = body_cfg.get("font", {})
                for run in p.runs:
                    _apply_font(run, font_cfg)
                _apply_body_paragraph_format(p, body_cfg)
                had_content = True


def _merge_template_config(template_config: dict, render_params: dict) -> dict:
    """合并模板配置和用户单次排版参数。

    优先级规则（从高到低）：
    1. render_params：用户单次排版时的临时参数（来自前端确认页）
    2. template_config：模板保存的配置（JSONB 存储）
    3. 硬编码默认值：render_service.py 中的默认配置

    Args:
        template_config: 模板配置（来自数据库）
        render_params: 用户单次排版参数（来自前端）

    Returns:
        合并后的配置字典
    """
    # 深度合并，保留 template_config 中未被 render_params 覆盖的部分
    merged = {}

    # 遍历 template_config 的每个模块
    for key in ["cover", "header_footer", "headings", "toc", "body", "figure"]:
        tmpl_value = template_config.get(key, {})
        render_value = render_params.get(key, {})

        if isinstance(tmpl_value, dict) and isinstance(render_value, dict):
            # 对 headings 做二级深度合并（h1/h2/h3/h4 各自合并）
            if key == "headings":
                all_sub_keys = set(list(tmpl_value.keys()) + list(render_value.keys()))
                merged[key] = {}
                for sub_key in all_sub_keys:
                    t = tmpl_value.get(sub_key, {})
                    r = render_value.get(sub_key, {})
                    if isinstance(t, dict) and isinstance(r, dict):
                        merged[key][sub_key] = {**t, **r}
                    else:
                        merged[key][sub_key] = r if r else t
            else:
                # 其他模块：浅层合并
                merged[key] = {**tmpl_value, **render_value}
        else:
            # 非字典类型：render_params 完全覆盖
            merged[key] = render_value if render_value else tmpl_value

    return merged


def execute_render(task: RenderTask, template_config: dict, render_params: dict) -> tuple[str, str]:
    """执行排版，返回 (result_path, preview_path)。"""
    # 合并配置（render_params 优先级更高）
    merged_config = _merge_template_config(template_config, render_params)

    # 应用后端默认值（仅填充缺失字段，不覆盖模板已有值）
    headings_cfg = merged_config.get("headings", {})
    for h_key in ["h1", "h2", "h3", "h4"]:
        if h_key not in headings_cfg:
            headings_cfg[h_key] = {}
        headings_cfg[h_key].setdefault("page_break_before", h_key == "h1")
    merged_config["headings"] = headings_cfg

    body_cfg_merged = merged_config.get("body", {})
    body_cfg_merged.setdefault("list_style", "none")
    merged_config["body"] = body_cfg_merged

    output_dir = Path(settings.OUTPUT_DIR) / str(task.created_by)
    output_dir.mkdir(parents=True, exist_ok=True)

    task_id = str(task.id)
    docx_path = output_dir / f"{task_id}.docx"
    preview_path = output_dir / f"{task_id}_preview.html"

    doc: Any = _docx_module.Document()  # type: ignore[attr-defined]  # python-docx factory fn

    # 页面设置
    body_cfg: dict = merged_config.get("body", {})
    margins_cfg: dict = body_cfg.get("margins", {})
    _set_page_margins(doc, margins_cfg)

    # 封面
    cover_cfg: dict = merged_config.get("cover", {})
    _build_cover(doc, cover_cfg, render_params)
    _add_page_break(doc)

    # 正文 sections（目录预填充和正文渲染都需要）
    ai_structure: dict = task.ai_structure or {}
    sections: list = ai_structure.get("sections", [])

    # 创建 Word 原生多级编号定义（用于 decimal 编号样式）
    num_id = _create_multilevel_numbering(doc, headings_cfg)

    # 目录
    toc_cfg: dict = merged_config.get("toc", {})
    _build_toc(doc, toc_cfg, sections)
    _add_page_break(doc)
    headings_cfg: dict = merged_config.get("headings", {})
    figure_cfg: dict = merged_config.get("figure", {})
    _write_sections(doc, sections, headings_cfg, body_cfg, figure_cfg, _num_id=num_id)

    # 页眉页脚
    hf_cfg: dict = merged_config.get("header_footer", {})
    _set_header_footer(doc, hf_cfg, render_params, margins_cfg)

    # 设置 updateFields，Word 打开时自动更新目录（find-or-create，避免重复）
    settings_el = doc.settings.element
    existing_uf = settings_el.find(qn("w:updateFields"))
    if existing_uf is not None:
        existing_uf.set(qn("w:val"), "true")
    else:
        update = OxmlElement("w:updateFields")
        update.set(qn("w:val"), "true")
        settings_el.append(update)

    doc.save(str(docx_path))
    logger.info("Saved docx: %s", docx_path)

    # HTML 预览
    from app.services.preview_service import generate_html_preview  # noqa: PLC0415

    html = generate_html_preview(str(docx_path))
    preview_path.write_text(html, encoding="utf-8")
    logger.info("Saved preview: %s", preview_path)

    return str(docx_path), str(preview_path)


def run_render_task(db: Session, task_id: uuid.UUID) -> None:
    """后台任务入口：执行排版并更新 RenderTask 状态。"""
    task: RenderTask | None = db.query(RenderTask).filter(RenderTask.id == task_id).first()
    if task is None:
        logger.error("RenderTask %s not found", task_id)
        return

    task.status = "processing"
    db.commit()

    try:
        from app.models.template import Template  # noqa: PLC0415

        tmpl: Template | None = db.query(Template).filter(Template.id == task.template_id).first()
        if tmpl is None:
            raise ValueError(f"Template {task.template_id} not found")

        render_params: dict = task.ai_structure.get("render_params", {}) if task.ai_structure else {}

        result_path, preview_path = execute_render(task, tmpl.config, render_params)

        task.result_path = result_path
        task.preview_path = preview_path
        task.status = "done"
        db.commit()
        logger.info("RenderTask %s done", task_id)

    except Exception as exc:
        logger.error("RenderTask %s failed: %s", task_id, exc, exc_info=True)
        task.status = "failed"
        task.error_message = str(exc)
        db.commit()
