# TXT文件输出目录配置

## 📁 修改说明

现在所有生成的TXT文件都会统一保存到项目根目录下的 `txt/` 目录中，而不是分散在各个处理结果目录中。

## 🔧 修改的文件

### 1. enhanced_txt_generator.py
- **修改位置**: `main()` 函数中的默认输出路径
- **修改内容**: 
  ```python
  # 修改前
  output_path = f"{args.pdf_name}.txt"
  
  # 修改后
  import os
  os.makedirs("txt", exist_ok=True)
  output_path = f"txt/{args.pdf_name}.txt"
  ```

### 2. parse_enhanced.py
- **修改位置**: `generate_txt_file()` 方法中的TXT文件保存路径
- **修改内容**:
  ```python
  # 修改前
  txt_path = os.path.join(result_dir, txt_filename)
  
  # 修改后
  txt_dir = "txt"
  os.makedirs(txt_dir, exist_ok=True)
  txt_path = os.path.join(txt_dir, txt_filename)
  ```

### 3. post_process_enhancement.py
- **修改位置**: `generate_txt_file()` 方法中的TXT文件保存路径
- **修改内容**:
  ```python
  # 修改前
  txt_path = self.result_dir / txt_filename
  
  # 修改后
  txt_dir = Path("txt")
  txt_dir.mkdir(exist_ok=True)
  txt_path = txt_dir / txt_filename
  ```

## 📂 目录结构

修改后的目录结构：
```
file_processing/
├── txt/                          # 📁 所有TXT文件统一存放目录
│   ├── document1.txt            # 文档1的TXT文件
│   ├── document2.txt            # 文档2的TXT文件
│   └── ...
├── output/                       # 其他处理结果（MD、PDF、JSON等）
│   ├── document1/
│   │   ├── document1.md
│   │   ├── document1_middle.json
│   │   └── ...
│   └── ...
└── ...
```

## 🎯 优势

1. **集中管理**: 所有TXT文件集中在一个目录，便于查找和管理
2. **避免重复**: 不会在每个处理结果目录中都生成TXT文件
3. **清晰结构**: 将TXT文件与其他处理结果分离，目录结构更清晰
4. **便于备份**: 可以单独备份txt目录中的所有文本文件

## 🚀 使用方法

### 手动生成TXT文件
```bash
# 使用enhanced_txt_generator.py（自动保存到txt目录）
python3 enhanced_txt_generator.py "path/to/middle.json" "pdf_name"

# 或指定自定义输出路径
python3 enhanced_txt_generator.py "path/to/middle.json" "pdf_name" -o "custom/path.txt"
```

### 自动生成（在PDF处理过程中）
使用 `parse_enhanced.py` 或 `post_process_enhancement.py` 时，TXT文件会自动保存到 `txt/` 目录。

## ✅ 验证

修改完成后，您可以：
1. 运行任何TXT生成命令
2. 检查 `txt/` 目录是否自动创建
3. 确认TXT文件是否正确保存在该目录中
4. 验证TXT文件内容是否完整（包含完整的文档内容，而不是省略标记）

## 🔧 图片显示修复

### 问题描述
之前的版本中，图片在TXT文件中只显示为`[图像]`，丢失了图片路径和标题信息。

### 修复内容
修改了`enhanced_txt_generator.py`中的`_process_image_block`方法，现在能够正确提取：
- 图片路径：从`blocks[].lines[].spans[].image_path`字段
- 图片标题：从`image_caption`类型的块中提取

### 修复效果
现在图片在TXT文件中的显示格式为：
```
[图像] images/19d92a5cdcbb723356d70a4f572c61af14b7d5d770464bc7ca58350997a0f584.jpg
图1 配光屏幕
```

而不是简单的：
```
[图像]
```

## 📝 注意事项

- `txt/` 目录会在首次生成TXT文件时自动创建
- 如果指定了自定义输出路径（使用 `-o` 参数），仍会使用指定的路径
- 现有的其他输出格式（MD、PDF、JSON等）不受影响，仍保存在原来的位置
- 图片信息现在包含完整的路径和标题，便于定位和理解 