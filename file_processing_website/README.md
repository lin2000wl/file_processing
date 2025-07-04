# 文件处理网站

基于 MonkeyOCR 的智能文档解析平台，支持 PDF 和图像文件的 OCR 识别、表格提取、公式识别等功能。

## 🚀 快速开始

### 开发环境启动

使用统一启动脚本，一键启动前后端服务器：

```bash
# 启动开发环境（包含前端、后端、Redis）
./scripts/start-dev.sh

# 停止开发环境
./scripts/stop-dev.sh
```

启动成功后：
- 📱 前端地址: http://localhost:3000
- 🔧 后端地址: http://localhost:8000  
- 📚 API文档: http://localhost:8000/docs

### 手动启动（可选）

如果需要分别启动前后端：

```bash
# 启动后端
cd backend
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端（新终端）
cd frontend
npm run dev
```

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: Redis
- **异步任务**: Celery
- **OCR引擎**: MonkeyOCR
- **Python**: 3.9+

### 前端
- **框架**: Vue.js 3
- **UI库**: Element Plus
- **语言**: TypeScript
- **构建工具**: Vite
- **状态管理**: Pinia

## 📋 功能特性

- ✅ 文件上传（拖拽支持）
- ✅ 多格式支持（PDF、PNG、JPG）
- ✅ 实时任务进度跟踪
- ✅ 批量文件处理
- ✅ 多种识别模式（文本、公式、表格）
- ✅ 结果预览和下载
- ✅ 响应式界面设计

## 🔧 开发指南

### 项目结构

```
file_processing_website/
├── backend/           # FastAPI 后端
│   ├── app/          # 应用代码
│   ├── .venv/        # Python 虚拟环境
│   └── requirements.txt
├── frontend/          # Vue.js 前端
│   ├── src/          # 源代码
│   ├── public/       # 静态资源
│   └── package.json
├── scripts/           # 启动脚本
├── docker/           # Docker 配置
└── docs/             # 文档
```

### 开发环境要求

- Node.js 16+
- Python 3.9+
- Redis 6+
- Git

### 代码规范

- 后端遵循 PEP 8 规范
- 前端使用 ESLint + Prettier
- 提交信息遵循 Conventional Commits

## 📖 API 文档

启动后端服务器后，访问 http://localhost:8000/docs 查看完整的 API 文档。

### 主要接口

- `GET /health` - 健康检查
- `POST /api/v1/files/upload` - 文件上传
- `GET /api/v1/tasks/` - 获取任务列表
- `POST /api/v1/tasks/create` - 创建处理任务
- `GET /api/v1/results/{task_id}` - 获取处理结果

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 检查端口占用
   lsof -i :3000
   lsof -i :8000
   
   # 杀死进程
   pkill -f vite
   pkill -f uvicorn
   ```

2. **Redis 连接失败**
   ```bash
   # 启动 Redis
   redis-server --daemonize yes
   
   # 检查 Redis 状态
   redis-cli ping
   ```

3. **依赖安装失败**
   ```bash
   # 后端依赖
   cd backend
   pip install -r requirements.txt
   
   # 前端依赖
   cd frontend
   npm install
   ```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**开发团队**: AI开发助手  
**最后更新**: 2025年1月 