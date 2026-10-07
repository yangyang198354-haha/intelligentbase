<script setup lang="ts">
/**
 * @module MOD-IB-24
 * @implements IFC-IB-376（REV-18）「系统管理」父级节点的**透传容器**
 * @depends MOD-IB-24（router 子路由）
 * @author software-developer
 *
 * 「系统管理」分组的父级容器（REV-18 / ADR-42）。
 *
 * ## 为什么是一个「什么也不做」的组件
 *
 * ADR-42 要求导航树**新增父级节点**「系统管理」，下挂三子项（账户管理 / 项目管理 /
 * LLM Key 管理）。`vue-router` 的嵌套路由需要一个**父组件**承载子路由的 `<router-view>`。
 * 本容器**只**渲染 `<router-view>`，不引入任何布局 / 状态 —— 视觉外壳仍由
 * `ConsoleLayout` 统一提供（父级仅是**路由结构**上的分组，不是第二套布局）。
 *
 * **权限不在这里**：子路由各自的 `requiresAdmin` 与**服务端 `403`** 才是裁决者
 * （ADR-42：UI 分组不是权限机制）。
 */
</script>

<template>
  <router-view />
</template>
