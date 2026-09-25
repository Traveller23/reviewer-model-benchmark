# Reviewer Model Benchmark 页面生成工具

本工具读取同目录的 `statistics.json`, 生成可离线打开的 `charts.html`, 用于比较不同模型和推理强度在 4 项 Reviewer 基准中的分数, 平均耗时及等效 API 费用. 页面提供英文和中文切换, 包含 2 张柱状图, 3 张散点图, 以及可按需显示的帕累托前沿.

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

输入文件应为 `schemaVersion: 3` 的配置数组. 每个配置包含模型, 推理强度和若干 Reviewer 记录. 每个 Reviewer 记录必须有编号 1, 2, 3 的 3 个 `repetitions` 条目, 才能计算其分数.

单次重复使用 `repetitions[].score` 原始分数, 范围为 0 到 1. 当 `scoreSource` 为 `diagnostic` 时, 这次分数乘以 `0.9`. 未得分的条目 (`score: null`) 和得 0 分的条目都贡献 0. 每项 Reviewer 的分数始终是 3 次修正后分数之和除以 **3**, 不因某次未得分而缩小分母. 图表把结果乘以 100 显示.

综合分数仅对 4 项 Reviewer 都已有可计算分数的模型配置生成. 计算公式是:

```text
综合分数 = 100 × (
    0.20 × Code Standards
  + 0.20 × Code Spec
  + 0.25 × Commit Audit
  + 0.35 × Spec Readiness
)
```

公式中的各项 Reviewer 分数是 0 到 1 的修正后平均值. 尚未记录的整项 Reviewer 不会被当作 0 分; 其已有的其他分项可以出现在分项柱状图中, 但该配置暂不进入综合分数和散点图.

平均耗时是 4 项 Reviewer 的 `durationMs` 合计除以 3, 再换算为分钟. 等效 API 费用先汇总 4 项 Reviewer 的 `tokenUsage.input`, `tokenUsage.cachedInput` 和 `tokenUsage.output`, 分别除以 3, 再按 `build.py` 的 `PRICES` 每百万 token 单价计算并相加. 它表示按公开 API 单价换算的费用, 不一定是实际账单. 本地 Bonsai 2 按对应的阿里云北京 API 单价估算.

某项所需的耗时或 token 合计缺失时, 对应的耗时或费用记为不可用, 该配置不出现在需要该指标的散点图中. 缺少 token 数据不会影响已有分数. 三张散点图分别比较费用与分数, 耗时与分数, 耗时与费用; 每张图的帕累托前沿只针对该图中可见且指标完整的配置计算.

## 实现和维护

`build.py` 用 Python 读取 JSON 和计算指标, 用 Plotly 生成图表并把图表脚本嵌入 HTML. 页面文字和图表坐标轴可在英文与中文之间切换; 图表交互在浏览器本地运行. `resources/site.css` 和预下载字体控制页面样式.

模型及推理强度的固定顺序, 4 项 Reviewer 的权重, 模型颜色和 API 单价都定义在 `build.py` 顶部. 价格是 2026-09-25 核对的静态值. 如果供应商调整价格, 需要同时更新 `PRICES`, 页面方法说明中的价格核对日期, 再重新生成页面. 当前估算未包含缓存写入, 长上下文或工具附加费用.

本工具不运行 benchmark, 不读取原 effort 目录, 不自动同步新数据, 也不修改输入 JSON. `statistics.json` 应从可信的 benchmark 结果复制; 生成脚本只依据这份同目录快照工作.
