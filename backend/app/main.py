from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import ip_records

Base.metadata.create_all(bind=engine)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(
    title="IP Manager API",
    description="IP 地址使用信息管理平台",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ip_records.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# 必须放在 API 路由之后：Docker 单镜像时由后端直接托管前端构建产物
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="frontend")
