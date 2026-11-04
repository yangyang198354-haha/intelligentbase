# DeepSeek Search / Fetch API 资料存档（画像 P11-3 依据）

- 出处：DeepSeek 官方文档 https://api-docs.deepseek.com/guides/search
- 摘录时间：2026-11-02（主会话据官方页面整理；页面未写上线日期，写明计费自北京时间 2026-11-01 00:00 起）
- 本文件不含任何凭据。密钥复用现有 DeepSeek API Key，只在 `/etc/intelligentbase/ib-web.env` 中配置，不写值。

## 端点与鉴权

| API | 方法 | URL |
|---|---|---|
| Search | POST | `https://api.deepseek.com/v1/tools/search` |
| Fetch | POST | `https://api.deepseek.com/v1/tools/fetch` |

请求头（两者都需要）：
- `Authorization: Bearer <DeepSeek API Key>`
- `Content-Type: application/json`

请求和响应都是 JSON。请求体里的未知字段会被忽略。

## Search 请求

| 字段 | 类型 | 必填 | 默认 | 含义 |
|---|---|---|---|---|
| `query` | string | 是 | — | 1–128 个 Unicode 字符，不能全是空白；支持下列操作符 |
| `count` | integer | 否 | 10 | 返回条数，1–50 |
| `ori_question` | string | 否 | — | 用户的原始问题，1–128 字符，帮助理解查询；`null` 视为未提供 |
| `localization` | string | 否 | `""` | 用于本地化结果的 IP 地址 |
| `need_content` | boolean | 否 | false | true 时在 `content` 返回正文；false 时 `content` 恒为空串 |

查询操作符（可以在同一个查询里组合使用）：
- `site:` 限定站点，多个站点用空格分隔并用 `OR` 连接
- `-site:` 排除站点
- `-词` 排除含该词的页面
- `-"短语"` 排除精确短语
- `"短语"` 精确匹配
- `lang:zh,en` 限定语言
- `after:` / `before:` 按发布日期过滤，格式为 `YYYY` 或 `YYYY-MM-DD`

## Search 响应

HTTP 200，返回 `{"results": [...]}`；没有匹配时返回空数组。每条结果包含：

| 字段 | 类型 | 含义 |
|---|---|---|
| `rerank_score` | number | 0–3，综合相关性、权威性、时效性；≥1.5 为高质量 |
| `title` | string | 标题 |
| `url` | string | 网址 |
| `snippet` | string | 短摘要，约 100–200 字，用于界面展示 |
| `summary` | string | 长摘要，约 600–800 字，供模型使用 |
| `content` | string | 正文；`need_content=false` 或正文不可得时为空 |
| `site_name` | string \| null | 站点名 |
| `site_icon` | string \| null | 站点图标 URL |
| `date` | string \| null | 发布时间，UTC，RFC 3339 格式 |
| `authority` | integer | 权威等级 0–4，-1 表示未知；≥3 为高权威 |

## Fetch 请求与响应

请求：`url`（string，必填）。要求：不超过 8192 字符，必须是带主机名的 http 或 https 地址，且不能包含用户名或密码。

响应：`title`（string，取不到时为空串）和 `content`（Markdown 正文）。能否抓到内容取决于目标站点的可用性和访问策略。

## 错误

错误格式兼容 OpenAI：`error.message`、`error.type`（如 `invalid_request_error`）、`error.param`（恒为 null）、`error.code`。

| HTTP | 含义 | 是否重试 |
|---|---|---|
| 400 | 请求头或请求体非法（JSON 格式错误、字段值非法） | 否，需修改请求 |
| 401 | Key 缺失或无效 | 否 |
| 402 | 账户余额不足 | 充值后再重试 |
| 403 | Fetch 请求被安全策略拒绝 | 否 |
| 404 | Fetch 没有拿到可用内容（URL 不可用、被站点策略屏蔽、目标站出错、内容类型不支持、提取不出 Markdown） | 否 |
| 408 | 读取请求体超时 | 等待后重试 |
| 413 | 请求体过大 | 否 |
| 429 | 超出 QPS 限制（账户级，或 Fetch 的单域名限制） | 等待后重试 |
| 500 | 服务端内部错误 | 等待后重试 |
| 504 | 下游请求超时 | 等待后重试 |

两个接口都是只读的，没有副作用。

## 限流与计费

- QPS：Search 100，Fetch 25。按账户计，与用哪个 Key 无关；两个接口分别计数，也不占用模型并发额度。
- Fetch 另有单域名 QPS 限制，超出返回 429，文档没给具体数值。
- 价格：Search 和 Fetch 都是每 1000 次成功请求 0.75 美元，`count` 不影响价格。
- 只有返回 HTTP 200 且有结果才计费：Search 要求 `results` 非空，Fetch 要求返回了正文。失败、空结果、超时都不计费。
- 文档没有给出具体的超时数值。

## 示例请求体（来自官方页面）

```json
{"query": "DeepSeek V4 release", "count": 5, "need_content": true}
```

```json
{"url": "https://example.com/article"}
```

## 测试替身

没有官方沙箱。测试只能用项目自己的离线替身，按本文件的字段和错误码构造响应；自动化测试中禁止调用真实端点。
