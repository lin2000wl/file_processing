<template>
  <div class="home-view">
    <div class="header">
      <h1>MonkeyOCR 文件处理平台</h1>
      <p>基于深度学习的智能文档解析系统</p>
    </div>
    
    <div class="main-content">
      <el-row :gutter="24">
        <!-- 左侧：文件上传区域 -->
        <el-col :span="12">
          <el-card class="upload-section" shadow="hover">
            <template #header>
              <h3>
                <el-icon><upload-filled /></el-icon>
                文件上传
              </h3>
            </template>
            
            <FileUploader 
              @upload-success="onUploadSuccess"
              @upload-error="onUploadError"
              @upload-progress="onUploadProgress"
            />
            
            <div class="upload-options" v-if="uploadedFiles.length > 0">
              <h4>处理选项</h4>
              <el-form :model="processOptions" label-width="100px" size="small">
                <el-form-item label="任务类型">
                  <el-radio-group v-model="processOptions.taskType">
                    <el-radio :value="TaskType.FULL">完整解析</el-radio>
                    <el-radio :value="TaskType.TEXT">文本提取</el-radio>
                    <el-radio :value="TaskType.FORMULA">公式识别</el-radio>
                    <el-radio :value="TaskType.TABLE">表格识别</el-radio>
                  </el-radio-group>
                </el-form-item>
                
                <el-form-item label="分页处理">
                  <el-switch v-model="processOptions.splitPages" />
                </el-form-item>
                
                <el-form-item label="输出格式">
                  <el-select v-model="processOptions.outputFormat">
                    <el-option label="Markdown" value="markdown" />
                    <el-option label="HTML" value="html" />
                    <el-option label="JSON" value="json" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="语言">
                  <el-select v-model="processOptions.language">
                    <el-option label="自动检测" value="auto" />
                    <el-option label="中文" value="zh" />
                    <el-option label="英文" value="en" />
                  </el-select>
                </el-form-item>
                
                <el-form-item>
                  <el-button 
                    type="primary" 
                    @click="startProcessing"
                    :loading="processing"
                    :disabled="uploadedFiles.length === 0"
                  >
                    开始处理
                  </el-button>
                  <el-button 
                    type="default" 
                    @click="clearUploadedFiles"
                    :disabled="uploadedFiles.length === 0"
                  >
                    清空列表
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-card>
        </el-col>
        
        <!-- 右侧：任务管理区域 -->
        <el-col :span="12">
          <el-card class="task-section" shadow="hover">
            <template #header>
              <h3>
                <el-icon><list /></el-icon>
                任务管理
              </h3>
            </template>
            
            <TaskManager @view-results="onViewResults" />
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 结果查看对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="任务结果"
      width="80%"
      :destroy-on-close="true"
    >
      <div v-if="currentResults.length > 0">
        <div v-for="result in currentResults" :key="result.file_id" class="result-item">
          <h4>{{ result.filename }}</h4>
          <el-button size="small" @click="downloadSingleResult(result)">
            下载
          </el-button>
          <el-button size="small" @click="previewResult(result)">
            预览
          </el-button>
        </div>
      </div>
      <div v-else>
        <el-empty description="暂无结果" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, List } from '@element-plus/icons-vue'
import FileUploader from '@/components/FileUploader.vue'
import TaskManager from '@/components/TaskManager.vue'
import type { FileInfo, TaskResult } from '@/types'
import { TaskType } from '@/types'
import { taskApi, resultApi } from '@/api'

// State
const uploadedFiles = ref<FileInfo[]>([])
const processing = ref(false)
const resultDialogVisible = ref(false)
const currentResults = ref<TaskResult[]>([])

// 处理选项
const processOptions = reactive({
  taskType: TaskType.FULL,
  splitPages: false,
  outputFormat: 'markdown',
  language: 'auto'
})

// Methods
const onUploadSuccess = (files: FileInfo[]) => {
  uploadedFiles.value.push(...files)
  ElMessage.success(`成功上传 ${files.length} 个文件`)
}

const onUploadError = (error: string) => {
  ElMessage.error(`上传失败: ${error}`)
}

const onUploadProgress = (progress: number) => {
  // 可以在这里显示上传进度
}

const startProcessing = async () => {
  if (uploadedFiles.value.length === 0) {
    ElMessage.warning('请先上传文件')
    return
  }
  
  try {
    processing.value = true
    
    const fileIds = uploadedFiles.value.map(file => file.file_id)
    const options = {
      split_pages: processOptions.splitPages,
      output_format: processOptions.outputFormat,
      language: processOptions.language,
      custom_params: {}
    }
    
    const response = await taskApi.createTask(fileIds, processOptions.taskType, options)
    
    ElMessage.success('任务创建成功，开始处理...')
    
    // 不立即清空文件列表，让用户可以看到哪些文件正在处理
    // 可以在任务完成后再清空，或者添加一个手动清空按钮
    
  } catch (error) {
    console.error('创建任务失败:', error)
    ElMessage.error('创建任务失败')
  } finally {
    processing.value = false
  }
}

const onViewResults = async (taskId: string) => {
  try {
    const response = await resultApi.getTaskResults(taskId)
    currentResults.value = response.data?.results || []
    resultDialogVisible.value = true
  } catch (error) {
    console.error('获取结果失败:', error)
    ElMessage.error('获取结果失败')
  }
}

const downloadSingleResult = async (result: TaskResult) => {
  try {
    // 这里需要根据实际API调整
    window.open(result.download_url, '_blank')
    ElMessage.success('下载开始')
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

const previewResult = async (result: TaskResult) => {
  try {
    // 这里可以实现预览功能
    ElMessage.info('预览功能待实现')
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('预览失败')
  }
}

const clearUploadedFiles = () => {
  uploadedFiles.value = []
  ElMessage.success('已清空上传文件列表')
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
  padding: 20px;
  background-color: #f5f7fa;
}

.header {
  text-align: center;
  margin-bottom: 40px;
}

.header h1 {
  color: #303133;
  margin-bottom: 8px;
  font-size: 2.5em;
  font-weight: 600;
}

.header p {
  color: #606266;
  font-size: 1.2em;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
}

.upload-section,
.task-section {
  height: 100%;
  min-height: 600px;
}

.upload-section .el-card__header h3,
.task-section .el-card__header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #303133;
}

.upload-options {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

.upload-options h4 {
  margin-bottom: 16px;
  color: #303133;
}

.result-item {
  padding: 16px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-item h4 {
  margin: 0;
  color: #303133;
}

@media (max-width: 768px) {
  .main-content .el-col {
    margin-bottom: 20px;
  }
}
</style>
