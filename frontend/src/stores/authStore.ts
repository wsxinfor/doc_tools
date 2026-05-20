import { create } from 'zustand'
import type { User } from '../types/api'

interface AuthState {
  user: User | null
  token: string | null
  setAuth: (user: User, token: string) => void
  logout: () => void
}

const storedToken = localStorage.getItem('token')
const storedUser = localStorage.getItem('user')

export const useAuthStore = create<AuthState>((set) => ({
  user: storedUser ? (JSON.parse(storedUser) as User) : null,
  token: storedToken,
  setAuth: (user, token) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ user, token })
  },
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ user: null, token: null })
  },
}))
