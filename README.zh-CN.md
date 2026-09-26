# Reviewer Model Benchmark 页面生成工具

**[English](README.md)** · 简体中文

[打开已发布的 Benchmark 页面](https://traveller23.github.io/reviewer-model-benchmark/)

本工具读取同目录的 `statistics.json`, 生成可离线打开的 `charts.html`, 用于比较不同模型和推理强度在 4 项 Reviewer 基准中的分数, 平均耗时, 平均 token 用量及等效 API 费用. 页面提供英文和中文切换, 包含 5 张柱状图, 3 张散点图, 以及可按需显示的帕累托前沿.

这个页面是独立的比较视图. 它不会修改输入数据, 也不会替代 benchmark 自身生成的正式分项报告.

## 测量范围与耗时

ARW 是提供这组开发审查任务的软件项目.

| Reviewer | 工作 | 综合分数权重 |
| --- | --- | ---: |
| Code Standards | 对照仓库指令与实现质量标准审查代码. | 20% |
| Code Spec | 检查改动是否落实已给出的要求. | 20% |
| Commit Audit | 审计暂存的提交候选及必要检查. | 25% |
| Spec Readiness | 实施前检查要求的完整性与可实现性. | 35% |

Reviewer 是 ARW 开发流程中执行特定代码或文档审查任务的 AI Agent. Code Standards、Code Spec、Commit Audit 各有一个固定场景, Spec Readiness 有两个场景. 五个 GPT 模型各测 `low`、`medium`、`high`、`xhigh`、`max`; 本地 Bonsai 2 测 `low`、`medium`、`xhigh`, 共 28 个配置. 每个配置对五个场景独立重复三次, 总共 420 次场景调用和 336 次角色重复. 当前快照的角色重复中, 99 次标记为诊断评分. 所有模型使用相同的可见场景材料和隐藏评分用例. 完整场景、原始报告与隐藏用例不在本仓库, 因此可以从快照重算图表, 不能仅靠快照重跑模型测量.

结果只描述这组固定任务, 不是通用模型排名, 也不授予生产审查资格.

正式模型采集的**墙上时间**, 以最终保留调用的第一个开始和最后一个结束为界. 时间均为日本时间 (UTC+09:00):

| 组别 | 开始 | 结束 | 墙上历时 |
| --- | --- | --- | ---: |
| GPT, 375 次调用 | 2026-09-24 22:35:09 | 2026-09-26 11:27:22 | 36 小时 52 分 13 秒 |
| 本地 Bonsai 2, 45 次调用 | 2026-09-25 09:25:15 | 2026-09-26 16:17:41 | 30 小时 52 分 26 秒 |
| 两组整体 | 2026-09-24 22:35:09 | 2026-09-26 16:17:41 | 41 小时 42 分 32 秒 |

两组**重叠了 26 小时 2 分 7 秒**: GPT 最多同时运行 3 次调用, Bonsai 2 单实例运行, 两组可以并行. 上表包含两次调用之间的暂停与恢复, 不含首个调用前的准备及最后调用后的评分、裁决和页面工作. GPT 起止点取自最终 375 份 Codex 会话的开始与完成时间; Bonsai 2 起止点取自与最终 45 次调用对应的 Windows worker 清单, 包括同一调用中的修订. 这些详细日志未公开, `statistics.json` 只保存各场景自己的耗时.

如果场景与本地运行程序已验证, **下次顺利重测可按约 25 小时排期**, 从准备到一次最终评分:

| 环节 | 估算口径 |
| --- | ---: |
| GPT 各实例耗时合计 39 小时 22 分 57 秒, 除以持续满载的 3 个并行名额 | 13 小时 7 分 39 秒 |
| Bonsai 2 各串行实例耗时合计 | 22 小时 6 分 24 秒 |
| 两组并行采集, 由 Bonsai 2 决定 | 约 22 小时 6 分 |
| 理想前期准备 | 30 分钟 |
| 一轮后期评分与核对 | 2 小时 15 分钟 |
| **理想排期合计** | **约 24 小时 51 分钟** |

前期与后期的时间是排期假设. 该估算要求 GPT 名额结束后立即补位, GPT 与 Bonsai 2 全程可重叠运行; 不包含这次遇到的修复、重跑与中断. 它不是实际墙上耗时, 也不是下次运行的保证值.

## 本地 Bonsai 2 部署

Bonsai 2 是 [Prism ML 基于 Qwen3.8-27B 制作的三值权重模型](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf). 本次使用的文件是 [Ternary-Bonsai-2-27B-PQ2_0.gguf](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/main/Ternary-Bonsai-2-27B-PQ2_0.gguf), 通过 [Prism ML 的 llama.cpp 运行程序](https://github.com/PrismML-Eng/Bonsai-demo)在 Windows 宿主机使用 CUDA 推理, 没有调用阿里云 API. 宿主机为 Intel Core i9-14900K、约 64 GB 内存、NVIDIA RTX 4070 Ti SUPER 16 GB 显存. balanced 启动档使用 200,000 token 上下文、单个服务槽位、GPU 全层 (`-ngl 99`)、`q8_0` K/V 缓存、batch 2048、microbatch 256、16 CPU 线程、8 个上下文检查点和 2 GiB 提示缓存 RAM 预算. 请求开启思考模式并转发 `low`、`medium` 或 `xhigh`, 同时只运行一个本地 worker. 之前的独立 150K-token 测试记录整卡显存峰值约 15.04 GiB; 那是另一项工作负载, 不是本次 Reviewer 测量的显存结果.

档位名称只是各模型的请求设置, 不表示相同计算量. [Prism ML 说明 Bonsai 2 的 `low` 可能表现得接近 `xhigh`](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf); 图中的标签不能证明两档行为有明确差异. GPT 使用托管的 Codex Reviewer 会话, 其运行环境与本地 Bonsai 2 不同, 读耗时图时应考虑这一点.

## 文件

仓库根目录的主要文件和目录如下:

```text
./
├── build.py
├── statistics.json
├── README.md
├── README.zh-CN.md
├── .env.example
├── .github/
│   └── workflows/
│       └── pages.yml
└── resources/
    ├── site.css
    ├── favicon.svg
    └── fonts/
```

`statistics.json` 是输入数据的独立快照. 维护者更新它时, 先将 `.env.example` 复制为已忽略的 `.env`, 再把可信来源文件的绝对路径填入 `BENCHMARK_SOURCE_STATISTICS`. 构建页面只读取已提交的 `statistics.json`, 不读取 `.env`, 也不会从其他目录自动同步数据. `charts.html` 是 `build.py` 生成的本地文件, 不提交到 Git; `resources/favicon.svg` 也由脚本生成, 但保存在仓库中. `resources/site.css` 和 `resources/fonts/` 是页面所需的预下载资源. 保留整个 `resources/` 目录, 才能在其他计算机上按预期显示样式和字体. 字体许可和来源见 `resources/fonts/README.md`.

在仓库根目录用 Bash 复制并核对新快照:

```bash
. ./.env
: "${BENCHMARK_SOURCE_STATISTICS:?请在 .env 设置 BENCHMARK_SOURCE_STATISTICS}"
cp -- "$BENCHMARK_SOURCE_STATISTICS" statistics.json
cmp -- "$BENCHMARK_SOURCE_STATISTICS" statistics.json
```

## 使用

生成页面需要 Python 和 Plotly. 本工具已用 Python 3.14.4 与 Plotly 6.9.0 验证. 以下命令在本目录执行:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install plotly==6.9.0
.venv/bin/python build.py
```

Windows 中可使用 `py -m venv .venv`, `.venv\Scripts\python -m pip install plotly==6.9.0` 和 `.venv\Scripts\python build.py`.

默认读取 `build.py` 同目录的 `statistics.json`, 并覆盖同目录的 `charts.html`. 也可以传入自定义输入和输出路径:

```bash
.venv/bin/python build.py path/to/statistics.json path/to/charts.html
```

输出页面通过相对路径加载 `resources/`. 若指定其他输出目录, 该目录也必须有对应的 `resources/` 文件夹. 用浏览器直接打开 `charts.html` 即可; 查看图表不需要 Python, 网络或 Web 服务器. 页面底部的外部价格资料链接需要联网才能访问.

更新 benchmark 数据时, 按上述步骤从 `.env` 指定的来源复制并核对文件, 然后运行 `build.py`. 页面页脚的“更新于”是页面构建日期, 不代表数据采集或价格核对日期.

## 计分和指标

输入文件应为 `schemaVersion: 4` 的配置数组. 每个配置包含模型, 推理强度, 逐场景 `observations` 和若干 Reviewer 记录. 每项 Reviewer 预期有编号 1, 2, 3 的 3 次重复; 缺少某次重复记录时, 该次分数按不可用处理, 仍可用其他正分重复计算 Reviewer 分数. 本工具只支持 v4, 不读取旧版角色或重复级的耗时及 token 汇总.

单次重复使用 `repetitions[].score` 原始分数, 范围为 0 到 1. 当 `scoreSource` 为 `diagnostic` 或 `mainAgentCorrectedScoringCopy` 为 `true` 时, 这次正分重复乘以一次 `0.9`; 两种状态同时出现仍只乘以一次 `0.9`.

Reviewer 的分数只对正分重复求平均. 某次重复为 0 分、分数不可用 (`score: null`), 或整条重复记录缺失时, 这次不参与平均; 只要出现其中任一种情况, 就在该 Reviewer 的正分平均值上乘以一次 `0.9`, 出现多次仍只乘一次, 也不影响其他 Reviewer 的平均分. 因此正分重复的状态折扣和 Reviewer 平均分的排除折扣最多各一次, 合计最多两次 `0.9` (`0.81`). 如果没有正分重复, 该 Reviewer 在综合分数中按 0 分计算. 图表把 Reviewer 分数乘以 100 显示.

每个模型与推理强度组合都使用 4 项 Reviewer 的固定权重计算综合分数. 计算公式是:

```text
综合分数 = 100 × (
    0.20 × Code Standards
  + 0.20 × Code Spec
  + 0.25 × Commit Audit
  + 0.35 × Spec Readiness
)
```

公式中的各项 Reviewer 分数是 0 到 1 的修正后平均值. 某项 Reviewer 为 0 分, 尚未记录, 或没有有效正分重复时, 该项按 0 分带入固定权重, 并在评分明细中显示 0; 不因缺项重新分配权重.

耗时和 token 只统计 `score` 大于 0 的重复; 诊断评分或 Main Agent 修正过评分副本的正分重复仍纳入. 每项 Reviewer 的每次正分重复, 从 `observations[]` 中找到对应场景, 只读取该场景的 `runtime.durationMs` 以及 `runtime.tokenUsage.input`, `cachedInput`, `output`. Code Standards, Code Spec 与 Commit Audit 取各自的 `default` 场景. Spec Readiness 的一次重复虽包含两个场景, 但只取完整审查的 `artifact-promotion` 场景; 提前返回的 `runtime-migration` 场景不参与耗时或 token 计算, 即内部既不求和也不平均.

先对每项 Reviewer 有耗时记录的正分重复求耗时的算术平均值; 三类 token 用量则对三类数量都记录完整的正分重复分别求算术平均值. 某个模型与推理强度组合在散点图中的耗时, 是有数据的 Reviewer 平均耗时的算术平均值; 三类 token 也分别取有数据的 Reviewer 对应平均用量的算术平均值.

等效 API 费用先对每项 Reviewer 的三类平均 token 用量, 使用 `build.py` 的 `PRICES` 每百万 token 单价计算费用, 再对有数据的 Reviewer 费用求算术平均值. 它不是实际账单. 本地 Bonsai 2 借用阿里云北京 `qwen3.8-27b` API 单价作比较代理, 实际没有发生这笔 API 费用; 估算也不包含本地硬件与电费.

某项 Reviewer 没有正分重复时, 它的耗时、token 和费用都不计算. 如果某次正分重复的上述指定场景没有可用耗时, 只忽略这次的耗时, 对其余有耗时记录的正分重复求平均; 只有一次可用耗时都没有, 该 Reviewer 的耗时才不计算. 如果某次正分重复的指定场景没有记全三类 token 数量, 就把这次从三类 token 的平均值中一起排除; 只有一次完整记录都没有, 该 Reviewer 的 token 和费用才不计算. token 数量为 0 是有效记录. 耗时与 token 独立计算, 某次缺少其中一项不影响另一项的平均值. 对应明细图只省略该 Reviewer 缺少数据的指标柱子, 并在图下说明原因; 评分明细仍显示该 Reviewer 的分数, 没有有效正分时显示 0. 模型与推理强度组合的耗时, token 或费用仍对其他有数据的 Reviewer 求平均; 只有四项 Reviewer 的某个运行指标均不可用时, 该组合才不出现在需要该指标的散点图中. 缺少 token 数据不会影响已有分数.

三张散点图分别比较费用与分数, 耗时与分数, 耗时与费用; 每张图的帕累托前沿只针对该图中可见且指标完整的配置计算. 费用与分数, 耗时与费用以及费用明细图均可切换费用轴的线性与对数刻度. token 明细是按 Reviewer 分组的堆叠柱状图, 从下到上依次是未缓存输入, 缓存输入, 输出; 三类 token 使用固定颜色.

## 实现和维护

`build.py` 用 Python 读取 JSON 和计算指标, 用 Plotly 生成图表并把图表脚本嵌入 HTML. 页面文字和图表坐标轴可在英文与中文之间切换; 图表交互在浏览器本地运行. `resources/site.css` 和预下载字体控制页面样式.

模型及推理强度的固定顺序, 4 项 Reviewer 的权重, 模型颜色和 API 单价都定义在 `build.py` 顶部. 价格是 2026-09-25 核对的静态值. 如果供应商调整价格, 需要同时更新 `PRICES`, 页面方法说明中的价格核对日期, 再重新生成页面. 当前估算未包含缓存写入, 长上下文或工具附加费用.

本工具不运行 benchmark, 不读取原 effort 目录, 不自动同步新数据, 也不修改输入 JSON. `statistics.json` 应从可信的 benchmark 结果复制; 生成脚本只依据这份同目录快照工作.

## GitHub Pages 发布

`.github/workflows/pages.yml` 从仓库内的快照生成 `index.html`, 并连同 `resources/`、`statistics.json` 和 `build.py` 发布. 页面资源使用相对路径, 因此可在仓库子路径访问. 在仓库设置中将 Pages 来源设为 **GitHub Actions**; GitHub Free 下仓库需要公开. 工作流不会设置自定义域名. 本地的 `charts.html` 仍不加入 Git.
