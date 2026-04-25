import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, getProfile } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  // State
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)

  // Getters
  const isLoggedIn = computed(() => !!token.value)
  const isTeacher = computed(() => userInfo.value?.role === 'teacher' || userInfo.value?.role === 'admin')
  const username = computed(() => userInfo.value?.username || '')

  // Actions
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const clearToken = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('token')
  }

  const loginAction = async (credentials) => {
    const res = await login(credentials)
    if (res.code === 200) {
      setToken(res.data.token)
      userInfo.value = res.data.user
      return res
    }
    throw new Error(res.message)
  }

  const fetchUserInfo = async () => {
    if (!token.value) return
    try {
      const res = await getProfile()
      if (res.code === 200) {
        userInfo.value = res.data
        return res.data
      }
    } catch (error) {
      clearToken()
      throw error
    }
  }

  const logout = () => {
    clearToken()
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    isTeacher,
    username,
    setToken,
    clearToken,
    loginAction,
    fetchUserInfo,
    logout
  }
})
