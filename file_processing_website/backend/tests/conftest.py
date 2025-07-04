import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
import redis.asyncio as redis

from app.main import app
from app.core.database import get_redis_client


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """创建测试客户端"""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def async_client():
    """创建异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def redis_client():
    """创建Redis测试客户端"""
    client = redis.Redis.from_url("redis://localhost:6379/1", decode_responses=True)
    
    # 清空测试数据库
    await client.flushdb()
    
    yield client
    
    # 清理测试数据
    await client.flushdb()
    await client.close()


@pytest.fixture
def mock_redis_client(mocker):
    """模拟Redis客户端"""
    mock_client = mocker.AsyncMock()
    mocker.patch('app.core.database.get_redis_client', return_value=mock_client)
    return mock_client


@pytest.fixture
def sample_file_data():
    """示例文件数据"""
    return {
        "file_id": "test_file_123",
        "original_name": "test.pdf",
        "file_size": 1024000,
        "content_type": "application/pdf",
        "storage_path": "/storage/uploads/test_file_123.pdf",
        "upload_time": "2025-01-01T00:00:00Z",
        "status": "uploaded"
    }


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        "task_id": "task_123",
        "file_id": "test_file_123",
        "task_type": "parse",
        "status": "pending",
        "progress": 0,
        "created_time": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def sample_session_data():
    """示例会话数据"""
    return {
        "session_id": "session_123",
        "file_ids": ["test_file_123"],
        "created_time": "2025-01-01T00:00:00Z",
        "last_activity": "2025-01-01T00:00:00Z"
    } 