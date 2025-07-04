#!/bin/bash

# 文件处理网站开发环境设置脚本
# 用途：一键设置完整的开发环境

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

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装 $1"
        exit 1
    fi
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查Python
    if command -v python3.9 &> /dev/null; then
        log_success "Python 3.9 已安装"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
        if [[ "$PYTHON_VERSION" == "3.9" ]] || [[ "$PYTHON_VERSION" > "3.9" ]]; then
            log_success "Python $PYTHON_VERSION 已安装"
        else
            log_error "需要 Python 3.9+，当前版本: $PYTHON_VERSION"
            exit 1
        fi
    else
        log_error "Python 未安装"
        exit 1
    fi
    
    # 检查Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [[ "$NODE_VERSION" -ge "18" ]]; then
            log_success "Node.js v$(node --version | cut -d'v' -f2) 已安装"
        else
            log_error "需要 Node.js 18+，当前版本: v$(node --version | cut -d'v' -f2)"
            exit 1
        fi
    else
        log_error "Node.js 未安装"
        exit 1
    fi
    
    # 检查Redis
    if command -v redis-server &> /dev/null; then
        log_success "Redis 已安装"
    else
        log_warning "Redis 未安装，将尝试使用Docker启动Redis"
        check_command docker
    fi
    
    # 检查UV
    if command -v uv &> /dev/null; then
        log_success "UV 已安装"
    else
        log_info "安装 UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        log_success "UV 安装完成"
    fi
}

# 设置后端环境
setup_backend() {
    log_info "设置后端环境..."
    
    cd backend
    
    # 创建虚拟环境
    if [ ! -d ".venv" ]; then
        log_info "创建Python虚拟环境..."
        uv venv
        log_success "虚拟环境创建完成"
    else
        log_info "虚拟环境已存在"
    fi
    
    # 安装依赖
    log_info "安装Python依赖..."
    uv pip install -r requirements.txt
    uv pip install -r requirements-dev.txt
    log_success "Python依赖安装完成"
    
    # 创建环境变量文件
    if [ ! -f ".env" ]; then
        log_info "创建环境变量文件..."
        cat > .env << EOF
# 开发环境配置
DEBUG=true
ENVIRONMENT=development

# Redis配置
REDIS_URL=redis://localhost:6379/0

# 文件存储配置
STORAGE_PATH=../storage
MAX_FILE_SIZE=52428800
MAX_TOTAL_SIZE=209715200

# MonkeyOCR配置
MODEL_CONFIGS_PATH=../../model_configs.yaml
MODELS_DIR=../../model_weight

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=../logs

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
        log_success "环境变量文件创建完成"
    else
        log_info "环境变量文件已存在"
    fi
    
    cd ..
}

# 设置前端环境
setup_frontend() {
    log_info "设置前端环境..."
    
    cd frontend
    
    # 安装依赖
    log_info "安装前端依赖..."
    npm install
    log_success "前端依赖安装完成"
    
    cd ..
}

# 创建存储目录
create_directories() {
    log_info "创建必要目录..."
    
    mkdir -p storage/{uploads,processing,results}
    mkdir -p logs
    mkdir -p model_weight
    
    log_success "目录创建完成"
}

# 启动Redis
start_redis() {
    log_info "启动Redis..."
    
    if command -v redis-server &> /dev/null; then
        # 检查Redis是否已运行
        if redis-cli ping &> /dev/null; then
            log_info "Redis 已在运行"
        else
            redis-server --daemonize yes
            log_success "Redis 启动完成"
        fi
    else
        # 使用Docker启动Redis
        if docker ps | grep -q redis; then
            log_info "Redis Docker容器已在运行"
        else
            docker run -d --name redis-dev -p 6379:6379 redis:7-alpine
            log_success "Redis Docker容器启动完成"
        fi
    fi
}

# 安装pre-commit hooks
setup_precommit() {
    log_info "设置pre-commit hooks..."
    
    cd backend
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        pip install pre-commit
        cd ..
        pre-commit install
        log_success "Pre-commit hooks 安装完成"
    else
        log_warning "虚拟环境未找到，跳过pre-commit安装"
    fi
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    # 后端测试
    cd backend
    source .venv/bin/activate
    pytest --cov=app --cov-report=term-missing
    cd ..
    
    # 前端测试
    cd frontend
    npm run test
    cd ..
    
    log_success "测试完成"
}

# 主函数
main() {
    echo "=================================="
    echo "  文件处理网站开发环境设置"
    echo "=================================="
    echo ""
    
    check_requirements
    create_directories
    setup_backend
    setup_frontend
    start_redis
    setup_precommit
    
    echo ""
    echo "=================================="
    log_success "开发环境设置完成！"
    echo "=================================="
    echo ""
    echo "下一步操作："
    echo "1. 启动开发服务器："
    echo "   ./scripts/start-dev.sh"
    echo ""
    echo "2. 运行测试："
    echo "   ./scripts/test.sh"
    echo ""
    echo "3. 查看日志："
    echo "   tail -f logs/app.log"
    echo ""
}

# 运行主函数
main "$@" 