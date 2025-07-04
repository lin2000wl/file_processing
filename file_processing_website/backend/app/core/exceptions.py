"""
异常处理模块
"""
from typing import Any, Dict
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
import traceback


class FileProcessingException(Exception):
    """文件处理异常基类"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class FileNotFoundError(FileProcessingException):
    """文件不存在异常"""
    def __init__(self, message: str = "文件不存在"):
        super().__init__(message, 404)


class FileTypeNotAllowedError(FileProcessingException):
    """文件类型不允许异常"""
    def __init__(self, message: str = "不支持的文件类型"):
        super().__init__(message, 415)


class FileSizeExceededError(FileProcessingException):
    """文件大小超限异常"""
    def __init__(self, message: str = "文件大小超出限制"):
        super().__init__(message, 413)


class TaskNotFoundError(FileProcessingException):
    """任务不存在异常"""
    def __init__(self, message: str = "任务不存在"):
        super().__init__(message, 404)


class InvalidParameterError(FileProcessingException):
    """参数无效异常"""
    def __init__(self, message: str = "请求参数无效"):
        super().__init__(message, 400)


def create_error_response(code: int, message: str, details: Any = None) -> Dict[str, Any]:
    """创建错误响应"""
    response = {
        "success": False,
        "code": code,
        "message": message,
        "data": None,
        "timestamp": None
    }
    
    if details:
        response["details"] = details
    
    return response


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.status_code, exc.detail)
    )


async def file_processing_exception_handler(request: Request, exc: FileProcessingException) -> JSONResponse:
    """文件处理异常处理器"""
    logger.error(f"文件处理异常: {exc.code} - {exc.message}")
    
    return JSONResponse(
        status_code=exc.code,
        content=create_error_response(exc.code, exc.message)
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.error(f"未处理的异常: {type(exc).__name__} - {str(exc)}")
    logger.error(f"异常详情: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(500, "服务器内部错误")
    )


def setup_exception_handlers(app: FastAPI):
    """设置异常处理器"""
    
    # 注册异常处理器
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(FileProcessingException, file_processing_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("异常处理器设置完成") 