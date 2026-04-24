import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

st.set_page_config(
    page_title="Weekly Article, Word Count, and Topic Model",
    layout="wide",
)

st.title("Weekly Article, Word Count, and Topic Model")

model = pd.DataFrame({
    "Metric": [
        "Page Views (GA4)",
        "Engaged Minutes (Parse.ly)",
        "Account Registrations (GA4)",
        "Subscriptions (GA4)",
    ],
    "Baseline": [
        462416,
        226000,
        2650,
        160,
    ],

    "Article Effect": [
        7566.6360,
        3536.0864,
        -3.1476,
        4.1451,
    ],
    "Article Std Error": [
        1812.078,
        1242.753,
        24.456,
        1.668,
    ],

    "Mean Words Effect": [
        22.5574,
        31.8648,
        0.3176,
        0.0004,
    ],
    "Mean Words Std Error": [
        14.060,
        9.644,
        0.190,
        0.013,
    ],

    "Topic Effect": [
        1315.3837,
        513.2204,
        87.0369,
        -3.5822,
    ],
    "Topic Std Error": [
        2909.563,
        1995.880,
        39.277,
        2.683,
    ],

    "Residual Std Error": [
        56257.426323,
        38599.714521,
        759.609401,
        51.607990,
    ],

    "Articles Articles Covariance": [
        3.283627e6,
        1.544436e6,
        5.981119e2,
        2.781999e0,
    ],
    "Articles Mean Words Covariance": [
        6597.152721,
        3097.601330,
        1.199604,
        0.005467,
    ],
    "Articles Topics Covariance": [
        -3.791977e6,
        -1.786729e6,
        -6.919444e2,
        -3.234415e0,
    ],
    "Mean Words Mean Words Covariance": [
        197.683010,
        93.015713,
        0.036022,
        0.000167,
    ],
    "Mean Words Topics Covariance": [
        -9257.707114,
        -4367.468522,
        -1.691384,
        -0.007673,
    ],
    "Topics Topics Covariance": [
        8.465560e6,
        3.983537e6,
        1.542699e3,
        7.198256e0,
    ],
})

baseline_articles = 18
baseline_mean_words = 1700
baseline_topics = 11

def calculate_projection(articles, mean_words, topics):
    delta_articles = articles - baseline_articles
    delta_mean_words = mean_words - baseline_mean_words
    delta_topics = topics - baseline_topics

    result = model.copy()

    result["Current Articles"] = articles
    result["Current Mean Word Count per Article"] = mean_words
    result["Current Topics Covered"] = topics

    result["Article Delta"] = delta_articles
    result["Mean Word Count Delta"] = delta_mean_words
    result["Topic Delta"] = delta_topics

    result["Projected"] = (
        result["Baseline"]
        + delta_articles * result["Article Effect"]
        + delta_mean_words * result["Mean Words Effect"]
        + delta_topics * result["Topic Effect"]
    )

    result["Change vs Baseline"] = result["Projected"] - result["Baseline"]

    result["Approx Std Error"] = (
        (delta_articles ** 2) * result["Articles Articles Covariance"]
        + (delta_mean_words ** 2) * result["Mean Words Mean Words Covariance"]
        + (delta_topics ** 2) * result["Topics Topics Covariance"]
        + 2 * delta_articles * delta_mean_words * result["Articles Mean Words Covariance"]
        + 2 * delta_articles * delta_topics * result["Articles Topics Covariance"]
        + 2 * delta_mean_words * delta_topics * result["Mean Words Topics Covariance"]
        + result["Residual Std Error"] ** 2
    ).pow(0.5)

    result["Low 95%"] = result["Projected"] - 1.96 * result["Approx Std Error"]
    result["High 95%"] = result["Projected"] + 1.96 * result["Approx Std Error"]

    return result


def calculate_words_per_article():
    data = pd.DataFrame({
        "Metric": [
            "Page Views (GA4)",
            "Engaged Minutes (Parse.ly)",
            "Account Registrations (GA4)",
            "Subscriptions (GA4)",
        ],
        "Display": [
            "2,143 ± 840 words",
            "1,532 ± 790 words",
            "1,202 ± 600 words",
            "2,677 ± 1,600 words",
        ],
    })
    return data

def format_y_axis(x, pos):
    if abs(x) >= 100_000:
        return f"{x / 1000:,.0f}K"
    if abs(x) >= 1_000:
        return f"{x:,.0f}"
    return f"{x:.0f}"


def make_plot(result):
    fig, axes = plt.subplots(
        nrows=1,
        ncols=len(result),
        figsize=(4.5 * len(result), 4.5),
    )

    if len(result) == 1:
        axes = [axes]

    for ax, (_, row) in zip(axes, result.iterrows()):
        values = [row["Baseline"], row["Projected"]]

        error_values = [
            1.96 * row["Residual Std Error"],
            1.96 * row["Approx Std Error"],
        ]

        ax.bar(
            ["Baseline", "Projected"],
            values,
            yerr=error_values,
            capsize=0,
            color=["#1f77b4", "#ff7f0e"],
            ecolor="gray",
            error_kw={
                "elinewidth": 1,
                "capsize": 0,
            },
        )

        ax.set_title(row["Metric"])
        ax.yaxis.set_major_formatter(FuncFormatter(format_y_axis))

        high = max(row["Baseline"], row["Projected"], row["High 95%"])
        padding = high * 0.2 if high != 0 else 1
        ax.set_ylim(0, high + padding)

        change = row["Change vs Baseline"]
        percent_change = change / row["Baseline"] if row["Baseline"] else 0

        ax.text(
            1.05,
            row["Projected"],
            f"{percent_change:+.0%}",
            ha="left",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

        ax.tick_params(axis="x", rotation=25)

    fig.suptitle("Weekly Chronicle.com Projected Metrics", y=1.05)
    plt.tight_layout()

    return fig

col1, col2, col3 = st.columns(3)

with col1:
    articles = st.slider(
        f"Weekly Articles Published (Average = {baseline_articles})",
        min_value=10,
        max_value=baseline_articles + 20,
        value=baseline_articles,
        step=1,
    )

with col2:
    mean_words = st.slider(
        f"Mean Article Word Count (Average = {baseline_mean_words:,.0f})",
        min_value=500,
        max_value=int(baseline_mean_words + 2000),
        value=int(baseline_mean_words),
        step=100,
    )

with col3:
    topics = st.slider(
        f"Weekly Topics Covered (Average = {baseline_topics})",
        min_value=5,
        max_value=max(20, baseline_topics + 20),
        value=baseline_topics,
        step=1,
    )

result = calculate_projection(articles, mean_words, topics)

display_cols = [
    "Metric",
    "Baseline",
    "Projected",
    "Change vs Baseline",
    "Low 95%",
    "High 95%",
]

table = result[display_cols].copy()

for col in [
    "Baseline",
    "Projected",
    "Change vs Baseline",
    "Low 95%",
    "High 95%",
]:
    table[col] = table[col].map(lambda x: f"{x:,.0f}")

st.subheader("Projected Weekly Metrics")

st.dataframe(
    table,
    width="stretch",
    hide_index=True,
)

fig = make_plot(result)
st.pyplot(fig)

summary = calculate_words_per_article()

st.subheader("How many mean words is 1 article equal to?")

st.dataframe(
    summary[["Metric", "Display"]].rename(
        columns={"Display": "Equivalent Mean Words"}
    ),
    width="stretch",
    hide_index=True,
)

st.divider()

st.caption(
    "Projected = Baseline + Article Delta × Article Effect + "
    "Mean Word Count Delta × Mean Words Effect + "
    "Topic Delta × Topic Effect. "
    "95% range includes coefficient uncertainty, covariance, and residual model error."
)