<template>
  <div class="ai-assistant-page">
    <el-row :gutter="20" class="full-height-row">
      <!-- 左侧对话区 -->
      <el-col :span="16" class="full-height-col">
        <el-card class="chat-card">
          <template #header>
            <div class="card-header">
              <div>
                <el-icon :size="20" color="#409EFF"><ChatDotRound /></el-icon>
                <span class="title">AI 校园助手</span>
                <el-tag v-if="contextUsed" type="success" size="small" class="ml-2">知识库</el-tag>
              </div>
              <div class="header-actions">
                <el-button type="primary" :icon="Plus" @click="newChat">新建对话</el-button>
              </div>
            </div>
          </template>

          <!-- 消息列表 -->
          <div class="chat-messages" ref="messagesRef">
            <div
              v-for="(msg, index) in messages"
              :key="index"
              :class="['message', msg.role]"
            >
              <el-avatar
                :size="36"
                :icon="msg.role === 'user' ? User : ChatDotRound"
                :class="msg.role"
              />
              <div class="message-content">
                <div class="message-text" v-html="formatMessage(msg.content)"></div>
                <span v-if="msg.streaming" class="streaming-cursor">▊</span>
                <!-- 确认借阅按钮 -->
                <div v-if="msg.books && msg.books.length > 0 && !msg.streaming" class="borrow-confirm">
                  <el-divider />
                  <div class="book-list">
                    <div v-for="book in msg.books.slice(0, 3)" :key="book.id" class="book-item">
                      <el-icon><Document /></el-icon>
                      <span class="book-title">《{{ book.title }}》</span>
                      <el-tag :type="book.available > 0 ? 'success' : 'danger'" size="small">
                        {{ book.available > 0 ? `可借 ${book.available} 本` : '暂无库存' }}
                      </el-tag>
                    </div>
                  </div>
                  <div v-if="msg.books.some(b => b.available > 0)" class="confirm-actions">
                    <span class="confirm-hint">是否确认借阅第一本书？</span>
                    <el-button type="primary" size="small" @click="confirmBorrow">确认借阅</el-button>
                    <el-button size="small" @click="cancelBorrow">取消</el-button>
                  </div>
                </div>
                <div class="message-meta">
                  <span class="message-time">{{ msg.time }}</span>
                  <el-tag v-if="msg.source === 'quick_reply'" type="info" size="small">快速回复</el-tag>
                  <el-tag v-else-if="msg.data_source === 'database'" type="success" size="small">个人数据</el-tag>
                  <el-tag v-else-if="msg.data_source === 'knowledge_base'" type="warning" size="small">知识库</el-tag>
                </div>
              </div>
            </div>
            <div v-if="loading && !messages.some(m => m.streaming)" class="message assistant">
              <el-avatar :size="36" :icon="ChatDotRound" class="assistant" />
              <div class="message-content">
                <div class="streaming-indicator">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区 -->
          <div class="chat-input">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              :placeholder="inputPlaceholder"
              resize="none"
              @keydown.enter.prevent="handleKeydown"
            />
            <div class="input-actions">
              <span class="hint">Enter 发送，Ctrl + Enter 换行 | 支持查询借阅、预约、图书等信息</span>
              <el-button type="primary" :icon="Promotion" :loading="loading" @click="sendMessage">
                发送
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧功能区 -->
      <el-col :span="8" class="full-height-col right-panel">
        <!-- 对话记录 -->
        <el-card class="chat-history-card">
          <template #header>
            <div class="card-header">
              <span>📝 对话记录</span>
              <span class="record-count">{{ allHistory.length }} 条历史提问</span>
            </div>
          </template>
          <div class="chat-history">
            <div
              v-for="(item, index) in allHistory"
              :key="index"
              class="history-item"
              @click="inputMessage = item.content"
            >
              <el-icon size="14"><ChatDotRound /></el-icon>
              <span class="history-text" :title="item.content">{{ item.content }}</span>
              <span class="history-time">{{ item.time }}</span>
            </div>
            <div v-if="allHistory.length === 0" class="history-empty">
              暂无对话记录
            </div>
          </div>
        </el-card>

        <!-- 快捷问题 -->
        <el-card class="quick-questions-card">
          <template #header>
            <div class="card-header">
              <span>常见问题</span>
            </div>
          </template>
          <div class="quick-questions">
            <el-button
              v-for="q in quickQuestions"
              :key="q"
              text
              class="question-btn"
              @click="askQuestion(q)"
            >
              {{ q }}
            </el-button>
          </div>
        </el-card>

        <!-- 智能操作提示 -->
        <el-card class="tips-card">
          <template #header>
            <div class="card-header">
              <span>💡 智能操作提示</span>
            </div>
          </template>
          <div class="tips-list">
            <div class="tip-item">
              <el-icon color="#409EFF"><Search /></el-icon>
              <div>
                <div class="tip-title">查询信息</div>
                <div class="tip-desc">"我借了哪些书"、"我的预约"</div>
              </div>
            </div>
            <div class="tip-item">
              <el-icon color="#67C23A"><Document /></el-icon>
              <div>
                <div class="tip-title">发布通知</div>
                <div class="tip-desc">教师可说"发布关于期中考试的通知"</div>
              </div>
            </div>
            <div class="tip-item">
              <el-icon color="#E6A23C"><Calendar /></el-icon>
              <div>
                <div class="tip-title">办理预约</div>
                <div class="tip-desc">"帮我预约明天的图书馆座位"</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 知识库状态 -->
        <el-card class="kb-card" v-if="userRole === 'teacher' || userRole === 'admin'">
          <template #header>
            <div class="card-header">
              <span>📚 知识库管理</span>
            </div>
          </template>
          <div class="kb-info">
            <p>文档数量: {{ kbDocuments.length }}</p>
            <el-button type="primary" size="small" @click="reloadKnowledgeBase" :loading="reloading">
              重新加载知识库
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound,
  User,
  Plus,
  Promotion,
  Search,
  Document,
  Calendar
} from '@element-plus/icons-vue'
import { campusAssistant, campusAssistantStream, executeAction, listKnowledgeDocuments, reloadKnowledgeBase as reloadKB } from '@/api/ai'
import { marked } from 'marked'
import dayjs from 'dayjs'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const userRole = computed(() => userStore.userInfo?.role || 'student')

// 从 localStorage 读取对话历史
const STORAGE_KEY = 'ai_chat_history'
const HISTORY_KEY = 'ai_chat_all_history'

const loadMessages = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      return JSON.parse(saved)
    } catch (e) {
      console.error('读取历史记录失败:', e)
    }
  }
  return [
    {
      role: 'assistant',
      content: '您好！我是智慧校园 AI 助手，可以帮您：\n\n📖 查询图书和借阅记录\n📅 查看和办理场地预约\n📢 获取通知和任务信息\n📝 辅助教师发布通知\n\n请问有什么可以帮助您的？',
      time: dayjs().format('HH:mm'),
      context_used: false
    }
  ]
}

const messages = ref(loadMessages())

// 所有历史提问记录（跨对话保留）
const allHistory = ref([])

// 加载所有历史提问
const loadAllHistory = () => {
  const saved = localStorage.getItem(HISTORY_KEY)
  if (saved) {
    try {
      allHistory.value = JSON.parse(saved)
    } catch (e) {
      console.error('读取历史提问失败:', e)
    }
  }
}

// 保存对话历史到 localStorage
const saveMessages = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value))
}

// 保存历史提问到 localStorage
const saveHistory = (question, time) => {
  // 避免重复添加相同的问题
  const exists = allHistory.value.some(h => h.content === question)
  if (!exists) {
    allHistory.value.unshift({
      content: question,
      time: time
    })
    // 只保留最近50条历史
    if (allHistory.value.length > 50) {
      allHistory.value = allHistory.value.slice(0, 50)
    }
    localStorage.setItem(HISTORY_KEY, JSON.stringify(allHistory.value))
  }
}

const inputMessage = ref('')
const loading = ref(false)
const messagesRef = ref()
const contextUsed = ref(false)
const kbDocuments = ref([])
const reloading = ref(false)

// 待执行的操作（如借书确认）
const pendingAction = ref(null)

const inputPlaceholder = computed(() => {
  if (userRole.value === 'teacher' || userRole.value === 'admin') {
    return '请输入您的问题，例如：\n- 我借了哪些书\n- 发布关于五一放假的通知\n- 查询我的通知'
  }
  return '请输入您的问题，例如：\n- 我借了哪些书\n- 帮我预约明天的图书馆座位\n- 查询最新通知'
})

const quickQuestions = [
  '我借了哪些书？',
  '我的预约记录',
  '有哪些图书可以借？',
  '我的未读通知',
  '我的任务有哪些？',
  userRole.value === 'teacher' ? '发布关于期中考试的通知' : '图书馆开放时间'
]

const formatMessage = (text) => {
  if (!text) return ''
  // 使用 marked 解析 Markdown
  const html = marked.parse(text, {
    breaks: true,  // 将换行符转为 <br>
    gfm: true      // 启用 GitHub Flavored Markdown
  })
  return html
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

const handleKeydown = (e) => {
  if (e.ctrlKey) {
    // Ctrl+Enter 换行
    const start = e.target.selectionStart
    const end = e.target.selectionEnd
    const value = inputMessage.value
    inputMessage.value = value.substring(0, start) + '\n' + value.substring(end)
    // 设置光标位置到换行后
    nextTick(() => {
      e.target.selectionStart = e.target.selectionEnd = start + 1
    })
  } else {
    // Enter 发送
    sendMessage()
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  
  const userMsg = inputMessage.value.trim()
  const currentTime = dayjs().format('HH:mm')
  messages.value.push({
    role: 'user',
    content: userMsg,
    time: currentTime
  })
  
  // 保存用户消息到当前对话和历史记录
  saveMessages()
  saveHistory(userMsg, currentTime)
  
  inputMessage.value = ''
  loading.value = true
  contextUsed.value = false
  scrollToBottom()
  
  // 添加一个空的助手消息，用于流式填充
  // 必须通过数组索引获取响应式代理，否则修改不会触发 Vue 更新
  messages.value.push({
    role: 'assistant',
    content: '',
    time: dayjs().format('HH:mm'),
    source: 'stream',
    data_source: null,
    streaming: true,
    books: null
  })
  const assistantMsg = messages.value[messages.value.length - 1]
  
  // 检查是否是确认操作
  const isConfirm = ['确认', '可以', '好的', '是', '行', '同意'].some(word => userMsg.includes(word))
  const isCancel = ['取消', '不要', '算了', '否', '不'].some(word => userMsg.includes(word))
  
  // 如果有待执行的操作且用户确认
  if (pendingAction.value && isConfirm && !isCancel) {
    // 直接执行操作
    assistantMsg.streaming = false
    assistantMsg.content = '正在处理您的请求...'
    
    try {
      const result = await executeAction(pendingAction.value)
      if (result.code === 200) {
        assistantMsg.content = `✅ ${result.message}`
        if (result.data?.due_date) {
          assistantMsg.content += `\n\n应还日期：${result.data.due_date}`
        }
      } else {
        assistantMsg.content = `❌ ${result.message}`
      }
      pendingAction.value = null  // 清除待执行操作
      saveMessages()
      loading.value = false
      return
    } catch (error) {
      assistantMsg.content = '❌ 操作失败，请稍后重试'
      pendingAction.value = null
      saveMessages()
      loading.value = false
      return
    }
  }
  
  // 如果取消操作
  if (pendingAction.value && isCancel) {
    pendingAction.value = null
    assistantMsg.streaming = false
    assistantMsg.content = '已取消操作。'
    saveMessages()
    loading.value = false
    return
  }
  
  try {
    // 构建上下文（最近10轮对话）
    const context = messages.value
      .filter(m => !m.streaming) // 排除正在生成的消息
      .slice(-20) // 最近20条消息（10轮对话）
      .map(m => ({
        role: m.role,
        content: m.content
      }))
    
    // 使用流式接口
    await new Promise((resolve, reject) => {
      campusAssistantStream(
        { question: userMsg, context },
        (chunk) => {
          // 处理不同类型的消息
          if (chunk.type === 'intent') {
            // 意图识别结果
            if (chunk.data.needs_db_query) {
              contextUsed.value = true
            }
          } else if (chunk.type === 'books') {
            // 收到图书数据，保存到消息和待执行操作
            assistantMsg.books = chunk.data
            // 找第一本可借的书
            const availableBook = chunk.data.find(b => b.available > 0)
            if (availableBook) {
              pendingAction.value = {
                action: 'borrow_book',
                params: { book_id: availableBook.id }
              }
            }
          } else if (chunk.type === 'db_data') {
            // 有数据库数据
            contextUsed.value = true
          } else if (chunk.type === 'data_source') {
            // 数据来源：database 或 knowledge_base
            assistantMsg.data_source = chunk.data
          } else if (chunk.type === 'content') {
            // 流式内容 - 直接追加并触发更新
            assistantMsg.content += chunk.data
            // 强制触发 Vue 更新
            nextTick(() => {
              scrollToBottom()
            })
          } else if (chunk.type === 'error') {
            // 错误
            assistantMsg.content += `\n\n[错误: ${chunk.data}]`
          }
        },
        (error) => {
          reject(error)
        },
        () => {
          // 完成
          assistantMsg.streaming = false
          assistantMsg.time = dayjs().format('HH:mm')
          saveMessages()
          resolve()
        }
      )
    })
    
  } catch (error) {
    ElMessage.error('请求失败，请稍后重试')
    assistantMsg.streaming = false
    assistantMsg.content = '抱歉，网络请求失败，请稍后重试。'
    assistantMsg.time = dayjs().format('HH:mm')
    saveMessages()
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const askQuestion = (q) => {
  inputMessage.value = q
  sendMessage()
}

const confirmBorrow = () => {
  // 自动填入"确认"并发送
  inputMessage.value = '确认借阅'
  sendMessage()
}

const cancelBorrow = () => {
  // 自动填入"取消"并发送
  inputMessage.value = '取消'
  sendMessage()
}

const newChat = () => {
  messages.value = [
    {
      role: 'assistant',
      content: '您好！我是智慧校园 AI 助手，可以帮您：\n\n📖 查询图书和借阅记录\n📅 查看和办理场地预约\n📢 获取通知和任务信息\n📝 辅助教师发布通知\n\n请问有什么可以帮助您的？',
      time: dayjs().format('HH:mm'),
      context_used: false
    }
  ]
  contextUsed.value = false
  // 只清除当前对话，保留历史提问记录
  localStorage.removeItem(STORAGE_KEY)
  ElMessage.success('已创建新对话')
}

const fetchKnowledgeDocuments = async () => {
  try {
    const res = await listKnowledgeDocuments()
    if (res.code === 200) {
      kbDocuments.value = res.data.documents
    }
  } catch (error) {
    console.error('获取知识库文档失败:', error)
  }
}

const reloadKnowledgeBase = async () => {
  reloading.value = true
  try {
    const res = await reloadKB()
    if (res.code === 200) {
      ElMessage.success('知识库重新加载成功')
      fetchKnowledgeDocuments()
    } else {
      ElMessage.error(res.message || '重新加载失败')
    }
  } catch (error) {
    ElMessage.error('重新加载失败')
  } finally {
    reloading.value = false
  }
}

onMounted(() => {
  scrollToBottom()
  fetchKnowledgeDocuments()
  loadAllHistory()
})
</script>

<style scoped>
.ai-assistant-page {
  height: calc(100vh - 100px);
  padding: 16px;
  background-color: #f0f2f5;
}

.full-height-row {
  height: 100%;
}

.full-height-col {
  height: 100%;
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.right-panel :deep(.el-card) {
  margin: 0 !important;
}

.chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chat-history-card {
  flex: 1;
  overflow: hidden;
}

.chat-history-card :deep(.el-card__body) {
  height: calc(100% - 50px);
  padding: 12px;
  overflow-y: auto;
}

.chat-history {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.history-item:hover {
  background-color: #ecf5ff;
}

.history-text {
  flex: 1;
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-time {
  font-size: 11px;
  color: #909399;
}

.history-empty {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 20px 0;
}

.record-count {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.quick-questions-card {
  flex-shrink: 0;
}

.tips-card {
  flex-shrink: 0;
}

.kb-card {
  flex-shrink: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header > div {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.title {
  font-weight: bold;
  font-size: 16px;
}

.ml-2 {
  margin-left: 8px;
}

.chat-messages {
  height: calc(100% - 200px);
  overflow-y: auto;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message.user .message-content {
  background-color: #409EFF;
  color: #fff;
}

.message-text {
  line-height: 1.6;
  word-break: break-word;
}

.message-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.typing {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 流式输出指示器 */
.streaming-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 4px 0;
}

.streaming-indicator .dot {
  width: 8px;
  height: 8px;
  background-color: #909399;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite both;
}

.streaming-indicator .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.streaming-indicator .dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
    background-color: #409EFF;
  }
}

/* 流式生成光标 */
.streaming-cursor {
  display: inline-block;
  color: #409EFF;
  font-weight: bold;
  margin-left: 2px;
  animation: cursor-blink 0.8s infinite;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.chat-input {
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.hint {
  font-size: 12px;
  color: #909399;
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-btn {
  justify-content: flex-start;
  text-align: left;
  padding: 8px 12px;
  height: auto;
  white-space: normal;
  line-height: 1.4;
}

.tips-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tip-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.tip-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.tip-desc {
  font-size: 12px;
  color: #909399;
}

.kb-info {
  text-align: center;
}

.kb-info p {
  margin: 0 0 12px 0;
  color: #606266;
}

/* Markdown 内容样式 */
.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4) {
  margin: 12px 0 8px 0;
  font-weight: 600;
  line-height: 1.4;
}

.message-text :deep(h1) { font-size: 1.3em; }
.message-text :deep(h2) { font-size: 1.2em; }
.message-text :deep(h3) { font-size: 1.1em; }

.message-text :deep(p) {
  margin: 8px 0;
  line-height: 1.6;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(li) {
  margin: 4px 0;
}

.message-text :deep(code) {
  background-color: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #e83e8c;
}

.message-text :deep(pre) {
  background-color: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-text :deep(pre code) {
  background-color: transparent;
  color: inherit;
  padding: 0;
}

.message-text :deep(blockquote) {
  border-left: 4px solid #409EFF;
  padding-left: 12px;
  margin: 8px 0;
  color: #606266;
}

.message-text :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid #dcdfe6;
  padding: 8px 12px;
  text-align: left;
}

.message-text :deep(th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

.message-text :deep(a) {
  color: #409EFF;
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
}

.message-text :deep(strong) {
  font-weight: 600;
}

.message-text :deep(em) {
  font-style: italic;
}

/* 用户消息的 Markdown 样式适配 */
.message.user .message-text :deep(code) {
  background-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.message.user .message-text :deep(pre) {
  background-color: rgba(0, 0, 0, 0.2);
}

.message.user .message-text :deep(a) {
  color: #fff;
  text-decoration: underline;
}

/* 借阅确认区域样式 */
.borrow-confirm {
  margin-top: 12px;
  padding-top: 8px;
}

.book-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.book-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
}

.book-title {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.confirm-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.confirm-hint {
  font-size: 13px;
  color: #606266;
}

.message.user .borrow-confirm .book-item {
  background-color: rgba(255, 255, 255, 0.15);
}

.message.user .borrow-confirm .book-title {
  color: #fff;
}

.message.user .borrow-confirm .confirm-hint {
  color: rgba(255, 255, 255, 0.9);
}
</style>
