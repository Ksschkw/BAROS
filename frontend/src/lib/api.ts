import axios from 'axios'
import { useAuthStore } from '@/store/authStore'
import { toast } from 'sonner'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL 
    ? `${import.meta.env.VITE_API_URL}/api/v1` 
    : '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
  timeout: 10000,
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Never retry these endpoints
    if (
      originalRequest.url === '/auth/refresh' ||
      originalRequest.url === '/auth/me' ||
      originalRequest.url === '/auth/logout'
    ) {
      return Promise.reject(error)
    }

    // If 401 and haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        await api.post('/auth/refresh')
        // Refresh succeeded – retry original
        return api(originalRequest)
      } catch {
        // Refresh failed – only redirect if not already on landing page
        useAuthStore.getState().logout()
        if (window.location.pathname !== '/') {
          window.location.href = '/'
        }
        return Promise.reject(error)
      }
    }

    // Handle generic 400 errors (like Solana/USDC errors) with sonner toast
    if (error.response?.status === 400 && error.response?.data?.detail) {
      toast.error(error.response.data.detail)
    }

    return Promise.reject(error)
  }
)

export default api