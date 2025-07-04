/**
 * 结果管理API
 */
import client from './client'
import type { ApiResponse, TaskResult } from '@/types'

export const resultApi = {
  /**
   * 获取任务结果
   */
  async getTaskResults(taskId: string): Promise<ApiResponse<{ results: TaskResult[] }>> {
    const response = await client.get<ApiResponse<{ results: TaskResult[] }>>(`/results/${taskId}`)
    return response.data
  },

  /**
   * 下载结果文件
   */
  async downloadResult(taskId: string, resultId: string): Promise<void> {
    const response = await client.get(`/results/${taskId}/download/${resultId}`, {
      responseType: 'blob',
    })
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition']
    let filename = 'result'
    if (contentDisposition) {
      const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match && match[1]) {
        filename = match[1].replace(/['"]/g, '')
      }
    }
    
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  /**
   * 下载所有结果（压缩包）
   */
  async downloadAllResults(taskId: string): Promise<void> {
    const response = await client.get(`/results/${taskId}/download-all`, {
      responseType: 'blob',
    })
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 默认文件名
    const filename = `task_${taskId}_results.zip`
    
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  },

  /**
   * 预览结果内容
   */
  async previewResult(taskId: string, resultId: string): Promise<ApiResponse<{ content: string, content_type: string }>> {
    const response = await client.get<ApiResponse<{ content: string, content_type: string }>>(`/results/${taskId}/preview/${resultId}`)
    return response.data
  }
} 