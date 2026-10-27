/**
 * @module MOD-R26-18
 * @implements IFC-R26-180 Agent Builder 的 DTO 类型（与后端 `builder_views` 手写 DTO 一一对应）
 *
 * 独立成文件的原因：草案里有 `fallback_prompt` 字段名（兜底提示词，属 Builder 草案而非定义文档专家输入）；
 * 既有冒烟用例对 `client.ts` 全文断言“不得出现 fallback_prompt”（REV-20 对 ExpertSpecInput 的退役口径），
 * 把草案类型放在这里可保持该口径对 `client.ts` 成立，而不放宽任何断言。HTTP 仍只经 `client.ts`。
 */

export interface AgentDraftDto {
  name: string;
  cn_label: string;
  main_prompt: string;
  fallback_prompt: string;
  keywords: string[];
  exemplars: string[];
  is_data_expert: boolean;
  is_delegating: boolean;
  tool_names: string[];
  tool_params: [string, string | number | boolean][];
  knowledge_folder_ids: string[];
  max_steps: number;
  source: 'generated' | 'optimized' | 'cloned' | 'blank';
}

export interface AdaptationNoteDto {
  code: string;
  field: string;
  message: string;
}

export interface RubricResultDto {
  rubric_version: string;
  total: number;
  grade: 'fail' | 'pass' | 'excellent';
  dimension_scores: Record<string, number>;
  deductions: {
    dimension: string;
    check_id: string;
    field: string;
    points: number;
    evidence: string;
    /** A04：该扣分项来自 LLM 判定（其余为规则项）。 */
    llm_judged: boolean;
  }[];
  llm_check_ids: string[];
  coverage: 'full' | 'rules_only';
  cache_hit: boolean;
}

export interface FieldChangeDto {
  field: string;
  before: string | null;
  after: string | null;
  note: string;
}
