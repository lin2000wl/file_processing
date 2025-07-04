# MonkeyOCR Docker GPU 支持指南

## 🎯 概述

由于在VMware虚拟机中直接安装NVIDIA驱动存在兼容性问题，我们提供了基于Docker的GPU支持方案。这种方案更加稳定且易于管理。

## 📋 前提条件

### 1. 系统要求
- Ubuntu 20.04+ 或其他支持Docker的Linux发行版
- Docker 20.10+
- NVIDIA Container Toolkit (已安装)

### 2. 已完成的配置
✅ Docker已安装并运行  
✅ NVIDIA Container Toolkit已安装  
✅ Docker GPU运行时已配置  

## 🚀 快速启动

### 方案1: GPU版本（推荐，如果有GPU直通）
```bash
# 启动GPU版本
./docker/start-gpu.sh
```

### 方案2: CPU版本（当前环境适用）
```bash
# 启动CPU版本
docker-compose -f docker/docker-compose.cpu.yml up -d
```

## 📊 服务验证

### 检查服务状态
```bash
# GPU版本
docker-compose -f docker/docker-compose.gpu.yml ps

# CPU版本
docker-compose -f docker/docker-compose.cpu.yml ps
```

### 测试GPU支持
```bash
# 运行GPU测试
docker-compose -f docker/docker-compose.gpu.yml exec monkeyocr-gpu python3 /app/docker/test-gpu.py
```

### 测试MonkeyOCR功能
```bash
# 进入容器
docker-compose -f docker/docker-compose.gpu.yml exec monkeyocr-gpu bash

# 运行测试
python3 parse.py /app/test_document.pdf
```

## 🔧 配置说明

### GPU版本配置
- **基础镜像**: `nvidia/cuda:11.8-devel-ubuntu22.04`
- **PyTorch**: GPU版本 (CUDA 11.8)
- **设备**: `device: cuda` (自动检测)
- **后端**: `lmdeploy` (高性能GPU推理)

### CPU版本配置
- **基础镜像**: `ubuntu:22.04`
- **PyTorch**: CPU版本
- **设备**: `device: cpu` (强制CPU)
- **后端**: `transformers` (CPU友好)

## 📁 文件结构

```
docker/
├── Dockerfile.gpu          # GPU版本Docker镜像
├── Dockerfile.cpu          # CPU版本Docker镜像
├── docker-compose.gpu.yml  # GPU版本服务编排
├── docker-compose.cpu.yml  # CPU版本服务编排
├── model_configs_cpu.yaml  # CPU版本模型配置
├── test-gpu.py             # GPU测试脚本
├── start-gpu.sh            # GPU版本启动脚本
└── README_GPU.md           # 本说明文档
```

## 🌐 服务访问

启动成功后，可以通过以下地址访问：

- **API服务**: http://localhost:8000
- **Redis**: localhost:6379
- **健康检查**: http://localhost:8000/health

## 📋 常用命令

### 启动服务
```bash
# GPU版本
docker-compose -f docker/docker-compose.gpu.yml up -d

# CPU版本
docker-compose -f docker/docker-compose.cpu.yml up -d
```

### 停止服务
```bash
# GPU版本
docker-compose -f docker/docker-compose.gpu.yml down

# CPU版本
docker-compose -f docker/docker-compose.cpu.yml down
```

### 查看日志
```bash
# GPU版本
docker-compose -f docker/docker-compose.gpu.yml logs -f

# CPU版本
docker-compose -f docker/docker-compose.cpu.yml logs -f
```

### 进入容器
```bash
# GPU版本
docker-compose -f docker/docker-compose.gpu.yml exec monkeyocr-gpu bash

# CPU版本
docker-compose -f docker/docker-compose.cpu.yml exec monkeyocr-cpu bash
```

### 重新构建镜像
```bash
# GPU版本
docker-compose -f docker/docker-compose.gpu.yml build --no-cache

# CPU版本
docker-compose -f docker/docker-compose.cpu.yml build --no-cache
```

## 🔍 故障排除

### 问题1: GPU不可用
**现象**: 容器中显示GPU不可用
**解决方案**:
1. 检查宿主机GPU状态
2. 确认VMware GPU直通配置
3. 验证NVIDIA驱动安装

### 问题2: 容器启动失败
**现象**: 容器无法启动
**解决方案**:
1. 检查Docker服务状态
2. 查看容器日志
3. 确认端口未被占用

### 问题3: 内存不足
**现象**: 模型加载失败
**解决方案**:
1. 增加虚拟机内存
2. 使用CPU版本
3. 减少batch_size

## 📈 性能对比

| 模式 | 处理速度 | 内存使用 | 推荐场景 |
|------|----------|----------|----------|
| GPU版本 | 快 | 高 | 生产环境，大量处理 |
| CPU版本 | 慢 | 中 | 开发测试，小量处理 |

## 🎯 推荐使用

**当前环境推荐**: 使用CPU版本
- 虚拟机环境更稳定
- 功能完整可用
- 适合开发和测试

**生产环境推荐**: 使用云GPU实例
- 性能更好
- 更稳定可靠
- 成本可控

## 📞 技术支持

如遇问题，请提供以下信息：
1. 错误日志
2. 系统配置
3. Docker版本
4. 具体操作步骤 