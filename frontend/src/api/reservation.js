import request from '@/utils/request'

export const getVenues = () => {
  return request.get('/reservations/venues')
}

export const getReservations = () => {
  return request.get('/reservations/')
}

export const createReservation = (data) => {
  return request.post('/reservations/', data)
}

export const approveReservation = (id, data) => {
  return request.post(`/reservations/${id}/approve`, data)
}
