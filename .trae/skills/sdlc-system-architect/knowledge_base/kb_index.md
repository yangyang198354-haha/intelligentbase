# KB Index — system_architect

<!-- 由 Agent 自动维护。每行一条知识条目摘要。检索优先使用本索引。 -->
<!-- 格式: <entry id="KE-ARCH-NNN" type="..." confidence="0.0-1.0" frequency="N" trigger_keywords="..." status="ACTIVE|DEPRECATED|UNDER_REVIEW"/> -->
<!-- 落盘位置: intelligentbase/.claude/agents/knowledge_base/system_architect/（当前项目根；参考仓库只读，禁止写入） -->
<!-- 最后更新: 2026-10-07（R18 增量轮，session 5）。confidence 不变（本轮修订包处于 DRAFT_FOR_GATE_REVIEW，未经 PM 门控确认）；frequency 按复用次数递增。 -->
<!-- 注意: KE-ARCH-017 ~ 020 的**完整正文**位于 kb_full_r7.xml；KE-ARCH-021 ~ 024 的**完整正文**位于 kb_full_r18.xml（kb_full.xml 已超出单次 Write 容量，为避免截断丢数据未做整文件覆盖；待具备 Edit/append 能力时合并回 kb_full.xml → 见 KE-ARCH-009 / KE-ARCH-014 / KE-ARCH-015 的边界条件）。检索先用本索引，命中后按正文文件读取。 -->

<entry id="KE-ARCH-001" type="pattern" confidence="0.8" frequency="7" trigger_keywords="端口适配器,可替换性,替身,抽象层,依赖注入,纯追加端口" status="ACTIVE"/>
<entry id="KE-ARCH-002" type="heuristic" confidence="0.8" frequency="6" trigger_keywords="ADR,已锁定选型,决策点,架构决策记录,追加式修订,影响复核表" status="ACTIVE"/>
<entry id="KE-ARCH-003" type="exception" confidence="0.8" frequency="6" trigger_keywords="循环依赖,DAG,无环证明,模块依赖,拓扑序,新增模块" status="ACTIVE"/>
<entry id="KE-ARCH-004" type="exception" confidence="0.9" frequency="6" trigger_keywords="许可合规,AGPL,GPL,PyMuPDF,开源协议,传染性,传递依赖,无新增依赖" status="ACTIVE"/>
<entry id="KE-ARCH-005" type="heuristic" confidence="0.7" frequency="5" trigger_keywords="CPU推理,延迟未实测,不可逆风险,形态可逆,兜底,值域扩展" status="ACTIVE"/>
<entry id="KE-ARCH-006" type="pattern" confidence="0.8" frequency="6" trigger_keywords="多租户隔离,隔离边界,collection,scope,单入口,归属断言,范围不可自证" status="ACTIVE"/>
<entry id="KE-ARCH-007" type="exception" confidence="0.9" frequency="5" trigger_keywords="WebSocket,SSE,token,query string,流式,凭据泄漏,Django" status="ACTIVE"/>
<entry id="KE-ARCH-008" type="heuristic" confidence="0.8" frequency="6" trigger_keywords="降级,失败模式,空结果,可观测,契约设计,fail-closed" status="ACTIVE"/>
<entry id="KE-ARCH-009" type="procedural" confidence="0.6" frequency="6" trigger_keywords="大文件写入,交付物,工具限制,Edit不可用,分批,截断" status="ACTIVE"/>
<entry id="KE-ARCH-010" type="heuristic" confidence="0.8" frequency="6" trigger_keywords="TBD,未实测,不编造数值,目标机,性能指标" status="ACTIVE"/>
<entry id="KE-ARCH-011" type="procedural" confidence="0.7" frequency="4" trigger_keywords="框架切换,修订,R1,载体映射,编号稳定,ADR复核,登记型口径修订" status="ACTIVE"/>
<entry id="KE-ARCH-012" type="heuristic" confidence="0.7" frequency="2" trigger_keywords="SSE,WSGI,ASGI,worker耗尽,长连接,Channels,同步栈" status="ACTIVE"/>
<entry id="KE-ARCH-013" type="exception" confidence="0.75" frequency="1" trigger_keywords="服务端归属,线协议契约,客户端已落盘,评审项补齐,单列契约文件,已评估未采纳" status="ACTIVE"/>
<entry id="KE-ARCH-014" type="procedural" confidence="0.8" frequency="3" trigger_keywords="锚点包,APPLY-READY,交付落盘,PM读不到会话,唯一锚点,原文照抄" status="ACTIVE"/>
<entry id="KE-ARCH-015" type="exception" confidence="0.9" frequency="3" trigger_keywords="知识库落盘,只读参考仓库,路径解析,跨项目复用,硬约束违反" status="ACTIVE"/>
<entry id="KE-ARCH-016" type="heuristic" confidence="0.75" frequency="1" trigger_keywords="AVX2,SIGILL,wheel指令集基线,老CPU,onnxruntime,目标机实测" status="ACTIVE"/>
<entry id="KE-ARCH-017" type="exception" confidence="0.8" frequency="2" trigger_keywords="新增模块,组合根,编号即拓扑序,依赖边,无环证明,落点归属,不得新开模块" status="ACTIVE"/>
<entry id="KE-ARCH-018" type="pattern" confidence="0.8" frequency="1" trigger_keywords="fail-fast,准入闸门,装配期校验,类型层事实,无强制继续开关,ValidationReport" status="ACTIVE"/>
<entry id="KE-ARCH-019" type="heuristic" confidence="0.8" frequency="2" trigger_keywords="计数同步,需求计数,用例数,口径分离,禁用项,跨组边界" status="ACTIVE"/>
<entry id="KE-ARCH-020" type="heuristic" confidence="0.85" frequency="1" trigger_keywords="施工前置条件,实现落差,判定a或b,不擅自扩缩围,上报PM裁决,已批准需求" status="ACTIVE"/>
<entry id="KE-ARCH-021" type="heuristic" confidence="0.8" frequency="1" trigger_keywords="首启死锁,凭据存DB,未配置态,fail-closed,启动校验,fail-fast冲突,派生后果" status="ACTIVE"/>
<entry id="KE-ARCH-022" type="heuristic" confidence="0.8" frequency="1" trigger_keywords="登记型修订,补丁位,事实订正,假陈述,无新选型,版本口径,tech_stack" status="ACTIVE"/>
<entry id="KE-ARCH-023" type="pattern" confidence="0.8" frequency="1" trigger_keywords="软删,停用,可恢复,零迁移,删除保护,二次确认,status枚举,类型层事实" status="ACTIVE"/>
<entry id="KE-ARCH-024" type="exception" confidence="0.85" frequency="1" trigger_keywords="口径张力,OPEN ITEM,不自行改写ADR,登记不裁决,歧义上报,ADR-21" status="ACTIVE"/>
