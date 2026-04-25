<template>
  <div class="dashboard">
    <!-- 欢迎卡片 -->
    <el-card class="welcome-card">
      <div class="welcome-content">
        <div>
          <h2>欢迎回来，{{ userStore.userInfo?.name || userStore.username }}！</h2>
          <p class="subtitle">今天是 {{ today }}，祝您工作愉快！</p>
        </div>
        <el-button type="primary" :icon="ChatDotRound" @click="$router.push('/ai-assistant')">
          打开 AI 助手
        </el-button>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import {
  ChatDotRound,
  Collection,
  OfficeBuilding,
  List,
  Bell,
  HomeFilled,
  User
} from '@element-plus/icons-vue'
import { getBorrows } from '@/api/library'
import { getReservations } from '@/api/reservation'
import { getTasks } from '@/api/task'
import { getNotifications, getUnreadCount } from '@/api/notification'
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
</style>
