"""Authenticated GPU/API smoke test. No domain-accuracy claim is made."""
import argparse
import json
import math
import os
import statistics
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:18008')
parser.add_argument('--output', default='smoke-results.json')
args = parser.parse_args()
key = os.environ.get('KEV_API_KEY', '')
headers = {'Content-Type': 'application/json'}
if key:
    headers['Authorization'] = f'Bearer {key}'

def request(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(args.url.rstrip('/') + path, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)

if key:
    try:
        urllib.request.urlopen(args.url.rstrip('/') + '/v1/models', timeout=10)
    except urllib.error.HTTPError as exc:
        assert exc.code == 401, f'Expected 401, received {exc.code}'
    else:
        raise AssertionError('Unauthenticated request was accepted')
models = request('/v1/models')
assert 'cuda' in json.dumps(models).lower(), 'Server did not report a CUDA device'
payload = {
    'model': 'kev-latest',
    'state': 'A customer says: My card was charged twice for one order. Please refund the duplicate charge.',
    'questions': {
        'department': {'type': 'choice', 'instructions': 'Which department should handle this?',
                       'criteria': {'billing': 'Duplicate charges, payment problems and invoices',
                                    'shipping': 'Delivery tracking and missing parcels'}},
        'duplicate': {'type': 'noul', 'instructions': 'Does the customer report a duplicate charge?'},
        'urgency': {'type': 'score', 'instructions': 'How urgent is this request?',
                    'criteria': ['Routine', 'Urgent', 'Emergency']},
    },
}
latencies = []
results = []
for _ in range(6):
    started = time.perf_counter()
    result = request('/v1/systemone', payload)
    latencies.append(round((time.perf_counter()-started)*1000, 2))
    answers = result['answers']
    probabilities = answers['department']['probabilities']
    assert set(probabilities) == {'billing', 'shipping'}
    assert all(math.isfinite(v) and 0 <= v <= 1 for v in probabilities.values())
    assert abs(sum(probabilities.values())-1) < 0.01
    assert answers['department']['choice'] in probabilities
    assert 0 <= answers['duplicate']['noul'] <= 1
    assert math.isfinite(answers['urgency']['score']) and 0 <= answers['urgency']['score'] <= 2
    results.append(result)
request('/v1/systemone/separate', payload)
choice_payload = dict(payload, questions={'department': payload['questions']['department']})
request('/v1/systemone/permute', {'request': choice_payload, 'question': 'department', 'n_perm': 2, 'seed': 0})
report = {'models': models, 'first_request_ms': latencies[0],
          'warm_median_ms': statistics.median(latencies[1:]),
          'request_latencies_ms': latencies, 'results': results,
          'models_after': request('/v1/models'),
          'scope': 'Synthetic smoke test; not a calibrated domain benchmark'}
with open(args.output, 'w', encoding='utf-8') as handle:
    json.dump(report, handle, indent=2)
print(json.dumps({'first_request_ms': report['first_request_ms'],
                  'warm_median_ms': report['warm_median_ms'],
                  'department': results[-1]['answers']['department']['choice'],
                  'output': args.output}))
