# intelligentbase

通用 RAG + 多智能体**基础架构基座**：一套可复用于多个项目的本地知识库 + 检索增强 + 多智能体编排底座。

独立于 FreeArk 演进，**不替换** FreeArk；目标是沉淀一个可迁移、可复用的工程化基座。

## 定位

- **开源标准向量库**：Qdrant（Apache-2.0，裸 `.deb` 本地部署）
- **开源 embedding**：bge-m3（1024 维 dense，cosine 相似度，本地 CPU 推理，独立 `ib-embed` 服务）
- **Web 数据导入**：Word / PDF / Markdown 等，带分块（chunking）+ OCR + 图片回溯
- **多智能体**：LangChain + LangGraph 编排（路由 / 工具 / 专家）
- **LLM**：云端 DeepSeek（`langchain-openai`，pin `<0.3`）
- **Web**：Django + DRF + Waitress/Gunicorn + **原生 SSE**（`StreamingHttpResponse`，无 Channels / 无 Redis）
- **前端**：Vue 3 + Vite，`fetch` + `Authorization: Bearer`（无 axios）

## 目录结构

```
docs/           需求 / 架构 / 模块设计 / 测试与部署文档（SDLC 全链路产物）
src/
  ib/           框架无关核心（解析 / 分块 / embedding / 检索 / 编排 / 路由 / 工具）
  ib_embed/     bge-m3 embedding 独立推理服务
  ibweb/        Django Web（REST + SSE）
  frontend/     Vue 3 前端
  deploy/       systemd unit、nginx 配置、部署清单
tests/          unit / integration / e2e
```

## 关键设计决策

| 决策 | 选择 | 依据 |
|------|------|------|
| 向量库 | Qdrant | Apache-2.0，本地裸装 |
| Embedding | bge-m3 (1024-dim) | MIT，本地推理，非豆包 |
| Web 实时 | 原生 SSE | 免 Redis/Channels 复杂度 |
| 隔离 | collection-per-project（硬）+ filter（软） | 单实例多项目 |
| 存储 | SQLite WAL ledger + sha256 blob store | 无外部依赖，账本即队列 |
| 部署 | 物理机直部署（禁 Docker） | 沿用 FreeArk 约束 |

## 文档入口

- [需求规格](docs/requirements_spec.md) · [用户故事](docs/user_stories.md)
- [架构决策 ADR](docs/architecture_design.md) · [模块设计](docs/module_design.md) · [技术选型](docs/tech_stack.md)
- [测试计划](docs/test_plan.md) · [测试报告](docs/test_report.md)
- [部署计划](docs/deployment_plan.md) · [CI/CD 流水线](docs/cicd_pipeline.md)

## 快速开始（本地开发）

```bash
cd src
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py test                          # SQLite / InMemory，不连外部服务
```

> 生产部署见 `docs/deployment_plan.md`；embedding 模型权重不入 git，部署时离线下载 bge-m3。
