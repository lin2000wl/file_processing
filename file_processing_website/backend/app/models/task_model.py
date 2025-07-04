"""
任务信息数据模型
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"             # 等待中
    RUNNING = "running"             # 运行中
    COMPLETED = "completed"         # 已完成
    FAILED = "failed"              # 失败
    CANCELLED = "cancelled"         # 已取消


class TaskType(str, Enum):
    """任务类型枚举"""
    FULL = "full"                  # 完整处理
    TEXT = "text"                  # 仅文本识别
    FORMULA = "formula"            # 仅公式识别
    TABLE = "table"                # 仅表格识别


class TaskOptions(BaseModel):
    """任务处理选项"""
    split_pages: bool = Field(default=False, description="是否分页处理")
    output_format: str = Field(default="markdown", description="输出格式")
    language: str = Field(default="auto", description="语言设置")
    custom_params: Dict[str, Any] = Field(default_factory=dict, description="自定义参数")


class TaskProgress(BaseModel):
    """任务进度信息"""
    current_step: str = Field(..., description="当前步骤")
    progress_percent: float = Field(default=0.0, description="进度百分比 (0-1)")
    processed_files: int = Field(default=0, description="已处理文件数")
    total_files: int = Field(default=0, description="总文件数")
    estimated_remaining: Optional[int] = Field(None, description="预计剩余时间（秒）")


class TaskResult(BaseModel):
    """任务结果信息"""
    file_id: str = Field(..., description="结果文件ID")
    filename: str = Field(..., description="结果文件名")
    content_type: str = Field(..., description="文件类型")
    size: int = Field(..., description="文件大小")
    download_url: str = Field(..., description="下载链接")


class TaskSummary(BaseModel):
    """任务摘要统计"""
    total_files: int = Field(..., description="总文件数")
    processed_files: int = Field(..., description="已处理文件数")
    failed_files: int = Field(..., description="失败文件数")
    processing_time: int = Field(..., description="处理时间（秒）")


class TaskInfo(BaseModel):
    """任务信息模型"""
    
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务ID")
    
    # 基本信息
    task_type: TaskType = Field(..., description="任务类型")
    file_ids: List[str] = Field(..., description="文件ID列表")
    options: TaskOptions = Field(default_factory=TaskOptions, description="处理选项")
    
    # 状态信息
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    progress: TaskProgress = Field(default_factory=lambda: TaskProgress(current_step="初始化"), description="进度信息")
    
    # 时间信息
    created_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    started_time: Optional[datetime] = Field(None, description="开始时间")
    completed_time: Optional[datetime] = Field(None, description="完成时间")
    
    # 结果信息
    results: List[TaskResult] = Field(default_factory=list, description="处理结果")
    summary: Optional[TaskSummary] = Field(None, description="任务摘要")
    
    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    
    # 会话信息
    session_id: Optional[str] = Field(None, description="会话ID")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="任务元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_redis_dict(self) -> dict:
        """转换为Redis存储格式"""
        import json
        
        data = {}
        
        # 基本字段
        data['task_id'] = self.task_id
        data['task_type'] = self.task_type.value
        data['file_ids'] = json.dumps(self.file_ids)
        data['status'] = self.status.value
        data['session_id'] = self.session_id or ""
        data['error_message'] = self.error_message or ""
        
        # 时间字段
        data['created_time'] = self.created_time.isoformat()
        data['started_time'] = self.started_time.isoformat() if self.started_time else ""
        data['completed_time'] = self.completed_time.isoformat() if self.completed_time else ""
        
        # 复杂对象序列化为JSON
        data['options'] = json.dumps(self.options.dict() if hasattr(self.options, 'dict') else self.options)
        data['progress'] = json.dumps(self.progress.dict() if hasattr(self.progress, 'dict') else self.progress)
        data['results'] = json.dumps([r.dict() if hasattr(r, 'dict') else r for r in self.results])
        data['metadata'] = json.dumps(self.metadata)
        
        return data
    
    @classmethod
    def from_redis_dict(cls, data: dict) -> 'TaskInfo':
        """从Redis数据创建实例"""
        import json
        
        # 转换基本字段
        kwargs = {
            'task_id': data.get('task_id', ''),
            'task_type': TaskType(data.get('task_type', 'full')),
            'file_ids': json.loads(data.get('file_ids', '[]')),
            'status': TaskStatus(data.get('status', 'pending')),
            'session_id': data.get('session_id') or None,
            'error_message': data.get('error_message') or None,
            'metadata': json.loads(data.get('metadata', '{}'))
        }
        
        # 转换时间字段
        for time_field in ['created_time', 'started_time', 'completed_time']:
            time_str = data.get(time_field, '')
            if time_str:
                kwargs[time_field] = datetime.fromisoformat(time_str)
            else:
                kwargs[time_field] = None
        
        # 转换复杂对象
        try:
            options_data = json.loads(data.get('options', '{}'))
            kwargs['options'] = TaskOptions(**options_data) if options_data else TaskOptions()
        except:
            kwargs['options'] = TaskOptions()
        
        try:
            progress_data = json.loads(data.get('progress', '{}'))
            kwargs['progress'] = TaskProgress(**progress_data) if progress_data else TaskProgress(current_step="初始化")
        except:
            kwargs['progress'] = TaskProgress(current_step="初始化")
        
        try:
            results_data = json.loads(data.get('results', '[]'))
            kwargs['results'] = results_data  # 暂时存储为原始数据，稍后可以转换为TaskResult对象
        except:
            kwargs['results'] = []
        
        return cls(**kwargs)
    
    def get_redis_key(self) -> str:
        """获取Redis键名"""
        return f"task:{self.task_id}"
    
    def update_progress(self, step: str, percent: float, processed: int = None, estimated: int = None):
        """更新任务进度"""
        self.progress.current_step = step
        self.progress.progress_percent = percent
        if processed is not None:
            self.progress.processed_files = processed
        if estimated is not None:
            self.progress.estimated_remaining = estimated 