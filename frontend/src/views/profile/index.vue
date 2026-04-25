<template>
  <div class="profile-page">
    <el-row :gutter="20">
      <el-col :span="8">
        <!-- 个人信息卡片 -->
        <el-card>
          <div class="profile-header">
            <el-avatar :size="80" :icon="UserFilled" />
            <h3>{{ userStore.userInfo?.name || userStore.username }}</h3>
            <el-tag :type="userStore.isTeacher ? 'success' : 'primary'" size="large">
              {{ userStore.isTeacher ? '教师' : '学生' }}
            </el-tag>
          </div>
          <el-divider />
          <div class="profile-info">
            <div class="info-item">
              <span class="label">用户名</span>
              <span class="value">{{ userStore.userInfo?.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">角色</span>
              <span class="value">{{ userStore.userInfo?.role }}</span>
            </div>
            <div class="info-item" v-if="userStore.userInfo?.student_no">
              <span class="label">学号</span>
              <span class="value">{{ userStore.userInfo?.student_no }}</span>
            </div>
            <div class="info-item" v-if="userStore.userInfo?.department">
              <span class="label">院系</span>
              <span class="value">{{ userStore.userInfo?.department }}</span>
            </div>
            <div class="info-item" v-if="userStore.userInfo?.major">
              <span class="label">专业</span>
              <span class="value">{{ userStore.userInfo?.major }}</span>
            </div>
            <div class="info-item" v-if="userStore.userInfo?.phone">
              <span class="label">电话</span>
              <span class="value">{{ userStore.userInfo?.phone }}</span>
            </div>
            <div class="info-item" v-if="userStore.userInfo?.email">
              <span class="label">邮箱</span>
              <span class="value">{{ userStore.userInfo?.email }}</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <!-- 账户设置 -->
        <el-card>
          <template #header>
            <div class="card-header">
              <span>账户设置</span>
            </div>
          </template>
          <el-form label-width="120px">
            <el-form-item label="修改密码">
              <el-button type="primary" @click="showChangePassword = true">
                修改密码
              </el-button>
            </el-form-item>
            <el-form-item label="退出登录">
              <el-button type="danger" @click="handleLogout">
                退出登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 数据统计 -->
        <el-card style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>数据统计</span>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.borrows }}</div>
                <div class="stat-label">图书借阅</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.reservations }}</div>
                <div class="stat-label">场地预约</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.tasks }}</div>
                <div class="stat-label">完成任务</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 修改密码对话框 -->
    <change-password-dialog v-model="showChangePassword" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UserFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getBorrows } from '@/api/library'
import { getReservations } from '@/api/reservation'
import { getTasks } from '@/api/task'
import ChangePasswordDialog from '@/layouts/components/ChangePasswordDialog.vue'

const router = useRouter()
const userStore = useUserStore()
const showChangePassword = ref(false)
const stats = ref({
  borrows: 0,
  reservations: 0,
  tasks: 0
})

const fetchStats = async () => {
  try {
    const [borrowRes, reservationRes, taskRes] = await Promise.all([
      getBorrows(),
      getReservations(),
      getTasks()
    ])
    
    if (borrowRes.code === 200) {
      stats.value.borrows = borrowRes.data.items?.length || 0
    }
    if (reservationRes.code === 200) {
      stats.value.reservations = reservationRes.data.items?.length || 0
    }
    if (taskRes.code === 200) {
      const tasks = taskRes.data.items || []
      stats.value.tasks = tasks.filter(t => t.is_completed).length
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    userStore.logout()
    ElMessage.success('退出成功')
    router.push('/login')
  })
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.profile-page {
  padding-bottom: 20px;
}

.profile-header {
  text-align: center;
  padding: 20px 0;
}

.profile-header h3 {
  margin: 16px 0 8px;
  font-size: 20px;
}

.profile-info {
  padding: 0 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item .label {
  color: #909399;
}

.info-item .value {
  color: #303133;
  font-weight: 500;
}

.card-header {
  font-weight: bold;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  line-height: 1;
}

.stat-label {
  margin-top: 8px;
  color: #909399;
  font-size: 14px;
}
</style>
