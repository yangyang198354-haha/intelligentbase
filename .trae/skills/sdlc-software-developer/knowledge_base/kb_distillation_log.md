# Distillation Log — software_developer
<!-- 仅追加 -->
<op time="2026-09-27T00:00:00Z" type="CREATE" entry_id="KE-DEV-001" round="1" reason="错误学习：计数口径混淆若误用即回归缺陷（protected-line 逐字保护 + diff -U0 取证）"/>
<op time="2026-09-27T00:00:00Z" type="CREATE" entry_id="KE-DEV-002" round="1" reason="procedural：一次性装配守卫模块的增量数据源应按幂等新增入口扩展，而非放宽守卫"/>
<op time="2026-09-27T00:00:00Z" type="CREATE" entry_id="KE-DEV-003" round="1" reason="pattern：『能力必须不存在』做成类型层事实 + 装配期 fail-fast 闸门"/>
<op time="2026-09-27T00:00:00Z" type="CREATE" entry_id="KE-DEV-004" round="1" reason="procedural：大文件用 Edit 而非 Write；受保护行号漂移须逐字取证"/>
<op time="2026-09-27T00:00:00Z" type="CREATE" entry_id="KE-DEV-005" round="2" reason="错误学习：构建失败常含多个独立根因，修一处会暴露下一处；必须跑到完整流水线全绿再交付"/>
<op time="2026-09-27T00:00:00Z" type="CREATE" entry_id="KE-DEV-006" round="2" reason="procedural：npm ci 是锁完整性的最强证据；回归断言须用负向对照证明非空转"/>
<op time="2026-09-27T00:00:00Z" type="CREATE" entry_id="KE-DEV-007" round="2" reason="procedural：零依赖冒烟入口用无参 node --test（跨 Node 版本一致），目录参数与 glob 均不可移植"/>
<op time="2026-09-27T00:00:00Z" type="CREATE" entry_id="KE-DEV-008" round="2" reason="procedural：传递依赖许可须读安装后各包 package.json + 确认 LICENSE 文件存在，并注意嵌套包与精确版本"/>
<op time="2026-09-28T00:00:00Z" type="UPDATE" entry_id="KE-DEV-004" round="3" reason="合并/强化（重叠度≥70%）：同一主题第 2 次命中 → freq 1→2、confidence 0.6→0.8，新增『修订段落续写进同一物理行以免行号漂移』技巧"/>
<op time="2026-09-28T00:00:00Z" type="CREATE" entry_id="KE-DEV-009" round="3" reason="pattern：设计字段集与既有实现冲突时按最小一致做兼容扩展（旧字段逐字保留 + 新字段全默认）并登记设计缺口，不擅改设计文档"/>
<op time="2026-09-28T00:00:00Z" type="CREATE" entry_id="KE-DEV-010" round="3" reason="pattern：fail-closed 判据做成纯函数以离线穷举组合；恢复类端点前置检查先于开流、显式 4xx、不退化为新建重跑；残缺载荷不补默认批准"/>
<op time="2026-09-28T00:00:00Z" type="CREATE" entry_id="KE-DEV-011" round="3" reason="procedural：新增校验须用全新错误码以免误伤既有『某码不存在』护栏；新校验追加在既有项之后；旧兜底保留并用行为断言守护"/>
<op time="2026-09-28T00:00:00Z" type="CREATE" entry_id="KE-DEV-012" round="3" reason="pattern：兼容超集手法（可选关键字默认 None = 零行为差异；裸 dict 签名只新增载荷类型不改签名）；骨架不生成业务语义"/>
<op time="2026-09-28T00:00:00Z" type="UPDATE" entry_id="KE-DEV-004" round="3" reason="XML 实体转义修复：content 内裸 &lt;受保护字符串&gt; 转义为 &amp;lt;…&amp;gt;（文件此前非良构）"/>
<op time="2026-09-28T00:00:00Z" type="UPDATE" entry_id="KE-DEV-006" round="3" reason="XML 实体转义修复：content 内裸 HEAD:&lt;path&gt; 转义（round-2 遗留的非良构点）"/>
<op time="2026-09-28T00:00:00Z" type="UPDATE" entry_id="KE-DEV-008" round="3" reason="XML 实体转义修复：content 内裸 node_modules/&lt;pkg&gt; · &lt;parent&gt; 转义（round-2 遗留的非良构点）；修复后 kb_full.xml 经 xml.dom.minidom 解析通过、12 条目"/>
<op time="2026-10-06T00:00:00Z" type="CREATE" entry_id="KE-DEV-013" round="4" reason="heuristic：契约项有指定落点模块时必须在指定模块落地；只在消费点读取不算实现（IFC-IB-312 缺口自查）"/>
<op time="2026-10-06T00:00:00Z" type="CREATE" entry_id="KE-DEV-014" round="4" reason="pattern：端口协议禁改时用实现侧扩展 + 替身同签名 + [DEVIATION] 登记（upsert_chunks / revoke_sessions_for_user 先例）"/>
<op time="2026-10-06T00:00:00Z" type="CREATE" entry_id="KE-DEV-015" round="4" reason="exception：Windows 临时 SQLite 清理异常会掩盖真实断言失败；须显式 close + ignore_cleanup_errors + 扫 main/-wal/-shm 三件套"/>
<op time="2026-10-06T00:00:00Z" type="CREATE" entry_id="KE-DEV-016" round="4" reason="exception：log_event 的 outcome 是位置参数，放入 **extra 会 TypeError 导致审计静默丢失；审计函数签名应拒绝敏感字段"/>
<op time="2026-10-06T00:00:00Z" type="CREATE" entry_id="KE-DEV-017" round="4" reason="exception：源码纪律断言须先剥离注释，且优先断言结构而非自然语言词，避免假阳性"/>
<op time="2026-10-11T00:00:00Z" type="CREATE" entry_id="KE-DEV-018" round="5" reason="exception：退场旧标识的仓库级 grep 归零测试按子串判定，会命中新代码含注释里的旧字面量；内置默认值须与退场标签不同字且注释不复述旧值（REV-19 内置 KB agent cn_label 撞 ADR-31 旧标签）"/>
<op time="2026-10-11T00:00:00Z" type="CREATE" entry_id="KE-DEV-019" round="5" reason="exception：XML 头内追加含裸 < > 的文字破坏 ElementTree 严格解析（正文不受影响）；头内须实体转义 &lt; &gt;，且 Markdown 表头类文档应如实登记 ET 不适用（REV-19 impl_plan §26）"/>
