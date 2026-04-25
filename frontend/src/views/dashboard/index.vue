<template>
  <div class="dashboard">
    <!-- 顶部欢迎区域 -->
    <div class="welcome-section">
      <div class="welcome-left">
        <h1>👋 欢迎回来，{{ userStore.userInfo?.name || userStore.username }}</h1>
        <p class="date">{{ today }} · {{ greeting }}</p>
      </div>
      <div class="welcome-right">
        <el-button type="primary" :icon="Setting" circle @click="$router.push('/profile')" />
      </div>
    </div>

    <!-- 主体内容区域 -->
    <el-row :gutter="24" class="main-content">
      <!-- 左侧：AI助手 -->
      <el-col :xs="24" :sm="24" :md="16" :lg="16">
        <div class="ai-section">
          <div class="ai-header">
            <div class="ai-brand">
              <div class="ai-icon">
                <el-icon :size="24"><ChatDotRound /></el-icon>
              </div>
              <div class="ai-info">
                <span class="ai-name">AI 校园助手</span>
                <span v-if="contextUsed" class="ai-status">
                  <el-tag type="success" size="small">知识库已连接</el-tag>
                </span>
                <span v-else class="ai-status">随时为您服务</span>
              </div>
            </div>
            <div class="ai-actions">
              <el-button link :icon="Plus" @click="newChat">新建对话</el-button>
              <el-button type="primary" link :icon="FullScreen" @click="$router.push('/ai-assistant')">
                全屏模式
              </el-button>
            </div>
          </div>

          <!-- 聊天区域 -->
          <div class="chat-container">
            <div class="chat-messages" ref="messagesRef">
              <div
                v-for="(msg, index) in messages"
                :key="index"
                :class="['message', msg.role]"
              >
                <div class="avatar">
                  <el-avatar
                    :size="36"
                    :icon="msg.role === 'user' ? User : ChatDotRound"
                  />
                </div>
                <div class="message-bubble">
                  <div class="message-text" v-html="formatMessage(msg.content)"></div>
                  <span v-if="msg.streaming" class="streaming-cursor">▊</span>
                  <!-- 确认借阅按钮 -->
                  <div v-if="msg.books && msg.books.length > 0 && !msg.streaming" class="borrow-confirm">
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
                      <div class="confirm-btns">
                        <el-button type="primary" size="small" @click="confirmBorrow">确认借阅</el-button>
                        <el-button size="small" @click="cancelBorrow">取消</el-button>
                      </div>
                    </div>
                  </div>
                  <div class="message-footer">
                    <span class="message-time">{{ msg.time }}</span>
                    <el-tag v-if="msg.data_source === 'database'" type="success" size="small" effect="plain">个人数据</el-tag>
                    <el-tag v-else-if="msg.data_source === 'knowledge_base'" type="warning" size="small" effect="plain">知识库</el-tag>
                  </div>
                </div>
              </div>
              <div v-if="loading && !messages.some(m => m.streaming)" class="message assistant">
                <div class="avatar">
                  <el-avatar :size="36" :icon="ChatDotRound" />
                </div>
                <div class="message-bubble">
                  <div class="streaming-indicator">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 快捷问题 -->
            <div class="quick-chips">
              <span class="chips-label">常用：</span>
              <el-button
                v-for="q in quickQuestions.slice(0, 4)"
                :key="q"
                round
                size="small"
                @click="askQuestion(q)"
              >
                {{ q }}
              </el-button>
            </div>

            <!-- 输入区 -->
            <div class="chat-input-wrapper">
              <div class="chat-input">
                <el-input
                  v-model="inputMessage"
                  type="textarea"
                  :rows="2"
                  :placeholder="inputPlaceholder"
                  resize="none"
                  @keydown.enter.prevent="handleKeydown"
                />
                <el-button
                  type="primary"
                  class="send-btn"
                  :loading="loading"
                  @click="sendMessage"
                >
                  <el-icon><Promotion /></el-icon>
                </el-button>
              </div>
              <div class="input-hint">
                <span>Enter 发送 · Ctrl+Enter 换行 · 支持图书借阅、预约查询、通知发布</span>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：概览信息 -->
      <el-col :xs="24" :sm="24" :md="8" :lg="8">
        <div class="sidebar">
          <!-- 统计概览 -->
          <div class="stats-grid">
            <div class="stat-box" @click="$router.push('/library')">
              <div class="stat-icon" style="background: #e6f2ff; color: #409EFF;">
                <el-icon><Collection /></el-icon>
              </div>
              <div class="stat-detail">
                <span class="stat-num">{{ stats.borrowCount }}</span>
                <span class="stat-name">我的借阅</span>
              </div>
            </div>
            <div class="stat-box" @click="$router.push('/reservation')">
              <div class="stat-icon" style="background: #e6f7ed; color: #67C23A;">
                <el-icon><OfficeBuilding /></el-icon>
              </div>
              <div class="stat-detail">
                <span class="stat-num">{{ stats.reservationCount }}</span>
                <span class="stat-name">我的预约</span>
              </div>
            </div>
            <div class="stat-box" @click="$router.push('/tasks')">
              <div class="stat-icon" style="background: #fdf6ec; color: #E6A23C;">
                <el-icon><List /></el-icon>
              </div>
              <div class="stat-detail">
                <span class="stat-num">{{ stats.taskCount }}</span>
                <span class="stat-name">待办任务</span>
              </div>
            </div>
            <div class="stat-box" @click="$router.push('/notifications')">
              <div class="stat-icon" style="background: #fef0f0; color: #F56C6C;">
                <el-icon><Bell /></el-icon>
              </div>
              <div class="stat-detail">
                <span class="stat-num">{{ stats.unreadCount }}</span>
                <span class="stat-name">未读通知</span>
              </div>
            </div>
          </div>

          <!-- 快捷入口 -->
          <div class="quick-menu">
            <h3 class="section-title">快捷入口</h3>
            <div class="menu-grid">
              <div
                v-for="link in quickLinks"
                :key="link.path"
                class="menu-item"
                @click="$router.push(link.path)"
              >
                <div class="menu-icon" :style="{ background: link.color + '20', color: link.color }">
                  <el-icon :size="20"><component :is="link.icon" /></el-icon>
                </div>
                <span class="menu-name">{{ link.title }}</span>
              </div>
            </div>
          </div>

          <!-- 最近通知 -->
          <div class="recent-notifications">
            <h3 class="section-title">
              最近通知
              <el-button link size="small" @click="$router.push('/notifications')">查看全部</el-button>
            </h3>
            <div class="notification-list">
              <div v-if="!recentNotifications.length" class="empty-notifications">
                <el-icon :size="40" color="#dcdfe6"><Bell /></el-icon>
                <span>暂无新通知</span>
              </div>
              <template v-else>
                <div
                  v-for="item in recentNotifications.slice(0, 3)"
                  :key="item.id"
                  class="notification-item"
                  :class="{ unread: !item.is_read }"
                  @click="$router.push('/notifications')"
                >
                  <div class="notification-dot" :class="item.type"></div>
                  <div class="notification-content">
                    <span class="notification-title">{{ item.title }}</span>
                    <span class="notification-time">{{ item.created_at }}</span>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
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
  User,
  Plus,
  Promotion,
  Document,
  Setting,
  FullScreen,
  Calendar,
  Reading,
  Location,
  Message
} from '@element-plus/icons-vue'
import { getBorrows } from '@/api/library'
import { getReservations } from '@/api/reservation'
import { getTasks } from '@/api/task'
import { getNotifications, getUnreadCount } from '@/api/notification'
import { campusAssistantStream, executeAction } from '@/api/ai'
import { marked } from 'marked'
import dayjs from 'dayjs'

const userStore = useUserStore()
const today = computed(() => dayjs().format('YYYY年M月D日'))

const greeting = computed(() => {
  const hour = dayjs().hour()
  if (hour < 12) return '早上好，开启美好的一天！'
  if (hour < 14) return '中午好，记得休息哦！'
  if (hour < 18) return '下午好，继续加油！'
  return '晚上好，今天辛苦了！'
})

const stats = ref({
  borrowCount: 0,
  reservationCount: 0,
  taskCount: 0,
  unreadCount: 0
})

const quickLinks = [
  { path: '/library', title: '图书借阅', icon: Reading, color: '#409EFF' },
  { path: '/reservation', title: '场地预约', icon: Location, color: '#67C23A' },
  { path: '/tasks', title: '任务管理', icon: Calendar, color: '#E6A23C' },
  { path: '/notifications', title: '通知中心', icon: Message, color: '#F56C6C' }
]

const recentNotifications = ref([])

// AI 助手相关状态
const CURRENT_CHAT_KEY = 'ai_current_chat'

const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

const getWelcomeMessage = () => ({
  role: 'assistant',
  content: '您好！我是智慧校园 AI 助手，可以帮您：\n\n📖 查询图书和借阅记录\n📅 查看和办理场地预约\n📢 获取通知和任务信息\n📝 辅助教师发布通知\n\n请问有什么可以帮助您的？',
  time: dayjs().format('HH:mm'),
  context_used: false
})

const currentSession = ref({
  id: generateId(),
  title: '新对话',
  messages: [getWelcomeMessage()],
  createdAt: dayjs().format('YYYY-MM-DD HH:mm:ss'),
  updatedAt: dayjs().format('YYYY-MM-DD HH:mm:ss')
})

const inputMessage = ref('')
const loading = ref(false)
const messagesRef = ref()
const contextUsed = ref(false)
const pendingAction = ref(null)

const messages = computed(() => currentSession.value.messages)

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
  '我的未读通知'
]

const loadCurrentSession = () => {
  const saved = localStorage.getItem(CURRENT_CHAT_KEY)
  if (saved) {
    try {
      const session = JSON.parse(saved)
      currentSession.value = {
        ...session,
        messages: session.messages || [getWelcomeMessage()]
      }
    } catch (e) {
      console.error('读取当前对话失败:', e)
    }
  }
}

const saveCurrentSession = () => {
  currentSession.value.updatedAt = dayjs().format('YYYY-MM-DD HH:mm:ss')
  localStorage.setItem(CURRENT_CHAT_KEY, JSON.stringify(currentSession.value))
}

const updateSessionTitle = () => {
  const firstUserMsg = currentSession.value.messages.find(m => m.role === 'user')
  if (firstUserMsg && currentSession.value.title === '新对话') {
    const title = firstUserMsg.content.slice(0, 20) + (firstUserMsg.content.length > 20 ? '...' : '')
    currentSession.value.title = title
  }
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

  currentSession.value.messages.push({
    role: 'user',
    content: userMsg,
    time: currentTime
  })

  updateSessionTitle()
  saveCurrentSession()
  inputMessage.value = ''
  loading.value = true
  contextUsed.value = false
  scrollToBottom()

  currentSession.value.messages.push({
    role: 'assistant',
    content: '',
    time: dayjs().format('HH:mm'),
    source: 'stream',
    data_source: null,
    streaming: true,
    books: null
  })
  const assistantMsg = currentSession.value.messages[currentSession.value.messages.length - 1]

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
      saveCurrentSession()
      loading.value = false
      return
    } catch (error) {
      assistantMsg.content = '❌ 操作失败，请稍后重试'
      pendingAction.value = null
      saveCurrentSession()
      loading.value = false
      return
    }
  }

  if (pendingAction.value && isCancel) {
    pendingAction.value = null
    assistantMsg.streaming = false
    assistantMsg.content = '已取消操作。'
    saveCurrentSession()
    loading.value = false
    return
  }

  try {
    const context = currentSession.value.messages
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
          saveCurrentSession()
          resolve()
        }
      )
    })
  } catch (error) {
    assistantMsg.streaming = false
    assistantMsg.content = '抱歉，网络请求失败，请稍后重试。'
    assistantMsg.time = dayjs().format('HH:mm')
    saveCurrentSession()
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
  if (currentSession.value.messages.length > 1) {
    const CHAT_SESSIONS_KEY = 'ai_chat_sessions'
    const sessions = JSON.parse(localStorage.getItem(CHAT_SESSIONS_KEY) || '[]')
    sessions.unshift({ ...currentSession.value })
    if (sessions.length > 50) sessions.pop()
    localStorage.setItem(CHAT_SESSIONS_KEY, JSON.stringify(sessions))
  }

  currentSession.value = {
    id: generateId(),
    title: '新对话',
    messages: [getWelcomeMessage()],
    createdAt: dayjs().format('YYYY-MM-DD HH:mm:ss'),
    updatedAt: dayjs().format('YYYY-MM-DD HH:mm:ss')
  }

  contextUsed.value = false
  pendingAction.value = null
  saveCurrentSession()
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
  loadCurrentSession()
  fetchStats()
  fetchRecentNotifications()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

/* 欢迎区域 */
.welcome-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 0 4px;
}

.welcome-left h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.welcome-left .date {
  margin: 8px 0 0;
  font-size: 14px;
  color: #909399;
}

/* 主体内容 */
.main-content {
  align-items: stretch;
}

/* AI 助手区域 */
.ai-section {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  height: calc(100vh - 160px);
  min-height: 600px;
  overflow: hidden;
}

.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.ai-brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.ai-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ai-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.ai-status {
  font-size: 12px;
  color: #67C23A;
}

.ai-actions {
  display: flex;
  gap: 8px;
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f8f9fa;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  flex-direction: row-reverse;
}

.avatar .el-avatar {
  background: #e4e7ed;
  color: #606266;
}

.message.user .avatar .el-avatar {
  background: #409EFF;
  color: #fff;
}

.message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  position: relative;
}

.message.assistant .message-bubble {
  border-top-left-radius: 4px;
}

.message.user .message-bubble {
  background: #409EFF;
  color: #fff;
  border-top-right-radius: 4px;
}

.message-text {
  line-height: 1.6;
  font-size: 14px;
}

.message-text :deep(p) {
  margin: 8px 0;
}

.message-text :deep(p:first-child) {
  margin-top: 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-footer {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.message.user .message-footer {
  border-top-color: rgba(255, 255, 255, 0.2);
}

.message-time {
  font-size: 11px;
  color: #909399;
}

.message.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

/* 流式输出效果 */
.streaming-cursor {
  display: inline-block;
  color: #409EFF;
  font-weight: bold;
  animation: blink 0.8s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.streaming-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 0;
}

.streaming-indicator .dot {
  width: 8px;
  height: 8px;
  background: #c0c4cc;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite both;
}

.streaming-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.streaming-indicator .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; background: #409EFF; }
}

/* 快捷问题 */
.quick-chips {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  flex-wrap: wrap;
}

.chips-label {
  font-size: 12px;
  color: #909399;
}

.quick-chips .el-button {
  font-size: 12px;
}

/* 输入区域 */
.chat-input-wrapper {
  padding: 16px 20px 20px;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

.chat-input {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.chat-input .el-textarea {
  flex: 1;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 12px 16px;
  resize: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid #e4e7ed;
}

.chat-input :deep(.el-textarea__inner:focus) {
  border-color: #409EFF;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.15);
}

.send-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  padding: 0;
  flex-shrink: 0;
}

.input-hint {
  margin-top: 8px;
  font-size: 11px;
  color: #c0c4cc;
  text-align: center;
}

/* 借阅确认 */
.borrow-confirm {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
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
  background: #f5f7fa;
  border-radius: 8px;
  font-size: 13px;
}

.book-title {
  flex: 1;
  color: #303133;
}

.confirm-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.confirm-hint {
  font-size: 13px;
  color: #606266;
}

.confirm-btns {
  display: flex;
  gap: 8px;
}

.message.user .borrow-confirm {
  border-top-color: rgba(255, 255, 255, 0.2);
}

.message.user .book-item {
  background: rgba(255, 255, 255, 0.15);
}

.message.user .book-title,
.message.user .confirm-hint {
  color: #fff;
}

/* 右侧边栏 */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 统计网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-box {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.stat-box:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-detail {
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.stat-name {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 快捷菜单 */
.quick-menu {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.section-title {
  margin: 0 0 16px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.menu-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 12px 4px;
  border-radius: 8px;
  transition: all 0.3s;
}

.menu-item:hover {
  background: #f5f7fa;
}

.menu-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.menu-name {
  font-size: 12px;
  color: #606266;
}

/* 最近通知 */
.recent-notifications {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.notification-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-notifications {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 0;
  color: #c0c4cc;
  gap: 8px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.notification-item:hover {
  background: #f5f7fa;
}

.notification-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}

.notification-dot.urgent { background: #F56C6C; }
.notification-dot.normal { background: #409EFF; }
.notification-dot.low { background: #67C23A; }

.notification-item.unread .notification-dot {
  box-shadow: 0 0 0 3px rgba(245, 108, 108, 0.2);
}

.notification-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 11px;
  color: #909399;
}

/* Markdown 样式 */
.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
}

.message.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-text :deep(ul), .message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(li) {
  margin: 4px 0;
}

/* 响应式适配 */
@media screen and (max-width: 992px) {
  .dashboard {
    padding: 16px;
  }

  .welcome-section {
    margin-bottom: 16px;
  }

  .welcome-left h1 {
    font-size: 20px;
  }

  .ai-section {
    height: auto;
    min-height: 500px;
  }

  .chat-messages {
    height: 350px;
  }

  .sidebar {
    margin-top: 20px;
  }
}

@media screen and (max-width: 768px) {
  .dashboard {
    padding: 12px;
  }

  .welcome-section {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .welcome-left h1 {
    font-size: 18px;
  }

  .ai-header {
    padding: 12px 16px;
  }

  .ai-icon {
    width: 36px;
    height: 36px;
  }

  .ai-name {
    font-size: 14px;
  }

  .chat-messages {
    padding: 12px;
    height: 300px;
  }

  .message-bubble {
    max-width: 85%;
    padding: 10px 12px;
  }

  .quick-chips {
    padding: 10px 12px;
  }

  .chat-input-wrapper {
    padding: 12px;
  }

  .send-btn {
    width: 40px;
    height: 40px;
  }

  .stats-grid {
    gap: 8px;
  }

  .stat-box {
    padding: 12px;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
  }

  .stat-num {
    font-size: 20px;
  }

  .menu-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media screen and (max-width: 480px) {
  .message-bubble {
    max-width: 90%;
  }

  .message-text {
    font-size: 13px;
  }

  .input-hint {
    display: none;
  }

  .confirm-btns {
    flex-direction: column;
  }

  .confirm-btns .el-button {
    width: 100%;
  }
}
</style>
