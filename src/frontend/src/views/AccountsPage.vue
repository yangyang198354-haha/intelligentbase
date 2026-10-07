<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-329 账户管理页（列表 / 新建 / 停用 / 重置口令；**仅 admin**）
 *             IFC-IB-373（REV-18）账户**编辑**（`project_id` 重绑 / `username` / `status`）
 *             与**删除**（软删 + 二次确认 + 禁删 admin 与最后管理员）
 * @depends MOD-IB-24（app/env 单例）, MOD-IB-23（IFC-IB-321 / IFC-IB-373）
 * @author software-developer
 *
 * 账户管理（管理员）。
 *
 * ## 本页是**管理入口**，不是权限边界
 *
 * 每个动作都会被服务端重新判定（`_require_admin`：主体必须是**全局**账户且策略允许管理），
 * 非 admin 一律 403。前端隐藏入口 + 禁用按钮只是体验。**禁止**出现「前端已判断为管理员，
 * 因此可以跳过服务端校验」这类思路。
 *
 * ## 账户与项目 **N:1**（ADR-21-R1）
 *
 * 每个运维账户**恰绑定一个项目**（一个项目可有多个账户）。新建账户**必须**绑定项目；
 * 且目标项目须在**项目注册表**存在且 `active`，否则服务端 `422`（**顺序依赖：先建项目、
 * 后建账号**，REQ-FUNC-IB-45）。因此本页把「绑定项目」设为**下拉选择**（数据源 =
 * `GET /api/projects`），而不是自由文本 —— 从界面层避免「半配置账户」。
 *
 * ## 口令输入一次性，不回显
 *
 * 新建 / 重置口令都用 `type="password"`，提交后立即清空输入框；列表**从不**展示口令或
 * 其哈希（后端返回的 `AccountSummary` 里根本没有该字段）。编辑 / 删除**同样**不回显任何凭据。
 */
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';

import { client } from '../app/env';
import { ApiClientError, type AccountSummary, type ProjectSummary } from '../api/client';

const accounts = ref<AccountSummary[]>([]);
const projects = ref<ProjectSummary[]>([]);
const loading = ref(false);
const loadError = ref('');

const createVisible = ref(false);
const createSubmitting = ref(false);
const createForm = reactive({ username: '', password: '', project_id: '' });

const resetVisible = ref(false);
const resetSubmitting = ref(false);
const resetTarget = ref<AccountSummary | null>(null);
const resetPassword = ref('');

// REV-18（IFC-IB-373）：编辑与删除（软删）。
const editVisible = ref(false);
const editSubmitting = ref(false);
const editTarget = ref<AccountSummary | null>(null);
const editForm = reactive({ username: '', project_id: '', status: 'active' as 'active' | 'disabled' });

const deletingId = ref('');

const activeCount = computed(() => accounts.value.filter((a) => a.status === 'active').length);

function messageOf(err: unknown, fallback: string): string {
  if (err instanceof ApiClientError) {
    if (err.status === 403) return '当前账户无权管理账户（仅管理员可操作）。';
    if (err.status === 409) return err.message || '操作被拒绝（可能是用户名冲突或管理员保护）。';
    if (err.status === 422) return err.message || '目标项目不存在或未启用，请先创建项目。';
    return err.message || fallback;
  }
  return '无法连接服务，请确认服务已启动。';
}

async function load(): Promise<void> {
  loading.value = true;
  loadError.value = '';
  try {
    const [envelope, projectList] = await Promise.all([
      client.listAccounts(),
      client.listProjects().catch(() => [] as ProjectSummary[]),
    ]);
    accounts.value = envelope.items;
    // 账户可绑定的项目 = 注册表**活动**项目（admin 可见全部；用于顺序依赖的下拉）。
    projects.value = projectList;
  } catch (err) {
    loadError.value = messageOf(err, '加载账户列表失败。');
  } finally {
    loading.value = false;
  }
}

function openCreate(): void {
  createForm.username = '';
  createForm.password = '';
  createForm.project_id = projects.value[0]?.project_id ?? '';
  createVisible.value = true;
}

async function submitCreate(): Promise<void> {
  if (!createForm.username.trim() || !createForm.password || !createForm.project_id.trim()) {
    ElMessage.warning('用户名、口令、绑定项目均为必填');
    return;
  }
  createSubmitting.value = true;
  try {
    await client.createAccount({
      username: createForm.username.trim(),
      password: createForm.password,
      project_id: createForm.project_id.trim(),
    });
    createForm.password = ''; // 立即清空，口令不留驻内存
    createVisible.value = false;
    ElMessage.success('账户已创建；首次登录后需修改口令');
    await load();
  } catch (err) {
    ElMessage.error(messageOf(err, '创建账户失败。'));
  } finally {
    createSubmitting.value = false;
  }
}

async function disableAccount(row: AccountSummary): Promise<void> {
  try {
    await ElMessageBox.confirm(
      `停用后，${row.username} 的全部会话将立即失效，且无法再登录。确定继续？`,
      '停用账户',
      { confirmButtonText: '停用', cancelButtonText: '取消', type: 'warning' },
    );
  } catch {
    return; // 用户取消
  }
  try {
    await client.disableAccount(row.user_id);
    ElMessage.success('账户已停用');
    await load();
  } catch (err) {
    ElMessage.error(messageOf(err, '停用账户失败。'));
  }
}

function openReset(row: AccountSummary): void {
  resetTarget.value = row;
  resetPassword.value = '';
  resetVisible.value = true;
}

async function submitReset(): Promise<void> {
  const target = resetTarget.value;
  if (!target || !resetPassword.value) {
    ElMessage.warning('请输入新口令');
    return;
  }
  resetSubmitting.value = true;
  try {
    await client.resetAccountPassword(target.user_id, resetPassword.value);
    resetPassword.value = '';
    resetVisible.value = false;
    ElMessage.success('口令已重置；该账户下次登录须修改口令');
    await load();
  } catch (err) {
    ElMessage.error(messageOf(err, '重置口令失败。'));
  } finally {
    resetSubmitting.value = false;
  }
}

// ---- REV-18（IFC-IB-373）：编辑（project_id 重绑 / username / status） ---- //

function openEdit(row: AccountSummary): void {
  editTarget.value = row;
  editForm.username = row.username;
  editForm.project_id = row.project_id ?? '';
  editForm.status = row.status;
  editVisible.value = true;
}

async function submitEdit(): Promise<void> {
  const target = editTarget.value;
  if (!target) return;
  const payload: { username?: string; project_id?: string; status?: 'active' | 'disabled' } = {};
  if (editForm.username.trim() && editForm.username.trim() !== target.username) {
    payload.username = editForm.username.trim();
  }
  if (editForm.project_id && editForm.project_id !== target.project_id) {
    payload.project_id = editForm.project_id;
  }
  if (editForm.status !== target.status) {
    payload.status = editForm.status;
  }
  if (Object.keys(payload).length === 0) {
    ElMessage.info('没有需要保存的修改');
    return;
  }
  editSubmitting.value = true;
  try {
    await client.updateAccount(target.user_id, payload);
    editVisible.value = false;
    ElMessage.success('账户已更新');
    await load();
  } catch (err) {
    ElMessage.error(messageOf(err, '更新账户失败。'));
  } finally {
    editSubmitting.value = false;
  }
}

// ---- REV-18（IFC-IB-373）：删除（软删 + 二次确认 + 禁删 admin） ---- //

async function deleteAccount(row: AccountSummary): Promise<void> {
  if (row.role === 'admin') {
    ElMessage.warning('管理员账户不可删除（禁止删除 admin 或最后一个有效管理员）。');
    return;
  }
  // 二次确认：输入用户名与目标一致（服务端同样校验 confirm_username，否则 400）。
  try {
    await ElMessageBox.confirm(
      `确定删除账户「${row.username}」？该操作为**软删**（停用，可恢复），并立即撤销其全部会话。`,
      '删除账户',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    );
  } catch {
    return; // 用户取消
  }
  deletingId.value = row.user_id;
  try {
    await client.deleteAccount(row.user_id, row.username);
    ElMessage.success('账户已删除（停用）');
    await load();
  } catch (err) {
    ElMessage.error(messageOf(err, '删除账户失败。'));
  } finally {
    deletingId.value = '';
  }
}

onMounted(load);
</script>

<template>
  <section class="accounts">
    <div class="head">
      <div>
        <h2 class="ib-page-title">账户管理</h2>
        <p class="ib-page-sub">
          共 {{ accounts.length }} 个账户（启用 {{ activeCount }} 个）。每个运维账户绑定一个项目（一个项目可有多个账户）；管理员为全局账户。
        </p>
      </div>
      <el-button type="primary" @click="openCreate">新建账户</el-button>
    </div>

    <el-alert
      v-if="loadError"
      type="error"
      :closable="false"
      show-icon
      :title="loadError"
      class="load-error"
    />

    <el-table v-loading="loading" :data="accounts" class="ib-card" empty-text="暂无账户">
      <el-table-column prop="username" label="用户名" min-width="140" />
      <el-table-column label="角色" width="110">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'warning' : 'info'" disable-transitions>
            {{ row.role === 'admin' ? '管理员' : '运维' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="绑定项目" min-width="140">
        <template #default="{ row }">
          <span v-if="row.project_id">{{ row.project_id }}</span>
          <span v-else class="ib-muted">全部项目</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'" disable-transitions>
            {{ row.status === 'active' ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="口令状态" width="130">
        <template #default="{ row }">
          <span v-if="row.must_change_password" class="warn">待首次修改</span>
          <span v-else class="ib-muted">正常</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button link type="primary" @click="openReset(row)">重置口令</el-button>
          <el-button
            link
            type="warning"
            :disabled="row.status !== 'active' || row.role === 'admin'"
            @click="disableAccount(row)"
          >
            停用
          </el-button>
          <el-button
            link
            type="danger"
            :disabled="row.role === 'admin' || deletingId === row.user_id"
            @click="deleteAccount(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="createVisible" title="新建账户" width="440px">
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="createForm.username" autocomplete="off" placeholder="例如 zhangsan" />
        </el-form-item>
        <el-form-item label="初始口令">
          <el-input
            v-model="createForm.password"
            type="password"
            show-password
            autocomplete="new-password"
            placeholder="至少 8 位，含大小写 / 数字 / 符号中 2 类"
          />
        </el-form-item>
        <el-form-item label="绑定项目">
          <el-select v-model="createForm.project_id" placeholder="选择项目" style="width: 100%">
            <el-option
              v-for="p in projects"
              :key="p.project_id"
              :label="`${p.name}（${p.project_id}）`"
              :value="p.project_id"
            />
          </el-select>
        </el-form-item>
        <p class="ib-muted form-hint">
          目标项目须已存在且启用（**先建项目、后建账号**）；新账户首次登录必须修改口令，
          在修改完成前，除改密页外的功能均不可用。
        </p>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createSubmitting" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resetVisible" title="重置口令" width="420px">
      <p class="ib-muted">
        为 <strong>{{ resetTarget?.username }}</strong> 设置新口令。重置后该账户的全部会话将失效，
        且下次登录须再次修改口令。
      </p>
      <el-input
        v-model="resetPassword"
        type="password"
        show-password
        autocomplete="new-password"
        placeholder="新口令（至少 8 位）"
      />
      <template #footer>
        <el-button @click="resetVisible = false">取消</el-button>
        <el-button type="primary" :loading="resetSubmitting" @click="submitReset">确认重置</el-button>
      </template>
    </el-dialog>

    <!-- REV-18（IFC-IB-373）：编辑账户（project_id 重绑 / username / status；不回显任何凭据） -->
    <el-dialog v-model="editVisible" title="编辑账户" width="440px">
      <el-form label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" autocomplete="off" />
        </el-form-item>
        <el-form-item label="绑定项目">
          <el-select v-model="editForm.project_id" placeholder="选择项目" style="width: 100%">
            <el-option
              v-for="p in projects"
              :key="p.project_id"
              :label="`${p.name}（${p.project_id}）`"
              :value="p.project_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width: 100%">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </el-form-item>
        <p class="ib-muted form-hint">
          重绑项目时，目标项目须存在且启用，否则服务端拒绝。
        </p>
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

.warn {
  color: var(--ib-warning);
}

.form-hint {
  font-size: 12px;
  margin: 0;
}
</style>
