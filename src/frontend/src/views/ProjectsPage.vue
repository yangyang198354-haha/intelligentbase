<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-376（REV-18）项目管理页（项目 CRUD + 软删二次确认；**仅 admin**）
 * @depends MOD-IB-24（app/env 单例）, MOD-IB-23（IFC-IB-372）
 * @author software-developer
 *
 * 项目管理（管理员）——「系统管理 → 项目管理」。
 *
 * ## 本页是**管理入口**，不是权限边界
 *
 * 每个动作都会被服务端重新判定（`_require_admin`：主体必须是**全局**账户且策略允许管理），
 * 非 admin 一律 403。前端隐藏入口 + 禁用按钮只是体验（ADR-42：UI 分组不是权限机制）。
 *
 * ## 删除是**软删**（`status="disabled"`）
 *
 * 软删**不物理级联**（OOS-19）：数据保留、可恢复。删除须**二次确认**（输入项目标识一致，
 * 服务端同样校验 `confirm_project_id`，否则 400）。
 *
 * ## 列表数据源 = `GET /api/projects`（注册表活动项目）
 *
 * 该端点由 REV-18 切换为**项目注册表**数据源，返回 `ProjectSummary(project_id, name,
 * is_current)`。**软删后的项目不再出现在活动列表**（`list_active()` 只回 `active`）——
 * 与「停用即从选择器消失」的口径一致。
 */
import { onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

import { client } from '../app/env';
import { ApiClientError, type ProjectSummary } from '../api/client';

const projects = ref<ProjectSummary[]>([]);
const loading = ref(false);
const loadError = ref('');

const createVisible = ref(false);
const createSubmitting = ref(false);
const createForm = reactive({ project_id: '', name: '' });

const editVisible = ref(false);
const editSubmitting = ref(false);
const editTarget = ref<ProjectSummary | null>(null);
const editName = ref('');

const deletingId = ref('');

function messageOf(err: unknown, fallback: string): string {
  if (err instanceof ApiClientError) {
    if (err.status === 403) return '当前账户无权管理项目（仅管理员可操作）。';
    if (err.status === 409) return '该项目标识已存在，请换一个。';
    return err.message || fallback;
  }
  return '无法连接服务，请确认服务已启动。';
}

async function load(): Promise<void> {
  loading.value = true;
  loadError.value = '';
  try {
    projects.value = await client.listProjects();
  } catch (err) {
    loadError.value = messageOf(err, '加载项目列表失败。');
  } finally {
    loading.value = false;
  }
}

function openCreate(): void {
  createForm.project_id = '';
  createForm.name = '';
  createVisible.value = true;
}

async function submitCreate(): Promise<void> {
  if (!createForm.project_id.trim() || !createForm.name.trim()) {
    ElMessage.warning('项目标识与名称为必填');
    return;
  }
  createSubmitting.value = true;
  try {
    await client.createProject(createForm.project_id.trim(), createForm.name.trim());
    createVisible.value = false;
    ElMessage.success('项目已创建（可继续为该项目创建运维账户）');
    await load();
  } catch (err) {
    ElMessage.error(messageOf(err, '创建项目失败。'));
  } finally {
    createSubmitting.value = false;
  }
}

function openEdit(row: ProjectSummary): void {
  editTarget.value = row;
  editName.value = row.name;
  editVisible.value = true;
}

async function submitEdit(): Promise<void> {
  const target = editTarget.value;
  if (!target) return;
  const name = editName.value.trim();
  if (!name) {
    ElMessage.warning('项目名称不能为空');
    return;
  }
  if (name === target.name) {
    ElMessage.info('没有需要保存的修改');
    return;
  }
  editSubmitting.value = true;
  try {
    await client.updateProject(target.project_id, { name });
    editVisible.value = false;
    ElMessage.success('项目已更新');
    await load();
  } catch (err) {
    ElMessage.error(messageOf(err, '更新项目失败。'));
  } finally {
    editSubmitting.value = false;
  }
}

async function deleteProject(row: ProjectSummary): Promise<void> {
  // 二次确认：输入项目标识与目标一致（服务端同样校验 confirm_project_id，否则 400）。
  try {
    const { value } = await ElMessageBox.prompt(
      `删除为**软删**（停用，数据保留、可恢复）。请输入项目标识「${row.project_id}」以确认：`,
      '停用 / 删除项目',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
    );
    if ((value ?? '').trim() !== row.project_id) {
      ElMessage.warning('确认标识不一致，已取消');
      return;
    }
  } catch {
    return; // 用户取消
  }
  deletingId.value = row.project_id;
  try {
    await client.deleteProject(row.project_id, row.project_id);
    ElMessage.success('项目已删除（停用）');
    await load();
  } catch (err) {
    ElMessage.error(messageOf(err, '删除项目失败。'));
  } finally {
    deletingId.value = '';
  }
}

onMounted(load);
</script>

<template>
  <section class="projects">
    <div class="head">
      <div>
        <h2 class="ib-page-title">项目管理</h2>
        <p class="ib-page-sub">
          共 {{ projects.length }} 个活动项目。**先建项目、后建账号**（账户须绑定已启用的项目）。
        </p>
      </div>
      <el-button type="primary" @click="openCreate">新建项目</el-button>
    </div>

    <el-alert
      v-if="loadError"
      type="error"
      :closable="false"
      show-icon
      :title="loadError"
      class="load-error"
    />

    <el-table v-loading="loading" :data="projects" class="ib-card" empty-text="暂无项目">
      <el-table-column prop="project_id" label="项目标识" min-width="160" />
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column label="当前项目" width="110">
        <template #default="{ row }">
          <el-tag v-if="row.is_current" type="success" disable-transitions>当前</el-tag>
          <span v-else class="ib-muted">—</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button
            link
            type="danger"
            :disabled="deletingId === row.project_id"
            @click="deleteProject(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="createVisible" title="新建项目" width="440px">
      <el-form label-position="top">
        <el-form-item label="项目标识">
          <el-input v-model="createForm.project_id" placeholder="例如 p_gamma（字母 / 数字 / _ / -）" />
        </el-form-item>
        <el-form-item label="项目名称">
          <el-input v-model="createForm.name" placeholder="例如 伽马项目" />
        </el-form-item>
        <p class="ib-muted form-hint">
          新建后，可在「账户管理」为该项目创建运维账户。项目标识用于 collection 前缀与
          项目域资料归属，请使用稳定、可读的短标识。
        </p>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createSubmitting" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="editVisible" title="编辑项目" width="440px">
      <el-form label-position="top">
        <el-form-item label="项目标识">
          <el-input :model-value="editTarget?.project_id ?? ''" disabled />
        </el-form-item>
        <el-form-item label="名称">
          <el-input v-model="editName" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="editSubmitting" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.load-error {
  margin-bottom: 12px;
}

.form-hint {
  font-size: 12px;
  margin: 0;
}
</style>
