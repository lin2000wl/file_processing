<template>
  <div class="file-uploader">
    <el-upload
      ref="uploadRef"
      class="upload-demo"
      drag
      multiple
      :action="uploadUrl"
      :before-upload="beforeUpload"
      :on-success="onSuccess"
      :on-error="onError"
      :on-progress="onProgress"
      :file-list="fileList"
      :auto-upload="false"
      :show-file-list="true"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持PDF、PNG、JPG格式，单个文件不超过{{ maxSize }}MB，最多{{ maxFiles }}个文件
        </div>
      </template>
    </el-upload>
    
    <div class="upload-actions" v-if="fileList.length > 0">
      <el-button type="primary" @click="submitUpload" :loading="uploading">
        开始上传
      </el-button>
      <el-button @click="clearFiles">清空文件</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import type { UploadFile, UploadFiles, UploadInstance } from 'element-plus'
import { fileApi } from '@/api'

// Props
interface Props {
  maxFiles?: number
  maxSize?: number // MB
  acceptedTypes?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  maxFiles: 20,
  maxSize: 50,
  acceptedTypes: () => ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
})

// Emits
const emit = defineEmits<{
  'upload-success': [files: any[]]
  'upload-error': [error: string]
  'upload-progress': [progress: number]
}>()

// Refs
const uploadRef = ref<UploadInstance>()

// State
const fileList = ref<UploadFiles>([])
const uploading = ref(false)
const uploadUrl = computed(() => '/api/v1/files/upload')

// Methods
const beforeUpload = (file: UploadFile) => {
  // 文件类型检查
  if (!props.acceptedTypes.includes(file.type!)) {
    ElMessage.error(`不支持的文件类型: ${file.type}`)
    return false
  }
  
  // 文件大小检查
  if (file.size! / 1024 / 1024 > props.maxSize) {
    ElMessage.error(`文件 ${file.name} 大小不能超过${props.maxSize}MB`)
    return false
  }
  
  // 文件数量检查
  if (fileList.value.length >= props.maxFiles) {
    ElMessage.error(`最多只能上传${props.maxFiles}个文件`)
    return false
  }
  
  return true
}

const onSuccess = (response: any, file: UploadFile) => {
  if (response.success) {
    emit('upload-success', response.data.files)
    ElMessage.success(`文件 ${file.name} 上传成功`)
  } else {
    emit('upload-error', response.message)
    ElMessage.error(`文件 ${file.name} 上传失败: ${response.message}`)
  }
}

const onError = (error: any, file: UploadFile) => {
  emit('upload-error', `文件 ${file.name} 上传失败`)
  ElMessage.error(`文件 ${file.name} 上传失败`)
  console.error('Upload error:', error)
}

const onProgress = (event: any, file: UploadFile) => {
  const progress = Math.round(event.percent)
  emit('upload-progress', progress)
}

const submitUpload = () => {
  if (!uploadRef.value) return
  
  uploading.value = true
  uploadRef.value.submit()
  
  // 监听上传完成
  const checkComplete = () => {
    const hasUploading = fileList.value.some(file => file.status === 'uploading')
    if (!hasUploading) {
      uploading.value = false
    } else {
      setTimeout(checkComplete, 100)
    }
  }
  
  setTimeout(checkComplete, 100)
}

const clearFiles = () => {
  uploadRef.value?.clearFiles()
  fileList.value = []
}

// 获取文件扩展名
const getFileExtension = (filename: string): string => {
  return filename.split('.').pop()?.toLowerCase() || ''
}

// 验证文件扩展名
const isValidExtension = (filename: string): boolean => {
  const ext = getFileExtension(filename)
  const validExts = ['pdf', 'png', 'jpg', 'jpeg']
  return validExts.includes(ext)
}
</script>

<style scoped>
.file-uploader {
  width: 100%;
}

.upload-demo {
  width: 100%;
}

.upload-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
}

.el-icon--upload {
  font-size: 67px;
  color: #c0c4cc;
  margin: 40px 0 16px;
  line-height: 50px;
}

.el-upload__text {
  color: #606266;
  font-size: 14px;
}

.el-upload__text em {
  color: #409eff;
  font-style: normal;
}

.el-upload__tip {
  color: #606266;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 8px;
}
</style> 