<script setup lang="ts">
/** @module MOD-R26-20  自评结果：总分 / 等级 / 五维得分 / 扣分清单（字段 + 检查项 + 扣分 + 证据）/ 覆盖度与缓存标记。 */
import type { RubricResultDto } from '../../api/builderTypes';

defineProps<{ result: RubricResultDto }>();
const GRADE: Record<string, string> = { fail: '不合格', pass: '合格', excellent: '优秀' };
const DIM: Record<string, string> = { completeness: '完整性与格式', adaptation: '项目适配度', routing: '路由质量', prompt: '提示词质量', safety: '安全与约束' };
</script>

<template>
  <div class="eval">
    <p><strong>{{ result.total }} 分</strong> · {{ GRADE[result.grade] }}
      <el-tag v-if="result.coverage === 'rules_only'" size="small" type="info">仅规则项（LLM 判定项未计入）</el-tag>
      <el-tag v-if="result.cache_hit" size="small">LLM 判定项来自缓存</el-tag></p>
    <ul class="dims"><li v-for="(v, k) in result.dimension_scores" :key="k">{{ DIM[k] ?? k }}：{{ v }}</li></ul>
    <p class="hint">标有“LLM 判定”的扣分项由模型判定（占 6 分），其余为规则项（可复现）。</p>
    <ul>
      <li v-for="(d, i) in result.deductions" :key="i">
        [{{ d.field }}] {{ d.check_id }} −{{ d.points }}：{{ d.evidence }}
        <el-tag v-if="d.llm_judged" size="small" type="warning">LLM 判定</el-tag>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.dims { display: flex; gap: 14px; flex-wrap: wrap; padding-left: 0; list-style: none; }
.hint { color: var(--el-text-color-secondary); font-size: 12px; }
</style>
