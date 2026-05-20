import { useState, useEffect } from 'react'
import {
  Form, Input, Button, Tabs, message, Typography, Spin,
  Switch, Select, Row, Col, Divider, Collapse,
} from 'antd'
import { useNavigate, useParams } from 'react-router-dom'
import { createTemplate, getTemplate, updateTemplate } from '../../../api/templates'
import FontPicker from '../../../components/FontPicker'
import ColorPicker from '../../../components/ColorPicker'
import FontSizePicker from '../../../components/FontSizePicker'
import type { TemplateConfig, HeadingConfig } from '../../../types/template'
import type { AxiosError } from 'axios'

const { Title } = Typography

const ALIGN_OPTIONS = [
  { label: '左对齐', value: 'left' },
  { label: '居中', value: 'center' },
  { label: '右对齐', value: 'right' },
]

/** 新建模板时的默认配置，英文字体统一 Times New Roman，正文小四 */
const DEFAULT_CONFIG: TemplateConfig = {
  cover: {
    bg_color: '#FFFFFF',
  },
  header_footer: {
    first_page_hide: true,
  },
  headings: {
    h1: { font: { cn_font: '黑体', en_font: 'Times New Roman', size: 16, bold: true, color: '#000000' }, spacing: { before: 12, after: 6, line: 1.5 }, alignment: 'left', numbering_style: 'none', page_break_before: true },
    h2: { font: { cn_font: '黑体', en_font: 'Times New Roman', size: 14, bold: true, color: '#000000' }, spacing: { before: 6, after: 6, line: 1.5 }, alignment: 'left', numbering_style: 'none', page_break_before: false },
    h3: { font: { cn_font: '黑体', en_font: 'Times New Roman', size: 12, bold: true, color: '#000000' }, spacing: { before: 6, after: 3, line: 1.5 }, alignment: 'left', numbering_style: 'none' },
    h4: { font: { cn_font: '宋体', en_font: 'Times New Roman', size: 12, bold: false, color: '#000000' }, spacing: { before: 3, after: 3, line: 1.5 }, alignment: 'left', numbering_style: 'none' },
  },
  toc: {
    max_level: 3, title_text: '目  录',
    title_font: { cn_font: '宋体', en_font: 'Times New Roman', size: 14, bold: true, color: '#000000' },
    entry_font: { cn_font: '宋体', en_font: 'Times New Roman', size: 12, color: '#000000' },
    show_page_number: true, separate_page: true,
  },
  body: {
    font: { cn_font: '宋体', en_font: 'Times New Roman', size: 12, color: '#000000' },
    spacing: { before: 0, after: 0, line: 1.5 },
    first_line_indent: 2,
    list_style: 'none',
    margins: { top: 2.54, bottom: 2.54, left: 3.17, right: 3.17 },
  },
  figure: {
    image_alignment: 'center',
    caption_font: { cn_font: '宋体', en_font: 'Times New Roman', size: 10.5, color: '#333333' },
    caption_style: 'simple',
    table: {
      header_bg_color: '#D6E7F5',
      header_font: { cn_font: '宋体', en_font: 'Times New Roman', size: 12, color: '#000000' },
      header_alignment: 'center',
      body_font: { cn_font: '仿宋', en_font: 'Times New Roman', size: 12, color: '#000000' },
      body_alignment: 'left',
      border_width_outer: 1.5,
      border_width_inner: 0.5,
      repeat_header: true,
    },
  },
}

function HeadingTab({
  hKey,
  config,
  onChange,
}: {
  hKey: string
  config: HeadingConfig
  onChange: (c: HeadingConfig) => void
}) {
  const cfg = config ?? {}
  const font = cfg.font ?? {}
  const spacing = cfg.spacing ?? {}

  const numberingOptions = hKey === 'h1'
    ? [
        { label: '无编号', value: 'none' },
        { label: '第 1 章、第 2 章', value: 'chapter-arabic' },
        { label: '第一章、第二章', value: 'chapter-chinese' },
        { label: '一、二、三、', value: 'cn-number' },
        { label: '1、2、3、', value: 'arabic-number' },
      ]
    : hKey === 'h2'
      ? [
          { label: '无编号', value: 'none' },
          { label: '1.1、1.2、1.3...（自动）', value: 'decimal' },
        ]
      : hKey === 'h3'
        ? [
            { label: '无编号', value: 'none' },
            { label: '1.1.1、1.1.2、1.1.3...（自动）', value: 'decimal' },
          ]
        : [
            { label: '无编号', value: 'none' },
            { label: '1.1.1.1、1.1.1.2...（自动）', value: 'decimal' },
          ]

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <div>中文字体</div>
          <FontPicker type="cn" value={font.cn_font} onChange={(v) => onChange({ ...cfg, font: { ...font, cn_font: v } })} />
        </Col>
        <Col span={6}>
          <div>英文字体</div>
          <FontPicker type="en" value={font.en_font} onChange={(v) => onChange({ ...cfg, font: { ...font, en_font: v } })} />
        </Col>
        <Col span={4}>
          <div>字号</div>
          <FontSizePicker value={font.size} onChange={(v) => onChange({ ...cfg, font: { ...font, size: v } })} />
        </Col>
        <Col span={5}>
          <div>颜色</div>
          <ColorPicker value={font.color ?? '#000000'} onChange={(v) => onChange({ ...cfg, font: { ...font, color: v } })} />
        </Col>
      </Row>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <div>加粗</div>
          <Switch checked={font.bold} onChange={(v) => onChange({ ...cfg, font: { ...font, bold: v } })} />
        </Col>
        <Col span={4}>
          <div>斜体</div>
          <Switch checked={font.italic} onChange={(v) => onChange({ ...cfg, font: { ...font, italic: v } })} />
        </Col>
        <Col span={4}>
          <div>下划线</div>
          <Switch checked={font.underline} onChange={(v) => onChange({ ...cfg, font: { ...font, underline: v } })} />
        </Col>
        <Col span={6}>
          <div>对齐方式</div>
          <Select value={cfg.alignment ?? 'left'} options={ALIGN_OPTIONS} onChange={(v) => onChange({ ...cfg, alignment: v })} style={{ width: '100%' }} />
        </Col>
      </Row>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <div>编号样式</div>
          <Select
            value={cfg.numbering_style ?? 'none'}
            onChange={(v) => onChange({ ...cfg, numbering_style: v })}
            options={numberingOptions}
            style={{ width: '100%' }}
          />
        </Col>
      </Row>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={5}>
          <div>段前（pt）</div>
          <FontSizePicker value={spacing.before ?? 0} onChange={(v) => onChange({ ...cfg, spacing: { ...spacing, before: v } })} />
        </Col>
        <Col span={5}>
          <div>段后（pt）</div>
          <FontSizePicker value={spacing.after ?? 0} onChange={(v) => onChange({ ...cfg, spacing: { ...spacing, after: v } })} />
        </Col>
        <Col span={5}>
          <div>行距（倍）</div>
          <Select
            value={spacing.line ?? 1.5}
            options={[1, 1.25, 1.5, 2, 2.5, 3].map((n) => ({ label: `${n}倍`, value: n }))}
            onChange={(v) => onChange({ ...cfg, spacing: { ...spacing, line: v } })}
            style={{ width: '100%' }}
          />
        </Col>
        {(hKey === 'h1' || hKey === 'h2' || hKey === 'h3' || hKey === 'h4') && (
          <Col span={6}>
            <div>页前分页</div>
            <Switch checked={cfg.page_break_before ?? false} onChange={(v) => onChange({ ...cfg, page_break_before: v })} />
          </Col>
        )}
      </Row>
    </div>
  )
}

export default function TemplateEditorPage() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [config, setConfig] = useState<TemplateConfig>(DEFAULT_CONFIG)

  useEffect(() => {
    if (id) {
      setLoading(true)
      getTemplate(id)
        .then((tmpl) => {
          form.setFieldsValue({ name: tmpl.name, description: tmpl.description })
          setConfig(tmpl.config as TemplateConfig)
        })
        .finally(() => setLoading(false))
    }
  }, [id, form])

  const updateConfig = (path: string[], value: unknown) => {
    setConfig((prev) => {
      const next = { ...prev } as Record<string, unknown>
      let cur = next
      for (let i = 0; i < path.length - 1; i++) {
        const key = path[i]
        // 使用原值或空对象进行浅拷贝，保留该层级原有的其他字段
        cur[key] = { ...((cur[key] as Record<string, unknown>) ?? {}) }
        cur = cur[key] as Record<string, unknown>
      }
      cur[path[path.length - 1]] = value
      return next as TemplateConfig
    })
  }

  const onSave = async () => {
    try {
      await form.validateFields()
    } catch {
      return
    }
    const values = form.getFieldsValue() as { name: string; description?: string }
    setSaving(true)
    try {
      if (id) {
        await updateTemplate(id, { ...values, config: config as Record<string, unknown> })
        message.success('保存成功')
      } else {
        await createTemplate({ ...values, config: config as Record<string, unknown> })
        message.success('创建成功')
        navigate('/templates')
      }
    } catch (err) {
      const axiosErr = err as AxiosError<{ message?: string }>
      message.error(axiosErr.response?.data?.message ?? '保存失败')
    } finally {
      setSaving(false)
    }
  }

  const cover = config.cover ?? {}
  const hf = config.header_footer ?? {}
  const headings = config.headings ?? {}
  const toc = config.toc ?? {}
  const body = config.body ?? {}
  const bodyFont = body.font ?? {}
  const bodyMargins = body.margins ?? {}
  const figure = config.figure ?? {}

  const tabItems = [
    {
      key: 'cover',
      label: '封面设置',
      children: (
        <div>
          <Row gutter={16}>
            <Col span={6}>
              <div>封面背景色</div>
              <ColorPicker value={cover.bg_color ?? '#FFFFFF'} onChange={(v) => updateConfig(['cover', 'bg_color'], v)} />
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'header_footer',
      label: '页眉页脚',
      children: (
        <div>
          <Row gutter={16}>
            <Col span={8}>
              <div>首页不显示页眉页脚</div>
              <Switch checked={(hf.first_page_hide as boolean) ?? true} onChange={(v) => updateConfig(['header_footer', 'first_page_hide'], v)} />
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'headings',
      label: '标题样式',
      children: (
        <Tabs
          items={['h1', 'h2', 'h3', 'h4'].map((hk) => ({
            key: hk,
            label: hk.toUpperCase(),
            children: (
              <HeadingTab
                hKey={hk}
                config={(headings[hk] ?? {}) as HeadingConfig}
                onChange={(c) => updateConfig(['headings', hk], c)}
              />
            ),
          }))}
        />
      ),
    },
    {
      key: 'toc',
      label: '目录',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <div>目录层级深度</div>
              <Select
                value={(toc.max_level as number) ?? 3}
                options={[1, 2, 3].map((n) => ({ label: `${n} 级`, value: n }))}
                onChange={(v) => updateConfig(['toc', 'max_level'], v)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={8}>
              <div>目录标题文字</div>
              <Input value={(toc.title_text as string) ?? '目  录'} onChange={(e) => updateConfig(['toc', 'title_text'], e.target.value)} />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={5}>
              <div>标题字号</div>
              <FontSizePicker value={(toc.title_font as { size?: number } | undefined)?.size ?? 14} onChange={(v) => updateConfig(['toc', 'title_font', 'size'], v)} />
            </Col>
            <Col span={5}>
              <div>条目字号</div>
              <FontSizePicker value={(toc.entry_font as { size?: number } | undefined)?.size ?? 12} onChange={(v) => updateConfig(['toc', 'entry_font', 'size'], v)} />
            </Col>
            <Col span={6}>
              <div>显示页码</div>
              <Switch checked={(toc.show_page_number as boolean) ?? true} onChange={(v) => updateConfig(['toc', 'show_page_number'], v)} />
            </Col>
            <Col span={4}>
              <div>目录后分页</div>
              <Switch checked={(toc.separate_page as boolean) ?? true} onChange={(v) => updateConfig(['toc', 'separate_page'], v)} />
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'body',
      label: '正文格式',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={5}>
              <div>中文字体</div>
              <FontPicker type="cn" value={bodyFont.cn_font} onChange={(v) => updateConfig(['body', 'font', 'cn_font'], v)} />
            </Col>
            <Col span={5}>
              <div>英文字体</div>
              <FontPicker type="en" value={bodyFont.en_font} onChange={(v) => updateConfig(['body', 'font', 'en_font'], v)} />
            </Col>
            <Col span={4}>
              <div>字号</div>
              <FontSizePicker value={bodyFont.size ?? 12} onChange={(v) => updateConfig(['body', 'font', 'size'], v)} />
            </Col>
            <Col span={5}>
              <div>颜色</div>
              <ColorPicker value={bodyFont.color ?? '#000000'} onChange={(v) => updateConfig(['body', 'font', 'color'], v)} />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={4}>
              <div>首行缩进（字符）</div>
              <Select
                value={(body.first_line_indent as number) ?? 2}
                options={[0, 1, 2].map((n) => ({ label: `${n} 字符`, value: n }))}
                onChange={(v) => updateConfig(['body', 'first_line_indent'], v)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={4}>
              <div>行距（倍）</div>
              <Select
                value={(body.spacing as { line?: number } | undefined)?.line ?? 1.5}
                options={[1, 1.25, 1.5, 2, 2.5, 3].map((n) => ({ label: `${n}倍`, value: n }))}
                onChange={(v) => updateConfig(['body', 'spacing', 'line'], v)}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={4}>
              <div>列表样式</div>
              <Select
                value={(body.list_style as string) ?? 'none'}
                options={[
                  { label: '无', value: 'none' },
                  { label: '▶ 三角', value: 'triangle' },
                  { label: '◆ 菱形', value: 'diamond' },
                  { label: '● 实心圆', value: 'circle' },
                  { label: '◇ 空心菱形', value: 'hollow_diamond' },
                  { label: '■ 方块', value: 'square' },
                  { label: '▪ 小方块', value: 'dot' },
                ]}
                onChange={(v) => updateConfig(['body', 'list_style'], v)}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>
          <Divider orientation="left">页边距（cm）</Divider>
          <Row gutter={16}>
            {(['top', 'bottom', 'left', 'right'] as const).map((side) => (
              <Col key={side} span={4}>
                <div>{{ top: '上', bottom: '下', left: '左', right: '右' }[side]}</div>
                <Select
                  value={(bodyMargins[side] as number) ?? 2.54}
                  options={[1.5, 1.8, 2, 2.54, 3, 3.17, 3.5].map((n) => ({ label: `${n} cm`, value: n }))}
                  onChange={(v) => updateConfig(['body', 'margins', side], v)}
                  style={{ width: '100%' }}
                />
              </Col>
            ))}
          </Row>
        </div>
      ),
    },
    {
      key: 'figure',
      label: '图表格式',
      children: (
        <div>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <div>图片对齐</div>
              <Select
                value={(figure.image_alignment as string) ?? 'center'}
                options={ALIGN_OPTIONS}
                onChange={(v) => updateConfig(['figure', 'image_alignment'], v)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div>说明文字体 - 中文</div>
              <FontPicker type="cn" value={(figure.caption_font?.cn_font as string) ?? '宋体'} onChange={(v) => updateConfig(['figure', 'caption_font', 'cn_font'], v)} />
            </Col>
            <Col span={5}>
              <div>说明文字体 - 英文</div>
              <FontPicker type="en" value={(figure.caption_font?.en_font as string) ?? 'Times New Roman'} onChange={(v) => updateConfig(['figure', 'caption_font', 'en_font'], v)} />
            </Col>
            <Col span={5}>
              <div>说明文字号</div>
              <FontSizePicker value={(figure.caption_font?.size as number) ?? 10.5} onChange={(v) => updateConfig(['figure', 'caption_font', 'size'], v)} />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <div>图片编号样式</div>
              <Select
                value={(figure.caption_style as string) ?? 'simple'}
                options={[
                  { label: '图 1、图 2...（简单序号）', value: 'simple' },
                  { label: '图 1-1、图 2-1...（带章节号）', value: 'chapter-figure' },
                ]}
                onChange={(v) => updateConfig(['figure', 'caption_style'], v)}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>
          <Divider orientation="left">表格样式</Divider>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <div>表头中文字体</div>
              <FontPicker type="cn" value={(figure.table?.header_font?.cn_font as string) ?? '宋体'} onChange={(v) => updateConfig(['figure', 'table', 'header_font', 'cn_font'], v)} />
            </Col>
            <Col span={6}>
              <div>表头英文字体</div>
              <FontPicker type="en" value={(figure.table?.header_font?.en_font as string) ?? 'Times New Roman'} onChange={(v) => updateConfig(['figure', 'table', 'header_font', 'en_font'], v)} />
            </Col>
            <Col span={5}>
              <div>表头字号</div>
              <FontSizePicker value={(figure.table?.header_font?.size as number) ?? 12} onChange={(v) => updateConfig(['figure', 'table', 'header_font', 'size'], v)} />
            </Col>
            <Col span={7}>
              <div>表头字体颜色</div>
              <ColorPicker value={(figure.table?.header_font?.color as string) ?? '#000000'} onChange={(v) => updateConfig(['figure', 'table', 'header_font', 'color'], v)} />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <div>表头背景色</div>
              <ColorPicker value={(figure.table?.header_bg_color as string) ?? '#D6E7F5'} onChange={(v) => updateConfig(['figure', 'table', 'header_bg_color'], v)} />
            </Col>
            <Col span={6}>
              <div>表头对齐</div>
              <Select
                value={(figure.table?.header_alignment as string) ?? 'center'}
                options={ALIGN_OPTIONS}
                onChange={(v) => updateConfig(['figure', 'table', 'header_alignment'], v)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div>表头垂直对齐</div>
              <Select
                value={(figure.table?.header_v_alignment as string) ?? 'center'}
                options={[
                  { label: '上', value: 'top' },
                  { label: '中', value: 'center' },
                  { label: '下', value: 'bottom' },
                ]}
                onChange={(v) => updateConfig(['figure', 'table', 'header_v_alignment'], v)}
                style={{ width: '100%' }}
              />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <div>表体中文字体</div>
              <FontPicker type="cn" value={(figure.table?.body_font?.cn_font as string) ?? '仿宋'} onChange={(v) => updateConfig(['figure', 'table', 'body_font', 'cn_font'], v)} />
            </Col>
            <Col span={6}>
              <div>表体英文字体</div>
              <FontPicker type="en" value={(figure.table?.body_font?.en_font as string) ?? 'Times New Roman'} onChange={(v) => updateConfig(['figure', 'table', 'body_font', 'en_font'], v)} />
            </Col>
            <Col span={5}>
              <div>表体字号</div>
              <FontSizePicker value={(figure.table?.body_font?.size as number) ?? 12} onChange={(v) => updateConfig(['figure', 'table', 'body_font', 'size'], v)} />
            </Col>
            <Col span={7}>
              <div>表体字体颜色</div>
              <ColorPicker value={(figure.table?.body_font?.color as string) ?? '#000000'} onChange={(v) => updateConfig(['figure', 'table', 'body_font', 'color'], v)} />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <div>表体对齐</div>
              <Select
                value={(figure.table?.body_alignment as string) ?? 'left'}
                options={ALIGN_OPTIONS}
                onChange={(v) => updateConfig(['figure', 'table', 'body_alignment'], v)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div>表体垂直对齐</div>
              <Select
                value={(figure.table?.body_v_alignment as string) ?? 'center'}
                options={[
                  { label: '上', value: 'top' },
                  { label: '中', value: 'center' },
                  { label: '下', value: 'bottom' },
                ]}
                onChange={(v) => updateConfig(['figure', 'table', 'body_v_alignment'], v)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div>边框颜色</div>
              <ColorPicker value={(figure.table?.border_color as string) ?? 'auto'} onChange={(v) => updateConfig(['figure', 'table', 'border_color'], v)} />
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={6}>
              <div>外框宽度 (pt)</div>
              <Select
                value={(figure.table?.border_width_outer as number) ?? 1.5}
                options={[0.5, 0.75, 1, 1.5, 2, 2.5, 3].map((n) => ({ label: `${n} pt`, value: n }))}
                onChange={(v) => updateConfig(['figure', 'table', 'border_width_outer'], v)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={6}>
              <div>内框宽度 (pt)</div>
              <Select
                value={(figure.table?.border_width_inner as number) ?? 0.5}
                options={[0.5, 0.75, 1, 1.5, 2].map((n) => ({ label: `${n} pt`, value: n }))}
                onChange={(v) => updateConfig(['figure', 'table', 'border_width_inner'], v)}
                style={{ width: '100%' }}
              />
            </Col>
            <Col span={8}>
              <div>表头跨页重复</div>
              <Switch checked={(figure.table?.repeat_header as boolean) ?? true} onChange={(v) => updateConfig(['figure', 'table', 'repeat_header'], v)} />
            </Col>
          </Row>
        </div>
      ),
    },
    {
      key: 'help',
      label: '配置说明',
      children: (
        <Collapse
          items={[
            {
              key: '1',
              label: '封面设置',
              children: (
                <div>
                  <p><strong>封面背景色</strong>：设置文档封面的背景颜色，默认为白色 #FFFFFF。</p>
                  <p><strong>说明</strong>：封面包含客户名称、项目名称、文档版本、公司名称、日期等字段，字体和布局由系统自动处理。</p>
                </div>
              ),
            },
            {
              key: '2',
              label: '页眉页脚',
              children: (
                <div>
                  <p><strong>首页不显示页眉页脚</strong>：封面页通常不需要页眉页脚，勾选后首页将不显示。</p>
                  <p><strong>页眉内容</strong>：左侧显示客户名称，右侧显示项目名称（来自渲染参数）。</p>
                  <p><strong>页脚内容</strong>：固定格式，包含公司 Logo、地址（北京市怀柔区乐园西大街 13 号院 28 号楼 1 层）、电话（010-82843001）。</p>
                </div>
              ),
            },
            {
              key: '3',
              label: '标题样式（H1-H4）',
              children: (
                <div>
                  <p><strong>中/英文字体</strong>：分别设置标题中的中文和英文字体。推荐：黑体/宋体组合。</p>
                  <p><strong>字号</strong>：标题大小，单位 pt。推荐：H1=16pt, H2=14pt, H3=12pt, H4=12pt。</p>
                  <p><strong>编号样式</strong>：</p>
                  <ul>
                    <li>H1：可选"第 X 章"、"第一章"、"一、"、"1、"或无编号</li>
                    <li>H2-H4：可选"1.1"、"1.1.1"等自动编号或无编号</li>
                  </ul>
                  <p><strong>段前段后间距</strong>：标题与前后内容的间距，单位 pt。</p>
                  <p><strong>页前分页</strong>：勾选后，该级别标题始终从新的一页开始。</p>
                </div>
              ),
            },
            {
              key: '4',
              label: '目录',
              children: (
                <div>
                  <p><strong>目录层级深度</strong>：目录中显示的最大标题层级。例如选择 3 级，则 H1/H2/H3 会出现在目录中。</p>
                  <p><strong>目录标题文字</strong>：目录页的标题，默认"目  录"（宋体、四号、加粗）。</p>
                  <p><strong>标题/条目字号</strong>：目录标题和条目文字的字号。</p>
                  <p><strong>显示页码</strong>：目录条目右侧是否显示页码。</p>
                  <p><strong>目录后分页</strong>：目录后是否插入分页符，使正文从新的一页开始。</p>
                </div>
              ),
            },
            {
              key: '5',
              label: '正文格式',
              children: (
                <div>
                  <p><strong>中/英文字体</strong>：正文字体。推荐：宋体/Times New Roman 组合。</p>
                  <p><strong>字号</strong>：正文字大小，默认 12pt（五号）。</p>
                  <p><strong>首行缩进</strong>：段落首行缩进字符数，通常 2 字符。</p>
                  <p><strong>行距</strong>：行与行之间的距离倍数，默认 1.5 倍。</p>
                  <p><strong>页边距</strong>：页面上下左右的边距，单位 cm。默认：上 2.54、下 2.54、左 3.17、右 3.17。</p>
                </div>
              ),
            },
            {
              key: '6',
              label: '图表格式',
              children: (
                <div>
                  <p><strong>图片对齐</strong>：图片在页面中的对齐方式，推荐居中。</p>
                  <p><strong>说明文字体</strong>：图片下方"图 1"、"图 2"等说明文字的字体，推荐宋体、五号（10.5pt）。</p>
                  <p><strong>表格样式</strong>：</p>
                  <ul>
                    <li>表头字体/背景色：表格第一行的字体和背景色，推荐宋体、蓝色背景 #D6E7F5</li>
                    <li>表体字体：表格数据行的字体，推荐仿宋</li>
                    <li>对齐方式：表头和表体的水平/垂直对齐方式</li>
                    <li>边框宽度：外框和内框的线条粗细，单位 pt</li>
                    <li>表头跨页重复：勾选后，表格跨页时表头会自动在下一页重复显示</li>
                  </ul>
                  <p><strong>智能表头检测</strong>：系统会自动判断表格第一行是否为表头——如果第一行有单元格文本超过 20 字符，则按无表头处理。</p>
                </div>
              ),
            },
            {
              key: '7',
              label: '配置优先级说明',
              children: (
                <div>
                  <p>模板配置在以下情况下会被覆盖（优先级从高到低）：</p>
                  <ol>
                    <li><strong>用户单次排版参数</strong>：用户在确认页面临时调整的参数优先级最高</li>
                    <li><strong>模板保存的配置</strong>：在模板编辑器中设置的配置</li>
                    <li><strong>系统硬编码默认值</strong>：未配置时使用后端代码中的默认值</li>
                  </ol>
                </div>
              ),
            },
          ]}
        />
      ),
    },
  ]

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          {id ? '编辑模板' : '新建模板'}
        </Title>
        <Button type="primary" onClick={onSave} loading={saving} data-testid="save-template-btn">
          保存模板
        </Button>
      </div>
      <Form form={form} layout="vertical" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="name" label="模板名称" rules={[{ required: true, message: '请输入模板名称' }]}>
              <Input data-testid="template-name-input" />
            </Form.Item>
          </Col>
          <Col span={16}>
            <Form.Item name="description" label="描述">
              <Input />
            </Form.Item>
          </Col>
        </Row>
      </Form>
      <Tabs items={tabItems} tabPosition="left" style={{ minHeight: 400 }} />
    </div>
  )
}
