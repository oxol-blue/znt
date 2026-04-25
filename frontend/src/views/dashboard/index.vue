<template>
  <div class="dashboard">
    <!-- 欢迎卡片 -->
    <el-card class="welcome-card">
      <div class="welcome-content">
        <div>
          <h2>欢迎回来，{{ userStore.userInfo?.name || userStore.username }}！</h2>
          <p class="subtitle">今天是 {{ today }}，祝您工作愉快！</p>
        </div>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-row">
      <el-col :span="6">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-item">
            <el-icon :size="40" color="#409EFF"><Collection /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.borrowCount }}</div>
              <div class="stat-label">我的借阅</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-item">
            <el-icon :size="40" color="#67C23A"><OfficeBuilding /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.reservationCount }}</div>
              <div class="stat-label">我的预约</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-item">
            <el-icon :size="40" color="#E6A23C"><List /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.taskCount }}</div>
              <div class="stat-label">待办任务</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-item">
            <el-icon :size="40" color="#F56C6C"><Bell /></el-icon>
            <div class="stat-info">
              <div class="stat-value">{{ stats.unreadCount }}</div>
              <div class="stat-label">未读通知</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷入口 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快捷入口</span>
            </div>
          </template>
          <div class="quick-links">
            <el-button
              v-for="link in quickLinks"
              :key="link.path"
              :icon="link.icon"
              @click="$router.push(link.path)"
            >
              {{ link.title }}
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近通知</span>
              <el-button text @click="$router.push('/notifications')">查看全部</el-button>
            </div>
          </template>
          <el-empty v-if="!recentNotifications.length" description="暂无通知" />
          <el-timeline v-else>
            <el-timeline-item
              v-for="item in recentNotifications"
              :key="item.id"
              :type="item.type === 'urgent' ? 'danger' : 'primary'"
              :timestamp="item.created_at"
            >
              {{ item.title }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>

    <!-- AI 助手区域 -->
    <el-row :gutter="20" class="ai-row">
      <el-col :span="24">
        <el-card class="ai-assistant-card">
          <template #header>
            <div class="card-header">
              <div class="ai-title">
                <el-icon :size="20" color="#409EFF"><ChatDotRound /></el-icon>
                <span>AI 校园助手</span>
                <el-tag v-if="contextUsed" type="success" size="small">知识库</el-tag>
              </div>
              <div class="header-actions">
                <el-button type="primary" link :icon="Plus" @click="newChat">新建对话</el-button>
                <el-button text @click="$router.push('/ai-assistant')">进入完整版</el-button>
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
                    <div v-for="book in (pendingAction?.bookTitle ? 
                      msg.books.filter(b => b.title === pendingAction.bookTitle || b.available > 0).slice(0, 1) : 
                      msg.books.slice(0, 3))" :key="book.id" class="book-item">
                      <el-icon><Document /></el-icon>
                      <span class="book-title">《{{ book.title }}》</span>
                      <el-tag :type="book.available > 0 ? 'success' : 'danger'" size="small">
                        {{ book.available > 0 ? `可借 ${book.available} 本` : '暂无库存' }}
                      </el-tag>
                    </div>
                  </div>
                  <div v-if="msg.books.some(b => b.available > 0)" class="confirm-actions">
                    <span class="confirm-hint">是否确认借阅《{{ pendingAction?.bookTitle || '该书' }}》？</span>
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

          <!-- 快捷问题 -->
          <div class="quick-questions-bar">
            <el-button
              v-for="q in quickQuestions.slice(0, 4)"
              :key="q"
              type="primary"
              plain
              size="small"
              @click="askQuestion(q)"
            >
              {{ q }}
            </el-button>
          </div>

          <!-- 输入区 -->
          <div class="chat-input">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="2"
              :placeholder="inputPlaceholder"
              resize="none"
              @keydown.enter.prevent="handleKeydown"
            />
            <div class="input-actions">
              <span class="hint">Enter 发送，Ctrl + Enter 换行</span>
              <el-button type="primary" :icon="Promotion" :loading="loading" @click="sendMessage">
                发送
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound,
  Collection,
  OfficeBuilding,
  List,
  Bell,
  HomeFilled,
  User,
  Plus,
  Promotion,
  Document
} from '@element-plus/icons-vue'
import { getBorrows } from '@/api/library'
import { getReservations } from '@/api/reservation'
import { getTasks } from '@/api/task'
import { getNotifications, getUnreadCount } from '@/api/notification'
import { campusAssistantStream, executeAction } from '@/api/ai'
import { marked } from 'marked'
import dayjs from 'dayjs'

const userStore = useUserStore()
const today = computed(() => dayjs().format('YYYY年MM月DD日'))

const stats = ref({
  borrowCount: 0,
  reservationCount: 0,
  taskCount: 0,
  unreadCount: 0
})

const quickLinks = [
  { path: '/library', title: '图书借阅', icon: 'Collection' },
  { path: '/reservation', title: '场地预约', icon: 'OfficeBuilding' },
  { path: '/tasks', title: '任务管理', icon: 'List' },
  { path: '/notifications', title: '通知中心', icon: 'Bell' }
]

const recentNotifications = ref([])

// AI 助手相关状态
const STORAGE_KEY = 'dashboard_ai_chat'
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesRef = ref()
const contextUsed = ref(false)
const pendingAction = ref(null)

const userRole = computed(() => userStore.userInfo?.role || 'student')

const inputPlaceholder = computed(() => {
  if (userRole.value === 'teacher' || userRole.value === 'admin') {
    return '输入问题，如：我借了哪些书、发布关于五一放假的通知...'
  }
  return '输入问题，如：我借了哪些书、帮我预约图书馆座位...'
})

const quickQuestions = [
  '我借了哪些书？',
  '我的预约记录',
  '有哪些图书可以借？',
  '我的未读通知',
  '我的任务有哪些？',
  userRole.value === 'teacher' ? '发布关于期中考试的通知' : '图书馆开放时间'
]

// 初始化消息
const initMessages = () => {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      messages.value = JSON.parse(saved)
      return
    } catch (e) {
      console.error('读取历史记录失败:', e)
    }
  }
  messages.value = [
    {
      role: 'assistant',
      content: '您好！我是智慧校园 AI 助手，可以帮您：\n\n📖 查询图书和借阅记录\n📅 查看和办理场地预约\n📢 获取通知和任务信息\n📝 辅助教师发布通知\n\n请问有什么可以帮助您的？',
      time: dayjs().format('HH:mm'),
      context_used: false
    }
  ]
}

const saveMessages = () => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value))
}

const formatMessage = (text) => {
  if (!text) return ''
  return marked.parse(text, { breaks: true, gfm: true })
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
    const start = e.target.selectionStart
    const end = e.target.selectionEnd
    const value = inputMessage.value
    inputMessage.value = value.substring(0, start) + '\n' + value.substring(end)
    nextTick(() => {
      e.target.selectionStart = e.target.selectionEnd = start + 1
    })
  } else {
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
  
  saveMessages()
  inputMessage.value = ''
  loading.value = true
  contextUsed.value = false
  scrollToBottom()
  
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
  
  const isConfirm = ['确认', '可以', '好的', '是', '行', '同意'].some(word => userMsg.includes(word))
  const isCancel = ['取消', '不要', '算了', '否', '不'].some(word => userMsg.includes(word))
  
  if (pendingAction.value && isConfirm && !isCancel) {
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
      pendingAction.value = null
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
  
  if (pendingAction.value && isCancel) {
    pendingAction.value = null
    assistantMsg.streaming = false
    assistantMsg.content = '已取消操作。'
    saveMessages()
    loading.value = false
    return
  }
  
  try {
    const context = messages.value
      .filter(m => !m.streaming)
      .slice(-20)
      .map(m => ({ role: m.role, content: m.content }))
    
    await new Promise((resolve, reject) => {
      campusAssistantStream(
        { question: userMsg, context },
        (chunk) => {
          if (chunk.type === 'intent') {
            if (chunk.data.needs_db_query) {
              contextUsed.value = true
            }
          } else if (chunk.type === 'books') {
            assistantMsg.books = chunk.data
            const bookMatch = userMsg.match(/《(.+?)》/)
            const requestedTitle = bookMatch ? bookMatch[1] : ''
            let availableBook = null
            if (requestedTitle) {
              availableBook = chunk.data.find(b => 
                b.available > 0 && (
                  b.title === requestedTitle || 
                  b.title.includes(requestedTitle)
                )
              )
            }
            if (!availableBook) {
              availableBook = chunk.data.find(b => b.available > 0)
            }
            if (availableBook) {
              pendingAction.value = {
                action: 'borrow_book',
                params: { book_id: availableBook.id },
                bookTitle: availableBook.title
              }
            }
          } else if (chunk.type === 'db_data') {
            contextUsed.value = true
          } else if (chunk.type === 'data_source') {
            assistantMsg.data_source = chunk.data
          } else if (chunk.type === 'content') {
            assistantMsg.content += chunk.data
            nextTick(() => { scrollToBottom() })
          } else if (chunk.type === 'error') {
            assistantMsg.content += `\n\n[错误: ${chunk.data}]`
          }
        },
        (error) => { reject(error) },
        () => {
          assistantMsg.streaming = false
          assistantMsg.time = dayjs().format('HH:mm')
          saveMessages()
          resolve()
        }
      )
    })
  } catch (error) {
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
  inputMessage.value = '确认借阅'
  sendMessage()
}

const cancelBorrow = () => {
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
  localStorage.removeItem(STORAGE_KEY)
  ElMessage.success('已创建新对话')
}

const fetchStats = async () => {
  try {
    const [borrowRes, reservationRes, taskRes, unreadRes] = await Promise.all([
      getBorrows(),
      getReservations(),
      getTasks(),
      getUnreadCount()
    ])
    
    if (borrowRes.code === 200) {
      stats.value.borrowCount = borrowRes.data.items?.length || 0
    }
    if (reservationRes.code === 200) {
      stats.value.reservationCount = reservationRes.data.items?.length || 0
    }
    if (taskRes.code === 200) {
      const tasks = taskRes.data.items || []
      stats.value.taskCount = tasks.filter(t => !t.is_completed).length
    }
    if (unreadRes.code === 200) {
      stats.value.unreadCount = unreadRes.data.unread_count
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchRecentNotifications = async () => {
  try {
    const res = await getNotifications()
    if (res.code === 200) {
      recentNotifications.value = (res.data.items || []).slice(0, 5)
    }
  } catch (error) {
    console.error('获取通知失败:', error)
  }
}

onMounted(() => {
  fetchStats()
  fetchRecentNotifications()
  initMessages()
})
</script>

<style scoped>
.dashboard {
  padding-bottom: 20px;
}

.welcome-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-content h2 {
  margin: 0 0 8px;
  font-size: 24px;
}

.subtitle {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.quick-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.quick-links .el-button {
  min-width: 120px;
}

:deep(.el-timeline-item__content) {
  color: #606266;
}

/* AI 助手卡片样式 */
.ai-row {
  margin-top: 20px;
}

.ai-assistant-card {
  border-radius: 12px;
}

.ai-assistant-card :deep(.el-card__body) {
  padding: 16px;
}

.ai-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  font-size: 16px;
}

.chat-messages {
  height: 300px;
  overflow-y: auto;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 12px;
}

.message {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 12px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.message.user .message-content {
  background-color: #409EFF;
  color: #fff;
}

.message-text {
  line-height: 1.5;
  word-break: break-word;
  font-size: 14px;
}

.message-text :deep(p) {
  margin: 6px 0;
}

.message-meta {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 6px;
}

.message-time {
  font-size: 11px;
  color: #909399;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

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

.quick-questions-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
  padding: 0 4px;
}

.chat-input {
  border-top: 1px solid #ebeef5;
  padding-top: 12px;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 8px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.input-actions .hint {
  font-size: 12px;
  color: #909399;
}

/* 借阅确认样式 */
.borrow-confirm {
  margin-top: 10px;
  padding-top: 8px;
}

.book-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.book-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background-color: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
}

.book-title {
  flex: 1;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.confirm-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.confirm-hint {
  font-size: 12px;
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

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .welcome-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .welcome-content h2 {
    font-size: 18px;
  }
  
  .subtitle {
    font-size: 13px;
  }
  
  .stat-row {
    margin-bottom: 12px;
  }
  
  .stat-row .el-col {
    margin-bottom: 8px;
  }
  
  .stat-card {
    margin-bottom: 0;
  }
  
  .stat-card :deep(.el-card__body) {
    padding: 12px !important;
  }
  
  .stat-item {
    gap: 12px;
  }
  
  .stat-item .el-icon {
    font-size: 32px !important;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .stat-label {
    font-size: 12px;
    margin-top: 4px;
  }
  
  .el-row {
    margin-left: 0 !important;
    margin-right: 0 !important;
  }
  
  .el-col-12 {
    width: 100%;
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin-bottom: 12px;
  }
  
  .quick-links {
    justify-content: center;
  }
  
  .quick-links .el-button {
    flex: 1;
    min-width: auto;
    font-size: 13px;
  }
  
  /* AI 助手移动端适配 */
  .ai-row {
    margin-top: 12px;
  }
  
  .ai-assistant-card :deep(.el-card__header) {
    padding: 12px;
  }
  
  .ai-assistant-card :deep(.el-card__body) {
    padding: 12px;
  }
  
  .ai-title {
    font-size: 14px;
  }
  
  .header-actions .el-button {
    padding: 4px 8px;
    font-size: 12px;
  }
  
  .chat-messages {
    height: 250px;
    padding: 8px;
  }
  
  .message {
    gap: 8px;
    margin-bottom: 10px;
  }
  
  .message-content {
    max-width: 85%;
    padding: 8px 10px;
  }
  
  .message-text {
    font-size: 13px;
  }
  
  .quick-questions-bar {
    gap: 6px;
  }
  
  .quick-questions-bar .el-button {
    padding: 6px 10px;
    font-size: 12px;
  }
  
  .chat-input :deep(.el-textarea__inner) {
    min-height: 50px !important;
  }
  
  .input-actions {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .input-actions .el-button {
    align-self: flex-end;
  }
}

@media screen and (max-width: 480px) {
  .welcome-content h2 {
    font-size: 16px;
  }
  
  .stat-item {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }
  
  .stat-item .el-icon {
    font-size: 28px !important;
  }
  
  .quick-links .el-button {
    padding: 8px 12px;
  }
  
  .chat-messages {
    height: 220px;
  }
  
  .message-content {
    max-width: 90%;
  }
  
  .confirm-actions {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
  
  .confirm-actions .el-button {
    width: 100%;
  }
}
</style>
