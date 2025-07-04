"""
API路由包
"""
from fastapi import APIRouter
from app.api.endpoints import files, tasks, results

# 创建API路由器
api_router = APIRouter()

# 注册各个端点路由
api_router.include_router(files.router, prefix="/files", tags=["文件管理"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(results.router, prefix="/results", tags=["结果获取"]) 