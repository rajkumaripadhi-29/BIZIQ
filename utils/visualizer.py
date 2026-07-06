import re
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json


# ── Colour palette ────────────────────────────────────────────────────────────
COLORS = [
    "#4361EE", "#7209B7", "#F72585", "#4CC9F0",
    "#3A0CA3", "#560BAD", "#480CA8", "#3F37C9",
]

LAYOUT_DEFAULTS = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", size=13, color="#E0E0E0"),
    margin=dict(l=40, r=40, t=50, b=50),
    legend=dict(bgcolor="rgba(0,0,0,0)", borderwidth=0),
)


def _fig_to_json(fig) -> str:
    fig.update_layout(**LAYOUT_DEFAULTS)
    return json.loads(fig.to_json())


# ── Aggregation intelligence ──────────────────────────────────────────────────

# Tokens that indicate an ID / serial / record count → count records
_COUNT_TOKENS = {
    "id", "no", "num", "number", "roll", "index", "code",
    "serial", "sno", "sr", "reg", "uid", "eid", "student",
    "employee", "customer", "member", "user", "client",
}
# Tokens that indicate mean is the right aggregation
_MEAN_TOKENS = [
    "mark", "score", "grade", "gpa", "cgpa", "salary", "wage",
    "price", "rate", "ratio", "rating", "performance", "accuracy",
    "efficiency", "avg", "average", "age", "weight", "height",
    "temp", "percent", "speed", "duration", "margin",
]
# Tokens that indicate sum is the right aggregation
_SUM_TOKENS = [
    "revenue", "sales", "profit", "production", "quantity", "qty",
    "amount", "total", "cost", "expense", "budget", "tax", "value",
    "volume", "capacity", "output", "units", "spend", "investment",
    "income", "earning", "gross", "net",
]


def _detect_agg_method(col: str) -> str:
    """
    Choose count / mean / sum based on the column name's semantic meaning.
      count → ID/roll/serial columns  (meaningless to sum)
      mean  → quality measures       (marks, salary, rate …)
      sum   → additive quantities    (revenue, sales, cost …)
    """
    tokens = set(re.split(r"[\s_\-]+", col.lower()))
    col_lower = col.lower()
    if tokens & _COUNT_TOKENS:
        return "count"
    for kw in _MEAN_TOKENS:
        if kw in col_lower:
            return "mean"
    for kw in _SUM_TOKENS:
        if kw in col_lower:
            return "sum"
    return "sum"


def _make_description(chart_type: str, x_col: str, y_col: str,
                      agg_method: str = "sum") -> str:
    """Return a one-line human-readable description for a chart."""
    if chart_type == "line":
        if agg_method == "mean":
            return f"This graph compares the average {y_col} performance over different time periods."
        return f"This graph shows how {y_col} changed over different months/years."
    
    if chart_type == "bar":
        if agg_method == "count":
            return f"This graph shows the count distribution across different {x_col} categories."
        if agg_method == "mean":
            return f"This graph compares the average {y_col} performance of different {x_col} groups."
        return f"This graph shows the total {y_col} contributed by each {x_col} category."
    
    if chart_type == "scatter":
        return f"This graph explores the correlation between {x_col} and {y_col} to identify patterns."
    
    if chart_type == "pie":
        if agg_method == "count":
            return f"This chart shows the percentage distribution of {x_col} across the dataset."
        if agg_method == "mean":
            return f"This chart shows the share of average {y_col} across {x_col} categories."
        return f"This chart shows the contribution share of each {x_col} to the total {y_col}."
    
    return ""


# ── Individual chart builders ─────────────────────────────────────────────────

def line_chart(df: pd.DataFrame, time_col: str, numeric_col: str,
               agg_method: str = "sum") -> dict:
    """Time-series line chart. Groups duplicate timestamps with agg_method."""
    tmp = df[[time_col, numeric_col]].dropna()
    if tmp[time_col].duplicated().any():
        agg_fn = {"mean": "mean", "count": "count"}.get(agg_method, "sum")
        tmp = getattr(tmp.groupby(time_col)[numeric_col], agg_fn)().reset_index()
    tmp = tmp.sort_values(time_col)
    if agg_method == "mean":
        title = f"Average {numeric_col} Over {time_col}"
    elif agg_method == "count":
        title = f"Count of {numeric_col} Over {time_col}"
    else:
        title = f"{numeric_col} Trend Over {time_col}"
    fig = px.line(
        tmp, x=time_col, y=numeric_col,
        title=title,
        color_discrete_sequence=[COLORS[0]],
        markers=True,
    )
    fig.update_traces(line=dict(width=3))
    fig.update_xaxes(showgrid=False, title_text=time_col)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title_text=numeric_col)
    return _fig_to_json(fig)


def bar_chart(df: pd.DataFrame, cat_col: str, numeric_col: str,
              agg_method: str = "sum") -> dict:
    """Bar chart with intelligent aggregation: count / mean / sum."""
    if agg_method == "count":
        tmp = (df.groupby(cat_col).size()
               .reset_index(name="Count")
               .sort_values("Count", ascending=False).head(15))
        y_col, y_label = "Count", "Count"
        chart_title = f"Number of {cat_col} Categories"
    elif agg_method == "mean":
        tmp = (df.groupby(cat_col)[numeric_col].mean().round(2)
               .reset_index().sort_values(numeric_col, ascending=False).head(15))
        y_col, y_label = numeric_col, f"Avg {numeric_col}"
        chart_title = f"Average {numeric_col} by {cat_col}"
    else:
        tmp = (df.groupby(cat_col)[numeric_col].sum()
               .reset_index().sort_values(numeric_col, ascending=False).head(15))
        y_col, y_label = numeric_col, f"Total {numeric_col}"
        chart_title = f"Total {numeric_col} by {cat_col}"
    fig = px.bar(
        tmp, x=cat_col, y=y_col,
        title=chart_title,
        color=y_col,
        color_continuous_scale=["#3A0CA3", "#4361EE", "#4CC9F0"],
    )
    fig.update_xaxes(showgrid=False, title_text=cat_col)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)", title_text=y_label)
    fig.update_coloraxes(showscale=False)
    return _fig_to_json(fig)


def scatter_chart(df: pd.DataFrame, x_col: str, y_col: str) -> dict:
    """Scatter plot with a numpy linear trendline (no statsmodels needed)."""
    tmp = df[[x_col, y_col]].dropna()
    x_vals = tmp[x_col].values.astype(float)
    y_vals = tmp[y_col].values.astype(float)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals,
        mode="markers",
        name=y_col,
        marker=dict(color=COLORS[2], opacity=0.7, size=8),
    ))

    # Compute linear trendline via numpy
    if len(x_vals) >= 2:
        coeffs = np.polyfit(x_vals, y_vals, deg=1)
        x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
        y_line = np.polyval(coeffs, x_line)
        fig.add_trace(go.Scatter(
            x=x_line, y=y_line,
            mode="lines",
            name="Trend",
            line=dict(color=COLORS[3], width=2, dash="dot"),
        ))

    fig.update_layout(
        title=f"{x_col} vs {y_col}",
        xaxis_title=x_col,
        yaxis_title=y_col,
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.08)")
    return _fig_to_json(fig)


def pie_chart(df: pd.DataFrame, cat_col: str, numeric_col: str,
              agg_method: str = "sum") -> dict:
    """Donut chart with intelligent aggregation: count / mean / sum."""
    if agg_method == "count":
        tmp = (df.groupby(cat_col).size()
               .reset_index(name="Count")
               .sort_values("Count", ascending=False).head(10))
        values_col = "Count"
        chart_title = f"{cat_col} Distribution"
    elif agg_method == "mean":
        tmp = (df.groupby(cat_col)[numeric_col].mean().round(2)
               .reset_index().sort_values(numeric_col, ascending=False).head(10))
        values_col = numeric_col
        chart_title = f"Average {numeric_col} by {cat_col}"
    else:
        tmp = (df.groupby(cat_col)[numeric_col].sum()
               .reset_index().sort_values(numeric_col, ascending=False).head(10))
        values_col = numeric_col
        chart_title = f"{cat_col} Contribution to {numeric_col}"
    fig = px.pie(
        tmp, names=cat_col, values=values_col,
        title=chart_title,
        color_discrete_sequence=COLORS,
        hole=0.45,
    )
    fig.update_traces(textinfo="label+percent", pull=[0.03] * len(tmp))
    return _fig_to_json(fig)


# ── Custom chart builder (user-selected columns) ─────────────────────────────

def generate_custom_chart(df: pd.DataFrame, x_col: str, y_col: str,
                          chart_type: str) -> dict:
    """
    Build a single chart from user-chosen columns and chart type.
    Intelligently selects count/mean/sum based on the y-column name.
    Returns {title, description, chart_json, chart_type}.
    """
    chart_type = chart_type.lower().strip()
    # For scatter: no aggregation; for others: detect from y_col
    agg = "sum" if chart_type == "scatter" else _detect_agg_method(y_col)

    if chart_type == "line":
        result = line_chart(df, x_col, y_col, agg)
        title = (f"Average {y_col} Over {x_col}" if agg == "mean"
                 else f"{y_col} Trend Over {x_col}")
    elif chart_type == "bar":
        result = bar_chart(df, x_col, y_col, agg)
        title = (f"Average {y_col} by {x_col}" if agg == "mean"
                 else f"Total {y_col} by {x_col}" if agg == "sum"
                 else f"Number of {x_col} Categories")
    elif chart_type == "scatter":
        result = scatter_chart(df, x_col, y_col)
        title = f"{x_col} vs {y_col}"
    elif chart_type == "pie":
        result = pie_chart(df, x_col, y_col, agg)
        title = (f"{x_col} Distribution" if agg == "count"
                 else f"{x_col} Contribution to {y_col}")
    else:
        raise ValueError(f"Unsupported chart type: {chart_type}")

    return {
        "title": title,
        "description": _make_description(chart_type, x_col, y_col, agg),
        "chart_json": result,
        "chart_type": chart_type,
    }


# ── Master chart generator ────────────────────────────────────────────────────

def generate_charts(df: pd.DataFrame, col_types: dict) -> list[dict]:
    """
    Intelligently decide which charts to generate.
    - Detects count/mean/sum per column pair
    - Skips duplicates, uninformative cols, and caps at 8 charts
    - Attaches title + description to every chart
    """
    MAX_CHARTS = 8
    CORR_THRESHOLD = 0.4
    seen_pairs: set = set()

    numeric   = col_types["numeric"]
    cats      = col_types["categorical"]
    datetimes = col_types["datetime"]
    charts: list[dict] = []

    def _pair_key(a: str, b: str) -> tuple:
        return (min(a, b), max(a, b))

    def _add(chart_dict: dict, a: str, b: str) -> bool:
        key = _pair_key(a, b)
        if key in seen_pairs or len(charts) >= MAX_CHARTS:
            return False
        charts.append(chart_dict)
        seen_pairs.add(key)
        return True

    # A. Date/Time + Numeric → Line charts
    for dt_col in datetimes[:2]:
        for num_col in numeric[:2]:
            if len(charts) >= MAX_CHARTS:
                break
            try:
                agg = _detect_agg_method(num_col)
                chart = line_chart(df, dt_col, num_col, agg)
                title = (f"Average {num_col} Over {dt_col}" if agg == "mean"
                         else f"{num_col} Trend Over {dt_col}")
                _add({"title": title,
                      "description": _make_description("line", dt_col, num_col, agg),
                      "chart_json": chart, "chart_type": "line"}, dt_col, num_col)
            except Exception:
                pass

    # B. Categorical + Numeric → Bar or Pie
    for cat_col in cats[:4]:
        if len(charts) >= MAX_CHARTS:
            break
        unique_count = df[cat_col].nunique()
        if unique_count < 2 or unique_count > 50:
            continue
        for num_col in numeric[:2]:
            if len(charts) >= MAX_CHARTS:
                break
            try:
                agg = _detect_agg_method(num_col)
                if unique_count <= 6:
                    chart = pie_chart(df, cat_col, num_col, agg)
                    title = (f"{cat_col} Distribution" if agg == "count"
                             else f"{cat_col} Contribution to {num_col}")
                    _add({"title": title,
                          "description": _make_description("pie", cat_col, num_col, agg),
                          "chart_json": chart, "chart_type": "pie"}, cat_col, num_col)
                else:
                    chart = bar_chart(df, cat_col, num_col, agg)
                    title = (f"Average {num_col} by {cat_col}" if agg == "mean"
                             else f"Total {num_col} by {cat_col}" if agg == "sum"
                             else f"Number of {cat_col} Categories")
                    _add({"title": title,
                          "description": _make_description("bar", cat_col, num_col, agg),
                          "chart_json": chart, "chart_type": "bar"}, cat_col, num_col)
            except Exception:
                pass

    # C. Numeric + Numeric → Scatter (high-correlation pairs only)
    if len(numeric) >= 2 and len(charts) < MAX_CHARTS:
        try:
            corr_matrix = df[numeric].corr().abs()
            pairs = (
                corr_matrix
                .where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
                .stack().sort_values(ascending=False)
            )
            scatter_added = 0
            for (x_col, y_col), corr_val in pairs.items():
                if scatter_added >= 3 or len(charts) >= MAX_CHARTS:
                    break
                if corr_val < CORR_THRESHOLD:
                    continue
                try:
                    chart = scatter_chart(df, x_col, y_col)
                    if _add({"title": f"{x_col} vs {y_col}",
                             "description": _make_description("scatter", x_col, y_col),
                             "chart_json": chart, "chart_type": "scatter"}, x_col, y_col):
                        scatter_added += 1
                except Exception:
                    pass
        except Exception:
            pass

    return charts
