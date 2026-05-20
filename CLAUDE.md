# CLAUDE.md — DocFormat 项目根目录

> 所有模块（M1-M6 / FM1-FM6）已完成。当前处于维护/迭代阶段。

---

## 网络环境说明

本项目开发环境为 **WSL2 Ubuntu**（项目位于 `/mnt/d/claude/doc-tools`，D 盘挂载），验证和测试在 **Windows 宿主机浏览器** 中进行。

### 核心规则：所有服务必须绑定 0.0.0.0

WSL2 的 `127.0.0.1` 和 Windows 的 `127.0.0.1` 不是同一个网络空间。
所有启动的服务必须绑定 `0.0.0.0`，否则 Windows 浏览器无法访问。

### 项目标识

- 项目名称：doc-tools
- 后端端口：8000
- 前端端口：5173
- 日志文件：/tmp/doc-tools-backend.log

### 重要规则
- 只操作本项目目录下的文件
- 只管理本项目的端口（8000、5173）
- 发现其他端口的进程不要关闭

### 项目启动命令

```bash
# 后端（WSL2 中）
source .venv_linux/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（WSL2 中）
npm run dev -- --host 0.0.0.0

# Docker 数据库（端口映射已由 docker-compose 处理）
docker-compose -f docker-compose.dev.yml up -d
```

### 配置文件中同样适用
```python
# ❌ 错误
host = "127.0.0.1"

# ✅ 正确  
host = "0.0.0.0"
```

### 验证方式
Windows 浏览器访问 `http://localhost:端口号` 即可（如 `http://localhost:8000/docs`、`http://localhost:5173`）。

---

## §1 项目概述

**项目**：DocFormat — 北京昱华源码科技有限公司内部智能文档排版工具
**流程**：上传 Word/MD → AI 清洗 + 结构识别（用户确认）→ 套用模板 → 输出 Word
**公司常量**：`DEFAULT_COMPANY_NAME = "北京昱华源码科技有限公司"`（封面/页脚，禁止硬编码）

**技术栈**：React 18 + TypeScript + Vite + Ant Design | Python 3.11 + FastAPI + SQLAlchemy + Alembic | PostgreSQL | python-docx + mammoth | 通义千问/OpenAI Adapter

---

## §2 启动与配置

```bash
# 数据库（Docker）
docker-compose -f docker-compose.dev.yml up -d

# 后端（backend/）
source .venv_linux/bin/activate && uvicorn app.main:app --port 8000 --host 0.0.0.0

# 前端（frontend/）
npm run dev -- --host 0.0.0.0
```

**端口**：前端 5173 / 后端 8000 / 数据库 5433（本机 PG16 占用 5432）

**迁移 & 初始化**（首次）：
```bash
alembic upgrade head
python scripts/create_admin.py   # admin / admin123456
```

---

## §2.5 前端 UI 规范

**规范文档**：`frontend/UI_GUIDE.md`

**色彩方案**：方案 A · 烟灰·霜白
- 侧栏背景：`#4a5568` 暖灰色
- Active 指示线：`#68d391` 薄荷绿（左侧 2px 边框）
- 页面底色：`#f7f8fa` 霜白色

**核心规则**：
- ✅ 所有颜色使用 CSS 变量（`--color-*`）
- ✅ 0.5px 细边框，无阴影（`box-shadow: none`）
- ✅ 圆角 ≤ 4px，字重 ≤ 500
- ✅ 图标使用 Lucide React（size=16, strokeWidth=1.5）
- ❌ 禁止渐变背景、禁止实心图标、禁止硬编码 hex 颜色值

---

## §3 Always / Never

```
✅ 超过 3 个文件改动前，先列计划等确认
✅ 所有外部输入用 Pydantic 校验
✅ DDL 改动必须写 Alembic 迁移（含 downgrade）
✅ AI 结果必须经用户确认才能进入下一步
✅ 公司名称从 DEFAULT_COMPANY_NAME 读取

❌ 测试未通过不 commit
❌ 业务代码不直接 import AI SDK，必须通过 adapters/ 层
❌ 不自动 git push
❌ 不混合多模块改动到同一 commit
```

---

## §4 核心数据模型

```
User:        id, username, password_hash, role(admin|user), is_active
Document:    id, filename, file_path, file_type(docx|md), uploader_id, is_deleted
Template:    id, name, config(JSONB), created_by, is_deleted
RenderTask:  id, document_id, template_id, status(pending|processing|done|failed),
             ai_clean_result(TEXT), ai_structure(JSONB), result_path, preview_path,
             error_message, created_by
SystemConfig: key, value（AI provider/key，加密存储）
```

**模板 config 顶层结构**：`cover | header_footer | headings(h1-h4) | toc | body | figure`

---

## §5 已知问题

- 本机 PG16 占用 5432，Docker 映射 5433:5432，DATABASE_URL 必须使用 5433 端口

---

## §6 提交规范

```
feat|fix|test|refactor|chore|docs|migrate(模块): 描述

不自动 push；同模块 API 和前端分两次 commit
```

---

## §7 错误处理

```
错误格式：{ "code": "CODE", "message": "描述", "detail": null }
400 入参错误 | 401 未认证 | 403 无权限 | 404 不存在 | 422 业务规则违反 | 500 内部错误
AI 失败：{ "status": "ai_failed", "message": "..." }（不阻断流程）
```
