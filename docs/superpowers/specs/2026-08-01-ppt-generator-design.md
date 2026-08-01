# PPT Generator 技术设计方案

## 1. 项目背景与目标

本项目是一个招聘评估用的 PPT 生成器。输入为 JSON：

```json
{
  "topic": "主题",
  "brief": "简介（≤500 字）",
  "audience": "目标受众"
}
```

输出为一套 25–30 张的 `.pptx` 文件。核心要求是：**风格一致、叙事连贯**，不是独立卡片拼凑，也不能通过拆句、重复内容或放大标题凑页数。

优化目标按优先级排序：
1. 业务内容正确、合适
2. 美观度达到专业交付水准
3. 生成速度：平均单页 ≤ 30 秒
4. 生成成本：平均单页 ≤ ¥0.10

## 2. 关键决策

| 维度 | 选择 | 说明 |
| :--- | :--- | :--- |
| LLM 模型 | 字节火山方舟 `kimi-k2.6` | 通过 OpenAI 兼容 API 调用，`ARK_API_KEY` 环境变量配置 |
| 模板系统 | 约束模板 | 代码预定义 8–10 种版式，LLM 选择版式并填充字段 |
| 事实策略 | 混合策略 | 通用知识由 LLM 生成，具体事实（学费、截止日期、签证费等）由 Tavily 搜索验证 |
| 流水线 | 多阶段串行 | 规划 → 研究 → 内容生成 → 校验 → 渲染 |
| 搜索工具 | Tavily | `TAVILY_API_KEY` 环境变量配置 |
| 配图 | 图片搜索 API | 默认 Unsplash（免费），关键词由 LLM 生成 |
| 图标 | Phosphor Icons | 本地 SVG，离线可用 |
| PPT 渲染 | `python-pptx` | 标准 Python 库，稳定可靠 |

## 3. 总体架构

```
CLI/JSON Input
    ↓
[Pipeline Orchestrator]  ──→  Cost & Time Tracker
    ↓
[Stage 1: Planner]          (LLM: kimi-k2.6)
    ↓  outline + fact_queries[]
    ↓
[Stage 2: Researcher]       (Tavily API, parallel)
    ↓  research_report.json
    ↓
[Stage 3: Content Generator] (LLM: kimi-k2.6)
    ↓  slides.json (25-30 pages)
    ↓
[Stage 4: Validator]        (LLM: kimi-k2.6, optional)
    ↓  slides_final.json
    ↓
[Stage 5: Renderer]         (python-pptx + image search)
    ↓
output.pptx
```

### 核心组件

| 组件 | 职责 | 文件 |
| :--- | :--- | :--- |
| `PipelineOrchestrator` | 按顺序执行各阶段，记录耗时和成本，处理重试 | `PPT_Generator/pipeline.py` |
| `Planner` | 解析输入，生成叙事大纲和事实查询清单 | `PPT_Generator/planner.py` |
| `Researcher` | 调用 Tavily 搜索，汇总事实摘要 | `PPT_Generator/researcher.py` |
| `ContentGenerator` | 基于大纲和事实生成每页结构化内容 | `PPT_Generator/content_generator.py` |
| `Validator` | 检查页数、连贯性、事实一致性、版式合理性 | `PPT_Generator/validator.py` |
| `Renderer` | 将结构化内容渲染为 `.pptx` | `PPT_Generator/renderer.py` |
| `TemplateRegistry` | 注册和管理预定义版式 | `PPT_Generator/templates/` |
| `CostTracker` | 统计 LLM tokens、搜索调用、图片调用 | `PPT_Generator/cost_tracker.py` |
| `CLI` | 解析 JSON 输入、调用 pipeline、输出文件 | `PPT_Generator/cli.py` |

## 4. 数据契约

各阶段通过 Pydantic 模型传递。

```python
class Slide(BaseModel):
    page_number: int
    layout_id: str
    title: str
    subtitle: Optional[str] = None
    bullets: List[str] = []
    table: Optional[List[List[str]]] = None
    image_keyword: Optional[str] = None
    image_url: Optional[str] = None
    source_notes: List[str] = []
    notes: Optional[str] = None          # 演讲者备注，不渲染到页面

class Presentation(BaseModel):
    topic: str
    audience: str
    narrative_arc: str
    slides: List[Slide]
    total_pages: int
    sources: List[str]
```

## 5. 阶段详细设计

### Stage 1: Planner

**输入**：`topic`, `brief`, `audience`

**输出**：

```json
{
  "narrative_arc": "...",
  "sections": [
    {"section_title": "...", "pages": 5, "key_points": [...]}
  ],
  "fact_queries": [
    {"entity": "Imperial Business Analytics", "attributes": ["deadline", "tuition", "duration"]}
  ]
}
```

**Prompt 要求**：
- 输出 25–30 页大纲
- 结构：封面 → 引入 → 背景 → 主体（3–4 章节）→ 行动建议 → 结尾
- 必须列出需要搜索验证的事实清单

### Stage 2: Researcher

- 对 `fact_queries` 中每个 query 并行调用 Tavily
- 默认 `search_depth="basic"`，结果不足时升级到 `advanced`
- 使用 `include_answer=True` 获取直接摘要
- 输出：`{entity, attribute, value, source_url, confidence}`
- 置信度：`high` / `medium` / `low`

### Stage 3: Content Generator

**输入**：Planner 输出 + Researcher 输出

**输出**：`Presentation` 对象

**Prompt 要求**：
- 提供可用版式列表及字段要求
- 每页选择一个版式
- 不确定信息标注"尚未公布"或"需核实"
- 每页包含来源标注

### Stage 4: Validator

**检查项**：
1. 页数是否在 25–30 之间
2. 叙事是否连贯
3. 是否存在重复或空泛页面
4. 不确定信息是否已标注
5. 版式选择是否与内容匹配

**修复策略**：
- 页数不足：补充过渡页或深化章节
- 页数过多：合并或删除低价值页面
- 版式不匹配：建议更换版式

### Stage 5: Renderer

- 用 `python-pptx` 创建 `Presentation` 对象
- 根据 `layout_id` 选择对应版式函数
- 渲染文字、表格、图标
- 下载图片并插入（失败时使用纯色背景+文字回退）
- 保存 `.pptx`

## 6. 约束模板系统

### 设计原则

1. 版式数量控制在 8–10 个
2. 每个版式有固定字段
3. 统一设计系统（配色、字体、间距、图标）
4. 文本过长时自动缩小字号或截断

### 预定义版式

| layout_id | 用途 | 字段 |
| :--- | :--- | :--- |
| `title` | 封面 | title, subtitle, image_keyword |
| `section_divider` | 章节过渡页 | section_title, section_number, image_keyword |
| `bullet_focus` | 单点重点 | title, bullets[3-5], optional_image |
| `two_column` | 左右对比 | title, left_title, left_bullets, right_title, right_bullets |
| `three_card` | 三点并列 | title, cards[{title, bullet}] |
| `timeline` | 时间线 | title, events[{date, description}] |
| `comparison_table` | 表格对比 | title, headers[], rows[][] |
| `data_highlight` | 数据/数字强调 | title, big_number, description, source |
| `quote` | 引用/结论 | quote, source, context |
| `closing` | 结尾页 | title, bullets[行动建议] |

### 设计系统

- 画布尺寸：16:9（13.333 x 7.5 英寸）
- 主色调：深蓝 `#1E3A5F`，强调色 `#4A90D9`
- 字体：中文使用系统默认中文字体（Microsoft YaHei / PingFang SC），西文使用 Arial
- 边距：左右 0.8 英寸，上下 0.6 英寸
- 图标：Phosphor Icons，24px/32px/48px 三档

### 版式注册

```python
# PPT_Generator/templates/__init__.py
TEMPLATE_REGISTRY = {
    "title": TitleLayout(),
    "section_divider": SectionDividerLayout(),
    "bullet_focus": BulletFocusLayout(),
    # ...
}
```

每个 `Layout` 类实现 `render(slide: Slide, prs_slide)` 方法。

## 7. 成本控制

目标：每页平均成本 ≤ ¥0.10。

| 成本项 | 预估 | 控制方式 |
| :--- | :--- | :--- |
| LLM 调用（2–3 次） | ¥0.03–0.08/页 | 控制输出长度，减少调用次数 |
| Tavily 搜索 | ¥0.01–0.02/页 | 只搜索必要事实，basic depth |
| 图片搜索 | ¥0.00–0.01/页 | Unsplash 免费，控制图片数量 |
| 图标 | ¥0 | 本地 SVG |

**单页预估总成本：¥0.05–0.10**。

## 8. 速度控制

目标：每页平均时间 ≤ 30 秒（25 页总时间 ≤ 12.5 分钟）。

| 阶段 | 预估时间 |
| :--- | :--- |
| Planner | 10–20 秒 |
| Researcher（并行） | 10–30 秒 |
| Content Generator | 30–60 秒 |
| Validator | 10–20 秒 |
| Renderer | 5–15 秒 |
| **总计** | **65–145 秒** |

总时间可能超出单页 30 秒目标。后续优化方向：
1. 将 Content Generator 拆分为按章节并行
2. 对简单页面使用更快模型
3. 引入常见主题缓存

## 9. 错误处理与稳定性

| 故障点 | 处理策略 |
| :--- | :--- |
| LLM 输出非 JSON | 正则提取 JSON，失败重试 2 次；仍失败则跳过该阶段 |
| Tavily 搜索失败 | 单个 query 失败继续其他 query，该 query 标记为"未找到" |
| 图片下载失败 | 使用纯色背景或占位图标，不中断渲染 |
| 页数不足 25 | Validator 自动补充页面 |
| 页数超过 30 | Validator 自动合并或删除低价值页面 |
| 渲染异常 | 捕获异常，降级渲染（去掉图片/表格） |

所有外部调用统一封装 `retry_with_backoff`，最多 2 次重试，指数退避。重试成本计入总成本。

## 10. 测试策略

| 测试类型 | 内容 |
| :--- | :--- |
| 单元测试 | 每个 stage 独立测试，使用 mock LLM/搜索响应 |
| 集成测试 | 端到端生成一份 PPT，检查页数、文件可打开、无空页 |
| 模板测试 | 每个版式用假数据渲染一页，检查无溢出/重叠 |
| 成本测试 | 统计一次完整生成的 mock 成本，验证 ≤¥0.10/页 |

## 11. 可观测性

- `PipelineOrchestrator` 记录每个阶段的耗时和调用次数
- `CostTracker` 按调用类型汇总成本
- 输出报告中包含：总耗时、总成本、每页平均耗时/成本、LLM 调用次数、搜索次数

## 12. 环境与配置

### 依赖

- Python ≥ 3.9
- `python-pptx`
- `pydantic`
- `httpx` 或 `openai`
- `pytest`
- Phosphor Icons（静态资源）

### 环境变量

| 变量 | 说明 |
| :--- | :--- |
| `ARK_API_KEY` | 火山方舟 API key |
| `ARK_BASE_URL` | 方舟 OpenAI 兼容 endpoint（可选，默认已知） |
| `TAVILY_API_KEY` | Tavily API key |
| `UNSPLASH_ACCESS_KEY` | Unsplash Access Key（可选，未配置时降低图片质量或跳过） |

### 常用命令

```bash
# 激活环境
source .venv/bin/activate

# 安装依赖
pip install -e ".[dev]"

# 运行生成
python -m PPT_Generator input.json output.pptx

# 运行测试
pytest
```
