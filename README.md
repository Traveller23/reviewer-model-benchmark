# Reviewer Model Benchmark

**English** · [简体中文](README.zh-CN.md)

[Open the published benchmark page](https://cybersoul.net/reviewer-model-benchmark/)

This repository builds a static benchmark page from `statistics.json`. Scoring version **v1.1** compares five hosted GPT models, DeepSeek V4.1 Flash, and one locally served Bonsai 2 model on four AI review roles at different reasoning effort settings. The page has five bar charts, three scatter plots, and optional Pareto fronts. The results describe this specific workload, not a general model ranking or authorization for production review.

## Scoring version v1.1

The differences in previously measured scores come from a change in statistical treatment: 64 repetition records changed from `diagnostic` to `formal`, and 14 `mainAgentCorrectedScoringCopy` flags were cleared. This removes the 0.9 status discount from 63 positive repetitions; the remaining changed repetition is zero. Raw scores, recorded time, token usage, reviewer weights and the aggregation formula are unchanged. Of the original 28 configurations, 22 scores rise and six stay unchanged. Their simple mean moves from 65.2345 to 66.4519 points on the 0–100 scale.

This version also adds [DeepSeek V4.1 Flash](https://api-docs.deepseek.com/quick_start/pricing/) (`deepseek-flash`) at `low`, `high`, and `max`. Its weighted scores are 61.5043, 64.0161, and 69.6247. The scoring version is separate from the input's schema version 4 and the price-check date.

## What was measured

ARW is the software project whose development workflow supplied these tasks. A *Reviewer* is an AI agent assigned one review task in that workflow.

| Role | Task | Score share |
| --- | --- | ---: |
| Code Standards | Check code against repository instructions and implementation quality standards. | 20% |
| Code Spec | Check whether changes implement supplied requirements. | 20% |
| Commit Audit | Audit a staged commit candidate and required checks. | 25% |
| Spec Readiness | Check requirements before implementation for completeness and feasibility. | 35% |

The first three roles each use one fixed scenario; Spec Readiness uses two. Each of the 31 model and effort configurations ran all five scenarios in three independent repetitions: 465 scenario runs and 372 role repetitions. The current snapshot has 35 role repetitions marked as diagnostic scores. The same visible fixture material and hidden scoring cases were used across models. The full fixtures, reports, and hidden cases are not included here; the snapshot can reproduce the charts but cannot replay model runs.

Five GPT models ran through isolated Codex Reviewer sessions at `low`, `medium`, `high`, `xhigh`, and `max`. DeepSeek V4.1 Flash ran through its hosted API at `low`, `high`, and `max` with thinking enabled. Bonsai 2 ran locally at `low`, `medium`, and `xhigh` with thinking enabled in a custom read-only Windows worker. Effort labels are requested provider settings, not equal compute budgets. [Prism ML says Bonsai 2 `low` may behave close to `xhigh`](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf), so plotted labels do not prove distinct model behavior. The models also had different execution environments and scheduling.

## Wall-clock collection time

For the **original GPT and Bonsai 2 collection**, the first retained call's start and last retained call's completion give these elapsed windows (Japan time, UTC+09:00). This table and the clean-repeat estimate below cover those original groups; DeepSeek's additional 45 calls are excluded:

| Group | Start | End | Wall-clock span |
| --- | --- | --- | ---: |
| Hosted GPT, 375 calls | 2026-09-24 22:35:09 | 2026-09-26 11:27:22 | 36 h 52 min 13 s |
| Local Bonsai 2, 45 calls | 2026-09-25 09:25:15 | 2026-09-26 16:17:41 | 30 h 52 min 26 s |
| Both groups together | 2026-09-24 22:35:09 | 2026-09-26 16:17:41 | 41 h 42 min 32 s |

The groups overlapped for **26 h 2 min 7 s**. GPT allowed up to three independent calls at once; Bonsai 2 used one local worker, and the two groups could run in parallel. These spans include pauses and recovery between their first and last retained calls. They exclude setup before those calls and scoring, adjudication, or page work after them.

Timing was reconstructed from the 375 final GPT Codex session start/completion timestamps and the Windows worker manifests associated with all 45 final Bonsai 2 calls. The manifests include revisions of the same call; the earliest worker start and latest worker end define the Bonsai 2 window. Those detailed session and manifest logs are private and are not in the published `statistics.json`, which only stores per-scenario durations.

For a **clean repeat**, plan on **about 25 hours** from preparation through one final scoring pass, assuming the fixtures and local runtime are already validated:

| Component | Planning calculation |
| --- | ---: |
| GPT calls, 39 h 22 min 57 s summed across instances, divided by three continuously occupied slots | 13 h 7 min 39 s |
| Bonsai 2 calls, 22 h 6 min 24 s summed across serial instances | 22 h 6 min 24 s |
| Parallel collection phase, limited by Bonsai 2 | about 22 h 6 min |
| Preparation allowance | 30 min |
| One scoring and verification pass | 2 h 15 min |
| **Total idealized schedule** | **about 24 h 51 min** |

The preparation and scoring allowances are planning assumptions. This estimate assumes immediate reuse of each GPT slot and full overlap between GPT and Bonsai 2. It excludes the repairs, reruns, and interruptions that lengthened this study. It is not an observed duration or a guarantee for a future run.

## Bonsai 2 deployment in this study

Bonsai 2 is [Prism ML's ternary version of Qwen3.8-27B](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf). The exact weight file was [Ternary-Bonsai-2-27B-PQ2_0.gguf](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf/blob/main/Ternary-Bonsai-2-27B-PQ2_0.gguf), served on the Windows host with [Prism ML's llama.cpp runtime](https://github.com/PrismML-Eng/Bonsai-demo) and CUDA. This was local inference, not Alibaba Cloud API inference.

| Component | Benchmark configuration |
| --- | --- |
| Host | Intel Core i9-14900K, about 64 GB RAM, NVIDIA RTX 4070 Ti SUPER with 16 GB VRAM |
| Model | `Ternary-Bonsai-2-27B-PQ2_0.gguf` |
| Server | Prism ML llama.cpp `llama-server`, Windows CUDA 12.4; recorded runtime build `prism-b10709-9a9394a` |
| Context and concurrency | 200,000 tokens, one server slot, one worker at a time |
| GPU and cache | `-ngl 99`, K and V cache `q8_0` |
| Batching and CPU | batch 2048, microbatch 256, 16 CPU threads |
| Reuse | 8 context checkpoints, 2 GiB prompt-cache RAM budget |
| Requests | thinking enabled; worker forwarded `low`, `medium`, or `xhigh` |

These settings document the recorded deployment, not a performance guarantee. A separate local 150K-token check recorded about 15.04 GiB whole-GPU peak use under this profile; that check used a different workload, so it is not the Reviewer benchmark's measured VRAM use.

## Files and local build

| Path | Purpose |
| --- | --- |
| `statistics.json` | Independent schema-v4 snapshot of per-scenario runtime observations and per-repetition scores. |
| `pricing.json` | Dated official pricing rules and the reference rates used to reproduce equivalent costs. |
| `build.py` | Computes chart metrics and generates HTML. |
| `charts.html` | Generated local page; excluded from Git. |
| `.env.example` | Template for the maintainer's local, ignored `.env` file. |
| `resources/` | Local CSS, favicon, bundled fonts, and font licenses. |

The checked-in `statistics.json` is an independent snapshot. To refresh it, a maintainer copies `.env.example` to the ignored `.env` file and sets `BENCHMARK_SOURCE_STATISTICS` there to the trusted source file's absolute path. The site build reads only the checked-in snapshot; it does not read `.env` or silently synchronize data from another checkout. To copy and verify a new snapshot from the repository root in Bash:

```bash
. ./.env
: "${BENCHMARK_SOURCE_STATISTICS:?Set BENCHMARK_SOURCE_STATISTICS in .env}"
cp -- "$BENCHMARK_SOURCE_STATISTICS" statistics.json
cmp -- "$BENCHMARK_SOURCE_STATISTICS" statistics.json
```

Build with Python and Plotly 6.9.0 (validated with Python 3.14.4):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install plotly==6.9.0
.venv/bin/python build.py
```

If Python's `venv` module is unavailable, an installed `uv` can create the project environment:

```bash
uv venv --seed --python python3 .venv
.venv/bin/python -m pip install plotly==6.9.0
.venv/bin/python build.py
```

On Windows, use `py -m venv .venv`, `.venv\Scripts\python -m pip install plotly==6.9.0`, and `.venv\Scripts\python build.py`.

`build.py` reads `statistics.json` beside itself and writes `charts.html` beside itself. It also accepts input and output paths: `.venv/bin/python build.py path/to/statistics.json path/to/charts.html`. The output directory must contain the matching `resources/` directory. The generated HTML opens directly in a browser without a web server or network; external source links need a network connection.

The footer's "Updated" date is the page build date, not the model collection or price-check date.

## Score and metric rules

The input is a nonempty array of `schemaVersion: 4` configurations. Each configuration has per-scenario `observations` and four role records with up to three numbered repetitions. `build.py` does not read older schemas or role-level runtime summaries.

Each repetition has a raw score from 0 to 1. A positive repetition marked `diagnostic` or `mainAgentCorrectedScoringCopy: true` is multiplied by 0.9 once, even when both flags are present. A role score averages only positive repetitions. If any repetition is zero, unavailable, or missing, the positive-score average is multiplied by 0.9 once more. Thus there are at most two 0.9 factors. With no positive repetition, the role contributes zero. Missing roles also contribute zero; weights are never redistributed.

```text
Weighted score = 100 × (
    0.20 × Code Standards
  + 0.20 × Code Spec
  + 0.25 × Commit Audit
  + 0.35 × Spec Readiness
)
```

Elapsed time and token usage use only positive-score repetitions. A role's recorded values are averaged over its usable repetitions. For Spec Readiness, only the normal `artifact-promotion` scenario supplies chart runtime metrics; the early-return `runtime-migration` scenario remains part of scoring. Configuration-level time and token values are arithmetic means over roles with available data. Missing time and incomplete three-part token records are excluded separately; zero token counts are valid. Missing role metrics omit only the affected bars and roles from that metric's configuration mean.

The three token parts are uncached input, cached input, and output. Estimated *equivalent API cost* prices each role's average token use at the reference rates in `pricing.json`, then averages available role costs. Prices were checked on **2026-09-29**; the six previously plotted models' reference rates are unchanged after verification.

| Model | Reference profile | Uncached input | Cached input | Output |
| --- | --- | ---: | ---: | ---: |
| gpt-6-astra | Standard, short context | $10 | $1 | $50 |
| gpt-6-sol | Standard, short context | $2 | $0.2 | $10 |
| gpt-5.6-sol | Standard, short context | $4 | $0.4 | $20 |
| gpt-6-luna | Standard, short context | $0.1 | $0.01 | $0.5 |
| gpt-5.6-luna | Standard, short context | $0.2 | $0.02 | $1.2 |
| DeepSeek V4.1 Flash | Peak/off-peak arithmetic mean, 50% each | $0.225 | $0.0045 | $0.9 |
| Bonsai 2 | Beijing, implicit-cache comparison proxy | $0.424 | $0.085 | $1.696 |

All rates are USD per million tokens. [OpenAI](https://developers.openai.com/api/docs/pricing) charges long-context rates for a single request exceeding 272,000 input tokens: input/cache rates double and output rates increase by 50% for the full request. Cache writes cost 1.25 times uncached input. GPT-6 Batch/Flex prices are half Standard; Fast is twice Standard. [GPT-5.6 Sol's current promotion](https://developers.openai.com/api/docs/models/gpt-5.6-sol) is available at least through November 21, 2026; [GPT-5.6 Luna's model page](https://developers.openai.com/api/docs/models/gpt-5.6-luna) supplies its rates.

[DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/) peak input/cached-input/output rates are $0.3/$0.006/$1.2; off-peak rates are half peak. This benchmark uses their arithmetic mean, assuming a 50% share of each. Peak is Monday–Friday 01:00–04:00 and 06:00–10:00 UTC, excluding Chinese public holidays; all other times are off-peak. [Qwen Beijing](https://www.alibabacloud.com/help/en/model-studio/qwen3-8-27b) explicit cache creation/read rates are $0.53/$0.042; this benchmark uses implicit caching. `pricing.json` also records the long-context rates, DeepSeek peak/off-peak rates and Qwen Singapore rates.

The snapshot contains per-review token totals rather than per-request context lengths, cache-write counts or billing timestamps. Those totals cannot identify long-context requests or a peak/off-peak mix, so the charts use the stated reference profiles. The estimate is not a bill and excludes cache writes, tools, regional processing premiums, local hardware and electricity. **Bonsai 2 incurred no corresponding cloud API charge.** Update `pricing.json` and its check date before regenerating charts after a price change.

Scatter plots compare equivalent cost with score, time with score, and time with equivalent cost. Each optional Pareto front uses only the visible configurations with complete values on that plot. Cost axes can use linear or logarithmic scales. Token detail is a stacked bar of the three token parts.

## Publishing

Cloudflare Pages is connected to this GitHub repository and builds the `master` branch with Python 3.12 and Plotly 6.9.0. Its build output directory is `_site`. These commands create the published subpath from the checked-in snapshot:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install plotly==6.9.0
mkdir -p _site/reviewer-model-benchmark/resources
cp -R resources/. _site/reviewer-model-benchmark/resources/
.venv/bin/python build.py statistics.json _site/reviewer-model-benchmark/index.html
```

The page's asset links are relative to that `index.html`. The local `charts.html` stays out of Git. Custom domain settings are managed outside this repository. Font source and license details are in [resources/fonts/README.md](resources/fonts/README.md).
