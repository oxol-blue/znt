import request from '@/utils/request'

export const getTasks = () => {
  return request.get('/tasks/')
}

export const createTask = (data) => {
  return request.post('/tasks/', data)
}

export const completeTask = (id) => {
  return request.post(`/tasks/${id}/complete`)
}
