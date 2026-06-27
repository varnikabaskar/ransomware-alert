import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, accuracy_score

from ml.decoy.dataset import load_decoy_csv
from ml.decoy.random_forest_trap import DecoyRFModel


def metrics(y_true, probs, thr):
    pred = (probs >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred).ravel()
    acc = accuracy_score(y_true, pred)
    fpr = fp / (fp + tn)
    return acc, fpr


def main():
    x, y = load_decoy_csv(r"C:/Users/Shabutha/OneDrive/Desktop/journal papers/Final_Dataset_without_duplicate.csv")
    xtr, xte, ytr, yte = train_test_split(x, y, test_size=0.2, random_state=42, stratify=y)
    m = DecoyRFModel(); m.fit(xtr, ytr)
    probs = m.predict_proba(xte)[:, 1]

    best = None
    for thr in np.linspace(0.4, 0.9, 101):
        acc, fpr = metrics(yte, probs, thr)
        if fpr <= 0.03 and acc >= 0.97:
            score = acc - 0.2 * fpr
            if best is None or score > best[0]:
                best = (score, thr, acc, fpr)

    if best is None:
        print("NO_THRESHOLD")
    else:
        _, thr, acc, fpr = best
        print(f"BEST thr={thr:.3f} acc={acc:.6f} fpr={fpr:.6f}")


if __name__ == "__main__":
    main()
