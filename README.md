# IP 地址使用信息平台

基于 **FastAPI + Vue3 + Element Plus + SQLite** 的内网 IP 分配与使用信息管理工具。

## 介绍

因为办公网络内固定IP的设备越来越多了，市面上现有的平台功能复杂，多出很多不需要的功能，故自己写一个平台记录网络中的设备信息。喜欢的朋友可以一起开发维护。

平台使用AI辅助开发(其实是我辅助AI开发)，可能由于测试不到位一些BUG没有发现。

## 功能

- IP 记录的新增、编辑、删除
- 按关键词 / 状态筛选与分页
- 状态统计：空闲 / 使用中 / 预留 / 停用
- 网段占用示意图
- CSV / Excel 导入导出（同 IP 自动更新）
- 用户登录鉴权（JWT）
- 网段存活检测（ICMP Ping，支持一键登记）
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

默认管理员账号：`admin` / `admin123`  
（可通过环境变量 `ADMIN_USERNAME`、`ADMIN_PASSWORD`、`JWT_SECRET` 覆盖）

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
docker run -d -p 8000:8000 \
  --cap-add=NET_RAW --cap-add=NET_ADMIN \
  -v ip_manager_data:/data \
  --name ip-manager ip-manager:latest
```

### 生产环境更新

```bash
# 拉取/同步最新代码后
docker compose up -d --build
```

不要使用 `docker compose down -v`，否则会删除数据卷。

### 检测工具在 Docker 下的说明

检测是在**容器/服务器所在网络**发起的，不是浏览器那台电脑。

常见原因与处理：

1. 旧镜像没有 `ping`：需重新 `docker compose up -d --build`
2. 缺少 ICMP 权限：`docker-compose.yml` 已配置 `cap_add: NET_RAW`
3. 服务器与办公网不在同一网段：容器扫不到你内网设备
4. 目标禁 Ping：现已补充 TCP 常见端口探测兜底

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
| POST | `/api/auth/login` | 登录获取 Token |
| GET | `/api/auth/me` | 当前用户信息 |
| POST | `/api/scan/subnet` | 网段存活检测 |
| GET | `/api/ip-records` | 分页查询 |
| GET | `/api/ip-records/stats` | 状态统计 |
| GET | `/api/ip-records/export?format=csv\|xlsx` | 导出 |
| GET | `/api/ip-records/import/template?format=csv\|xlsx` | 下载导入模板 |
| POST | `/api/ip-records/import` | 上传 CSV/Excel 导入 |
| POST | `/api/ip-records` | 新增 |
| PUT | `/api/ip-records/{id}` | 更新 |
| DELETE | `/api/ip-records/{id}` | 删除 |
