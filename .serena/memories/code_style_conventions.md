# 代码风格和约定

## 编码规范
- **Python风格**：遵循PEP 8标准
- **导入顺序**：标准库 → 第三方库 → 本地模块
- **命名约定**：
  - 类名：PascalCase (如 `MonkeyOCR`)
  - 函数名：snake_case (如 `parse_file`)
  - 常量：UPPER_CASE (如 `MODEL_NAME`)
  - 变量：snake_case

## 类型提示
- 使用类型提示，特别是函数参数和返回值
- 使用 `typing` 模块的类型 (`List`, `Union`, `Optional`)
- 示例：`def batch_inference(self, images: List[Union[str, Image.Image]], questions: List[str]) -> List[str]:`

## 文档字符串
- 使用简洁的文档字符串描述函数功能
- 包含参数说明和返回值说明
- 示例：
```python
def parse_folder(folder_path, output_dir, config_path, task=None):
    """
    Parse all PDF and image files in a folder
    
    Args:
        folder_path: Input folder path
        output_dir: Output directory
        config_path: Configuration file path
        task: Optional task type for single task recognition
    """
```

## 日志记录
- 使用 `loguru` 库进行日志记录
- 统一的日志格式和级别
- 示例：`logger.info('using device: {}'.format(self.device))`