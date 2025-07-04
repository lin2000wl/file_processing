"""
日志配置模块
"""
import sys
from pathlib import Path
from loguru import logger
from app.core.config import settings


def setup_logging():
    """配置应用日志"""
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 控制台日志
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # 文件日志
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.add(
        str(log_file),
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # 错误日志单独记录
    error_log_file = log_file.parent / "error.log"
    logger.add(
        str(error_log_file),
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成") 