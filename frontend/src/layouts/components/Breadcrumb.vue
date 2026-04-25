<template>
  <el-breadcrumb separator="/">
    <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
    <el-breadcrumb-item v-if="$route.meta.title">
      {{ $route.meta.title }}
    </el-breadcrumb-item>
  </el-breadcrumb>
</template>

<script setup>
</script>

<style scoped>
:deep(.el-breadcrumb__inner) {
  color: #606266;
}

:deep(.el-breadcrumb__inner.is-link:hover) {
  color: #409EFF;
}
</style>
