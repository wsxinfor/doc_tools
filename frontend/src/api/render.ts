import client from './client'
import type { ApiResponse, RenderTask, AiStructure } from '../types/api'

export interface CreateRenderPayload {
  document_id: string
  template_id: string
  ai_clean_result?: string  // 已废弃，后端现在从 ai_structure 提取正文
  ai_structure: AiStructure
  render_params: {
    client_name: string
    project_name: string
    doc_version: string
    date: string
  }
}

export const createRenderTask = (payload: CreateRenderPayload) =>
  client.post<ApiResponse<RenderTask>>('/render', payload).then((r) => r.data.data)

export const getRenderStatus = (id: string) =>
  client.get<ApiResponse<RenderTask>>(`/render/${id}/status`).then((r) => r.data.data)

export const getRenderList = () =>
  client.get<ApiResponse<RenderTask[]>>('/render').then((r) => r.data.data)

export const getPreviewUrl = (id: string) => `/api/render/${id}/preview`

export const getDownloadUrl = (id: string) => `/api/render/${id}/download`

export const downloadRender = (id: string, token: string) => {
  const a = document.createElement('a')
  a.href = `/api/render/${id}/download`
  // Trigger via fetch with auth header to stream download
  fetch(`/api/render/${id}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  })
    .then((res) => res.blob())
    .then((blob) => {
      const url = URL.createObjectURL(blob)
      a.href = url
      a.download = `document_${id}.docx`
      a.click()
      URL.revokeObjectURL(url)
    })
}
