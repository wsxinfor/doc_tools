import client from './client'
import type { ApiResponse, Template } from '../types/api'

export const getTemplates = () =>
  client.get<ApiResponse<Template[]>>('/templates').then((r) => r.data.data)

export const getTemplate = (id: string) =>
  client.get<ApiResponse<Template>>(`/templates/${id}`).then((r) => r.data.data)

export const createTemplate = (data: { name: string; description?: string; config: Record<string, unknown> }) =>
  client.post<ApiResponse<Template>>('/templates', data).then((r) => r.data.data)

export const updateTemplate = (
  id: string,
  data: { name?: string; description?: string; config?: Record<string, unknown> },
) => client.put<ApiResponse<Template>>(`/templates/${id}`, data).then((r) => r.data.data)

export const deleteTemplate = (id: string) =>
  client.delete(`/templates/${id}`).then((r) => r.data)
