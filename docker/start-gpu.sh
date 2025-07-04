#!/bin/bash

# MonkeyOCR GPU Docker 启动脚本
echo "🚀 启动MonkeyOCR GPU Docker环境..."

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 检查NVIDIA Container Toolkit
if ! which nvidia-ctk >/dev/null 2>&1; then
    echo "❌ NVIDIA Container Toolkit未安装"
    echo "请先运行: sudo apt install nvidia-container-toolkit"
    exit 1
fi

# 检查Docker配置
if ! docker info 2>/dev/null | grep -q "nvidia"; then
    echo "⚠️  Docker可能未正确配置GPU支持"
    echo "尝试重新配置..."
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    sleep 5
fi

# 切换到项目目录
cd "$(dirname "$0")/.."

# 创建必要的目录
mkdir -p storage/uploads storage/processing storage/results

# 构建并启动服务
echo "🔨 构建Docker镜像..."
docker-compose -f docker/docker-compose.gpu.yml build

echo "🚀 启动服务..."
docker-compose -f docker/docker-compose.gpu.yml up -d

echo "⏳ 等待服务启动..."
sleep 10

# 运行GPU测试
echo "🧪 运行GPU测试..."
docker-compose -f docker/docker-compose.gpu.yml exec monkeyocr-gpu python3 /app/docker/test-gpu.py

echo "✅ 启动完成！"
echo "📊 服务状态:"
docker-compose -f docker/docker-compose.gpu.yml ps

echo ""
echo "🌐 访问地址:"
echo "  - API服务: http://localhost:8000"
echo "  - Redis: localhost:6379"
echo ""
echo "📋 常用命令:"
echo "  - 查看日志: docker-compose -f docker/docker-compose.gpu.yml logs -f"
echo "  - 停止服务: docker-compose -f docker/docker-compose.gpu.yml down"
echo "  - 进入容器: docker-compose -f docker/docker-compose.gpu.yml exec monkeyocr-gpu bash" 