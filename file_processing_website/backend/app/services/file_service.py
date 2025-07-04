import os
import uuid
import shutil
import magic
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import UploadFile, HTTPException
from loguru import logger

from app.core.config import settings
from app.core.database import get_redis
from app.models.file_model import FileInfo, FileStatus
from app.core.exceptions import (
    FileTypeNotAllowedError,
    FileSizeExceededError,
    FileNotFoundError
)


class FileService:
    """文件服务类"""
    
    def __init__(self):
        self.storage_paths = settings.storage_paths
        # 确保存储目录存在
        settings.ensure_storage_dirs()

    @property
    def redis(self):
        """获取Redis客户端"""
        from app.core.database import redis_manager
        if not redis_manager.redis:
            raise RuntimeError("Redis未连接，请先调用init_database()方法")
        return redis_manager.redis
    
    async def upload_files(
        self, 
        files: List[UploadFile], 
        session_id: Optional[str] = None
    ) -> List[FileInfo]:
        """
        上传文件
        
        Args:
            files: 上传的文件列表
            session_id: 会话ID
            
        Returns:
            上传的文件信息列表
            
        Raises:
            FileTypeNotAllowedError: 文件类型不允许
            FileSizeExceededError: 文件大小超限
        """
        logger.info(f"开始上传 {len(files)} 个文件，会话ID: {session_id}")
        
        # 验证文件
        await self._validate_files(files)
        
        uploaded_files = []
        
        for file in files:
            try:
                # 创建文件信息
                file_info = await self._create_file_info(file, session_id)
                
                # 保存文件到存储目录
                await self._save_file(file, file_info.storage_path)
                
                # 保存文件信息到Redis
                await self._save_file_info(file_info)
                
                uploaded_files.append(file_info)
                logger.info(f"文件上传成功: {file_info.filename} -> {file_info.file_id}")
                
            except Exception as e:
                logger.error(f"上传文件失败: {file.filename}, 错误: {str(e)}")
                # 清理已保存的文件
                if 'file_info' in locals() and os.path.exists(file_info.storage_path):
                    os.remove(file_info.storage_path)
                raise
        
        logger.info(f"批量上传完成，成功: {len(uploaded_files)} 个文件")
        return uploaded_files
    
    async def get_file_info(self, file_id: str) -> Optional[FileInfo]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件信息，如果不存在返回None
        """
        redis_key = f"file:{file_id}"
        data = await self.redis.hgetall(redis_key)
        
        if not data:
            return None
            
        return FileInfo.from_redis_dict(data)
    
    async def delete_file(self, file_id: str) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            删除是否成功
        """
        file_info = await self.get_file_info(file_id)
        if not file_info:
            raise FileNotFoundError(f"文件不存在: {file_id}")
        
        try:
            # 删除物理文件
            if os.path.exists(file_info.storage_path):
                os.remove(file_info.storage_path)
                logger.info(f"删除物理文件: {file_info.storage_path}")
            
            # 删除Redis记录
            redis_key = f"file:{file_id}"
            await self.redis.delete(redis_key)
            logger.info(f"删除文件记录: {file_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"删除文件失败: {file_id}, 错误: {str(e)}")
            raise
    
    async def update_file_status(
        self, 
        file_id: str, 
        status: FileStatus, 
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新文件状态
        
        Args:
            file_id: 文件ID
            status: 新状态
            error_message: 错误信息（可选）
            
        Returns:
            更新是否成功
        """
        redis_key = f"file:{file_id}"
        
        # 检查文件是否存在
        if not await self.redis.exists(redis_key):
            return False
        
        # 更新状态
        update_data = {"status": status.value}
        if error_message:
            update_data["error_message"] = error_message
        
        await self.redis.hset(redis_key, mapping=update_data)
        logger.info(f"更新文件状态: {file_id} -> {status.value}")
        
        return True
    
    async def get_files_by_session(self, session_id: str) -> List[FileInfo]:
        """
        获取会话的所有文件
        
        Args:
            session_id: 会话ID
            
        Returns:
            文件信息列表
        """
        # 扫描所有文件键
        pattern = "file:*"
        keys = await self.redis.keys(pattern)
        
        files = []
        for key in keys:
            data = await self.redis.hgetall(key)
            if data.get("session_id") == session_id:
                files.append(FileInfo.from_redis_dict(data))
        
        return files
    
    async def cleanup_expired_files(self) -> int:
        """
        清理过期文件
        
        Returns:
            清理的文件数量
        """
        logger.info("开始清理过期文件")
        
        # 获取所有文件键
        pattern = "file:*"
        keys = await self.redis.keys(pattern)
        
        cleaned_count = 0
        
        for key in keys:
            # 检查键是否过期（TTL为-1表示永不过期，-2表示已过期）
            ttl = await self.redis.ttl(key)
            if ttl == -2:  # 已过期
                file_id = key.split(":")[-1]
                try:
                    await self.delete_file(file_id)
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"清理过期文件失败: {file_id}, 错误: {str(e)}")
        
        logger.info(f"清理过期文件完成，共清理 {cleaned_count} 个文件")
        return cleaned_count
    
    async def _validate_files(self, files: List[UploadFile]) -> None:
        """验证文件"""
        # 检查文件数量
        if len(files) > 20:  # 最大20个文件
            raise HTTPException(400, "文件数量超过限制（最大20个）")
        
        # 检查总大小
        total_size = sum(file.size or 0 for file in files)
        if total_size > 200 * 1024 * 1024:  # 200MB
            raise FileSizeExceededError("文件总大小超过限制（最大200MB）")
        
        for file in files:
            # 检查单个文件大小
            if (file.size or 0) > settings.UPLOAD_MAX_SIZE:
                raise FileSizeExceededError(
                    f"文件 {file.filename} 大小超过限制（最大{settings.UPLOAD_MAX_SIZE // 1024 // 1024}MB）"
                )
            
            # 检查文件类型
            await self._validate_file_type(file)
    
    async def _validate_file_type(self, file: UploadFile) -> None:
        """验证文件类型"""
        if not file.filename:
            raise FileTypeNotAllowedError("文件名不能为空")
        
        # 检查扩展名
        file_ext = Path(file.filename).suffix.lower().lstrip('.')
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise FileTypeNotAllowedError(
                f"不支持的文件类型: {file_ext}，支持的类型: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # 在开发环境下暂时跳过MIME类型检查
        if settings.DEBUG:
            logger.debug("开发环境：跳过MIME类型检查")
            return
        
        # 检查MIME类型
        content = await file.read(1024)  # 读取前1KB用于检测
        await file.seek(0)  # 重置文件指针
        
        mime_type = magic.from_buffer(content, mime=True)
        
        allowed_mimes = {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg'
        }
        
        expected_mime = allowed_mimes.get(file_ext)
        if expected_mime and mime_type != expected_mime:
            raise FileTypeNotAllowedError(
                f"文件内容与扩展名不匹配: {file.filename}"
            )
    
    async def _create_file_info(self, file: UploadFile, session_id: Optional[str]) -> FileInfo:
        """创建文件信息对象"""
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix.lower()
        
        # 生成存储文件名（使用UUID避免冲突）
        storage_filename = f"{file_id}{file_ext}"
        storage_path = self.storage_paths["uploads"] / storage_filename
        
        return FileInfo(
            file_id=file_id,
            filename=storage_filename,
            original_filename=file.filename,
            size=file.size or 0,
            content_type=file.content_type or "application/octet-stream",
            extension=file_ext.lstrip('.'),
            storage_path=str(storage_path),
            session_id=session_id,
            status=FileStatus.UPLOADED
        )
    
    async def _save_file(self, file: UploadFile, storage_path: str) -> None:
        """保存文件到存储目录"""
        try:
            with open(storage_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logger.debug(f"文件保存成功: {storage_path}")
        except Exception as e:
            logger.error(f"保存文件失败: {storage_path}, 错误: {str(e)}")
            raise
        finally:
            await file.seek(0)  # 重置文件指针
    
    async def _save_file_info(self, file_info: FileInfo) -> None:
        """保存文件信息到Redis"""
        redis_key = file_info.get_redis_key()
        data = file_info.to_redis_dict()
        
        # 保存到Redis，设置24小时过期
        await self.redis.hset(redis_key, mapping=data)
        await self.redis.expire(redis_key, 86400)  # 24小时
        
        logger.debug(f"文件信息保存到Redis: {redis_key}") 

# 创建全局服务实例
file_service = FileService()
