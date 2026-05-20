"""
配置中心。

集中定义：模型参数、数据库连接、路径常量、子 Agent 作用域映射。
所有"可配置的东西"都在这里，其他模块从这里取，不要散落硬编码。

设计原则：模型对象用工厂函数延迟创建（get_main_model 等），
        导入本模块本身不需要安装 langchain 等重依赖，
        便于配置/连接的早期验证。
"""

from pathlib import Path

from agent import env_utils

# ============================================================
# 一、模型配置
# ============================================================
# 用 DeepSeek（OpenAI 兼容接口）。模型名说明：
#   deepseek-chat     → DeepSeek-V3（通用对话，主力）
#   deepseek-reasoner → DeepSeek-R1（强推理，按需）

MAIN_MODEL_CONFIG = {
    "model": "deepseek-chat",
    "openai_api_key": env_utils.DEEPSEEK_API_KEY,
    "openai_api_base": env_utils.DEEPSEEK_BASE_URL,
    "temperature": 0.7,
}

# 摘要专用模型：要求输出稳定，温度调低
SUMMARY_MODEL_CONFIG = {
    "model": "deepseek-chat",
    "openai_api_key": env_utils.DEEPSEEK_API_KEY,
    "openai_api_base": env_utils.DEEPSEEK_BASE_URL,
    "temperature": 0.3,
}


def get_main_model():
    """延迟创建主 Agent 模型（需要 langchain-openai）。"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(**MAIN_MODEL_CONFIG)


def get_summary_model():
    """延迟创建摘要模型。"""
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(**SUMMARY_MODEL_CONFIG)


# ============================================================
# 二、数据库
# ============================================================
MONGODB_URI = env_utils.MONGODB_URI
MONGODB_DB_NAME = env_utils.MONGODB_DB_NAME
MONGODB_CHECKPOINT_COLLECTION = "checkpoints"
REDIS_URL = env_utils.REDIS_URL


def get_checkpointer():
    """
    延迟创建 MongoDB checkpointer（保存 Agent 对话状态）。
    需要 langgraph-checkpoint-mongodb + pymongo。
    """
    from langgraph.checkpoint.mongodb import MongoDBSaver
    from pymongo import MongoClient
    client = MongoClient(MONGODB_URI)
    return MongoDBSaver(
        client=client,
        db_name=MONGODB_DB_NAME,
        checkpoint_collection_name=MONGODB_CHECKPOINT_COLLECTION,
    )


def get_store():
    """
    延迟创建 Store（保存用户记忆/技能）。
    开发期用内存 Store；生产可换持久化实现。
    """
    from langgraph.store.memory import InMemoryStore
    return InMemoryStore()


# ============================================================
# 三、路径常量
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"

# 本地资源目录
LOCAL_SKILLS_DIR = SRC_ROOT / "skills"
LOCAL_SUBAGENT_CONFIG_DIR = SRC_ROOT / "agent" / "subagents" / "configs"
LOCAL_AGENTS_MD = SRC_ROOT / "agent" / "memory" / "AGENTS.md"
DOWNLOAD_DIR = PROJECT_ROOT / "download"

# 沙箱内路径（Agent 运行时在沙箱里看到的路径）
SANDBOX_SKILLS_ROOT = "/skills"
SANDBOX_MEMORIES_ROOT = "/memories"
SANDBOX_ANALYSIS_ROOT = "/analysis"
SANDBOX_DATA_ROOT = "/data"

# 文件名常量
AGENTS_MD_FILENAME = "/AGENTS.md"
USER_PREFERENCES_FILENAME = "preferences.md"


# ============================================================
# 四、子 Agent 作用域映射（子 Agent 名 → 技能目录）
# ============================================================
SCOPE_MAP = {
    "main": "main",
    "research-proxy": "research",
    "risk-analyst": "risk",
    "market-pulse": "market",
    "report-writer": "report",
}


# ============================================================
# 五、跨项目服务地址
# ============================================================
RESEARCH_SERVICE_URL = env_utils.RESEARCH_SERVICE_URL
KB_SERVICE_URL = env_utils.KB_SERVICE_URL
