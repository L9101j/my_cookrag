<template>
  <div class="common-layout">
    <el-container>
      <el-aside width="300px">
        <div class="logo">
          <h2>CookRag</h2>
        </div>
        <el-menu
          default-active="/"
          class="el-menu-vertical-demo"
          router
        >
          <el-menu-item index="/">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能聊天</span>
          </el-menu-item>
          <el-menu-item index="/recipe">
            <el-icon><Food /></el-icon>
            <span>浏览食谱</span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>历史记录</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound, Food, Clock } from '@element-plus/icons-vue'
</script>

<style scoped>

.common-layout {
  height: 100vh;
  width: 98vw;
  margin-left: 0;
  margin-right: auto;
  overflow: hidden;
}
.el-container {
  height: 100%;
}
.el-aside {
  background-color: #f5f7fa;
  border-right: 1px solid #e6e6e6;
  display: flex;
  flex-direction: column;
  font-size: 30px;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #e6e6e6;
  background-color: #fff;
}
.logo h2 {
  margin: 0;
  color: #409eff;
}
.el-menu {
  border-right: none;
  background-color: transparent;
  flex: 1;
}
.el-menu-item {
  font-size: 20px;
  margin-bottom: 15px;
  padding: 15px 30px;
  display: flex; /* 使用 flex 布局 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  text-align: center; 
}
.el-main {
  padding: 0;
  background-color: #fff;
  height: 100%;
  overflow: hidden;
  font-size: 20px;
}
</style>
