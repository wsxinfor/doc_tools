export interface FontConfig {
  cn_font?: string
  en_font?: string
  size?: number
  bold?: boolean
  italic?: boolean
  underline?: boolean
  color?: string
}

export interface SpacingConfig {
  before?: number
  after?: number
  line?: number
}

export interface MarginConfig {
  top?: number
  bottom?: number
  left?: number
  right?: number
}

export interface HeadingConfig {
  font?: FontConfig
  spacing?: SpacingConfig
  alignment?: 'left' | 'center' | 'right'
  numbering_style?: 'none' | 'chapter-arabic' | 'chapter-chinese' | 'cn-number' | 'arabic-number' | 'decimal'
  page_break_before?: boolean
}

export interface CoverFieldConfig {
  font?: FontConfig
  position?: string
}

export interface CoverConfig {
  client_name?: CoverFieldConfig
  project_name?: CoverFieldConfig
  doc_version?: CoverFieldConfig
  company_name?: CoverFieldConfig
  date?: CoverFieldConfig
  bg_color?: string
  logo_path?: string | null
  logo_position?: string | null
}

export interface HeaderFooterConfig {
  header_left?: string
  header_center?: string
  header_right?: string
  footer_left?: string
  footer_center?: string
  footer_right?: string
  show_divider?: boolean
  divider_color?: string
  font?: FontConfig
  first_page_hide?: boolean
}

export interface TocConfig {
  max_level?: number
  title_text?: string
  title_font?: FontConfig
  entry_font?: FontConfig
  show_page_number?: boolean
  separate_page?: boolean
}

export interface BodyConfig {
  font?: FontConfig
  spacing?: SpacingConfig
  first_line_indent?: number
  margins?: MarginConfig
  list_style?: string
}

export interface TableConfig {
  // 表头配置
  header_font?: FontConfig
  header_bg_color?: string
  header_alignment?: 'left' | 'center' | 'right'
  header_v_alignment?: 'top' | 'center' | 'bottom'

  // 表体配置
  body_font?: FontConfig
  body_alignment?: 'left' | 'center' | 'right'
  body_v_alignment?: 'top' | 'center' | 'bottom'

  // 首列特殊配置（可选）
  first_col_font?: FontConfig
  first_col_alignment?: 'left' | 'center' | 'right'

  // 边框配置
  border_color?: string
  border_width_outer?: number
  border_width_inner?: number

  // 布局配置
  column_widths?: number[]
  repeat_header?: boolean
}

export interface FigureConfig {
  image_alignment?: 'left' | 'center' | 'right'
  caption_font?: FontConfig
  caption_style?: 'simple' | 'chapter-figure'  // simple=图 1, chapter-figure=图 1-1
  table?: TableConfig
}

export interface TemplateConfig {
  cover?: CoverConfig
  header_footer?: HeaderFooterConfig
  headings?: Record<string, HeadingConfig>
  toc?: TocConfig
  body?: BodyConfig
  figure?: FigureConfig
}
