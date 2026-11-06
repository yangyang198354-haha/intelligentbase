// MOD-R29-21：MCP 外部工具的统一文案词表（纯 TS，仅 import type；供管理页 / 配置页 / 审计页共用，M-PM-011）。
import type { McpAdminState, McpRisk, McpServerDto, McpToolState } from '../api/client';

/** 工具状态词表。 */
const TOOL_STATE: Record<McpToolState, string> = {
  pending_review: '待审核',
  enabled: '已启用',
  disabled: '已禁用',
  needs_rereview: '待复审',
  offline: '已下线',
  excluded: '已排除',
};

const RISK: Record<McpRisk, string> = {
  read_only: '只读',
  side_effect: '有副作用',
  unknown: '未知',
};

/** 失效原因词表（McpDenyReason → 展示）；未登记的原因回落为通用说明。 */
const INVALID_REASON: Record<string, string> = {
  tool_needs_rereview: '工具待复审',
  tool_not_enabled: '工具已禁用',
  tool_offline: '工具已下线',
  tool_missing: '工具不存在',
  server_disabled: 'Server 已停用',
  server_unverified: 'Server 未启用',
  server_not_open: 'Server 未对本项目开放',
  risk_not_waived: '放行已撤销',
  tool_stale: '指纹不符（等待刷新）',
  credential_missing: '凭证未配置',
  secret_key_missing: '凭证主密钥未配置',
  server_down: 'Server 不可用',
};

/** 连接验证失败类别词表。 */
const FAILURE: Record<string, string> = {
  ok: '验证通过',
  unreachable: '无法连接',
  timeout: '连接超时',
  auth_failed: '鉴权失败',
  protocol_incompatible: '协议版本不兼容',
  protocol_error: '协议响应无效',
  address_blocked: '地址被拒',
  credential_missing: '凭证未配置',
  secret_key_missing: '凭证主密钥未配置',
  no_tools_capability: '服务方未声明工具能力',
};

/** 创建 / 变更错误码（后端 error.code）的统一文案。 */
const API_ERROR: Record<string, string> = {
  transport_not_supported: '传输类型不受支持',
  plain_http_public_forbidden: '公网目标禁止明文 http',
  address_blocked: '地址被拒',
  secret_key_missing: '凭证主密钥未配置',
  server_id_invalid: '标识名不合法',
  server_id_exists: '标识名已存在',
  stale_update: '数据已被他处修改，请刷新后重试',
  verification_failed: '连接验证未通过',
  fingerprint_changed: '工具内容已变化，请重新查看后审核',
  needs_review: '工具需先通过审核',
  server_in_use: '该服务仍被项目授权引用',
  cleanup_failed: '清理授权失败，服务已停用但未删除',
  tenant_params_unacked: '存在疑似租户 / 项目 / 用户标识的必填参数，须显式确认',
  mcp_disabled: '外部工具功能未启用',
};

/** 传输类型下拉的唯一取值（AC-001-06：不得出现 stdio）。 */
export const TRANSPORT_OPTIONS: readonly string[] = ['streamable_http'];

/** Server 状态：未启用 / 可用 / 不可用 / 已停用 / 有待复审工具。 */
export function serverStatusLabel(dto: Pick<McpServerDto, 'admin_state' | 'health' | 'tool_counts'>): string {
  const state: McpAdminState = dto.admin_state;
  if (state === 'registered') return '未启用';
  if (state === 'disabled') return '已停用';
  if (dto.health === 'down') return '不可用';
  if ((dto.tool_counts?.needs_rereview ?? 0) > 0) return '有待复审工具';
  return '可用';
}

export function toolStateLabel(state: McpToolState | string): string {
  return TOOL_STATE[state as McpToolState] ?? String(state);
}

export function riskLabel(risk: McpRisk | string): string {
  return RISK[risk as McpRisk] ?? String(risk);
}

export function invalidReasonLabel(reason: string | null | undefined): string {
  if (!reason) return '';
  return INVALID_REASON[reason] ?? '当前不可用';
}

export function failureCategoryLabel(category: string): string {
  return FAILURE[category] ?? '验证未通过';
}

export function apiErrorLabel(code: string, fallback = '操作失败'): string {
  return API_ERROR[code] ?? fallback;
}

/** 副作用 / 未知风险的外部工具默认不可勾选，须管理员放行。 */
export const WAIVER_HINT = '需管理员放行';
export const UNVERIFIED_ANNOTATION_NOTE = '服务方自报，未经核实';
