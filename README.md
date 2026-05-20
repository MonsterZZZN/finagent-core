# finagent-core

> 金融 AI 助手主入口项目
> FinAgent 平台的三个子项目之一（core / research / kb）

## 这是什么

finagent-core 是金融 AI 助手的**主入口**，负责理解用户意图、调度子 Agent、调用数据工具，并集成另外两个项目（深度研究 finagent-research、知识库 finagent-kb）。

技术底座基于 **DeepAgents + LangGraph**，采用「主 Agent + 子 Agent + Skills + MCP 工具」的分层架构。

## 核心能力

- **风险分析**：持仓体检、VaR、期货保证金/强平距离、压力测试
- **市场监控**：实时市场状态、异动归因
- **报告生成**：早盘简报、收盘复盘、调研报告
- **深度研究**（代理调用 finagent-research）
- **知识检索**（调用 finagent-kb）

## 技术栈

| 层 | 技术 |
|---|---|
| Agent 框架 | DeepAgents 0.4.12 + LangGraph |
| 数据工具 | FastMCP（MCP Server） |
| 大模型 | DeepSeek（OpenAI 兼容） |
| 数据源 | AKShare（免费） |
| 存储 | MongoDB（对话状态）+ Redis（缓存） |
| API | FastAPI + SSE |

## 快速开始

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env              # 然后编辑 .env 填入 DeepSeek key

# 4. 确保 MongoDB / Redis 已启动（见根目录环境部署教程）

# 5. 启动（待后续步骤完成）
# python start_web.py
```

## 项目结构

详见 [docs/项目结构说明.md](docs/项目结构说明.md) —— 每个目录和文件的作用都有说明。

```
finagent-core/
├── src/
│   ├── agent/          # Agent 核心（主 Agent、配置、中间件、子 Agent、工具）
│   ├── mcp_server/     # MCP 数据工具服务（行情/财报/新闻等）
│   ├── skills/         # 技能包（风险分析/市场监控/报告生成）
│   └── api_view/       # Web API 层
└── docs/               # 文档
```

## 开发进度

- [x] 步骤 1：项目骨架
- [ ] 步骤 2：配置层（连数据库）
- [ ] 步骤 3：记忆与人格
- [ ] 步骤 4：MCP 数据工具
- [ ] 步骤 5：风险分析 Skill
- [ ] 步骤 6：风险分析子 Agent
- [ ] 步骤 7：主 Agent
- [ ] 步骤 8：API 层
- [ ] 步骤 9：跨项目集成
- [ ] 步骤 10：合规中间件 + 打磨

## 许可与声明

本项目所有 AI 输出仅供研究参考，不构成投资建议。
