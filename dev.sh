#!/bin/bash
# ============================================================
# finagent-core 开发助手脚本
# 用法（在项目根目录）：bash dev.sh <命令>
#   bash dev.sh up        # 拉代码 + 同步依赖（最常用）
#   bash dev.sh conn      # 测数据库连接
#   bash dev.sh market    # 测行情工具
#   bash dev.sh mcp       # 启动 MCP 数据服务
#   bash dev.sh install   # 重装全部依赖
# ============================================================

# 切到脚本所在目录（项目根），并激活虚拟环境
cd "$(dirname "$0")" || exit 1
if [ -d venv ]; then
    source venv/bin/activate
fi

case "$1" in
  up)
    echo "📥 拉取最新代码..."
    if ! git pull; then
        echo "❌ 代码拉取失败（网络问题？）。代码未更新，请重试或检查 git 远程地址。"
        exit 1
    fi
    echo "📦 同步依赖（已装的会跳过）..."
    pip install -q -r requirements.txt || echo "⚠️  部分依赖安装有问题，把报错发给我"
    echo "✅ 更新完成"
    ;;
  install)
    echo "📦 安装全部依赖..."
    pip install -r requirements.txt
    ;;
  conn)
    python test_connection.py
    ;;
  market)
    python test_market_data.py
    ;;
  mcp)
    echo "🚀 启动 MCP 数据服务（Ctrl+C 停止）..."
    cd src && python -m mcp_server.server_main
    ;;
  *)
    echo "用法: bash dev.sh <命令>"
    echo "  up        拉代码 + 同步依赖（最常用）"
    echo "  install   安装全部依赖"
    echo "  conn      测数据库连接"
    echo "  market    测行情工具"
    echo "  mcp       启动 MCP 数据服务"
    ;;
esac
