import request from '@/utils/request'

export const getBooks = (params) => {
  return request.get('/library/books', { params })
}

export const createBook = (data) => {
  return request.post('/library/books', data)
}

export const borrowBook = (data) => {
  return request.post('/library/borrow', data)
}

export const getBorrows = () => {
  return request.get('/library/borrows')
}
