# 技术栈

## 核心技术
- **Python 3.9+**：主要编程语言
- **PyTorch**：深度学习框架
- **Transformers**：Hugging Face模型库
- **YOLO**：目标检测模型（DocLayout YOLO）
- **LayoutLMv3**：文档版面理解模型

## 主要依赖
- **PyMuPDF (fitz)**：PDF处理
- **PIL/Pillow**：图像处理
- **transformers==4.52.4**：模型推理
- **loguru**：日志记录
- **pydantic**：数据验证
- **FastAPI**：API服务
- **Gradio**：Web界面

## 推理后端
- **LMDeploy**：默认推理后端
- **vLLM**：高性能推理
- **transformers**：原生推理
- **OpenAI API**：云端API调用

## 部署方式
- **Docker**：容器化部署
- **本地安装**：pip安装
- **CUDA支持**：GPU加速