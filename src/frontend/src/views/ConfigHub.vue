<script setup lang="ts">
/**
 * @module MOD-R26-21
 * 「可视化配置」导航入口的页面壳：默认进入“编排画布”（动态图 / Builder / 版本 / 试运行）；
 * 旧形态（v1）项目另保留“传统表单”页签（原 ConfigPage），首次在画布保存后项目即升级为 v2，该页签随之隐藏。
 */
import { onMounted, ref } from 'vue';

import type { ApiClient } from '../api/client';
import ConfigPage from './ConfigPage.vue';
import ConfigStudio from './ConfigStudio.vue';

const props = defineProps<{ client: ApiClient }>();
const tab = ref('studio');
const legacy = ref(false);

onMounted(async () => {
  try {
    legacy.value = (await props.client.configStatus()).legacy;
  } catch {
    legacy.value = false;
  }
});
</script>

<template>
  <el-tabs v-model="tab" class="hub">
    <el-tab-pane label="编排画布" name="studio">
      <ConfigStudio v-if="tab === 'studio'" :client="client" />
    </el-tab-pane>
    <el-tab-pane v-if="legacy" label="传统表单（旧形态项目）" name="classic" lazy>
      <ConfigPage :client="client" />
    </el-tab-pane>
  </el-tabs>
</template>
