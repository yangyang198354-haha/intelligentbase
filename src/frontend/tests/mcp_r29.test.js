/**
 * [REV-29 / GROUP_D] MCP 外部工具前端测试（node:test，零新增依赖；MOD-R29-21 / 22 / 23）。GR-C-003 条件 4。
 *
 * 做法（同 advisor_r28.test.js / config_studio_r27.test.js）：
 *  1. mcpLabels.ts / externalGrants.ts——用工程已有的 `typescript` 在内存中转译为 ESM（二者只有 `import type`，转译后无运行期依赖），真实执行；
 *  2. client.ts——转译后真实实例化 ApiClient，以替身 `fetch` 捕获请求（不触网），验证 mcp* 方法的路径 / 方法 / 请求体形状；
 *  3. McpServersPage.vue / router / ConsoleLayout.vue / AgentDetailPanel.vue——无挂载环境，只读源码、剥注释后做结构断言。
 *
 * 局限（如实）：没有组件挂载环境与可用的无头浏览器，且不得新增依赖——管理页的实际渲染 / 点击 / 表单交互 / 对话框流程、
 * 配置页外部工具勾选的实际交互无法在此验证，列入 e2e_test_report「人工验证清单」（CR-009）。
 * 层级口径：unit = 词表与纯函数、client 请求形状的真实执行；integration = 源码结构契约（页面 ↔ client ↔ 路由 / 导航）。
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { describe, it } from 'node:test';

import ts from 'typescript';

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, '..', 'src');
const read = (...p) => readFileSync(join(src, ...p), 'utf8');
const stripComments = (s) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/[^\n]*/g, '$1').replace(/<!--[\s\S]*?-->/g, '');
const transpile = (...p) => ts.transpileModule(read(...p), { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText;
const toUrl = (js) => `data:text/javascript;base64,${Buffer.from(js).toString('base64')}`;

const L = await import(toUrl(transpile('utils', 'mcpLabels.ts')));
const G = await import(toUrl(transpile('utils', 'externalGrants.ts')));
const CL = await import(toUrl(transpile('api', 'client.ts')));

const page = stripComments(read('views', 'McpServersPage.vue'));
const router = stripComments(read('router', 'index.ts'));
const layout = stripComments(read('layouts', 'ConsoleLayout.vue'));
const panel = stripComments(read('components', 'config', 'AgentDetailPanel.vue'));
const clientSrc = stripComments(read('api', 'client.ts'));

function harness() {
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url: String(url), init });
    return { ok: true, status: 200, headers: { get: () => 'application/json' }, json: async () => ({}), text: async () => '{}' };
  };
  globalThis.sessionStorage = { getItem: () => 'tok', setItem() {}, removeItem() {} };
  globalThis.localStorage = globalThis.sessionStorage;
  return { c: new CL.ApiClient(''), calls };
}

// =========================================================================== //
// 词表（unit：真实执行）
// =========================================================================== //

describe('mcpLabels 词表', () => {
  it('TC-FE-R29-001 工具状态 / 风险 / 失效原因 / 失败类别词表：与架构 §C 词汇一致，未知值有兜底（不抛错）', () => {
    assert.deepEqual(['pending_review', 'enabled', 'disabled', 'needs_rereview', 'offline', 'excluded'].map(L.toolStateLabel),
      ['待审核', '已启用', '已禁用', '待复审', '已下线', '已排除']);
    assert.deepEqual(['read_only', 'side_effect', 'unknown'].map(L.riskLabel), ['只读', '有副作用', '未知']);
    assert.equal(L.toolStateLabel('???'), '???');
    assert.equal(L.invalidReasonLabel('tool_needs_rereview'), '工具待复审');
    assert.equal(L.invalidReasonLabel('server_not_open'), 'Server 未对本项目开放');
    assert.equal(L.invalidReasonLabel('risk_not_waived'), '放行已撤销');
    assert.equal(L.invalidReasonLabel('totally_unknown_reason'), '当前不可用');
    assert.equal(L.invalidReasonLabel(null), '');
    assert.deepEqual(['unreachable', 'timeout', 'auth_failed', 'protocol_incompatible', 'no_tools_capability', 'address_blocked'].map(L.failureCategoryLabel),
      ['无法连接', '连接超时', '鉴权失败', '协议版本不兼容', '服务方未声明工具能力', '地址被拒']);
    assert.equal(L.failureCategoryLabel('whatever'), '验证未通过');
  });

  it('TC-FE-R29-002 Server 状态文案：未启用 / 已停用 / 不可用 / 有待复审工具 / 可用（AC-001-01、AC-003-01）', () => {
    const base = { admin_state: 'enabled', health: 'up', tool_counts: { needs_rereview: 0 } };
    assert.equal(L.serverStatusLabel({ ...base, admin_state: 'registered' }), '未启用');
    assert.equal(L.serverStatusLabel({ ...base, admin_state: 'disabled' }), '已停用');
    assert.equal(L.serverStatusLabel({ ...base, health: 'down' }), '不可用');
    assert.equal(L.serverStatusLabel({ ...base, tool_counts: { needs_rereview: 2 } }), '有待复审工具');
    assert.equal(L.serverStatusLabel(base), '可用');
    assert.equal(L.serverStatusLabel({ admin_state: 'enabled', health: 'up' }), '可用', '缺 tool_counts 也不抛错');
  });

  it('TC-FE-R29-003 传输类型下拉唯一取值 streamable_http（不出现 stdio，AC-001-06）；未核实注解提示语；API 错误码文案', () => {
    assert.deepEqual([...L.TRANSPORT_OPTIONS], ['streamable_http']);
    assert.ok(!JSON.stringify([...L.TRANSPORT_OPTIONS]).includes('stdio'));
    assert.equal(L.UNVERIFIED_ANNOTATION_NOTE, '服务方自报，未经核实');
    assert.equal(L.WAIVER_HINT, '需管理员放行');
    assert.equal(L.apiErrorLabel('transport_not_supported'), '传输类型不受支持');
    assert.equal(L.apiErrorLabel('plain_http_public_forbidden'), '公网目标禁止明文 http');
    assert.equal(L.apiErrorLabel('secret_key_missing'), '凭证主密钥未配置');
    assert.equal(L.apiErrorLabel('server_in_use'), '该服务仍被项目授权引用');
    assert.equal(L.apiErrorLabel('no_such_code', '兜底'), '兜底');
  });
});

describe('externalGrants 纯函数', () => {
  const T = (name, server, risk, grantable) => ({ local_name: `mcp__${server}__${name}`, display_name: `mcp.${server}.${name}`, server_id: server, risk, grantable, invalid_reason: null, description: '', param_specs: [
    { name: `mcp__${server}__${name}.mcp_timeout_s` }, { name: `mcp__${server}__${name}.mcp_max_calls_per_turn` }, { name: `mcp__${server}__${name}.q` }] });
  const tools = [T('search', 'crm', 'read_only', true), T('update', 'crm', 'side_effect', false), T('get', 'kb', 'unknown', false)];

  it('TC-FE-R29-004 按 Server 分组保持目录顺序；展示名带注册名；置灰规则（有副作用 / 未知且未放行置灰，已勾选者仍可取消）', () => {
    const g = G.groupByServer(tools);
    assert.deepEqual(g.map((x) => [x.server_id, x.tools.length]), [['crm', 2], ['kb', 1]]);
    assert.equal(G.toolTitle(tools[0]), 'mcp.crm.search（mcp__crm__search）');
    assert.equal(G.isGreyed(tools[0], false), false);
    assert.equal(G.isGreyed(tools[1], false), true);
    assert.equal(G.isGreyed(tools[1], true), false, '已授权的失效/受限项不置灰：允许取消勾选');
    assert.match(G.greyHint(tools[1], L.riskLabel, L.WAIVER_HINT), /有副作用风险：需管理员放行/);
    assert.equal(G.greyHint(tools[0], L.riskLabel, L.WAIVER_HINT), '');
    assert.equal(G.isExternalName('mcp__crm__search'), true);
    assert.equal(G.isExternalName('search_knowledge'), false);
  });

  it('TC-FE-R29-005 勾选 / 取消写入草稿授权：不改原对象、去重、取消时同步清理该工具的参数值（AC-016-01）', () => {
    const doc = { tool_grants: [{ expert_name: 'kb-agent', tool_names: ['search_knowledge'], param_values: [{ name: 'mcp__crm__search.mcp_timeout_s', value: '10' }, { name: 'search_knowledge.top_k', value: '3' }] }] };
    const snap = JSON.stringify(doc);
    const on = G.toggleExternalGrant(doc, 'kb-agent', 'mcp__crm__search', true);
    assert.deepEqual(on.tool_grants[0].tool_names, ['search_knowledge', 'mcp__crm__search']);
    assert.equal(JSON.stringify(doc), snap, '不得就地修改入参');
    assert.deepEqual(G.toggleExternalGrant(on, 'kb-agent', 'mcp__crm__search', true).tool_grants[0].tool_names, ['search_knowledge', 'mcp__crm__search'], '重复勾选幂等');
    const off = G.toggleExternalGrant(on, 'kb-agent', 'mcp__crm__search', false);
    assert.deepEqual(off.tool_grants[0].tool_names, ['search_knowledge']);
    assert.deepEqual(off.tool_grants[0].param_values.map((p) => p.name), ['search_knowledge.top_k'], '外部工具的参数值随取消授权被清理，内置工具参数不受影响');
    const fresh = G.toggleExternalGrant({ tool_grants: [] }, 'advisor', 'mcp__crm__get', true);
    assert.deepEqual(fresh.tool_grants, [{ expert_name: 'advisor', tool_names: ['mcp__crm__get'], param_values: [] }], '该 agent 尚无授权行时新建');
  });

  it('TC-FE-R29-006 失效徽标：只列该 agent 的失效项并带原因文案；仅渲染两个限制参数规格（AC-017-01）', () => {
    const status = [
      { local_name: 'mcp__crm__search', expert_name: 'kb-agent', valid: false, reason: 'tool_needs_rereview' },
      { local_name: 'mcp__crm__get', expert_name: 'kb-agent', valid: true, reason: null },
      { local_name: 'mcp__crm__x', expert_name: 'advisor', valid: false, reason: 'server_not_open' },
    ];
    assert.deepEqual(G.invalidBadges('kb-agent', status, L.invalidReasonLabel), [{ local_name: 'mcp__crm__search', label: '工具待复审' }]);
    assert.deepEqual(G.invalidBadges('advisor', status, L.invalidReasonLabel), [{ local_name: 'mcp__crm__x', label: 'Server 未对本项目开放' }]);
    assert.deepEqual(G.invalidBadges('kb-agent', undefined, L.invalidReasonLabel), []);
    assert.deepEqual(G.limitSpecs(tools[0]).map((s) => s.name.split('.').pop()), ['mcp_timeout_s', 'mcp_max_calls_per_turn']);
  });
});

// =========================================================================== //
// client.ts（unit：真实执行，替身 fetch）
// =========================================================================== //

describe('ApiClient mcp* 请求形状', () => {
  it('TC-FE-R29-010 Server 生命周期：方法 / 路径 / 请求体；标识名做 URL 编码；删除带 confirm 与 force 查询参数', async () => {
    const { c, calls } = harness();
    await c.mcpListServers();
    await c.mcpCreateServer({ server_id: 'crm', description: 'd', transport: 'streamable_http', endpoint_url: 'https://x/mcp', auth_kind: 'bearer', credential_scope: 'shared', scope_kind: 'platform', data_categories: ['query_text'] });
    await c.mcpPatchServer('crm', { description: 'n', expected_updated_at: 't0' });
    await c.mcpVerify('crm'); await c.mcpEnable('crm'); await c.mcpDisable('crm'); await c.mcpRefresh('crm');
    await c.mcpDeleteServer('crm', { confirm: 'crm', force: true });
    await c.mcpDeleteServer('a b', { confirm: 'a b', force: false });
    const shape = calls.map((x) => [x.init.method ?? 'GET', x.url]);
    assert.deepEqual(shape, [
      ['GET', '/api/mcp/servers'], ['POST', '/api/mcp/servers'], ['PATCH', '/api/mcp/servers/crm'],
      ['POST', '/api/mcp/servers/crm/verify'], ['POST', '/api/mcp/servers/crm/enable'], ['POST', '/api/mcp/servers/crm/disable'], ['POST', '/api/mcp/servers/crm/refresh'],
      ['DELETE', '/api/mcp/servers/crm?confirm=crm&force=1'], ['DELETE', '/api/mcp/servers/a%20b?confirm=a+b&force=0'],
    ]);
    assert.deepEqual(JSON.parse(calls[2].init.body), { description: 'n', expected_updated_at: 't0' });
    assert.equal(JSON.parse(calls[1].init.body).transport, 'streamable_http');
  });

  it('TC-FE-R29-011 凭证：PUT 带 scope / secret，DELETE 带 scope（项目范围另带 project_id）；开放范围 PUT 请求体', async () => {
    const { c, calls } = harness();
    await c.mcpSetCredential('crm', { scope: 'shared', secret: 'S' });
    await c.mcpSetCredential('erp', { scope: 'project', project_id: 'p_alpha', secret: 'T' });
    await c.mcpClearCredential('crm', 'shared');
    await c.mcpClearCredential('erp', 'project', 'p_alpha');
    await c.mcpSetOpen('crm', { open_all: false, project_ids: ['p_alpha'] });
    assert.deepEqual(calls.map((x) => [x.init.method, x.url]), [
      ['PUT', '/api/mcp/servers/crm/credentials'], ['PUT', '/api/mcp/servers/erp/credentials'],
      ['DELETE', '/api/mcp/servers/crm/credentials?scope=shared'], ['DELETE', '/api/mcp/servers/erp/credentials?scope=project&project_id=p_alpha'],
      ['PUT', '/api/mcp/servers/crm/open'],
    ]);
    assert.deepEqual(JSON.parse(calls[1].init.body), { scope: 'project', project_id: 'p_alpha', secret: 'T' });
    assert.deepEqual(JSON.parse(calls[4].init.body), { open_all: false, project_ids: ['p_alpha'] });
    for (const x of calls) assert.ok(!/token=/.test(x.url), '令牌只经 Authorization 头，URL 不含 token=');
  });

  it('TC-FE-R29-012 工具：筛选查询串、审核（approve / reject）、启停、固定入参、放行 / 撤销', async () => {
    const { c, calls } = harness();
    await c.mcpListTools();
    await c.mcpListTools({ server_id: 'crm', state: 'needs_rereview', risk: 'unknown', granted: false });
    await c.mcpGetTool(7);
    await c.mcpReviewTool(7, { decision: 'approve', expected_fingerprint: 'fp', risk: 'read_only', hidden_params: ['debug'], ack_tenant_params: true });
    await c.mcpReviewTool(7, { decision: 'reject' });
    await c.mcpSetToolState(7, false);
    await c.mcpPutBinding(7, 'p_alpha', { tenant: 'a-001' });
    await c.mcpPutWaiver(7, 'p_alpha', '已评估');
    await c.mcpDeleteWaiver(7, 'p_alpha');
    assert.deepEqual(calls.map((x) => [x.init.method ?? 'GET', x.url]), [
      ['GET', '/api/mcp/tools'], ['GET', '/api/mcp/tools?server_id=crm&state=needs_rereview&risk=unknown&granted=0'], ['GET', '/api/mcp/tools/7'],
      ['POST', '/api/mcp/tools/7/review'], ['POST', '/api/mcp/tools/7/review'], ['POST', '/api/mcp/tools/7/state'],
      ['PUT', '/api/mcp/tools/7/bindings/p_alpha'], ['PUT', '/api/mcp/tools/7/waivers/p_alpha'], ['DELETE', '/api/mcp/tools/7/waivers/p_alpha'],
    ]);
    assert.deepEqual(JSON.parse(calls[3].init.body), { decision: 'approve', expected_fingerprint: 'fp', risk: 'read_only', hidden_params: ['debug'], ack_tenant_params: true });
    assert.deepEqual(JSON.parse(calls[4].init.body), { decision: 'reject' });
    assert.deepEqual(JSON.parse(calls[6].init.body), { fixed_args: { tenant: 'a-001' } });
    assert.deepEqual(JSON.parse(calls[7].init.body), { reason: '已评估' });
  });

  it('TC-FE-R29-013 治理 / 内网允许名单 / 审计：路径与参数（空过滤项不入查询串）', async () => {
    const { c, calls } = harness();
    await c.mcpGetGovernance();
    await c.mcpPutGovernance({ call_timeout_s: 20 });
    await c.mcpListInternalAllow();
    await c.mcpAddInternalAllow('10.0.0.8', 9000);
    await c.mcpRemoveInternalAllow('10.0.0.8', 9000);
    await c.mcpAudit({ server_id: 'crm', tool: '', kind: 'call', limit: 50 });
    await c.mcpAudit();
    assert.deepEqual(calls.map((x) => [x.init.method ?? 'GET', x.url]), [
      ['GET', '/api/mcp/governance'], ['PUT', '/api/mcp/governance'], ['GET', '/api/mcp/internal-allow'], ['POST', '/api/mcp/internal-allow'],
      ['DELETE', '/api/mcp/internal-allow?host=10.0.0.8&port=9000'], ['GET', '/api/mcp/audit?server_id=crm&kind=call&limit=50'], ['GET', '/api/mcp/audit'],
    ]);
    assert.deepEqual(JSON.parse(calls[3].init.body), { host: '10.0.0.8', port: 9000 });
  });
});

// =========================================================================== //
// 页面 / 路由 / 导航 / 配置页（integration：源码结构契约）
// =========================================================================== //

describe('McpServersPage 源码契约', () => {
  it('TC-FE-R29-020 HTTP 只经 client（无 fetch / axios / 外链 / CDN）；使用词表；不含 stdio 选项（AC-001-06）', () => {
    assert.match(page, /import \{ client \} from '\.\.\/app\/env'/);
    assert.ok(!/\bfetch\(/.test(page) && !/axios/.test(page), '页面不得自行发 HTTP');
    assert.ok(!/https?:\/\/(?!…)[a-z0-9.-]+\.[a-z]{2,}/i.test(page.replace(/placeholder="[^"]*"/g, '')), '运行期禁止外链 / CDN');
    assert.match(page, /TRANSPORT_OPTIONS/);
    assert.ok(!/stdio/i.test(page), '登记表单不出现 stdio');
    for (const m of ['mcpListServers', 'mcpCreateServer', 'mcpVerify', 'mcpEnable', 'mcpDisable', 'mcpRefresh', 'mcpDeleteServer', 'mcpSetCredential',
      'mcpSetOpen', 'mcpReviewTool', 'mcpPutBinding', 'mcpPutWaiver', 'mcpGetGovernance', 'mcpAddInternalAllow', 'mcpAudit']) {
      assert.ok(page.includes(`client.${m}(`), `页面应调用 client.${m}`);
    }
  });

  it('TC-FE-R29-021 凭证输入框 type="password"、autocomplete="new-password"；提交后立即清空，永不回填（AC-006-04）', () => {
    assert.match(page, /<input v-model="secret" type="password" autocomplete="new-password"/);
    const fn = page.slice(page.indexOf('async function saveCredential'), page.indexOf('async function clearCredential'));
    assert.ok(fn.length > 50);
    assert.ok(fn.indexOf("secret.value = ''") >= 0 && fn.indexOf("secret.value = ''") < fn.indexOf('client.mcpSetCredential'), '先捕获值并清空输入框，再发请求（失败也不回填）');
    assert.ok(!/secret\.value\s*=\s*[^'\s]/.test(page.replace(/secret\.value = ''/g, '')), 'secret 只会被置空，从不被赋值为服务端返回值');
    assert.ok(!/detail\.value\.secret|\.credential\.value|secret:\s*detail/.test(page), '页面从不读取服务端凭证值');
  });

  it('TC-FE-R29-022 删除对话框：要求输入标识名二次确认；强制删除为独立勾选；确认值经 client 的 confirm / force 参数发出（AC-005-04 / 06）', () => {
    assert.match(page, /v-model="delConfirm"/);
    assert.match(page, /v-model="delForce"/);
    assert.match(page, /mcpDeleteServer\(delTarget\.value\.server_id, \{ confirm: delConfirm\.value, force: delForce\.value \}\)/);
    assert.match(page, /delConfirm\.value\s*(!==|===)\s*delTarget\.value\.server_id|disabled/);
  });

  it('TC-FE-R29-023 审核对话框并列展示：描述原文 / schema / 服务方注解（标“服务方自报，未经核实”）/ 差异 / 疑似租户参数确认 / 风险裁定 / 屏蔽参数 / 用途说明改写', () => {
    assert.match(page, /UNVERIFIED_ANNOTATION_NOTE/);
    assert.match(page, /review\.suspect_tenant_params/);
    assert.match(page, /v-model="reviewForm\.ack"/);
    assert.match(page, /v-model="reviewForm\.hidden"/);
    assert.match(page, /v-model="reviewForm\.llmDescription"/);
    assert.match(page, /v-model="reviewForm\.risk"/);
    assert.match(page, /review\.diff|\.diff\b/);
    assert.match(page, /maxlength="1000"/, '用途说明改写 ≤ 1000 字符');
  });

  it('TC-FE-R29-024 放行：理由必填（空理由前端先拦）；无“调用前确认（HITL）”界面（已移出本轮 OOS-R29-12）', () => {
    assert.match(page, /放行理由/);
    assert.match(page, /waiverReason/);
    assert.ok(!/HITL|调用前确认|人工确认后调用/.test(page.replace(/\/\/[^\n]*/g, '')), '本轮不做 HITL 界面');
  });

  it('TC-FE-R29-025 403 / 503 / 409 等服务端拒绝有专门文案（用 apiErrorLabel 兜底而非裸错误码）', () => {
    assert.match(page, /apiErrorLabel/);
    assert.match(page, /failureCategoryLabel/);
    assert.match(page, /serverStatusLabel/);
  });
});

describe('路由 / 导航 / 配置页接线', () => {
  it('TC-FE-R29-030 路由 #/system/mcp：仅 admin（requiresAdmin）、挂在 system 下、组件为 McpServersPage', () => {
    assert.match(router, /import McpServersPage from '\.\.\/views\/McpServersPage\.vue'/);
    assert.match(router, /path: 'mcp',\s*name: 'mcp',\s*component: McpServersPage,\s*meta: \{ title: 'MCP 服务', requiresAdmin: true \}/);
    const sys = router.slice(router.indexOf("path: 'system'"));
    assert.ok(sys.indexOf("path: 'mcp'") > 0, 'mcp 路由位于 system 子路由内');
  });

  it('TC-FE-R29-031 导航：SYSTEM_ORDER 严格为五项且 mcp 在末尾；既有三项相对顺序不变；入口可发现性由路由表派生（adminOnly）', () => {
    assert.match(layout, /const SYSTEM_ORDER = \['accounts', 'projects', 'llm-key', 'web-governance', 'mcp'\];/);
    const order = layout.match(/SYSTEM_ORDER = \[([^\]]*)\]/)[1].split(',').map((s) => s.trim().replace(/'/g, ''));
    assert.deepEqual(order, ['accounts', 'projects', 'llm-key', 'web-governance', 'mcp']);
    assert.match(layout, /adminOnly: r\.meta\.requiresAdmin === true/);
  });

  it('TC-FE-R29-032 配置页外部工具区：来自 catalog.external_tools；无可见外部工具且无失效授权时不渲染；沿用既有保存通道（emit change），不新增 HTTP', () => {
    assert.match(panel, /externalGroups = computed\(\(\) => groupByServer\(props\.catalog\?\.external_tools \?\? \[\]\)\)/);
    assert.match(panel, /v-if="externalGroups\.length \|\| staleBadges\.length"/);
    assert.match(panel, /emit\('change', toggleExternalGrant\(/);
    assert.ok(!/\bfetch\(|client\.mcp/.test(panel), '配置页面板不直接发 HTTP');
    assert.match(panel, /isGreyed\(t, hasTool\(t\.local_name\)\)/);
    assert.match(panel, /失效：/);
  });

  it('TC-FE-R29-033 client.ts 约束：无 axios / CDN；mcp 方法全部经 this.request；凭证方法响应类型不含 secret 字段；McpServerDto 类型无凭证值字段', () => {
    assert.ok(!/axios/.test(clientSrc));
    const mcpBlock = clientSrc.slice(clientSrc.indexOf('mcpListServers'));
    assert.ok(!/\bfetch\(/.test(mcpBlock.slice(0, mcpBlock.indexOf('mcpAudit') + 600)), 'mcp* 方法不直接 fetch');
    const dto = clientSrc.match(/export interface McpServerDto \{[\s\S]*?\n\}/)[0];
    assert.ok(!/secret|token|password|credential_value/i.test(dto.replace(/credential: McpCredentialStatusDto;/, '')), 'McpServerDto 无凭证值字段');
    const credResp = clientSrc.match(/mcpSetCredential\([\s\S]*?\): Promise<\{([^}]*)\}>/)[1];
    assert.ok(!/secret/.test(credResp), '凭证写入响应类型不含 secret');
  });
});
