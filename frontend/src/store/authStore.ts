import { create } from 'zustand'
import api from '@/lib/api'

interface User {
  id: string
  email: string
  display_name: string
  phone_number?: string | null
  profile_image_url?: string | null
  google_id?: string | null
  is_verified: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: {
    email: string
    password?: string
    display_name: string
    phone_number?: string
  }) => Promise<void>
  googleAuth: (token: string) => Promise<void>
  logout: () => Promise<void>
  fetchUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,

  fetchUser: async () => {
    try {
      const res = await api.get('/auth/me')
      set({ user: res.data, isLoading: false })
    } catch {
      // No backend or not logged in – still set loading to false
      set({ user: null, isLoading: false })
    }
  },

  login: async (email, password) => {
    await api.post('/auth/login', { email, password })
    const userRes = await api.get('/auth/me')
    set({ user: userRes.data })
  },

  register: async (data) => {
    await api.post('/auth/register', data)
    if (data.password) {
      await api.post('/auth/login', { email: data.email, password: data.password })
    }
    const userRes = await api.get('/auth/me')
    set({ user: userRes.data })
  },

  googleAuth: async (token) => {
    await api.post('/auth/google', { token })
    const userRes = await api.get('/auth/me')
    set({ user: userRes.data })
  },

  logout: async () => {
    try {
      await api.post('/auth/logout')
    } catch {}
    set({ user: null })
  },
}))