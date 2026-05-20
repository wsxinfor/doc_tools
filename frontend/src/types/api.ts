export interface ApiResponse<T> {
  data: T
  message: string
}

export interface ApiError {
  code: string
  message: string
  detail: string | null
}

export interface User {
  id: string
  username: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Document {
  id: string
  filename: string
  file_path: string | null
  file_type: 'docx' | 'md' | 'txt'
  source_type: 'file' | 'text'
  content: string | null
  file_size: number
  uploader_id: string
  is_deleted: boolean
  created_at: string
}

export interface Template {
  id: string
  name: string
  description: string | null
  config: Record<string, unknown>
  created_by: string
  created_at: string
  updated_at: string
}

export interface RenderTask {
  id: string
  document_id: string
  template_id: string
  status: 'pending' | 'processing' | 'done' | 'failed'
  result_path: string | null
  preview_path: string | null
  error_message: string | null
  created_by: string
  created_at: string
  updated_at: string
}

export interface Section {
  level: number
  text: string
  paragraph_type: 'heading' | 'body' | 'table' | 'image'
  children: Section[]
  table_data?: {
    rows: string[][]
  }
  image_path?: string
}

export interface AiStructure {
  title: string
  sections: Section[]
}
