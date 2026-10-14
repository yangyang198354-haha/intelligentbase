# KB Index — pm_orchestrator
<!-- 由 Agent 自动维护。本文件于 2026-09-25 由 FreeArk 仓库迁移至 intelligentbase 项目目录，以保持 FreeArk 只读。 -->
<!-- 检索口径：本索引与 kb_full.xml 的唯一权威为 kb_full.xml。标注 status="UNAVAILABLE" 的行属悬空项（全文已丢失），命中时**不得**注入 <kb_entries>，须按「无经验先验」处理，禁止臆造其内容（输入锚定铁律）。 -->
<entry id="KE-PM-033" type="domain" confidence="0.90" frequency="1" trigger_keywords="TRAE平台前提,工具集差异,主控具备Edit与Shell,KE-PM-019前提失效,KE-PM-021前提失效,KB-CONFLICT,平台迁移适配,ClaudeCode历史条目" status="ACTIVE"/>
<entry id="KE-PM-032" type="pattern" confidence="0.75" frequency="1" trigger_keywords="文书回填轮,交付物订正轮,非门控变更轮,追加式订正,等价措辞失真,阻塞表逐条重审,前瞻条款不写runbook,版本bump只到文书层,显式字面路径,backup=False" status="ACTIVE"/>
<entry id="KE-PM-031" type="pattern" confidence="0.80" frequency="1" trigger_keywords="缺陷修复轮,最小改动面,不碰测试断言,先证前提再派单,坑证伪,版本只bump改动层,闭合上游条件,白名单精确加键,增量门控,GR-C-015,DEFECT-R19-D-01" status="ACTIVE"/>
<entry id="KE-PM-030" type="heuristic" confidence="0.80" frequency="2" trigger_keywords="生产者自述非证据,不采信子代理自评,独立复核,grep读源码,委托只读校验,旁路异常分支,函数内局部import,NameError,失败分支用例,fail-safe契约,永不抛异常非致命,下游复跑捕获,跨组闭环,门控判FAIL路由上游,TC-INT-147" status="ACTIVE"/>
<entry id="KE-PM-029" type="pattern" confidence="0.70" frequency="1" trigger_keywords="apply-ready包,自述笔误,rationale计数不符,落盘忠实性,包自述vs实落,数量对称,包设计使然,落盘缺陷归属" status="ACTIVE"/>
<entry id="KE-PM-028" type="pattern" confidence="0.70" frequency="1" trigger_keywords="全局度量变更,陈旧计数,现时态复述,全文grep扫描,计数归口,历史轮次保留,测度真值,status同步" status="ACTIVE"/>
<entry id="KE-PM-027" type="procedural" confidence="0.85" frequency="1" trigger_keywords="RESEARCH_SUPPLEMENT,需求补充调研,官方文档对标,差距分析,WebFetch不可用,WebSearch证据分级,待官方证实,候选建议边界,不覆盖APPROVED文件,无对应REQ需求级缺口,可视化配置,先定义后可视化,接缝复用" status="ACTIVE"/>
<entry id="KE-PM-026" type="heuristic" confidence="0.75" frequency="1" trigger_keywords="计划修订,执行脚本漂移,checklists未同步,plan与清单不一致,端口二义,EADDRINUSE,真源核验,顺手发现,mtime时序归因,R4修订" status="ACTIVE"/>
<entry id="KE-PM-025" type="pattern" confidence="0.85" frequency="7" trigger_keywords="Edit机械落盘,XML合法性,属性值裸引号,未转义小于号,标签配对,结构自检,phase_status,状态文件破损,静默破损,PM_FIX,自闭合vs成对,解析器收官门,续行误闭合裸gt,插入点落入起始标签内部,锚点选择,形态g,设计文档file_header,多段文档header抽取,属性值内裸小于号,历史叙述段裸尖括号,形态h,复核清单枚举" status="ACTIVE"/>
<entry id="KE-PM-024" type="pattern" confidence="0.80" frequency="1" trigger_keywords="缺陷冻结,defect freeze,反向断言,守卫串,已知缺陷固化,断言退化,坏行为断言,GROUP_D,缺陷登记" status="ACTIVE"/>
<entry id="KE-PM-023" type="pattern" confidence="0.90" frequency="2" trigger_keywords="通过率门控,防注水,复跑对账,collect-only,函数计数,skip,xfail,addopts,deselect,monkeypatch替身边界,测试证据,非git仓库mtime,翻转忠实性" status="ACTIVE"/>
<entry id="KE-PM-022" type="heuristic" confidence="0.80" frequency="1" trigger_keywords="追加式修订,R2,陈旧描述,stale,R1残留,在用交付物,部署清单,契约散文vs字段级定义,只增不改" status="ACTIVE"/>
<entry id="KE-PM-021" type="pattern" confidence="0.90" frequency="3" trigger_keywords="独立复跑,verifier,自检证据,compileall,selfcheck,stderr负路径日志,不信自述,PM无Bash,实测证据,复核实缺陷真伪" status="ACTIVE"/>
<entry id="KE-PM-020" type="pattern" confidence="0.85" frequency="1" trigger_keywords="fail-open,静默失败,降级degraded,用例粉饰缺陷,happy-path反例,检索降级,门控自检,CRITICAL归零" status="ACTIVE"/>
<entry id="KE-PM-019" type="exception" confidence="0.85" frequency="1" trigger_keywords="整文件Write载荷超限,50-55KB,子代理无Edit工具,架构文档过大,authoring与落盘分离,Edit机械落盘,R1修订" status="ACTIVE"/>
<entry id="KE-PM-018" type="procedural" confidence="0.85" frequency="1" trigger_keywords="PARTIAL_FLOW,只读参考仓库,需求锚定,通用基座抽离,约束不默认继承,KB路径迁移" status="ACTIVE"/>
<entry id="KE-PM-017" type="factual" confidence="0.95" frequency="1" trigger_keywords="intelligentbase,Qdrant,bge-m3,禁Docker,DeepSeek,单实例多项目,索引重建,OCR,RapidOCR" status="ACTIVE"/>
<entry id="KE-PM-016" type="procedural" confidence="0.90" frequency="1" trigger_keywords="PARTIAL_FLOW,多图,向后兼容,WS协议扩展,OQ阻塞,双方案并排,增量需求,部分失败降级" status="UNAVAILABLE"/>
<entry id="KE-PM-015" type="procedural" confidence="0.90" frequency="1" trigger_keywords="PARTIAL_FLOW,reasoning流,增量ADR,字段名探查,向后兼容,前置任务,WS协议扩展" status="UNAVAILABLE"/>
<entry id="KE-PM-014" type="procedural" confidence="0.90" frequency="1" trigger_keywords="PARTIAL_FLOW,纯前端,Vue多文件,路由新增,OQ决策落图,静态测试" status="ACTIVE"/>
<entry id="KE-PM-013" type="procedural" confidence="0.90" frequency="1" trigger_keywords="纯前端,UIConsistency,CI/CD裁剪,npm_build,nginx_reload,零停机" status="ACTIVE"/>
<entry id="KE-PM-012" type="procedural" confidence="0.90" frequency="1" trigger_keywords="PARTIAL_FLOW,dashboard,power_status,开机状况,IN子查询,unknown模式,OQ-002" status="ACTIVE"/>
<entry id="KE-PM-011" type="factual" confidence="0.95" frequency="1" trigger_keywords="system_mode,system_switch,operation_mode,PLCLatestData,param_name,开机判定,看板" status="UNAVAILABLE"/>
<entry id="KE-PM-010" type="procedural" confidence="0.90" frequency="1" trigger_keywords="PARTIAL_FLOW,开发测试,waitress,环境变量,单元测试,mock,不部署" status="ACTIVE"/>
<entry id="KE-PM-009" type="factual" confidence="0.90" frequency="1" trigger_keywords="waitress,CONN_MAX_AGE,reconnect,Lost_connection,持久连接,容量计算,max_connections" status="ACTIVE"/>
<entry id="KE-PM-008" type="procedural" confidence="0.90" frequency="1" trigger_keywords="PARTIAL_FLOW,需求到设计,暂停等待确认,waitress,连接调优,ADR,环境变量参数化" status="ACTIVE"/>
<entry id="KE-PM-007" type="pattern" confidence="0.90" frequency="1" trigger_keywords="PARTIAL_FLOW,性能分析,瓶颈诊断,只读测试,subprocess" status="ACTIVE"/>
<entry id="KE-PM-006" type="factual" confidence="0.95" frequency="1" trigger_keywords="waitress,线程数,threads,看板,dashboard,归零,超时" status="ACTIVE"/>
<entry id="KE-PM-005" type="pattern" confidence="0.85" frequency="1" trigger_keywords="跳过staging,风险接受,RISK_ACCEPTED,deployment_report,PENDING_USER_EXECUTION" status="ACTIVE"/>
<entry id="KE-PM-004" type="procedural" confidence="0.90" frequency="1" trigger_keywords="PHASE_11,runbook,生产部署,手动执行,密码SSH" status="ACTIVE"/>
<entry id="KE-PM-003" type="factual" confidence="0.95" frequency="1" trigger_keywords="FR-001,undefined,el-input-number,前端边界" status="ACTIVE"/>
<entry id="KE-PM-002" type="pattern" confidence="0.90" frequency="1" trigger_keywords="SendMessage不可用,跨会话,重载,状态恢复" status="ACTIVE"/>
<entry id="KE-PM-001" type="procedural" confidence="0.90" frequency="1" trigger_keywords="GROUP_D,test_engineer,测试阶段,重载状态" status="ACTIVE"/>
