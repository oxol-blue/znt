import request from '@/utils/request'

export const getNotifications = () => {
  return request.get('/notifications/')
}

export const getUnreadCount = () => {
  return request.get('/notifications/unread-count')
}

export const createNotification = (data) => {
  return request.post('/notifications/', data)
}

export const markRead = (id) => {
  return request.put(`/notifications/${id}/read`)
}
