# Reviewer Model Benchmark 页面生成工具

本工具读取同目录的 `statistics.json`, 生成可离线打开的 `charts.html`, 用于比较不同模型和推理强度在 4 项 Reviewer 基准中的分数, 平均耗时, 平均 token 用量及等效 API 费用. 页面提供英文和中文切换, 包含 5 张柱状图, 3 张散点图, 以及可按需显示的帕累托前沿.

这个页面是独立的比较视图. 它不会修改输入数据, 也不会替代 benchmark 自身生成的正式分项报告.

## 文件

将以下文件和目录放在一起:

```text
./
├── build.py
├── statistics.json
├── charts.html
├── README.md
└── resources/
    ├── site.css
    ├── favicon.svg
    └── fonts/
```

`statistics.json` 是输入数据的独立快照. 目前它的权威来源是 `${BENCHMARK_SOURCE_STATISTICS}`; 生成正式页面前, 先将该文件复制到本目录. `charts.html` 和 `resources/favicon.svg` 由 `build.py` 生成. `resources/site.css` 和 `resources/fonts/` 是页面所需的预下载资源. 保留整个 `resources/` 目录, 才能在其他计算机上按预期显示样式和字体. 字体许可和来源见 `resources/fonts/README.md`.

## 使用

生成页面需要 Python 和 Plotly. 本工具已用 Python 3.14.4 与 Plotly 6.9.0 验证. 以下命令在本目录执行:

```bash
cp ${BENCHMARK_SOURCE_STATISTICS} ./statistics.json
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

更新 benchmark 数据时, 按上述步骤重新复制权威文件, 然后运行 `build.py`. 页脚的更新日期是生成页面的日期.

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

等效 API 费用先对每项 Reviewer 的三类平均 token 用量, 使用 `build.py` 的 `PRICES` 每百万 token 单价计算费用, 再对有数据的 Reviewer 费用求算术平均值. 它不一定是实际账单. 本地 Bonsai 2 按对应的阿里云北京 API 单价估算.

某项 Reviewer 没有正分重复时, 它的耗时、token 和费用都不计算. 如果某次正分重复的上述指定场景没有可用耗时, 只忽略这次的耗时, 对其余有耗时记录的正分重复求平均; 只有一次可用耗时都没有, 该 Reviewer 的耗时才不计算. 如果某次正分重复的指定场景没有记全三类 token 数量, 就把这次从三类 token 的平均值中一起排除; 只有一次完整记录都没有, 该 Reviewer 的 token 和费用才不计算. token 数量为 0 是有效记录. 耗时与 token 独立计算, 某次缺少其中一项不影响另一项的平均值. 对应明细图只省略该 Reviewer 缺少数据的指标柱子, 并在图下说明原因; 评分明细仍显示该 Reviewer 的分数, 没有有效正分时显示 0. 模型与推理强度组合的耗时, token 或费用仍对其他有数据的 Reviewer 求平均; 只有四项 Reviewer 的某个运行指标均不可用时, 该组合才不出现在需要该指标的散点图中. 缺少 token 数据不会影响已有分数.

三张散点图分别比较费用与分数, 耗时与分数, 耗时与费用; 每张图的帕累托前沿只针对该图中可见且指标完整的配置计算. 费用与分数, 耗时与费用以及费用明细图均可切换费用轴的线性与对数刻度. token 明细是按 Reviewer 分组的堆叠柱状图, 从下到上依次是未缓存输入, 缓存输入, 输出; 三类 token 使用固定颜色.

## 实现和维护

`build.py` 用 Python 读取 JSON 和计算指标, 用 Plotly 生成图表并把图表脚本嵌入 HTML. 页面文字和图表坐标轴可在英文与中文之间切换; 图表交互在浏览器本地运行. `resources/site.css` 和预下载字体控制页面样式.

模型及推理强度的固定顺序, 4 项 Reviewer 的权重, 模型颜色和 API 单价都定义在 `build.py` 顶部. 价格是 2026-09-25 核对的静态值. 如果供应商调整价格, 需要同时更新 `PRICES`, 页面方法说明中的价格核对日期, 再重新生成页面. 当前估算未包含缓存写入, 长上下文或工具附加费用.

本工具不运行 benchmark, 不读取原 effort 目录, 不自动同步新数据, 也不修改输入 JSON. `statistics.json` 应从可信的 benchmark 结果复制; 生成脚本只依据这份同目录快照工作.
