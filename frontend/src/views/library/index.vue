<template>
  <div class="library-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>图书管理</span>
          <el-button
            v-if="userStore.isTeacher"
            type="primary"
            :icon="Plus"
            @click="showAddDialog = true"
          >
            添加图书
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索书名或作者"
          :prefix-icon="Search"
          clearable
          @keyup.enter="handleSearch"
          style="width: 300px"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
      </div>

      <!-- 图书列表 -->
      <el-table :data="books" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="书名" min-width="150" />
        <el-table-column prop="author" label="作者" width="120" />
        <el-table-column prop="isbn" label="ISBN" width="140" />
        <el-table-column prop="publisher" label="出版社" width="140" />
        <el-table-column prop="publish_date" label="出版日期" width="100" />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.category }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="库存" width="120">
          <template #default="{ row }">
            <el-progress
              :percentage="Math.round((row.available_quantity / row.total_quantity) * 100)"
              :status="row.available_quantity > 0 ? 'success' : 'exception'"
              :format="() => `${row.available_quantity}/${row.total_quantity}`"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              :disabled="row.available_quantity <= 0"
              @click="handleBorrow(row)"
            >
              借阅
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 借阅记录 -->
    <el-card class="borrow-card">
      <template #header>
        <div class="card-header">
          <span>我的借阅记录</span>
        </div>
      </template>
      <el-table :data="borrows" stripe size="small">
        <el-table-column prop="book_title" label="书名" />
        <el-table-column prop="borrow_date" label="借阅日期" width="120" />
        <el-table-column prop="due_date" label="应还日期" width="120" />
        <el-table-column prop="return_date" label="归还日期" width="120">
          <template #default="{ row }">
            <span v-if="row.return_date">{{ row.return_date }}</span>
            <el-tag v-else type="warning" size="small">未归还</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.return_date" type="success" size="small">已归还</el-tag>
            <el-tag v-else-if="isOverdue(row.due_date)" type="danger" size="small">已逾期</el-tag>
            <el-tag v-else type="primary" size="small">借阅中</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 添加图书对话框 -->
    <add-book-dialog v-model="showAddDialog" @success="fetchBooks" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { getBooks, borrowBook, getBorrows } from '@/api/library'
import AddBookDialog from './components/AddBookDialog.vue'
import dayjs from 'dayjs'

const userStore = useUserStore()
const loading = ref(false)
const books = ref([])
const borrows = ref([])
const searchKeyword = ref('')
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const showAddDialog = ref(false)

const fetchBooks = async () => {
  loading.value = true
  try {
    const res = await getBooks({
      page: page.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value
    })
    if (res.code === 200) {
      books.value = res.data.items || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('获取图书失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchBorrows = async () => {
  try {
    const res = await getBorrows()
    if (res.code === 200) {
      borrows.value = res.data.items || []
    }
  } catch (error) {
    console.error('获取借阅记录失败:', error)
  }
}

const handleSearch = () => {
  page.value = 1
  fetchBooks()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  fetchBooks()
}

const handleCurrentChange = (val) => {
  page.value = val
  fetchBooks()
}

const handleBorrow = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要借阅《${row.title}》吗？`, '确认借阅', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })
    
    const res = await borrowBook({ book_id: row.id })
    if (res.code === 200) {
      ElMessage.success('借阅成功')
      fetchBooks()
      fetchBorrows()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('借阅失败:', error)
    }
  }
}

const isOverdue = (dueDate) => {
  return dayjs(dueDate).isBefore(dayjs(), 'day')
}

onMounted(() => {
  fetchBooks()
  fetchBorrows()
})
</script>

<style scoped>
.library-page {
  padding-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.borrow-card {
  margin-top: 20px;
}

/* 移动端适配 */
@media screen and (max-width: 768px) {
  .library-page .el-card__body {
    padding: 12px;
  }
  
  .search-bar {
    flex-direction: column;
    gap: 8px;
    margin-bottom: 12px;
  }
  
  .search-bar .el-input {
    width: 100% !important;
  }
  
  .search-bar .el-button {
    width: 100%;
  }
  
  .el-table {
    font-size: 12px;
  }
  
  .el-table .cell {
    padding: 4px;
  }
  
  .pagination {
    margin-top: 12px;
  }
  
  .el-pagination {
    justify-content: center;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .borrow-card {
    margin-top: 12px;
  }
  
  .borrow-card .el-card__body {
    padding: 12px;
  }
}
</style>
