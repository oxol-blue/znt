<template>
  <div class="tasks-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>任务管理</span>
          <el-button
            v-if="userStore.isTeacher"
            type="primary"
            :icon="Plus"
            @click="showAddDialog = true"
          >
            发布任务
          </el-button>
        </div>
      </template>

      <!-- 任务列表 -->
      <el-table :data="tasks" v-loading="loading" stripe>
        <el-table-column prop="title" label="任务标题" min-width="150" />
        <el-table-column prop="content" label="任务内容" min-width="200" show-overflow-tooltip />
        <el-table-column prop="task_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeType(row.task_type)" size="small">
              {{ getTaskTypeLabel(row.task_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="面向对象" width="100">
          <template #default="{ row }">
            {{ getTargetTypeLabel(row.target_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_date" label="截止日期" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'published'" type="success" size="small">进行中</el-tag>
            <el-tag v-else type="info" size="small">已结束</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="完成状态" width="100" v-if="!userStore.isTeacher">
          <template #default="{ row }">
            <el-tag v-if="row.is_completed" type="success" size="small">已完成</el-tag>
            <el-tag v-else type="warning" size="small">未完成</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!userStore.isTeacher && !row.is_completed && row.status === 'published'"
              type="primary"
              size="small"
              @click="handleComplete(row)"
            >
              完成
            </el-button>
            <el-button
              v-else-if="userStore.isTeacher"
              type="info"
              size="small"
              disabled
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 发布任务对话框 -->
    <el-dialog v-model="showAddDialog" title="发布任务" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="任务标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入任务标题" />
        </el-form-item>
        <el-form-item label="任务内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="请输入任务内容"
          />
        </el-form-item>
        <el-form-item label="任务类型" prop="task_type">
          <el-select v-model="form.task_type" placeholder="选择类型" style="width: 100%">
            <el-option label="日常任务" value="daily" />
            <el-option label="学习任务" value="study" />
            <el-option label="活动任务" value="activity" />
            <el-option label="考试任务" value="exam" />
          </el-select>
        </el-form-item>
        <el-form-item label="面向对象" prop="target_type">
          <el-select v-model="form.target_type" placeholder="选择面向对象" style="width: 100%">
            <el-option label="全体学生" value="all" />
            <el-option label="本科生" value="undergraduate" />
            <el-option label="研究生" value="graduate" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期" prop="start_date">
          <el-date-picker
            v-model="form.start_date"
            type="date"
            placeholder="选择开始日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="截止日期" prop="end_date">
          <el-date-picker
            v-model="form.end_date"
            type="date"
            placeholder="选择截止日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getTasks, createTask, completeTask } from '@/api/task'

const userStore = useUserStore()
const tasks = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const submitting = ref(false)
const formRef = ref()

const form = ref({
  title: '',
  content: '',
  task_type: 'daily',
  target_type: 'all',
  start_date: '',
  end_date: ''
})

const rules = {
  title: [{ required: true, message: '请输入任务标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入任务内容', trigger: 'blur' }],
  task_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  target_type: [{ required: true, message: '请选择面向对象', trigger: 'change' }],
  start_date: [{ required: true, message: '请选择开始日期', trigger: 'change' }],
  end_date: [
    { required: true, message: '请选择截止日期', trigger: 'change' },
    {
      validator: (rule, value, callback) => {
        if (value && form.value.start_date && value < form.value.start_date) {
          callback(new Error('截止日期不能早于开始日期'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}

const getTaskTypeLabel = (type) => {
  const map = {
    daily: '日常任务',
    study: '学习任务',
    activity: '活动任务',
    exam: '考试任务'
  }
  return map[type] || type
}

const getTaskTypeType = (type) => {
  const map = {
    daily: '',
    study: 'success',
    activity: 'warning',
    exam: 'danger'
  }
  return map[type] || ''
}

const getTargetTypeLabel = (type) => {
  const map = {
    all: '全体学生',
    undergraduate: '本科生',
    graduate: '研究生'
  }
  return map[type] || type
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const res = await getTasks()
    if (res.code === 200) {
      tasks.value = res.data.items || []
    }
  } catch (error) {
    console.error('获取任务失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const res = await createTask(form.value)
    if (res.code === 200) {
      ElMessage.success('发布成功')
      showAddDialog.value = false
      fetchTasks()
      form.value = {
        title: '',
        content: '',
        task_type: 'daily',
        target_type: 'all',
        start_date: '',
        end_date: ''
      }
    }
  } catch (error) {
    console.error('发布任务失败:', error)
  } finally {
    submitting.value = false
  }
}

const handleComplete = async (row) => {
  try {
    const res = await completeTask(row.id)
    if (res.code === 200) {
      ElMessage.success('任务完成')
      fetchTasks()
    }
  } catch (error) {
    console.error('完成任务失败:', error)
  }
}

onMounted(() => {
  fetchTasks()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
