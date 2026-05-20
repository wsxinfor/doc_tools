# frontend/CLAUDE.md

> 所有模块（FM1-FM6 + 管理员页面）已完成。本文件只保留结构参考。
> 任务卡已删除——如需查看原始需求，参考 git 历史。

---

## 目录结构

```
src/
├── pages/    Login | Documents | AIProcess | Templates/TemplateEditor | Render | Admin
├── api/      client(axios+interceptors) | auth | documents | aiProcess | templates | render
├── stores/   authStore(持久化) | renderStore(排版流程临时态，不持久化)
├── components/ Layout | FontSizePicker | FontPicker | ColorPicker
└── types/    api.ts | template.ts
```

## 路由

```
/login | /documents | /ai-process/:docId | /templates | /templates/new | /templates/:id/edit
/render/new | /render/:taskId | /render/history | /admin/users | /admin/settings
```

## 关键约定

- `renderStore` 不持久化 — 刷新后 cleanedText/structure 清空，需重新走 AI 流程
- 字体大小用 `FontSizePicker`（小四/四号等中文名，value 为 pt 数值）
- 模板默认英文字体：Times New Roman
- API 请求走 `src/api/client.ts`（自动注入 Bearer token，401 跳 /login）

## 检查

```bash
npx tsc --noEmit
npm run lint
```
