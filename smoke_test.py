"""Starts the real server as a separate process with NO API key and checks it. Run: python smoke_test.py"""
import json, os, subprocess, sys, time, urllib.request, urllib.error
env = {k: v for k, v in os.environ.items() if 'KEY' not in k.upper() and 'TOKEN' not in k.upper()}
srv = subprocess.Popen([sys.executable, 'app.py'], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
B = 'http://127.0.0.1:8000'
def call(path, body=None):
    req = urllib.request.Request(B + path, data=None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode()),
                                 headers={'Content-Type': 'application/json'})
    try: r = urllib.request.urlopen(req, timeout=10); return r.status, r.read().decode()
    except urllib.error.HTTPError as e: return e.code, e.read().decode()
ok = True
def check(name, cond): global ok; ok &= bool(cond); print('PASS' if cond else 'FAIL', '-', name)
try:
    for _ in range(40):
        try: urllib.request.urlopen(B + '/health', timeout=1); break
        except Exception: time.sleep(0.5)
    st, b = call('/health'); check('/health 200 {"status":"ok"}', st == 200 and json.loads(b)['status'] == 'ok')
    st, b = call('/'); check('web UI served (HTML form + calls /score)', st == 200 and '<button' in b and '/score' in b)
    risky = dict(claim_id='S1', submitted_at='2026-10-02 11:30', partner_id='SP3129', sku='KH-CF-01', days_since_purchase=131,
                 claim_amount_inr=1995, photo_attached='Y', partner_inspected='N', customer_prior_claims=2)
    st, b = call('/score', risky); j = json.loads(b)
    check('/score 200 with score in 0..1', st == 200 and 0 <= j['risk_score'] <= 1)
    check('readable reasons returned', isinstance(j['reasons'], list) and j['reasons'] and all(isinstance(x, str) and len(x) > 10 for x in j['reasons']))
    print('      ->', j['recommendation'], j['risk_score'], j['reasons'])
    safe = dict(risky, claim_id='S2', partner_id='SP3033', claim_amount_inr=8000, partner_inspected='Y', customer_prior_claims=0)
    st, b2 = call('/score', safe); check('risky claim scores higher than a large inspected claim', json.loads(b2)['risk_score'] < j['risk_score'])
    st, b = call('/score', b'not json'); check('bad JSON -> polite 400 error message', st == 400 and 'error' in json.loads(b))
    st, b = call('/score', {'claim_id': 'x'}); check('missing fields -> 400 listing them', st == 400 and 'Missing fields' in json.loads(b)['error'])
    st, b = call('/score', dict(risky, sku='BAD')); check('unknown SKU -> 422 polite error', st == 422 and 'error' in json.loads(b))
finally: srv.terminate()
print('ALL PASSED' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
