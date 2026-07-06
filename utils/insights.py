import pandas as pd
import numpy as np


def generate_insights(df: pd.DataFrame, col_types: dict) -> list[str]:
    """
    Generate human-readable business insights based on column correlations
    and basic descriptive statistics.
    """
    insights = []
    numeric  = col_types["numeric"]
    cats     = col_types["categorical"]
    datetimes = col_types["datetime"]

    # ── Correlation-based insights ─────────────────────────────────────────
    if len(numeric) >= 2:
        corr = df[numeric].corr()
        for i, col_a in enumerate(numeric):
            for col_b in numeric[i + 1:]:
                r = corr.loc[col_a, col_b]
                if abs(r) >= 0.7:
                    direction = "increases" if r > 0 else "decreases"
                    strength  = "strong" if abs(r) >= 0.85 else "moderate"
                    insights.append(
                        f"📈 <strong>{col_a}</strong> and <strong>{col_b}</strong> show a "
                        f"{strength} positive relationship — {col_b} tends to {direction} "
                        f"when {col_a} increases (correlation: {r:.2f})."
                    )
                elif abs(r) >= 0.4:
                    direction = "rise" if r > 0 else "fall"
                    insights.append(
                        f"🔗 There is a noticeable link between <strong>{col_a}</strong> and "
                        f"<strong>{col_b}</strong> — values of {col_b} tend to {direction} "
                        f"as {col_a} grows."
                    )

    # ── Top / Bottom performer insights (categorical) ──────────────────────
    for cat_col in cats[:2]:
        for num_col in numeric[:2]:
            try:
                grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False)
                top    = grouped.index[0]
                bottom = grouped.index[-1]
                top_val    = grouped.iloc[0]
                bottom_val = grouped.iloc[-1]
                insights.append(
                    f"🏆 <strong>{top}</strong> leads in {num_col} "
                    f"(total: {_fmt(top_val)}), while <strong>{bottom}</strong> "
                    f"contributes the least ({_fmt(bottom_val)})."
                )
                # concentration check
                share = top_val / grouped.sum() * 100 if grouped.sum() != 0 else 0
                if share >= 50:
                    insights.append(
                        f"⚠️ <strong>{top}</strong> accounts for {share:.1f}% of total "
                        f"{num_col} — revenue / output is highly concentrated."
                    )
            except Exception:
                pass

    # ── Time-series growth insights ────────────────────────────────────────
    for dt_col in datetimes[:1]:
        for num_col in numeric[:2]:
            try:
                tmp = df[[dt_col, num_col]].dropna().sort_values(dt_col)
                first_half  = tmp.iloc[: len(tmp) // 2][num_col].mean()
                second_half = tmp.iloc[len(tmp) // 2 :][num_col].mean()
                if first_half == 0:
                    continue
                growth = (second_half - first_half) / first_half * 100
                trend  = "upward 📈" if growth > 0 else "downward 📉"
                insights.append(
                    f"📅 <strong>{num_col}</strong> shows a {trend} trend over time "
                    f"({growth:+.1f}% change from the first half to the second half of the dataset)."
                )
            except Exception:
                pass

    # ── Overall numeric summary insights ──────────────────────────────────
    for num_col in numeric[:4]:
        col_data = df[num_col].dropna()
        if len(col_data) == 0:
            continue
        cv = col_data.std() / col_data.mean() * 100 if col_data.mean() != 0 else 0
        if cv > 60:
            insights.append(
                f"📊 <strong>{num_col}</strong> shows high variability "
                f"(CV: {cv:.1f}%) — significant fluctuations exist across records."
            )
        elif cv < 15:
            insights.append(
                f"✅ <strong>{num_col}</strong> is relatively stable "
                f"(CV: {cv:.1f}%) — consistent performance across the dataset."
            )

    if not insights:
        insights.append(
            "ℹ️ The dataset was processed successfully. "
            "Upload a richer dataset with diverse numeric and categorical columns "
            "for deeper business insights."
        )

    return insights[:10]   # cap at 10 insights


def _fmt(value) -> str:
    """Format large numbers with K / M suffix."""
    try:
        v = float(value)
        if abs(v) >= 1_000_000:
            return f"{v/1_000_000:.2f}M"
        if abs(v) >= 1_000:
            return f"{v/1_000:.1f}K"
        return f"{v:.2f}"
    except Exception:
        return str(value)
