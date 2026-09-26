<file_header>
  <project>intelligentbase</project>
  <artifact>r2_apply_package_part7</artifact>
  <path>docs/r2_apply_package_part7.md</path>
  <doc_id>APPLY-INTELBASE-R2-001-P7</doc_id>
  <version>1.0.0</version>
  <revision>R2</revision>
  <status>APPLY_READY</status>
  <phase>GROUP_B / R2 补交（L-03）</phase>
  <author>sub_agent_system_architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-004</invocation_id>
  <created_at>2026-09-26</created_at>
  <targets>docs/tech_stack.md（TS-08 ~ TS-10）；本修订包的条目计数、施加顺序与残余项</targets>
  <scope_boundary>只含编辑指令（锚点 + 新内容）与台账。不含实现代码、伪代码、部署脚本、凭据或键值。</scope_boundary>
</file_header>

# R2 APPLY-READY 修订包（part7）— tech_stack.md 收尾 + 计数与残余项

---

## 1. tech_stack.md（TS-08 ~ TS-10）

### TS-08 · tech_stack.md — §6 自检声明追加 R2 行

目标文件：`docs/tech_stack.md`
锚点（唯一；原文照抄 — §6 的最后一行）:
```text
- 本阶段**止于 GROUP_B**：产出后停止，等待 PM 门控评审，不进入 GROUP_C。
```
新内容（保留锚点行，其后追加）:
```text
- 本阶段**止于 GROUP_B**：产出后停止，等待 PM 门控评审，不进入 GROUP_C。
- **（R2）L-03 补交已完成**：新增 **§1.2 服务端配置键登记**（`ib-embed` / MOD-IB-26 的配置**键名**清单，**只登记键名与语义、不含任何值**，对应 IFC-IB-286 的第二份 `EnvironmentFile`）；「Embedding 推理运行时」行改写为**三候选**并显式化**选择依据 / 许可 / CPU-only 可用性 / 传递依赖 / 指令集基线风险**；§2 台账补登传递依赖 `torch`（BSD-3-Clause）与 `transformers`（Apache-2.0）（**条件性采纳**）；§5.2 新增**目标机缺 AVX2 → SIGILL** 风险行（该风险**同时命中既有 OCR 链路**，须合并评估）。
- **（R2）技术面硬约束未松动**：**未引入 PyMuPDF**（仍为 AGPL-3.0，不采纳）、**未引入 Docker/容器化**（DR-03）、**未引入 Redis/RabbitMQ**；新候选 ③（`onnxruntime` 直载）与既有 OCR 运行时**同组件**，**未净增组件面**。
- **（R2）凭据纪律**：§1.2 **只登记键名**；`ib-embed` **不需要任何令牌**，其 `EnvironmentFile` **不得**写入任何凭据；全文**不含任何键值**。
- **（R2）未改动他处**：`FreeArk` 仓库**任何文件未作修改**；需求侧文档（`requirements_spec.md` / `user_stories.md`）**未作修改**；`architecture_design.md` / `module_design.md` 的 R1 结论**未改写**（R2 只追加）。
```

### TS-09 · tech_stack.md — §4.2 / §4.3 验证清单各补一项（指令集基线）

目标文件：`docs/tech_stack.md`

**A · §4.2 Embedding 验证清单**
锚点（唯一；原文照抄 — §4.2 表的最后一行）:
```text
| 10 | 与 Qdrant 距离度量对齐（余弦 vs 余弦） | 跨层检索分数量级合理 |
```
新内容（保留锚点行，其后追加一行；序号顺延）:
```text
| 10 | 与 Qdrant 距离度量对齐（余弦 vs 余弦） | 跨层检索分数量级合理 |
| **11** | **（R2）目标机指令集基线：推理运行时在目标机完成一次**真推理**（非仅 `pip list`）且**进程未崩溃** | `SIGILL` 零命中；记录目标机 CPU 指令集（是否含 AVX2）→ **[TBD-T18]**；**不得以开发机结果替代**（AC-IB-07-05 同精神） |
```

**B · §4.3 OCR 链路验证清单**
锚点（唯一；原文照抄 — §4.3 表的最后一行）:
```text
| 6 | 单文档入库时长上界已实测（含 OCR） | 记录 [TBD-T11]（用于校准租约时长） |
```
新内容（保留锚点行，其后追加一行；序号顺延）:
```text
| 6 | 单文档入库时长上界已实测（含 OCR） | 记录 [TBD-T11]（用于校准租约时长） |
| **7** | **（R2）OCR 的 `onnxruntime` 在同一目标机上完成一次真推理且进程未崩溃** | 与 §4.2 第 11 项**同源风险**（[TBD-T18]），**须合并判定**：两者若均触发 `SIGILL`，须一并处置构建方式，不得分别归因 |
```

### TS-10 · tech_stack.md — 文件头 hygiene（时间戳 / 输入版本 / 新增输入）

目标文件：`docs/tech_stack.md`

**A · `<updated_at>`**
锚点（唯一；原文照抄）:
```text
  <updated_at>2026-09-25</updated_at>
```
新内容（整段替换锚点）:
```text
  <updated_at>2026-09-26</updated_at>
```

**B ·  Architecture design 输入版本**
锚点（唯一；原文照抄）:
```text
    <input path="docs/architecture_design.md" version="1.1.0" status="DRAFT_FOR_GATE_REVIEW"/>
```
新内容（整段替换锚点）:
```text
    <input path="docs/architecture_design.md" version="1.2.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW"/>
```

**C · Module design 输入版本 + 新增契约输入**
锚点（唯一；原文照抄）:
```text
    <input path="docs/module_design.md" version="1.1.0" status="DRAFT_FOR_GATE_REVIEW"/>
```
新内容（整段替换锚点，并在其后追加一行新输入）:
```text
    <input path="docs/module_design.md" version="1.2.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW"/>
    <input path="docs/ib_embed_service_contract.md" version="1.0.0" revision="R2" status="DRAFT_FOR_GATE_REVIEW" note="MOD-IB-26 契约唯一落点；本文件 §1.2 的键名清单以其 §9 为准"/>
```

> **注**：`requirements_spec.md` 的输入行**不动**（需求侧未修改，仍 `1.1.0 / APPROVED`）。

---

## 2. 本修订包的条目计数（按目标文件分组）

| 目标文件 | 条目数 | 定位点（锚点数） | 覆盖范围 |
|----------|--------|------------------|----------|
| `docs/module_design.md` | **22**（MD-01 ~ MD-22） | **26**（MD-07 / MD-19 各 2 处，MD-21 3 处） | 文件头与版本、`inputs`、§1 计数与总览行、§2.1 三行数据结构、§2.2.1 R2 IFC 段号索引、§3 的 MOD-IB-09/13/21/23/24/25 增补与 **MOD-IB-26 新小节**、§4.1 依赖边、§4.2 无环补句、§4.3 分层、§5 装配与可逆开关、§7.4 降级两行、§9 覆盖三处、§11 自检 |
| `docs/architecture_design.md` | **11**（AD-01 ~ AD-11） | **11** | 文件头与版本、`revision_history`、首部摘要、**ADR-02-R2 附注**、**§2.0.1 R2 影响复核表**、ADR-04/06/11/13 inline 复核句、§9 TBD 追加 T16/T17/T18、§10.3 自检 R2 行 |
| `docs/tech_stack.md` | **10**（TS-01 ~ TS-10） | **14**（TS-05 / TS-09 各 2 处，TS-10 3 处） | 文件头与版本、`revision_history`、首部摘要、**「Embedding 推理运行时」行改写（bge-m3 加载库选型）**、许可台账新增行与遗留动作、**§1.2 服务端配置键登记**、§5.2 指令集风险行、§6 自检、§4.2/§4.3 检查项、文件头 hygiene |
| **合计** | **43 条目** | **51 定位点** | 三份目标文档的 R1 → R2 全量增量 |

**分册索引**：part1 = 总则（不变式 6 条）+ MD-01~MD-08；part2 = MD-09~MD-16；part3 = MD-17~MD-22 + AD-01~AD-03；part4 = AD-04~AD-05；part5 = AD-06~AD-11 + TS-01~TS-03；part6 = TS-04~TS-07；part7 = TS-08~TS-10 + 计数与残余项。

**新增 / 变更的编号台账**

| 编号 | 归属 | 性质 |
|------|------|------|
| MOD-IB-26 | ib-embed 服务端 | **新增模块**（编号 26 > 其全部依赖 {01,02,04}，且**无入边**） |
| IFC-IB-266 ~ 274 | MOD-IB-26 | 新增（正文在 `ib_embed_service_contract.md`） |
| IFC-IB-275 | MOD-IB-09 | 新增（`InProcessBgeM3Embedder`，第三适配器） |
| IFC-IB-276 | MOD-IB-01 | 新增（页面图三结构字段级定义） |
| IFC-IB-277 ~ 281 | MOD-IB-13 | 新增（M-02 五条） |
| IFC-IB-282 | MOD-IB-21 | 新增（`related_images` 载荷类型化） |
| IFC-IB-283 | MOD-IB-23 | 新增（图片字节端点） |
| IFC-IB-284 | MOD-IB-24 | 新增（前端渲染约束） |
| IFC-IB-285 | — | **预留未分配**（显式占位，不得回收改义） |
| IFC-IB-286 | MOD-IB-25 | 新增（第二份 `EnvironmentFile` 模板） |
| TBD-T16 | architecture_design §9 | 新增（`ib-embed` 并发/线程校准） |
| TBD-T17 | architecture_design §9 | **预留未分配** |
| TBD-T18 | architecture_design §9 / tech_stack §5.2 | 新增（目标机 CPU 指令集基线与 SIGILL） |

---

## 3. 施加顺序（建议）

1. **`module_design.md`**：MD-01 → MD-04（文件头 / `inputs` / 版本行）→ MD-05~MD-08（§1 / §2.1 / §2.2.1）→ MD-09~MD-16（§3 各模块增补 + §4.1）→ MD-17~MD-22（§4.2 / §4.3 / §5 / §7.4 / §9 / §11）。
2. **`architecture_design.md`**：AD-01~AD-03（头 / 摘要）→ AD-04~AD-05（ADR-02 附注 + §2.0.1 表）→ AD-06~AD-09（inline 复核句）→ AD-10~AD-11（§9 / §10.3）。
3. **`tech_stack.md`**：TS-01~TS-03（头 / 摘要）→ TS-04~TS-07（选型行 / 台账 / §1.2 / §5.2）→ TS-08~TS-10（§6 / §4.x / hygiene）。

**施加前后的机器校验建议（PM 侧）**：

| # | 校验 | 判据 |
|---|------|------|
| 1 | **锚点唯一性** | 施加**前**对每个锚点做一次全文计数，**必须恰好命中 1 处**；命中 0 或 ≥2 即说明该锚点需重新定位（本包锚点均为原文照抄，含全角括号与原始空格） |
| 2 | **编号只增不改** | 施加后 `git diff` 中，`IFC-IB-001 ~ 265` 的**删除行应为 0**（仅新增行）；`MOD-IB-01~25` / 13 个端口名 / `ADR-01~13` / `FM-1~8` 的既有条目**无删除行** |
| 3 | **无环（DAG）** | `MOD-IB-26` 只应出现在：§1 总览行、§3 新小节标题、§4.1 新边、§4.3 层视图、§9 覆盖列；**不得出现在任何模块的「依赖模块」列**（即 26 无入边） |
| 4 | **契约单一落点** | MOD-IB-26 的接口正文只应在 `docs/ib_embed_service_contract.md`；`module_design.md` §3 出现的是**摘要**（且已注明「以契约文件为准」） |
| 5 | **无代码 / 无凭据** | 新增内容中 `def ` / `class ` / `import ` / `return ` 等实现语法**零命中**；`sk-` / `ghp_` / `-----BEGIN` / `?token=` **零命中** |
| 6 | **覆盖不变** | §9 覆盖矩阵仍为 **24/24 REQ-FUNC + 14 REQ-NFR**；端口数仍 **13** |

---

## 4. 需 PM / 用户裁决的残余项

> **编号恢复说明（诚实交代）**：上一次调用（`INV-GROUP_B-INTELBASE-003`）的残余项清单只存在于**会话文本**中，本次**无法逐字恢复其原文编号**。下表给出**内容对齐**的对应关系：凡能与上次语义对上的，**沿用其编号**；新增项顺延。**不对齐即为信息丢失，请 PM 以本表为准重述基线。**

| # | 残余项 | 影响 | 建议裁决 | 对应上次 |
|---|--------|------|----------|----------|
| **R-1** | `/embed` 路径的**冻结确认**：客户端（`src/ib/embedding/__init__.py`）已按 `POST /embed` 落盘；契约 §11 明确**拒绝** `/v1/embeddings` | 若日后有人「对齐 OpenAI 生态」改路径，**服务端与客户端会不同步** | PM 确认：`/embed` 为**冻结路径**，改路径须走架构评审 | —（部分对应「协议兼容」议题） |
| **R-2** | **Embedding 推理运行时最终择一**（`FlagEmbedding` / `sentence-transformers` / `onnxruntime` 直载 ONNX，见 TS-04） | 决定依赖面、内存峰值与 [TBD-T18] 风险敞口 | **GROUP_C 目标机实测后择一**；在实测前**不预先拍板**（本包已按此纪律书写） | — |
| **R-3** | **`ib-embed.env` 是否单独一份模板**（即 IFC-IB-286 的第二份 `EnvironmentFile`） | 若与 `ib-web` 共用一份，**键集合会混在一起**，凭据面与配置面无法分治 | 建议**独立一份**（本包已按独立书写）；若 PM 决定合并，须删去 TS-04 的键清单并回写 IFC-IB-286 | **上次 R-3** |
| **R-4** | **`IB_EMBED_MEMORY_LIMIT_MB` 与单元文件 `MemoryMax` 的再校准**（目标机 11GiB） | 上限设小了 → 模型加载即被 OOM-kill；设大了 → 与 OCR/Qdrant/`ib-web` 争抢 | 须在 [TBD-T16] 实测后**一并重定**两个值（键 + 单元），**不得只改一个** | **上次 R-4** |
| **R-5** | **M-02（页面图回溯）是否升格为独立 REQ** | 现在是落在 REQ-FUNC-IB-10/11/14/17 **既有语义之内**（只增辅覆盖）；若升格，覆盖率基数从 24 变 25 | **架构层不自行新增 REQ**。建议**不升格**（理由：它是「解析产出页面图」与「检索供专家使用」的自然延伸）；若升格须回**需求侧**立项并回写覆盖矩阵 | **上次 R-5** |
| **R-6** | **图片端点（IFC-IB-283）是否进入 v1 范围** | 若不进 v1，`related_images` 载荷可只为「同一轮回答下方有图」提供**最小**能力 | 建议**进 v1**（读路径成本低、且是「问图不出图」的修复闭环）；若裁剪，须同步裁剪 IFC-IB-282/284 的验收 | —（上次可能为「取图方式」议题） |
| **R-7** | **`ChunkImageRecord` 在文档重建时的再生策略** | 关联表是**派生元数据**（ADR-05 复核已认定不成为新真源）；重建若不重跑绑定，会出现**孤儿关联行** | 建议：重建**随 `process_pending` 重跑再生**，并以幂等键覆盖；孤儿行由 `(doc_id)` 级联删除兜底 | **上次 R-7** |
| **R-8** | **【R2 新】指令集基线风险同时命中既有 OCR 链路** | `onnxruntime` 已是 D-08 **已采纳**项；若目标机确实缺 AVX2 触发 `SIGILL`，受影响的不只是 R2 的新增运行时 | 必须**合并评估**（[TBD-T18]）；若确无可用构建，须回 PM 裁决是否放宽 DR-08 / 降级 OCR（**不得**以 PyMuPDF 或 Docker 规避） | —（R2 新增） |
| **R-9** | **【R2 新】既有 `IFC-IB-131` 重号**（同时出现在 MOD-IB-11 `LedgerRepository` 与 MOD-IB-12 `BlobStore` 的清单中） | 下游若按 IFC 号引用会**歧义** | **登记但不修正**（任何重排都会打断下游引用）。**建议 GROUP_C 在引用该号时改为「IFC-IB-131（MOD-IB-11）」形式限定**；若 PM 要求统一改号，须单独立项并全量回写引用 | —（R2 新增） |

---

## 5. 本包安全与边界声明

- 本包**只含编辑指令**（锚点 + 新内容）：**无实现代码、无伪代码、无部署脚本、无任何凭据或配置值**（配置项**只登记键名与语义**）。
- 本包**只新增 `docs/r2_apply_package_part*.md`**；三份目标文档**未做整文件重写**（`module_design.md` 仍为 R1 原状，>50KB 不改）。
- **未向 `FreeArk` 仓库（只读参考）写入任何文件**；未修改需求侧文档；本阶段**止于 GROUP_B**。

---

（part7 结束；R2 修订包全 7 册完毕）
