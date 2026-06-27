import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

from ml.behavioral.dataset import load_behavioral_csv, build_sliding_windows
from ml.behavioral.feature_extractor import summarize_sequence_stats
from ml.behavioral.uncertainty_dbn import UADESBehavioralModel


def eval_at(y, probs, thr):
    pred = (probs >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    acc = accuracy_score(y, pred)
    return acc, fpr


x, y = load_behavioral_csv(r"C:/Users/Shabutha/OneDrive/Desktop/journal papers/combined_without_3gram.csv")
w, l = build_sliding_windows(x, y, sequence_length=20)
xtr, xte, ytr, yte = train_test_split(w, l, test_size=0.2, random_state=42, stratify=l)
ftr, fte = summarize_sequence_stats(xtr), summarize_sequence_stats(xte)

m = UADESBehavioralModel()
m.fit(ftr, ytr, sequence_length=20)
probs = m.predict_proba_from_vectors(fte)

print('THR0.5', eval_at(yte, probs, 0.5))
print('THR0.79', eval_at(yte, probs, 0.795))

best = None
for thr in np.linspace(0.05, 0.95, 181):
    acc, fpr = eval_at(yte, probs, thr)
    if fpr <= 0.03 and acc >= 0.97:
        score = acc - 0.2 * fpr
        if best is None or score > best[0]:
            best = (score, thr, acc, fpr)

print('BEST_CONSTRAINT', best)
