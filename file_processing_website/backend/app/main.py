"""
文件处理网站 - FastAPI主应用
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import uvicorn
import time

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import init_database, close_database
from app.api import api_router
from app.core.exceptions import setup_exception_handlers

# 设置日志
setup_logging()

# 创建FastAPI应用
app = FastAPI(
    title="文件处理网站API",
    description="基于MonkeyOCR的文档处理服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 记录请求
    logger.info(f"Request: {request.method} {request.url}")
    
    # 处理请求
    response = await call_next(request)
    
    # 记录响应
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "service": "file-processing-website",
        "version": "1.0.0"
    }

# 注册API路由
app.include_router(api_router, prefix="/api/v1")

# 设置异常处理器
setup_exception_handlers(app)

# 应用生命周期事件
@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("🚀 文件处理网站启动中...")
    logger.info(f"环境: {'开发' if settings.DEBUG else '生产'}")
    logger.info(f"服务地址: http://{settings.HOST}:{settings.PORT}")
    
    # 初始化数据库连接
    try:
        await init_database()
        logger.info("✅ 数据库连接初始化成功")
    except Exception as e:
        logger.error(f"❌ 数据库连接初始化失败: {e}")
        # 在开发环境下可以继续运行，生产环境应该退出
        if not settings.DEBUG:
            raise

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 文件处理网站正在关闭...")
    
    # 关闭数据库连接
    try:
        await close_database()
        logger.info("✅ 数据库连接已关闭")
    except Exception as e:
        logger.error(f"❌ 数据库连接关闭失败: {e}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 