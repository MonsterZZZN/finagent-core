"""
连接测试脚本。

验证能否连上 MongoDB 和 Redis，以及环境变量是否配好。
这是步骤 2 的验证手段——只依赖 python-dotenv + pymongo + redis，
不需要安装完整的 Agent 依赖。

用法（在服务器上、项目根目录、激活 venv 后）：
    python test_connection.py
"""

import sys
from pathlib import Path

# 把 src 加入导入路径，这样可以 import agent 包
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from agent import env_utils  # noqa: E402


def test_env():
    """检查环境变量"""
    print("=" * 50)
    print("【1】环境变量检查")
    print("=" * 50)
    print(f"  DEEPSEEK_API_KEY : {'✅ 已配置' if env_utils.DEEPSEEK_API_KEY else '⚠️  未配置（DB测试不需要，但跑Agent需要）'}")
    print(f"  MONGODB_URI      : {env_utils.MONGODB_URI}")
    print(f"  REDIS_URL        : {env_utils.REDIS_URL}")
    print()


def test_mongo():
    """测试 MongoDB 连接"""
    print("=" * 50)
    print("【2】MongoDB 连接测试")
    print("=" * 50)
    try:
        from pymongo import MongoClient
        client = MongoClient(env_utils.MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("  ✅ MongoDB 连接成功")
        client.close()
        return True
    except Exception as e:
        print(f"  ❌ MongoDB 连接失败：{e}")
        return False


def test_redis():
    """测试 Redis 连接"""
    print("=" * 50)
    print("【3】Redis 连接测试")
    print("=" * 50)
    try:
        import redis
        r = redis.from_url(env_utils.REDIS_URL, socket_connect_timeout=5)
        r.ping()
        print("  ✅ Redis 连接成功")
        return True
    except Exception as e:
        print(f"  ❌ Redis 连接失败：{e}")
        return False


if __name__ == "__main__":
    test_env()
    ok_mongo = test_mongo()
    print()
    ok_redis = test_redis()
    print()
    print("=" * 50)
    if ok_mongo and ok_redis:
        print("🎉 数据库连接全部正常！步骤 2 验证通过。")
    else:
        print("⚠️  有连接失败，请检查 docker 容器是否启动、.env 是否正确。")
    print("=" * 50)
