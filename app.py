"""Kestrel claim-risk service. Run: python app.py  -> http://localhost:8000 . No API key, no network."""
import json, joblib, pandas as pd, numpy as np
from flask import Flask, request, jsonify, Response
from features import prep, FEATS
APP = Flask(__name__)
M = joblib.load('model.pkl'); MODEL, F2, BASE = M['model'], M['feats'], M['baseline']
P = pd.read_csv('partners.csv'); PR = pd.read_csv('products.csv'); PS = json.load(open('partner_stats.json'))
REQ = ['claim_id','submitted_at','partner_id','sku','days_since_purchase','claim_amount_inr','photo_attached','partner_inspected','customer_prior_claims']
WORDS = {  # feature -> sentence used when it pushes risk up
 'small_uninsp': 'Small claim (under Rs 2,000) paid without inspection - the group where fraud rose after May 2026',
 'p_hist_rate': 'This partner has had confirmed fraud cases before',
 'p_hist_f': 'This partner has had confirmed fraud cases before',
 'p_age': 'Partner is recently onboarded',
 'p_vol30': 'Partner has submitted unusually many claims in the last 30 days',
 'p_small_share30': 'Most of this partner\'s recent claims are small and uninspected',
 'prior': 'Customer has several earlier warranty claims', 'cust_hi': 'Customer has several earlier warranty claims',
 'log_amt': 'Claim amount is unusual for this kind of claim', 'amt_ratio': 'Claim amount is high compared with the product price',
 'days_ratio': 'Claim timing within the warranty period is unusual', 'photo': 'No photo attached', 'inspected': 'Not inspected',
 'p_type': 'Partner type has a higher past fraud rate', 'p_hist_n': 'Partner has little claim history', 'post': 'Claim falls in the post-May-2026 period'}
def features(r):
    d = pd.DataFrame([{k: r.get(k) for k in REQ + ['product_serial','claim_description','inspector_note']}])
    d['claim_amount_inr'] = d.claim_amount_inr.astype(float); d['days_since_purchase'] = d.days_since_purchase.astype(float)
    d['customer_prior_claims'] = d.customer_prior_claims.astype(int)
    d = prep(d, P, PR)
    if d.list_price_inr.isna().any() or d.p_age.isna().any(): raise ValueError('unknown partner_id or sku')
    s = PS.get(r['partner_id'], {'n': 0, 'f': 0, 'vol30': 0, 'small30': 0.0})
    d['p_hist_n'], d['p_hist_f'] = s['n'], s['f']; d['p_hist_rate'] = (s['f'] + .2) / (s['n'] + 20)
    d['p_vol30'] = float(r.get('partner_claims_last_30d', s['vol30'])); d['p_small_share30'] = float(r.get('partner_small_share_30d', s['small30'])); d['post'] = int(d.t.iloc[0] >= pd.Timestamp('2026-05-01'))
    return d[F2]
def score(r):
    X = features(r); p = float(MODEL.predict_proba(X)[:, 1][0]); reasons = []
    for f in F2:                       # occlusion: how much does the score drop if this feature were "typical"?
        Xb = X.copy(); Xb[f] = BASE[f]; drop = p - float(MODEL.predict_proba(Xb)[:, 1][0])
        if drop > 0.01: reasons.append((drop, WORDS.get(f, f)))
    amt = float(r['claim_amount_inr'])
    if 1900 <= amt < 2000 and r['partner_inspected'] != 'Y': reasons.append((1.0, 'Amount sits just under the Rs 2,000 no-inspection limit'))
    seen, out = set(), []
    for _, w in sorted(reasons, reverse=True):
        if w not in seen: seen.add(w); out.append(w)
    level = 'REVIEW' if p >= 0.10 else 'watch' if p >= 0.03 else 'normal'
    return {'claim_id': r['claim_id'], 'risk_score': round(p, 4), 'recommendation': level,
            'reasons': out[:4] or ['No unusual signals'],
            'note': 'Score is for ranking, not a probability. Send the highest-scoring claims to the investigation desk (capacity 40/month).'}
@APP.post('/score')
def ep():
    r = request.get_json(silent=True)
    if not isinstance(r, dict): return jsonify(error='Send a JSON object'), 400
    miss = [k for k in REQ if r.get(k) in (None, '')]
    if miss: return jsonify(error='Missing fields: ' + ', '.join(miss)), 400
    try: return jsonify(score(r))
    except Exception as e: return jsonify(error=f'Could not score this claim: {e}'), 422
@APP.get('/health')
def health(): return jsonify(status='ok')
@APP.get('/')
def home(): return Response(open('index.html', encoding='utf-8').read(), mimetype='text/html')
if __name__ == '__main__': APP.run(host='0.0.0.0', port=8000)
