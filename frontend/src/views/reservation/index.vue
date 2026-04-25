<template>
  <div class="reservation-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>场地预约</span>
        </div>
      </template>

      <!-- 场地选择 -->
      <div class="venue-section">
        <h3>选择场地</h3>
        <el-row :gutter="20">
          <el-col :span="8" v-for="venue in venues" :key="venue.id">
            <el-card
              :class="['venue-card', selectedVenue?.id === venue.id ? 'selected' : '']"
              @click="selectVenue(venue)"
              shadow="hover"
            >
              <div class="venue-info">
                <el-icon :size="32" color="#409EFF"><OfficeBuilding /></el-icon>
                <h4>{{ venue.name }}</h4>
                <p class="venue-type">{{ venue.type }}</p>
                <p class="venue-capacity">容纳人数：{{ venue.capacity }}人</p>
                <p class="venue-location">{{ venue.location }}</p>
                <el-tag :type="venue.status === 'available' ? 'success' : 'danger'" size="small">
                  {{ venue.status === 'available' ? '可用' : '维护中' }}
                </el-tag>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 预约表单 -->
      <div v-if="selectedVenue" class="reservation-form">
        <el-divider />
        <h3>预约信息</h3>
        <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="预约日期" prop="reserve_date">
                <el-date-picker
                  v-model="form.reserve_date"
                  type="date"
                  placeholder="选择日期"
                  value-format="YYYY-MM-DD"
                  :disabled-date="disabledDate"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="开始时间" prop="start_time">
                <el-time-picker
                  v-model="form.start_time"
                  placeholder="开始时间"
                  format="HH:mm"
                  value-format="HH:mm"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="结束时间" prop="end_time">
                <el-time-picker
                  v-model="form.end_time"
                  placeholder="结束时间"
                  format="HH:mm"
                  value-format="HH:mm"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="参与人数" prop="participants">
                <el-input-number
                  v-model="form.participants"
                  :min="1"
                  :max="selectedVenue.capacity"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="预约用途" prop="purpose">
                <el-input v-model="form.purpose" placeholder="请输入预约用途" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item>
            <el-button type="primary" @click="handleSubmit" :loading="submitting">提交预约</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 我的预约记录 -->
    <el-card class="reservation-list">
      <template #header>
        <div class="card-header">
          <span>我的预约记录</span>
        </div>
      </template>
      <el-table :data="reservations" stripe>
        <el-table-column prop="venue_name" label="场地" />
        <el-table-column prop="reserve_date" label="预约日期" width="120" />
        <el-table-column prop="start_time" label="开始时间" width="100" />
        <el-table-column prop="end_time" label="结束时间" width="100" />
        <el-table-column prop="purpose" label="用途" />
        <el-table-column prop="participants" label="人数" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'pending'" type="warning" size="small">待审批</el-tag>
            <el-tag v-else-if="row.status === 'approved'" type="success" size="small">已通过</el-tag>
            <el-tag v-else-if="row.status === 'rejected'" type="danger" size="small">已拒绝</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 待审批列表（教师可见） -->
    <el-card class="reservation-list" v-if="userStore.isTeacher">
      <template #header>
        <div class="card-header">
          <span>待审批预约</span>
        </div>
      </template>
      <el-table :data="pendingReservations" stripe>
        <el-table-column prop="applicant_name" label="申请人" />
        <el-table-column prop="venue_name" label="场地" />
        <el-table-column prop="reserve_date" label="预约日期" width="120" />
        <el-table-column prop="start_time" label="时间" width="120">
          <template #default="{ row }">
            {{ row.start_time }} - {{ row.end_time }}
          </template>
        </el-table-column>
        <el-table-column prop="purpose" label="用途" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="success" size="small" @click="handleApprove(row, 'approve')">通过</el-button>
            <el-button type="danger" size="small" @click="handleApprove(row, 'reject')">拒绝</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { OfficeBuilding } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getVenues, getReservations, createReservation, approveReservation } from '@/api/reservation'
import dayjs from 'dayjs'

const userStore = useUserStore()
const venues = ref([])
const reservations = ref([])
const selectedVenue = ref(null)
const submitting = ref(false)
const formRef = ref()

const form = ref({
  reserve_date: '',
  start_time: '',
  end_time: '',
  participants: 1,
  purpose: ''
})

const rules = {
  reserve_date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  purpose: [{ required: true, message: '请输入预约用途', trigger: 'blur' }]
}

const pendingReservations = computed(() => {
  return reservations.value.filter(r => r.status === 'pending')
})

const selectVenue = (venue) => {
  selectedVenue.value = venue
  form.value.participants = Math.min(form.value.participants, venue.capacity)
}

const disabledDate = (time) => {
  return time.getTime() < Date.now() - 86400000
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const res = await createReservation({
      ...form.value,
      venue_id: selectedVenue.value.id
    })
    
    if (res.code === 200) {
      ElMessage.success('预约成功，等待审批')
      resetForm()
      fetchReservations()
    }
  } catch (error) {
    console.error('预约失败:', error)
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    reserve_date: '',
    start_time: '',
    end_time: '',
    participants: 1,
    purpose: ''
  }
  selectedVenue.value = null
}

const handleApprove = async (row, action) => {
  try {
    await ElMessageBox.confirm(`确定要${action === 'approve' ? '通过' : '拒绝'}该预约吗？`, '确认', {
      type: action === 'approve' ? 'success' : 'warning'
    })
    
    const res = await approveReservation(row.id, { action })
    if (res.code === 200) {
      ElMessage.success('操作成功')
      fetchReservations()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('审批失败:', error)
    }
  }
}

const fetchVenues = async () => {
  try {
    const res = await getVenues()
    if (res.code === 200) {
      venues.value = res.data || []
    }
  } catch (error) {
    console.error('获取场地失败:', error)
  }
}

const fetchReservations = async () => {
  try {
    const res = await getReservations()
    if (res.code === 200) {
      reservations.value = res.data.items || []
    }
  } catch (error) {
    console.error('获取预约记录失败:', error)
  }
}

onMounted(() => {
  fetchVenues()
  fetchReservations()
})
</script>

<style scoped>
.reservation-page {
  padding-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.venue-section {
  margin-bottom: 20px;
}

.venue-section h3 {
  margin-bottom: 16px;
  font-size: 16px;
  color: #303133;
}

.venue-card {
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 16px;
}

.venue-card:hover {
  transform: translateY(-5px);
}

.venue-card.selected {
  border: 2px solid #409EFF;
}

.venue-info {
  text-align: center;
}

.venue-info h4 {
  margin: 12px 0 8px;
  font-size: 16px;
}

.venue-type {
  color: #909399;
  font-size: 14px;
  margin: 4px 0;
}

.venue-capacity {
  color: #606266;
  font-size: 13px;
  margin: 4px 0;
}

.venue-location {
  color: #909399;
  font-size: 12px;
  margin: 4px 0 8px;
}

.reservation-form {
  margin-top: 20px;
}

.reservation-form h3 {
  margin-bottom: 20px;
  font-size: 16px;
  color: #303133;
}

.reservation-list {
  margin-top: 20px;
}
</style>
