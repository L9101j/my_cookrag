<template>
  <div class="chat-container">
    <div class="chat-header">
      <h3>智能烹饪助手</h3>
    </div>
    <div class="messages" ref="messagesContainer">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        class="message-wrapper"
        :class="{ 'user-message': msg.role === 'user', 'bot-message': msg.role === 'assistant' }"
      >
        <div class="avatar">
          <el-avatar :icon="msg.role === 'user' ? UserFilled : Service" :size="36" />
        </div>
        <div class="message-content">
          <el-card shadow="hover" :body-style="{ padding: '10px 15px' }">
            <div class="msg-text">{{ msg.content }}</div>
            <div v-if="msg.sources" style="margin-top: 16px">
              <el-tag
              v-for="source in msg.sources"
              :key="source"
              type="primary"
              effect="plain"
              style="margin-right: 10px; margin-bottom: 8px"
              size="large"
              >
              {{ source }}    
              </el-tag>
            </div>
          </el-card>
        </div>
      </div>
    </div>
    <div class="input-area">
      <el-input
        v-model="inputMessage"
        placeholder="请输入您的问题，例如：如何做红烧肉？"
        @keyup.enter="sendMessage"
        :disabled="loading"
        size="large"
        style="height: 36px"
      >
        <template #append>
          <el-button @click="sendMessage" :loading="loading">发送</el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, watch} from 'vue'
import { UserFilled, Service } from '@element-plus/icons-vue'
import apiClient from '@/service/api'
import { useRoute, useRouter } from 'vue-router'

interface ChatMessageRequest {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
}
interface ChatMessageQuery {
  message: string
  filters?: Record<string, any>
}
interface ChatHistoryItem {
  message_id: number
  role: 'user' | 'assistant'
  content: string
  intent?: string
  sources?: string[]
  timestamp: string
}
interface ChatHistoryResponse {
  session_id: string
  history: ChatHistoryItem[]
}


const STORAGE_KEY = 'chat_messages'
const route = useRoute()
const router = useRouter() 
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const sessionId = ref<string | null>(null)
const lastAssistantMessageId = ref<number | null>(null)
const messages = ref<ChatMessageRequest[]>([])
const enablePersist = ref(true)

const loadMessages = (): ChatMessageRequest[] => {
  try {
    const stored = sessionStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error('加载消息失败:', e)
  }
  // 默认消息
  return [{ role: 'assistant', content: '你好!我是你的智能烹饪助手,有什么可以帮你的吗?(推荐菜谱时，当前只会固定返回6个)' }]
}

// 保存消息到 sessionStorage
const saveMessages = () => {
  if(!enablePersist.value) return
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value))
  } catch (e) {
    console.error('保存消息失败:', e)
  }
}

// 监听消息变化,自动保存
watch(
  messages,
  () => {
    saveMessages()
  },
  { deep: true }
)

watch(
  () => route.fullPath,
  async () => {
    // 这里也可以判断一下 name === 'Chat'，但 Chat 页面里一般就是当前页
    await initByRoute()
  }
)

// 组件挂载时加载消息
const initByRoute = async () => {
  const sidFormRoute = route.query.session_id as string | undefined
  if (sidFormRoute) {
    enablePersist.value = false
    await loadHistoryFromServer(sidFormRoute)
  } else {
    enablePersist.value = true
    messages.value = loadMessages()
  }
  scrollToBottom()
}

// 组件挂载时加载消息
onMounted(async () => {
  await initByRoute()
})

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const loadHistoryFromServer = async (session_id: string) => {
  try{
    const resp = await apiClient.get(`/api/chat/history/${session_id}`)
    const d = resp.data.data as ChatHistoryResponse
    const history = d.history || []
    messages.value = history.map(item => ({
      role: item.role,
      content: item.content,
      sources: item.sources || undefined
    }))
    sessionId.value = session_id
  }catch(e){
    console.error('加载历史记录失败:', e)
    messages.value = loadMessages()
  }
}

const getIdFromServer = async () => {
  const resp = await apiClient.get('/api/chat/get_id')
  const payload = resp.data?.data || {}
  sessionId.value = payload.session_id
  return payload as { session_id: string; message_id: number }
}

const getSourcesFromServer = async (session_id: string, message_id: number) => {
  const resp = await apiClient.get('/api/chat/get_sources', {
    params: { session_id, message_id }
  })
  return (resp.data?.data?.sources || []) as string[]
}

const CallChatAPI = async(userquery: ChatMessageQuery) => {
    const baseURL = apiClient.defaults.baseURL || ''
    const resp = await fetch(`${baseURL}/api/chat/query_response`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(userquery)
    });
    if(!resp.ok||!resp.body){
        throw new Error(`HTTP error! status: ${resp.status}`);
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')

  // 最后一条消息就是我们预先插入的 assistant 消息
    const assistantIndex = messages.value.length - 1

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      const chunkText = decoder.decode(value, { stream: true })

      if (messages.value[assistantIndex]) {
        messages.value[assistantIndex].content += chunkText
      }
      scrollToBottom()
   }
};


const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  // 1. 先从服务器获取 session_id 和 message_id
  const { session_id, message_id } = await getIdFromServer()
  sessionId.value = session_id
  const assistantMessageId = message_id + 1
  lastAssistantMessageId.value = assistantMessageId

  const userMsg = inputMessage.value
  messages.value.push({ role: 'user', content: userMsg })
  inputMessage.value = ''
  loading.value = true
  scrollToBottom()
  messages.value.push({ role: 'assistant', content: '' })
  scrollToBottom()
  const userquery: ChatMessageQuery = {message: userMsg}

  try{
    await CallChatAPI(userquery)
    if (sessionId.value && lastAssistantMessageId.value != null) {
      const sources = await getSourcesFromServer(
        sessionId.value,
        lastAssistantMessageId.value
      )
      const lastIndex = messages.value.length - 1
      const lastMsg = messages.value[lastIndex]
      if (lastMsg && lastMsg.role === 'assistant') {
        lastMsg.sources = sources
      }
      console.log('本次回答引用的菜谱:', sources)
    }
  } catch (e) {
    console.error(e)
    const lastIndex = messages.value.length - 1
    if (messages.value[lastIndex]) {
      messages.value[lastIndex].content = '抱歉，服务器出现错误，请稍后再试。'
    }
  } finally {
    loading.value = false
    scrollToBottom()
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.chat-header {
  padding: 15px 20px;
  border-bottom: 1px solid #ebeef5;
  background-color: #fff;
}
.chat-header h3 {
  margin: 0;
  font-weight: 500;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f9f9f9;
}
.message-wrapper {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}
.user-message {
  flex-direction: row-reverse;
}
.avatar {
  margin: 0 10px;
}
.message-content {
  max-width: 70%;
}
.msg-text {
  white-space: pre-wrap; /* 保留换行和多空格，同时自动换行 */
  word-break: break-word; /* 避免长单词撑破布局 */
}
.user-message .message-content .el-card {
  background-color: #ecf5ff;
  border-color: #d9ecff;
}
.input-area {
  padding: 40px;
  background-color: #fff;
  border-top: 1px solid #ebeef5;
}
.input-area .el-input{
  font-size: 20px; /* 修改文字大小 */
}
.el-tag {
  font-size: 16px; /* 修改标签文字大小 */
}

</style>