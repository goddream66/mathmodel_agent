# Mathmodel_agent（数学建模智能体）

Mathmodel_agent 是一款面向数学建模竞赛（尤其是国赛 3 天紧凑赛程）的智能体框架：你只需提供题目 PDF，它就能以“流程化工作流”的方式帮助你快速产出思路与论文草稿。

核心理念：用一个总控智能体把建模、编程实验、论文写作拆成三个专家智能体协同完成，实现 1+1+1+1>>4。

## 主要能力（当前版本 + 可扩展）

- **总控 + 三专家 agent**：建模手、编程手、论文手按阶段协作（见 [agents](file:///d:/trae_project/trae_mathagent/src/mathagent/agents)）
- **共享但隔离的统一数据库（SQLite）**：共享区保存关键中间结果，同时各 agent 有独立命名空间（见 [sqlite_store.py](file:///d:/trae_project/trae_mathagent/src/mathagent/memory/sqlite_store.py)）
- **PDF 题面读取 + 可选 OCR**：文字版 PDF 直接提取文字；图片/表格截图可用 OCR 追加识别文本（见 [loaders.py](file:///d:/trae_project/trae_mathagent/src/mathagent/io/loaders.py)）
- **结构化分题分析范式**：自动拆分子问题，逐题输出任务类型、候选模型/算法、求解流程、数据需求与评价方式（见 [problem_analysis.py](file:///d:/trae_project/trae_mathagent/src/mathagent/skills/problem_analysis.py)）
- **每个 agent 独立 LLM 配置**：同一项目里不同 agent 可使用不同厂商/中转站 API（统一走 OpenAI 兼容接口）

说明：
- 图表绘制与论文“国奖风格”写作目前以模板与 LLM 可选增强为主；后续可以在编程手/论文手中接入数据、自动绘图与更严格的论文规范模板。

## 你需要哪些“东西”（小白版）

### 1) 大模型（LLM）
相当于“脑子”，负责推理、写作、提出方案。框架会把它当作一个可替换的组件：你用什么模型都行（本地/云端）。

### 2) Tool / MCP（相当于“手”）
智能体光会想还不够，还要会“做”。常见能力：
- 跑 Python 做计算、画图、仿真
- 读写文件（数据、图片、论文、模板）
- 搜索资料（竞赛套路、算法要点、参数含义）
- 调用求解器（线性规划、整数规划、最短路、最小费用流、非线性优化等）

MCP 可以理解为“标准插口”：只要某个外部能力按 MCP 的规则提供服务，智能体就能像插 USB 一样接上用（不必每次手写对接逻辑）。

### 3) Skill（相当于“招式/套路”）
Skill 是可复用的“任务套路”，比如：
- “把题目转成数学符号与假设”
- “挑选合适模型（回归/分类/规划/图论/仿真）”
- “自动生成实验计划（对比基线、做消融、做敏感性分析）”
- “把结果写成论文段落（含表格/图注）”

在这个仓库里，Skill 会被做成可以组合的模块：你随时能新增、替换、打包复用。

### 4) Memory / Knowledge（相当于“笔记本/资料库”）
两类记忆最有用：
- 项目记忆：当前题目的变量定义、关键假设、已选方法、实验结论
- 资料库：常见建模模板、算法清单、写作模板、过往案例

### 5) Guardrails（相当于“质检”）
建模智能体最容易“看起来很像，但其实不对”。所以要有自动检查：
- 量纲/单位检查
- 约束是否自洽、变量是否定义
- 结果是否可复现（随机种子、依赖版本、输出文件）
- 结论是否和图表/数值一致

## 本仓库的代码结构（骨架）

```
src/mathagent/
  app.py              # 入口：一次建模任务怎么跑
  orchestrator.py     # 流程编排：按阶段调用 skills/tools
  state.py            # 统一的任务状态（题目、假设、模型、结果）
  skills/             # “招式”：每个阶段一个可插拔模块
  tools/              # “手”：统一工具接口与注册表（可接 MCP）
tests/
```

## 运行方式（先跑通骨架）

1) 创建虚拟环境（可选）
2) 安装为可编辑模式（推荐，便于开发）：

```bash
python -m pip install -e .
```

3) 如果要读取 PDF 题目，额外安装：

```bash
python -m pip install -e .[pdf]
```

4) 如果 PDF 里有图片（表格截图/图表），并且你希望识别图片里的文字，额外安装 OCR：

```bash
python -m pip install -e .[ocr]
```

5) 运行：

```bash
python -m mathagent
```

你会看到一个“空实现但可跑”的流程输出。接下来你要做的就是：
- 把 LLM 适配器接入（把“脑子”接上）
- 把 Python 执行/求解器/搜索 等工具接入（把“手”接上）
- 逐个完善 Skills（把“套路”补齐）

## 多厂商 LLM 接入（每个 agent 独立配置）

当前采用“OpenAI 兼容接口”作为统一接入层：只要厂商/中转站提供 OpenAI 风格的接口（`/v1/chat/completions`），就能接入。

每个 agent 可以单独配置自己的 `PROVIDER / BASE_URL / API_KEY / MODEL`（用环境变量区分）：
- `MODELING_API_KEY` / `MODELING_BASE_URL` / `MODELING_MODEL` / `MODELING_PROVIDER`
- `CODING_API_KEY` / `CODING_BASE_URL` / `CODING_MODEL` / `CODING_PROVIDER`
- `WRITING_API_KEY` / `WRITING_BASE_URL` / `WRITING_MODEL` / `WRITING_PROVIDER`
- `MANAGER_API_KEY` / `MANAGER_BASE_URL` / `MANAGER_MODEL` / `MANAGER_PROVIDER`

示例（OpenAI）：

```bash
set MODELING_PROVIDER=openai
set MODELING_BASE_URL=https://api.openai.com
set MODELING_API_KEY=你的key
set MODELING_MODEL=gpt-4o-mini
```

示例（中转站/代理，OpenAI 兼容）：

```bash
set WRITING_PROVIDER=openai_compat
set WRITING_BASE_URL=https://你的中转站域名
set WRITING_API_KEY=你的key
set WRITING_MODEL=你在中转站配置的模型名
```
