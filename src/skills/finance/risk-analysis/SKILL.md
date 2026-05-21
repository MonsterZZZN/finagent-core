---
name: risk-analysis
description: >
  金融组合风险分析技能。计算持仓集中度、VaR/波动率、相关性、期货保证金/强平距离、
  压力测试，并把风险数字翻译成易懂的解读。当任务涉及"风险体检"、"VaR"、"保证金"、
  "强平"、"集中度"、"压力测试"、"持仓诊断"等关键词时加载此技能。
---

# 金融风险分析技能（操作手册）

## 适用场景
- 持仓体检（综合风险评分）
- 单仓风险评估
- 期货账户专项（保证金占用 / 强平距离）—— 见 scripts/margin_analyzer.py（步骤5b）
- 组合压力测试 —— 见 scripts/stress_test.py（步骤5b）
- 相关性诊断 —— 见 scripts/correlation_calc.py（步骤5b）

## 数据约定：持仓格式

主 Agent / 子 Agent 传入的持仓统一为这个结构：

```json
[
  {"ticker": "600519", "name": "贵州茅台", "market_value": 300000, "industry": "白酒"},
  {"ticker": "000858", "name": "五粮液",   "market_value": 200000, "industry": "白酒"},
  {"ticker": "300750", "name": "宁德时代", "market_value": 100000, "industry": "电池"}
]
```

- `ticker`、`market_value` 必填；`name`、`industry` 用于解读和集中度。

## 分析流程

### 第 1 步：持仓校验
检查 positions 完整性（ticker / market_value 必填）。缺失 → 报错让主 Agent 补全，**绝不猜测**。

### 第 2 步：集中度分析（scripts/concentration.py）
把 positions 写入 `/data/positions.json`，运行：
```bash
python scripts/concentration.py /data/positions.json
```
输出：单股最大集中度、股票 HHI、行业 HHI、Top 行业、各权重。

### 第 3 步：波动率与 VaR（scripts/var_calculator.py）
1. 对每只持仓，用 `market_data_kline` 工具取近 60 日 K 线
2. 由收盘价算日收益率
3. 按持仓权重合成"组合日收益率序列"
4. 写入 `/data/returns.json`，运行：
```bash
python scripts/var_calculator.py /data/returns.json
```
输出：1 日 95% VaR、CVaR、年化波动率。

### 第 4 步：对照阈值（data/thresholds.yaml）
把各指标和阈值对比，分 **关注 / 警示 / 危险** 三档，找出超标项。

### 第 5 步：风险解读
读 `reference/interpretation_style.md`，把数字翻译成人话：
- 突出最重要的 3-5 个风险点（按严重程度排序）
- 每个风险点用"数字 + 类比 + 关注点"表达
- 末尾必须附风险提示

## 报告模板

```markdown
# 持仓风险评估报告

## 综合风险等级
{low / medium / high / critical}

## Top 风险点
1. {数字 + 通俗解释 + 建议关注}
2. ...

## 各维度明细
- 集中度：单股最高 X%，行业 HHI Y
- 波动率：年化 X%
- VaR：1日95%置信下，潜在损失约 X%

## 建议关注（非操作建议）
...

---
*以上基于公开信息，仅供研究参考，不构成投资建议。*
```

## 严格不做
- ❌ 不给买卖建议（"建议减仓 X%"）、不预测涨跌、不承诺收益
- ❌ 数字必须用脚本计算，**不能让 LLM 估算**
- ✅ 末尾必须附风险提示

## 期货账户分析流程（持仓含期货时）

期货与股票风险逻辑不同，含期货持仓时走此流程：
1. 把期货账户（动态权益 + 各持仓）写入 `/data/futures_account.json`
2. 运行 `python scripts/margin_analyzer.py /data/futures_account.json`
3. 得到：保证金占用率、各合约强平距离、最危险合约、单品种敞口、方向性集中
4. 对照 `data/exchange_margin_rules.yaml` 的阈值分档
5. 解读时参考 `reference/futures_methodology.md`，用"还能反向波动 X% 就追保"这种直观语言

## 当前已实现脚本
- ✅ `scripts/concentration.py` —— 集中度
- ✅ `scripts/var_calculator.py` —— VaR / 波动率
- ✅ `scripts/margin_analyzer.py` —— 期货保证金 / 强平距离 / 方向性集中
- ⬜ `scripts/stress_test.py` —— 压力测试（步骤5c）
- ⬜ `scripts/correlation_calc.py` —— 相关性（步骤5c）
