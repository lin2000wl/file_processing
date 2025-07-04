"""
任务管理API端点
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from loguru import logger

router = APIRouter()

@router.post("")
async def create_task(
    file_ids: List[str],
    task_type: str = "full",
    options: Optional[dict] = None
):
    """
    创建处理任务
    
    Args:
        file_ids: 文件ID列表
        task_type: 任务类型 (full, text, formula, table)
        options: 处理选项
        
    Returns:
        任务创建结果
    """
    from app.services import task_service
    from app.models.task_model import TaskType
    
    logger.info(f"创建任务请求: {task_type}, 文件数量: {len(file_ids)}")
    
    try:
        # 转换任务类型
        task_type_enum = TaskType(task_type)
        
        # 创建任务
        task_info = await task_service.create_task(
            file_ids=file_ids,
            task_type=task_type_enum,
            options=options
        )
        
        return {
            "success": True,
            "data": {
                "task_id": task_info.task_id,
                "status": task_info.status.value,
                "created_time": task_info.created_time.isoformat(),
                "estimated_time": 120  # 预估时间，可以根据文件数量动态计算
            }
        }
        
    except ValueError as e:
        logger.error(f"任务创建失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"任务创建异常: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.get("/{task_id}")
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    from app.services import task_service
    
    logger.info(f"获取任务状态: {task_id}")
    
    task_info = await task_service.get_task(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "success": True,
        "data": {
            "task_id": task_info.task_id,
            "status": task_info.status.value,
            "progress": task_info.progress.progress_percent,
            "current_step": task_info.progress.current_step,
            "created_time": task_info.created_time.isoformat(),
            "estimated_remaining": task_info.progress.estimated_remaining,
            "error_message": task_info.error_message
        }
    }

@router.get("")
async def get_task_list(
    session_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    size: int = 20
):
    """
    获取任务列表
    
    Args:
        session_id: 会话ID
        status: 任务状态过滤
        page: 页码
        size: 每页大小
        
    Returns:
        任务列表
    """
    from app.services import task_service
    from app.models.task_model import TaskStatus
    
    logger.info(f"获取任务列表: page={page}, size={size}")
    
    try:
        # 转换状态枚举
        status_enum = None
        if status:
            status_enum = TaskStatus(status)
        
        # 获取任务列表
        result = await task_service.get_tasks(
            session_id=session_id,
            status=status_enum,
            page=page,
            size=size
        )
        
        # 转换任务数据为API格式
        tasks_data = []
        for task in result["tasks"]:
            tasks_data.append({
                "task_id": task.task_id,
                "task_type": task.task_type.value,
                "status": task.status.value,
                "file_ids": task.file_ids,
                "created_time": task.created_time.isoformat(),
                "progress": {
                    "progress_percent": task.progress.progress_percent,
                    "current_step": task.progress.current_step,
                    "processed_files": task.progress.processed_files,
                    "total_files": task.progress.total_files,
                    "estimated_remaining": task.progress.estimated_remaining
                },
                "error_message": task.error_message
            })
        
        return {
            "success": True,
            "data": {
                "tasks": tasks_data,
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
                "pages": result["pages"]
            }
        }
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")

@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """
    取消任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        取消结果
    """
    from app.services import task_service
    
    logger.info(f"取消任务: {task_id}")
    
    success = await task_service.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="任务无法取消")
    
    return {
        "success": True,
        "message": "任务已取消"
    }


@router.post("/{task_id}/retry")
async def retry_task(task_id: str):
    """
    重试任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        重试结果
    """
    from app.services import task_service
    
    logger.info(f"重试任务: {task_id}")
    
    success = await task_service.retry_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="任务无法重试")
    
    return {
        "success": True,
        "message": "任务已重新启动"
    }


@router.get("/{task_id}/results")
async def get_task_results(task_id: str):
    """
    获取任务结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务结果
    """
    from app.services import task_service
    
    logger.info(f"获取任务结果: {task_id}")
    
    task_info = await task_service.get_task(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task_info.status.value != "completed":
        raise HTTPException(status_code=400, detail="任务尚未完成")
    
    return {
        "success": True,
        "data": {
            "task_id": task_info.task_id,
            "results": task_info.results,
            "completed_time": task_info.completed_time.isoformat() if task_info.completed_time else None
        }
    }

@router.delete("/{task_id}")
async def cancel_task(task_id: str):
    """
    取消任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        取消结果
    """
    logger.info(f"取消任务: {task_id}")
    
    # TODO: 实现任务取消逻辑
    return {
        "success": True,
        "message": "任务取消成功"
    } 