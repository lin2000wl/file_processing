"""
应用配置管理
"""
import os
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """应用配置类"""
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # 文件存储配置
    UPLOAD_MAX_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: Union[str, List[str]] = "pdf,png,jpg,jpeg"
    STORAGE_PATH: str = "./storage"
    
    # MonkeyOCR配置
    MODEL_CONFIG_PATH: str = "../model_configs.yaml"
    MODELS_DIR: str = "../model_weight"
    
    # 任务配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    TASK_TIMEOUT: int = 3600  # 1小时
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8080"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """解析CORS origins"""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def assemble_allowed_extensions(cls, v: Union[str, List[str]]) -> List[str]:
        """解析允许的文件扩展名"""
        if isinstance(v, str):
            return [i.strip().lower() for i in v.split(",")]
        return v
    
    @property
    def redis_url(self) -> str:
        """Redis连接URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @property
    def storage_paths(self) -> dict:
        """存储路径配置"""
        base_path = Path(self.STORAGE_PATH)
        return {
            "uploads": base_path / "uploads",
            "processing": base_path / "processing", 
            "results": base_path / "results"
        }
    
    def ensure_storage_dirs(self):
        """确保存储目录存在"""
        for path in self.storage_paths.values():
            path.mkdir(parents=True, exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

# 确保存储目录存在
settings.ensure_storage_dirs() 