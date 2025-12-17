"""
plots.py

Generates analytical figures for DE1 Homework:
1. Average sentiment: Articles vs YouTube (incl. mixed)
2. Average sentiment by source (incl. mixed)
3. Sentiment distribution (Positive vs Negative)
4. Diverging sentiment by source (Articles vs YouTube)
5. Sentiment Polarization Index
6. Stacked sentiment composition by source

All graphs are saved to output/graphs/
"""

# -----------------------------
# 1. IMPORTS
# -----------------------------
import pandas as pd
import matplotlib.pyplot as plt
import os

# -----------------------------
# 2. SENTIMENT COLOR PALETTE
# -----------------------------
SENTIMENT_COLORS = {
    "positive": "#9CAFAA",   
    "negative": "#EFBC9B",   
    "neutral":  "#FBF3D5",  
    "mixed":    "#D6DAC8"   
}
CONTENT_TYPE_COLORS = {
    "article": "#727D73",   
    "youtube": "#EDA35A"   
}

# -----------------------------
# 3. LOAD DATA
# -----------------------------
df = pd.read_csv("output/csv/sentiment_results.csv")

os.makedirs("output/graphs", exist_ok=True)
os.makedirs("output/csv", exist_ok=True)

# -----------------------------
# 4. GRAPH 1:
# Average sentiment: Articles vs YouTube
# -----------------------------
avg_by_type = (
    df
    .groupby("content_type")[["positive", "negative", "neutral", "mixed"]]
    .mean()
)

avg_by_type.plot(
    kind="bar",
    color=[
        SENTIMENT_COLORS["positive"],
        SENTIMENT_COLORS["negative"],
        SENTIMENT_COLORS["neutral"],
        SENTIMENT_COLORS["mixed"],
    ]
)

plt.title("Average Sentiment: Articles vs YouTube")
plt.ylabel("Average Sentiment Score")
plt.xlabel("Content Type")
plt.xticks(rotation=0)
plt.legend(
    title="Sentiment",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)
plt.tight_layout()
plt.savefig("output/graphs/graph_1_articles_vs_youtube.png")
plt.close()

# -----------------------------
# 5. GRAPH 2:
# Average sentiment by source
# -----------------------------
avg_by_source = (
    df
    .groupby("source")[["positive", "negative", "neutral", "mixed"]]
    .mean()
)

avg_by_source.plot(
    kind="bar",
    color=[
        SENTIMENT_COLORS["positive"],
        SENTIMENT_COLORS["negative"],
        SENTIMENT_COLORS["neutral"],
        SENTIMENT_COLORS["mixed"],
    ]
)

plt.title("Average Sentiment by Source")
plt.ylabel("Average Sentiment Score")
plt.xlabel("Source")
plt.xticks(rotation=45, ha="right")
plt.legend(
    title="Sentiment",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    borderaxespad=0
)
plt.tight_layout()
plt.savefig("output/graphs/graph_2_sentiment_by_source.png")
plt.close()

# -----------------------------
# 6. GRAPH 3:
# Sentiment distribution (Positive vs Negative)
# -----------------------------
plt.figure(figsize=(6, 5))

for content_type in df["content_type"].unique():
    subset = df[df["content_type"] == content_type]
    plt.scatter(
        subset["positive"],
        subset["negative"],
        label=content_type.capitalize(),
        color=CONTENT_TYPE_COLORS.get(content_type, "gray"),
        alpha=1
    )

plt.xlabel("Positive Sentiment Score")
plt.ylabel("Negative Sentiment Score")
plt.title("Sentiment Distribution: Articles vs YouTube")
plt.legend(title="Content Type")
plt.tight_layout()
plt.savefig("output/graphs/graph_3_sentiment_distribution.png")
plt.close()


# -----------------------------
# 7. GRAPH 4:
# Diverging sentiment by source
# -----------------------------
summary = (
    df
    .groupby(["content_type", "source"])[["positive", "negative"]]
    .mean()
    .reset_index()
)

articles = summary[summary["content_type"] == "article"].copy()
youtube = summary[summary["content_type"] == "youtube"].copy()

articles["negative"] = -articles["negative"]
youtube["negative"] = -youtube["negative"]

fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 6), sharex=True)

# Articles subplot
axes[0].barh(
    articles["source"],
    articles["negative"],
    color=SENTIMENT_COLORS["negative"],
    label="Negative"
)
axes[0].barh(
    articles["source"],
    articles["positive"],
    color=SENTIMENT_COLORS["positive"],
    label="Positive"
)
axes[0].axvline(0, color="black", linewidth=1)
axes[0].set_title("Articles")
axes[0].set_xlabel("Sentiment Score")

# YouTube subplot
axes[1].barh(
    youtube["source"],
    youtube["negative"],
    color=SENTIMENT_COLORS["negative"],
    label="Negative"
)
axes[1].barh(
    youtube["source"],
    youtube["positive"],
    color=SENTIMENT_COLORS["positive"],
    label="Positive"
)
axes[1].axvline(0, color="black", linewidth=1)
axes[1].set_title("YouTube")
axes[1].set_xlabel("Sentiment Score")

axes[0].legend(loc="lower right")

plt.suptitle("Sentiment Balance by Source and Content Type")
plt.tight_layout()
plt.savefig("output/graphs/graph_4_sentiment_diverging_by_source.png")
plt.close()

# -----------------------------
# 8. GRAPH 5 + TABLE:
# Sentiment Polarization Index
# -----------------------------
polarization = (
    df
    .assign(polarization=lambda x: x["positive"] - x["negative"])
    .groupby(["content_type", "source"])["polarization"]
    .mean()
    .reset_index()
)

polarization.to_csv(
    "output/csv/sentiment_polarization_table.csv",
    index=False
)

plt.figure(figsize=(10, 5))

for content_type in polarization["content_type"].unique():
    subset = polarization[polarization["content_type"] == content_type]
    plt.bar(
        subset["source"],
        subset["polarization"],
        label=content_type.capitalize(),
        color=CONTENT_TYPE_COLORS.get(content_type, "gray"),
        alpha=1,
    )

plt.axhline(0, color="black", linewidth=1)
plt.title("Sentiment Polarization Index by Source")
plt.ylabel("Positive − Negative")
plt.xticks(rotation=45, ha="right")
plt.legend(title="Content Type")
plt.tight_layout()
plt.savefig("output/graphs/graph_5_polarization_index.png")
plt.close()

# -----------------------------
# 9. GRAPH 6:
# Stacked sentiment composition by source
# -----------------------------
composition = (
    df
    .groupby("source")[["positive", "negative", "neutral", "mixed"]]
    .mean()
)

composition.plot(
    kind="bar",
    stacked=True,
    figsize=(10, 6),
    color=[
        SENTIMENT_COLORS["positive"],
        SENTIMENT_COLORS["negative"],
        SENTIMENT_COLORS["neutral"],
        SENTIMENT_COLORS["mixed"],
    ]
)

plt.title("Sentiment Composition by Source")
plt.ylabel("Average Sentiment Share")
plt.xlabel("Source")
plt.xticks(rotation=45, ha="right")
plt.legend(
    title="Sentiment",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)
plt.tight_layout()
plt.savefig("output/graphs/graph_6_sentiment_composition.png")
plt.close()

# -----------------------------
# 10. TABLE:
# Ranking sources by sentiment polarity
# -----------------------------
ranking = (
    df
    .assign(polarity=lambda x: x["positive"] - x["negative"])
    .groupby(["content_type", "source"])["polarity"]
    .mean()
    .reset_index()
    .sort_values("polarity")
)

ranking.to_csv(
    "output/csv/sentiment_ranking_table.csv",
    index=False
)

# -----------------------------
# DONE
# -----------------------------
print("Graphs successfully generated:")
print("- graph_1_articles_vs_youtube.png")
print("- graph_2_sentiment_by_source.png")
print("- graph_3_sentiment_distribution.png")
print("- graph_4_sentiment_diverging_by_source.png")
print("- graph_5_polarization_index.png")
print("- graph_6_sentiment_composition.png")
