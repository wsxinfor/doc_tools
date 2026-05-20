# DocFormat 架构说明

> 智能文档排版工具 — 核心流程、模板系统、关键代码链路

---

## 一、核心流程架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DocFormat 核心流程                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. 上传原文件                                                           │
│     ↓                                                                   │
│  2. 识别阶段（AI + 本地）                                                │
│     ├── 2.1 封面/目录识别 → 跳过（DocumentExtractor._find_body_start） │
│     ├── 2.2 标题识别 → 样式 + 格式 + 文本模式（DocumentExtractor）      │
│     ├── 2.3 表格识别 → 框架提取（DocumentExtractor._process_table）    │
│     ├── 2.4 图片识别 → 提取 + 编号（DocumentExtractor._extract_images）│
│     └── 2.5 AI 清洗/结构修正 → ai_service.correct_structure            │
│     ↓                                                                   │
│  3. 用户确认结构（前端 AIProcess 页面）                                   │
│     └── 可调整标题层级、确认章节树                                        │
│     ↓                                                                   │
│  4. 选择模板                                                              │
│     ├── 4.1 固定内容（后端硬编码）                                        │
│     │   ├── 封面布局：client_name, project_name, doc_version...        │
│     │   ├── 页脚固定：logo + 地址 + Tel                                 │
│     │   └── 公司名：DEFAULT_COMPANY_NAME                               │
│     └── 4.2 可编辑内容（Template.config JSONB）                          │
│         ├── cover: 封面字段字体/位置/背景色                              │
│         ├── header_footer: 页眉文本来源、页脚样式                        │
│         ├── headings: h1-h4 字体/编号/段前段后                           │
│         ├── toc: 目录最大层级/标题样式                                   │
│         ├── body: 正文字体/段落/缩进/页边距                              │
│         └── figure: 图表样式（表格表头/表体/边框）                       │
│     ↓                                                                   │
│  5. 排版引擎（render_service.py）                                        │
│     ├── execute_render() → 合并 template_config + render_params         │
│     ├── _build_cover() → 生成封面                                       │
│     ├── _build_toc() → 生成目录占位                                     │
│     ├── _write_sections() → 逐章节渲染（核心）                          │
│     └── _set_header_footer() → 设置页眉页脚                              │
│     ↓                                                                   │
│  6. 预览 & 导出                                                           │
│     ├── 生成 HTML 预览（preview_service.py）                              │
│     └── 下载 .docx 文件                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.1 数据流转

```
用户上传 DOCX
    ↓
DocumentExtractor.extract_all()
    → sections: [{level, text, paragraph_type, children}, ...]
    ↓
AI 结构识别（异步任务）
    → ai_structure: { sections: [...], title: "..." }
    ↓
用户确认/调整（前端 AIProcess 页面）
    ↓
选择模板 + render_params
    ↓
RenderTask 创建（status=pending）
    ↓
后台任务 run_render_task()
    ↓
execute_render(task, template_config, render_params)
    ↓
生成 .docx + HTML 预览
    ↓
RenderTask status=done
```

---

## 二、模板系统分析

### 2.1 三层优先级架构

```
优先级从高到低：
1. render_params（用户单次排版时的临时参数，来自前端确认页）
2. template_config（模板保存的配置，JSONB 存储）
3. 硬编码常量（render_service.py 中的 _FOOTER_* 等）
```

### 2.2 模板配置结构

```python
TemplateConfig:
├── cover              # 封面配置
│   ├── client_name    # 甲方名称字段
│   ├── project_name   # 项目名字段
│   ├── doc_version    # 文档版本字段
│   ├── company_name   # 公司名称字段
│   ├── date           # 日期字段
│   ├── bg_color       # 背景色
│   └── logo_path      # logo 路径
│
├── header_footer      # 页眉页脚配置
│   ├── header_left    # 【未使用】实际用 client_name
│   ├── header_right   # 【未使用】实际用 project_name
│   ├── footer_*       # 【未使用】页脚固定格式
│   └── first_page_hide # 首页隐藏页眉
│
├── headings           # 标题配置（h1-h4）
│   ├── font           # 字体
│   ├── spacing        # 段前段后
│   ├── alignment      # 对齐
│   ├── numbering_style # 编号样式
│   └── page_break_before # 页前分页
│
├── toc                # 目录配置
│   ├── max_level      # 最大层级
│   ├── title_text     # 目录标题（默认"目  录"）
│   └── separate_page  # 独立成页
│
├── body               # 正文配置
│   ├── font           # 字体
│   ├── spacing        # 行距
│   ├── first_line_indent # 首行缩进
│   └── margins        # 页边距
│
└── figure             # 图表配置
    ├── image_alignment # 图片对齐
    ├── caption_font   # 说明文字体
    └── table          # 表格样式
        ├── header_font, body_font
        ├── header_bg_color
        ├── header_alignment, body_alignment
        ├── header_v_alignment, body_v_alignment
        ├── border_width_outer/inner  # pt 单位（前端）
        └── repeat_header
```

### 2.3 未使用/冗余字段

| 字段 | 说明 | 状态 |
|-----|------|-----|
| `header_footer.header_left/center/right` | 页眉文本 | 未使用，实际用 client_name/project_name |
| `header_footer.footer_*` | 页脚文本 | 未使用，页脚固定格式 |
| `table.first_col_font` | 表格首列特殊样式 | 保留（用户可能需要） |

### 2.4 封面/页脚固定内容

```python
# 页脚固定内容（照搬 1.docx）
_FOOTER_ADDRESS = "北京市怀柔区乐园西大街 13 号院 28 号楼 1 层"
_FOOTER_TEL = "Tel：010-82843001"
_FOOTER_BORDER_COLOR = "622423"
_LOGO_PATH = Path(__file__).parent.parent / "static" / "footer_logo.png"

# 公司名称（封面）
DEFAULT_COMPANY_NAME = "北京昱华源码科技有限公司"
```

---

## 三、关键代码链路

### 3.1 排版引擎调用链

```
run_render_task (后台任务)
  ↓
execute_render(task, template_config, render_params)
  ↓
_build_cover(doc, cover_cfg, render_params)     # 封面
_build_toc(doc, toc_cfg, sections)              # 目录
_write_sections(doc, sections, headings_cfg, body_cfg, figure_cfg)  # 正文
  ├─ _add_triangle_bullet_paragraph()           # 三角形项目符号
  ├─ _add_page_break()                          # 分页
  ├─ _add_table(doc, table_data, table_cfg)     # 表格（动态表头检测）
  └─ _add_image_to_doc()                        # 图片
  ↓
_set_header_footer(doc, hf_cfg, render_params)  # 页眉页脚
  ↓
doc.save() + generate_html_preview()
```

### 3.2 文档提取流程（DocumentExtractor）

```python
# 1. 找正文起点（跳过封面/目录）
_find_body_start(elements)
  ├─ 按 w:br page 分页符切页
  ├─ 检查前 3 页是否为封面/目录
  └─ 返回第一个正文页 index

_is_cover_or_toc_page(page_items)
  ├─ 检测 TOC 字段（sdt 元素、TOC 指令）
  ├─ 检测 Heading 样式标题
  ├─ 检测封面特征元素（公司/项目/版本/日期）
  └─ 判定：无 Heading + 段落≤30 或有封面元素

# 2. 提取章节
_process_paragraph(para)
  ├─ 跳过 TOC 条目
  ├─ 提取嵌入型图片 → _extract_images_from_paragraph()
  ├─ 检测图片说明（图 N...）→ 给最近 image 打 has_caption 标记
  ├─ 判断标题 → _is_heading() / _get_heading_level()
  └─ 添加 section 节点

# 3. 处理表格
_process_table(tbl_element)
  ├─ 提取行数据
  └─ 添加 section {paragraph_type: "table", table_data: {rows: [...]}}
```

### 3.3 表格渲染流程

```python
# execute_render()
figure_cfg = template_config.get("figure", {})
_write_sections(doc, sections, headings_cfg, body_cfg, figure_cfg)

# _write_sections()
elif para_type == "table":
    table_data = sec.get("table_data", {}).get("rows", [])
    table_cfg = figure_cfg.get("table", {})
    _add_table(doc, table_data, table_cfg)

# _add_table()
# 1. 动态判断表头
first_row = table_data[0] if table_data else []
has_header = max(len(str(cell)) for cell in first_row) <= 20 if first_row else False

# 2. 标记表头行（跨页重复）
if has_header and table_cfg.get("repeat_header", True):
    _mark_table_header(table.rows[0])

# 3. 设置边框（pt → 1/8pt 转换）
border_outer = int(table_cfg.get("border_width_outer", 1.5) * 8)
border_inner = int(table_cfg.get("border_width_inner", 0.5) * 8)

# 4. 填充数据
for i, row_data in enumerate(table_data):
    is_header = (has_header and i == 0)  # 动态判断
    for j, cell_text in enumerate(row_data):
        _set_cell_style(cell, is_header=is_header, table_cfg=table_cfg)
```

### 3.4 单元格样式应用

```python
_set_cell_style(cell, cell_text, is_header, is_first_col, table_cfg)
  ├─ 清除段落原有 runs
  ├─ 添加文本 run
  ├─ 选择字体配置：
  │   ├─ is_header → header_font
  │   ├─ is_first_col → first_col_font 或 body_font
  │   └─ else → body_font
  ├─ _apply_font(run, font_cfg)
  ├─ 设置水平对齐（header_alignment / body_alignment）
  ├─ 设置垂直对齐（header_v_alignment / body_v_alignment）
  ├─ 设置表头背景色（header_bg_color）
  └─ _set_cell_autofit(cell)
```

---

## 四、数据结构定义

### 4.1 Section 结构（前端）

```typescript
interface Section {
  level: number           // 0=正文，1-4=标题级别
  text: string            // 文本内容
  paragraph_type: 'heading' | 'body' | 'image' | 'table'
  children?: Section[]
  image_path?: string     // 图片节点
  table_data?: {          // 表格节点
    rows: string[][]
  }
  has_caption?: boolean   // 图片是否有说明
}
```

### 4.2 RenderTask 模型

```python
class RenderTask:
    id: UUID
    document_id: UUID
    template_id: UUID
    status: "pending" | "processing" | "done" | "failed"
    ai_clean_result: str       # AI 清洗后的文本
    ai_structure: dict         # AI 识别的结构 {sections: [...]}
    result_path: str           # 输出 .docx 路径
    preview_path: str          # HTML 预览路径
    error_message: str
    created_at: datetime
```

---

## 五、配置单位说明

| 配置项 | 前端单位 | 后端单位 | 转换方式 |
|-------|---------|---------|---------|
| 字体大小 | pt（如 12） | Pt() | 直接使用 |
| 边框宽度 | pt（如 1.5） | 1/8pt（如 12） | `int(pt * 8)` |
| 段落间距 | pt | twips | `int(pt * 20)` |
| 行距 | 倍数（如 1.5） | twips | `int(倍数 * 240)` |
| 页边距 | cm | Cm() | 直接使用 |
| 缩进 | 字符数 | firstLine（继承段落样式） | 首行缩进 2 字符 |

---

## 六、API 路由概览

| 模块 | 路由 | 说明 |
|-----|------|------|
| 认证 | POST /api/auth/login | 登录 |
| 文档 | GET /api/documents | 列表 |
| 文档 | POST /api/documents | 上传 |
| AI | POST /api/ai/extract-structure | 异步结构识别 |
| AI | GET /api/ai/structure-tasks/:id | 查询任务状态 |
| 模板 | GET /api/templates | 列表 |
| 模板 | POST /api/templates | 创建 |
| 模板 | PUT /api/templates/:id | 更新 |
| 排版 | POST /api/render | 创建排版任务 |
| 排版 | GET /api/render/:id/status | 查询状态 |
| 排版 | GET /api/render/:id/preview | 预览 HTML |
| 排版 | GET /api/render/:id/download | 下载 .docx |
