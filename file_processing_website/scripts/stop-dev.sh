#!/bin/bash

# 文件处理网站开发环境停止脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 停止文件处理网站开发环境...${NC}"

# 停止前端服务器 (Vue.js dev server)
echo -e "${YELLOW}停止前端服务器...${NC}"
pkill -f "vite" 2>/dev/null && echo -e "${GREEN}✅ 前端服务器已停止${NC}" || echo -e "${YELLOW}⚠️  前端服务器未运行${NC}"

# 停止后端服务器 (FastAPI/Uvicorn)
echo -e "${YELLOW}停止后端服务器...${NC}"
pkill -f "uvicorn" 2>/dev/null && echo -e "${GREEN}✅ 后端服务器已停止${NC}" || echo -e "${YELLOW}⚠️  后端服务器未运行${NC}"

# 可选：停止Redis（通常保持运行）
read -p "是否停止Redis服务? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}停止Redis服务...${NC}"
    pkill redis-server 2>/dev/null && echo -e "${GREEN}✅ Redis服务已停止${NC}" || echo -e "${YELLOW}⚠️  Redis服务未运行${NC}"
fi

echo -e "${GREEN}🎉 开发环境已停止${NC}" 