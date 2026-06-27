import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score

from ml.behavioral.dataset import load_behavioral_csv, build_sliding_windows
from ml.behavioral.feature_extractor import summarize_sequence_stats
from ml.behavioral.uncertainty_dbn import UADESBehavioralModel
from ml.decoy.dataset import load_decoy_csv
from ml.decoy.random_forest_trap import DecoyRFModel


def eval_binary(y_true, probs, threshold=0.5):
    pred = (probs >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()
    acc = accuracy_score(y_true, pred)
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    return acc, fpr


def main():
    xb, yb = load_behavioral_csv(r"C:/Users/Shabutha/OneDrive/Desktop/journal papers/combined_without_3gram.csv")
    wb, lb = build_sliding_windows(xb, yb, sequence_length=20)
    xtr, xte, ytr, yte = train_test_split(wb, lb, test_size=0.2, random_state=42, stratify=lb)
    ftr, fte = summarize_sequence_stats(xtr), summarize_sequence_stats(xte)

    mb = UADESBehavioralModel()
    mb.fit(ftr, ytr, sequence_length=20)
    probb = mb.predict_proba_from_vectors(fte)
    acc_b, fpr_b = eval_binary(yte, probb)

    xd, yd = load_decoy_csv(r"C:/Users/Shabutha/OneDrive/Desktop/journal papers/Final_Dataset_without_duplicate.csv")
    xtr, xte, ytr, yte = train_test_split(xd, yd, test_size=0.2, random_state=42, stratify=yd)

    md = DecoyRFModel()
    md.fit(xtr, ytr)
    probd = md.predict_proba(xte)[:, 1]
    acc_d, fpr_d = eval_binary(yte, probd)

    print(f"BEH_ACC={acc_b:.6f} BEH_FPR={fpr_b:.6f}")
    print(f"DEC_ACC={acc_d:.6f} DEC_FPR={fpr_d:.6f}")


if __name__ == "__main__":
    main()
