<template>
  <el-dialog
    v-model="visible"
    title="添加图书"
    width="500px"
    :close-on-click-modal="false"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="书名" prop="title">
        <el-input v-model="form.title" placeholder="请输入书名" />
      </el-form-item>
      
      <el-form-item label="作者" prop="author">
        <el-input v-model="form.author" placeholder="请输入作者" />
      </el-form-item>
      
      <el-form-item label="ISBN" prop="isbn">
        <el-input v-model="form.isbn" placeholder="请输入ISBN" />
      </el-form-item>
      
      <el-form-item label="出版社" prop="publisher">
        <el-input v-model="form.publisher" placeholder="请输入出版社" />
      </el-form-item>
      
      <el-form-item label="出版日期" prop="publish_date">
        <el-date-picker
          v-model="form.publish_date"
          type="date"
          placeholder="选择出版日期"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>
      
      <el-form-item label="分类" prop="category">
        <el-select v-model="form.category" placeholder="选择分类" style="width: 100%">
          <el-option label="计算机" value="计算机" />
          <el-option label="文学" value="文学" />
          <el-option label="科学" value="科学" />
          <el-option label="历史" value="历史" />
          <el-option label="艺术" value="艺术" />
          <el-option label="其他" value="其他" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="总库存" prop="total_quantity">
        <el-input-number v-model="form.total_quantity" :min="1" :max="1000" style="width: 100%" />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { createBook } from '@/api/library'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref()
const loading = ref(false)

const form = reactive({
  title: '',
  author: '',
  isbn: '',
  publisher: '',
  publish_date: '',
  category: '',
  total_quantity: 1
})

const rules = {
  title: [{ required: true, message: '请输入书名', trigger: 'blur' }],
  author: [{ required: true, message: '请输入作者', trigger: 'blur' }],
  isbn: [{ required: true, message: '请输入ISBN', trigger: 'blur' }],
  publisher: [{ required: true, message: '请输入出版社', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  total_quantity: [{ required: true, message: '请输入库存', trigger: 'blur' }]
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const res = await createBook({
      ...form,
      available_quantity: form.total_quantity
    })
    
    if (res.code === 200) {
      ElMessage.success('添加成功')
      visible.value = false
      emit('success')
      // 重置表单
      Object.keys(form).forEach(key => {
        form[key] = key === 'total_quantity' ? 1 : ''
      })
    }
  } catch (error) {
    console.error('添加图书失败:', error)
  } finally {
    loading.value = false
  }
}
</script>
