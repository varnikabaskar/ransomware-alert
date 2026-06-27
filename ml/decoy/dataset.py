import numpy as np
import pandas as pd
import re

FEATURE_COLUMNS = [
    "access_freq",
    "rename_burst",
    "entropy_jump",
    "unknown_process_touch",
]
LABEL_COLUMN = "label"


class DecoyDatasetError(ValueError):
    pass


def _safe_numeric(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip()
    if not text:
        return 0.0

    hex_match = re.search(r"0x[0-9a-fA-F]+", text)
    if hex_match:
        try:
            return float(int(hex_match.group(0), 16))
        except ValueError:
            pass

    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def _norm(series: pd.Series) -> pd.Series:
    arr = series.map(_safe_numeric).astype(np.float32)
    min_v = float(arr.min())
    max_v = float(arr.max())
    if max_v - min_v < 1e-9:
        return pd.Series(np.zeros(len(arr), dtype=np.float32), index=arr.index)
    return ((arr - min_v) / (max_v - min_v)).astype(np.float32)


def _find_col(df: pd.DataFrame, *names: str) -> str | None:
    lookup = {c.lower(): c for c in df.columns}
    for name in names:
        key = name.lower()
        if key in lookup:
            return lookup[key]
    return None


def _series_or_zero(df: pd.DataFrame, *names: str) -> pd.Series:
    col = _find_col(df, *names)
    if col is None:
        return pd.Series(np.zeros(len(df), dtype=np.float32), index=df.index)
    return df[col]


def _extract_label(df: pd.DataFrame) -> np.ndarray:
    label_col = _find_col(df, "label", "class", "category", "rg", "target", "y")
    if label_col is None:
        raise DecoyDatasetError("No label column found. Expected one of: label, Class, Category, RG, target, y")

    raw = df[label_col]
    numeric = pd.to_numeric(raw, errors="coerce")
    if numeric.notna().mean() > 0.95:
        return (numeric.fillna(0) > 0).astype(np.int32).to_numpy()

    def map_text(v: object) -> int:
        text = str(v).strip().lower()
        if text in {"0", "benign", "goodware", "good", "clean", "normal"}:
            return 0
        if text in {"1", "malware", "ransomware", "malicious", "bad"}:
            return 1
        return 0 if "benign" in text or "good" in text else 1

    return raw.map(map_text).astype(np.int32).to_numpy()


def _build_decoy_features(df: pd.DataFrame) -> np.ndarray:
    if all(col in df.columns for col in FEATURE_COLUMNS):
        return df[FEATURE_COLUMNS].apply(lambda s: s.map(_safe_numeric)).fillna(0.0).to_numpy(dtype=np.float32)

    files_mal = _series_or_zero(df, "files_malicious")
    files_sus = _series_or_zero(df, "files_suspicious")
    files_unk = _series_or_zero(df, "files_unknown")
    reg_read = _series_or_zero(df, "registry_read")
    reg_write = _series_or_zero(df, "registry_write")
    reg_delete = _series_or_zero(df, "registry_delete")
    proc_mal = _series_or_zero(df, "processes_malicious")
    proc_sus = _series_or_zero(df, "processes_suspicious")
    apis = _series_or_zero(df, "apis")
    dlls = _series_or_zero(df, "dlls_calls")
    net_threat = _series_or_zero(df, "network_threats")

    signal_presence = (
        (_find_col(df, "files_malicious") is not None)
        + (_find_col(df, "registry_read") is not None)
        + (_find_col(df, "processes_suspicious") is not None)
    )

    if signal_presence >= 2:
        features_df = pd.DataFrame(
            {
                "access_freq": _norm(files_sus + files_unk + reg_read + reg_write),
                "rename_burst": _norm(files_mal + reg_delete + proc_sus),
                "entropy_jump": _norm(net_threat + (apis * 0.01) + (dlls * 0.01)),
                "unknown_process_touch": _norm(proc_mal + proc_sus),
            }
        )
        return features_df[FEATURE_COLUMNS].to_numpy(dtype=np.float32)

    numeric_df = df.apply(lambda s: s.map(_safe_numeric))
    candidate_names = [
        "AddressOfEntryPoint",
        "SizeOfCode",
        "IMPORT_Size",
        "NumberOfSections",
        "CheckSum",
        "Subsystem",
    ]

    selected: list[pd.Series] = []
    for name in candidate_names:
        col = _find_col(numeric_df, name)
        if col is not None:
            selected.append(_norm(numeric_df[col]))
        if len(selected) == len(FEATURE_COLUMNS):
            break

    if len(selected) < len(FEATURE_COLUMNS):
        for col in numeric_df.columns:
            if len(selected) == len(FEATURE_COLUMNS):
                break
            selected.append(_norm(numeric_df[col]))

    if len(selected) < len(FEATURE_COLUMNS):
        raise DecoyDatasetError("Unable to construct decoy feature set from dataset")

    features_df = pd.concat(selected[: len(FEATURE_COLUMNS)], axis=1)
    features_df.columns = FEATURE_COLUMNS
    return features_df.to_numpy(dtype=np.float32)


def load_decoy_csv(csv_path: str) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(csv_path)
    x = _build_decoy_features(df)
    y = _extract_label(df)
    return x, y
