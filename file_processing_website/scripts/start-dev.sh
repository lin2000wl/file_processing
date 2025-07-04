#!/bin/bash

# 文件处理网站开发环境启动脚本
# 同时启动前端和后端服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo -e "${BLUE}🚀 启动文件处理网站开发环境...${NC}"
echo -e "${BLUE}项目目录: $PROJECT_ROOT${NC}"

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}📋 检查依赖...${NC}"
    
    # 检查Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Node.js: $(node --version)${NC}"
    
    # 检查Python
    if ! command -v python &> /dev/null; then
        echo -e "${RED}❌ Python 未安装${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python: $(python --version)${NC}"
    
    # 检查Redis
    if ! command -v redis-server &> /dev/null; then
        echo -e "${YELLOW}⚠️  Redis 未安装，尝试启动服务...${NC}"
    fi
}

# 启动Redis
start_redis() {
    echo -e "${YELLOW}🔧 启动Redis服务...${NC}"
    
    # 检查Redis是否已经运行
    if pgrep redis-server > /dev/null; then
        echo -e "${GREEN}✅ Redis已在运行${NC}"
    else
        # 尝试启动Redis
        if command -v redis-server &> /dev/null; then
            redis-server --daemonize yes
            sleep 2
            if pgrep redis-server > /dev/null; then
                echo -e "${GREEN}✅ Redis启动成功${NC}"
            else
                echo -e "${RED}❌ Redis启动失败${NC}"
                exit 1
            fi
        else
            echo -e "${RED}❌ Redis未安装，请先安装Redis${NC}"
            exit 1
        fi
    fi
}

# 启动后端
start_backend() {
    echo -e "${YELLOW}🐍 启动后端服务器...${NC}"
    
    cd "$BACKEND_DIR"
    
    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        echo -e "${RED}❌ 后端虚拟环境不存在，请先运行 setup.sh${NC}"
        exit 1
    fi
    
    # 激活虚拟环境并启动
    source .venv/bin/activate
    
    echo -e "${BLUE}启动FastAPI服务器 (http://localhost:8000)...${NC}"
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    
    # 等待后端启动
    echo -e "${YELLOW}等待后端服务器启动...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 后端服务器启动成功 (PID: $BACKEND_PID)${NC}"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ 后端服务器启动超时${NC}"
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi
    done
}

# 启动前端
start_frontend() {
    echo -e "${YELLOW}⚡ 启动前端服务器...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 安装前端依赖...${NC}"
        npm install
    fi
    
    echo -e "${BLUE}启动Vue.js开发服务器 (http://localhost:3000)...${NC}"
    npm run dev &
    FRONTEND_PID=$!
    
    # 等待前端启动
    echo -e "${YELLOW}等待前端服务器启动...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 前端服务器启动成功 (PID: $FRONTEND_PID)${NC}"
            break
        fi
        sleep 1
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ 前端服务器启动超时${NC}"
            kill $FRONTEND_PID 2>/dev/null || true
            kill $BACKEND_PID 2>/dev/null || true
            exit 1
        fi
    done
}

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}🛑 正在停止服务器...${NC}"
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 前端服务器已停止${NC}"
    fi
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ 后端服务器已停止${NC}"
    fi
    
    echo -e "${BLUE}👋 开发环境已关闭${NC}"
    exit 0
}

# 设置信号处理
trap cleanup SIGINT SIGTERM

# 主函数
main() {
    check_dependencies
    start_redis
    start_backend
    start_frontend
    
    echo -e "\n${GREEN}🎉 开发环境启动完成！${NC}"
    echo -e "${BLUE}📱 前端地址: http://localhost:3000${NC}"
    echo -e "${BLUE}🔧 后端地址: http://localhost:8000${NC}"
    echo -e "${BLUE}📚 API文档: http://localhost:8000/docs${NC}"
    echo -e "\n${YELLOW}按 Ctrl+C 停止所有服务器${NC}"
    
    # 保持脚本运行
    wait
}

# 运行主函数
main 