<script setup lang="ts">
/**
 * @module MOD-R29-22
 * @implements US-001~007 / 010~015 / 021 / 024 / 026 MCP 服务管理页（“系统管理 → MCP 服务”；**仅 admin**）
 * @depends MOD-R29-21（client.mcp* / utils/mcpLabels）
 *
 * 管理入口而非权限边界：非 admin 的读写一律服务端 403。凭证输入框 type="password"，提交后立即清空，永不回填；
 * 工具描述 / schema / 注解均为服务方自报的不可信数据，仅以文本插值展示（不渲染为 HTML）。
 * 传输类型下拉只有 streamable_http；无任何“调用前确认”界面。
 */
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

import { client } from '../app/env';
import {
  ApiClientError,
  type McpAuditDto,
  type McpDataCategory,
  type McpGovernanceDto,
  type McpInternalAllowDto,
  type McpRisk,
  type McpServerDto,
  type McpToolDetailDto,
  type McpToolDto,
  type McpToolState,
} from '../api/client';
import {
  UNVERIFIED_ANNOTATION_NOTE,
  apiErrorLabel,
  failureCategoryLabel,
  riskLabel,
  serverStatusLabel,
  toolStateLabel,
  TRANSPORT_OPTIONS,
} from '../utils/mcpLabels';

const tab = ref<'servers' | 'tools' | 'governance' | 'audit'>('servers');
const loading = ref(false);
const loadError = ref('');
const servers = ref<McpServerDto[]>([]);
const tools = ref<McpToolDto[]>([]);
const projects = ref<string[]>([]);

const DATA_CATEGORY_OPTIONS: { value: McpDataCategory; label: string }[] = [
  { value: 'query_text', label: '用户提问文本' },
  { value: 'structured_args', label: '结构化参数' },
  { value: 'business_ids', label: '业务标识' },
  { value: 'other', label: '其他' },
];

function msg(err: unknown, fallback: string): string {
  if (err instanceof ApiClientError) {
    if (err.status === 403) return '当前账户无权管理 MCP 服务（仅管理员可操作）。';
    if (err.status === 503) return 'MCP 存储暂不可用或功能未启用，请稍后重试。';
    return apiErrorLabel(err.code, err.message || fallback);
  }
  return '无法连接服务，请确认服务已启动。';
}

async function reload(): Promise<void> {
  loading.value = true;
  loadError.value = '';
  try {
    servers.value = (await client.mcpListServers()).items;
    tools.value = (await client.mcpListTools(toolFilter)).items;
  } catch (err) {
    loadError.value = msg(err, '加载 MCP 服务失败。');
  } finally {
    loading.value = false;
  }
}

// ------------------------------------------------------------------ 登记
const regVisible = ref(false);
const reg = reactive({
  server_id: '',
  description: '',
  transport: 'streamable_http' as const,
  endpoint_url: '',
  auth_kind: 'bearer' as 'none' | 'bearer' | 'header',
  auth_header_name: '',
  credential_scope: 'shared' as 'shared' | 'project',
  scope_kind: 'platform' as 'platform' | 'project',
  owner_project: '',
  data_categories: ['query_text'] as McpDataCategory[],
});
const regError = ref('');
async function register(): Promise<void> {
  regError.value = '';
  try {
    await client.mcpCreateServer({
      server_id: reg.server_id.trim(),
      description: reg.description,
      transport: reg.transport,
      endpoint_url: reg.endpoint_url.trim(),
      auth_kind: reg.auth_kind,
      auth_header_name: reg.auth_kind === 'header' ? reg.auth_header_name.trim() : null,
      credential_scope: reg.credential_scope,
      scope_kind: reg.scope_kind,
      owner_project: reg.scope_kind === 'project' ? reg.owner_project : null,
      data_categories: reg.data_categories,
    });
    regVisible.value = false;
    ElMessage.success('已登记（状态：未启用，请先验证连接并启用）');
    await reload();
  } catch (err) {
    regError.value = msg(err, '登记失败。');
  }
}

// ------------------------------------------------------------------ Server 操作
async function act(label: string, fn: () => Promise<unknown>): Promise<void> {
  try {
    await fn();
    ElMessage.success(`${label}成功`);
  } catch (err) {
    ElMessage.error(`${label}失败：${msg(err, '请重试')}`);
  }
  await reload();
}
async function verify(s: McpServerDto): Promise<void> {
  try {
    const r = await client.mcpVerify(s.server_id);
    if (r.ok) ElMessage.success(`验证通过（${r.era === 'modern' ? '新版协议' : '兼容协议'} ${r.protocol_version ?? ''}）`);
    else ElMessage.warning(`验证未通过：${failureCategoryLabel(r.category)}`);
  } catch (err) {
    ElMessage.error(msg(err, '验证失败'));
  }
  await reload();
}
const enable = (s: McpServerDto) => act('启用', () => client.mcpEnable(s.server_id));
const disable = (s: McpServerDto) => act('停用', () => client.mcpDisable(s.server_id));
async function refresh(s: McpServerDto): Promise<void> {
  try {
    const { diff } = await client.mcpRefresh(s.server_id);
    ElMessage.success(`刷新完成：新增 ${diff.added.length}，变化 ${diff.changed.length}，下线 ${diff.offline.length}，排除 ${diff.excluded.length}`);
  } catch (err) {
    ElMessage.error(msg(err, '刷新失败'));
  }
  await reload();
}

// 删除：先展示影响清单并要求输入标识名二次确认；强制删除为独立勾选
const delVisible = ref(false);
const delTarget = ref<McpServerDto | null>(null);
const delConfirm = ref('');
const delForce = ref(false);
const delInfo = ref('');
async function openDelete(s: McpServerDto): Promise<void> {
  delTarget.value = s;
  delConfirm.value = '';
  delForce.value = false;
  delInfo.value = '';
  try {
    const d = await client.mcpGetServer(s.server_id);
    const c = d.references_count;
    delInfo.value = c && (c.projects || c.agents) ? `仍被 ${c.projects} 个项目 / ${c.agents} 个 agent 授权引用。` : '当前没有项目授权引用该服务。';
  } catch (err) {
    delInfo.value = msg(err, '无法读取引用情况');
  }
  delVisible.value = true;
}
async function doDelete(): Promise<void> {
  if (!delTarget.value) return;
  try {
    await client.mcpDeleteServer(delTarget.value.server_id, { confirm: delConfirm.value, force: delForce.value });
    ElMessage.success('已删除');
    delVisible.value = false;
  } catch (err) {
    ElMessage.error(msg(err, '删除失败'));
  }
  await reload();
}

// ------------------------------------------------------------------ 详情抽屉
const drawer = ref(false);
const detail = ref<McpServerDto | null>(null);
const secret = ref('');
const credScope = ref<'shared' | 'discovery' | 'project'>('shared');
const credProject = ref('');
const openAll = ref(false);
const openProjects = ref<string[]>([]);
async function openDetail(s: McpServerDto): Promise<void> {
  try {
    detail.value = await client.mcpGetServer(s.server_id);
  } catch (err) {
    ElMessage.error(msg(err, '读取详情失败'));
    return;
  }
  openAll.value = detail.value.open_all;
  openProjects.value = detail.value.open_projects ?? [];
  credScope.value = detail.value.credential_scope === 'shared' ? 'shared' : 'discovery';
  secret.value = '';
  try {
    projects.value = (await client.listProjects()).map((x) => x.project_id);
  } catch {
    projects.value = [];
  }
  drawer.value = true;
}
async function saveCredential(): Promise<void> {
  if (!detail.value) return;
  const value = secret.value;
  secret.value = ''; // 提交即清空，永不回填
  try {
    await client.mcpSetCredential(detail.value.server_id, {
      scope: credScope.value,
      project_id: credScope.value === 'project' ? credProject.value : undefined,
      secret: value,
    });
    ElMessage.success('凭证已保存（仅写入，不会再显示）');
    detail.value = await client.mcpGetServer(detail.value.server_id);
  } catch (err) {
    ElMessage.error(msg(err, '保存凭证失败'));
  }
}
async function clearCredential(): Promise<void> {
  if (!detail.value) return;
  await act('清除凭证', () =>
    client.mcpClearCredential(detail.value!.server_id, credScope.value, credScope.value === 'project' ? credProject.value : undefined),
  );
}
async function saveOpen(): Promise<void> {
  if (!detail.value) return;
  await act('保存开放范围', () => client.mcpSetOpen(detail.value!.server_id, { open_all: openAll.value, project_ids: openProjects.value }));
}

// ------------------------------------------------------------------ 工具目录 / 审核
const toolFilter = reactive<{ server_id?: string; state?: McpToolState; risk?: McpRisk }>({});
const reviewVisible = ref(false);
const review = ref<McpToolDetailDto | null>(null);
const reviewForm = reactive({ risk: 'unknown' as McpRisk, hidden: [] as string[], llmDescription: '', ack: false });
const reviewProps = computed(() => {
  const props = review.value?.observed?.input_schema?.properties;
  return props && typeof props === 'object' ? Object.keys(props as Record<string, unknown>) : [];
});
async function openReview(t: McpToolDto): Promise<void> {
  try {
    review.value = await client.mcpGetTool(t.tool_id);
  } catch (err) {
    ElMessage.error(msg(err, '读取工具失败'));
    return;
  }
  reviewForm.risk = review.value.risk;
  reviewForm.hidden = [...review.value.hidden_params];
  reviewForm.llmDescription = review.value.llm_description ?? '';
  reviewForm.ack = false;
  reviewVisible.value = true;
}
async function approve(): Promise<void> {
  const r = review.value;
  if (!r || !r.observed_fingerprint) return;
  try {
    await client.mcpReviewTool(r.tool_id, {
      decision: 'approve',
      expected_fingerprint: r.observed_fingerprint,
      risk: reviewForm.risk,
      hidden_params: reviewForm.hidden,
      llm_description: reviewForm.llmDescription || undefined,
      ack_tenant_params: reviewForm.ack,
    });
    ElMessage.success('已通过审核（后台将刷新相关项目的运行时）');
    reviewVisible.value = false;
  } catch (err) {
    ElMessage.error(msg(err, '审核失败'));
  }
  await reload();
}
async function reject(): Promise<void> {
  if (!review.value) return;
  await act('驳回', () => client.mcpReviewTool(review.value!.tool_id, { decision: 'reject' }));
  reviewVisible.value = false;
}
const toggleTool = (t: McpToolDto, on: boolean) => act(on ? '启用工具' : '禁用工具', () => client.mcpSetToolState(t.tool_id, on));

// 固定入参 / 放行
const bindVisible = ref(false);
const bindTool = ref<McpToolDto | null>(null);
const bindProject = ref('');
const bindJson = ref('{}');
const waiverReason = ref('');
function openBinding(t: McpToolDto): void {
  bindTool.value = t;
  bindProject.value = '';
  bindJson.value = '{}';
  waiverReason.value = '';
  bindVisible.value = true;
}
async function saveBinding(): Promise<void> {
  if (!bindTool.value || !bindProject.value) return;
  let parsed: Record<string, unknown>;
  try {
    parsed = JSON.parse(bindJson.value);
  } catch {
    ElMessage.error('固定入参须为合法 JSON 对象');
    return;
  }
  await act('保存固定入参', () => client.mcpPutBinding(bindTool.value!.tool_id, bindProject.value, parsed));
}
async function grantWaiver(): Promise<void> {
  if (!bindTool.value || !bindProject.value) return;
  if (!waiverReason.value.trim()) {
    ElMessage.error('放行理由必填');
    return;
  }
  await act('放行', () => client.mcpPutWaiver(bindTool.value!.tool_id, bindProject.value, waiverReason.value));
}
const revokeWaiver = () =>
  bindTool.value && bindProject.value ? act('撤销放行', () => client.mcpDeleteWaiver(bindTool.value!.tool_id, bindProject.value)) : Promise.resolve();

// ------------------------------------------------------------------ 治理 / 允许名单
const gov = ref<McpGovernanceDto | null>(null);
const govForm = reactive<Record<string, number>>({});
const allow = ref<McpInternalAllowDto[]>([]);
const allowForm = reactive({ host: '', port: 80 });
const GOV_FIELDS: { key: string; label: string }[] = [
  { key: 'discover_timeout_s', label: '连接验证 / 清单获取超时（秒）' },
  { key: 'call_timeout_s', label: '单次调用超时（秒）' },
  { key: 'max_calls_per_turn', label: '每回合外部工具调用上限（次）' },
  { key: 'max_result_bytes', label: '单次结果字节上限' },
  { key: 'breaker_threshold', label: '熔断阈值（连续失败次数）' },
  { key: 'breaker_cooldown_s', label: '熔断冷却（秒）' },
  { key: 'max_concurrency_per_server', label: '单 Server 并发上限' },
  { key: 'max_inflight_global', label: '全局并发上限' },
  { key: 'max_tools_per_server', label: '单 Server 工具数上限' },
  { key: 'max_description_chars', label: '描述字符数上限' },
  { key: 'max_schema_bytes', label: '入参 schema 字节上限' },
  { key: 'max_schema_depth', label: '入参 schema 深度上限' },
  { key: 'max_arg_bytes', label: '入参字节上限' },
  { key: 'health_interval_s', label: '健康探测间隔（秒，0 = 关闭）' },
  { key: 'revalidate_interval_s', label: '周期复核间隔（秒，0 = 关闭）' },
  { key: 'listener_max', label: '变更监听连接数上限' },
];
async function loadGov(): Promise<void> {
  try {
    const g = await client.mcpGetGovernance();
    gov.value = g;
    for (const f of GOV_FIELDS) govForm[f.key] = (g as unknown as Record<string, number>)[f.key];
    allow.value = (await client.mcpListInternalAllow()).items;
  } catch (err) {
    ElMessage.error(msg(err, '加载治理参数失败'));
  }
}
async function saveGov(): Promise<void> {
  await act('保存治理参数', async () => {
    gov.value = await client.mcpPutGovernance(govForm as unknown as Omit<McpGovernanceDto, 'hard_max' | 'updated_at' | 'updated_by'>);
  });
}
async function addAllow(): Promise<void> {
  try {
    const r = await client.mcpAddInternalAllow(allowForm.host.trim(), Number(allowForm.port));
    if (!r.effective) ElMessage.warning('该地址属于永不放行范围（链路本地 / 元数据等），已记录但不会生效');
    else ElMessage.success('已添加');
    allowForm.host = '';
    allow.value = (await client.mcpListInternalAllow()).items;
  } catch (err) {
    ElMessage.error(msg(err, '添加失败'));
  }
}
async function removeAllow(a: McpInternalAllowDto): Promise<void> {
  try {
    await ElMessageBox.confirm(`确认移除 ${a.host}:${a.port}？`, '移除内网允许名单条目', { type: 'warning' });
  } catch {
    return;
  }
  await act('移除', () => client.mcpRemoveInternalAllow(a.host, a.port));
  allow.value = (await client.mcpListInternalAllow()).items;
}

// ------------------------------------------------------------------ 审计
const audit = ref<McpAuditDto[]>([]);
const auditTotal = ref(0);
const auditFilter = reactive({ server_id: '', tool: '', project_id: '', kind: '' });
async function loadAudit(): Promise<void> {
  try {
    const r = await client.mcpAudit({ ...auditFilter, limit: 100 });
    audit.value = r.items;
    auditTotal.value = r.total;
  } catch (err) {
    ElMessage.error(msg(err, '加载审计失败'));
  }
}

function onTab(name: string | number): void {
  if (name === 'governance') void loadGov();
  if (name === 'audit') void loadAudit();
}

onMounted(reload);
</script>

<template>
  <section class="mcp-page">
    <div class="head">
      <div>
        <h2 class="ib-page-title">MCP 服务</h2>
        <p class="ib-page-sub">
          登记外部 MCP 服务，审核其工具后再按项目开放与授权。外部工具返回的内容属于不可信数据，仅作只读参考，并会随对话进入 LLM 上下文。
        </p>
      </div>
      <el-button type="primary" @click="regVisible = true">登记服务</el-button>
    </div>

    <el-alert v-if="loadError" type="error" :closable="false" show-icon :title="loadError" class="load-error" />

    <el-tabs v-model="tab" @tab-change="onTab">
      <el-tab-pane label="服务" name="servers">
        <el-table v-loading="loading" :data="servers" size="small" empty-text="尚未登记任何服务">
          <el-table-column prop="server_id" label="标识名" width="140" />
          <el-table-column label="状态" width="120">
            <template #default="{ row }">{{ serverStatusLabel(row) }}</template>
          </el-table-column>
          <el-table-column prop="endpoint_url" label="地址" min-width="220" show-overflow-tooltip />
          <el-table-column label="协议" width="130">
            <template #default="{ row }">{{ row.protocol_version || '—' }}</template>
          </el-table-column>
          <el-table-column label="工具" width="150">
            <template #default="{ row }">
              已启用 {{ row.tool_counts.enabled }} / 待审核 {{ row.tool_counts.pending_review }}
              <el-tag v-if="row.tool_counts.needs_rereview" type="warning" size="small">待复审 {{ row.tool_counts.needs_rereview }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="最近验证" width="150">
            <template #default="{ row }">{{ row.last_verify_at || '—' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="330" fixed="right">
            <template #default="{ row }">
              <el-button size="small" link @click="openDetail(row)">详情</el-button>
              <el-button size="small" link @click="verify(row)">测试连接</el-button>
              <el-button v-if="row.admin_state !== 'enabled'" size="small" link type="primary" @click="enable(row)">启用</el-button>
              <el-button v-else size="small" link @click="disable(row)">停用</el-button>
              <el-button size="small" link @click="refresh(row)">刷新工具</el-button>
              <el-button size="small" link type="danger" @click="openDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="工具目录" name="tools">
        <div class="filters">
          <el-select v-model="toolFilter.server_id" clearable placeholder="全部服务" size="small" @change="reload">
            <el-option v-for="s in servers" :key="s.server_id" :value="s.server_id" :label="s.server_id" />
          </el-select>
          <el-select v-model="toolFilter.state" clearable placeholder="全部状态" size="small" @change="reload">
            <el-option v-for="st in ['pending_review', 'enabled', 'disabled', 'needs_rereview', 'offline', 'excluded']" :key="st" :value="st" :label="toolStateLabel(st)" />
          </el-select>
          <el-select v-model="toolFilter.risk" clearable placeholder="全部风险" size="small" @change="reload">
            <el-option v-for="r in ['read_only', 'side_effect', 'unknown']" :key="r" :value="r" :label="riskLabel(r)" />
          </el-select>
        </div>
        <el-table :data="tools" size="small" empty-text="没有符合条件的工具">
          <el-table-column prop="display_name" label="工具（展示名）" min-width="200" show-overflow-tooltip />
          <el-table-column prop="local_name" label="注册名" min-width="200" show-overflow-tooltip />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.state === 'needs_rereview' ? 'warning' : row.state === 'enabled' ? 'success' : 'info'" size="small">{{ toolStateLabel(row.state) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="风险" width="90">
            <template #default="{ row }">{{ riskLabel(row.risk) }}</template>
          </el-table-column>
          <el-table-column label="授权引用" width="100">
            <template #default="{ row }">{{ row.grants.length }}</template>
          </el-table-column>
          <el-table-column label="操作" width="260" fixed="right">
            <template #default="{ row }">
              <el-button v-if="['pending_review', 'needs_rereview', 'disabled'].includes(row.state)" size="small" link type="primary" @click="openReview(row)">审核</el-button>
              <el-button v-else size="small" link @click="openReview(row)">查看</el-button>
              <el-button v-if="row.state === 'enabled'" size="small" link @click="toggleTool(row, false)">禁用</el-button>
              <el-button v-if="row.state === 'disabled' && row.approved_fingerprint" size="small" link @click="toggleTool(row, true)">启用</el-button>
              <el-button v-if="row.approved_fingerprint" size="small" link @click="openBinding(row)">固定入参 / 放行</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane label="治理与允许名单" name="governance">
        <el-card class="ib-card" header="全局治理参数（新调用立即生效；Server 与 agent 只能调低）">
          <el-form label-position="top" class="gov-grid">
            <el-form-item v-for="f in GOV_FIELDS" :key="f.key" :label="f.label">
              <el-input-number v-model="govForm[f.key]" :min="gov?.hard_max?.[f.key]?.min ?? 0" :max="gov?.hard_max?.[f.key]?.max ?? 100000" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="saveGov">保存</el-button>
          <span class="ib-muted meta">最后更新：{{ gov?.updated_at || '—' }}（{{ gov?.updated_by || '—' }}）</span>
        </el-card>
        <el-card class="ib-card" header="内网允许名单（精确 主机:端口；仅回环 / 内网 / CGNAT 可生效）">
          <el-table :data="allow" size="small" empty-text="名单为空">
            <el-table-column prop="host" label="主机" />
            <el-table-column prop="port" label="端口" width="90" />
            <el-table-column label="状态" width="160">
              <template #default="{ row }">
                <el-tag v-if="!row.effective" type="danger" size="small">永不放行（不生效）</el-tag>
                <el-tag v-else type="success" size="small">生效</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="90">
              <template #default="{ row }"><el-button size="small" link type="danger" @click="removeAllow(row)">移除</el-button></template>
            </el-table-column>
          </el-table>
          <div class="allow-add">
            <el-input v-model="allowForm.host" size="small" placeholder="主机名或 IP" />
            <el-input-number v-model="allowForm.port" size="small" :min="1" :max="65535" />
            <el-button size="small" type="primary" @click="addAllow">添加</el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="审计" name="audit">
        <div class="filters">
          <el-input v-model="auditFilter.server_id" size="small" placeholder="服务标识名" clearable />
          <el-input v-model="auditFilter.tool" size="small" placeholder="工具注册名" clearable />
          <el-input v-model="auditFilter.project_id" size="small" placeholder="项目" clearable />
          <el-select v-model="auditFilter.kind" size="small" clearable placeholder="类型">
            <el-option value="admin" label="管理" /><el-option value="call" label="调用" /><el-option value="system" label="系统" />
          </el-select>
          <el-button size="small" type="primary" @click="loadAudit">查询</el-button>
        </div>
        <el-table :data="audit" size="small" empty-text="没有审计记录">
          <el-table-column prop="ts" label="时间" width="170" />
          <el-table-column prop="kind" label="类型" width="80" />
          <el-table-column prop="action" label="动作" width="150" />
          <el-table-column prop="actor" label="操作者" width="140" show-overflow-tooltip />
          <el-table-column prop="project_id" label="项目" width="110" />
          <el-table-column prop="server_id" label="服务" width="110" />
          <el-table-column prop="tool_name" label="工具" min-width="160" show-overflow-tooltip />
          <el-table-column prop="outcome" label="结果" width="90" />
          <el-table-column prop="reason" label="原因" min-width="140" show-overflow-tooltip />
          <el-table-column prop="duration_ms" label="耗时(ms)" width="90" />
        </el-table>
        <p class="ib-muted meta">共 {{ auditTotal }} 条（审计不记录凭证与完整入参，仅摘要）。</p>
      </el-tab-pane>
    </el-tabs>

    <!-- 登记 -->
    <el-dialog v-model="regVisible" title="登记 MCP 服务" width="560px">
      <el-form label-width="110px" size="small">
        <el-form-item label="标识名"><el-input v-model="reg.server_id" placeholder="小写字母开头，a-z 0-9 -，2~24 位" /></el-form-item>
        <el-form-item label="说明"><el-input v-model="reg.description" maxlength="500" /></el-form-item>
        <el-form-item label="传输类型">
          <el-select v-model="reg.transport"><el-option v-for="t in TRANSPORT_OPTIONS" :key="t" :value="t" :label="t" /></el-select>
        </el-form-item>
        <el-form-item label="地址"><el-input v-model="reg.endpoint_url" placeholder="https://…（公网目标必须 https）" /></el-form-item>
        <el-form-item label="鉴权方式">
          <el-radio-group v-model="reg.auth_kind">
            <el-radio value="bearer">Bearer 令牌</el-radio>
            <el-radio value="header">自定义头</el-radio>
            <el-radio value="none">无（仅内网允许名单目标）</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="reg.auth_kind === 'header'" label="头名"><el-input v-model="reg.auth_header_name" /></el-form-item>
        <el-form-item label="凭证范围">
          <el-radio-group v-model="reg.credential_scope"><el-radio value="shared">全平台共用</el-radio><el-radio value="project">按项目专属</el-radio></el-radio-group>
        </el-form-item>
        <el-form-item label="可见范围">
          <el-radio-group v-model="reg.scope_kind"><el-radio value="platform">平台级</el-radio><el-radio value="project">项目专属</el-radio></el-radio-group>
          <el-input v-if="reg.scope_kind === 'project'" v-model="reg.owner_project" placeholder="所属项目标识" />
        </el-form-item>
        <el-form-item label="外发数据类别">
          <el-checkbox-group v-model="reg.data_categories">
            <el-checkbox v-for="c in DATA_CATEGORY_OPTIONS" :key="c.value" :value="c.value">{{ c.label }}</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <el-alert type="info" :closable="false" show-icon title="外部工具的返回内容会进入 LLM 上下文并随之发往 LLM 服务方，请确认登记的服务可接受。" />
      <el-alert v-if="regError" type="error" :closable="false" show-icon :title="regError" class="gap" />
      <template #footer>
        <el-button @click="regVisible = false">取消</el-button>
        <el-button type="primary" @click="register">登记</el-button>
      </template>
    </el-dialog>

    <!-- 详情抽屉 -->
    <el-drawer v-model="drawer" :title="`服务：${detail?.server_id ?? ''}`" size="520px">
      <template v-if="detail">
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="状态">{{ serverStatusLabel(detail) }}</el-descriptions-item>
          <el-descriptions-item label="地址">{{ detail.endpoint_url }}</el-descriptions-item>
          <el-descriptions-item label="协商结果">{{ detail.protocol_era || '—' }} {{ detail.protocol_version || '' }}（变更通知：{{ detail.supports_list_changed ? '支持' : '不支持' }}）</el-descriptions-item>
          <el-descriptions-item label="最近验证">{{ detail.last_verify_at || '—' }} {{ detail.last_verify_result ? failureCategoryLabel(detail.last_verify_result) : '' }}</el-descriptions-item>
          <el-descriptions-item label="凭证">
            全平台：{{ detail.credential.shared.configured ? `已设置（${detail.credential.shared.updated_at}）` : '未设置' }}；
            探测专用：{{ detail.credential.discovery.configured ? '已设置' : '未设置' }}；
            项目专属：{{ detail.credential.projects.map((p) => p.project_id).join('、') || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="覆盖限制">{{ JSON.stringify(detail.limits) }}</el-descriptions-item>
        </el-descriptions>

        <h4>凭证（只写不读）</h4>
        <el-form label-width="90px" size="small" @submit.prevent>
          <el-form-item label="范围">
            <el-radio-group v-model="credScope">
              <el-radio v-if="detail.credential_scope === 'shared'" value="shared">全平台共用</el-radio>
              <el-radio v-if="detail.credential_scope === 'project'" value="discovery">探测专用</el-radio>
              <el-radio v-if="detail.credential_scope === 'project'" value="project">项目专属</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="credScope === 'project'" label="项目">
            <el-select v-model="credProject" placeholder="选择项目"><el-option v-for="p in projects" :key="p" :value="p" :label="p" /></el-select>
          </el-form-item>
          <el-form-item label="凭证值">
            <input v-model="secret" type="password" autocomplete="new-password" class="secret-input" placeholder="提交后不会再显示" />
          </el-form-item>
          <el-button size="small" type="primary" :disabled="!secret" @click="saveCredential">保存 / 轮换</el-button>
          <el-button size="small" @click="clearCredential">清除</el-button>
          <p class="ib-muted meta">凭证主密钥未配置时，保存会被拒绝并提示“凭证主密钥未配置”。</p>
        </el-form>

        <h4>开放范围</h4>
        <el-checkbox v-model="openAll">开放给全部项目</el-checkbox>
        <el-select v-if="!openAll" v-model="openProjects" multiple collapse-tags placeholder="选择开放的项目" class="open-select">
          <el-option v-for="p in projects" :key="p" :value="p" :label="p" />
        </el-select>
        <el-button size="small" type="primary" @click="saveOpen">保存开放范围</el-button>
      </template>
    </el-drawer>

    <!-- 审核 -->
    <el-dialog v-model="reviewVisible" :title="`审核：${review?.display_name ?? ''}`" width="760px">
      <template v-if="review">
        <p class="ib-muted">以下内容均为服务方提供的不可信数据，仅作文本展示。</p>
        <el-descriptions :column="1" size="small" border>
          <el-descriptions-item label="描述（原文）"><pre class="pre">{{ review.observed?.description }}</pre></el-descriptions-item>
          <el-descriptions-item label="入参 schema"><pre class="pre">{{ JSON.stringify(review.observed?.input_schema, null, 2) }}</pre></el-descriptions-item>
          <el-descriptions-item :label="`服务方注解（${UNVERIFIED_ANNOTATION_NOTE}）`"><pre class="pre">{{ JSON.stringify(review.observed?.annotations, null, 2) }}</pre></el-descriptions-item>
          <el-descriptions-item v-if="review.diff.length" label="与已审核版本的差异">
            <el-tag v-for="d in review.diff" :key="d" type="warning" size="small">{{ d }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-alert v-if="review.suspect_tenant_params.length" type="warning" :closable="false" show-icon class="gap"
          :title="`必填参数 ${review.suspect_tenant_params.join('、')} 疑似租户 / 项目 / 用户标识：请屏蔽或为各项目固定其取值，或显式确认风险。`" />
        <el-form label-width="110px" size="small" class="gap">
          <el-form-item label="风险裁定">
            <el-radio-group v-model="reviewForm.risk">
              <el-radio value="read_only">只读</el-radio><el-radio value="side_effect">有副作用</el-radio><el-radio value="unknown">未知</el-radio>
            </el-radio-group>
            <span class="hint">有副作用 / 未知的工具默认不可授权，须按项目逐个放行</span>
          </el-form-item>
          <el-form-item label="屏蔽参数">
            <el-select v-model="reviewForm.hidden" multiple placeholder="LLM 不可见的参数">
              <el-option v-for="p in reviewProps" :key="p" :value="p" :label="p" />
            </el-select>
          </el-form-item>
          <el-form-item label="用途说明改写"><el-input v-model="reviewForm.llmDescription" type="textarea" :rows="2" maxlength="1000" placeholder="可选：自写的用途说明（LLM 看到的描述）" /></el-form-item>
          <el-form-item v-if="review.suspect_tenant_params.length" label="风险确认"><el-checkbox v-model="reviewForm.ack">我已确认上述疑似租户标识参数的风险</el-checkbox></el-form-item>
        </el-form>
      </template>
      <template #footer>
        <el-button @click="reviewVisible = false">关闭</el-button>
        <el-button v-if="review && ['pending_review', 'needs_rereview'].includes(review.state)" type="danger" plain @click="reject">驳回</el-button>
        <el-button v-if="review && ['pending_review', 'needs_rereview', 'disabled'].includes(review.state)" type="primary" @click="approve">通过审核</el-button>
      </template>
    </el-dialog>

    <!-- 固定入参 / 放行 -->
    <el-dialog v-model="bindVisible" :title="`固定入参 / 放行：${bindTool?.display_name ?? ''}`" width="560px">
      <el-form label-width="90px" size="small">
        <el-form-item label="项目"><el-select v-model="bindProject" placeholder="选择项目"><el-option v-for="p in projects" :key="p" :value="p" :label="p" /></el-select></el-form-item>
        <el-form-item label="固定入参"><el-input v-model="bindJson" type="textarea" :rows="3" placeholder='{"tenant_id": "…"}' /></el-form-item>
        <el-button size="small" type="primary" @click="saveBinding">保存固定入参</el-button>
        <el-form-item label="放行理由" class="gap"><el-input v-model="waiverReason" placeholder="有副作用 / 风险未知的工具须填写理由（必填）" /></el-form-item>
        <el-button size="small" type="warning" @click="grantWaiver">接受风险并放行</el-button>
        <el-button size="small" @click="revokeWaiver">撤销放行</el-button>
      </el-form>
    </el-dialog>

    <!-- 删除 -->
    <el-dialog v-model="delVisible" :title="`删除服务：${delTarget?.server_id ?? ''}`" width="480px">
      <p>{{ delInfo }}</p>
      <el-checkbox v-model="delForce">强制删除（先清理各项目定义文档中的相关授权，再删除服务）</el-checkbox>
      <p class="ib-muted">请输入标识名 <b>{{ delTarget?.server_id }}</b> 以确认：</p>
      <el-input v-model="delConfirm" size="small" />
      <template #footer>
        <el-button @click="delVisible = false">取消</el-button>
        <el-button type="danger" :disabled="delConfirm !== delTarget?.server_id" @click="doDelete">删除</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.load-error { margin-bottom: 12px; }
.filters { display: flex; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
.gov-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0 24px; }
.allow-add { display: flex; gap: 8px; margin-top: 8px; }
.meta { font-size: 12px; margin-left: 12px; }
.gap { margin-top: 12px; }
.hint { font-size: 12px; margin-left: 8px; color: var(--el-text-color-secondary); }
.pre { white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow: auto; margin: 0; font-size: 12px; }
.secret-input { width: 100%; padding: 4px 8px; border: 1px solid var(--el-border-color); border-radius: 4px; }
.open-select { display: block; margin: 8px 0; }
</style>
