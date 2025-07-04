#!/bin/bash

# 文件处理网站后端启动脚本

echo "🚀 启动文件处理网站后端服务..."

# 检查虚拟环境是否存在
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    uv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查依赖是否安装
if [ ! -f ".venv/pyvenv.cfg" ] || ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 正在安装依赖..."
    uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    echo "✅ 依赖安装完成"
fi

# 启动服务
echo "🌐 启动服务器 http://localhost:8000"
echo "📚 API文档: http://localhost:8000/docs"
echo "🛑 按 Ctrl+C 停止服务"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 