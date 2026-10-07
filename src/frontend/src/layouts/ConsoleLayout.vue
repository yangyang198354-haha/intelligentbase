<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-328 运维控制台外壳（左侧导航 + 右侧内容；深浅色；中文优先）
 *             IFC-IB-335（R14）项目选择器（admin 可选 / ops 只读）+ 切换项目重置视图态
 *             IFC-IB-376（REV-18）父级「系统管理」+ 三子项导航（账户 / 项目 / LLM Key）
 * @depends MOD-IB-24（app/env 会话单例, stores/theme）
 * @author software-developer
 *
 * 运维控制台外壳。
 *
 * ## 结构
 *
 * ```
 * ┌───────────┬──────────────────────────────┐
 * │  品牌     │  顶栏：页面标题 · 主题 · 用户 │
 * │  导航     ├──────────────────────────────┤
 * │  · 问答   │                              │
 * │  · 资料   │      <router-view>           │
 * │  · 重建   │                              │
 * │  · 配置   │                              │
 * │  系统管理*│                              │
 * │   · 账户  │                              │
 * │   · 项目  │                              │
 * │   · LLM   │                              │
 * └───────────┴──────────────────────────────┘
 * ```
 *
 * `*` 「系统管理」分组（含账户 / 项目 / LLM Key 三子项）**仅 admin** 可见（REV-18
 * IFC-IB-376 / ADR-42）。隐藏入口不是安全措施（服务端对非 admin 一律 403），
 * 但它避免了「点了才知道不能用」的体验问题。**授权与导航解耦**：UI 分组不作为权限机制。
 *
 * ## 导航项由路由表驱动
 *
 * 菜单项从 `router` 的子路由中筛出（而不是在本文件另写一份列表）—— 两份列表迟早漂移，
 * 表现为「路由存在但菜单里没有」，属于最容易被忽略的一类缺陷。
 */
import { computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessageBox } from 'element-plus';

import { projectContext, session } from '../app/env';
import { useTheme } from '../stores/theme';

const route = useRoute();
const router = useRouter();
const { isDark, toggleTheme } = useTheme();

type NavItem = { name: string; path: string; title: string; adminOnly: boolean };

/**
 * 期望的导航顺序（路由表注册顺序即期望顺序，但 `getRoutes()` 不保证保序）。
 *
 * REV-18（IFC-IB-376 / ADR-42）：既有 `accounts` 迁入父级「系统管理」分组，
 * 与新增 `projects` / `llm-key` 并列；顶级项为 `chat / files / rebuild / config`
 * （**资料管理**保持独立顶级，视图改为「项目域」）。
 */
const TOP_ORDER = ['chat', 'files', 'rebuild', 'config'];
const SYSTEM_ORDER = ['accounts', 'projects', 'llm-key'];

/** 从路由表派生**全部**带标题的导航项（唯一真源 = 路由表）。 */
const NAV: NavItem[] = (router.getRoutes() ?? [])
  .filter((r) => typeof r.name === 'string' && r.meta?.title && r.path !== '/' && r.name !== 'login' && r.name !== 'change-password')
  .map((r) => ({
    name: String(r.name),
    path: r.path,
    title: String(r.meta.title),
    adminOnly: r.meta.requiresAdmin === true,
  }));

/** 顶级导航（不含系统管理三子项）。 */
const topNav = computed(() =>
  NAV.filter((item) => TOP_ORDER.includes(item.name)).sort(
    (a, b) => TOP_ORDER.indexOf(a.name) - TOP_ORDER.indexOf(b.name),
  ),
);

/** 「系统管理」分组的三子项（REV-18 三分 IA）。 */
const systemNav = computed(() =>
  NAV.filter((item) => SYSTEM_ORDER.includes(item.name)).sort(
    (a, b) => SYSTEM_ORDER.indexOf(a.name) - SYSTEM_ORDER.indexOf(b.name),
  ),
);

const visibleTopNav = computed(() => topNav.value.filter((item) => !item.adminOnly || session.isAdmin.value));
/** 系统管理分组**仅 admin 可见**（服务端对非 admin 一律 403；此处只是不摆无用入口）。 */
const visibleSystemNav = computed(() => systemNav.value.filter((item) => !item.adminOnly || session.isAdmin.value));

const activeName = computed(() => String(route.name ?? ''));

const pageTitle = computed(() => {
  const item = NAV.find((n) => n.name === activeName.value);
  return item?.title ?? '';
});

const roleLabel = computed(() => (session.isAdmin.value ? '管理员' : '运维'));

/**
 * ops 的只读项目标签（其绑定项目不可切换）：优先显示服务端返回的项目名，
 * 列表尚未就绪时回退为账户自身 `project_id`。
 */
const opsProjectLabel = computed(
  () => projectContext.currentName.value || session.state.user?.project_id || '未绑定项目',
);

/**
 * 切换项目后**重置项目内视图态**的机制（IFC-IB-335）：对 `<router-view>` 施加 `:key`。
 *
 * 键变化 ⇒ 现有页面组件被销毁重建 ⇒ 组件内状态（会话历史 / 文件列表 / 可视化草稿）
 * 一并丢弃，从而**不会**出现「旧项目数据显示在新项目下」的串项显示。
 * 键不含路由（切换页签时保持不变，不影响正常导航）。
 */
const viewKey = computed(() => projectContext.state.current ?? 'none');

/** admin 选择项目（仅 admin 生效；store 对 ops 为 no-op）。 */
function onSelectProject(value: unknown): void {
  projectContext.select(String(value ?? ''));
}

/**
 * 拉取可见项目并确定「当前项目」（IFC-IB-335）。
 *
 * 触发点 = 会话用户就绪时（`bootstrap` / `login` 成功后用户必已就绪；`immediate` 覆盖
 * 首次挂载，`watch` 覆盖同页内身份变化）。`load` 失败 ⇒ `current` 保持空（不注入头）。
 */
async function ensureProjectContext(): Promise<void> {
  const user = session.state.user;
  if (!user) return;
  await projectContext.load(user.role, user.project_id ?? null);
}

watch(
  () => session.state.user?.user_id ?? '',
  () => {
    void ensureProjectContext();
  },
  { immediate: true },
);

async function confirmLogout(): Promise<void> {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出登录', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    });
  } catch {
    return; // 用户取消
  }
  await session.logout();
  projectContext.clear(); // 项目上下文不与会话一同残留（回到未选项目的 fail-closed 态）
  await router.replace({ name: 'login' });
}
</script>

<template>
  <div class="console">
    <aside class="sidebar">
      <div class="brand">
        <div class="mark" aria-hidden="true">知</div>
        <span class="brand-name">企业知识库</span>
      </div>

      <nav class="nav" aria-label="主导航">
        <button
          v-for="item in visibleTopNav"
          :key="item.name"
          type="button"
          class="nav-item"
          :class="{ active: activeName === item.name }"
          @click="router.push({ name: item.name })"
        >
          {{ item.title }}
        </button>

        <!-- REV-18（IFC-IB-376 / ADR-42）：父级「系统管理」+ 三子项（仅 admin 可见）。 -->
        <template v-if="visibleSystemNav.length">
          <div class="nav-group-label">系统管理</div>
          <button
            v-for="item in visibleSystemNav"
            :key="item.name"
            type="button"
            class="nav-item nav-item-child"
            :class="{ active: activeName === item.name }"
            @click="router.push({ name: item.name })"
          >
            {{ item.title }}
          </button>
        </template>
      </nav>

      <div class="sidebar-foot ib-muted">
        <span>{{ roleLabel }}</span>
        <span class="dot" aria-hidden="true">·</span>
        <!-- R14（IFC-IB-335）：admin 可显式选择「当前项目」；ops 显示只读的自身项目。 -->
        <el-select
          v-if="session.isAdmin.value"
          class="project-select"
          size="small"
          placeholder="选择项目"
          :model-value="projectContext.state.current ?? ''"
          @change="onSelectProject"
        >
          <el-option
            v-for="p in projectContext.state.available"
            :key="p.project_id"
            :label="p.name"
            :value="p.project_id"
          />
        </el-select>
        <span v-else class="ellipsis" :title="opsProjectLabel">{{ opsProjectLabel }}</span>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <h1 class="ib-page-title">{{ pageTitle }}</h1>
        <div class="topbar-actions">
          <el-button text :title="isDark ? '切换到浅色' : '切换到深色'" @click="toggleTheme">
            {{ isDark ? '浅色' : '深色' }}
          </el-button>
          <el-dropdown trigger="click">
            <span class="user">
              {{ session.displayName.value }}
              <span class="caret" aria-hidden="true">▾</span>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push({ name: 'change-password' })">
                  修改口令
                </el-dropdown-item>
                <el-dropdown-item divided @click="confirmLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <!-- R14：以当前项目为键，切换项目即重挂载现有页面（重置项目内视图态，防串项）。 -->
        <router-view :key="viewKey" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.console {
  display: flex;
  min-height: 100%;
  background: var(--ib-bg);
}

.sidebar {
  width: var(--ib-sidebar-width);
  flex: 0 0 var(--ib-sidebar-width);
  background: var(--ib-sidebar-bg);
  border-right: 1px solid var(--ib-border);
  display: flex;
  flex-direction: column;
  padding: 18px 12px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 8px 18px;
}

.mark {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: var(--ib-accent);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
}

.brand-name {
  font-weight: 600;
  font-size: 15px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.nav-item {
  appearance: none;
  border: 0;
  background: none;
  text-align: left;
  font: inherit;
  color: var(--ib-text-muted);
  padding: 9px 12px;
  border-radius: var(--ib-radius-sm);
  cursor: pointer;
}

.nav-item:hover {
  background: var(--ib-bg-elevated);
  color: var(--ib-text);
}

.nav-item.active {
  background: var(--ib-bg-elevated);
  color: var(--ib-accent);
  font-weight: 600;
  box-shadow: var(--ib-shadow-sm);
}

.nav-group-label {
  margin-top: 12px;
  padding: 6px 12px 2px;
  font-size: 12px;
  color: var(--ib-text-faint);
  letter-spacing: 0.04em;
}

.nav-item-child {
  padding-left: 24px;
  font-size: 13px;
}

.sidebar-foot {
  font-size: 12px;
  padding: 12px 12px 0;
  border-top: 1px solid var(--ib-border);
  display: flex;
  gap: 6px;
  align-items: baseline;
}

.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-select {
  flex: 1;
  min-width: 0;
}

.main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--ib-border);
  background: var(--ib-bg-elevated);
}

.topbar h1 {
  font-size: 16px;
  margin: 0;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user {
  cursor: pointer;
  color: var(--ib-text);
  font-size: 14px;
  padding: 4px 6px;
  border-radius: var(--ib-radius-sm);
}

.user:hover {
  background: var(--ib-bg-sunken);
}

.caret {
  color: var(--ib-text-faint);
  font-size: 12px;
}

.content {
  flex: 1;
  min-width: 0;
  padding: 24px;
  overflow: auto;
}

@media (max-width: 820px) {
  .sidebar {
    width: 168px;
    flex-basis: 168px;
  }
  .content {
    padding: 16px;
  }
}
</style>
