<template>
  <div class="ai-assistant-page">
    <el-row :gutter="isMobile ? 0 : 20" class="full-height-row">
      <!-- 左侧对话区 -->
      <el-col :span="isMobile ? 24 : 16" class="full-height-col">
        <el-card class="chat-card" :body-style="isMobile ? { padding: '8px' } : {}">
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
                    <!-- 如果用户明确指定了书名，只显示匹配的那本或第一本会借的 -->
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

      <!-- 移动端快捷问题悬浮按钮 -->
      <el-button
        v-if="isMobile"
        class="mobile-quick-btn"
        type="primary"
        circle
        size="large"
        @click="showQuickDrawer = true"
      >
        <el-icon><QuestionFilled /></el-icon>
      </el-button>
      
      <!-- 移动端快捷问题抽屉 -->
      <el-drawer
        v-model="showQuickDrawer"
        title="常见问题"
        size="80%"
        direction="btt"
        :with-header="true"
        class="mobile-drawer"
      >
        <div class="mobile-quick-questions">
          <el-button
            v-for="q in quickQuestions"
            :key="q"
            type="primary"
            plain
            class="mobile-question-btn"
            @click="askQuestionFromDrawer(q)"
          >
            {{ q }}
          </el-button>
        </div>
        
        <el-divider />
        
        <div class="mobile-tips">
          <h4>💡 智能操作提示</h4>
          <div class="tip-item">
            <el-icon color="#409EFF"><Search /></el-icon>
            <div>
              <div class="tip-title">查询信息</div>
              <div class="tip-desc">"我借了哪些书"</div>
            </div>
          </div>
          <div class="tip-item">
            <el-icon color="#67C23A"><Document /></el-icon>
            <div>
              <div class="tip-title">发布通知</div>
              <div class="tip-desc">教师可发布通知</div>
            </div>
          </div>
          <div class="tip-item">
            <el-icon color="#E6A23C"><Calendar /></el-icon>
            <div>
              <div class="tip-title">办理预约</div>
              <div class="tip-desc">"预约图书馆座位"</div>
            </div>
          </div>
        </div>
      </el-drawer>
      
      <!-- 右侧功能区 -->
      <el-col :span="8" class="full-height-col right-panel hidden-mobile">
        <!-- 对话历史列表 -->
        <el-card class="chat-history-card">
          <template #header>
            <div class="card-header">
              <span>📝 对话历史</span>
              <span class="record-count">{{ chatSessions.length }} 个历史对话</span>
            </div>
          </template>
          <div class="chat-history">
            <!-- 当前对话（置顶） -->
            <div class="history-item current">
              <el-icon size="14"><ChatDotRound /></el-icon>
              <div class="history-info">
                <span class="history-title" :title="currentSession.title">
                  <el-tag size="small" type="primary" class="current-tag">当前</el-tag>
                  {{ currentSession.title }}
                </span>
                <span class="history-time">{{ dayjs(currentSession.updatedAt).format('MM-DD HH:mm') }}</span>
              </div>
              <span class="message-count">{{ currentSession.messages.length }} 条</span>
            </div>

            <!-- 历史会话列表 -->
            <div
              v-for="session in chatSessions"
              :key="session.id"
              class="history-item"
              @click="loadSession(session.id)"
            >
              <el-icon size="14"><ChatDotRound /></el-icon>
              <div class="history-info">
                <span class="history-title" :title="session.title">{{ session.title }}</span>
                <span class="history-time">{{ dayjs(session.updatedAt).format('MM-DD HH:mm') }}</span>
              </div>
              <div class="history-actions">
                <span class="message-count">{{ session.messages.length }} 条</span>
                <el-button
                  type="danger"
                  link
                  size="small"
                  class="delete-btn"
                  @click="deleteSession(session.id, $event)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>

            <div v-if="chatSessions.length === 0" class="history-empty">
              暂无历史对话
              <div class="history-hint">点击"新建对话"开始新的聊天</div>
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
  Calendar,
  QuestionFilled,
  Delete
} from '@element-plus/icons-vue'
import { campusAssistant, campusAssistantStream, executeAction, listKnowledgeDocuments, reloadKnowledgeBase as reloadKB } from '@/api/ai'
import { marked } from 'marked'
import dayjs from 'dayjs'

import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const userRole = computed(() => userStore.userInfo?.role || 'student')

// 移动端检测
const isMobile = computed(() => window.innerWidth <= 768)
const showQuickDrawer = ref(false)

// Storage Keys
const CURRENT_CHAT_KEY = 'ai_current_chat'      // 当前对话
const CHAT_SESSIONS_KEY = 'ai_chat_sessions'    // 历史会话列表
const MAX_HISTORY = 50                          // 最大保存会话数

// 生成唯一ID
const generateId = () => Date.now().toString(36) + Math.random().toString(36).substr(2)

// 默认欢迎消息
const getWelcomeMessage = () => ({
  role: 'assistant',
  content: '您好！我是智慧校园 AI 助手，可以帮您：\n\n📖 查询图书和借阅记录\n📅 查看和办理场地预约\n📢 获取通知和任务信息\n📝 辅助教师发布通知\n\n请问有什么可以帮助您的？',
  time: dayjs().format('HH:mm'),
  context_used: false
})

// 当前会话
const currentSession = ref({
  id: generateId(),
  title: '新对话',
  messages: [getWelcomeMessage()],
  createdAt: dayjs().format('YYYY-MM-DD HH:mm:ss'),
  updatedAt: dayjs().format('YYYY-MM-DD HH:mm:ss')
})

// 会话历史列表
const chatSessions = ref([])

// 从 localStorage 加载当前会话
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

// 从 localStorage 加载会话历史
const loadChatSessions = () => {
  const saved = localStorage.getItem(CHAT_SESSIONS_KEY)
  if (saved) {
    try {
      chatSessions.value = JSON.parse(saved)
    } catch (e) {
      console.error('读取会话历史失败:', e)
    }
  }
}

// 保存当前会话
const saveCurrentSession = () => {
  currentSession.value.updatedAt = dayjs().format('YYYY-MM-DD HH:mm:ss')
  localStorage.setItem(CURRENT_CHAT_KEY, JSON.stringify(currentSession.value))
}

// 保存会话历史列表
const saveChatSessions = () => {
  localStorage.setItem(CHAT_SESSIONS_KEY, JSON.stringify(chatSessions.value))
}

// 更新会话标题（基于第一条用户消息）
const updateSessionTitle = () => {
  const firstUserMsg = currentSession.value.messages.find(m => m.role === 'user')
  if (firstUserMsg && currentSession.value.title === '新对话') {
    // 截取前20个字符作为标题
    const title = firstUserMsg.content.slice(0, 20) + (firstUserMsg.content.length > 20 ? '...' : '')
    currentSession.value.title = title
  }
}

// 兼容旧代码，messages 指向当前会话的消息
const messages = computed(() => currentSession.value.messages)

// 兼容旧代码
const saveMessages = () => {
  saveCurrentSession()
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

  // 添加用户消息到当前会话
  currentSession.value.messages.push({
    role: 'user',
    content: userMsg,
    time: currentTime
  })

  // 更新会话标题（如果是第一条用户消息）
  updateSessionTitle()

  // 保存当前会话
  saveCurrentSession()

  inputMessage.value = ''
  loading.value = true
  contextUsed.value = false
  scrollToBottom()
  
  // 关键修复：检测查询类问题，清除之前残留的pendingAction
  const queryPatterns = [
    /我借了什么书|我的借阅|借了什么|借了哪些|在借/,  // 借阅查询
    /可以借什么|有哪些书|有什么书|推荐.*书/,  // 图书查询
    /我的预约|预约记录|有什么预约/,  // 预约查询
    /我的通知|未读通知|有什么通知/,  // 通知查询
    /我的任务|待办|有什么任务/  // 任务查询
  ]
  const isQuery = queryPatterns.some(pattern => pattern.test(userMsg))
  if (isQuery && pendingAction.value) {
    console.log('[AI] 检测到查询意图，清除待执行操作')
    pendingAction.value = null
  }
  
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
  
  // 检查是否是确认操作 - 更严格的判断
  // 只认明确的确认词，排除"可以""好的"等常见词
  const isConfirm = ['确认', '是的', '确定', '没问题', '就这样', '可以了'].some(word => userMsg.includes(word))
  const isCancel = ['取消', '不要', '算了', '否', '不借', '不预约', '不发布'].some(word => userMsg.includes(word))
  
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
            // 从用户消息中提取书名
            const bookMatch = userMsg.match(/《(.+?)》/)
            const requestedTitle = bookMatch ? bookMatch[1] : ''
            // 优先匹配用户指定的书名，否则找第一本可借的书
            let availableBook = null
            if (requestedTitle) {
              // 尝试精确匹配或包含匹配
              availableBook = chunk.data.find(b => 
                b.available > 0 && (
                  b.title === requestedTitle || 
                  b.title.includes(requestedTitle)
                )
              )
            }
            // 如果没找到匹配的书，使用第一本可借的
            if (!availableBook) {
              availableBook = chunk.data.find(b => b.available > 0)
            }
            if (availableBook) {
              pendingAction.value = {
                action: 'borrow_book',
                params: { book_id: availableBook.id },
                bookTitle: availableBook.title  // 保存书名用于显示
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

const askQuestionFromDrawer = (q) => {
  showQuickDrawer.value = false
  askQuestion(q)
}

const confirmBorrow = async () => {
  // 直接执行操作，不走AI对话
  if (!pendingAction.value) {
    ElMessage.warning('没有待执行的操作')
    return
  }
  
  loading.value = true
  
  // 添加执行中提示消息
  const currentTime = dayjs().format('HH:mm')
  messages.value.push({
    role: 'assistant',
    content: '正在办理中...',
    time: currentTime,
    streaming: false
  })
  const loadingMsg = messages.value[messages.value.length - 1]
  
  try {
    const result = await executeAction(pendingAction.value)
    
    // 替换执行中消息为结果
    if (result.code === 200) {
      loadingMsg.content = `✅ ${result.message}`
      if (result.data?.due_date) {
        loadingMsg.content += `\n\n应还日期：${result.data.due_date}`
      }
      if (result.data?.reservation_id) {
        loadingMsg.content += `\n\n预约号：${result.data.reservation_id}`
      }
      ElMessage.success('办理成功')
    } else {
      loadingMsg.content = `❌ ${result.message}`
      ElMessage.error(result.message || '办理失败')
    }
    
    pendingAction.value = null  // 清除待执行操作
    saveMessages()
  } catch (error) {
    loadingMsg.content = '❌ 操作失败，请稍后重试'
    ElMessage.error('操作失败')
    pendingAction.value = null
    saveMessages()
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const cancelBorrow = () => {
  // 取消操作
  pendingAction.value = null
  const currentTime = dayjs().format('HH:mm')
  messages.value.push({
    role: 'assistant',
    content: '已取消操作。',
    time: currentTime
  })
  saveMessages()
  scrollToBottom()
}

// 加载指定会话
const loadSession = (sessionId) => {
  const session = chatSessions.value.find(s => s.id === sessionId)
  if (session) {
    // 先将当前会话保存到历史（如果有对话内容）
    if (currentSession.value.messages.length > 1) {
      chatSessions.value.unshift({ ...currentSession.value })
      saveChatSessions()
    }
    // 加载选中的会话为当前会话
    currentSession.value = {
      ...session,
      messages: [...session.messages]
    }
    saveCurrentSession()
    // 从历史列表中移除（避免重复）
    chatSessions.value = chatSessions.value.filter(s => s.id !== sessionId)
    saveChatSessions()
    ElMessage.success('已加载历史对话')
  }
}

// 新建对话
const newChat = () => {
  // 保存当前会话到历史列表（如果有多于欢迎消息的内容）
  if (currentSession.value.messages.length > 1) {
    chatSessions.value.unshift({ ...currentSession.value })
    // 限制历史记录数量
    if (chatSessions.value.length > MAX_HISTORY) {
      chatSessions.value = chatSessions.value.slice(0, MAX_HISTORY)
    }
    saveChatSessions()
  }

  // 创建新会话
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

// 删除历史会话
const deleteSession = (sessionId, event) => {
  event.stopPropagation()
  chatSessions.value = chatSessions.value.filter(s => s.id !== sessionId)
  saveChatSessions()
  ElMessage.success('已删除历史对话')
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
  loadCurrentSession()
  loadChatSessions()
  scrollToBottom()
  fetchKnowledgeDocuments()
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

/* 移动端快捷问题悬浮按钮 */
.mobile-quick-btn {
  position: fixed;
  right: 16px;
  bottom: 100px;
  z-index: 100;
  width: 48px;
  height: 48px;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 移动端快捷问题抽屉 */
.mobile-quick-questions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.mobile-question-btn {
  width: 100%;
  justify-content: flex-start;
  text-align: left;
  height: auto;
  padding: 12px 16px;
  white-space: normal;
  line-height: 1.4;
}

.mobile-tips {
  padding: 8px 0;
}

.mobile-tips h4 {
  margin-bottom: 16px;
  color: #303133;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .ai-assistant-page {
    height: calc(100vh - 60px);
    padding: 0;
  }
  
  .chat-card {
    border-radius: 0;
    border: none;
  }
  
  .chat-card :deep(.el-card__header) {
    padding: 12px 16px;
  }
  
  .chat-card :deep(.el-card__body) {
    padding: 8px;
  }
  
  .card-header .title {
    font-size: 16px;
  }
  
  .chat-messages {
    height: calc(100% - 140px);
    padding: 8px;
    margin-bottom: 8px;
  }
  
  .message {
    gap: 8px;
    margin-bottom: 12px;
  }
  
  .message-content {
    max-width: 85%;
    padding: 10px 12px;
    font-size: 14px;
  }
  
  .chat-input {
    padding-top: 8px;
  }
  
  .chat-input :deep(.el-textarea__inner) {
    min-height: 60px !important;
  }
  
  .input-actions {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .input-actions .hint {
    font-size: 11px;
  }
  
  .input-actions .el-button {
    align-self: flex-end;
  }
  
  /* 借阅确认移动端适配 */
  .book-item {
    padding: 6px 8px;
    font-size: 13px;
  }
  
  .book-title {
    font-size: 13px;
  }
  
  .confirm-actions {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
  
  .confirm-actions .el-button {
    width: 100%;
  }
}

/* 小屏幕手机额外适配 */
@media screen and (max-width: 480px) {
  .message-content {
    max-width: 90%;
    padding: 8px 10px;
    font-size: 13px;
  }
  
  .chat-messages {
    height: calc(100% - 130px);
  }
  
  .message .el-avatar {
    width: 32px !important;
    height: 32px !important;
  }
}
</style>
