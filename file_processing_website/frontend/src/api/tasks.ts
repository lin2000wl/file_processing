/**
 * 任务管理API
 */
import client from './client'
import type { ApiResponse, TaskInfo, TaskCreateResponse, TaskOptions } from '@/types'
import { TaskType } from '@/types'

export const taskApi = {
  /**
   * 创建处理任务
   */
  async createTask(
    fileIds: string[],
    taskType: TaskType = TaskType.FULL,
    options?: Partial<TaskOptions>
  ): Promise<ApiResponse<TaskCreateResponse>> {
    const response = await client.post<ApiResponse<TaskCreateResponse>>('/tasks', {
      file_ids: fileIds,
      task_type: taskType,
      options: options || {}
    })
    
    return response.data
  },

  /**
   * 获取任务信息
   */
  async getTask(taskId: string): Promise<ApiResponse<TaskInfo>> {
    const response = await client.get<ApiResponse<TaskInfo>>(`/tasks/${taskId}`)
    return response.data
  },

  /**
   * 获取任务列表
   */
  async getTasks(sessionId?: string): Promise<ApiResponse<{ tasks: TaskInfo[] }>> {
    const params = sessionId ? { session_id: sessionId } : {}
    const response = await client.get<ApiResponse<{ tasks: TaskInfo[] }>>('/tasks', { params })
    return response.data
  },

  /**
   * 取消任务
   */
  async cancelTask(taskId: string): Promise<ApiResponse> {
    const response = await client.post<ApiResponse>(`/tasks/${taskId}/cancel`)
    return response.data
  },

  /**
   * 获取任务状态
   */
  async getTaskStatus(taskId: string): Promise<ApiResponse<{ status: string, progress: number }>> {
    const response = await client.get<ApiResponse<{ status: string, progress: number }>>(`/tasks/${taskId}`)
    return response.data
  },

  /**
   * 重试失败的任务
   */
  async retryTask(taskId: string): Promise<ApiResponse> {
    const response = await client.post<ApiResponse>(`/tasks/${taskId}/retry`)
    return response.data
  }
} 