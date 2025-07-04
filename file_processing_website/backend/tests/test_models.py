import pytest
import json
from datetime import datetime
from app.models.database import FileInfo, TaskInfo, SessionInfo


class TestFileInfo:
    """文件信息模型测试"""

    def test_file_info_creation(self):
        """测试文件信息创建"""
        file_info = FileInfo(
            file_id="test_123",
            original_name="test.pdf",
            file_size=1024000,
            content_type="application/pdf",
            storage_path="/storage/test.pdf"
        )
        
        assert file_info.file_id == "test_123"
        assert file_info.original_name == "test.pdf"
        assert file_info.status == "uploaded"
        assert isinstance(file_info.upload_time, datetime)

    def test_file_info_to_redis(self):
        """测试文件信息Redis序列化"""
        file_info = FileInfo(
            file_id="test_123",
            original_name="test.pdf",
            file_size=1024000,
            content_type="application/pdf",
            storage_path="/storage/test.pdf"
        )
        
        redis_data = file_info.to_redis()
        assert isinstance(redis_data, str)
        
        # 验证可以反序列化
        data = json.loads(redis_data)
        assert data["file_id"] == "test_123"
        assert data["original_name"] == "test.pdf"

    def test_file_info_from_redis(self):
        """测试从Redis数据创建文件信息"""
        redis_data = {
            "file_id": "test_123",
            "original_name": "test.pdf",
            "file_size": 1024000,
            "content_type": "application/pdf",
            "storage_path": "/storage/test.pdf",
            "upload_time": "2025-01-01T00:00:00Z",
            "status": "uploaded"
        }
        
        file_info = FileInfo.from_redis(json.dumps(redis_data))
        assert file_info.file_id == "test_123"
        assert file_info.original_name == "test.pdf"


class TestTaskInfo:
    """任务信息模型测试"""

    def test_task_info_creation(self):
        """测试任务信息创建"""
        task_info = TaskInfo(
            task_id="task_123",
            file_id="file_123",
            task_type="parse"
        )
        
        assert task_info.task_id == "task_123"
        assert task_info.file_id == "file_123"
        assert task_info.status == "pending"
        assert task_info.progress == 0
        assert isinstance(task_info.created_time, datetime)

    def test_task_info_update_progress(self):
        """测试任务进度更新"""
        task_info = TaskInfo(
            task_id="task_123",
            file_id="file_123",
            task_type="parse"
        )
        
        task_info.update_progress(50, "Processing...")
        assert task_info.progress == 50
        assert task_info.message == "Processing..."
        assert isinstance(task_info.updated_time, datetime)


class TestSessionInfo:
    """会话信息模型测试"""

    def test_session_info_creation(self):
        """测试会话信息创建"""
        session_info = SessionInfo(session_id="session_123")
        
        assert session_info.session_id == "session_123"
        assert session_info.file_ids == []
        assert isinstance(session_info.created_time, datetime)

    def test_session_add_file(self):
        """测试会话添加文件"""
        session_info = SessionInfo(session_id="session_123")
        session_info.add_file("file_123")
        
        assert "file_123" in session_info.file_ids
        assert isinstance(session_info.last_activity, datetime) 