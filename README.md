# MonkeyOCR 文件处理项目

## 🎯 项目概述

基于MonkeyOCR的智能文档处理系统，支持PDF文档和图像的OCR识别、表格提取、公式识别和版面分析。本项目提供了完整的Docker化部署方案，支持GPU和CPU两种运行模式。

## ✨ 主要特性

- **🔍 智能OCR**: 基于深度学习的文档识别技术
- **📊 表格提取**: 精确的表格结构识别和数据提取
- **🧮 公式识别**: LaTeX格式的数学公式识别
- **📄 版面分析**: 智能的文档结构分析
- **🐳 Docker支持**: 完整的容器化部署方案
- **⚡ 多模式运行**: 支持GPU加速和CPU模式
- **🌐 Web界面**: 友好的用户交互界面

## 🏗️ 项目结构

```
MonkeyOCR/
├── magic_pdf/              # 核心处理模块
├── docker/                 # Docker配置文件
│   ├── Dockerfile.gpu      # GPU版本镜像
│   ├── Dockerfile.cpu      # CPU版本镜像
│   ├── docker-compose.gpu.yml
│   ├── docker-compose.cpu.yml
│   ├── README_GPU.md       # GPU配置指南
│   └── start-gpu.sh        # 启动脚本
├── file_processing_website/ # Web应用
│   ├── backend/            # 后端API
│   └── frontend/           # 前端界面
├── api/                    # API接口
├── demo/                   # 演示程序
├── parse.py               # 主处理脚本
├── model_configs.yaml     # 模型配置
└── requirements.txt       # 依赖列表
```

## 🚀 快速开始

### 方式1: Docker部署（推荐）

#### CPU版本（适合开发测试）
```bash
# 克隆项目
git clone https://github.com/lin2000wl/file_processing.git
cd file_processing

# 启动CPU版本
docker-compose -f docker/docker-compose.cpu.yml up -d

# 查看服务状态
docker-compose -f docker/docker-compose.cpu.yml ps
```

#### GPU版本（需要GPU支持）
```bash
# 启动GPU版本
./docker/start-gpu.sh

# 或手动启动
docker-compose -f docker/docker-compose.gpu.yml up -d
```

### 方式2: 直接运行

```bash
# 安装依赖
pip install -r requirements.txt

# 修改配置（CPU模式）
sed -i 's/device: cuda/device: cpu/' model_configs.yaml

# 运行处理
python parse.py input_document.pdf
```

## 📋 系统要求

### 基础要求
- Python 3.9+
- 8GB+ RAM
- 10GB+ 存储空间

### GPU版本额外要求
- NVIDIA GPU (GTX 1060+ 推荐)
- CUDA 11.8+
- NVIDIA Container Toolkit (Docker部署)

## 🔧 配置说明

### 模型配置
编辑 `model_configs.yaml` 文件：

```yaml
device: cpu  # cpu / cuda / mps
weights:
  doclayout_yolo: Structure/doclayout_yolo_docstructbench_imgsz1280_2501.pt
  layoutreader: Relation
models_dir: model_weight
chat_config:
  backend: transformers  # transformers / lmdeploy / vllm
  batch_size: 1
```

### Docker配置
- GPU版本: `docker/docker-compose.gpu.yml`
- CPU版本: `docker/docker-compose.cpu.yml`

## 📊 性能对比

| 模式 | 处理速度 | 内存使用 | 适用场景 |
|------|----------|----------|----------|
| GPU模式 | 快 (0.84页/秒) | 高 (6GB+) | 生产环境、大批量处理 |
| CPU模式 | 中等 | 中等 (4GB+) | 开发测试、小批量处理 |

## 🐳 Docker使用指南

详细的Docker配置和使用说明请参考：[Docker GPU支持指南](docker/README_GPU.md)

### 常用命令

```bash
# 启动服务
docker-compose -f docker/docker-compose.cpu.yml up -d

# 查看日志
docker-compose -f docker/docker-compose.cpu.yml logs -f

# 停止服务
docker-compose -f docker/docker-compose.cpu.yml down

# 进入容器
docker-compose -f docker/docker-compose.cpu.yml exec monkeyocr-cpu bash
```

## 🌐 API接口

启动服务后，可通过以下接口访问：

- **健康检查**: `GET http://localhost:8000/health`
- **文档处理**: `POST http://localhost:8000/parse`
- **文本提取**: `POST http://localhost:8000/extract/text`
- **表格提取**: `POST http://localhost:8000/extract/table`
- **公式识别**: `POST http://localhost:8000/extract/formula`

## 📝 使用示例

### 命令行使用
```bash
# 基本处理
python parse.py document.pdf

# 批量处理
python parse.py input_folder/ -g 20

# 指定输出目录
python parse.py document.pdf -o ./output/

# 仅提取文本
python parse.py document.pdf -t text
```

### API调用
```bash
# 上传文档处理
curl -X POST "http://localhost:8000/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

## 🔍 故障排除

### 常见问题

1. **GPU不可用**
   - 检查NVIDIA驱动安装
   - 确认CUDA版本兼容性
   - 使用CPU版本作为替代

2. **内存不足**
   - 减少batch_size设置
   - 使用CPU版本
   - 增加系统内存

3. **模型加载失败**
   - 检查模型文件路径
   - 确认网络连接
   - 查看详细错误日志

### 获取帮助

```bash
# 查看帮助信息
python parse.py --help

# 运行系统测试
python test-current-setup.py

# Docker环境测试
docker-compose -f docker/docker-compose.cpu.yml exec monkeyocr-cpu python3 docker/test-cpu.py
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目！

## 📄 许可证

本项目基于原MonkeyOCR项目，请遵守相应的开源许可证。

## 🔗 相关链接

- [MonkeyOCR原项目](https://github.com/opendatalab/MonkeyOCR)
- [Docker官方文档](https://docs.docker.com/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit)

## 📞 支持

如遇问题，请提供以下信息：
- 系统环境信息
- 错误日志
- 复现步骤
- 配置文件内容

---

**最后更新**: 2025年1月  
**版本**: v1.0  
**维护者**: lin2000wl
