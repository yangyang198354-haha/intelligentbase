<file_header>
  <project>intelligentbase</project>
  <artifact>r2_apply_package_part6</artifact>
  <path>docs/r2_apply_package_part6.md</path>
  <doc_id>APPLY-INTELBASE-R2-001-P6</doc_id>
  <version>1.0.0</version>
  <revision>R2</revision>
  <status>APPLY_READY</status>
  <phase>GROUP_B / R2 补交（L-03）</phase>
  <author>sub_agent_system_architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-004</invocation_id>
  <created_at>2026-09-26</created_at>
  <targets>docs/tech_stack.md（TS-04 ~ TS-07：bge-m3 加载库选型行改写 / 许可台账新增行 / §1.2 服务端配置键登记 / §5.2 指令集风险行）</targets>
  <scope_boundary>只含编辑指令（锚点 + 新内容）。不含实现代码、伪代码、部署脚本、凭据或键值。配置项只登记**键名与语义**。</scope_boundary>
</file_header>

# R2 APPLY-READY 修订包（part6）— tech_stack.md（TS-04 ~ TS-07）

> 承接 part5 的 TS-01 ~ TS-03（文件头 / revision_history / 首部版本行与 R2 摘要）。本册为 tech_stack.md 的**实体改动**。

---

### TS-04 · tech_stack.md — §1「Embedding 推理运行时」行改写（**bge-m3 加载库选型**；R2 核心项）

目标文件：`docs/tech_stack.md`
锚点（唯一；原文照抄）:
```text
| Embedding 推理运行时 | `FlagEmbedding`（首选）/ `sentence-transformers`（备选） | 部署时锁定 | 两者均为宽松许可；`FlagEmbedding` 为 BAAI 官方，对 bge 系列适配最直接；两者均支持 CPU | REQ-FUNC-IB-15 | 中 | 许可：`FlagEmbedding` MIT / `sentence-transformers` Apache-2.0。**最终择一须在 GROUP_C 以目标机实测（[TBD-T1]）为依据**，此处不预先拍板 |
```
新内容（整段替换锚点，仍为**单行表格行**）:
```text
| **Embedding 推理运行时（R2 改写）** | **三候选**：① `FlagEmbedding`（BAAI 官方）；② `sentence-transformers`；③ **直接以 `onnxruntime` 载 bge-m3 的 ONNX 导出** | 部署时锁定（**三者择一，不得并行安装**） | **选择依据（R2 显式化）**：① 对 bge 系列适配最直接、抽象层最少，但**带入 `torch` + `transformers`** 两条传递依赖（磁盘与内存面最大）；② 生态最广、CPU 支持成熟，同样带入 `torch` / `transformers`，且对 bge-m3 的多向量能力支持弱于 ①；③ **唯一不引入 `torch` 的路径**（仅 `onnxruntime`），bge-m3 官方提供 ONNX 权重，**CPU-only 可用**、内存面最小 —— 目标机内存仅 11GiB 且 OCR 链路**已依赖 `onnxruntime`**，选 ③ 可与之共享同一运行时依赖，代价是**须自行承担 tokenizer 与池化后处理**（1024 维 + L2 归一化的契约责任仍落在本行，与 §1「Embedding 模型」行一致）。**许可**：① MIT / ② Apache-2.0 / ③ MIT（`onnxruntime`）——三者均为宽松许可，**无一触犯 REQ-NFR-IB-12**。**CPU-only 可用性**：三者均可纯 CPU 运行、**均不需 GPU/CUDA**（③ 须选 CPU 版 wheel，**不得**装 GPU 版） | REQ-FUNC-IB-15；REQ-NFR-IB-10；REQ-NFR-IB-12 | **高** | **最终择一须在 GROUP_C 以目标机实测为依据**（[TBD-T1] 延迟 / [TBD-T4] 内存 / **[TBD-T18] 指令集基线**），此处不预先拍板；→ **指令集风险（R2 新发现）**：目标机 CPU 缺 **AVX2**，① / ② 经 PyTorch、③ 经 `onnxruntime`，其**预编译 x86_64 wheel 均可能触发 SIGILL**（非法指令，进程级崩溃，**不可捕获**）→ 缓解与判定见 §5.2 与 [TBD-T18]；→ **硬约束提醒（R2 重申）**：本项**不得**以 `PyMuPDF` 或任何 AGPL / copyleft 组件替代（见 §1.1），**不得**引入 Docker / 容器化（DR-03）；→ 若选 ① / ②，须在 §2 台账以**条件性采纳**登记传递依赖 `torch`（BSD-3-Clause）与 `transformers`（Apache-2.0） |
```

**说明（不写入文档，仅供 PM 施加时理解）**：该行**风险等级由「中」升为「高」**，原因是 [TBD-T18] 的 SIGILL 属**进程级不可捕获崩溃**（比「延迟不达标」严重一档）；此升级已在 part5 的 R2 修订摘要与 ADR-06-R2 复核句中登记。

---

### TS-05 · tech_stack.md — §2 许可台账新增两行（传递依赖）

目标文件：`docs/tech_stack.md`
锚点（唯一；原文照抄）:
```text
| `sentence-transformers` | Apache-2.0 | 宽松 | 采纳（备选） |
```
新内容（保留锚点行，其后追加两行）:
```text
| `sentence-transformers` | Apache-2.0 | 宽松 | 采纳（备选） |
| **`torch`（R2 新增；传递依赖，条件性）** | **BSD-3-Clause** | 宽松 | **条件性采纳**：仅当选 §1「Embedding 推理运行时」的 ① / ② 时才进入依赖集；选 ③（onnxruntime 直载）则**不引入**。许可本身合规，但**体积与内存面最大**，且是 [TBD-T18] 指令集风险的主要来源 |
| **`transformers`（R2 新增；传递依赖，条件性）** | **Apache-2.0** | 宽松 | **条件性采纳**：同 `torch`，仅 ① / ② 路径引入；③ 路径**不引入**（tokenizer 职责由本基座自行承担） |
```

**并追加一条遗留合规动作**（锚点 = §2 末的「遗留合规动作」段）:
锚点（唯一；原文照抄）:
```text
**遗留合规动作（部署阶段）**：`pypdf` / `pdfminer.six` / `pdfplumber` / `pypdfium2` 的实际许可文本须在锁定版本后**从发行包内 `LICENSE` 文件复核**（发行方可能随版本调整），复核结果记入部署记录。**（R1 追加）** 同规则适用于 **Django / DRF / Waitress / Gunicorn**（及条件性引入的 Uvicorn）。
```
新内容（保留锚点段，其后追加一句）:
```text
**遗留合规动作（部署阶段）**：`pypdf` / `pdfminer.six` / `pdfplumber` / `pypdfium2` 的实际许可文本须在锁定版本后**从发行包内 `LICENSE` 文件复核**（发行方可能随版本调整），复核结果记入部署记录。**（R1 追加）** 同规则适用于 **Django / DRF / Waitress / Gunicorn**（及条件性引入的 Uvicorn）。**（R2 追加）** 同规则适用于**实际选中的 Embedding 推理运行时**及其**传递依赖**（若选 ① / ② 则含 `torch` / `transformers`；若选 ③ 则含 `onnxruntime` 与 bge-m3 的 ONNX 权重再分发条款）—— **传递依赖的许可亦须逐条留痕**，不得只登记直接依赖。
```

---

### TS-06 · tech_stack.md — 新增 §1.2 服务端配置键登记

目标文件：`docs/tech_stack.md`
锚点（唯一；原文照抄）:
```text
## 2. 许可合规台账（REQ-NFR-IB-12）
```
新内容（在锚点**之前**插入新小节，再保留锚点）:
```text
### 1.2 服务端配置键登记（**R2 新增**；只登记键名与语义，**不含任何值**）

> **用途**：`ib-embed`（MOD-IB-26）此前**无服务端配置契约**（L-03）。本表登记其配置**键名**，使 `IFC-IB-286`（第二份 `EnvironmentFile` 模板）有据可依。**语义与默认值以 `docs/ib_embed_service_contract.md` §9 为准**（唯一落点），本表为**键名清单视图**。
> **凭据纪律（强制）**：`ib-embed` **不需要任何令牌** —— 该文件**不得**出现任何凭据型键名或值。若有人为它加鉴权令牌，是**净增凭据面**，须先回架构层评审。

| 键名 | 语义（一句话） | 关联 IFC |
|------|---------------|----------|
| `IB_EMBED_HOST` | 监听地址（默认仅本机回环） | IFC-IB-274 |
| `IB_EMBED_PORT` | 监听端口（客户端 `LocalHttpEmbedder` 的目标端口） | IFC-IB-266 / IFC-IB-274 |
| `IB_EMBED_MODEL_ID` | 模型标识（须与 `/descriptor` 回报一致） | IFC-IB-271 |
| `IB_EMBED_DIM` | 向量维度（须 = 客户端 `IB_EMBED_DIM` = `CollectionSpec.dim` = 1024，三方一致性） | IFC-IB-267 |
| `IB_EMBED_MODEL_PATH` | 本地权重**目录**（离线加载，不联网下载） | IFC-IB-270 |
| `IB_EMBED_MAX_BATCH` | 单请求批上限（**硬约束：≥ 客户端 `cold_batch_size`**） | IFC-IB-272 |
| `IB_EMBED_MAX_TOKENS` | 单条截断上限（保前缀） | IFC-IB-272 |
| `IB_EMBED_MAX_CONCURRENCY` | 推理并发上限（**有界**，不设无界） | IFC-IB-268 |
| `IB_EMBED_QUEUE_DEPTH` | 排队深度上限（超限**快速失败**并回显 `retry_after_s`，**绝不无界排队**） | IFC-IB-268 |
| `IB_EMBED_THREADS` | 推理线程数（与 Qdrant / `ib-web` / OCR 同为 CPU 竞争者） | IFC-IB-274 |
| `IB_EMBED_MEMORY_LIMIT_MB` | 服务端内存上限（**须与单元文件 `MemoryMax` 一致**） | IFC-IB-274 |

**未列出的键**：`IB_EMBED_BACKEND` 属**客户端**（`ib-web`）配置，**不在本表**；`IB_EMBED_TIMEOUT_*` / `IB_EMBED_RETRY_*` 亦属**客户端**冷/热双路径实例（IFC-IB-273：**服务端不区分冷热**）。**此处不得为服务端补一套超时/重试键**——那会把冷热纪律从客户端**双落点**化，破坏 ADR-02-R2 附注的单一落点。

---

## 2. 许可合规台账（REQ-NFR-IB-12）
```

---

### TS-07 · tech_stack.md — §5.2 中风险新增一行（目标机指令集基线 → SIGILL）

目标文件：`docs/tech_stack.md`
锚点（唯一；原文照抄 — §5.2 表的最后一行）:
```text
| 云端 LLM 不可达/限流 | 问答不可用 | §7.4 降级矩阵：`error` 事件 + 可读文案；路由降级到关键词档位 | REQ-NFR-IB-13 |
```
新内容（保留锚点行，其后追加一行）:
```text
| 云端 LLM 不可达/限流 | 问答不可用 | §7.4 降级矩阵：`error` 事件 + 可读文案；路由降级到关键词档位 | REQ-NFR-IB-13 |
| **（R2 新增）目标机 CPU 缺 AVX2 → 预编译 wheel 触发 SIGILL** | **进程级崩溃（不可捕获），非降级**：`ib-embed` 与 OCR 链路**双双不可用**；且**开发机（新 CPU）可用掩盖问题**，只在目标机暴露 | ① **[TBD-T18] 目标机实测优先**：先跑「导入 + 一次真实推理」的最小探针，**不以 `pip list` 或开发机结果代替**；② 判定后三选一 —— **换用无 AVX2 依赖的构建**（如 CPU 版 wheel 的兼容包）/ **自源码编译并关闭 AVX2**（`-mno-avx2` 类开关）/ **降级到纯 Python 后备路径**；③ **两条链路须合并评估**（OCR 的 `onnxruntime` 与 R2 的推理运行时**同源**）：分别修会重复踩坑且排障归因错误；④ 若实测确有 SIGILL 且无可用构建，须**回 PM 裁决**是否放宽 DR-08 / 降级 OCR 能力（**不得**以引入 PyMuPDF 或 Docker 规避） | REQ-NFR-IB-10；AC-IB-07-05；ADR-02 / ADR-06 / ADR-12；[TBD-T18] |
```

---

（part6 结束；§6 自检行、§4.2/§4.3 检查项、文件头 hygiene、条目计数与残余项 R-1~R-9 见 `docs/r2_apply_package_part7.md`）
