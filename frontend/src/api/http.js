import axios from 'axios'
import { clearAuth, getToken } from '../auth'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status
    let message = error.response?.data?.detail || error.message || '请求失败'

    if (error.response?.data instanceof Blob) {
      try {
        const text = await error.response.data.text()
        const parsed = JSON.parse(text)
        message = parsed.detail || message
      } catch {
        // ignore blob parse errors
      }
    }

    if (status === 401) {
      clearAuth()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(
      new Error(typeof message === 'string' ? message : JSON.stringify(message)),
    )
  },
)

export default http
