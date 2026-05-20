import client from './client'
import type { AiStructure, Section } from '../types/api'

export interface CleanResponse {
  status: 'ok' | 'ai_failed'
  cleaned_text?: string
  original_text?: string
  message?: string
}

export interface ExtractResponse {
  status: 'ok' | 'ai_failed'
  structure?: AiStructure
  message?: string
}

export interface StructureTask {
  id: string
  document_id: string
  status: 'pending' | 'processing' | 'done' | 'failed'
  ai_structure?: AiStructure
  edited_structure?: AiStructure
  error_message?: string
  created_by: string
  created_at: string
  updated_at: string
}

export interface AiSettings {
  provider: 'qwen' | 'openai'
  has_api_key: boolean
  model_url: string
  model_name: string
}

export interface AiTestResult {
  ok: boolean
  message: string
}

export interface UpdateStructureResponse {
  status: string
  message: string
  count: number
}

export interface FindReplaceRequest {
  find: string
  replace: string
  case_sensitive: boolean
  replace_all: boolean
}

export const cleanDocument = (doc_id: string) =>
  client.post<CleanResponse>('/ai/clean', { doc_id }).then((r) => r.data)

// 同步模式：直接从文档提取结构（适用于小文档）
export const extractStructure = (doc_id: string, signal?: AbortSignal) =>
  client
    .post<ExtractResponse>('/ai/extract-structure', { doc_id }, { signal })
    .then((r) => r.data)

// 异步模式：创建结构识别任务（适用于大文档）
export const extractStructureAsync = (doc_id: string) =>
  client
    .post<{ data: StructureTask }>('/ai/extract-structure-async', { document_id: doc_id })
    .then((r) => r.data.data)

// 获取任务状态
export const getStructureTaskStatus = (task_id: string) =>
  client
    .get<{ data: StructureTask }>(`/ai/structure-task/${task_id}/status`)
    .then((r) => r.data.data)

// AI 设置相关（用于管理员页面）
export const getAiSettings = () =>
  client.get<{ data: AiSettings; message: string }>('/admin/settings/ai').then((r) => r.data.data)

export const updateAiSettings = (
  provider: 'qwen' | 'openai',
  api_key: string,
  model_url: string,
  model_name: string,
) =>
  client
    .put('/admin/settings/ai', { provider, api_key, model_url, model_name })
    .then((r) => r.data)

export const testAiSettings = () =>
  client.post<AiTestResult>('/admin/settings/ai/test').then((r) => r.data)

// 更新结构数据（用户编辑后保存）
export const updateStructure = (task_id: string, structure: Section[], title?: string) =>
  client
    .put<UpdateStructureResponse>(`/ai/structure/${task_id}`, { structure, title })
    .then((r) => r.data)

// 查找替换
export const findAndReplace = (
  task_id: string,
  find: string,
  replace: string,
  case_sensitive: boolean = false,
  replace_all: boolean = true,
) =>
  client
    .post<UpdateStructureResponse>(`/ai/structure/${task_id}/find-replace`, {
      find,
      replace,
      case_sensitive,
      replace_all,
    })
    .then((r) => r.data)
