import client from './client'
import type { ApiResponse, TokenResponse, User } from '../types/api'

export const login = (username: string, password: string) =>
  client.post<TokenResponse>('/auth/login', { username, password }).then((r) => r.data)

export const logout = () =>
  client.post('/auth/logout').then((r) => r.data)

export const getMe = () =>
  client.get<ApiResponse<User>>('/auth/me').then((r) => r.data.data)

export const getUsers = () =>
  client.get<ApiResponse<User[]>>('/admin/users').then((r) => r.data.data)

export const createUser = (data: { username: string; password: string; role: 'admin' | 'user' }) =>
  client.post<ApiResponse<User>>('/admin/users', data).then((r) => r.data.data)

export const toggleUser = (id: string) =>
  client.put<ApiResponse<User>>(`/admin/users/${id}/toggle`).then((r) => r.data.data)
