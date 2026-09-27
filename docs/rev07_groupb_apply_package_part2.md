<file_header>
  <project>intelligentbase</project>
  <artifact>rev07_groupb_apply_package_part2</artifact>
  <path>docs/rev07_groupb_apply_package_part2.md</path>
  <doc_id>APPLY-INTELBASE-REV07-GROUPB-001</doc_id>
  <version>1.0.0</version>
  <status>DRAFT_FOR_GATE_REVIEW</status>
  <phase>GROUP_B / REV-07 增量修订（PHASE_03 架构设计）</phase>
  <author>system-architect</author>
  <invocation_id>INV-GROUP_B-INTELBASE-005</invocation_id>
  <created_at>2026-09-27</created_at>
  <targets>docs/architecture_design.md</targets>
</file_header>

# REV-07 APPLY-READY 修订包 · 第 2 册 — 架构文档指令（续）

**分册结构（以本表为准，修正第 1 册 `<package_parts>` 的册数声明）**：本包共 **7 册**，合计 **60 条**指令。

| 册 | 文件 | 内容 |
|----|------|------|
| 1 | `docs/rev07_groupb_apply_package.md` | §0 总览（含 REV-07-6 判定 (a) / 禁止清单）+ `R7-A-01 ~ R7-A-07` |
| **2（本册）** | `docs/rev07_groupb_apply_package_part2.md` | `R7-A-08 ~ R7-A-10` |
| 3 | `part3` | `R7-A-11`（**新增 ADR-14 / ADR-15 / ADR-16 全文**） |
| 4 | `part4` | `R7-A-12 ~ R7-A-20`（§6 / §8 / §9 / §10 增补与计数同步） |
| 5 | `part5` | `R7-M-01 ~ R7-M-14`（模块文档：头 / 总览 / §2 / §4 / §5 / §7.4 / §8） |
| 6 | `part6` | `R7-M-15 ~ R7-M-26`（模块文档：§9 覆盖矩阵与计数同步 / §11 自检） |
| 7 | `part7` | `R7-T-01 ~ R7-T-13`（技术栈）+ §4 落盘后核验清单 |

落盘规程与字段约定见第 1 册 §0.1（`anchor` 即 `old_string`，全局唯一；纯插入类 `old_string` 记 `（空：纯插入）`）。

---

## 1. `docs/architecture_design.md` 指令（续）

### R7-A-08
- target_file: `docs/architecture_design.md`
- action: `INSERT_AFTER`
- anchor（唯一）: `| 配置来源 | `ConfigurationSource` | 文件 + 环境变量 | 新增适配器（如接配置中心） | REQ-FUNC-IB-01 |`
- old_string: `（空：纯插入）`
- new_string:
```text
| 定义文档来源（**R7 新增**） | `DefinitionDocumentStore`（IFC-IB-287） | `FileDefinitionDocumentStore`（本地文件；原子写 + 语义哈希乐观并发） | 新增适配器（如接 DB / 配置中心，上层零改动） | AC-IB-17-01 / AC-IB-17-02；REQ-NFR-IB-11 |
```
- rationale: REV-07-5 / REQ-NFR-IB-11 — 定义文档载体经端口抽象，使「从文件换为 DB / 配置中心」只替换适配器；本行是 §1.3「可替换点」表的语汇一致补充。

### R7-A-09
- target_file: `docs/architecture_design.md`
- action: `REPLACE`
- anchor（= old_string，唯一）: `R2 的所有改动**不触及**：端口数（13）、`IFC-IB-001~265` 编号体系、REQ→MOD 覆盖矩阵（仍 24/24 + 14）与 DAG 无环性（模块数 25 → 26，纯追加）。`
- new_string: `R2 的所有改动**不触及**：端口数（13；**R7 同步：13 → 14，新增 `DefinitionDocumentStore`，纯追加**）、`IFC-IB-001~265` 编号体系、REQ→MOD 覆盖矩阵（**R7 同步计数：27/27 + 14；R2 时点基线为 24/24**）与 DAG 无环性（模块数 25 → 26，纯追加）。`
- rationale: REV-07-3 — 计数同步（仅需求计数语境）；R1 / R2 结论句保留并以括注说明基线时点，历史行不回改。

### R7-A-10
- target_file: `docs/architecture_design.md`
- action: `INSERT_BEFORE`
- anchor（唯一）: `### ADR-01 向量库抽象层与 Qdrant 集成方式`
- old_string: `（空：纯插入）`
- new_string:
```text
### 2.0.2 R7 影响复核表（R7 增量：可视化配置 = REQ-FUNC-IB-25 / IB-26 / IB-27）

> **口径**：R7 是**追加式增量**（新增 ADR 3 条、端口 1 个、IFC 段 11 条；**不新增模块、不新增依赖边**）。凡决策客体未被 R7 触及者，一律**显式声明「R7 不受影响」**，以便门控区分「已检查」与「漏检查」。以下逐条覆盖 **ADR-01 ~ ADR-16**（**无一条跳过**）。

| ADR | R7 复核结论 | 一句话理由 |
|-----|-------------|-----------|
| ADR-01 | **R7 不受影响** | 向量库端口与 collection 维度声明未动；定义文档属**配置侧**工件，不触碰 `PointPayload` / `CollectionSpec`（IFC-IB-001~012、100~110 不变） |
| ADR-02 | **R7 不受影响** | embedding 服务端形态与冷 / 热双路径未动；可视化不改变 `ib-embed` 线协议，也不改动其配置**键集**（`tech_stack.md` §1.2 不变） |
| ADR-03 | **R7 不受影响** | systemd 单元仍为**四个**；可视化是 `ib-web` 内的页面与端点（**非新进程**），未新增单元、未改 `ib-web` 载体 |
| ADR-04 | **R7 不受影响** | 隔离机制未动：定义文档是**项目级**工件（一项目一文档，`Scope` 必填），其端点一律复用归属断言（`403` 口径与 §1.4 第 2 条一致）；`CollectionResolver` 仍为唯一 collection 解析入口 |
| ADR-05 | **R7 不受影响** | 原文件内容寻址与重建机制未动；定义文档**不是**内容寻址对象（属配置，不参与 blob 寻址），也**不进入** `fingerprint` 因子 |
| ADR-06 | **R7 不受影响** | PDF 解析库选型与三路径未动；可视化**未引入任何新 PDF 库** |
| ADR-07 | **R7 不受影响** | 台账仍为 SQLite + `LedgerRepository` + 自管 SQL + **手写 scoped 迁移**；定义文档**不经台账**（无新表、无新迁移），**不经 Django ORM** |
| ADR-08 | **R7 不受影响** | 外发边界未动：可视化**不外发定义文档或其内容**（AC-IB-17-06）；图可视化库须**随构建产物本地打包、禁止运行期 CDN 加载**；`describe_egress()` 的 `data_categories` **无需扩项** |
| ADR-09 | **R7 不受影响（且 R7 是其应用）** | 定义文档在**装配期**被派生为构造参数后透传；编排骨架仍只认端口与纯数据、**仍不见业务语义** —— 与「两段式上下文 + 装配期注入」同一模式 |
| ADR-10 | **R7 不受影响** | 异步入库的队列载体与租约语义未动；定义文档的装载与校验发生在**启动 / 装配期**，不进入入库任务路径 |
| ADR-11 | **R7 不受影响** | 流式仍为 Django 原生 SSE + `StreamingHttpResponse`；可视化端点为**普通 HTTP（非流式）**，不占 worker 长连接预算，与 [TBD-T15] 容量纪律相容；「禁止 `?token=`」纪律**扩展至全部新端点**（含定义文档的 GET / PUT） |
| ADR-12 | **R7 不受影响** | OCR 与页面渲染两个端口及降级语义未动；可视化不消费也不改变其签名 |
| ADR-13 | **R7 不受影响** | `RetrievalResult` 字段与降级语义未动；R7 的新失败面是**装配期 fail-closed（拒绝装配）**，与运行期读路径 fail-open **在时间轴与契约上分离**（§7.3 / §7.4），二者不冲突 |
| **ADR-14（R7 新增）** | **新增** | 可视化配置的**编辑模型**：定义文档唯一真源 + 显式 round-trip，视图侧零持久化 |
| **ADR-15（R7 新增）** | **新增** | 定义文档**单一真源（双向同源）**与只读派生视图（派生不落盘、不可反写） |
| **ADR-16（R7 新增）** | **新增** | **装配期完备性校验 + fail-fast 准入闸门**（无「强制继续 / 忽略错误」开关） |

**R7 复核小结**：**既有 13 条 ADR 在 R7 下全部不受影响**（其中 ADR-09 判「不受影响，且 R7 是其应用」）；**新增 3 条**（ADR-14 / 15 / 16）→ **ADR 总数 13 → 16**。**无一条 ADR 未复核**。R7 的所有改动**不触及**：模块数（**26，未新增**）、`IFC-IB-001~286` 编号体系、**§4.1 依赖边（零新增边）**与 DAG 无环性；**端口数 13 → 14**（纯追加）；REQ→MOD 覆盖矩阵**由 24/24 同步为 27/27**（v1.2.0 需求总数，见 §10.3）。
```
- rationale: REV-07-2（ADR 计数与索引同步）+ 沿用 R1 / R2 的「逐条复核表」审计范式；明确点出「装配期 fail-closed 与运行期 fail-open 不冲突」这一最易被误读之处。
