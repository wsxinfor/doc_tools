# 企业应用前端 UI 开发规范

> 适用于 DocFormat 项目前端开发，所有 UI 改动必须遵循本规范。

---

## 一、设计哲学

- **轻而不失重**：摒弃纯黑，用青灰代替，保留专业感的同时减少视觉压迫
- **线条即装饰**：Logo、分割线、装饰元素均以 SVG 细线（stroke，不 fill）构建，无插图、无图片背景
- **色彩有据可依**：每个颜色都有功能含义，拒绝随意堆砌。Active 指示色与主色调形成冷暖对比
- **无阴影原则**：层次完全靠边框（0.5px）和背景色差异区分，禁用 `box-shadow` 做视觉层次
- **字重克制**：中文界面字重 400 已够用，最多 500，绝不使用 600/700 bold

---

## 二、色彩方案（方案 A · 烟灰·霜白）

| 用途 | 变量名 | 色值 | 说明 |
|------|--------|------|------|
| 侧栏背景 | `--color-sidebar-bg` | `#4a5568` | 暖灰色主侧栏 |
| 侧栏文字 | `--color-sidebar-text` | `#edf2f7` | 浅色文字 |
| 侧栏次要文字 | `--color-sidebar-muted` | `#a0aec0` | 弱化文字 |
| 侧栏分区标题 | `--color-sidebar-section` | `#3a4555` | 分组标题 |
| 侧栏悬停 | `--color-sidebar-hover` | `#5a6578` | 悬停背景 |
| 侧栏 Active 背景 | `--color-sidebar-active-bg` | `#5a6578` | 选中项背景 |
| 侧栏 Active 文字 | `--color-sidebar-active-text` | `#edf2f7` | 选中项文字 |
| 侧栏 Active 指示线 | `--color-sidebar-active-line` | `#68d391` | **薄荷绿** 左侧指示线 |
| 页面背景 | `--color-page-bg` | `#f7f8fa` | 霜白色页面底 |
| 卡片背景 | `--color-card-bg` | `#ffffff` | 纯白卡片 |
| 顶部栏背景 | `--color-topbar-bg` | `#ffffff` | 纯白顶栏 |
| 顶部栏边框 | `--color-topbar-border` | `#e2e8f0` | 浅灰边框 |
| 主文字色 | `--color-text-primary` | `#2d3748` | 深灰文字 |
| 次要文字 | `--color-text-secondary` | `#718096` | 中灰文字 |
| 三级文字 | `--color-text-tertiary` | `#a0aec0` | 浅灰文字 |
| 边框色 | `--color-border` | `#e2e8f0` | 默认边框 |
| 强边框色 | `--color-border-strong` | `#cbd5e0` | 强调边框 |
| 主按钮背景 | `--color-btn-bg` | `#4a5568` | 烟灰色按钮 |
| 按钮悬停 | `--color-btn-hover` | `#5a6578` | 悬停变亮 |

---

## 三、CSS 变量 Token

### 完整变量表（`src/styles/variables.css`）

```css
:root {
  /* 主色 - 方案 A 烟灰·霜白 */
  --color-sidebar-bg:      #4a5568;
  --color-sidebar-text:    #edf2f7;
  --color-sidebar-muted:   #a0aec0;
  --color-sidebar-section: #3a4555;
  --color-sidebar-hover:   #5a6578;
  --color-sidebar-active-bg:    #5a6578;
  --color-sidebar-active-text:  #edf2f7;
  --color-sidebar-active-line:  #68d391;

  /* 页面 */
  --color-page-bg:         #f7f8fa;
  --color-surface:         #ffffff;
  --color-topbar-bg:       #ffffff;
  --color-topbar-border:   #e2e8f0;

  /* 文字 */
  --color-text-primary:    #2d3748;
  --color-text-secondary:  #718096;
  --color-text-tertiary:   #a0aec0;
  --color-text-inverse:    #edf2f7;

  /* 边框 */
  --color-border:          #e2e8f0;
  --color-border-strong:   #cbd5e0;

  /* 卡片/输入 */
  --color-card-bg:         #ffffff;
  --color-input-border:    #cbd5e0;
  --color-input-focus:     #4a5568;
  --color-badge-bg:        #edf2f7;
  --color-badge-text:      #4a5568;

  /* 图表 */
  --color-chart-primary:   #4a5568;
  --color-chart-track:     #edf2f7;
  --color-chart-accent:    #68d391;

  /* 按钮 */
  --color-btn-bg:          #4a5568;
  --color-btn-text:        #edf2f7;
  --color-btn-hover:       #5a6578;

  /* 字体 */
  --font-sans:    'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  --font-mono:    'JetBrains Mono', 'Fira Code', monospace;
  --font-display: 'Noto Serif SC', 'STSong', serif;

  /* 圆角 */
  --radius-xs: 2px;
  --radius-sm: 3px;
  --radius-md: 4px;

  /* 间距（8px 基准） */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;

  /* 侧栏 */
  --sidebar-width: 200px;

  /* TopBar */
  --topbar-height: 48px;
}
```

---

## 四、允许与禁止

### ✅ 允许

| 类别 | 规则 |
|------|------|
| 图标 | SVG 线条图标（`stroke`，不 `fill`），`stroke-width: 1–1.5px` |
| 背景 | 单色纯色背景，无渐变 |
| 边框 | `0.5px ~ 1px` 细边框 |
| 动画 | `transition` 动画，`duration ≤ 200ms`，仅 `color / background / border-color / transform` |
| 字间距 | `letter-spacing` 加宽增加中文呼吸感 |
| 组件库 | Ant Design Pro 配合 Token 覆盖 |

### ❌ 禁止

| 类别 | 规则 |
|------|------|
| 阴影 | `box-shadow`（除 `outline` focus ring 外） |
| 渐变 | `background: linear-gradient(...)` 装饰性渐变 |
| 圆角 | 圆角 > 4px（输入框、按钮、导航项一律 ≤ 4px） |
| 图标 | Font Awesome 实心图标（改用 **Lucide** / Heroicons 线条图标） |
| 动画时长 | 任何动画 `duration > 300ms` |
| 字重 | 字重 600/700 |
| 纯黑纯白 | `#000000` 或 `#ffffff` 作为主背景色（用方案变量替代） |
| 登录页表单 | 登录页使用卡片阴影包裹表单 |
| 侧栏 active | 侧栏 active 导航项使用圆角 |

---

## 五、字体层级

| 用途 | 字号 | 字重 | letter-spacing | 备注 |
|------|------|------|----------------|------|
| 品牌/系统名（侧栏顶部） | 13px | 400 | 0.10em | `--font-sans` |
| 页面标题（TopBar） | 13px | 500 | 0.05em | |
| 区块标题 | 14px | 500 | 0.03em | |
| 正文 | 13px | 400 | normal | |
| 表单标签 | 10px | 400 | 0.12em | uppercase |
| 导航项 | 12px | 400 | 0.06em | |
| 导航分组标题 | 9px | 400 | 0.18em | uppercase |
| 数据卡片数值 | 20px | 400 | normal | 不加粗，保持轻盈 |
| 数据卡片标签 | 10px | 400 | 0.08em | |
| 按钮 | 12px | 400 | 0.15em | |
| Badge/Tag | 10px | 400 | 0.06em | |

---

## 六、登录页规范

### 布局结构

```
┌──────────────────────────────────────────────┐
│  左侧品牌区 (43%)        │  右侧表单区 (57%)   │
│  var(--color-sidebar-bg) │  var(--color-page-bg)  │
│                          │                     │
│  ┌ SVG 线条徽标 ┐        │  标题（欢迎登录）    │
│  └─────────────┘        │  ─────── 账号输入框  │
│  系统名称                │  ─────── 密码输入框  │
│  英文副标题              │  [ 登  录 ]          │
│  角落装饰线条            │                     │
└──────────────────────────────────────────────┘
```

### 规则清单

**左侧品牌区：**
- 背景色：`var(--color-sidebar-bg)`，纯色，无渐变
- Logo：SVG 几何线条，`stroke` 颜色用 `--color-sidebar-muted`，`stroke-width` 0.5–1px，无 `fill`
- 可选角落装饰：等间距平行线（SVG `<line>`）或方格（`<rect>` 无填充），`opacity: 0.15–0.2`
- 系统名：`--font-sans`，字重 400，`--color-sidebar-text`，`letter-spacing: 0.12em`
- 副标题：`--color-sidebar-muted`，`letter-spacing: 0.2em`，`font-size: 10px`
- 响应式 < 768px：左侧隐藏，表单居中全宽

**右侧表单区：**
- 输入框：底线样式，`border: none; border-bottom: 1px solid var(--color-input-border)`，无外框，无圆角
- 聚焦时底线变为 `var(--color-input-focus)`，`transition: border-color 0.15s`
- 标签：`font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase`
- 登录按钮：`background: var(--color-btn-bg); color: var(--color-btn-text); border-radius: var(--radius-xs); letter-spacing: 0.15em`
- 禁止使用卡片 wrapper（无 `box-shadow`，无额外边框包裹）

---

## 七、功能页规范（左侧导航 + 右侧内容）

### 整体布局

```
┌──────────────────────────────────────────────────────┐
│ Sidebar                 │ Main                        │
│ width: 200px (固定)     │ flex: 1; overflow-y: auto   │
│ background: sidebar-bg  │                             │
│ height: 100vh           │ ┌─────────────── TopBar ──┐ │
│ position: fixed         │ │ 48px; background: white  │ │
│                         │ └─────────────────────────┘ │
│ Logo 区 (52px)          │                             │
│ ───────────────         │ 内容区（padding: 20px）      │
│ 分组标题                │   卡片 / 表格 / 图表         │
│   • 导航项              │                             │
│   • 导航项 [active]     │                             │
│ ───────────────         │                             │
│ 底部用户区              │                             │
└─────────────────────────────────────────────────────┘
```

### 侧边栏 CSS

```css
.sidebar {
  width: var(--sidebar-width);
  height: 100vh;
  position: fixed; left: 0; top: 0;
  background: var(--color-sidebar-bg);
  display: flex; flex-direction: column;
  z-index: 100;
}
.sidebar-logo-area {
  height: 52px;
  display: flex; align-items: center;
  padding: 0 16px;
  border-bottom: 0.5px solid color-mix(in srgb, var(--color-sidebar-muted) 30%, transparent);
  flex-shrink: 0;
}
.sidebar-logo-text {
  font-size: 13px; font-weight: 400;
  color: var(--color-sidebar-text);
  letter-spacing: 0.10em;
}
.sidebar-nav { flex: 1; overflow-y: auto; padding: 8px 0; }
.nav-group-title {
  font-size: 9px; font-weight: 400;
  color: var(--color-sidebar-section);
  letter-spacing: 0.18em; text-transform: uppercase;
  padding: 12px 16px 4px;
}
.nav-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; cursor: pointer;
  font-size: 12px; letter-spacing: 0.06em;
  color: var(--color-sidebar-muted);
  border-left: 2px solid transparent;
  transition: color 0.12s, background 0.12s;
}
.nav-item:hover:not(.active) {
  color: var(--color-sidebar-text);
  background: var(--color-sidebar-hover);
}
.nav-item.active {
  color: var(--color-sidebar-active-text);
  background: var(--color-sidebar-active-bg);
  border-left-color: var(--color-sidebar-active-line);
  border-radius: 0; /* active 项绝不使用圆角 */
}
.nav-item-dot {
  width: 5px; height: 5px;
  border-radius: 50%; background: currentColor; flex-shrink: 0;
}
.sidebar-footer {
  padding: 12px 16px;
  border-top: 0.5px solid color-mix(in srgb, var(--color-sidebar-muted) 25%, transparent);
  font-size: 11px; color: var(--color-sidebar-muted);
}
```

### TopBar CSS

```css
.topbar {
  height: var(--topbar-height);
  background: var(--color-topbar-bg);
  border-bottom: 0.5px solid var(--color-topbar-border);
  display: flex; align-items: center;
  padding: 0 24px; gap: 10px;
  position: sticky; top: 0; z-index: 50;
  flex-shrink: 0;
}
.topbar-title {
  font-size: 13px; font-weight: 500;
  color: var(--color-text-primary);
  letter-spacing: 0.05em;
}
.topbar-badge {
  font-size: 10px;
  color: var(--color-badge-text);
  background: var(--color-badge-bg);
  padding: 2px 8px; border-radius: 10px;
}
.topbar-actions { margin-left: auto; display: flex; gap: 8px; }
```

### 内容区卡片

```css
/* 统计数据卡片 */
.stat-card {
  background: var(--color-card-bg);
  border: 0.5px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px 18px;
}
.stat-card-label {
  font-size: 10px; color: var(--color-text-secondary);
  letter-spacing: 0.08em;
}
.stat-card-value {
  font-size: 22px; font-weight: 400;
  color: var(--color-text-primary); margin-top: 4px;
}
.stat-card-trend {
  font-size: 10px; color: var(--color-chart-accent);
  margin-top: 3px;
}

/* 通用内容卡片 */
.content-card {
  background: var(--color-card-bg);
  border: 0.5px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
}
.content-card-header {
  font-size: 13px; font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 0.5px solid var(--color-border);
  letter-spacing: 0.04em;
}

/* 卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}
```

---

## 八、图标使用规范

### Lucide React 安装

```bash
npm install lucide-react
```

### 使用规范

```tsx
// 统一 size=16，strokeWidth=1.5，细线感
import { LayoutDashboard, BarChart2, Settings } from 'lucide-react'

<LayoutDashboard size={16} strokeWidth={1.5} color="currentColor" />
```

### 侧栏导航图标

- 所有导航项图标使用 Lucide
- `size={16}`、`strokeWidth={1.5}`
- 颜色使用 `currentColor`，继承父元素文字色

---

## 九、Ant Design 主题覆盖

### ConfigProvider 配置（`src/App.tsx`）

```tsx
<ConfigProvider
  locale={zhCN}
  theme={{
    token: {
      colorPrimary:    '#4a5568',   // 方案 A 主色
      colorBgContainer: '#ffffff',
      borderRadius:    3,
      colorBorder:     '#e2e8f0',
      fontFamily:      'Noto Sans SC, PingFang SC, Microsoft YaHei, sans-serif',
      fontSize:        13,
    },
  }}
>
```

### 全局 CSS 覆盖（`src/styles/global.css`）

```css
/* 禁用 box-shadow（层次靠边框和背景色差异） */
.ant-card, .ant-btn, .ant-input, .ant-select-selector {
  box-shadow: none !important;
}

/* 按钮主色 */
.ant-btn-primary {
  background: var(--color-btn-bg);
  border-color: var(--color-btn-bg);
}

.ant-btn-primary:hover {
  background: var(--color-btn-hover);
  border-color: var(--color-btn-hover);
}
```

---

## 十、新页面开发清单

开发新页面时，按以下步骤操作：

### 1. 创建页面样式文件

```
src/pages/YourPage/
├── index.tsx
└── styles.css    ← 新建
```

### 2. 在 index.tsx 中引入样式

```tsx
import './styles.css'
```

### 3. 使用 CSS 变量，避免硬编码

```tsx
// ❌ 错误
<div style={{ background: '#f5f5f5' }}>

// ✅ 正确
<div className="my-container">  /* 在 styles.css 中使用 var(--color-page-bg) */
```

### 4. 页面标题区标准结构

```tsx
<div className="page-header">
  <Typography.Title level={4} className="page-title">
    页面标题
  </Typography.Title>
  <Button type="primary" icon={<PlusOutlined />}>
    操作按钮
  </Button>
</div>
```

### 5. 表格标准结构

```tsx
<Table
  dataSource={data}
  columns={columns}
  rowKey="id"
  className="data-table"  /* 在 styles.css 中定义边框和背景 */
/>
```

---

## 十一、ECharts 图表主题（可选）

### 安装

```bash
npm install echarts echarts-for-react
```

### 主题配置（`src/utils/echartsTheme.ts`）

```typescript
export const appTheme = {
  color: ['#4a5568', '#68d391', '#a0aec0', '#718096', '#cbd5e0'],
  backgroundColor: 'transparent',
  textStyle: {
    fontFamily: 'Noto Sans SC, PingFang SC, sans-serif',
    color: '#718096',
    fontSize: 12,
  },
  grid: { borderColor: '#e2e8f0' },
  categoryAxis: {
    axisLine: { lineStyle: { color: '#e2e8f0', width: 0.5 } },
    axisTick: { show: false },
    axisLabel: { color: '#a0aec0', fontSize: 11 },
    splitLine: { lineStyle: { color: '#f0f0f0', width: 0.5 } },
  },
  valueAxis: {
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#a0aec0', fontSize: 11 },
    splitLine: { lineStyle: { color: '#f0f0f0', width: 0.5 } },
  },
  bar: { itemStyle: { borderRadius: [2, 2, 0, 0] } },
  line: { lineStyle: { width: 1.5 }, symbol: 'none' },
}
```

---

## 十二、文件结构

```
frontend/src/
├── styles/
│   ├── variables.css      ← CSS 变量 Token
│   └── global.css         ← 全局样式 + Ant Design 覆盖
├── layouts/
│   ├── AuthLayout.tsx     ← 登录页布局（可选）
│   └── DashboardLayout.tsx ← 功能页布局（如拆分）
├── components/
│   ├── ui/
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Card.tsx
│   │   └── Badge.tsx
│   └── nav/
│       ├── Sidebar.tsx
│       ├── NavItem.tsx
│       └── TopBar.tsx
├── pages/
│   ├── Login/
│   │   ├── index.tsx
│   │   └── styles.css     ← 每页独立样式
│   ├── Documents/
│   │   ├── index.tsx
│   │   └── styles.css
│   └── ...
└── utils/
    └── echartsTheme.ts    ← 图表主题（可选）
```

---

## 十三、检查清单

每次 UI 提交前，确认以下事项：

- [ ] 所有颜色使用 CSS 变量，无硬编码 hex 值
- [ ] 无 `box-shadow`（除 focus ring）
- [ ] 无渐变背景
- [ ] 圆角 ≤ 4px
- [ ] 字重 ≤ 500
- [ ] 图标使用 Lucide（size=16, strokeWidth=1.5）
- [ ] TypeScript 类型检查通过（`npm run type-check`）
- [ ] 登录页/功能页符合布局规范
- [ ] 侧栏 active 项无圆角，左侧 2px 薄荷绿指示线

---

## 十四、版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-04-09 | 初始版本，方案 A 烟灰·霜白 |

---

**本规范由 CLAUDE.md 驱动，所有前端开发必须遵守。**
