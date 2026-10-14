# IP 地址使用信息平台

基于 **FastAPI + Vue3 + Element Plus + SQLite** 的内网 IP 分配与使用信息管理工具。

## 功能

- IP 记录的新增、编辑、删除
- 按关键词 / 状态筛选与分页
- 状态统计：空闲 / 使用中 / 预留 / 停用
- 记录字段：IP、网段、状态、主机名、MAC、使用人、部门、位置、备注

## 目录结构

```text
ip_manager/
├── backend/              # FastAPI 后端
│   ├── app/
│   └── requirements.txt
├── frontend/             # Vue3 前端
├── Dockerfile            # 单镜像构建（前后端合一）
└── docker-compose.yml
```

## Docker 一键部署（推荐）

将前端构建产物与后端打包进同一个镜像，启动后通过同一端口访问网站与 API。

```bash
# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f
```

浏览器访问：http://127.0.0.1:8000

- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health
- SQLite 数据通过 Docker volume `ip_manager_data` 持久化到容器内 `/data`

停止服务：

```bash
docker compose down
```

仅构建镜像：

```bash
docker build -t ip-manager:latest .
docker run -d -p 8000:8000 -v ip_manager_data:/data --name ip-manager ip-manager:latest
```

## 环境要求（本地开发）

- Python 3.10+（已在 Python 3.14 验证）
- Node.js 18+
- Docker / Docker Compose（可选，用于容器部署）

## 启动后端

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后：

- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器访问：http://127.0.0.1:5173

前端开发服务器已配置 `/api` 代理到后端 `8000` 端口。

## 主要 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/ip-records` | 分页查询 |
| GET | `/api/ip-records/stats` | 状态统计 |
| POST | `/api/ip-records` | 新增 |
| PUT | `/api/ip-records/{id}` | 更新 |
| DELETE | `/api/ip-records/{id}` | 删除 |
