"""
MCP Server 配置。

从 env_utils 取 MCP 服务的 host/port/path。
"""

from agent import env_utils

MCP_HOST = env_utils.MCP_HOST   # 默认 127.0.0.1
MCP_PORT = env_utils.MCP_PORT   # 默认 8003
MCP_PATH = env_utils.MCP_PATH   # 默认 /mcp
