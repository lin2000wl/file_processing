/**
 * 文件管理API
 */
import client from './client'
import type { ApiResponse, FileInfo, UploadResponse } from '@/types'

export const fileApi = {
  /**
   * 上传文件
   */
  async uploadFiles(files: File[]): Promise<ApiResponse<UploadResponse>> {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    
    const response = await client.post<ApiResponse<UploadResponse>>(
      '/files/upload',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 60000, // 上传超时时间60秒
      }
    )
    
    return response.data
  },

  /**
   * 获取文件信息
   */
  async getFileInfo(fileId: string): Promise<ApiResponse<FileInfo>> {
    const response = await client.get<ApiResponse<FileInfo>>(`/files/${fileId}`)
    return response.data
  },

  /**
   * 获取文件列表
   */
  async getFiles(sessionId?: string): Promise<ApiResponse<{ files: FileInfo[] }>> {
    const params = sessionId ? { session_id: sessionId } : {}
    const response = await client.get<ApiResponse<{ files: FileInfo[] }>>('/files', { params })
    return response.data
  },

  /**
   * 删除文件
   */
  async deleteFile(fileId: string): Promise<ApiResponse> {
    const response = await client.delete<ApiResponse>(`/files/${fileId}`)
    return response.data
  },

  /**
   * 下载文件
   */
  async downloadFile(fileId: string): Promise<void> {
    const response = await client.get(`/files/${fileId}/download`, {
      responseType: 'blob',
    })
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition']
    let filename = 'download'
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
  }
} 