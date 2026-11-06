// MOD-R29-23：配置页"外部工具"分组的纯函数（把勾选写入草稿 tool_grants、计算失效标注、风险置灰规则）。仅 import type。
import type { DefinitionDocumentV2, ExternalToolDto, McpGrantStatusDto } from '../api/client';

export const EXTERNAL_PREFIX = 'mcp__';

export function isExternalName(name: string): boolean {
  return name.startsWith(EXTERNAL_PREFIX);
}

/** 按 Server 分组（保持目录顺序）。 */
export function groupByServer(tools: ExternalToolDto[]): { server_id: string; tools: ExternalToolDto[] }[] {
  const out: { server_id: string; tools: ExternalToolDto[] }[] = [];
  for (const t of tools) {
    let g = out.find((x) => x.server_id === t.server_id);
    if (!g) {
      g = { server_id: t.server_id, tools: [] };
      out.push(g);
    }
    g.tools.push(t);
  }
  return out;
}

/** 有副作用 / 未知且未放行 ⇒ 置灰（已勾选者仍可取消）。 */
export function isGreyed(tool: ExternalToolDto, alreadyGranted: boolean): boolean {
  return !tool.grantable && !alreadyGranted;
}

/** 文案由调用方注入（本文件不 import 词表，保持可被 node:test 单文件转译加载）。 */
export function greyHint(tool: ExternalToolDto, label: (risk: string) => string, waiverHint: string): string {
  return tool.grantable ? '' : `${label(tool.risk)}风险：${waiverHint}`;
}

/** 展示名：`display_name`（括号注明注册名）。 */
export function toolTitle(tool: Pick<ExternalToolDto, 'display_name' | 'local_name'>): string {
  return `${tool.display_name}（${tool.local_name}）`;
}

/** 某 agent 已授权但当前失效的外部工具（带原因徽标文案）。 */
export function invalidBadges(
  expert: string,
  status: McpGrantStatusDto[] | undefined,
  label: (reason: string | null | undefined) => string,
): { local_name: string; label: string }[] {
  return (status ?? [])
    .filter((s) => s.expert_name === expert && !s.valid)
    .map((s) => ({ local_name: s.local_name, label: label(s.reason) }));
}

/** 勾选 / 取消外部工具：返回新的文档副本（不新增保存通道，沿用预检 → 差异清单 → 发布）。 */
export function toggleExternalGrant(doc: DefinitionDocumentV2, expert: string, tool: string, on: boolean): DefinitionDocumentV2 {
  const copy = JSON.parse(JSON.stringify(doc)) as DefinitionDocumentV2;
  let g = copy.tool_grants.find((x) => x.expert_name === expert);
  if (!g) {
    g = { expert_name: expert, tool_names: [], param_values: [] };
    copy.tool_grants.push(g);
  }
  g.tool_names = on ? [...new Set([...g.tool_names, tool])] : g.tool_names.filter((t) => t !== tool);
  if (!on) g.param_values = (g.param_values ?? []).filter((p) => !p.name.startsWith(`${tool}.`));
  return copy;
}

/** 仅渲染 mcp_timeout_s / mcp_max_calls_per_turn 两个限制参数。 */
export function limitSpecs(tool: ExternalToolDto) {
  return tool.param_specs.filter((s) => s.name.endsWith('.mcp_timeout_s') || s.name.endsWith('.mcp_max_calls_per_turn'));
}
