"""Evaluate labelled Kev decisions. Threshold tables are descriptive, not selected policies."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import time
import urllib.request


def load_cases(path):
    raw = Path(path).read_bytes()
    cases = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
    if not cases:
        raise ValueError('Dataset must contain at least one case')
    ids = set()
    for case in cases:
        if not isinstance(case.get('id'), str) or case['id'] in ids:
            raise ValueError('Every case needs a unique string id')
        ids.add(case['id'])
        if case.get('split') not in ('dev', 'test'):
            raise ValueError('Every case needs split dev or test')
        if 'state' not in case or not case.get('questions') or set(case['questions']) != set(case.get('expected', {})):
            raise ValueError('Provide state, questions, and matching expected keys')
        for key, question in case['questions'].items():
            target = case['expected'][key]
            kind = question.get('type')
            criteria = question.get('criteria')
            if kind == 'choice':
                if not isinstance(criteria, dict) or not criteria or target not in criteria:
                    raise ValueError('Choice target must name a criterion')
            elif kind == 'noul':
                if not isinstance(target, bool):
                    raise ValueError('Noul target must be a boolean')
            elif kind == 'score':
                if not isinstance(criteria, list) or not criteria or type(target) is not int or not 0 <= target < len(criteria):
                    raise ValueError('Score target must be an integer criterion index')
            else:
                raise ValueError('Unsupported question type')
    return cases, hashlib.sha256(raw).hexdigest()


def measure(question, target, answer):
    kind = question['type']
    if answer.get('type') != kind:
        raise ValueError('Unexpected answer type')
    if kind == 'noul':
        p = answer['noul']
        labels, values, target_label = ['false', 'true'], [1-p, p], str(target).lower()
    else:
        labels = list(question['criteria']) if kind == 'choice' else [str(i) for i in range(len(question['criteria']))]
        dist = answer['probabilities']
        if set(dist) != set(labels):
            raise ValueError('Answer probability keys do not match question')
        values, target_label = [dist[label] for label in labels], str(target)
    if not all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in values) or abs(sum(values)-1) > .02:
        raise ValueError('Invalid probability distribution')
    predicted = labels[max(range(len(values)), key=lambda i: values[i])]
    if kind == 'choice' and answer['choice'] != predicted:
        raise ValueError('Choice disagrees with probabilities')
    row = {'type': kind, 'target': target_label, 'prediction': predicted,
           'correct': predicted == target_label, 'top_probability': max(values),
           'brier': sum((v-(label == target_label))**2 for label, v in zip(labels, values))}
    if kind == 'score':
        score = answer['score']
        if not math.isfinite(score) or not 0 <= score <= len(labels)-1:
            raise ValueError('Invalid expected score')
        row['absolute_error'] = abs(score-target)
    return row


def summarize(rows):
    report = {}
    for kind in ('choice', 'noul', 'score'):
        group = [row for row in rows if row['type'] == kind]
        if not group:
            continue
        metrics = {'questions': len(group), 'accuracy': statistics.mean(row['correct'] for row in group),
                   'mean_brier_sum': statistics.mean(row['brier'] for row in group)}
        if kind == 'score':
            metrics['mean_absolute_error'] = statistics.mean(row['absolute_error'] for row in group)
        else:
            metrics['thresholds'] = []
            for threshold in (.5, .6, .7, .8, .9, .95, .99):
                accepted = [row for row in group if row['top_probability'] >= threshold]
                metrics['thresholds'].append({'threshold': threshold, 'accepted': len(accepted),
                    'coverage': len(accepted)/len(group),
                    'accepted_errors': sum(not row['correct'] for row in accepted),
                    'accepted_accuracy': statistics.mean(row['correct'] for row in accepted) if accepted else None})
            metrics['calibration_bins'] = []
            for index in range(10):
                bucket = [row for row in group if min(int(row['top_probability']*10), 9) == index]
                if bucket:
                    metrics['calibration_bins'].append({'lower': index/10, 'count': len(bucket),
                        'mean_probability': statistics.mean(row['top_probability'] for row in bucket),
                        'accuracy': statistics.mean(row['correct'] for row in bucket)})
        report[kind] = metrics
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset')
    parser.add_argument('--url', default='http://127.0.0.1:8008')
    parser.add_argument('--output', default='benchmark-results.json')
    args = parser.parse_args()
    cases, digest = load_cases(args.dataset)
    headers = {'Content-Type': 'application/json'}
    key = os.environ.get('KEV_API_KEY', '').strip()
    if key:
        headers['Authorization'] = 'Bearer '+key

    def request(path, payload=None):
        req = urllib.request.Request(args.url.rstrip('/')+path, headers=headers,
            data=json.dumps(payload).encode() if payload is not None else None)
        with urllib.request.urlopen(req, timeout=180) as response:
            return json.load(response)

    models = request('/v1/models')
    rows, failures, latencies = [], [], []
    started = time.perf_counter()
    first = cases[0]
    request('/v1/systemone', {'model': 'kev-latest', 'state': first['state'], 'questions': first['questions']})
    warmup_ms = (time.perf_counter()-started)*1000
    for case in cases:
        started = time.perf_counter()
        try:
            result = request('/v1/systemone', {'model': 'kev-latest', 'state': case['state'], 'questions': case['questions']})
            case_rows = [dict(measure(question, case['expected'][key], result['answers'][key]),
                              case_id=case['id'], question=key, split=case['split'])
                         for key, question in case['questions'].items()]
            rows.extend(case_rows)
            latencies.append((time.perf_counter()-started)*1000)
        except Exception as exc:
            failures.append({'case_id': case['id'], 'error_type': type(exc).__name__})
    report = {'dataset_sha256': digest, 'models': models, 'cases': len(cases),
              'failed_cases': failures, 'complete': not failures, 'rows': rows,
              'warmup_request_ms': warmup_ms, 'latency_median_ms': statistics.median(latencies) if latencies else None,
              'splits': {split: summarize([row for row in rows if row['split'] == split]) for split in ('dev', 'test')},
              'scope': 'Choose policies on dev only; use independent test data for confirmation. Metrics exclude failed cases, which must be resolved. Synthetic fixtures do not establish real-world accuracy.'}
    Path(args.output).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('cases', 'complete', 'latency_median_ms', 'splits')}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
