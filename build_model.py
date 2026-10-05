"""Train the final model on ALL labelled claims, write predictions.csv, model.pkl, partner_stats.json."""
import os, json, joblib, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from features import FEATS, LAG, load_frame
F2 = FEATS + ['post']; W = 10
H, test_ids = load_frame('.')
L = H[H.y.notna()]
m = make_pipeline(StandardScaler(), LogisticRegression(C=0.3, max_iter=3000))
m.fit(L[F2], L.y, logisticregression__sample_weight=np.where(L.post == 1, W, 1.0))
T = H[H.claim_id.isin(test_ids)].copy(); T['score'] = m.predict_proba(T[F2])[:, 1]
order = pd.read_csv('sample_submission.csv').claim_id if os.path.exists('sample_submission.csv') else pd.Series(test_ids)
out = pd.DataFrame({'claim_id': order}).merge(T[['claim_id', 'score']], on='claim_id', how='left')
assert len(out) == len(test_ids) == out.claim_id.nunique() and out.score.notna().all() and out.score.between(0, 1).all()
out.to_csv('predictions.csv', index=False)
joblib.dump({'model': m, 'feats': F2, 'baseline': L[L.post == 1][F2].median().to_dict()}, 'model.pkl')
end = H.t.max(); ps = {}                      # partner stats for live scoring, same 30-day label lag as training
for pid, g in H.groupby('partner_id'):
    lg = g[(g.y.notna()) & (g.t <= end - LAG)]; v = g[g.t > end - LAG]
    ps[pid] = {'n': int(len(lg)), 'f': int(lg.y.sum()), 'vol30': int(len(v)), 'small30': float(v.small_uninsp.mean()) if len(v) else 0.0}
json.dump(ps, open('partner_stats.json', 'w'))
print('trained on', len(L), 'labelled claims;', len(out), 'predictions written')
