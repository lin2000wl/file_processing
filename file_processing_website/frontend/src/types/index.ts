/**
 * 应用类型定义
 */

// 文件状态枚举
export enum FileStatus {
  UPLOADED = 'uploaded',
  PROCESSING = 'processing', 
  COMPLETED = 'completed',
  ERROR = 'error',
  DELETED = 'deleted'
}

// 任务状态枚举
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// 任务类型枚举
export enum TaskType {
  FULL = 'full',
  TEXT = 'text',
  FORMULA = 'formula',
  TABLE = 'table'
}

// 文件信息接口
export interface FileInfo {
  file_id: string
  filename: string
  original_filename: string
  size: number
  content_type: string
  extension: string
  storage_path: string
  upload_time: string
  status: FileStatus
  error_message?: string
  session_id?: string
  processing_task_id?: string
  metadata: Record<string, any>
}

// 任务选项接口
export interface TaskOptions {
  split_pages: boolean
  output_format: string
  language: string
  custom_params: Record<string, any>
}

// 任务进度接口
export interface TaskProgress {
  current_step: string
  progress_percent: number
  processed_files: number
  total_files: number
  estimated_remaining?: number
}

// 任务结果接口
export interface TaskResult {
  file_id: string
  filename: string
  content_type: string
  size: number
  download_url: string
}

// 任务摘要接口
export interface TaskSummary {
  total_files: number
  processed_files: number
  failed_files: number
  processing_time: number
}

// 任务信息接口
export interface TaskInfo {
  task_id: string
  task_type: TaskType
  file_ids: string[]
  options: TaskOptions
  status: TaskStatus
  progress: TaskProgress
  created_time: string
  started_time?: string
  completed_time?: string
  results: TaskResult[]
  summary?: TaskSummary
  error_message?: string
  error_details?: Record<string, any>
  session_id?: string
  metadata: Record<string, any>
}

// 会话信息接口
export interface SessionInfo {
  session_id: string
  created_time: string
  last_activity: string
  file_ids: string[]
  task_ids: string[]
  client_ip?: string
  user_agent?: string
  is_active: boolean
  uploaded_files_count: number
  completed_tasks_count: number
  metadata: Record<string, any>
}

// API响应接口
export interface ApiResponse<T = any> {
  success: boolean
  message: string
  data?: T
  error_code?: string
}

// 文件上传响应接口
export interface UploadResponse {
  files: FileInfo[]
}

// 任务创建响应接口
export interface TaskCreateResponse {
  task_id: string
  status: TaskStatus
  created_time: string
  estimated_time?: number
}

// WebSocket消息接口
export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
} 