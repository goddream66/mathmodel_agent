# MathAgent

一个面向数学建模场景的多智能体框架脚手架。当前仓库的目标不是“一步到位自动写完论文”，而是先把建模任务拆成清晰的角色、流程、提示词、工具接口和 LLM 配置层，方便你后续逐步增强。

## 项目定位

这个项目目前更适合做三件事：

- 作为数学建模智能体的基础框架
- 快速验证多智能体协作流程
- 逐步接入你自己的模型、中转站、工具链和论文生成能力

当前整体流程大致是：

1. `Manager` 负责任务编排
2. `Modeling` 负责题目拆解、问题分析、建模方案组织
3. `Coding` 负责求解与产物生成
4. `Review` 负责检查结果与报告
5. `Writing` 负责把分析结果组织成论文草稿

## 当前代码结构

```text
src/mathagent/
  app.py                 # 程序入口
  orchestrator.py        # 流程编排骨架
  state.py               # 统一状态对象
  prompts.py             # Prompt 加载与渲染
  agents/
    base.py              # Agent 基类
    manager.py           # ManagerAgent
    specialists.py       # Modeling / Coding / Review / Writing
  llm/
    config.py            # LLM 配置加载：优先读 config/llm.json，回退到环境变量
    factory.py           # provider 到具体客户端的构建工厂
    openai_compat.py     # OpenAI 兼容接口客户端
    dashscope.py         # DashScope 客户端
    custom_http.py       # 自定义 HTTP 中转接口客户端
  skills/
    ...                  # 各阶段可插拔技能
  tools/
    ...                  # 工具注册与抽象
  memory/
    ...                  # 运行时记忆存储
```

## 安装

推荐先用可编辑模式安装：

```bash
python -m pip install -e .
```

如果你需要读取 PDF 题目：

```bash
python -m pip install -e .[pdf]
```

如果 PDF 里有图片，并且你还想做 OCR：

```bash
python -m pip install -e .[ocr]
```

如果你希望 `Coding` 阶段优先尝试真实数值库和求解器模板，可以额外安装：

```bash
python -m pip install -e .[solver]
```

这组可选依赖会为 fallback solver 提供更强的实现机会，包括：

- `numpy`
- `pandas`
- `scipy`
- `pulp`
- `networkx`
- `openpyxl`

## 运行

最简单的运行方式：

```bash
python -m mathagent
```

带题目文件运行：

```bash
python -m mathagent --problem-file problems/your_problem.txt
```

带表格数据运行：

```bash
python -m mathagent --problem-file problems/your_problem.txt --data-file data/forecast_series.csv
```

也支持 Excel：

```bash
python -m mathagent --problem-file problems/your_problem.txt --data-file data/forecast_series.xlsx
```

如果有多个数据文件，可以重复传入：

```bash
python -m mathagent --problem-file problems/your_problem.txt --data-file data/items.csv --data-file data/edges.csv
```

进入命令行多轮对话模式：

```bash
python -m mathagent --chat
```

在聊天模式下，你可以连续补充题目、约束、数据说明和论文要求，然后输入 `/run` 生成最新分析与论文草稿。

如果你只想导出或查看某几章，可以使用章节筛选：

```bash
python -m mathagent --problem-file problems/your_problem.txt --report-section abstract --report-section results
```

这会保留完整 `report.md`，同时额外输出一个只含选定章节的 `report_selected.md`。

聊天模式下可用的新命令：

- `/sections`：查看可用章节和当前筛选状态
- `/sections abstract results`：把当前报告输出切到指定章节
- `/sections all`：恢复完整报告
- `/report`：查看当前筛选后的报告
- `/report abstract conclusion`：临时查看指定章节

常见参数：

- `--problem-file`：输入题目文件，支持文本和 PDF 处理流程
- `--data-file`：附加 CSV、JSON 或 XLSX 数据文件，可重复传入
- `--db-path`：运行记忆数据库路径，默认 `data/mathagent.db`
- `--out-dir`：输出目录，默认 `outputs`
- `--report-section`：只导出指定章节，可重复传入
- `--ocr`：处理 PDF 时启用 OCR
- `--ocr-mode`：OCR 模式，可选 `auto`、`images`、`page`

程序运行后会在输出目录里生成：

- `problem_text.md`
- `report.md`（如果生成成功）
- `report_selected.md`（使用 `--report-section` 时）
- `chat_transcript.md` 和 `chat_report.md`（使用 `--chat` 时）
- `chat_report_selected.md`（聊天模式启用章节筛选后）

## 表格数据约定

现在的数据加载层会先做一轮表格语义识别，再把结果传给 `Coding` 阶段，所以列名不一定非得写成固定的英文单词。

当前重点增强了几类常见别名：

- 预测类：`date`、`time`、`period`、`day`、`demand`、`sales`、`qty`、`quantity`、`value`
- 优化类：`cost`、`price`、`expense`、`budget`、`value`、`profit`、`revenue`、`benefit`
- 路径/网络类：`source`、`from`、`start`、`target`、`to`、`end`、`weight`、`distance`、`cost`
- 评价类：`score`、`metric`、`index`、`weight`

也就是说，像下面这些列名现在都更容易被模板识别：

- 预测数据：`qty_sold`、`period`
- 路径数据：`from_node`、`to_node`、`travel_cost`
- 优化数据：`expense`、`benefit`

如果你装了 `.[solver]`，现在也可以直接读 `.xlsx`。单个工作表会按一个表处理，多工作表会拆成多个表传给求解阶段。

## LLM 配置说明

这一节是最重要的。现在推荐的配置方式是：

1. 复制 `config/llm.example.json`
2. 重命名为 `config/llm.json`
3. 在里面填写你自己的接口信息

仓库已经通过 `.gitignore` 忽略了 `config/llm.json`，所以真实 API Key 建议只放在本地文件里，不要提交到 GitHub。

### 1. 推荐方式：`config/llm.json`

最小示例：

```json
{
  "MODELING": {
    "provider": "openai_compat",
    "base_url": "https://api.openai.com",
    "api_key": "your-modeling-key",
    "model": "gpt-4o-mini"
  },
  "WRITING": {
    "provider": "openai_compat",
    "base_url": "https://api.openai.com",
    "api_key": "your-writing-key",
    "model": "gpt-4o-mini"
  }
}
```

当前支持的角色段名有：

- `MANAGER`
- `MODELING`
- `CODING`
- `REVIEW`
- `WRITING`

也就是说，`config/llm.json` 顶层就写这些 key。

完整示例：

```json
{
  "MANAGER": {
    "provider": "openai_compat",
    "base_url": "https://api.openai.com",
    "api_key": "your-manager-key",
    "model": "gpt-4o-mini"
  },
  "MODELING": {
    "provider": "openai_compat",
    "base_url": "https://api.openai.com",
    "api_key": "your-modeling-key",
    "model": "gpt-4o-mini"
  },
  "CODING": {
    "provider": "openai_compat",
    "base_url": "https://api.openai.com",
    "api_key": "your-coding-key",
    "model": "gpt-4o-mini"
  },
  "REVIEW": {
    "provider": "openai_compat",
    "base_url": "https://api.openai.com",
    "api_key": "your-review-key",
    "model": "gpt-4o-mini"
  },
  "WRITING": {
    "provider": "openai_compat",
    "base_url": "https://api.openai.com",
    "api_key": "your-writing-key",
    "model": "gpt-4o-mini"
  }
}
```

字段说明：

- `provider`：provider 名称
- `base_url`：接口域名
- `api_key`：你的密钥
- `model`：模型名
- `options`：特殊 provider 的附加参数，普通 OpenAI 兼容接口一般不需要

### 2. 当前支持的 provider

当前支持这些 provider：

- `openai`
- `openai_compat`
- `deepseek`
- `qwen`
- `bytedance`
- `google`
- `aliyun`
- `dashscope`
- `alibaba`
- `custom_http`

含义可以简单理解成：

- `openai`、`openai_compat`、`deepseek`、`qwen`、`bytedance`、`google`
  这些名称当前都走 OpenAI 兼容客户端
- `aliyun`、`dashscope`、`alibaba`
  这些名称当前走 DashScope 客户端
- `custom_http`
  给那些不完全兼容 OpenAI 格式的中转站或自建接口使用

### 3. 什么叫 OpenAI 兼容

“OpenAI 兼容”指的是对方接口大体遵循 OpenAI Chat Completions 的请求和返回格式。常见特征包括：

- 路径类似 `/v1/chat/completions`
- 请求体可以传 `model`、`messages`、`temperature`
- 返回体里可以从 `choices.0.message.content` 取到文本

如果你的中转站满足这一套，通常直接这样配就够了：

```json
{
  "WRITING": {
    "provider": "openai_compat",
    "base_url": "https://your-relay.example.com",
    "api_key": "your-key",
    "model": "your-model-name"
  }
}
```

### 4. 如果中转站不完全兼容：使用 `custom_http`

如果你的接口存在下面这些情况：

- 请求路径不是 `/v1/chat/completions`
- 认证头不是标准 Bearer
- 请求体字段名不一样
- 返回 JSON 里的文本路径不一样

就可以使用 `custom_http`。

示例：

```json
{
  "WRITING": {
    "provider": "custom_http",
    "base_url": "https://your-relay.example.com",
    "api_key": "your-writing-key",
    "model": "relay-model-name",
    "options": {
      "path": "/v1/chat/completions",
      "headers": {
        "Authorization": "Bearer {api_key}",
        "Content-Type": "application/json"
      },
      "body": {
        "model": "{model}",
        "messages": "$messages",
        "temperature": "$temperature"
      },
      "response_path": "choices.0.message.content"
    }
  }
}
```

这些配置项分别表示：

- `path`：请求路径，会和 `base_url` 拼接
- `headers`：自定义请求头
- `body`：自定义请求体模板
- `response_path`：从返回 JSON 中提取文本的路径

模板里可用的占位符有：

- `"{api_key}"`
- `"{model}"`
- `"{base_url}"`
- `"$messages"`
- `"$temperature"`

例如：

- `Authorization: "Bearer {api_key}"` 会自动替换成真实 key
- `"messages": "$messages"` 会自动替换成消息数组
- `"temperature": "$temperature"` 会自动替换成当前温度

### 5. 环境变量仍然可以用，但现在是回退方案

程序会优先读 `config/llm.json`。如果这个文件不存在，再回退到环境变量。

PowerShell 示例：

```powershell
$env:MODELING_PROVIDER = "openai_compat"
$env:MODELING_BASE_URL = "https://api.openai.com"
$env:MODELING_API_KEY = "your-key"
$env:MODELING_MODEL = "gpt-4o-mini"
```

命名规则是：

- `<角色名>_PROVIDER`
- `<角色名>_BASE_URL`
- `<角色名>_API_KEY`
- `<角色名>_MODEL`

例如：

- `MANAGER_API_KEY`
- `MODELING_API_KEY`
- `CODING_API_KEY`
- `REVIEW_API_KEY`
- `WRITING_API_KEY`

### 6. 你现在最推荐的配置方式

如果你现在的目标只是先跑通项目，建议直接这样做：

1. 复制 `config/llm.example.json` 为 `config/llm.json`
2. 先配置 `MODELING` 和 `WRITING`
3. 如果接口是标准 OpenAI 风格，优先用 `openai_compat`
4. 只有当中转站的请求或返回格式不标准时，再改用 `custom_http`

补充说明：

- 当前代码里，`MODELING` 和 `WRITING` 是直接会用到 LLM 的核心角色
- `MANAGER` 的配置会被记录到运行记忆里，方便后续扩展
- `CODING` 和 `REVIEW` 的配置段已经预留好了，后续你可以继续把它们接上

## 测试

运行测试：

```bash
python -m pytest -q tests
```

## 后续建议

如果你下一步想把它真正做成“可多轮对话、最终出论文”的系统，比较推荐按这个顺序继续补：

1. 先稳定 `MODELING` 的输出结构
2. 给 `CODING` 接入真正的求解工具或 Python 执行能力
3. 强化 `REVIEW` 的校验逻辑
4. 把 `WRITING` 的论文模板和章节控制做细
5. 再加前端或聊天入口，支持多轮交互
