"""
文件管理API端点
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Header, Query
from typing import List, Optional
from loguru import logger

router = APIRouter()

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Header(None, alias="X-Session-ID")
):
    """
    文件上传接口
    
    Args:
        files: 上传的文件列表
        session_id: 会话ID（通过Header传递）
        
    Returns:
        上传结果
    """
    logger.info(f"接收到文件上传请求，文件数量: {len(files)}, 会话ID: {session_id}")
    
    try:
        from app.services.file_service import FileService
        from app.services.session_service import SessionService
        
        # 初始化服务
        file_service = FileService()
        session_service = SessionService()
        
        # 获取或创建会话
        current_session_id = await session_service.get_or_create_session(session_id)
        
        # 上传文件
        uploaded_files = await file_service.upload_files(files, current_session_id)
        
        # 将文件添加到会话
        for file_info in uploaded_files:
            await session_service.add_file_to_session(current_session_id, file_info.file_id)
        
        return {
            "success": True,
            "message": f"成功上传 {len(uploaded_files)} 个文件",
            "data": {
                "session_id": current_session_id,
                "files": [
                    {
                        "file_id": file_info.file_id,
                        "filename": file_info.filename,
                        "original_filename": file_info.original_filename,
                        "size": file_info.size,
                        "content_type": file_info.content_type,
                        "extension": file_info.extension,
                        "storage_path": file_info.storage_path,
                        "status": file_info.status.value,
                        "upload_time": file_info.upload_time.isoformat(),
                        "session_id": file_info.session_id,
                        "metadata": file_info.metadata
                    }
                    for file_info in uploaded_files
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}")
        raise

@router.get("/{file_id}")
async def get_file_info(file_id: str):
    """
    获取文件信息
    
    Args:
        file_id: 文件ID
        
    Returns:
        文件信息
    """
    logger.info(f"获取文件信息: {file_id}")
    
    try:
        from app.services.file_service import FileService
        
        file_service = FileService()
        file_info = await file_service.get_file_info(file_id)
        
        if not file_info:
            raise HTTPException(404, f"文件不存在: {file_id}")
        
        return {
            "success": True,
            "data": {
                "file_id": file_info.file_id,
                "filename": file_info.original_filename,
                "size": file_info.size,
                "content_type": file_info.content_type,
                "extension": file_info.extension,
                "status": file_info.status.value,
                "upload_time": file_info.upload_time.isoformat(),
                "session_id": file_info.session_id,
                "error_message": file_info.error_message
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息失败: {str(e)}")
        raise HTTPException(500, f"获取文件信息失败: {str(e)}")

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    """
    删除文件
    
    Args:
        file_id: 文件ID
        
    Returns:
        删除结果
    """
    logger.info(f"删除文件: {file_id}")
    
    try:
        from app.services.file_service import FileService
        
        file_service = FileService()
        success = await file_service.delete_file(file_id)
        
        if success:
            return {
                "success": True,
                "message": f"文件删除成功: {file_id}"
            }
        else:
            raise HTTPException(500, "文件删除失败")
            
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}")
        if "文件不存在" in str(e):
            raise HTTPException(404, str(e))
        else:
            raise HTTPException(500, f"删除文件失败: {str(e)}") 


@router.get("/")
async def get_files(
    session_id: Optional[str] = Query(None, description="会话ID"),
    status: Optional[str] = Query(None, description="文件状态筛选")
):
    """
    获取文件列表
    
    Args:
        session_id: 会话ID
        status: 文件状态筛选
        
    Returns:
        文件列表
    """
    logger.info(f"获取文件列表，会话ID: {session_id}, 状态: {status}")
    
    try:
        from app.services.file_service import FileService
        
        file_service = FileService()
        
        if session_id:
            files = await file_service.get_files_by_session(session_id)
        else:
            # 如果没有提供会话ID，返回空列表
            files = []
        
        # 按状态筛选
        if status:
            files = [f for f in files if f.status.value == status]
        
        return {
            "success": True,
            "data": {
                "files": [
                    {
                        "file_id": file_info.file_id,
                        "filename": file_info.original_filename,
                        "size": file_info.size,
                        "content_type": file_info.content_type,
                        "extension": file_info.extension,
                        "status": file_info.status.value,
                        "upload_time": file_info.upload_time.isoformat(),
                        "error_message": file_info.error_message
                    }
                    for file_info in files
                ],
                "total": len(files)
            }
        }
        
    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        raise HTTPException(500, f"获取文件列表失败: {str(e)}")


@router.post("/cleanup")
async def cleanup_expired_files():
    """
    清理过期文件
    
    Returns:
        清理结果
    """
    logger.info("开始清理过期文件")
    
    try:
        from app.services.file_service import FileService
        
        file_service = FileService()
        cleaned_count = await file_service.cleanup_expired_files()
        
        return {
            "success": True,
            "message": f"清理完成，共清理 {cleaned_count} 个过期文件",
            "data": {
                "cleaned_count": cleaned_count
            }
        }
        
    except Exception as e:
        logger.error(f"清理过期文件失败: {str(e)}")
        raise HTTPException(500, f"清理过期文件失败: {str(e)}")
