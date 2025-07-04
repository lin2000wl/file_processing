#!/bin/bash

# 文件处理网站测试运行脚本
# 用途：运行所有测试（后端+前端）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 运行后端测试
test_backend() {
    log_info "运行后端测试..."
    
    cd backend
    
    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        log_error "虚拟环境未找到，请先运行 ./scripts/setup-dev.sh"
        exit 1
    fi
    
    # 激活虚拟环境
    source .venv/bin/activate
    
    # 运行代码检查
    log_info "运行代码检查..."
    flake8 app/ || { log_error "代码检查失败"; exit 1; }
    black --check app/ || { log_error "代码格式检查失败"; exit 1; }
    isort --check-only app/ || { log_error "导入排序检查失败"; exit 1; }
    
    # 运行单元测试
    log_info "运行单元测试..."
    pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html:htmlcov || {
        log_error "后端测试失败"
        exit 1
    }
    
    cd ..
    log_success "后端测试通过"
}

# 运行前端测试
test_frontend() {
    log_info "运行前端测试..."
    
    cd frontend
    
    # 检查node_modules
    if [ ! -d "node_modules" ]; then
        log_error "前端依赖未安装，请先运行 ./scripts/setup-dev.sh"
        exit 1
    fi
    
    # 运行代码检查
    log_info "运行代码检查..."
    npm run lint || { log_error "前端代码检查失败"; exit 1; }
    
    # 运行类型检查
    log_info "运行类型检查..."
    npm run type-check || { log_error "类型检查失败"; exit 1; }
    
    # 运行单元测试
    log_info "运行单元测试..."
    npm run test || { log_error "前端测试失败"; exit 1; }
    
    # 运行构建测试
    log_info "运行构建测试..."
    npm run build || { log_error "构建失败"; exit 1; }
    
    cd ..
    log_success "前端测试通过"
}

# 运行集成测试
test_integration() {
    log_info "运行集成测试..."
    
    # 检查Redis是否运行
    if ! redis-cli ping &> /dev/null; then
        log_error "Redis未运行，请先启动Redis"
        exit 1
    fi
    
    # 启动后端服务器（后台）
    cd backend
    source .venv/bin/activate
    uvicorn app.main:app --host 127.0.0.1 --port 8001 &
    BACKEND_PID=$!
    cd ..
    
    # 等待服务器启动
    sleep 5
    
    # 运行集成测试
    cd backend
    pytest tests/integration/ -v || {
        log_error "集成测试失败"
        kill $BACKEND_PID
        exit 1
    }
    cd ..
    
    # 停止后端服务器
    kill $BACKEND_PID
    
    log_success "集成测试通过"
}

# 生成测试报告
generate_report() {
    log_info "生成测试报告..."
    
    # 创建报告目录
    mkdir -p reports
    
    # 合并覆盖率报告
    if [ -f "backend/htmlcov/index.html" ]; then
        cp -r backend/htmlcov reports/backend-coverage
        log_success "后端覆盖率报告: reports/backend-coverage/index.html"
    fi
    
    if [ -f "frontend/coverage/index.html" ]; then
        cp -r frontend/coverage reports/frontend-coverage
        log_success "前端覆盖率报告: reports/frontend-coverage/index.html"
    fi
}

# 主函数
main() {
    echo "=================================="
    echo "      文件处理网站测试套件"
    echo "=================================="
    echo ""
    
    # 解析命令行参数
    case "${1:-all}" in
        "backend")
            test_backend
            ;;
        "frontend")
            test_frontend
            ;;
        "integration")
            test_integration
            ;;
        "all")
            test_backend
            test_frontend
            test_integration
            ;;
        *)
            echo "用法: $0 [backend|frontend|integration|all]"
            echo ""
            echo "  backend     - 仅运行后端测试"
            echo "  frontend    - 仅运行前端测试"
            echo "  integration - 仅运行集成测试"
            echo "  all         - 运行所有测试（默认）"
            exit 1
            ;;
    esac
    
    generate_report
    
    echo ""
    echo "=================================="
    log_success "所有测试完成！"
    echo "=================================="
    echo ""
}

# 运行主函数
main "$@" 