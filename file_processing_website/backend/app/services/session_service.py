import secrets
from datetime import datetime
from typing import Optional
from loguru import logger

from app.core.database import redis_manager
from app.models.session_model import SessionInfo


class SessionService:
    """会话服务类"""
    
    def __init__(self):
        pass

    @property  
    def redis(self):
        """获取Redis客户端"""
        if not redis_manager.redis:
            raise RuntimeError("Redis未连接，请先调用init_database()方法")
        return redis_manager.redis
    
    async def create_session(self) -> str:
        """
        创建新会话
        
        Returns:
            会话ID
        """
        session_id = secrets.token_urlsafe(32)
        
        session_info = SessionInfo(session_id=session_id)
        
        # 保存到Redis
        redis_key = f"session:{session_id}"
        data = session_info.to_redis_dict()
        
        await self.redis.hset(redis_key, mapping=data)
        await self.redis.expire(redis_key, 86400)  # 24小时过期
        
        logger.info(f"创建新会话: {session_id}")
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话信息，如果不存在返回None
        """
        redis_key = f"session:{session_id}"
        data = await self.redis.hgetall(redis_key)
        
        if not data:
            return None
            
        return SessionInfo.from_redis_dict(data)
    
    async def validate_session(self, session_id: str) -> bool:
        """
        验证会话是否有效
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话是否有效
        """
        if not session_id:
            return False
            
        redis_key = f"session:{session_id}"
        return await self.redis.exists(redis_key)
    
    async def update_activity(self, session_id: str) -> bool:
        """
        更新会话活动时间
        
        Args:
            session_id: 会话ID
            
        Returns:
            更新是否成功
        """
        redis_key = f"session:{session_id}"
        
        if not await self.redis.exists(redis_key):
            return False
        
        await self.redis.hset(
            redis_key, 
            "last_activity", 
            datetime.now().isoformat()
        )
        
        logger.debug(f"更新会话活动时间: {session_id}")
        return True
    
    async def add_file_to_session(self, session_id: str, file_id: str) -> bool:
        """
        将文件添加到会话
        
        Args:
            session_id: 会话ID
            file_id: 文件ID
            
        Returns:
            添加是否成功
        """
        session_info = await self.get_session(session_id)
        if not session_info:
            return False
        
        session_info.add_file(file_id)
        
        # 更新Redis
        redis_key = f"session:{session_id}"
        data = session_info.to_redis_dict()
        await self.redis.hset(redis_key, mapping=data)
        
        logger.debug(f"文件添加到会话: {file_id} -> {session_id}")
        return True
    
    async def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """
        获取或创建会话
        
        Args:
            session_id: 可选的会话ID
            
        Returns:
            会话ID
        """
        if session_id and await self.validate_session(session_id):
            await self.update_activity(session_id)
            return session_id
        else:
            return await self.create_session() 


class MonkeyOCRService:
    """MonkeyOCR处理服务"""
    
    def __init__(self):
        self._model = None
        self._model_config_path = None
        
    def _ensure_model_loaded(self):
        """确保模型已加载"""
        if self._model is None:
            from app.core.config import settings
            import sys
            import os
            
            # 添加项目根目录到Python路径
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # 导入MonkeyOCR
            from magic_pdf.model.custom_model import MonkeyOCR
            
            # 使用配置文件路径
            config_path = os.path.join(project_root, "model_configs.yaml")
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Model config file not found: {config_path}")
            
            logger.info(f"Loading MonkeyOCR model with config: {config_path}")
            self._model = MonkeyOCR(config_path)
            self._model_config_path = config_path
            logger.info("✅ MonkeyOCR model loaded successfully")

    def _is_demo_mode(self) -> bool:
        """检查是否为演示模式（没有完整的ML环境）"""
        try:
            import torch
            return False
        except ImportError:
            return True
    
    async def _demo_process_file(self, file_path: str, task_type: str, options: dict) -> dict:
        """演示模式的文件处理（模拟结果）"""
        import time
        import os
        from pathlib import Path
        
        # 模拟处理时间
        await asyncio.sleep(2)
        
        filename = os.path.basename(file_path)
        file_ext = Path(file_path).suffix.lower()
        
        # 根据任务类型生成模拟结果
        if task_type == "text":
            content = f"这是从文件 {filename} 中提取的模拟文本内容。\n\n文件类型: {file_ext}\n处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        elif task_type == "formula":
            content = f"$$\\sum_{{i=1}}^{{n}} x_i = \\frac{{a + b}}{{c}}$$\n\n这是从 {filename} 中识别的模拟公式。"
        elif task_type == "table":
            content = f"""<table>
<tr><th>列1</th><th>列2</th><th>列3</th></tr>
<tr><td>数据1</td><td>数据2</td><td>数据3</td></tr>
<tr><td>来源</td><td>{filename}</td><td>模拟数据</td></tr>
</table>"""
        else:  # full
            content = f"""# 文档解析结果

## 文件信息
- 文件名: {filename}
- 文件类型: {file_ext}
- 处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 文本内容
这是一个完整的文档解析示例。在实际环境中，这里将包含：
- 提取的文本内容
- 识别的公式
- 解析的表格
- 检测的图像

## 模拟公式
$$E = mc^2$$

## 模拟表格
| 项目 | 值 | 说明 |
|------|----|----|
| 文件大小 | 2.5KB | 示例数据 |
| 页数 | 1 | 模拟页面 |
| 处理状态 | 成功 | 演示模式 |

**注意**: 这是演示模式的模拟结果。在生产环境中将使用真实的MonkeyOCR处理。
"""
        
        return {
            'success': True,
            'processing_time': 2.0,
            'result_files': {
                'markdown': content,
                'json': {
                    'filename': filename,
                    'file_type': file_ext,
                    'task_type': task_type,
                    'demo_mode': True,
                    'processed_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
            },
            'output_dir': '/tmp/demo_output',
            'task_type': task_type,
            'file_info': {
                'filename': filename,
                'file_type': file_ext,
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
            },
            'demo_mode': True
        }
    
    async def process_file(self, file_path: str, task_type: str = "full", options: dict = None) -> dict:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            task_type: 任务类型 (full, text, formula, table)
            options: 处理选项
            
        Returns:
            处理结果字典
        """
        import asyncio
        import tempfile
        import os
        from pathlib import Path
        
        try:
            # 确保模型已加载
            self._ensure_model_loaded()
            
            # 创建临时输出目录
            with tempfile.TemporaryDirectory() as temp_output_dir:
                # 在线程池中运行处理任务（因为MonkeyOCR是同步的）
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    self._process_file_sync, 
                    file_path, 
                    temp_output_dir, 
                    task_type, 
                    options or {}
                )
                
                return result
                
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            raise
    
    def _process_file_sync(self, file_path: str, output_dir: str, task_type: str, options: dict) -> dict:
        """
        同步处理文件（在线程池中运行）
        """
        import sys
        import os
        
        # 添加项目根目录到Python路径
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from magic_pdf.model.doc_analyze_by_custom_model_llm import doc_analyze_llm
        from magic_pdf.data.dataset import PymuDocDataset, ImageDataset
        from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
        import time
        
        start_time = time.time()
        
        try:
            # 根据文件类型创建数据集
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.pdf':
                dataset = PymuDocDataset(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png']:
                dataset = ImageDataset(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            # 创建数据写入器
            writer = FileBasedDataWriter(output_dir)
            
            # 处理选项
            split_pages = options.get('split_pages', False)
            
            if task_type == "full":
                # 完整解析
                result_dir = doc_analyze_llm(
                    dataset=dataset,
                    model=self._model,
                    output_writer=writer,
                    split_pages=split_pages
                )
            else:
                # 单任务识别
                from parse import TASK_INSTRUCTIONS
                instruction = TASK_INSTRUCTIONS.get(task_type)
                if not instruction:
                    raise ValueError(f"Unknown task type: {task_type}")
                
                # TODO: 实现单任务识别逻辑
                # 这里需要调用相应的单任务识别函数
                result_dir = output_dir
            
            # 读取结果文件
            result_files = {}
            for root, dirs, files in os.walk(result_dir):
                for file in files:
                    file_path_result = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path_result, result_dir)
                    
                    if file.endswith('.md'):
                        # 读取Markdown内容
                        with open(file_path_result, 'r', encoding='utf-8') as f:
                            result_files['markdown'] = f.read()
                    elif file.endswith('.json'):
                        # 读取JSON内容
                        import json
                        with open(file_path_result, 'r', encoding='utf-8') as f:
                            result_files['json'] = json.load(f)
                    elif file.endswith('.pdf'):
                        # 布局PDF文件路径
                        result_files['layout_pdf'] = file_path_result
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'processing_time': processing_time,
                'result_files': result_files,
                'output_dir': result_dir,
                'task_type': task_type,
                'file_info': {
                    'filename': os.path.basename(file_path),
                    'file_type': file_ext,
                    'file_size': os.path.getsize(file_path)
                }
            }
            
        except Exception as e:
            logger.error(f"同步处理文件失败: {e}")
            raise
    
    async def process_multiple_files(self, file_paths: list, task_type: str = "full", options: dict = None) -> dict:
        """
        批量处理多个文件
        
        Args:
            file_paths: 文件路径列表
            task_type: 任务类型
            options: 处理选项
            
        Returns:
            批量处理结果
        """
        results = []
        failed_files = []
        
        for file_path in file_paths:
            try:
                result = await self.process_file(file_path, task_type, options)
                results.append(result)
            except Exception as e:
                failed_files.append({
                    'file_path': file_path,
                    'error': str(e)
                })
                logger.error(f"处理文件失败 {file_path}: {e}")
        
        return {
            'success': len(failed_files) == 0,
            'total_files': len(file_paths),
            'successful_files': len(results),
            'failed_files': len(failed_files),
            'results': results,
            'failures': failed_files
        }


# 创建全局服务实例
monkeyocr_service = MonkeyOCRService()
