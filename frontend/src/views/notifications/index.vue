<template>
  <div class="notifications-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>通知中心</span>
          <el-button
            v-if="userStore.isTeacher"
            type="primary"
            :icon="Plus"
            @click="showSendDialog = true"
          >
            发送通知
          </el-button>
        </div>
      </template>

      <!-- 通知列表 -->
      <el-timeline>
        <el-timeline-item
          v-for="item in notifications"
          :key="item.id"
          :type="getType(item.type)"
          :timestamp="item.created_at"
          placement="top"
        >
          <el-card :class="['notification-card', { unread: !item.is_read }]">
            <template #header>
              <div class="notification-header">
                <div class="notification-title">
                  <el-tag
                    v-if="item.priority === 'urgent'"
                    type="danger"
                    size="small"
                    effect="dark"
                    style="margin-right: 8px"
                  >
                    紧急
                  </el-tag>
                  <span>{{ item.title }}</span>
                </div>
                <el-button
                  v-if="!item.is_read"
                  type="primary"
                  link
                  size="small"
                  @click="handleMarkRead(item)"
                >
                  标记已读
                </el-button>
              </div>
            </template>
            <div class="notification-content markdown-body" v-html="renderMarkdown(item.content)"></div>
            <div class="notification-footer">
              <span class="sender">发送人: {{ item.sender_name || '系统' }}</span>
              <span class="target" v-if="item.target_type">
                面向: {{ getTargetLabel(item.target_type) }}
              </span>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>

      <el-empty v-if="!notifications.length" description="暂无通知" />
    </el-card>

    <!-- 发送通知对话框 -->
    <el-dialog v-model="showSendDialog" title="发送通知" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="通知标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入通知标题">
            <template #append>
              <el-button @click="handleGenerate">AI 生成</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="通知内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="6"
            placeholder="请输入通知内容"
            v-loading="generating"
          />
        </el-form-item>
        <el-form-item label="通知类型" prop="type">
          <el-select v-model="form.type" placeholder="选择类型" style="width: 100%">
            <el-option label="公告" value="announcement" />
            <el-option label="提醒" value="reminder" />
            <el-option label="活动" value="activity" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="form.priority" placeholder="选择优先级" style="width: 100%">
            <el-option label="普通" value="normal" />
            <el-option label="重要" value="high" />
            <el-option label="紧急" value="urgent" />
          </el-select>
        </el-form-item>
        <el-form-item label="面向对象" prop="target_type">
          <el-select v-model="form.target_type" placeholder="选择面向对象" style="width: 100%">
            <el-option label="全体" value="all" />
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSendDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">发送</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getNotifications, createNotification, markRead } from '@/api/notification'
import { generateNotification } from '@/api/ai'
import { marked } from 'marked'

const userStore = useUserStore()
const notifications = ref([])
const showSendDialog = ref(false)
const submitting = ref(false)
const generating = ref(false)
const formRef = ref()

const form = ref({
  title: '',
  content: '',
  type: 'announcement',
  priority: 'normal',
  target_type: 'all'
})

const rules = {
  title: [{ required: true, message: '请输入通知标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入通知内容', trigger: 'blur' }],
  type: [{ required: true, message: '请选择通知类型', trigger: 'change' }],
  priority: [{ required: true, message: '请选择优先级', trigger: 'change' }],
  target_type: [{ required: true, message: '请选择面向对象', trigger: 'change' }]
}

const getType = (type) => {
  const map = {
    announcement: 'primary',
    reminder: 'warning',
    activity: 'success',
    urgent: 'danger',
    task: 'info'
  }
  return map[type] || 'primary'
}

const getTargetLabel = (target) => {
  const map = {
    all: '全体',
    student: '学生',
    teacher: '教师'
  }
  return map[target] || target
}

const renderMarkdown = (content) => {
  if (!content) return ''
  return marked.parse(content, { breaks: true })
}

const fetchNotifications = async () => {
  try {
    const res = await getNotifications()
    if (res.code === 200) {
      notifications.value = res.data.items || []
    }
  } catch (error) {
    console.error('获取通知失败:', error)
  }
}

const handleMarkRead = async (item) => {
  try {
    const res = await markRead(item.id)
    if (res.code === 200) {
      item.is_read = 1
      ElMessage.success('已标记为已读')
    }
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

const handleGenerate = async () => {
  if (!form.value.title) {
    ElMessage.warning('请先输入通知标题')
    return
  }
  
  generating.value = true
  try {
    const res = await generateNotification({
      title: form.value.title,
      type: form.value.type,
      target: getTargetLabel(form.value.target_type)
    })
    if (res.code === 200) {
      form.value.content = res.data.content
      ElMessage.success('内容已生成')
    }
  } catch (error) {
    console.error('生成失败:', error)
  } finally {
    generating.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const res = await createNotification(form.value)
    if (res.code === 200) {
      ElMessage.success('发送成功')
      showSendDialog.value = false
      fetchNotifications()
      form.value = {
        title: '',
        content: '',
        type: 'announcement',
        priority: 'normal',
        target_type: 'all'
      }
    }
  } catch (error) {
    console.error('发送通知失败:', error)
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchNotifications()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.notification-card {
  margin-bottom: 8px;
}

.notification-card.unread {
  border-left: 4px solid #409EFF;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-title {
  font-weight: bold;
  display: flex;
  align-items: center;
}

.notification-content {
  color: #606266;
  line-height: 1.6;
}

.notification-content.markdown-body :deep(p) {
  margin: 0.5em 0;
}

.notification-content.markdown-body :deep(strong) {
  font-weight: 600;
  color: #303133;
}

.notification-content.markdown-body :deep(em) {
  font-style: italic;
}

.notification-content.markdown-body :deep(ul),
.notification-content.markdown-body :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.notification-content.markdown-body :deep(li) {
  margin: 0.3em 0;
}

.notification-content.markdown-body :deep(h1),
.notification-content.markdown-body :deep(h2),
.notification-content.markdown-body :deep(h3),
.notification-content.markdown-body :deep(h4) {
  margin: 0.8em 0 0.4em;
  color: #303133;
  font-weight: 600;
}

.notification-content.markdown-body :deep(code) {
  background-color: #f5f7fa;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.notification-content.markdown-body :deep(pre) {
  background-color: #f5f7fa;
  padding: 1em;
  border-radius: 4px;
  overflow-x: auto;
}

.notification-content.markdown-body :deep(blockquote) {
  border-left: 4px solid #dcdfe6;
  margin: 0.5em 0;
  padding-left: 1em;
  color: #909399;
}

.notification-content.markdown-body :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.notification-content.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.notification-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 16px;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .el-card__body {
    padding: 12px;
  }
  
  .notification-card {
    margin-bottom: 8px;
  }
  
  .notification-card :deep(.el-card__body) {
    padding: 12px;
  }
  
  .notification-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .notification-title {
    font-size: 14px;
  }
  
  .notification-content {
    font-size: 13px;
  }
  
  .notification-footer {
    flex-direction: column;
    gap: 4px;
    font-size: 11px;
  }
  
  .el-dialog {
    width: 95% !important;
    margin: 10px auto;
  }
}
</style>
