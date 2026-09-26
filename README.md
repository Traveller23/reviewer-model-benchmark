# Reviewer Model Benchmark

**English** · [简体中文](README.zh-CN.md)

[Open the published benchmark page](https://traveller23.github.io/reviewer-model-benchmark/)

This repository builds a static benchmark page from `statistics.json`. It compares five hosted GPT models and one locally served Bonsai 2 model on four AI review roles at different reasoning effort settings. The page has five bar charts, three scatter plots, and optional Pareto fronts. The results describe this specific workload, not a general model ranking or authorization for production review.

## What was measured

ARW is the software project whose development workflow supplied these tasks. A *Reviewer* is an AI agent assigned one review task in that workflow.

| Role | Task | Score share |
| --- | --- | ---: |
| Code Standards | Check code against repository instructions and implementation quality standards. | 20% |
| Code Spec | Check whether changes implement supplied requirements. | 20% |
| Commit Audit | Audit a staged commit candidate and required checks. | 25% |
| Spec Readiness | Check requirements before implementation for completeness and feasibility. | 35% |

The first three roles each use one fixed scenario; Spec Readiness uses two. Each of the 28 model and effort configurations ran all five scenarios in three independent repetitions: 420 scenario runs and 336 role repetitions. The current snapshot has 99 role repetitions marked as diagnostic scores. The same visible fixture material and hidden scoring cases were used across models. The full fixtures, reports, and hidden cases are not included here; the snapshot can reproduce the charts but cannot replay model runs.

Five GPT models ran through isolated Codex Reviewer sessions at `low`, `medium`, `high`, `xhigh`, and `max`. Bonsai 2 ran locally at `low`, `medium`, and `xhigh` with thinking enabled in a custom read-only Windows worker. Effort labels are requested provider settings, not equal compute budgets. [Prism ML says Bonsai 2 `low` may behave close to `xhigh`](https://huggingface.co/prism-ml/Ternary-Bonsai-2-27B-gguf), so plotted labels do not prove distinct model behavior. GPT and Bonsai 2 also had different execution environments and scheduling.

## Wall-clock collection time

For the **formal model collection**, the first retained call's start and last retained call's completion give these elapsed windows (Japan time, UTC+09:00):

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
| `build.py` | Computes chart metrics and generates HTML. |
| `charts.html` | Generated local page; excluded from Git because GitHub Pages rebuilds it. |
| `.env.example` | Template for the maintainer's local, ignored `.env` file. |
| `resources/` | Local CSS, favicon, bundled fonts, and font licenses. |
| `.github/workflows/pages.yml` | Builds and publishes `index.html` to GitHub Pages. |

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

The three token parts are uncached input, cached input, and output. Estimated *equivalent API cost* prices each role's average token use at the static per-million-token rates in `build.py`, then averages available role costs. GPT uses published OpenAI Standard short-context rates. Local Bonsai 2 uses the Alibaba Cloud Beijing `qwen3.8-27b` rate as a comparison proxy. **Bonsai 2 incurred no such API charge.** The estimate is not a bill and excludes local hardware, electricity, cache writes, long-context, and tool charges. Prices were checked on 2026-09-25; refresh them before current cost decisions.

Scatter plots compare equivalent cost with score, time with score, and time with equivalent cost. Each optional Pareto front uses only the visible configurations with complete values on that plot. Cost axes can use linear or logarithmic scales. Token detail is a stacked bar of the three token parts.

## Publishing

The Pages workflow builds fresh HTML from the checked-in snapshot, places it at `index.html`, and publishes it with `resources/`, `statistics.json`, and `build.py`. The project site works at a repository subpath because its asset links are relative. Set the repository's Pages source to **GitHub Actions**; GitHub Free requires the repository to be public. The workflow does not configure a custom domain. Font source and license details are in [resources/fonts/README.md](resources/fonts/README.md).
