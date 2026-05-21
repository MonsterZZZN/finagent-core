"""
MCP Server 启动入口。

创建 FastMCP 实例，注册各数据工具组，以 streamable-http 方式启动。
Agent 端通过 MCP 协议连接本服务调用数据工具。

启动方式（在 src 目录下）：
    python -m mcp_server.server_main
"""

from fastmcp import FastMCP

from mcp_server.server_config import MCP_HOST, MCP_PORT, MCP_PATH
from mcp_server.tools.market_data_tools import register_market_data_tools

# 创建 MCP Server 实例
mcp = FastMCP(
    name="FinAgent-Data-MCP",
    instructions="金融数据查询工具集：行情、财报、新闻、公告、期货、宏观",
    version="1.0.0",
)

# 注册工具组（后续步骤会逐步增加：portfolio / news / earnings / futures / macro）
register_market_data_tools(mcp)


def main():
    """启动 MCP Server（streamable-http 传输）。"""
    print(f"[MCP] 启动金融数据服务 → http://{MCP_HOST}:{MCP_PORT}{MCP_PATH}")
    mcp.run(
        transport="streamable-http",
        host=MCP_HOST,
        port=MCP_PORT,
        path=MCP_PATH,
    )


if __name__ == "__main__":
    main()
