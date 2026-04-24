import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

st.set_page_config(
    page_title="Weekly Article and Word Count Model",
    layout="wide",
)

st.title("Weekly Article and Word Count Model")

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
        7843.7313,
        3305.1155,
        31.8693,
        2.6766,
    ],
    "Article Std Error": [
        1240.746,
        881.787,
        17.231,
        1.133,
    ],
    "Word Effect per Word": [
        3.6605,
        2.1575,
        0.0265,
        0.001,
    ],
    "Word Std Error per Word": [
        0.648,
        0.418,
        0.008,
        0.001,
    ],

    #"Residual Std Error": [
    #    57952.772680020884,  # Page Views
    #    37394.52187763929,      # Engaged Minutes — replace when you have it
    #    760.5118600423876,      # Account Registrations — replace when you have it
    #    52.044676873922135,      # Subscriptions — replace when you have it
    #],

    "Residual Std Error": [
        46404.778253,
        37659.308902,
        681.724890,
        50.927862,
    ],

    "Posts Posts Covariance": [
        2.583466e6,
        1.701461e6,
        5.626509e2,
        3.130446e0,
    ],

    "Posts Words Covariance": [
        -1.013996e3,
        -6.678139e2,
        -2.214952e-1,
        -1.238232e-3,
    ],

    "Words Words Covariance": [
        6.824645e-1,
        4.494686e-1,
        1.528026e-4,
        8.425159e-7,
    ],
})

baseline_articles = 18
baseline_words = 29500


def calculate_projection(articles, words):
    delta_articles = articles - baseline_articles
    delta_words = words - baseline_words

    result = model.copy()

    result["Current Articles"] = articles
    result["Current Word Count"] = words
    result["Article Delta"] = delta_articles
    result["Word Delta"] = delta_words
    result["Mean Word Count per Article"] = words / articles if articles else 0

    result["Projected"] = (
        result["Baseline"]
        + delta_articles * result["Article Effect"]
        + delta_words * result["Word Effect per Word"]
    )

    result["Change vs Baseline"] = result["Projected"] - result["Baseline"]

    #result["Approx Std Error"] = (
    #    (delta_articles * result["Article Std Error"]) ** 2
    #    + (delta_words * result["Word Std Error per Word"]) ** 2
    #    + result["Residual Std Error"] ** 2
    #).pow(0.5)

    result["Approx Std Error"] = (
        (delta_articles ** 2) * result["Posts Posts Covariance"]
        + (delta_words ** 2) * result["Words Words Covariance"]
        + 2 * delta_articles * delta_words * result["Posts Words Covariance"]
        + result["Residual Std Error"] ** 2
    ).pow(0.5)

    result["Low 95%"] = result["Projected"] - 1.96 * result["Approx Std Error"]
    result["High 95%"] = result["Projected"] + 1.96 * result["Approx Std Error"]

    return result


def calculate_words_per_article():
    summary = model.copy()

    summary["Words per Article Equivalent"] = (
        summary["Article Effect"] / summary["Word Effect per Word"]
    )

    summary["Words per Article Std Error"] = (
        summary["Words per Article Equivalent"]
        * (
            (summary["Article Std Error"] / summary["Article Effect"]) ** 2
            + (
                summary["Word Std Error per Word"]
                / summary["Word Effect per Word"]
            ) ** 2
        ) ** 0.5
    )

    summary["Display"] = (
        summary["Words per Article Equivalent"].map(lambda x: f"{x:,.0f}")
        + " ± "
        + summary["Words per Article Std Error"].map(lambda x: f"{x:,.0f}")
        + " words"
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

        #low = min(row["Baseline"], row["Projected"], row["Low 95%"])
        #high = max(row["Baseline"], row["Projected"], row["High 95%"])

        #padding = (high - low) * 0.2 if high != low else high * 0.2
        #ax.set_ylim(max(0, low - padding), high + padding)

        high = max(row["Baseline"], row["Projected"], row["High 95%"])

        padding = high * 0.2 if high != 0 else 1
        ax.set_ylim(0, high + padding)

        #change = row["Change vs Baseline"]
        #ax.text(
        #    1,
        #    row["Projected"],
        #    f"{change:+,.0f}",
        #    ha="center",
        #    va="bottom",
        #    fontsize=10,
        #    fontweight="bold",
        #)

        change = row["Change vs Baseline"]
        percent_change = change / row["Baseline"] if row["Baseline"] else 0

        ax.text(
            1.05,  # slight right offset
            row["Projected"],
            f"{percent_change:+.0%}",
            ha="left",  # anchor from left so it moves right cleanly
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )
        ax.tick_params(axis="x", rotation=25)

    fig.suptitle("Weekly Chronicle.com Projected Metrics", y=1.05)
    plt.tight_layout()

    return fig

col1, col2 = st.columns(2)

with col1:
    articles = st.slider(
        "Weekly Articles Published (Average = 18)",
        min_value=10,
        max_value=baseline_articles + 20,
        value=baseline_articles,
        step=1,
    )

with col2:
    words = st.slider(
        "Total word count (Average = 29,500)",
        min_value=max(0, baseline_words - 20000),
        max_value=baseline_words + 20000,
        value=baseline_words,
        step=1000,
    )

mean_words_per_article = words / articles if articles else 0

st.metric(
    "Mean Word Count per Article",
    f"{mean_words_per_article:,.0f}",
)

result = calculate_projection(articles, words)

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

st.subheader("How many words is 1 article equal to?")

st.dataframe(
    summary[["Metric", "Display"]].rename(
        columns={"Display": "Equivalent Words"}
    ),
    width="stretch",
    hide_index=True,
)

st.divider()

st.caption(
    "Projected = Baseline + Article Delta × Article Effect + "
    "Word Delta × Word Effect per Word. "
    "95% range includes coefficient uncertainty plus residual model error."
)