"""
Redis数据库连接模块
"""
import asyncio
from typing import Optional
import redis.asyncio as aioredis
from loguru import logger
from app.core.config import settings


class RedisManager:
    """Redis连接管理器"""
    
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.connection_pool: Optional[aioredis.ConnectionPool] = None
    
    async def connect(self):
        """建立Redis连接"""
        try:
            # 创建Redis客户端
            self.redis = aioredis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True,
                max_connections=20
            )
            
            # 测试连接
            await self.redis.ping()
            logger.info(f"✅ Redis连接成功: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis连接已断开")
    
    async def ping(self) -> bool:
        """检查Redis连接状态"""
        try:
            if self.redis:
                await self.redis.ping()
                return True
        except Exception as e:
            logger.error(f"Redis连接检查失败: {e}")
        return False
    
    def get_client(self) -> aioredis.Redis:
        """获取Redis客户端"""
        if not self.redis:
            raise RuntimeError("Redis未连接，请先调用connect()方法")
        return self.redis


# 全局Redis管理器实例
redis_manager = RedisManager()


def get_redis() -> aioredis.Redis:
    """获取Redis客户端的依赖注入函数"""
    if not redis_manager.redis:
        raise RuntimeError("Redis未连接，请先调用init_database()方法")
    return redis_manager.redis

# 创建文件服务模块


async def init_database():
    """初始化数据库连接"""
    await redis_manager.connect()


async def close_database():
    """关闭数据库连接"""
    await redis_manager.disconnect() 