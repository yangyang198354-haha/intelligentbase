<script setup lang="ts">
/**
 * @module MOD-IB-24 / MOD-014
 * @implements IFC-IB-256（资料管理页入口）；云盘式目录管理见 `views/library/*`（MOD-014）
 *             IFC-IB-376（REV-18）视图为「**项目域**」：不含「知识库标识」输入，上传的 `kb_id`
 *             由服务端按已认证主体 `project_id` 推导（ADR-41）
 * @author software-developer
 *
 * 资料管理页（**项目域**视图）= 页面骨架：标题与项目域提示文案 + 云盘式资料浏览器
 * （`LibraryBrowser`：目录浏览 / 文件夹上传 / 新建 / 重命名 / 移动 / 更新 / 删除）。
 * 路由 `files`、`props: { client }` 契约不变；旧的"扁平列表 + 单文件上传"区块已被浏览器取代。
 */
import type { ApiClient } from '../api/client';
import LibraryBrowser from './library/LibraryBrowser.vue';

defineProps<{ client: ApiClient }>();
const emit = defineEmits<{ (e: 'unauthorized'): void }>();
</script>

<template>
  <section class="page">
    <h2>资料管理（项目域）</h2>
    <p class="hint">
      资料归属**当前项目**（项目域）。可上传文件或整个文件夹，也可新建文件夹、重命名、移动、更新与删除；
      上传后进入解析队列，状态自动刷新。
    </p>
    <LibraryBrowser :client="client" @unauthorized="emit('unauthorized')" />
  </section>
</template>

<style scoped>
.page {
  padding-top: 16px;
}
.hint {
  color: var(--ib-text-muted);
  font-size: 13px;
}
</style>
