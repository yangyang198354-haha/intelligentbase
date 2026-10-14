# Distillation Log — test_engineer
<!-- 仅追加；永久 -->
<op time="2026-09-27T14:20:00+08:00" type="CREATE" entry_id="KE-TEST-001" round="1" reason="D-R8-01 夹具陈旧 vs 真实回归的判定方法，可复用"/>
<op time="2026-09-27T14:20:00+08:00" type="CREATE" entry_id="KE-TEST-002" round="1" reason="门控/算术自洽/证据留档的固定产出规范"/>
<op time="2026-09-27T14:20:00+08:00" type="CREATE" entry_id="KE-TEST-003" round="1" reason="FLAKE-IB-01 登记四栏范式 + 测试侧缓解建议"/>
<op time="2026-09-27T14:20:00+08:00" type="CREATE" entry_id="KE-TEST-004" round="1" reason="pytest 无包布局下测试文件基名唯一性约束"/>
<op time="2026-09-27T14:20:00+08:00" type="CREATE" entry_id="KE-TEST-005" round="1" reason="FND 缺陷闭合的补测与三层闭合判定启发式"/>
<op time="2026-09-27T15:45:00+08:00" type="UPDATE" entry_id="KE-TEST-002" round="2" reason="R9 增量轮沿用门控/版本线纪律，frequency 1→2"/>
<op time="2026-09-27T15:45:00+08:00" type="UPDATE" entry_id="KE-TEST-003" round="2" reason="FLAKE-IB-01 治理落地（有界重试），机制经探针确证；confidence 0.6→0.7"/>
<op time="2026-09-27T15:45:00+08:00" type="CREATE" entry_id="KE-TEST-006" round="2" reason="flake 测试侧有界重试的守约范式（只捕获特定类型/有界/裸 raise/探针自证/幂等前提）"/>
<op time="2026-10-07T00:00:00+08:00" type="UPDATE" entry_id="KE-TEST-002" round="3" reason="REV-18 增量轮沿用门控/版本线纪律 + 新增「分层用例数独立实测」；frequency 2→3"/>
<op time="2026-10-07T00:00:00+08:00" type="UPDATE" entry_id="KE-TEST-004" round="3" reason="REV-18 三个新测试文件继续遵守基名唯一性；frequency 1→2"/>
<op time="2026-10-07T00:00:00+08:00" type="CREATE" entry_id="KE-TEST-007" round="3" reason="Vue 前端源码结构断言型冒烟范式（stripComments 后正则；类型块 / 导航数组两种形态）"/>
<op time="2026-10-07T00:00:00+08:00" type="CREATE" entry_id="KE-TEST-008" round="3" reason="intelligentbase schema DDL 按域分流定位（ACCOUNT_DDL_STATEMENTS / project_registry / llm_key 单源函数）+ 迁移幂等验证法"/>
<op time="2026-10-07T00:00:00+08:00" type="CREATE" entry_id="KE-TEST-009" round="3" reason="已裁决「交付边界」（如 D-R18-01）的登记与断言口径：非缺陷 + 断言清晰边界错误 + 必带对照正例"/>
<op time="2026-10-07T00:00:00+08:00" type="CREATE" entry_id="KE-TEST-010" round="3" reason="错误学习：DDL_STATEMENTS 不含 users 表致 StopIteration，应改 ACCOUNT_DDL_STATEMENTS"/>
