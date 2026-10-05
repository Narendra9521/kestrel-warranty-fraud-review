"""Checks predictions.csv against the client's sample_submission.csv / test file."""
import pandas as pd, sys
from sklearn.metrics import roc_auc_score
from features import load_frame
p = pd.read_csv('predictions.csv'); s = pd.read_csv('sample_submission.csv'); t = pd.read_csv('test_unlabelled.csv')
chk = {
 'columns are claim_id,score': list(p.columns) == ['claim_id', 'score'],
 'row count equals test rows': len(p) == len(t),
 'no duplicate claim_id': p.claim_id.is_unique,
 'no missing ids': set(p.claim_id) == set(t.claim_id),
 'same ids and order as sample_submission': (p.claim_id.values == s.claim_id.values).all(),
 'no missing scores': p.score.notna().all(),
 'scores within 0..1': p.score.between(0, 1).all(),
 'scores are not all identical': p.score.nunique() > 100}
H, _ = load_frame('.'); L = H[H.y.notna() & (H.post == 1)]
import joblib; M = joblib.load('model.pkl'); sc = M['model'].predict_proba(L[M['feats']])[:, 1]
auc = roc_auc_score(L.y, sc); chk[f'higher score = more fraud (in-sample AUC {auc:.2f} > 0.5; honest out-of-time figure is in evidence.md)'] = auc > 0.5
for k, v in chk.items(): print('PASS' if v else 'FAIL', '-', k)
sys.exit(0 if all(chk.values()) else 1)
