# backend/CLAUDE.md

> 所有模块（M1-M6）已完成。本文件只保留结构参考和关键规范。
> 任务卡已删除——如需查看原始需求，参考 git 历史。

---

## 目录结构

```
backend/app/
├── api/          auth | documents | ai_process | templates | render | admin_settings
├── services/     auth | document | ai | template | render | preview
├── models/       user | document | template | render_task
├── schemas/      auth | document | template | render | ai
├── adapters/     base(AIAdapter) | qwen | openai_adapter | factory
└── core/         config | security | database | exceptions
```

## 关键文件

| 文件 | 说明 |
|------|------|
| `services/render_service.py` | 排版引擎，当前主要维护点 |
| `adapters/factory.py` | AI provider 工厂，从 SystemConfig 读配置 |
| `core/config.py` | pydantic-settings，DATABASE_URL 用 5433 |
| `app/static/footer_logo.png` | 页脚 logo，从 1.docx 提取 |

## API 约定

```python
# 成功：{ "data": {...}, "message": "ok" }
# 错误：{ "code": "CODE", "message": "描述", "detail": null }
# 认证：Authorization: Bearer <token>
```

## 测试

```bash
mypy app/
ruff check app/
pytest tests/ -v
```
