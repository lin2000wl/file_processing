#!/bin/bash

# 文件处理网站 - 前后端同时启动脚本
echo "🚀 启动文件处理网站..."

# 检查当前目录
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ 请在项目根目录运行此脚本"
    exit 1
fi

# 检查Redis是否运行
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis未运行，请先启动Redis服务"
    exit 1
fi

echo "✅ Redis服务正常"

# 启动后端服务器（后台运行）
echo "🔧 启动后端服务器..."
cd backend
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 3

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务启动成功: http://localhost:8000"
else
    echo "❌ 后端服务启动失败"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# 启动前端服务器
echo "🎨 启动前端服务器..."
cd frontend

# 设置清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    echo "✅ 服务已停止"
    exit 0
}

# 捕获Ctrl+C信号
trap cleanup SIGINT SIGTERM

echo "✅ 前端服务启动中..."
echo "📱 前端地址: http://localhost:3000"
echo "🔧 后端地址: http://localhost:8000"
echo "📄 API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "=========================="

# 启动前端（前台运行）
npm run dev

# 如果前端退出，清理后端
cleanup 