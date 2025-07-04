# 建议的命令

## 安装和设置
```bash
# 安装项目
pip install -e .

# 下载模型权重
python tools/download_model.py

# 从ModelScope下载模型
python tools/download_model.py -t modelscope
```

## 主要使用命令
```bash
# 基本文档解析
python parse.py input_path

# 指定输出目录和配置文件
python parse.py input_path -o ./output -c model_configs.yaml

# 单任务识别
python parse.py input_path -t text      # 文本识别
python parse.py input_path -t formula   # 公式识别
python parse.py input_path -t table     # 表格识别

# 批量处理
python parse.py /path/to/folder         # 处理文件夹
python parse.py /path/to/folder -g 20   # 分组处理（最多20页）

# 分页处理
python parse.py input_path -s           # 按页分割结果
```

## 服务运行
```bash
# 启动Gradio演示
python demo/demo_gradio.py

# 启动FastAPI服务
uvicorn api.main:app --port 8000
```

## Docker部署
```bash
# 构建Docker镜像
cd docker
docker compose build monkeyocr

# 运行Gradio演示
docker compose up monkeyocr-demo

# 运行开发环境
docker compose run --rm monkeyocr-dev
```

## 系统工具
- **git**：版本控制
- **ls**, **cd**, **find**, **grep**：文件系统操作
- **nvidia-smi**：GPU监控
- **htop**：系统监控