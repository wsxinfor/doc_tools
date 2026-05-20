import client from './client'
import type { ApiResponse, Document } from '../types/api'

export const uploadDocument = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return client
    .post<ApiResponse<Document>>('/documents/upload', formData)
    .then((r) => r.data.data)
}

/**
 * 从文本创建文档（粘贴文本模式）
 * @param filename 文件名
 * @param content 文本内容
 * @param fileType 文件类型（'md' | 'txt'），为空时自动检测
 */
export const createDocumentFromText = (
  filename: string,
  content: string,
  fileType?: 'md' | 'txt'
) => {
  // 自动检测 MD 格式
  const detectMarkdown = (text: string): boolean => {
    const patterns = [
      /^#{1,6}\s+/m,           // 标题
      /\*\*.*?\*\*/,           // 粗体
      /\*.*?\*/,               // 斜体
      /\[.*?\]\(.*?\)/,        // 链接
      /^\|.*\|/m,              // 表格
      /^```/m,                 // 代码块
      /^[\-\*]\s+/m,           // 无序列表
      /^\d+\.\s+/m,            // 有序列表
      /^>\s+/m,                // 引用
    ]
    return patterns.some(p => p.test(text))
  }

  const detectedType = fileType || (detectMarkdown(content) ? 'md' : 'txt')

  return client
    .post<ApiResponse<Document>>('/documents', {
      filename,
      file_type: detectedType,
      source_type: 'text',
      content,
      file_size: content.length,
    })
    .then((r) => r.data.data)
}

export const getDocuments = () =>
  client.get<ApiResponse<Document[]>>('/documents').then((r) => r.data.data)

export const getDocument = (id: string) =>
  client.get<ApiResponse<Document>>(`/documents/${id}`).then((r) => r.data.data)

export const deleteDocument = (id: string) =>
  client.delete(`/documents/${id}`).then((r) => r.data)
