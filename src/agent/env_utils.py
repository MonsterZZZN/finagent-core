"""
环境变量读取工具。

集中从项目根目录的 .env 文件加载所有配置项，暴露为模块级常量，
其他模块统一从这里取值，避免到处散落 os.getenv。

设计原则：本模块只依赖标准库 + python-dotenv，保持极轻量，
        这样连接测试等场景无需安装完整依赖即可使用。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# .env 位于项目根目录：本文件在 src/agent/env_utils.py，
# parents[0]=agent, parents[1]=src, parents[2]=项目根
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# 加载 .env（如果不存在则静默跳过，使用系统环境变量或默认值）
load_dotenv(ENV_PATH)


# ===== 大模型 =====
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# ===== 数据库 =====
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017/")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "finagent")
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

# ===== 跨项目服务地址 =====
RESEARCH_SERVICE_URL = os.getenv("RESEARCH_SERVICE_URL", "")
KB_SERVICE_URL = os.getenv("KB_SERVICE_URL", "")

# ===== MCP Server =====
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8003"))
MCP_PATH = os.getenv("MCP_PATH", "/mcp")

# ===== 运行环境 =====
APP_ENV = os.getenv("APP_ENV", "development")


def check_required() -> list[str]:
    """
    检查必填环境变量，返回缺失项列表（空列表表示齐全）。
    用于启动前的健康检查。
    """
    missing = []
    if not DEEPSEEK_API_KEY:
        missing.append("DEEPSEEK_API_KEY")
    if not MONGODB_URI:
        missing.append("MONGODB_URI")
    return missing
