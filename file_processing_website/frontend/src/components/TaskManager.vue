<template>
  <div class="task-manager">
    <div class="task-header">
      <h3>任务管理</h3>
      <el-button @click="refreshTasks" :loading="loading">
        <el-icon><refresh /></el-icon>
        刷新
      </el-button>
    </div>
    
    <div v-if="tasks.length === 0" class="empty-state">
      <el-empty description="暂无任务" />
    </div>
    
    <div v-else class="task-list">
      <el-card 
        class="task-card" 
        v-for="task in tasks" 
        :key="task.task_id"
        shadow="hover"
      >
        <template #header>
          <div class="card-header">
            <span class="task-title">{{ getTaskTitle(task) }}</span>
            <el-tag :type="getStatusType(task.status)" size="small">
              {{ getStatusText(task.status) }}
            </el-tag>
          </div>
        </template>
        
        <div class="task-content">
          <div class="task-info">
            <div class="info-item">
              <el-icon><document /></el-icon>
              <span>文件数量: {{ task.file_ids.length }}</span>
            </div>
            <div class="info-item">
              <el-icon><clock /></el-icon>
              <span>创建时间: {{ formatTime(task.created_time) }}</span>
            </div>
            <div class="info-item" v-if="task.progress.current_step">
              <el-icon><loading /></el-icon>
              <span>当前步骤: {{ task.progress.current_step }}</span>
            </div>
            <div class="info-item" v-if="task.progress.estimated_remaining">
              <el-icon><timer /></el-icon>
              <span>预计剩余: {{ task.progress.estimated_remaining }}秒</span>
            </div>
          </div>
          
          <div class="task-progress" v-if="task.status === 'running'">
            <div class="progress-info">
              <span>进度: {{ Math.round(task.progress.progress_percent) }}%</span>
              <span>{{ task.progress.processed_files }}/{{ task.progress.total_files }} 文件</span>
            </div>
            <el-progress 
              :percentage="Math.round(task.progress.progress_percent)"
              :status="task.status === 'failed' ? 'exception' : undefined"
              striped
              striped-flow
            />
          </div>
          
          <div class="task-actions">
            <el-button 
              v-if="task.status === 'completed'" 
              type="primary" 
              size="small"
              @click="viewResults(task.task_id)"
            >
              <el-icon><view /></el-icon>
              查看结果
            </el-button>
            
            <el-button 
              v-if="task.status === 'completed'" 
              type="success" 
              size="small"
              @click="downloadResults(task.task_id)"
            >
              <el-icon><download /></el-icon>
              下载结果
            </el-button>
            
            <el-button 
              v-if="task.status === 'failed'" 
              type="warning" 
              size="small"
              @click="retryTask(task.task_id)"
            >
              <el-icon><refresh /></el-icon>
              重试
            </el-button>
            
            <el-button 
              v-if="['pending', 'running'].includes(task.status)" 
              type="danger" 
              size="small"
              @click="cancelTask(task.task_id)"
            >
              <el-icon><close /></el-icon>
              取消
            </el-button>
          </div>
          
          <div v-if="task.error_message" class="error-message">
            <el-alert
              :title="task.error_message"
              type="error"
              :closable="false"
              show-icon
            />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, 
  Document, 
  Clock, 
  Loading, 
  Timer, 
  View, 
  Download, 
  Close 
} from '@element-plus/icons-vue'
import type { TaskInfo } from '@/types'
import { TaskStatus, TaskType } from '@/types'
import { taskApi, resultApi } from '@/api'

// Emits
const emit = defineEmits<{
  'view-results': [taskId: string]
}>()

// State
const tasks = ref<TaskInfo[]>([])
const loading = ref(false)
const wsConnections = ref<Map<string, WebSocket>>(new Map())

// Methods
const loadTasks = async () => {
  try {
    loading.value = true
    const response = await taskApi.getTasks()
    tasks.value = response.data?.tasks || []
    
    // 为运行中的任务建立WebSocket连接
    tasks.value.forEach(task => {
      if (task.status === TaskStatus.RUNNING) {
        connectWebSocket(task.task_id)
      }
    })
  } catch (error) {
    console.error('加载任务列表失败:', error)
    ElMessage.error('加载任务列表失败')
  } finally {
    loading.value = false
  }
}

const refreshTasks = () => {
  loadTasks()
}

const connectWebSocket = (taskId: string) => {
  if (wsConnections.value.has(taskId)) {
    return // 已经连接
  }
  
  const ws = new WebSocket(`ws://localhost:8000/ws/tasks/${taskId}`)
  
  ws.onopen = () => {
    console.log(`WebSocket connected for task ${taskId}`)
  }
  
  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data)
      if (message.type === 'progress_update') {
        updateTaskProgress(message.data)
      }
    } catch (error) {
      console.error('WebSocket message parse error:', error)
    }
  }
  
  ws.onclose = () => {
    console.log(`WebSocket disconnected for task ${taskId}`)
    wsConnections.value.delete(taskId)
  }
  
  ws.onerror = (error) => {
    console.error(`WebSocket error for task ${taskId}:`, error)
  }
  
  wsConnections.value.set(taskId, ws)
}

const updateTaskProgress = (data: any) => {
  const task = tasks.value.find(t => t.task_id === data.task_id)
  if (task) {
    // 更新任务状态和进度
    Object.assign(task, data)
    
    // 如果任务完成，关闭WebSocket连接
    if (data.status === TaskStatus.COMPLETED || data.status === TaskStatus.FAILED) {
      const ws = wsConnections.value.get(data.task_id)
      if (ws) {
        ws.close()
        wsConnections.value.delete(data.task_id)
      }
    }
  }
}

const viewResults = (taskId: string) => {
  emit('view-results', taskId)
}

const downloadResults = async (taskId: string) => {
  try {
    await resultApi.downloadAllResults(taskId)
    ElMessage.success('下载开始')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

const retryTask = async (taskId: string) => {
  try {
    await taskApi.retryTask(taskId)
    ElMessage.success('任务重试已开始')
    await loadTasks()
  } catch (error) {
    console.error('重试任务失败:', error)
    ElMessage.error('重试任务失败')
  }
}

const cancelTask = async (taskId: string) => {
  try {
    await ElMessageBox.confirm('确定要取消这个任务吗？', '确认取消', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    await taskApi.cancelTask(taskId)
    ElMessage.success('任务已取消')
    await loadTasks()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消任务失败:', error)
      ElMessage.error('取消任务失败')
    }
  }
}

// Helper functions
const getTaskTitle = (task: TaskInfo): string => {
  const typeMap = {
    [TaskType.FULL]: '完整解析',
    [TaskType.TEXT]: '文本提取',
    [TaskType.FORMULA]: '公式识别',
    [TaskType.TABLE]: '表格识别',
  }
  return `${typeMap[task.task_type]} - ${task.task_id.slice(0, 8)}`
}

const getStatusType = (status: TaskStatus): string => {
  const typeMap = {
    [TaskStatus.PENDING]: 'info',
    [TaskStatus.RUNNING]: 'warning',
    [TaskStatus.COMPLETED]: 'success',
    [TaskStatus.FAILED]: 'danger',
    [TaskStatus.CANCELLED]: 'info',
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status: TaskStatus): string => {
  const textMap = {
    [TaskStatus.PENDING]: '等待中',
    [TaskStatus.RUNNING]: '运行中',
    [TaskStatus.COMPLETED]: '已完成',
    [TaskStatus.FAILED]: '失败',
    [TaskStatus.CANCELLED]: '已取消',
  }
  return textMap[status] || status
}

const formatTime = (timeStr: string): string => {
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

// Lifecycle
onMounted(() => {
  loadTasks()
})

onUnmounted(() => {
  // 关闭所有WebSocket连接
  wsConnections.value.forEach(ws => {
    ws.close()
  })
  wsConnections.value.clear()
})
</script>

<style scoped>
.task-manager {
  width: 100%;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.task-header h3 {
  margin: 0;
  color: #303133;
}

.empty-state {
  padding: 40px;
  text-align: center;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-card {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-title {
  font-weight: 500;
  color: #303133;
}

.task-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

.task-progress {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.task-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.error-message {
  margin-top: 8px;
}
</style> 