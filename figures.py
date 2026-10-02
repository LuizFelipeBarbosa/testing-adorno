"""Generate article figures and the CSV tables behind them from a processed frame."""

from collections import Counter
from pathlib import Path
import re

import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import PercentFormatter, StrMethodFormatter
import numpy as np
import pandas as pd

from nlp_pipeline.utils import load_yaml


def create_figures(df: pd.DataFrame, output: Path, labels: list[str]) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    LABELS = labels
    NAMES = [
        "Standardization",
        "Pseudo-individualization",
        "Commodification / market logic",
        "Regressive listening",
        "Affective prepackaging",
        "Formal resistance",
    ]
    RULES = ["rule_" + label for label in LABELS]
    N = len(df)
    hits = df[RULES].any(axis=1)
    BLUE, ORANGE, GREY = "#2463a7", "#bd670d", "#8b98a5"
    BG, INK = "#fafafa", "#243343"
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "figure.facecolor": BG,
            "axes.facecolor": BG,
            "savefig.facecolor": BG,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.spines.bottom": False,
            "svg.fonttype": "none",
        }
    )
    book = PdfPages(output / "figures.pdf")

    def canvas(title, subtitle, height=6, left=0.29):
        fig, ax = plt.subplots(figsize=(12, height))
        fig.subplots_adjust(left=left, right=0.94, top=0.78, bottom=0.20)
        fig.text(0.035, 0.955, title, fontsize=19, weight="bold", va="top")
        fig.text(0.035, 0.88, subtitle, fontsize=10.5, va="top")
        ax.tick_params(length=0, pad=8)
        ax.grid(axis="x", color="#dce2e8", linewidth=0.6)
        ax.set_axisbelow(True)
        return fig, ax

    def save(fig, name, note):
        fig.text(0.035, 0.105, note, fontsize=9, va="top", color="#526170")
        fig.text(
            0.035,
            0.022,
            f"Source: testing-adorno · {N:,} retained comments · {df.song_title.nunique()} songs · 2025 releases",
            fontsize=8,
            color="#526170",
        )
        fig.savefig(output / f"{name}.png", dpi=180)
        fig.savefig(output / f"{name}.svg")
        book.savefig(fig)
        plt.close(fig)

    # Denominators are separate subsets, not a sequential language-filter funnel.
    fig, ax = canvas(
        f"{100 * hits.mean():.2f}% is a rule-match rate",
        "The detector matches wording. It has not measured the prevalence of critical engagement.",
        left=0.37,
    )
    categories = [
        "No label matched",
        "Formal resistance only",
        "At least one of the other five labels",
    ]
    values = [
        int((~hits).sum()),
        int((df[RULES[-1]] & ~df[RULES[:5]].any(axis=1)).sum()),
        int(df[RULES[:5]].any(axis=1).sum()),
    ]
    y = np.arange(3)[::-1]
    ax.scatter(values, y, color=[GREY, ORANGE, BLUE], s=85)
    ax.set_xscale("log")
    ax.set_xlim(40, 400000)
    ax.set_ylim(-0.5, 2.5)
    ax.set_yticks(y, categories)
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    for yy, value in zip(y, values):
        ax.annotate(
            f"{value:,}  ·  {100 * value / N:.3f}%",
            (value, yy),
            xytext=(10, 10),
            textcoords="offset points",
        )
    ax.set_xlabel("Comments · logarithmic scale")
    save(
        fig,
        "01_match_coverage",
        "These three groups are disjoint and cover the corpus. The last group includes one formal-resistance overlap.\n269 comments matched any label; the remaining 84,547 are not established to be uncritical.",
    )

    counts = df[RULES].sum().to_numpy()
    fig, ax = canvas(
        "Six labels, very different match counts",
        "All percentages use the full corpus. Labels overlap, so the six rows are not additive.",
        left=0.29,
    )
    y = np.arange(6)[::-1]
    ax.barh(y, counts, color=[BLUE] * 5 + [ORANGE], height=0.58)
    ax.set_yticks(y, NAMES)
    ax.set_xlim(0, 235)
    for yy, count in zip(y, counts):
        ax.text(count + 3, yy, f"{count:,}  ·  {100 * count / N:.4f}%", va="center")
    ax.set_xlabel("Comments matching each label")
    save(
        fig,
        "02_label_counts",
        f"{int(df[RULES].sum().sum())} label assignments across {int(hits.sum())} comments; {int((df[RULES].sum(axis=1) > 1).sum())} multi-label rows.\nOrange marks the inverse-polarity category. Neither color establishes theoretical validity.",
    )

    lengths = df.text_length
    sorted_lengths = np.sort(lengths)
    fig, ax = canvas(
        f"The median cleaned comment has {df.text_length.median():g} characters",
        "A cumulative distribution shows exact thresholds without hiding the long tail.",
        left=0.10,
    )
    ax.step(
        sorted_lengths, np.arange(1, N + 1) / N, where="post", color=BLUE, linewidth=2
    )
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlim(0, 6000)
    ax.set_ylim(0, 1.03)
    ax.set_xticks([0, 1, 5, 10, 25, 50, 100, 500, 1000, 5000])
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel(
        "Cleaned comment length · characters (linear from 0 to 1, logarithmic thereafter)"
    )
    ax.set_ylabel("Cumulative share")
    for cutoff, ypos in [(25, 0.42), (50, 0.27)]:
        proportion = float((lengths < cutoff).mean())
        ax.axvline(cutoff, color=GREY, linewidth=0.8, linestyle="--")
        ax.text(
            110,
            ypos,
            f"{int((lengths < cutoff).sum()):,} ({100 * proportion:.1f}%) have <{cutoff} characters",
        )
    save(
        fig,
        "03_comment_lengths",
        f"{int((lengths == 0).sum()):,} empty cleaned comments are included. Raw-text median: {df.raw_text.str.len().median():g} characters.\nRaw text: {int((df.raw_text.str.len() < 25).sum()):,} below 25 characters and {int((df.raw_text.str.len() < 50).sum()):,} below 50.",
    )

    grouped = df.groupby("song_title")
    stats = grouped.text_length.quantile([0.25, 0.5, 0.75, 0.9]).unstack()
    stats["n"] = grouped.size()
    stats = stats.sort_values(0.5)
    fig, ax = canvas(
        "Short comments dominate, but song distributions differ",
        "Dot: median · thick segment: middle 50% · thin segment: 25th–90th percentile.",
        height=7.5,
        left=0.24,
    )
    fig.subplots_adjust(right=0.77)
    for y, (_, row) in enumerate(stats.iterrows()):
        ax.plot([row[0.25], row[0.9]], [y, y], color=BLUE, alpha=0.5)
        ax.plot([row[0.25], row[0.75]], [y, y], color=BLUE, linewidth=7, alpha=0.3)
        ax.scatter(row[0.5], y, color=BLUE, s=25)
        ax.text(
            1.035,
            y,
            f"{row[0.5]:g}   |   n={int(row['n']):,}",
            transform=ax.get_yaxis_transform(),
            va="center",
            fontsize=9,
        )
    ax.set_yticks(range(len(stats)), stats.index)
    ax.set_xlim(0, 150)
    ax.set_xlabel("Cleaned length · characters")
    save(
        fig,
        "04_lengths_by_song",
        f"The right-hand column gives median and sample size. Medians range from {stats[0.5].min():g} to {stats[0.5].max():g} characters.\nNo equality-of-distributions test was performed; the data do not justify calling the shapes identical.",
    )

    languages = df.language.value_counts()
    top = languages.head(10)
    language_counts = pd.concat(
        [
            top,
            pd.Series(
                {f"Other ({len(languages) - 10} codes)": int(languages.iloc[10:].sum())}
            ),
        ]
    )
    fig, ax = canvas(
        "Language codes are detector outputs, not verified identities",
        "Language assignments from a seeded run; short strings can be unreliable.",
        height=7,
        left=0.20,
    )
    names = {
        "en": "English (en)",
        "es": "Spanish (es)",
        "unknown": "Unknown",
        "nl": "Dutch (nl)",
        "pt": "Portuguese (pt)",
        "so": "Somali (so)",
        "id": "Indonesian (id)",
        "tr": "Turkish (tr)",
        "de": "German (de)",
        "it": "Italian (it)",
    }
    y = np.arange(len(language_counts))[::-1]
    ax.barh(
        y,
        language_counts,
        color=[GREY if name == "unknown" else BLUE for name in language_counts.index],
        height=0.64,
    )
    ax.set_yticks(y, [names.get(name, name) for name in language_counts.index])
    for yy, value in zip(y, language_counts):
        ax.text(value + 400, yy, f"{value:,}  ·  {100 * value / N:.1f}%", va="center")
    ax.set_xlim(0, 38000)
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
    ax.set_xlabel("Comments")
    save(
        fig,
        "05_detected_languages",
        "Short strings are especially ambiguous; none of these languages has an independently measured accuracy here.\nUnknown includes 14,464 comments with fewer than three letters, plus 259 other detection failures.",
    )

    song_counts = grouped.size()
    any_counts = hits.groupby(df.song_title).sum()
    other_counts = df[RULES[:5]].any(axis=1).groupby(df.song_title).sum()
    rates = pd.DataFrame({"n": song_counts, "any": any_counts, "other": other_counts})
    rates["per_1000"] = rates["any"] / rates.n * 1000
    rates = rates.sort_values("per_1000")
    fig, ax = canvas(
        "Match rates vary with song and category",
        "Orange: any label · blue: any of the five labels other than formal resistance.",
        height=7.5,
        left=0.24,
    )
    for y, (_, row) in enumerate(rates.iterrows()):
        ax.scatter(row.per_1000, y + 0.12, color=ORANGE, s=34)
        ax.scatter(row.other / row.n * 1000, y - 0.12, color=BLUE, marker="D", s=24)
        ax.text(30, y, f"{int(row['any']):,} / {int(row.n):,}", va="center", fontsize=9)
    ax.set_yticks(range(len(rates)), rates.index)
    ax.set_xlim(-0.5, 38)
    ax.set_xlabel(
        "Matches per 1,000 comments · right-hand column: any-label count / sample size"
    )
    save(
        fig,
        "06_match_rates_by_song",
        "Descriptive corpus rates, not population estimates. Popularity sorting, replies and language coverage affect comparisons.\nNo sampling interval is shown: this is not a random sample, and comments within threads are dependent.",
    )

    fig, ax = canvas(
        "Reported “confidence” comes from assigned rule weights",
        "Each circle is a configured weight used by matching comments; circle area is proportional to count.",
        left=0.29,
    )
    taxonomy = load_yaml(Path(__file__).parent / "nlp_pipeline/labels.yaml")["labels"]
    minimums = [taxonomy[label]["min_confidence"] for label in LABELS]
    weights = []
    for y, (label, minimum) in enumerate(zip(LABELS[::-1], minimums[::-1])):
        conf = df.loc[df["rule_" + label], "rule_" + label + "_conf"]
        frequencies = conf.value_counts()
        ax.scatter(
            frequencies.index,
            np.full(len(frequencies), y),
            s=frequencies.values * 12,
            alpha=0.65,
            color=ORANGE if label == "FORMAL_RESISTANCE" else BLUE,
        )
        ax.plot(
            [minimum, minimum],
            [y - 0.35, y + 0.35],
            color=INK,
            linestyle=":",
            linewidth=1,
        )
        weights.append(
            {
                "label": label,
                "n": len(conf),
                "mean_weight": float(conf.mean()),
                "max_weight": float(conf.max()),
                "below_configured_minimum": int((conf < minimum).sum()),
            }
        )
    ax.set_yticks(range(6), NAMES[::-1])
    ax.set_xlim(0.35, 0.93)
    ax.set_xlabel("Maximum matching rule weight per comment")
    save(
        fig,
        "07_rule_weights",
        "Dotted ticks: minimums declared in labels.yaml but not enforced in RuleMiner. They do not filter these results.\nThese weights are not calibrated probabilities; averages cannot establish precision or compare label reliability.",
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 6.5))
    fig.subplots_adjust(left=0.19, right=0.94, top=0.73, bottom=0.24, wspace=0.65)
    fig.text(
        0.035,
        0.955,
        "Show matched phrases rather than repeated tokens",
        fontsize=19,
        weight="bold",
    )
    fig.text(
        0.035,
        0.88,
        "Top eight exact matched phrases after lowercasing and whitespace normalization; each comment counts once per phrase.",
        fontsize=10,
    )
    trigger_rows = []
    for ax, label, name, color in zip(
        axes, [LABELS[0], LABELS[-1]], [NAMES[0], NAMES[-1]], [BLUE, ORANGE]
    ):
        counts = Counter()
        for spans in df.loc[df["rule_" + label], "rule_" + label + "_spans"]:
            phrases = {re.sub(r"\s+", " ", span[2].lower()).strip() for span in spans}
            counts.update(phrases)
        entries = counts.most_common(8)[::-1]
        ax.barh(
            [text for text, _ in entries],
            [n for _, n in entries],
            color=color,
            height=0.6,
        )
        ax.set_title(
            f"{name} · n={int(df['rule_' + label].sum())}",
            loc="left",
            fontsize=11,
            weight="bold",
        )
        ax.set_xlim(0, max(n for _, n in entries) * 1.23)
        for text, n in entries:
            ax.text(n + 0.4, text, str(n), va="center")
        ax.tick_params(length=0)
        ax.set_xlabel("Comments containing matched phrase")
        trigger_rows.extend(
            {"label": label, "phrase": text, "comments": n}
            for text, n in counts.items()
        )
    save(
        fig,
        "08_matched_phrases",
        "A comment may appear in several bars; duplicates across different comment IDs remain. Longer or variant phrases stay separate.\nThe detector selects these phrases by design. Their frequency is not independent evidence for the theory.",
    )

    fig, ax = canvas(
        f"{int((df[RULES].sum(axis=1) > 1).sum())} comments match multiple labels",
        "All three pairs include standardization. The other twelve distinct label pairs have zero matches.",
        left=0.36,
    )
    pair_names = [
        "Standardization + regressive listening",
        "Standardization + formal resistance",
        "Standardization + market logic",
    ]
    pair_labels = [LABELS[3], LABELS[5], LABELS[2]]
    pair_counts = [
        int((df[RULES[0]] & df["rule_" + label]).sum()) for label in pair_labels
    ]

    y = np.arange(3)[::-1]
    ax.barh(y, pair_counts, color=BLUE, height=0.5)
    ax.set_yticks(y, pair_names)
    ax.set_xlim(0, 2)
    ax.set_xticks([0, 1, 2])
    for yy, count in zip(y, pair_counts):
        ax.text(count + 0.04, yy, f"{count} comment", va="center")
    ax.set_xlabel("Comments matching both labels")
    save(
        fig,
        "09_label_overlap",
        "No comment has three or more labels. A heatmap diagonal would count all matches per label, including overlaps.\nSparse detector overlap does not establish that listeners reason about only one dimension at a time.",
    )
    book.close()
    pd.DataFrame(
        {
            "label": LABELS,
            "count": df[RULES].sum().to_numpy(),
            "percent_of_corpus": df[RULES].sum().to_numpy() / N * 100,
        }
    ).to_csv(output / "label_counts.csv", index=False)
    rates.to_csv(output / "song_rates.csv")
    stats.to_csv(output / "song_lengths.csv")
    languages.rename("comments").to_csv(output / "language_counts.csv")
    pd.DataFrame(weights).to_csv(output / "rule_weights.csv", index=False)
    pd.DataFrame(trigger_rows).to_csv(output / "matched_phrases.csv", index=False)
    return sorted(output.glob("*.png"))
