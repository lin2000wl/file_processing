"""
任务管理服务
"""
import asyncio
import uuid
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from loguru import logger

from app.core.database import get_redis
from app.models.task_model import TaskInfo, TaskStatus, TaskType, TaskProgress
from app.services.file_service import file_service
from app.services.session_service import monkeyocr_service


class TaskService:
    """任务管理服务"""
    
    def __init__(self):
        self.task_key_prefix = "task:"
        self.task_list_key = "tasks:list"
        self.session_tasks_key_prefix = "session:tasks:"
        
    async def create_task(
        self, 
        file_ids: List[str], 
        task_type: TaskType = TaskType.FULL,
        options: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> TaskInfo:
        """
        创建新任务
        
        Args:
            file_ids: 文件ID列表
            task_type: 任务类型
            options: 处理选项
            session_id: 会话ID
            
        Returns:
            创建的任务信息
        """
        redis = get_redis()
        
        # 生成任务ID
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        # 验证文件存在
        valid_files = []
        for file_id in file_ids:
            file_info = await file_service.get_file_info(file_id)
            if file_info:
                valid_files.append(file_info)
            else:
                logger.warning(f"文件不存在: {file_id}")
        
        if not valid_files:
            raise ValueError("没有有效的文件")
        
        # 创建任务信息
        task_info = TaskInfo(
            task_id=task_id,
            file_ids=[f.file_id for f in valid_files],
            task_type=task_type,
            status=TaskStatus.PENDING,
            options=options or {},
            session_id=session_id,
            created_time=datetime.now(),
            progress=TaskProgress(
                progress_percent=0.0,
                current_step="任务已创建",
                processed_files=0,
                total_files=len(valid_files),
                estimated_remaining=None
            )
        )
        
        # 保存到Redis
        await redis.hset(
            f"{self.task_key_prefix}{task_id}",
            mapping=task_info.to_redis_dict()
        )
        
        # 添加到任务列表
        await redis.lpush(self.task_list_key, task_id)
        
        # 如果有会话ID，添加到会话任务列表
        if session_id:
            await redis.lpush(f"{self.session_tasks_key_prefix}{session_id}", task_id)
        
        # 设置过期时间（24小时）
        await redis.expire(f"{self.task_key_prefix}{task_id}", 86400)
        
        logger.info(f"任务创建成功: {task_id}, 类型: {task_type}, 文件数: {len(valid_files)}")
        
        # 异步启动任务处理
        asyncio.create_task(self._process_task(task_info))
        
        return task_info
    
    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        redis = get_redis()
        
        task_data = await redis.hgetall(f"{self.task_key_prefix}{task_id}")
        if not task_data:
            return None
        
        return TaskInfo.from_redis_dict(task_data)
    
    async def get_tasks(
        self, 
        session_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """
        获取任务列表
        
        Args:
            session_id: 会话ID筛选
            status: 状态筛选
            page: 页码
            size: 每页大小
            
        Returns:
            任务列表和分页信息
        """
        redis = get_redis()
        
        # 确定要查询的任务列表
        if session_id:
            list_key = f"{self.session_tasks_key_prefix}{session_id}"
        else:
            list_key = self.task_list_key
        
        # 获取任务ID列表
        start = (page - 1) * size
        end = start + size - 1
        task_ids = await redis.lrange(list_key, start, end)
        
        # 获取总数
        total = await redis.llen(list_key)
        
        # 获取任务详情
        tasks = []
        for task_id in task_ids:
            task_info = await self.get_task(task_id)
            if task_info:
                # 状态筛选
                if status is None or task_info.status == status:
                    tasks.append(task_info)
        
        return {
            "tasks": tasks,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task_info = await self.get_task(task_id)
        if not task_info:
            return False
        
        if task_info.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            return False
        
        # 更新任务状态
        task_info.status = TaskStatus.CANCELLED
        task_info.updated_time = datetime.now()
        task_info.progress.current_step = "任务已取消"
        
        await self._update_task(task_info)
        
        logger.info(f"任务已取消: {task_id}")
        return True
    
    async def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        task_info = await self.get_task(task_id)
        if not task_info:
            return False
        
        if task_info.status != TaskStatus.FAILED:
            return False
        
        # 重置任务状态
        task_info.status = TaskStatus.PENDING
        task_info.updated_time = datetime.now()
        task_info.error_message = None
        task_info.progress.progress_percent = 0.0
        task_info.progress.current_step = "任务重试中"
        task_info.progress.processed_files = 0
        
        await self._update_task(task_info)
        
        # 重新启动任务处理
        asyncio.create_task(self._process_task(task_info))
        
        logger.info(f"任务重试: {task_id}")
        return True
    
    async def _update_task(self, task_info: TaskInfo):
        """更新任务信息到Redis"""
        redis = get_redis()
        await redis.hset(
            f"{self.task_key_prefix}{task_info.task_id}",
            mapping=task_info.to_redis_dict()
        )
    
    async def _process_task(self, task_info: TaskInfo):
        """
        异步处理任务
        """
        try:
            logger.info(f"开始处理任务: {task_info.task_id}")
            
            # 更新状态为运行中
            task_info.status = TaskStatus.RUNNING
            task_info.started_time = datetime.now()
            task_info.progress.current_step = "准备处理文件"
            await self._update_task(task_info)
            
            # 获取文件路径
            file_paths = []
            for file_id in task_info.file_ids:
                file_info = await file_service.get_file_info(file_id)
                if file_info:
                    file_paths.append(file_info.storage_path)
            
            if not file_paths:
                raise ValueError("没有有效的文件路径")
            
            # 处理文件
            if len(file_paths) == 1:
                # 单文件处理
                await self._process_single_file(task_info, file_paths[0])
            else:
                # 多文件处理
                await self._process_multiple_files(task_info, file_paths)
            
            # 任务完成
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_time = datetime.now()
            task_info.progress.progress_percent = 100.0
            task_info.progress.current_step = "处理完成"
            task_info.progress.processed_files = task_info.progress.total_files
            
            await self._update_task(task_info)
            
            logger.info(f"任务处理完成: {task_info.task_id}")
            
        except Exception as e:
            logger.error(f"任务处理失败 {task_info.task_id}: {e}")
            
            # 更新任务状态为失败
            task_info.status = TaskStatus.FAILED
            task_info.error_message = str(e)
            task_info.progress.current_step = f"处理失败: {str(e)}"
            
            await self._update_task(task_info)
    
    async def _process_single_file(self, task_info: TaskInfo, file_path: str):
        """处理单个文件"""
        # 更新进度
        task_info.progress.current_step = f"正在处理文件: {file_path}"
        task_info.progress.progress_percent = 10.0
        await self._update_task(task_info)
        
        # 调用MonkeyOCR处理
        result = await monkeyocr_service.process_file(
            file_path=file_path,
            task_type=task_info.task_type.value,
            options=task_info.options
        )
        
        # 保存结果
        task_info.results = [result]
        task_info.progress.progress_percent = 90.0
        task_info.progress.processed_files = 1
        await self._update_task(task_info)
    
    async def _process_multiple_files(self, task_info: TaskInfo, file_paths: List[str]):
        """处理多个文件"""
        results = []
        
        for i, file_path in enumerate(file_paths):
            # 更新进度
            progress = (i / len(file_paths)) * 90.0  # 90%用于处理，10%用于完成
            task_info.progress.current_step = f"正在处理文件 {i+1}/{len(file_paths)}: {file_path}"
            task_info.progress.progress_percent = progress
            task_info.progress.processed_files = i
            await self._update_task(task_info)
            
            # 处理单个文件
            try:
                result = await monkeyocr_service.process_file(
                    file_path=file_path,
                    task_type=task_info.task_type.value,
                    options=task_info.options
                )
                results.append(result)
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'file_path': file_path
                })
        
        # 保存结果
        task_info.results = results
        task_info.progress.processed_files = len(file_paths)


# 创建全局服务实例
task_service = TaskService() 