#!/bin/bash
# 增强版PDF处理快速启动脚本
# 自动激活虚拟环境并运行parse_enhanced.py

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 虚拟环境路径
VENV_PATH="$SCRIPT_DIR/file_processing_website/backend/venv"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ 虚拟环境不存在: $VENV_PATH"
    echo "请先设置虚拟环境"
    exit 1
fi

# 激活虚拟环境
source "$VENV_PATH/bin/activate"

# 检查是否成功激活
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ 虚拟环境激活失败"
    exit 1
fi

echo "✅ 虚拟环境已激活: $VIRTUAL_ENV"

# 运行增强版处理脚本
echo "🚀 启动增强版PDF处理..."
python "$SCRIPT_DIR/parse_enhanced.py" "$@" 