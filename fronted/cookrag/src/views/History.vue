<template>
  <div class="history-container">
    <div class="header">
      <h2>历史记录</h2>
      <el-button
        type="danger"
        plain
        size="small"
        :loading="clearing"
        @click="onClearHistory"
      >
        清空历史
      </el-button>
    </div>

    <!-- 加载中 -->
    <el-skeleton v-if="loading" animated>
      <template #template>
        <el-skeleton-item variant="h3" style="width: 40%" />
        <el-skeleton-item variant="text" />
        <el-skeleton-item variant="text" />
      </template>
    </el-skeleton>

    <!-- 没有任何历史记录 -->
    <el-empty
      v-else-if="sessions.length === 0"
      description="暂无历史记录"
    />

    <!-- 按日期（session_id）展示 -->
    <el-timeline v-else>
      <el-timeline-item
        v-for="sid in sessions"
        :key="sid"
        :timestamp="formatSessionIdToDate(sid)"
        placement="top"
      >
        <el-card
          class="session-card"
          shadow="hover"
          @click="openSession(sid)"
        >
          <h4>会话日期：{{ formatSessionIdToDate(sid) }}</h4>
          <p>点击查看该日的所有聊天记录</p>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {useRouter} from 'vue-router'
import apiClient from '@/service/api'

const clearing = ref(false)
const loading = ref(true)
const sessions = ref<string[]>([])
const router = useRouter()

const getSessions = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/api/chat/history_lists')
    sessions.value = response.data.data.sessions || []
    console.log('获取历史记录成功', sessions.value)
  } catch (error) {
    ElMessage.error('获取历史记录失败')
  } finally {
    loading.value = false
  }
}

const onClearHistory = async ()=>{
  if (!sessions.value) 
    return
  try{
    await ElMessageBox.confirm(
      '确定要清空所有历史记录吗？此操作不可撤销。',
      '清空历史记录',
      {
        confirmButtonText: '清空',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
  }catch {
    return
  }
  clearing.value = true
  try{
    await apiClient.delete('/api/chat/clear_history')
    ElMessage.success('历史记录已清空')
    sessions.value = []
  }  catch{
    ElMessage.error('清空历史记录失败')
  } finally {
    clearing.value = false
  }
}

const formatSessionIdToDate = (sid: string): string => {
  if (!sid || sid.length !== 8) return sid
  const year = sid.slice(0,4)
  const month = sid.slice(4,6)
  const day = sid.slice(6,8)
  return `${year}-${month}-${day}`

}

const openSession = (sid: string) => {
  
  router.push({ name: 'Chat', query: { session_id: sid } })
}

onMounted(() => {
  getSessions()
})

</script>

<style scoped>
.history-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}
.session-card {
  cursor: pointer;
}
.session-card:hover {
  border-color: var(--el-color-primary);
}
</style>