<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-327 / 328 应用根组件（路由出口 + 中文语境）
 * @author software-developer
 *
 * 根组件（R13 重写）。
 *
 * ## 为什么根组件只剩一个 `<router-view>`
 *
 * R1~R12 的 `App.vue` 同时承担「应用外壳」（令牌输入 + 页签切换）。R13 引入路由后，
 * 外壳属于**布局**（`layouts/ConsoleLayout.vue`），登录页则是**独立**于外壳之外的页面
 * （未登录时不应看到控制台骨架）。把两者都塞进根组件会退化成大量 `v-if`；交给路由表
 * 表达「哪些页面属于外壳」才是结构上的正确位置。
 *
 * ## 为什么不再有「粘贴访问令牌」入口
 *
 * 令牌由 `POST /api/auth/login` 以用户名 + 口令换取（IFC-IB-316）。保留手动粘贴入口
 * 等于保留一条**绕过账户体系**的通道（任何拿到令牌的人都能进），与 REQ-FUNC-IB-28
 * 「登录必须经账户口令，不可绕过」直接冲突，故**整条入口被删除**，而非隐藏。
 */
</script>

<template>
  <router-view />
</template>
