"""
文件信息数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class FileStatus(str, Enum):
    """文件状态枚举"""
    UPLOADED = "uploaded"           # 已上传
    PROCESSING = "processing"       # 处理中
    COMPLETED = "completed"         # 处理完成
    ERROR = "error"                # 处理错误
    DELETED = "deleted"            # 已删除


class FileInfo(BaseModel):
    """文件信息模型"""
    
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="文件ID")
    filename: str = Field(..., description="文件名")
    original_filename: str = Field(..., description="原始文件名")
    size: int = Field(..., description="文件大小（字节）")
    content_type: str = Field(..., description="文件MIME类型")
    extension: str = Field(..., description="文件扩展名")
    
    # 存储信息
    storage_path: str = Field(..., description="存储路径")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")
    
    # 状态信息
    status: FileStatus = Field(default=FileStatus.UPLOADED, description="文件状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    
    # 会话信息
    session_id: Optional[str] = Field(None, description="会话ID")
    
    # 处理信息
    processing_task_id: Optional[str] = Field(None, description="处理任务ID")
    
    # 元数据
    metadata: dict = Field(default_factory=dict, description="文件元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_redis_dict(self) -> dict:
        """转换为Redis存储格式"""
        import json
        
        data = self.dict()
        data['upload_time'] = self.upload_time.isoformat()
        
        # 序列化metadata为JSON字符串
        data['metadata'] = json.dumps(self.metadata)
        
        # 将None值转换为空字符串，避免Redis存储错误
        for key, value in data.items():
            if value is None:
                data[key] = ""
        
        return data
    
    @classmethod
    def from_redis_dict(cls, data: dict) -> 'FileInfo':
        """从Redis数据创建实例"""
        import json
        
        # 处理时间字段
        if 'upload_time' in data and isinstance(data['upload_time'], str):
            data['upload_time'] = datetime.fromisoformat(data['upload_time'])
        
        # 处理metadata字段
        if 'metadata' in data:
            if isinstance(data['metadata'], str):
                try:
                    data['metadata'] = json.loads(data['metadata']) if data['metadata'] else {}
                except json.JSONDecodeError:
                    data['metadata'] = {}
            elif data['metadata'] is None:
                data['metadata'] = {}
        
        # 处理None值转换为适当的默认值
        for key, value in data.items():
            if value == "":
                if key in ['error_message', 'session_id', 'processing_task_id']:
                    data[key] = None
        
        return cls(**data)
    
    def get_redis_key(self) -> str:
        """获取Redis键名"""
        return f"file:{self.file_id}" 