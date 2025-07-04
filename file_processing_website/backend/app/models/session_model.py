"""
会话信息数据模型
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class SessionInfo(BaseModel):
    """会话信息模型"""
    
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="会话ID")
    
    # 基本信息
    created_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    last_activity: datetime = Field(default_factory=datetime.now, description="最后活动时间")
    
    # 关联信息
    file_ids: List[str] = Field(default_factory=list, description="关联的文件ID列表")
    task_ids: List[str] = Field(default_factory=list, description="关联的任务ID列表")
    
    # 客户端信息
    client_ip: Optional[str] = Field(None, description="客户端IP")
    user_agent: Optional[str] = Field(None, description="用户代理")
    
    # 会话状态
    is_active: bool = Field(default=True, description="是否活跃")
    
    # 统计信息
    uploaded_files_count: int = Field(default=0, description="上传文件数量")
    completed_tasks_count: int = Field(default=0, description="完成任务数量")
    
    # 元数据
    metadata: Dict[str, Any] = Field(default_factory=dict, description="会话元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_redis_dict(self) -> dict:
        """转换为Redis存储格式"""
        import json
        data = self.dict()
        # 转换时间字段
        data['created_time'] = self.created_time.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        # 转换列表和字典字段为JSON字符串
        data['file_ids'] = json.dumps(self.file_ids)
        data['task_ids'] = json.dumps(self.task_ids)
        data['metadata'] = json.dumps(self.metadata)
        # 处理特殊类型
        for key, value in data.items():
            if value is None:
                data[key] = ""
            elif isinstance(value, bool):
                data[key] = str(value)
        return data
    
    @classmethod
    def from_redis_dict(cls, data: dict) -> 'SessionInfo':
        """从Redis数据创建实例"""
        import json
        # 转换时间字段
        if 'created_time' in data and isinstance(data['created_time'], str):
            data['created_time'] = datetime.fromisoformat(data['created_time'])
        if 'last_activity' in data and isinstance(data['last_activity'], str):
            data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        # 转换JSON字符串为列表和字典
        if 'file_ids' in data and isinstance(data['file_ids'], str):
            data['file_ids'] = json.loads(data['file_ids'])
        if 'task_ids' in data and isinstance(data['task_ids'], str):
            data['task_ids'] = json.loads(data['task_ids'])
        if 'metadata' in data and isinstance(data['metadata'], str):
            data['metadata'] = json.loads(data['metadata'])
        # 处理特殊类型
        for key, value in data.items():
            if value == "" and key in ['client_ip', 'user_agent']:
                data[key] = None
            elif key == 'is_active' and isinstance(value, str):
                data[key] = value == 'True'
        return cls(**data)
    
    def get_redis_key(self) -> str:
        """获取Redis键名"""
        return f"session:{self.session_id}"
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_activity = datetime.now()
    
    def add_file(self, file_id: str):
        """添加文件ID"""
        if file_id not in self.file_ids:
            self.file_ids.append(file_id)
            self.uploaded_files_count += 1
            self.update_activity()
    
    def add_task(self, task_id: str):
        """添加任务ID"""
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
            self.update_activity()
    
    def complete_task(self):
        """标记任务完成"""
        self.completed_tasks_count += 1
        self.update_activity()
    
    def is_expired(self, ttl_hours: int = 24) -> bool:
        """检查会话是否过期"""
        expiry_time = self.last_activity + timedelta(hours=ttl_hours)
        return datetime.now() > expiry_time 