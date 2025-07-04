# 项目结构

## 目录结构
```
MonkeyOCR/
├── api/                    # FastAPI接口
├── demo/                   # Gradio演示
├── docker/                 # Docker配置
├── docs/                   # 文档
├── magic_pdf/              # 核心代码包
│   ├── config/            # 配置相关
│   ├── data/              # 数据处理
│   ├── dict2md/           # 内容转换
│   ├── filter/            # 过滤器
│   ├── libs/              # 工具库
│   ├── model/             # 模型相关
│   ├── operators/         # 操作符
│   ├── post_proc/         # 后处理
│   ├── pre_proc/          # 预处理
│   ├── resources/         # 资源文件
│   └── utils/             # 工具函数
├── tools/                  # 工具脚本
├── parse.py               # 主要解析脚本
├── model_configs.yaml     # 模型配置
├── requirements.txt       # 依赖列表
└── setup.py              # 安装脚本
```

## 核心模块
- **magic_pdf.model.custom_model**：核心模型类
- **magic_pdf.data.dataset**：数据集处理
- **magic_pdf.model.doc_analyze_by_custom_model_llm**：文档分析
- **magic_pdf.pdf_parse_union_core_v2_llm**：PDF解析核心