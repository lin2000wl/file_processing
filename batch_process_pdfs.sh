#!/bin/bash
# 批量处理PDF文件脚本
# 处理pdf目录下的所有PDF文件

# 脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# PDF文件目录
PDF_DIR="$SCRIPT_DIR/pdf"

# 输出目录
OUTPUT_DIR="$SCRIPT_DIR/output"

# 虚拟环境路径
VENV_PATH="$SCRIPT_DIR/venv"

echo "🚀 批量PDF处理工具"
echo "=================================================="

# 检查PDF目录是否存在
if [ ! -d "$PDF_DIR" ]; then
    echo "❌ PDF目录不存在: $PDF_DIR"
    exit 1
fi

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

# 文件重命名函数
rename_files() {
    echo "📝 开始重命名PDF文件..."
    echo "--------------------------------------------------"
    
    # 使用find命令查找所有PDF文件，并用while循环处理（支持包含空格的文件名）
    find "$PDF_DIR" -name "*.pdf" -type f -print0 | while IFS= read -r -d '' file; do
        # 获取文件名（不含路径）
        filename=$(basename "$file")
        
        # 获取不含扩展名的文件名
        name_without_ext="${filename%.*}"
        
        # 替换特殊字符为下划线
        # 替换空格、中文标点、特殊符号等
        new_name=$(echo "$name_without_ext" | sed 's/[[:space:]]\+/_/g' | \
                   sed 's/[，。！？；：""''（）【】《》〈〉「」『』〔〕［］｛｝]/\_/g' | \
                   sed 's/[,\.!?;:"(){}[\]<>]/\_/g' | \
                   sed 's/[-]/\_/g' | \
                   sed 's/_\+/_/g' | \
                   sed 's/^_\|_$//g')
        
        # 添加.pdf扩展名
        new_filename="${new_name}.pdf"
        new_file="$PDF_DIR/$new_filename"
        
        # 如果文件名发生了变化，则重命名
        if [ "$filename" != "$new_filename" ]; then
            if mv "$file" "$new_file"; then
                echo "✅ 重命名: $filename → $new_filename"
            else
                echo "❌ 重命名失败: $filename"
            fi
        else
            echo "ℹ️  无需重命名: $filename"
        fi
    done
    
    echo "--------------------------------------------------"
    echo "📝 文件重命名完成"
    echo ""
}

# 执行文件重命名
rename_files

# 重新查找所有PDF文件（重命名后）
echo "🔍 重新扫描PDF文件..."
PDF_FILES=()
while IFS= read -r -d '' file; do
    PDF_FILES+=("$file")
done < <(find "$PDF_DIR" -name "*.pdf" -type f -print0)

if [ ${#PDF_FILES[@]} -eq 0 ]; then
    echo "❌ 在 $PDF_DIR 目录下未找到任何PDF文件"
    exit 1
fi

echo "📁 找到 ${#PDF_FILES[@]} 个PDF文件:"
for file in "${PDF_FILES[@]}"; do
    echo "   - $(basename "$file")"
done

echo ""
echo "🎯 开始批量处理..."
echo "=================================================="

# 统计变量
total_files=${#PDF_FILES[@]}
success_count=0
failed_count=0
failed_files=()

# 处理每个PDF文件
for i in "${!PDF_FILES[@]}"; do
    file="${PDF_FILES[$i]}"
    file_num=$((i + 1))
    filename=$(basename "$file")
    
    echo ""
    echo "📄 处理文件 $file_num/$total_files: $filename"
    echo "--------------------------------------------------"
    
    # 使用parse_enhanced.py处理文件
    if python "$SCRIPT_DIR/parse_enhanced.py" "$file" -o "$OUTPUT_DIR"; then
        echo "✅ 成功处理: $filename"
        ((success_count++))
    else
        echo "❌ 处理失败: $filename"
        ((failed_count++))
        failed_files+=("$filename")
    fi
    
    echo "--------------------------------------------------"
done

# 显示最终统计
echo ""
echo "🎉 批量处理完成！"
echo "=================================================="
echo "📊 处理统计:"
echo "   总文件数: $total_files"
echo "   成功处理: $success_count"
echo "   处理失败: $failed_count"

if [ $failed_count -gt 0 ]; then
    echo ""
    echo "❌ 失败的文件:"
    for failed_file in "${failed_files[@]}"; do
        echo "   - $failed_file"
    done
fi

echo ""
echo "📁 结果保存在: $OUTPUT_DIR"
echo "=================================================="

# 显示输出目录结构
if [ $success_count -gt 0 ]; then
    echo ""
    echo "📂 输出目录结构:"
    ls -la "$OUTPUT_DIR" 2>/dev/null || echo "输出目录为空或不存在"
fi 