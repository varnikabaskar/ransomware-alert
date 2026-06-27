from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BEHAVIORAL = PROJECT_ROOT / "data" / "behavioral" / "epoch_fpr_metrics.csv"
DEFAULT_DECOY = PROJECT_ROOT / "data" / "decoy" / "family_stop_loss_metrics.csv"
DEFAULT_RUNTIME = PROJECT_ROOT / "data" / "decoy" / "decoy_watch_runtime_metrics.csv"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "docs" / "graphs"


def _load_or_sample_behavioral(path: Path) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(
            {
                "epoch": [5, 10, 20, 30, 40, 50, 60],
                "false_positive_rate": [0.082, 0.061, 0.046, 0.036, 0.030, 0.026, 0.024],
            }
        )

    required = {"epoch", "false_positive_rate"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Behavioral CSV is missing required columns: {sorted(missing)}")

    return df


def _load_or_sample_decoy(path: Path) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(
            {
                "family": ["LockBit", "Phobos", "Ryuk", "WannaCry", "REvil", "Maze"],
                "stopping_time_sec": [8.4, 10.1, 7.2, 11.3, 9.0, 6.7],
                "avg_file_loss": [3.1, 4.0, 2.6, 4.5, 3.4, 2.2],
            }
        )

    required = {"family", "stopping_time_sec", "avg_file_loss"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Decoy CSV is missing required columns: {sorted(missing)}")

    return df.sort_values("stopping_time_sec").reset_index(drop=True)


def _load_or_sample_runtime(path: Path) -> pd.DataFrame:
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(
            {
                "minute": [1, 2, 3, 4, 5, 6, 7, 8],
                "watch_latency_ms": [120, 110, 134, 140, 126, 118, 112, 108],
                "events_processed": [40, 48, 53, 60, 58, 62, 69, 73],
            }
        )

    required = {"minute", "watch_latency_ms", "events_processed"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Runtime CSV is missing required columns: {sorted(missing)}")

    return df


def plot_behavioral_epoch_vs_fpr(df: pd.DataFrame, output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["false_positive_rate"], df["epoch"], marker="o", linewidth=2, color="#1f77b4")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("Number of Epochs")
    ax.set_title("Behavioral Analysis: Epochs vs False Positive Rate")
    ax.grid(alpha=0.3)

    out_path = output_dir / "behavioral_epochs_vs_false_positive_rate.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def plot_decoy_family_stop_time_vs_file_loss(df: pd.DataFrame, output_dir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(
        df["stopping_time_sec"],
        df["avg_file_loss"],
        s=130,
        c=range(len(df)),
        cmap="viridis",
        alpha=0.85,
        edgecolors="black",
        linewidths=0.6,
    )

    for _, row in df.iterrows():
        ax.annotate(
            row["family"],
            (row["stopping_time_sec"], row["avg_file_loss"]),
            textcoords="offset points",
            xytext=(5, 5),
            fontsize=9,
        )

    ax.set_xlabel("Ransomware Families in terms of Stopping Time (seconds)")
    ax.set_ylabel("Average File Loss After Detection")
    ax.set_title("Decoy Files: File Loss vs Family Stopping Time")
    ax.grid(alpha=0.3)

    cbar = fig.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label("Family Index")

    out_path = output_dir / "decoy_family_stopping_time_vs_file_loss.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def plot_runtime_decoy_watch(df: pd.DataFrame, output_dir: Path) -> Path:
    fig, ax1 = plt.subplots(figsize=(10, 5))

    ax1.plot(df["minute"], df["watch_latency_ms"], marker="o", color="#d62728", linewidth=2)
    ax1.set_xlabel("Runtime (minute)")
    ax1.set_ylabel("Decoy Watch Latency (ms)", color="#d62728")
    ax1.tick_params(axis="y", labelcolor="#d62728")
    ax1.grid(alpha=0.25)

    ax2 = ax1.twinx()
    ax2.bar(df["minute"], df["events_processed"], alpha=0.25, color="#2ca02c", width=0.5)
    ax2.set_ylabel("Events Processed", color="#2ca02c")
    ax2.tick_params(axis="y", labelcolor="#2ca02c")

    plt.title("Runtime Analysis of Decoy Watch File")

    out_path = output_dir / "runtime_analysis_decoy_watch.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate ransomware detection project graphs")
    parser.add_argument("--behavioral-csv", type=Path, default=DEFAULT_BEHAVIORAL)
    parser.add_argument("--decoy-csv", type=Path, default=DEFAULT_DECOY)
    parser.add_argument("--runtime-csv", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    behavioral_df = _load_or_sample_behavioral(args.behavioral_csv)
    decoy_df = _load_or_sample_decoy(args.decoy_csv)
    runtime_df = _load_or_sample_runtime(args.runtime_csv)

    out1 = plot_behavioral_epoch_vs_fpr(behavioral_df, output_dir)
    out2 = plot_decoy_family_stop_time_vs_file_loss(decoy_df, output_dir)
    out3 = plot_runtime_decoy_watch(runtime_df, output_dir)

    print("Generated graph files:")
    print(out1)
    print(out2)
    print(out3)


if __name__ == "__main__":
    main()
