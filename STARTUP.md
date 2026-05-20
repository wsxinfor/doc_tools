# DocFormat 启动与关闭指南

---

## 快速启动/关闭

### 启动全部服务
```bash
# 1. 启动数据库（Docker）
docker-compose -f docker-compose.dev.yml up -d

# 2. 启动后端（新终端，backend/ 目录）
cd D:/claude/doc-tools/backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0

# 3. 启动前端（新终端，frontend/ 目录）
cd D:/claude/doc-tools/frontend
npm run dev -- --host 0.0.0.0
```

### 关闭全部服务
```bash
# 1. 关闭数据库
docker-compose -f docker-compose.dev.yml down

# 2. 关闭后端/前端
# 在对应终端按 Ctrl+C，或执行：
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

---

## 详细步骤

### 一、数据库服务

| 操作 | 命令 |
|------|------|
| 启动 | `docker-compose -f docker-compose.dev.yml up -d` |
| 关闭 | `docker-compose -f docker-compose.dev.yml down` |
| 查看状态 | `docker-compose ps` |
| 查看日志 | `docker-compose logs -f` |
| 重启 | `docker-compose restart` |

**端口映射**：本机 5433 → 容器 5432（PostgreSQL）

---

### 二、后端服务（FastAPI）

| 操作 | 命令 |
|------|------|
| 启动 | `cd backend` + `.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0` |
| 关闭 | 终端按 `Ctrl+C` |
| 访问文档 | http://localhost:8000/docs |

**依赖检查**：
```bash
# 确认虚拟环境存在
ls backend/.venv/Scripts/python.exe

# 确认端口未被占用
netstat -ano | findstr :8000
```

---

### 三、前端服务（Vite + React）

| 操作 | 命令 |
|------|------|
| 启动 | `cd frontend` + `npm run dev -- --host 0.0.0.0` |
| 关闭 | 终端按 `Ctrl+C` |
| 访问地址 | http://localhost:5173 |

**依赖检查**：
```bash
# 确认 node_modules 存在
ls frontend/node_modules

# 确认端口未被占用
netstat -ano | findstr :5173
```

---

## 常见排错

### 1. 端口被占用

**错误现象**：`Address already in use` 或启动后立即退出

**解决方法**：
```bash
# 查找占用进程
netstat -ano | findstr :8000   # 或 :5173

# 杀死进程（PID 替换为实际值）
taskkill /F /PID <PID>

# 或一键关闭所有相关进程
taskkill /F /IM python.exe
taskkill /F /IM node.exe
```

---

### 2. 数据库连接失败

**错误现象**：后端启动时报 `connection refused` 或 `database does not exist`

**检查步骤**：
```bash
# 1. 确认 Docker 容器运行中
docker-compose ps

# 2. 查看数据库日志
docker-compose logs postgres

# 3. 测试连接（密码：postgres）
docker-compose exec postgres psql -U postgres -d docformat
```

**修复**：
```bash
# 重启数据库
docker-compose down && docker-compose up -d

# 重新运行迁移（后端目录）
.venv/Scripts/python.exe -m alembic upgrade head
```

---

### 3. 虚拟环境问题

**错误现象**：`.venv/Scripts/python.exe: command not found`

**解决方法**：
```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
```

---

### 4. 前端依赖缺失

**错误现象**：`npm run dev` 报错 `module not found`

**解决方法**：
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

---

### 5. AI 服务不可用

**错误现象**：调用 AI 接口超时或返回 401

**检查步骤**：
1. 登录管理员页面（admin / admin123456）
2. 检查「系统配置」中的 AI Provider 和 API Key
3. 使用「测试连接」按钮验证

**默认配置**：
- Provider: `tongyi`（通义千问）
- 需在 `.env` 或数据库中配置 API Key

---

### 6. 静态资源 404

**错误现象**：footer logo 等图片无法加载

**检查路径**：`backend/app/static/footer_logo.png`

**修复**：确认文件存在，或从 `1.docx` 重新提取 logo。

---

## 服务状态速查

```bash
# 数据库
docker-compose ps

# 后端（端口监听）
netstat -ano | findstr :8000

# 前端（端口监听）
netstat -ano | findstr :5173

# Docker 日志
docker-compose logs -f

# 后端进程
tasklist | findstr python

# 前端进程
tasklist | findstr node
```

---

## 完整重启流程

```bash
# 1. 关闭所有服务
taskkill /F /IM node.exe
taskkill /F /IM python.exe
docker-compose down

# 2. 等待 2 秒后重新启动
docker-compose up -d
sleep 2

# 3. 启动后端（新终端 1）
cd D:/claude/doc-tools/backend
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0

# 4. 启动前端（新终端 2）
cd D:/claude/doc-tools/frontend
npm run dev -- --host 0.0.0.0
```

---

## 联系支持

内部问题请提交至：北京昱华源码科技有限公司 - 技术部


sk-8b19e4d541a847fb8fbe22252a828864