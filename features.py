import numpy as np, pandas as pd
PROD = pd.read_csv('products.csv') if __import__('os').path.exists('products.csv') else None
LAG = pd.Timedelta(days=30)      # label lag: an outcome is only known 30 days after the claim
VOLWIN = pd.Timedelta(days=30)   # window for partner volume features (claims only, no labels)
FEATS = ['log_amt','amt_ratio','days_ratio','prior','photo','inspected','small_uninsp','p_age','p_type',
         'p_hist_n','p_hist_f','p_hist_rate','p_vol30','p_small_share30','cust_hi']

def prep(df, partners, products):
    d = df.copy()
    d['t'] = pd.to_datetime(d.submitted_at)
    d = d.merge(partners, on='partner_id', how='left').merge(products, on='sku', how='left')
    d['log_amt'] = np.log1p(d.claim_amount_inr)
    d['amt_ratio'] = d.claim_amount_inr / d.list_price_inr
    d['days_ratio'] = d.days_since_purchase / (d.warranty_months * 30)
    d['prior'] = d.customer_prior_claims
    d['cust_hi'] = (d.prior >= 2).astype(int)
    d['photo'] = (d.photo_attached == 'Y').astype(int)
    d['inspected'] = (d.partner_inspected == 'Y').astype(int)
    d['small_uninsp'] = ((d.claim_amount_inr < 2000) & (d.inspected == 0)).astype(int)
    d['p_age'] = (d.t - pd.to_datetime(d.onboarded_date)).dt.days
    d['p_type'] = d.partner_type.map({'authorised_service_centre': 0, 'franchise': 1, 'freelance_technician': 2}).fillna(-1)
    return d

def add_history(d, labelled, volume_pool, lag=LAG, cap=None):
    """Causal partner features. labelled: deduped rows with is_fraud known (history, used with 30-day lag).
    volume_pool: all claims (labels not needed) for 30-day volume.
    A label is usable for claim t only if its claim was submitted <= t - lag AND (if cap is given) <= cap,
    where cap is the model's training cutoff. Nothing newer is ever read."""
    lab = labelled[['partner_id', 't', 'is_fraud']].sort_values('t')
    vol = volume_pool[['partner_id', 't', 'small_uninsp']].sort_values('t')
    L = {k: (g.t.values, np.cumsum(g.is_fraud.values)) for k, g in lab.groupby('partner_id')}
    V = {k: (g.t.values, np.cumsum(g.small_uninsp.values)) for k, g in vol.groupby('partner_id')}
    n, f, v, ss = [], [], [], []
    for pid, t in zip(d.partner_id, d.t):
        tl, cf = L.get(pid, (np.array([], dtype='datetime64[ns]'), np.array([])))
        lim = t - lag if cap is None else min(t - lag, cap)
        i = np.searchsorted(tl, np.datetime64(lim), side='right')
        n.append(i); f.append(cf[i - 1] if i else 0)
        tv, cs = V.get(pid, (np.array([], dtype='datetime64[ns]'), np.array([])))
        hi = np.searchsorted(tv, np.datetime64(t), side='left')
        lo = np.searchsorted(tv, np.datetime64(t - VOLWIN), side='left')
        cnt = hi - lo
        v.append(cnt)
        sm = (cs[hi - 1] - (cs[lo - 1] if lo else 0)) if hi > lo else 0
        ss.append(sm / cnt if cnt else 0)
    d = d.copy()
    d['p_hist_n'], d['p_hist_f'] = n, f
    d['p_hist_rate'] = (d.p_hist_f + 0.2) / (d.p_hist_n + 20)   # smoothed toward ~1%
    d['p_vol30'], d['p_small_share30'] = v, ss
    return d


def load_base(data_dir='.'):
    """Claims with row-level features but WITHOUT partner history. Returns (A, labelled, test_ids).
    - Re-submitted claim_ids: keep the FIRST submission (what would have been scored at the time).
    - Blank is_fraud (still under investigation) stays NaN and is never used as a label."""
    import os
    j = lambda f: os.path.join(data_dir, f)
    tr = pd.read_csv(j('train.csv')).sort_values('submitted_at').drop_duplicates('claim_id', keep='first')
    te = pd.read_csv(j('test_unlabelled.csv'))
    P, PR = pd.read_csv(j('partners.csv')), pd.read_csv(j('products.csv'))
    A = prep(pd.concat([tr, te]).drop_duplicates('claim_id'), P, PR).sort_values('t').reset_index(drop=True)
    A['y'] = A.claim_id.map(tr.set_index('claim_id').is_fraud)
    A['post'] = (A.t >= '2026-05-01').astype(int)
    lab = A[A.y.notna()][['partner_id', 't', 'y']].rename(columns={'y': 'is_fraud'})
    return A, lab, te.claim_id.tolist()


def load_frame(data_dir='.'):
    """Used by the FINAL model (build_model.py): history features use every label at least 30 days older than each claim."""
    A, lab, test_ids = load_base(data_dir)
    H = add_history(A, lab, A)
    H['y'] = A.y.values
    return H, test_ids
