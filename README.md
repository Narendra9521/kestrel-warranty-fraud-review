# Kestrel Home - warranty claim risk scorer

Ranks warranty claims by fraud risk so the investigation desk (max 40 claims/month) checks the riskiest first.
100% local and free: scikit-learn logistic regression + a small Flask app. **No API key, no paid service, no internet at run time.**

## What you need
- Python 3.10 or newer (tested on 3.12), any OS.
- The client data files, which are NOT in this repo (policy s10 forbids publishing them). Copy these five files into
  this folder, unchanged: `train.csv`, `test_unlabelled.csv`, `partners.csv`, `products.csv`, `sample_submission.csv`.

## Setup and run (clean machine)
```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt      # only step that needs internet

python build_model.py                # trains, writes predictions.csv, model.pkl, partner_stats.json (~10 s)
python verify_predictions.py         # checks predictions.csv (ids, range, no gaps)
python app.py                        # starts the service; open http://localhost:8000
```
In a second terminal (optional): `python smoke_test.py` starts its own server copy and tests /health, /score, reasons, the UI and bad input.
Reproduce the evidence: `python evaluate.py` (rewrites `evidence.md`, a few minutes).

## Using the service
- Screen: http://localhost:8000 - fill the form, press **Check claim**. Shows REVIEW / watch / normal, the score and the reasons.
- API: `POST /score` with JSON fields `claim_id, submitted_at, partner_id, sku, days_since_purchase, claim_amount_inr,
  photo_attached (Y/N), partner_inspected (Y/N), customer_prior_claims`. Returns `risk_score, recommendation, reasons`.
  Optional: `partner_claims_last_30d`, `partner_small_share_30d`. Bad input returns a plain-English JSON error (400/422), never a crash.
- `GET /health` returns `{"status":"ok"}`.
- Score is for **ranking**, not a probability. REVIEW = score >= 0.10, watch = 0.03-0.10.

## Files
| file | purpose |
|---|---|
| `features.py` | feature building, causal partner-history features, shared data loader |
| `build_model.py` | final training + `predictions.csv` |
| `evaluate.py` | chronological walk-forward evaluation -> `evidence.md` |
| `verify_predictions.py`, `smoke_test.py` | submission checks and service checks |
| `app.py`, `index.html` | endpoint and screen |
| `memo.md` | memo to Ritu, form draft |

## Data handling
Client CSVs, the trained model and partner statistics are git-ignored on purpose. Do not commit or upload them anywhere public.

## Known limits
See section 6 of `evidence.md`. In short: only 36 fraud cases since the May-2026 policy change, so treat the model as a ranking aid.
