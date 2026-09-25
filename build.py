"""Build the offline Reviewer Model Benchmark page from local statistics.json."""

import argparse
import colorsys
import json
import math
from collections import defaultdict
from datetime import date
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio


REVIEWERS = (
    ("code-standards-reviewer", "Code Standards", 0.20),
    ("code-spec-reviewer", "Code Spec", 0.20),
    ("commit-audit-reviewer", "Commit Audit", 0.25),
    ("spec-readiness-reviewer", "Spec Readiness", 0.35),
)
EFFORTS = {"low": 0, "medium": 1, "high": 2, "xhigh": 3, "max": 4}
MODEL_ORDER = (
    "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
    "gpt-5.6-sol", "gpt-5.6-luna", "Ternary-Bonsai-2-27B-PQ2_0.gguf",
)
MODEL_COLORS = ("#4c78b8", "#198f76", "#b47627", "#8659b9", "#bb5272", "#2f8fa9")
ROLE_COLORS = ("#6388b7", "#5f9e98", "#b3935e", "#9b7fb5")
CHART_TEXT = "#5c5e5c"
CHART_PLOT = "#f8f5ef"
CHART_GRID = "#eae3d9"
CHART_FONT = "Source Sans 3, Source Han Sans, sans-serif"
CHART_DATA_FONT = "Source Sans 3, Source Han Sans, sans-serif"
PARETO_COLOR = "#e6aa00"
BAR_EFFORT_ORDER = tuple(sorted(EFFORTS, key=EFFORTS.get, reverse=True))
# Official Standard short-context API rates in USD per million tokens, checked 2026-09-25.
PRICES = {
    "gpt-6-astra": (10.0, 1.0, 50.0),
    "gpt-6-sol": (2.0, 0.2, 10.0),
    "gpt-6-luna": (0.1, 0.01, 0.5),
    "gpt-5.6-sol": (4.0, 0.4, 20.0),
    "gpt-5.6-luna": (0.2, 0.02, 1.2),
    "Ternary-Bonsai-2-27B-PQ2_0.gguf": (0.424, 0.085, 1.696),
}
MODEL_PALETTE = dict(zip(MODEL_ORDER, MODEL_COLORS))
LEGEND_GAP = "\u00a0" * 10

BRAND_ICON_PATHS = '''
<path fill-rule="nonzero" d="M0 53v1813.33h1386.67v-320H1280v213.34H106.667V159.667H1280V373h106.67V53z"/>
<path d="M260 420h620v72H260z M260 610h500v72H260z M260 800h430v72H260z M260 990h360v72H260z"/>
<path fill-rule="evenodd" d="M1226.67 1439.67c113.33 0 217.48-39.28 299.6-104.96l302.37 302.65c20.82 20.84 54.59 20.85 75.42.04 20.84-20.82 20.86-54.59.04-75.43l-302.41-302.68c65.7-82.12 104.98-186.29 104.98-299.623 0-265.097-214.91-480-480-480-265.1 0-480.003 214.903-480.003 480 0 265.093 214.903 480.003 480.003 480.003Zm0-106.67c206.18 0 373.33-167.15 373.33-373.333 0-206.187-167.15-373.334-373.33-373.334-206.19 0-373.337 167.147-373.337 373.334 0 206.183 167.147 373.333 373.337 373.333Z"/>
'''
FAVICON_COLOR = "#805e38"

ICON_SHAPES = {
    "standards": '<path d="m8 5-6 7 6 7m8-14 6 7-6 7M14 2 10 22" stroke-width="2.5"/>',
    "spec": '<path d="M5 2h10l4 4v16H5Z" fill="currentColor" stroke="none"/><path d="M15 2v5h4M8 12h8m-8 4h8m-8 4h5" stroke="#fffefa" stroke-width="1.7"/>',
    "audit": '<path d="M12 2 21 5v6c0 5.2-3.5 8.6-9 11-5.5-2.4-9-5.8-9-11V5Z" fill="currentColor" stroke="none"/><path d="M5 6.2 12 3.8V12H5V6.2Zm7 5.8h7.7c-.5 3.6-3.1 6.4-7.7 8.6V12Z" fill="#fffefa" stroke="none"/><path d="M12 3v17M4 12h16" stroke-width="1"/>',
    "readiness": '<path d="M3 4h3v3H3Zm6 .3h12v2.4H9ZM3 10.5h3v3H3Zm6 .3h12v2.4H9ZM3 17h3v3H3Zm6 .3h12v2.4H9Z" fill="currentColor" stroke="none"/>',
    "external": '<path d="M5 19 19 5M9 5h10v10"/>',
}

SUMMARY_ICON_SHAPES = {
    "models": ("0 0 48 48", '''
<path d="M44,33H36a2,2,0,0,0-2,2v2c-4.7-.4-7.9-3.5-7.9-7.9v-9A13,13,0,0,0,14,7.1V5a2,2,0,0,0-2-2H4A2,2,0,0,0,2,5v8a2,2,0,0,0,2,2h8a2,2,0,0,0,2-2V11.1a9,9,0,0,1,8.1,9v9c0,6.6,5,11.4,11.9,11.9v2a2,2,0,0,0,2,2h8a2,2,0,0,0,2-2V35A2,2,0,0,0,44,33ZM10,11H6V7h4ZM42,41H38V37h4Z"/>
<path d="M44,3H36a2,2,0,0,0-2,2V7a14,14,0,0,0-7.2,2.9,12,12,0,0,1,2.1,3.4A9.1,9.1,0,0,1,34,11.1V13a2,2,0,0,0,2,2h8a2,2,0,0,0,2-2V5A2,2,0,0,0,44,3Zm-2,8H38V7h4Z"/>
<path d="M19.1,34.6A8.6,8.6,0,0,1,14,36.9V35a2,2,0,0,0-2-2H4a2,2,0,0,0-2,2v8a2,2,0,0,0,2,2h8a2,2,0,0,0,2-2V41a13.4,13.4,0,0,0,7.3-3.1A14.6,14.6,0,0,1,19.1,34.6ZM10,41H6V37h4Z"/>
'''),
    "configurations": ("0 0 32 32", '''
<path d="M24,19.171c-1.165,0.412 -2,1.524 -2,2.829c-0,1.305 0.835,2.417 2,2.829l-0,2.171c0,0.552 0.448,1 1,1c0.552,-0 1,-0.448 1,-1l-0,-2.171c1.165,-0.412 2,-1.524 2,-2.829c-0,-1.305 -0.835,-2.417 -2,-2.829l-0,-14.183c0,-0.552 -0.448,-1 -1,-1c-0.552,-0 -1,0.448 -1,1l-0,14.183Zm1,1.829c0.552,0 1,0.448 1,1c-0,0.552 -0.448,1 -1,1c-0.552,0 -1,-0.448 -1,-1c-0,-0.552 0.448,-1 1,-1Z"/>
<path d="M15.006,7.159c-1.164,0.412 -2,1.523 -2,2.829c0,1.305 0.836,2.417 2,2.829l0,14.183c0,0.552 0.448,1 1,1c0.552,0 1,-0.448 1,-1l0,-14.183c1.165,-0.412 2,-1.524 2,-2.829c0,-1.306 -0.835,-2.417 -2,-2.829l0,-2.171c0,-0.552 -0.448,-1 -1,-1c-0.552,-0 -1,0.448 -1,1l0,2.171Zm1,3.829c-0.552,-0 -1,-0.448 -1,-1c0,-0.552 0.448,-1 1,-1c0.552,-0 1,0.448 1,1c0,0.552 -0.448,1 -1,1Z"/>
<path d="M6,19.176c-1.157,0.416 -1.986,1.524 -1.986,2.824c-0,1.3 0.829,2.408 1.986,2.824l0,2.176c-0,0.552 0.448,1 1,1c0.552,0 1,-0.448 1,-1l0,-2.166c1.172,-0.408 2.014,-1.524 2.014,-2.834c-0,-1.31 -0.842,-2.426 -2.014,-2.834l0,-14.178c-0,-0.552 -0.448,-1 -1,-1c-0.552,-0 -1,0.448 -1,1l0,14.188Zm1.014,3.824c-0.552,0 -1,-0.448 -1,-1c-0,-0.552 0.448,-1 1,-1c0.552,0 1,0.448 1,1c-0,0.552 -0.448,1 -1,1Z"/>
'''),
    "benchmark": ("0 0 1920 1920", '''
<path d="M833.935 1063.327c28.913 170.315 64.038 348.198 83.464 384.79 27.557 51.84 92.047 71.944 144 44.387 51.84-27.558 71.717-92.273 44.16-144.113-19.426-36.593-146.937-165.46-271.624-285.064Zm-43.821-196.405c61.553 56.923 370.899 344.81 415.285 428.612 56.696 106.842 15.811 239.887-91.144 296.697-32.64 17.28-67.765 25.411-102.325 25.411-78.72 0-154.955-42.353-194.371-116.555-44.386-83.802-109.102-501.346-121.638-584.245-3.501-23.717 8.245-47.21 29.365-58.277 21.346-11.294 47.096-8.02 64.828 8.357ZM960.045 281.99c529.355 0 960 430.757 960 960 0 77.139-8.922 153.148-26.654 225.882l-10.39 43.144h-524.386v-112.942h434.258c9.487-50.71 14.231-103.115 14.231-156.084 0-467.125-380.047-847.06-847.059-847.06-467.125 0-847.059 379.935-847.059 847.06 0 52.97 4.744 105.374 14.118 156.084h487.454v112.942H36.977l-10.39-43.144C8.966 1395.137.044 1319.128.044 1241.99c0-529.243 430.645-960 960-960Zm542.547 390.686 79.85 79.85-112.716 112.715-79.85-79.85 112.716-112.715Zm-1085.184 0L530.123 785.39l-79.85 79.85L337.56 752.524l79.849-79.85Zm599.063-201.363v159.473H903.529V471.312h112.942Z" fill-rule="evenodd"/>
'''),
}


def icon(name, class_name=""):
    css = f" icon-{class_name}" if class_name else ""
    if name == "brand":
        return (f'<svg class="icon{css}" viewBox="0 0 1920 1920" '
                f'fill="currentColor" aria-hidden="true">{BRAND_ICON_PATHS}</svg>')
    if name in SUMMARY_ICON_SHAPES:
        view_box, paths = SUMMARY_ICON_SHAPES[name]
        return (f'<svg class="icon{css}" viewBox="{view_box}" fill="currentColor" '
                f'aria-hidden="true">{paths}</svg>')
    return (f'<svg class="icon{css}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{ICON_SHAPES[name]}</svg>')


def favicon_svg():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1920" '
            f'fill="{FAVICON_COLOR}">{BRAND_ICON_PATHS}</svg>')


def model_label(model):
    return model.replace("Ternary-Bonsai-2-27B-PQ2_0.gguf", "Bonsai 2")


def label(item):
    config = item["configuration"]
    return f"{model_label(config['model'])} / {config['reasoningEffort']}"


def finite_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def adjusted_reviewer_score(role):
    repetitions = role.get("repetitions")
    if not isinstance(repetitions, list) or len(repetitions) != 3:
        return None
    seen = set()
    total = 0.0
    diagnostic_count = 0
    for repetition in repetitions:
        number = repetition.get("repetition")
        source = repetition.get("scoreSource")
        value = repetition.get("score")
        if number not in (1, 2, 3) or number in seen:
            raise ValueError("Reviewer repetitions must have the distinct numbers 1, 2 and 3.")
        if source not in ("formal", "diagnostic", "unavailable"):
            raise ValueError(f"Unknown repetition score source: {source}")
        if value is not None:
            if not finite_number(value) or not 0 <= value <= 1 or source == "unavailable":
                raise ValueError(f"Invalid repetition score: {value}")
            total += value * (0.9 if source == "diagnostic" else 1.0)
            diagnostic_count += source == "diagnostic"
        seen.add(number)
    return total / 3, diagnostic_count


def extract(items):
    grouped = []
    complete = []
    seen = set()
    for item in items:
        config = item["configuration"]
        model = config["model"]
        effort = config["reasoningEffort"]
        if model not in PRICES or effort not in EFFORTS:
            raise ValueError(f"Unknown model or reasoning effort: {model} / {effort}")
        if (model, effort) in seen:
            raise ValueError(f"Duplicate configuration: {model} / {effort}")
        seen.add((model, effort))
        title = label(item)
        roles = {}
        for role in item.get("roles", []):
            reviewer_id = role["reviewerId"]
            if reviewer_id in roles:
                raise ValueError(f"Duplicate reviewer: {title} / {reviewer_id}")
            result = adjusted_reviewer_score(role)
            if result is not None:
                roles[reviewer_id] = {"raw": role, "score": result[0],
                                      "diagnosticCount": result[1]}
        if roles:
            grouped.append({"model": model, "effort": effort, "label": title, "roles": roles})
        if not all(key in roles for key, _, _ in REVIEWERS):
            continue
        score = sum(roles[key]["score"] * weight for key, _, weight in REVIEWERS)
        durations = [roles[key]["raw"].get("durationMs") for key, _, _ in REVIEWERS]
        duration = (sum(durations) / 3 / 60_000
                    if all(finite_number(value) and value >= 0 for value in durations) else None)
        token_totals = [roles[key]["raw"].get("tokenUsage") for key, _, _ in REVIEWERS]
        has_tokens = all(isinstance(usage, dict) and all(
            finite_number(usage.get(token)) and usage[token] >= 0
            for token in ("input", "cachedInput", "output")) for usage in token_totals)
        cost = None
        if has_tokens:
            totals = [sum(usage[token] for usage in token_totals) / 3
                      for token in ("input", "cachedInput", "output")]
            cost = sum(count * rate for count, rate in zip(totals, PRICES[model])) / 1_000_000
        complete.append({"model": model, "effort": effort, "label": title,
                         "score": 100 * score, "minutes": duration, "cost": cost,
                         "diagnosticCount": sum(roles[key]["diagnosticCount"]
                                                for key, _, _ in REVIEWERS)})
    return grouped, complete


METRICS = {
    "score": ("Score", True, ".1f"),
    "minutes": ("Execution time (min)", False, ".1f"),
    "cost": ("Equivalent API cost (USD)", False, ".4f"),
}
METRIC_LABELS_ZH = {"score": "分数", "minutes": "耗时 (min)", "cost": "等效费用 (USD)"}


def short_value(record, key):
    if key == "cost":
        return f"${record[key]:.2f}"
    if key == "minutes":
        return f"{record[key]:.1f} min"
    return f"{record[key]:.1f}"


def hover_summary(record, xkey, ykey):
    return (f"{record['label']}\n{short_value(record, xkey)} · "
            f"{short_value(record, ykey)}")


def rgba(color, alpha):
    red, green, blue = (int(color[offset:offset + 2], 16) for offset in (1, 3, 5))
    return f"rgba({red},{green},{blue},{alpha})"


def effort_bar_color(model, effort):
    base = MODEL_PALETTE[model]
    rgb = [int(base[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    hue, _, _ = colorsys.rgb_to_hls(*rgb)
    strength = EFFORTS[effort]
    lightness = 0.30 + strength * 0.11
    saturation = 0.24 + strength * 0.075
    channels = colorsys.hls_to_rgb(hue, lightness, saturation)
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in channels)


def pareto(points, xkey, ykey):
    maximize_x = METRICS[xkey][1]
    maximize_y = METRICS[ykey][1]
    result = []
    for point in points:
        x, y = point[xkey], point[ykey]
        if any((other is not point and
                (other[xkey] >= x if maximize_x else other[xkey] <= x) and
                (other[ykey] >= y if maximize_y else other[ykey] <= y) and
                (other[xkey] != x or other[ykey] != y)) for other in points):
            continue
        result.append(point)
    return sorted(result, key=lambda point: point[xkey])


def chart(complete, xkey, ykey, chart_id):
    usable = [record for record in complete if record[xkey] is not None and record[ykey] is not None]
    front = pareto(usable, xkey, ykey)
    figure = go.Figure()
    available_models = {record["model"] for record in usable}
    models = [model for model in MODEL_ORDER if model in available_models]
    for index, model in enumerate(models):
        records = sorted((record for record in usable if record["model"] == model),
                         key=lambda record: EFFORTS.get(record["effort"], 99))
        figure.add_trace(go.Scatter(x=[r[xkey] for r in records], y=[r[ykey] for r in records],
                                    mode="lines+markers", showlegend=False, legendgroup=f"model-{index}",
                                    customdata=[hover_summary(r, xkey, ykey) for r in records],
                                    hoverinfo="none",
                                    line={"color": rgba(MODEL_PALETTE[model], 0.55), "width": 3},
                                    marker={"size": 11, "symbol": "circle",
                                            "color": MODEL_PALETTE[model],
                                            "line": {"color": "#fff", "width": 1.5}}))
    # Static legend traces keep their symbols unchanged when real traces are dimmed or outlined.
    for index, model in enumerate(models):
        color = MODEL_PALETTE[model]
        figure.add_trace(go.Scatter(x=[None], y=[None], mode="lines+markers",
                                    name=model_label(model) + LEGEND_GAP,
                                    showlegend=True, legendgroup=f"model-{index}", legendrank=index + 1,
                                    hoverinfo="skip", line={"color": rgba(color, 0.55), "width": 3},
                                    marker={"size": 11, "symbol": "circle", "color": color,
                                            "line": {"color": "#fff", "width": 1.5}}))
    front_x = [r[xkey] for r in front]
    front_y = [r[ykey] for r in front]
    figure.add_trace(go.Scatter(x=front_x, y=front_y, name="Pareto Front" + LEGEND_GAP, mode="lines",
                                visible="legendonly", hoverinfo="skip", legendrank=0,
                                line={"color": PARETO_COLOR, "width": 4}))
    figure.add_trace(go.Scatter(x=front_x, y=front_y, mode="markers", showlegend=False,
                                visible="legendonly", hoverinfo="skip",
                                marker={"size": 11, "color": "rgba(0,0,0,0)",
                                        "line": {"color": PARETO_COLOR, "width": 2.5}}))
    figure.update_layout(template="plotly_white", height=600, margin={"l": 75, "r": 32, "t": 60, "b": 70},
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=CHART_PLOT,
                         font={"color": CHART_TEXT, "family": CHART_FONT},
                         legend={"orientation": "h", "y": 1.02, "yanchor": "bottom", "x": 0,
                                 "font": {"size": 11}, "groupclick": "togglegroup"},
                         xaxis_title=METRICS[xkey][0], yaxis_title=METRICS[ykey][0],
                         hovermode="closest", dragmode="pan")
    for axis in (figure.update_xaxes, figure.update_yaxes):
        axis(gridcolor=CHART_GRID, zerolinecolor="#c7bbaa",
             tickfont={"family": CHART_DATA_FONT, "size": 11})
    for key, axis in ((xkey, figure.update_xaxes), (ykey, figure.update_yaxes)):
        if key == "cost":
            axis(tickprefix="$", showtickprefix="all", tickformat=".2f")
        elif key == "minutes":
            axis(ticksuffix=" min", showticksuffix="all", tickformat=".0f")
    # Plotly draws later traces on top. Keep the Pareto line after model traces.
    # Recompute the visible 2D frontier whenever a model is hidden or restored in the legend.
    script = """
    const gd = document.getElementById('{plot_id}');
    const frame = document.getElementById('benchmark-frame-CHART_ID');
    const tip = document.getElementById('benchmark-tooltip-CHART_ID');
    const modelCount = MODEL_COUNT;
    const frontIndex = modelCount * 2;
    const frontPointsIndex = frontIndex + 1;
    const maximizeX = MAX_X, maximizeY = MAX_Y;
    const modelNames = MODEL_NAMES;
    let hoveredModel = -1;
    let updating = false;
    const focusStyle = document.createElement('style');
    focusStyle.textContent = Array.from({length:modelCount}, (_, index) => {
      const selector = '#' + gd.id + ' .scatterlayer .trace' + gd._fullData[index].uid;
      return `${selector} .js-line {stroke-opacity:var(--model-${index}-line-opacity,.55)!important;stroke-width:var(--model-${index}-line-width,3px)!important}`
        + `${selector} .point {opacity:var(--model-${index}-point-opacity,1)!important}`;
    }).join(' ');
    document.head.appendChild(focusStyle);
    const legendModel = target => {
      const group = target?.closest?.('.legend .traces');
      if (!group || !gd.contains(group)) return -1;
      return modelNames.indexOf(group.querySelector('.legendtext')?.textContent?.trim());
    };
    const applyLegendFocus = () => {
      const focused = hoveredModel >= 0 && gd.data[hoveredModel].visible !== false
        && gd.data[hoveredModel].visible !== 'legendonly' ? hoveredModel : -1;
      for (let index = 0; index < modelCount; index++) {
        gd.style.setProperty(`--model-${index}-line-opacity`,
          String(focused < 0 ? .55 : index === focused ? .8 : .25));
        gd.style.setProperty(`--model-${index}-line-width`, focused === index ? '3.4px' : '3px');
        gd.style.setProperty(`--model-${index}-point-opacity`,
          String(focused < 0 || index === focused ? 1 : .42));
      }
    };
    gd.addEventListener('mouseover', event => {
      const index = legendModel(event.target);
      if (index >= 0 && index !== hoveredModel) {
        hoveredModel = index;
        applyLegendFocus();
      }
    });
    gd.addEventListener('mouseout', event => {
      const from = legendModel(event.target), to = legendModel(event.relatedTarget);
      if (from >= 0 && from !== to && from === hoveredModel) {
        hoveredModel = to;
        applyLegendFocus();
      }
    });
    gd.on('plotly_hover', event => {
      const {points} = event;
      const point = points.find(p => p.curveNumber < modelCount);
      if (!point) return;
      tip.textContent = point.data.customdata[point.pointNumber];
      tip.hidden = false;
      const frameBox = frame.getBoundingClientRect(), graphBox = gd.getBoundingClientRect();
      const px = Number.isFinite(point.xPixel) ? point.xPixel : event.xPixel;
      const py = Number.isFinite(point.yPixel) ? point.yPixel : event.yPixel;
      const x = graphBox.left - frameBox.left + px;
      const y = graphBox.top - frameBox.top + py - 9;
      tip.style.left = Math.max(tip.offsetWidth / 2 + 6,
        Math.min(frame.clientWidth - tip.offsetWidth / 2 - 6, x)) + 'px';
      tip.style.top = Math.max(tip.offsetHeight + 6, y) + 'px';
    });
    gd.on('plotly_unhover', () => { tip.hidden = true; });
    gd.on('plotly_relayout', () => { tip.hidden = true; });
    gd.on('plotly_restyle', function([changes, indices]) {
      if (updating || !indices.some(i => i <= frontIndex)) return;
      const shown = gd.data[frontIndex].visible !== false && gd.data[frontIndex].visible !== 'legendonly';
      const modelTraces = gd.data.slice(0, modelCount);
      const pts = modelTraces.filter(t => t.visible !== false && t.visible !== 'legendonly')
        .flatMap(t => t.x.map((x, i) => [x, t.y[i]]));
      const front = pts.filter(([x,y]) => !pts.some(([a,b]) =>
        (maximizeX ? a >= x : a <= x) && (maximizeY ? b >= y : b <= y) && (a !== x || b !== y)))
        .sort((a,b) => a[0]-b[0]);
      updating = true;
      const frontX = front.map(p => p[0]), frontY = front.map(p => p[1]);
      Plotly.restyle(gd, {x:[frontX,frontX], y:[frontY,frontY],
                        visible:[shown ? true : 'legendonly', shown ? true : 'legendonly']},
                    [frontIndex,frontPointsIndex])
        .finally(() => { updating = false; applyLegendFocus(); });
    });
    applyLegendFocus();
    """.replace("MAX_X", str(METRICS[xkey][1]).lower()).replace("MAX_Y", str(METRICS[ykey][1]).lower())
    script = script.replace("MODEL_COUNT", str(len(models))).replace("CHART_ID", str(chart_id))
    script = script.replace("MODEL_NAMES", json.dumps([model_label(model) for model in models]))
    return pio.to_html(figure, full_html=False, include_plotlyjs=False,
                       post_script=script, div_id=f"benchmark-scatter-{chart_id}",
                       config={"responsive": True, "displaylogo": False, "scrollZoom": True})


def bar_tooltip_script(chart_id, details_en, details_zh):
    script = """
    const gd = document.getElementById('{plot_id}');
    const tip = document.getElementById('benchmark-bar-tooltip-CHART_ID');
    document.body.appendChild(tip);
    const viewport = gd.closest('.bar-viewport');
    const keepModebarVisible = () => {
      const modebar = gd.querySelector('.modebar-container');
      if (!modebar) return;
      const overflow = Math.max(0, gd.clientWidth - viewport.clientWidth);
      modebar.style.width = Math.min(gd.clientWidth, viewport.clientWidth) + 'px';
      modebar.style.right = Math.max(0, overflow - viewport.scrollLeft) + 'px';
    };
    viewport.addEventListener('scroll', keepModebarVisible, {passive:true});
    window.addEventListener('resize', keepModebarVisible);
    new ResizeObserver(keepModebarVisible).observe(viewport);
    gd.on('plotly_afterplot', () => requestAnimationFrame(keepModebarVisible));
    keepModebarVisible();
    const detailsByLanguage = {en: DETAILS_EN, zh: DETAILS_ZH};
    let lastMouse = null;
    const add = (parent, tag, className, content) => {
      const element = document.createElement(tag);
      element.className = className;
      element.textContent = content;
      parent.appendChild(element);
      return element;
    };
    const place = event => {
      let left = event.clientX + 15, top = event.clientY + 15;
      if (left + tip.offsetWidth + 8 > window.innerWidth) left = event.clientX - tip.offsetWidth - 15;
      if (top + tip.offsetHeight + 8 > window.innerHeight) top = event.clientY - tip.offsetHeight - 15;
      tip.style.left = Math.max(8, left) + 'px';
      tip.style.top = Math.max(8, top) + 'px';
    };
    gd.addEventListener('mousemove', event => {
      lastMouse = event;
      if (!tip.hidden) place(event);
    });
    gd.on('plotly_hover', event => {
      const detail = detailsByLanguage[window.chartLanguage || 'en'][event.points[0]?.x];
      if (!detail) return;
      tip.replaceChildren();
      add(tip, 'strong', 'bar-tip-title', detail.label);
      add(tip, 'div', 'bar-tip-meta', detail.meta);
      for (const row of detail.rows) {
        const line = add(tip, 'div', 'bar-tip-row', '');
        const dot = add(line, 'span', 'bar-tip-dot', '');
        dot.style.backgroundColor = row.color;
        add(line, 'span', 'bar-tip-name', row.name);
        add(line, 'strong', 'bar-tip-value', row.value.toFixed(row.digits));
      }
      tip.hidden = false;
      if (lastMouse) place(lastMouse);
    });
    gd.on('plotly_unhover', () => { tip.hidden = true; });
    gd.addEventListener('mouseleave', () => { tip.hidden = true; });
    """
    return (script.replace("CHART_ID", chart_id)
            .replace("DETAILS_EN", json.dumps(details_en, ensure_ascii=False))
            .replace("DETAILS_ZH", json.dumps(details_zh, ensure_ascii=False)))


def bars(grouped, complete):
    model_rank = {model: index for index, model in enumerate(MODEL_ORDER)}
    grouped = sorted(grouped, key=lambda record: (model_rank[record["model"]],
                                                   -EFFORTS[record["effort"]]))
    complete = sorted(complete, key=lambda record: (model_rank[record["model"]],
                                                     -EFFORTS[record["effort"]]))
    xlabels = [record["label"] for record in grouped]
    ticktext = [title.replace(" / ", "<br>") for title in xlabels]
    colored_ticktext = [f'<span style="color:{MODEL_PALETTE[record["model"]]}">'
                        f'{ticktext[index]}</span>' for index, record in enumerate(grouped)]
    weighted = {record["label"]: record["score"] for record in complete}
    role_details = {language: {} for language in ("en", "zh")}
    for record in grouped:
        title, roles = record["label"], record["roles"]
        for language in ("en", "zh"):
            score_label = (f"{weighted[title]:.1f} · weighted score" if language == "en"
                           else f"{weighted[title]:.1f} · 综合分数") if title in weighted else (
                               "Weighted score unavailable" if language == "en" else "综合分数暂不可用")
            reviewer_label = "reviewers" if language == "en" else "位 Reviewer"
            role_details[language][title] = {
                "label": title,
                "meta": f"{score_label} · {len(roles)}/4 {reviewer_label}",
                "rows": [{"name": name, "color": ROLE_COLORS[index],
                          "value": 100 * roles[key]["score"], "digits": 1}
                         for index, (key, name, _) in enumerate(REVIEWERS) if key in roles],
            }
    multi = go.Figure()
    for index, (key, name, _) in enumerate(REVIEWERS):
        values = [100 * record["roles"][key]["score"] if key in record["roles"] else None
                  for record in grouped]
        legend_name = name + LEGEND_GAP
        multi.add_trace(go.Bar(x=xlabels, y=values, name=legend_name, marker_color=ROLE_COLORS[index],
                               text=[f"{value:.0f}" if value is not None else "" for value in values],
                               textposition="outside", textangle=0, cliponaxis=False,
                               textfont={"color": CHART_TEXT, "family": CHART_DATA_FONT,
                                         "size": 10}, hoverinfo="none"))
    # Each category gets about one two-line label's width. Bars occupy most of
    # that slot, leaving only a small separation between adjacent categories.
    chart_width = max(1200, len(xlabels) * 84)
    multi.update_layout(barmode="group", bargap=0.18, bargroupgap=0.10,
                        template="plotly_white", height=580, width=chart_width,
                        margin={"l": 65, "r": 25, "t": 95, "b": 90},
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=CHART_PLOT,
                        font={"color": CHART_TEXT, "family": CHART_FONT},
                        legend={"orientation": "h", "y": 1.02, "yanchor": "bottom"},
                        yaxis_title="Score", yaxis_range=[0, 108], dragmode="pan")
    multi.update_xaxes(categoryorder="array", categoryarray=xlabels,
                       tickmode="array", tickvals=xlabels, ticktext=colored_ticktext,
                       tickangle=0, tickfont={"size": 11})
    multi.update_yaxes(gridcolor=CHART_GRID, zerolinecolor="#c7bbaa",
                       tickfont={"family": CHART_DATA_FONT, "size": 11})
    scores_by_config = {(record["model"], record["effort"]): record["score"] for record in complete}
    active_models = [model for model in MODEL_ORDER
                     if any(record["model"] == model for record in complete)]
    model_labels = [model_label(model) for model in active_models]
    colored_model_labels = [f'<span style="color:{MODEL_PALETTE[model]}">{model_label(model)}</span>'
                            for model in active_models]
    model_positions = list(range(len(active_models)))
    effort_details = {language: {} for language in ("en", "zh")}
    for model_index, (model, title) in enumerate(zip(active_models, model_labels)):
        rows = [{"name": effort, "color": effort_bar_color(model, effort),
                 "value": scores_by_config[(model, effort)], "digits": 1}
                for effort in BAR_EFFORT_ORDER if (model, effort) in scores_by_config]
        for language in ("en", "zh"):
            meta = (f"Weighted score · {len(rows)} effort levels" if language == "en"
                    else f"综合分数 · {len(rows)} 档推理强度")
            effort_details[language][model_index] = {"label": title, "meta": meta, "rows": rows}
    effort_chart = go.Figure()
    bar_width, bar_gap = 0.16, 0.01
    for effort in BAR_EFFORT_ORDER:
        positions, values, offsets, colors = [], [], [], []
        for model_index, model in enumerate(active_models):
            if (model, effort) not in scores_by_config:
                continue
            available = [name for name in BAR_EFFORT_ORDER if (model, name) in scores_by_config]
            group_width = len(available) * bar_width + (len(available) - 1) * bar_gap
            positions.append(model_index)
            values.append(scores_by_config[(model, effort)])
            offsets.append(-group_width / 2 + available.index(effort) * (bar_width + bar_gap))
            colors.append(effort_bar_color(model, effort))
        effort_chart.add_trace(go.Bar(x=positions, y=values, name=effort, showlegend=False,
                                      offset=offsets,
                                      width=bar_width,
                                      marker_color=colors,
                                      text=[f"{value:.1f}" for value in values],
                                      textposition="outside", textangle=0, cliponaxis=False,
                                      textfont={"color": CHART_TEXT, "family": CHART_DATA_FONT,
                                                "size": 10}, hoverinfo="none"))
    effort_chart.update_layout(barmode="overlay", showlegend=False,
                               template="plotly_white", height=520, autosize=True,
                               margin={"l": 65, "r": 25, "t": 36, "b": 78},
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor=CHART_PLOT,
                               font={"color": CHART_TEXT, "family": CHART_FONT},
                               yaxis_title="Score", yaxis_range=[0, 105],
                               dragmode="pan",
                               legend={"orientation": "h", "y": 1.02, "yanchor": "bottom"})
    effort_chart.update_xaxes(tickmode="array", tickvals=model_positions,
                              ticktext=colored_model_labels, range=[-0.6, len(model_positions) - 0.4],
                              tickangle=0, tickfont={"size": 12})
    effort_chart.update_yaxes(gridcolor=CHART_GRID, zerolinecolor="#c7bbaa",
                              tickfont={"family": CHART_DATA_FONT, "size": 11})
    bar_config = {"responsive": True, "displaylogo": False, "displayModeBar": "hover",
                  "doubleClick": "reset"}
    return (pio.to_html(multi, full_html=False, include_plotlyjs=False, div_id="benchmark-bars-grouped",
                        post_script=bar_tooltip_script("grouped", role_details["en"], role_details["zh"]),
                        config=bar_config),
            pio.to_html(effort_chart, full_html=False, include_plotlyjs=True,
                        div_id="benchmark-bars-effort",
                        post_script=bar_tooltip_script("effort", effort_details["en"], effort_details["zh"]),
                        config=bar_config))


def page_copy():
    return {
        "en": {
            "brand": "Reviewer Model\nBenchmark",
            "topbar_context": "Model performance overview", "nav_label": "EXPLORE",
            "nav_overview": "Overview", "nav_score": "Weighted score",
            "nav_tradeoffs": "Trade-offs", "nav_cost_score": "Cost vs. score",
            "nav_time_score": "Time vs. score", "nav_time_cost": "Time vs. cost",
            "nav_reviewers": "Reviewer breakdown", "nav_method": "Method & data",
            "eyebrow": "MODEL COMPARISON / BENCHMARK",
            "headline": "Model benchmark using four reviewers",
            "lead": "We use four reviewers throughout the project development lifecycle to evaluate and score models at different reasoning effort levels, then compare their quality, cost, and execution time.",
            "stat_models": "MODELS", "stat_configurations": "CONFIGURATIONS", "stat_benchmarks": "REVIEWER BENCHMARKS",
            "score_kicker": "01 / QUALITY", "score_title": "Weighted score by reasoning effort",
            "score_desc": "Each model forms a group. Its bars show reasoning effort levels with scores from all four reviewers, ordered from highest to lowest.",
            "score_read": "Each group is a model; each bar is a reasoning effort level. Taller bars mean higher scores.",
            "trade_kicker": "02 / TRADE-OFFS", "trade_title": "Quality, time and cost",
            "trade_intro": "Each dot represents one model and reasoning effort configuration. Connecting lines follow effort levels within the same model. The Pareto Front is off by default. Click Pareto Front in any chart legend to show the best visible points and the line connecting them.",
            "cost_score_title": "Equivalent API cost vs. score",
            "cost_score_desc": "Equivalent API cost converts the tokens used for the same workload to USD at published API rates. Locally run models use the corresponding cloud API rate so costs can be compared.",
            "cost_score_read": "Higher is better; farther left is cheaper. The line between dots shows how a model changes across effort levels.",
            "time_score_title": "Execution time vs. score",
            "time_score_desc": "See the quality gained as a model spends more time on the benchmark workload.",
            "time_score_read": "Higher is better; farther left is faster. Time is the average of three benchmark rounds.",
            "time_cost_title": "Execution time vs. equivalent API cost",
            "time_cost_desc": "Inspect the relationship between elapsed time and estimated token cost.",
            "time_cost_read": "Farther left is faster; lower is cheaper. This plot does not encode quality, so use it alongside the score charts.",
            "review_kicker": "03 / BENCHMARK DETAIL", "review_title": "Score by reviewer benchmark",
            "review_desc": "Each group shows the reviewer scores available for a model and effort configuration. Bar labels are rounded for readability; hover for one decimal place.",
            "reviewer_guide_title": "Reviewer work, difficulty and score share",
            "difficulty_label": "Difficulty", "score_share_label": "Score share",
            "difficulty_moderate": "Moderate", "difficulty_high": "High", "difficulty_highest": "Highest",
            "reviewer_standards": "Reviews code changes against repository instructions and implementation quality standards.",
            "reviewer_spec": "Checks whether code changes implement the supplied governing requirements accurately and completely.",
            "reviewer_audit": "Audits a frozen staged candidate for commit scope, required checks and governance requirement coverage.",
            "reviewer_readiness": "Before implementation, checks whether governing documents are complete, consistent, feasible and verifiable.",
            "review_read": "The label color identifies the model. Scroll horizontally to compare all configurations.",
            "method_kicker": "DATA NOTES", "method_title": "How scores and costs are calculated",
            "method_body": "A diagnostic repetition contributes 90% of its score. Each reviewer score is the sum of three adjusted repetition scores divided by three; an unscored repetition contributes zero. Weighted scores require all four reviewers and use their shares above. Equivalent API cost adds uncached input, cached input and output token costs at published per-million-token prices, then divides the three-round total by three. Configurations with missing token totals are omitted from cost charts. GPT uses OpenAI Standard short-context rates; local Bonsai 2 uses the public Alibaba Cloud Beijing qwen3.8-27b API rate. Prices checked 2026-09-25. Cache writes, long context and tool charges are excluded.",
            "openai_prices": "OpenAI pricing", "luna_prices": "GPT-5.6 Luna pricing", "qwen_prices": "Qwen pricing",
            "footer_name": "Reviewer Model Benchmark",
            "footer_copyright": "© 2026 Tranzvision",
            "read_label": "How to read",
        },
        "zh": {
            "brand": "Reviewer\n模型基准",
            "topbar_context": "模型表现概览", "nav_label": "页面索引",
            "nav_overview": "概览", "nav_score": "综合分数",
            "nav_tradeoffs": "权衡比较", "nav_cost_score": "费用与分数",
            "nav_time_score": "耗时与分数", "nav_time_cost": "耗时与费用",
            "nav_reviewers": "Reviewer 分项", "nav_method": "方法与数据",
            "eyebrow": "模型比较 / 基准",
            "headline": "基于 Reviewer 的模型 Benchmark",
            "lead": "我们使用覆盖项目开发生命周期的四个 Reviewer, 验证并评分不同模型和推理强度, 以比较模型的质量, 费用与耗时.",
            "stat_models": "模型", "stat_configurations": "模型配置", "stat_benchmarks": "REVIEWER 基准",
            "score_kicker": "01 / 质量", "score_title": "按推理强度比较综合分数",
            "score_desc": "每组是一个模型, 柱子显示已取得全部 4 项 Reviewer 分数的推理强度, 按从高到低排列.",
            "score_read": "每组代表一个模型, 每根柱子代表一种推理强度. 柱子越高, 分数越高.",
            "trade_kicker": "02 / 权衡", "trade_title": "质量, 耗时与费用",
            "trade_intro": "每个点代表一个模型与推理强度组合. 连线连接同一模型的不同推理强度. 帕累托前沿默认关闭. 点击任一散点图图例中的帕累托前沿, 即可显示当前可见配置的最优点及其连线.",
            "cost_score_title": "等效 API 费用与分数",
            "cost_score_desc": "等效 API 费用是把完成同一组任务消耗的 token, 按公开 API 单价换算成美元; 本地运行的模型也按对应云端 API 价格计算, 便于比较.",
            "cost_score_read": "越高表示分数越好, 越靠左表示费用越低. 点之间的连线显示模型随推理强度的变化.",
            "time_score_title": "耗时与分数",
            "time_score_desc": "查看模型在 benchmark 工作中花费更多时间时, 分数如何变化.",
            "time_score_read": "越高表示分数越好, 越靠左表示耗时越少. 耗时为 3 轮测量的平均值.",
            "time_cost_title": "耗时与等效 API 费用",
            "time_cost_desc": "查看运行耗时与估算 token 费用之间的关系.",
            "time_cost_read": "越靠左表示越快, 越靠下表示越便宜. 此图不表示质量, 需结合分数图阅读.",
            "review_kicker": "03 / 基准明细", "review_title": "按 Reviewer 基准项比较分数",
            "review_desc": "每组显示一个模型配置已取得的各项 Reviewer 分数. 柱面数字四舍五入, 悬停可查看一位小数.",
            "reviewer_guide_title": "Reviewer 工作, 难度与评分占比",
            "difficulty_label": "难度", "score_share_label": "评分占比",
            "difficulty_moderate": "中等", "difficulty_high": "较高", "difficulty_highest": "最高",
            "reviewer_standards": "对照仓库指令与实现质量标准, 审查代码变更.",
            "reviewer_spec": "检查代码变更是否准确, 完整地落实已提供的治理要求.",
            "reviewer_audit": "对冻结的暂存候选进行提交前审计, 检查提交范围, 必要检查与治理要求覆盖.",
            "reviewer_readiness": "在实施前检查治理文档是否完整, 一致, 可实现且可验证.",
            "review_read": "标签颜色对应模型. 水平滚动可查看全部配置.",
            "method_kicker": "数据说明", "method_title": "分数与费用的计算方法",
            "method_body": "诊断性质的单次重复按原分数的 90% 计入. 每项 Reviewer 的分数为 3 次修正后分数之和除以 3; 未得分的一次按 0 计, 分母仍为 3. 综合分数仅在 4 项 Reviewer 均有结果时计算, 采用上方列出的权重. 等效 API 费用按公开的每百万 token 单价, 汇总未缓存输入, 缓存输入和输出费用, 再将 3 轮合计除以 3. 缺少 token 合计的配置不进入费用图. GPT 使用 OpenAI Standard 短上下文价格; 本地 Bonsai 2 使用阿里云北京 qwen3.8-27b 公开 API 价格. 价格核对日期: 2026-09-25. 不含缓存写入, 长上下文和工具附加费用.",
            "openai_prices": "OpenAI 价格", "luna_prices": "GPT-5.6 Luna 价格", "qwen_prices": "Qwen 价格",
            "footer_name": "Reviewer 模型基准",
            "footer_copyright": "© 2026 Tranzvision",
            "read_label": "如何阅读",
        },
    }


def page(items):
    if not isinstance(items, list) or not items or any(
            not isinstance(item, dict) or item.get("schemaVersion") != 3
            for item in items):
        raise ValueError("Expected a nonempty schema-version-3 statistics.json array.")
    grouped, complete = extract(items)
    if not grouped or not complete:
        raise ValueError("At least one reviewer score and one complete configuration are required.")
    copy = page_copy()
    today = date.today()
    copy["en"]["footer_updated"] = f"Updated {today:%b} {today.day}, {today.year}"
    copy["zh"]["footer_updated"] = f"更新于 {today.year} 年 {today.month} 月 {today.day} 日"
    en = copy["en"]

    def phrase(key, tag="span", class_name=""):
        css = f' class="{class_name}"' if class_name else ""
        return f'<{tag}{css} data-i18n="{key}">{en[key]}</{tag}>'

    scatter_specs = (("cost", "score", "cost-score"),
                     ("minutes", "score", "time-score"),
                     ("minutes", "cost", "time-cost"))
    scatter_sections = []
    for index, (xkey, ykey, slug) in enumerate(scatter_specs, 1):
        scatter_sections.append(
            f'<article class="panel" id="{slug}">'
            f'{phrase(slug.replace("-", "_") + "_title", "h3")}'
            f'{phrase(slug.replace("-", "_") + "_desc", "p", "chart-desc")}'
            f'<div class="plot-frame" id="benchmark-frame-{index}">'
            f'<div class="point-tooltip" id="benchmark-tooltip-{index}" hidden></div>'
            f'{chart(complete, xkey, ykey, index)}</div>'
            f'<p class="reading-note"><strong data-i18n="read_label">{en["read_label"]}</strong> · '
            f'{phrase(slug.replace("-", "_") + "_read")}</p></article>')
    grouped_html, effort_html = bars(grouped, complete)
    reviewer_guide = []
    guide_keys = ("reviewer_standards", "reviewer_spec", "reviewer_audit", "reviewer_readiness")
    guide_icons = ("standards", "spec", "audit", "readiness")
    difficulty_keys = ("moderate", "moderate", "high", "highest")
    for (_, name, weight), guide_icon, key, difficulty in zip(REVIEWERS, guide_icons, guide_keys, difficulty_keys):
        reviewer_guide.append(
            f'<div class="reviewer-card"><div class="reviewer-card-title">'
            f'{icon(guide_icon, "reviewer-mark")}<strong>{name}</strong></div>'
            f'<div class="reviewer-card-meta"><span>{phrase("difficulty_label")}: '
            f'<strong>{phrase("difficulty_" + difficulty)}</strong></span>'
            f'<span>{phrase("score_share_label")}: <strong>{weight:.0%}</strong></span></div>'
            f'{phrase(key, "p")}</div>')
    i18n_json = json.dumps(copy, ensure_ascii=False).replace("<", "\\u003c")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Reviewer Model Benchmark</title>
<link rel="icon" type="image/svg+xml" href="resources/favicon.svg">
<style>
:root {{--page:#f4f6fa;--surface:#fff;--line:#dce4ee;--text:#18263b;--muted:#64758b;--accent:#2c609e;--font-body:'Segoe UI Variable Text','Segoe UI',Arial,'Noto Sans SC',sans-serif;--font-display:'Segoe UI Variable Display','Segoe UI',Arial,'Noto Sans SC',sans-serif;--font-data:'Cascadia Code',Consolas,monospace;color-scheme:light}} * {{box-sizing:border-box}} html {{scroll-behavior:smooth}} body {{margin:0;background:var(--page);color:var(--text);font:16px/1.58 var(--font-body)}} a {{color:var(--accent)}}
.app-shell {{display:grid;grid-template-columns:211px minmax(0,1fr);column-gap:28px;width:calc(100% - 48px);max-width:1416px;min-height:100vh;margin:0 auto}} .sidebar {{position:sticky;top:0;align-self:start;height:100vh;overflow-y:auto;background:var(--page);padding:28px 0;display:flex;flex-direction:column;gap:28px}}
.brand {{font:750 16px/1.3 var(--font-display);letter-spacing:.01em}} .side-label {{margin:0 0 10px 16px;color:#687b93;font:700 16px/1.4 var(--font-body);letter-spacing:.03em;text-transform:uppercase}}
.side-nav {{display:flex;flex-direction:column;gap:3px}} .side-nav a {{position:relative;display:block;padding:8px 0 8px 16px;color:#52637c;text-decoration:none;font-size:13px;line-height:1.25;transition:color .2s}} .side-nav a::before {{content:'';position:absolute;left:0;top:50%;width:5px;height:5px;transform:translateY(-50%);background:#a0adbc}} .side-nav a:hover,.side-nav a.active {{color:#243b56}} .side-nav a.active {{font-weight:700}} .side-nav a.active::before {{background:#243b56}} .side-nav a.sub {{padding-left:26px;font-size:12px}} .side-nav a.sub::before {{left:12px;width:4px;height:4px}}
.content {{min-width:0;width:100%;padding:0 0 100px}} .topbar {{height:68px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #dce3ec;background:var(--page)}} .topbar-context {{color:#697b93;font-size:12px;font-weight:650}} .language-group {{display:inline-flex;gap:2px;padding:3px;border:1px solid #d4deea;border-radius:9px;background:#eaf0f6}} .language-group button {{border:0;border-radius:6px;background:transparent;color:#687b92;padding:6px 11px;font:650 12px/1.3 var(--font-body);cursor:pointer;transition:background .18s,color .18s,box-shadow .18s}} .language-group button:hover {{color:#244d78}} .language-group button[aria-pressed="true"] {{background:var(--surface);color:#234f7f;box-shadow:0 1px 4px #1b365729}} .language-group button:focus-visible {{outline:2px solid #4779b1;outline-offset:2px}}
.hero {{padding:38px 0 44px;scroll-margin-top:24px}} .eyebrow,.section-kicker {{color:#3b6fa8;font:750 16px/1.4 var(--font-data);letter-spacing:.06em}} h1 {{max-width:1120px;font:750 clamp(30px,3vw,45px)/1.16 var(--font-display);letter-spacing:-.025em;margin:10px 0 13px}} .lead {{color:#52657d;font-size:17px;margin:0}} .summary-strip {{display:flex;align-items:stretch;width:max-content;max-width:100%;margin-top:24px;background:#fff;border:1px solid #dfe6ee;border-radius:10px;box-shadow:0 4px 18px #25354a08}} .summary-item {{display:flex;align-items:baseline;gap:11px;padding:14px 25px;border-right:1px solid #e6ebf2}} .summary-item:last-child {{border-right:0}} .summary-item strong {{font:700 23px/1 var(--font-data);color:#1f426b;font-variant-numeric:tabular-nums}} .summary-item span {{font-size:10px;letter-spacing:.1em;font-weight:700;color:#7788a0}}
.chart-section,.method-section {{margin:0 0 46px;scroll-margin-top:24px}} .section-heading {{padding:0 2px 17px}} h2 {{font:720 27px/1.25 var(--font-display);margin:6px 0 8px;letter-spacing:-.02em}} .section-heading p {{margin:0;color:#5f7188;font-size:14px;line-height:1.55}} .panel {{border:1px solid #dce4ee;background:#fff;border-radius:12px;margin:0 0 20px;padding:20px 18px 14px;overflow:hidden;scroll-margin-top:24px;box-shadow:0 10px 30px #283b540d;color:#24364d}} h3 {{font:700 20px/1.3 var(--font-display);margin:0 0 5px}} .chart-desc {{color:#64758b;font-size:14px;margin:0 0 8px}} .reading-note {{border-top:1px solid #e4eaf1;margin:2px 0 0;padding:11px 3px 1px;color:#61738a;font-size:13px;line-height:1.5}} .reading-note strong {{color:#2d517d}}
.plot-frame {{position:relative}} .point-tooltip {{position:absolute;z-index:20;max-width:220px;width:max-content;white-space:pre-line;transform:translate(-50%,-100%);pointer-events:none;padding:6px 9px;border:1px solid #9eb0c6;border-radius:7px;background:rgba(255,255,255,.86);color:#18304e;font:12px/1.35 var(--font-data);box-shadow:0 4px 14px #24364b30}}
.point-tooltip[hidden],.bar-tooltip[hidden] {{display:none}} .bar-tooltip {{position:fixed;z-index:100;min-width:210px;max-width:270px;pointer-events:none;padding:10px 12px;border:1px solid #c8c5bd;border-radius:8px;background:rgba(242,240,233,.94);color:#202833;font:12px/1.4 var(--font-body);box-shadow:0 6px 22px #0007}}
.bar-tip-title {{display:block;font-size:13px;margin-bottom:3px}} .bar-tip-meta {{color:#5b6570;border-bottom:1px solid #cdd0d2;padding-bottom:5px;margin-bottom:5px}} .bar-tip-row {{display:flex;align-items:center;gap:6px;padding:2px 0}} .bar-tip-dot {{width:9px;height:9px;border-radius:50%;flex:none}} .bar-tip-name {{flex:1}} .bar-tip-value {{margin-left:8px;font-family:var(--font-data)}}
.js-plotly-plot .scatterlayer .trace .js-line {{transition:stroke-opacity .28s ease,stroke-width .28s ease}} .js-plotly-plot .scatterlayer .trace .point {{transition:opacity .28s ease,stroke .28s ease,stroke-width .28s ease}}
.js-plotly-plot .modebar {{background:transparent!important}} .js-plotly-plot .modebar-group {{background-color:transparent!important}} .js-plotly-plot .modebar-btn path {{fill:#64758b!important}} .js-plotly-plot .modebar-btn:hover path,.js-plotly-plot .modebar-btn.active path {{fill:#2f659c!important}}
.bar-scroll {{min-width:max(100%,calc(var(--groups) * 84px))}} .bar-scroll > div {{margin-inline:auto}} .bar-viewport {{overflow-x:auto}} #score .bar-viewport {{overflow-x:clip}} #score .bar-scroll {{min-width:0;width:100%}} .method-section .panel {{padding:22px 24px;background:#fff;border-color:#dfe6ee;color:#26364b;box-shadow:0 4px 20px #25354a0b}} .method-section p {{color:#52657d;font-size:13px;line-height:1.7}} .source-links {{display:flex;flex-wrap:wrap;gap:16px;font-size:12px}}
.reviewer-guide {{margin:0 0 16px}} .reviewer-guide-heading {{font:680 15px/1.4 var(--font-display);margin:0 0 10px;color:#40536c}} .reviewer-grid {{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}} .reviewer-card {{min-height:130px;padding:14px 15px;border:1px solid #dce4ee;border-radius:9px;background:#fff}} .reviewer-card-title {{display:flex;align-items:center;gap:8px;color:#243a55;font-size:13px}} .reviewer-swatch {{width:8px;height:8px;border-radius:2px;flex:none}} .reviewer-card-meta {{display:flex;flex-wrap:wrap;gap:3px 12px;margin-top:7px;color:#576c84;font-size:12px;line-height:1.35}} .reviewer-card-meta strong {{color:#3a516f;font-weight:700}} .reviewer-card p {{margin:8px 0 0;color:#64758b;font-size:13px;line-height:1.5}}
@media(max-width:1300px) {{.reviewer-grid {{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:900px) {{.app-shell {{display:block;width:100%}} .sidebar {{position:sticky;z-index:30;top:0;height:auto;display:block;padding:12px 16px;border-bottom:1px solid #dce3ec}} .brand {{display:none}} .side-label {{display:none}} .side-nav {{display:flex;flex-direction:row;overflow-x:auto;white-space:nowrap;gap:4px}} .side-nav a,.side-nav a.sub {{padding:7px 9px;font-size:12px}} .side-nav a::before {{display:none}} .side-nav a.active {{border-bottom:2px solid #243b56}} .content {{padding:0 16px 70px}} .hero {{padding-top:25px;scroll-margin-top:64px}} .topbar {{height:51px}} .chart-section,.method-section,.panel {{scroll-margin-top:64px}} .summary-item {{padding:11px 13px;gap:6px}} .summary-item strong {{font-size:19px}} .summary-item span {{font-size:9px}}}}
@media(max-width:600px) {{.reviewer-grid {{grid-template-columns:1fr}} .reviewer-card {{min-height:0}}}}
</style><link rel="stylesheet" href="resources/fonts/fonts.css"><link rel="stylesheet" href="resources/site.css"></head><body><div class="app-shell">
<aside class="sidebar"><div class="brand">{icon('brand', 'brand-mark')}{phrase('brand')}</div><div><div class="side-label" data-i18n="nav_label">{en['nav_label']}</div><nav class="side-nav" aria-label="Page sections">
<a href="#overview" data-i18n="nav_overview" class="active">{en['nav_overview']}</a>
<a href="#score" data-i18n="nav_score">{en['nav_score']}</a>
<a href="#tradeoffs" data-i18n="nav_tradeoffs">{en['nav_tradeoffs']}</a>
<a href="#cost-score" class="sub" data-i18n="nav_cost_score">{en['nav_cost_score']}</a>
<a href="#time-score" class="sub" data-i18n="nav_time_score">{en['nav_time_score']}</a>
<a href="#time-cost" class="sub" data-i18n="nav_time_cost">{en['nav_time_cost']}</a>
<a href="#reviewers" data-i18n="nav_reviewers">{en['nav_reviewers']}</a>
<a href="#method" data-i18n="nav_method">{en['nav_method']}</a></nav></div>
</aside>
<main class="content"><div class="topbar">{phrase('topbar_context', 'span', 'topbar-context')}<div class="language-group" id="language-group" role="group" aria-label="Language"><button id="language-en" type="button" aria-pressed="true">English</button><button id="language-zh" type="button" aria-pressed="false">中文</button></div></div>
<section class="hero" id="overview">{phrase('eyebrow', 'div', 'eyebrow')}{phrase('headline', 'h1')}{phrase('lead', 'p', 'lead')}<div class="summary-strip"><div class="summary-item">{icon('models', 'summary-mark')}<strong>{len({record['model'] for record in grouped})}</strong>{phrase('stat_models')}</div><div class="summary-item">{icon('configurations', 'summary-mark')}<strong>{len(grouped)}</strong>{phrase('stat_configurations')}</div><div class="summary-item">{icon('benchmark', 'summary-mark')}<strong>{len(REVIEWERS)}</strong>{phrase('stat_benchmarks')}</div></div></section>
<section class="chart-section" id="score"><div class="section-heading">{phrase('score_kicker', 'div', 'section-kicker')}{phrase('score_title', 'h2')}{phrase('score_desc', 'p')}</div>
<article class="panel"><div class="bar-tooltip" id="benchmark-bar-tooltip-effort" hidden></div><div class="bar-viewport"><div class="bar-scroll" style="--groups:{len({record['model'] for record in complete})}">{effort_html}</div></div><p class="reading-note"><strong data-i18n="read_label">{en['read_label']}</strong> · {phrase('score_read')}</p></article></section>
<section class="chart-section" id="tradeoffs"><div class="section-heading">{phrase('trade_kicker', 'div', 'section-kicker')}{phrase('trade_title', 'h2')}{phrase('trade_intro', 'p')}</div>{''.join(scatter_sections)}</section>
<section class="chart-section" id="reviewers"><div class="section-heading">{phrase('review_kicker', 'div', 'section-kicker')}{phrase('review_title', 'h2')}{phrase('review_desc', 'p')}</div>
<div class="reviewer-guide">{phrase('reviewer_guide_title', 'h3', 'reviewer-guide-heading')}<div class="reviewer-grid">{''.join(reviewer_guide)}</div></div>
<article class="panel"><div class="bar-tooltip" id="benchmark-bar-tooltip-grouped" hidden></div><div class="bar-viewport"><div class="bar-scroll" style="--groups:{len(grouped)}">{grouped_html}</div></div><p class="reading-note"><strong data-i18n="read_label">{en['read_label']}</strong> · {phrase('review_read')}</p></article></section>
<section class="method-section" id="method"><div class="section-heading">{phrase('method_kicker', 'div', 'section-kicker')}{phrase('method_title', 'h2')}</div><div class="panel">{phrase('method_body', 'p')}<div class="source-links"><a href="https://developers.openai.com/api/docs/pricing" target="_blank" rel="noopener noreferrer">{phrase('openai_prices')}{icon('external', 'external-mark')}</a><a href="https://developers.openai.com/api/docs/models/gpt-5.6-luna" target="_blank" rel="noopener noreferrer">{phrase('luna_prices')}{icon('external', 'external-mark')}</a><a href="https://www.alibabacloud.com/help/en/model-studio/qwen3-8-27b" target="_blank" rel="noopener noreferrer">{phrase('qwen_prices')}{icon('external', 'external-mark')}</a></div></div></section>
</main></div><footer class="page-footer"><div class="footer-brand">{phrase('footer_name', 'span', 'footer-name')}{phrase('footer_copyright', 'span', 'footer-copyright')}</div>{phrase('footer_updated', 'span', 'footer-updated')}</footer><script>
const translations = {i18n_json};
window.chartLanguage = 'en';
const metricTitles = {{en:{{score:'Score',minutes:'Execution time (min)',cost:'Equivalent API cost (USD)'}},zh:{json.dumps(METRIC_LABELS_ZH, ensure_ascii=False)}}};
const scatterAxes = [['cost','score'],['minutes','score'],['minutes','cost']];
const chartIds = ['benchmark-bars-effort','benchmark-scatter-1','benchmark-scatter-2','benchmark-scatter-3','benchmark-bars-grouped'];
function setLanguage(language) {{
  window.chartLanguage = language;
  document.documentElement.lang = language === 'zh' ? 'zh-CN' : 'en';
  for (const element of document.querySelectorAll('[data-i18n]')) element.textContent = translations[language][element.dataset.i18n];
  document.getElementById('language-group').setAttribute('aria-label', language === 'en' ? 'Language' : '语言');
  document.getElementById('language-en').setAttribute('aria-pressed', String(language === 'en'));
  document.getElementById('language-zh').setAttribute('aria-pressed', String(language === 'zh'));
  for (const id of chartIds) document.getElementById(id)?.querySelectorAll('.hoverlayer').forEach(node => node.replaceChildren());
  document.querySelectorAll('.point-tooltip,.bar-tooltip').forEach(tip => {{ tip.hidden = true; }});
  scatterAxes.forEach(([x,y],index) => {{
    const gd = document.getElementById('benchmark-scatter-' + (index + 1));
    Plotly.relayout(gd, {{'xaxis.title.text':metricTitles[language][x], 'yaxis.title.text':metricTitles[language][y]}});
    Plotly.restyle(gd, {{name:[(language === 'en' ? 'Pareto Front' : '帕累托前沿') + {json.dumps(LEGEND_GAP)}]}}, [gd.data.length - 2]);
  }});
  for (const id of ['benchmark-bars-effort','benchmark-bars-grouped']) Plotly.relayout(document.getElementById(id), {{'yaxis.title.text':metricTitles[language].score}});
  requestAnimationFrame(() => chartIds.forEach(id => Plotly.Plots.resize(document.getElementById(id))));
}}
document.getElementById('language-en').addEventListener('click', () => {{ if (window.chartLanguage !== 'en') setLanguage('en'); }});
document.getElementById('language-zh').addEventListener('click', () => {{ if (window.chartLanguage !== 'zh') setLanguage('zh'); }});
const navLinks = [...document.querySelectorAll('.side-nav a')];
const sections = navLinks.map(link => document.querySelector(link.getAttribute('href'))).filter(Boolean);
const observer = new IntersectionObserver(entries => {{
  const visible = entries.filter(entry => entry.isIntersecting).sort((a,b) => a.boundingClientRect.top-b.boundingClientRect.top);
  if (!visible.length) return;
  navLinks.forEach(link => link.classList.toggle('active', link.getAttribute('href') === '#' + visible[0].target.id));
}}, {{rootMargin:'-10% 0px -70% 0px'}});
sections.forEach(section => observer.observe(section));
document.fonts.ready.then(() => requestAnimationFrame(() =>
  chartIds.forEach(id => Plotly.Plots.resize(document.getElementById(id)))));
</script></body></html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("statistics_json", nargs="?", type=Path,
                        default=Path(__file__).with_name("statistics.json"))
    parser.add_argument("output", nargs="?", type=Path,
                        default=Path(__file__).with_name("charts.html"))
    args = parser.parse_args()
    args.output.write_text(page(json.loads(args.statistics_json.read_text(encoding="utf-8"))),
                           encoding="utf-8")
    favicon_path = args.output.parent / "resources" / "favicon.svg"
    favicon_path.parent.mkdir(parents=True, exist_ok=True)
    favicon_path.write_text(favicon_svg(), encoding="utf-8")
    print(args.output)
