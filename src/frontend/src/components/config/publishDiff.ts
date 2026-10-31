/**
 * @module MOD-R27-03
 * @implements IFC-R27-008 差异清单一行文本；node_* 三类带中文节点类型，其余 kind 与 R26 现状逐字相同。
 */

import type { DiffItemDto, NodeKind } from '../../api/client';
import { KIND_LABEL as NODE_KIND_LABEL } from './graphModel';

const DIFF_KIND_LABEL: Record<string, string> = {
  agent_added: '新增 agent', agent_removed: '删除 agent', agent_disabled: '停用 agent', agent_enabled: '启用 agent',
  agent_field: '修改 agent 字段', prompt: '修改 提示词', tool_grant: '修改 工具授权', tool_param: '修改 工具参数',
  knowledge_scope: '修改 知识范围', route_param: '修改 路由参数', node_added: '新增节点', node_removed: '删除节点',
  node_changed: '修改节点', edge_added: '新增边', edge_removed: '删除边', edge_changed: '修改边', layout: '调整布局',
};
const NODE_ACTION: Record<string, string> = { node_added: '新增', node_removed: '删除', node_changed: '修改' };

export function formatDiffLine(i: DiffItemDto): string {
  const action = NODE_ACTION[i.kind];
  if (action) {
    const code = i.before ?? i.after;
    if (code) {
      const cn = (NODE_KIND_LABEL as Record<string, string>)[code as NodeKind] ?? code;
      return `${action} ${cn}节点：${i.object_id}`;
    }
  }
  const kind = DIFF_KIND_LABEL[i.kind] ?? i.kind;
  const delta = i.before !== null || i.after !== null ? `：${i.before ?? '∅'} → ${i.after ?? '∅'}` : '';
  return `${kind}：${i.object_id}${i.field ? ` · ${i.field}` : ''}${delta}`;
}
