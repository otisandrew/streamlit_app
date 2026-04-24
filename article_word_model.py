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
        7670.5871,
        3557.9361,
        -3.1059,
        4.1938,
    ],
    "Article Std Error": [
        1904.381,
        1305.388,
        25.780,
        1.753,
    ],

    "Mean Words Effect": [
        22.8580,
        31.9386,
        0.3216,
        0.0003,
    ],
    "Mean Words Std Error": [
        14.104,
        9.671,
        0.191,
        0.013,
    ],

    "Topic Effect": [
        1016.2025,
        436.0839,
        81.6239,
        -3.4655,
    ],
    "Topic Std Error": [
        2991.338,
        2051.728,
        40.519,
        2.759,
    ],

    "Residual Std Error": [
        56279.745857,
        38603.290347,
        762.370406,
        51.654574,
    ],

    "Articles Articles Covariance": [
        3.626668e6,
        1.704039e6,
        6.646040e2,
        3.074299e0,
    ],
    "Articles Mean Words Covariance": [
        7236.697864,
        3393.211266,
        1.323410,
        0.006002,
    ],
    "Articles Topics Covariance": [
        -4.272824e6,
        -2.011179e6,
        -7.843937e2,
        -3.642994e0,
    ],
    "Mean Words Mean Words Covariance": [
        198.926952,
        93.532663,
        0.036479,
        0.000168,
    ],
    "Mean Words Topics Covariance": [
        -10019.449889,
        -4718.529850,
        -1.840306,
        -0.008317,
    ],
    "Topics Topics Covariance": [
        8.948104e6,
        4.209586e6,
        1.641810e3,
        7.613108e0,
    ],
})

baseline_articles = 18
baseline_mean_words = 1700
baseline_topics = 12

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
    summary = model.copy()

    summary["Words per Article Equivalent"] = (
        summary["Article Effect"] / summary["Mean Words Effect"]
    )

    summary["Words per Article Std Error"] = (
        summary["Words per Article Equivalent"]
        * (
            (summary["Article Std Error"] / summary["Article Effect"]) ** 2
            + (summary["Mean Words Std Error"] / summary["Mean Words Effect"]) ** 2
        ) ** 0.5
    )

    summary["Display"] = summary.apply(
        lambda row: "Fill in Mean Words Effect"
        if row["Mean Words Effect"] == 0
        else (
            f"{row['Words per Article Equivalent']:,.0f}"
            f" ± {row['Words per Article Std Error']:,.0f} words"
        ),
        axis=1,
    )

    return summary


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
        f"Mean Words per Article (Average = {baseline_mean_words:,.0f})",
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

st.metric(
    "Mean Word Count per Article",
    f"{mean_words:,.0f}",
)

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