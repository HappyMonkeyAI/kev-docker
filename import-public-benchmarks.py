"""Convert pinned When2Call/ToolSelect data into labelled Kev choice requests."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random
import re

HF_REVISION = '0582f7749df63a96fdc3070932e83e72396ace53'
TOOL_REVISION = 'a000c57c33d0d0e0b3734b36517ed1fb8e171e1a'


def ordered_options(options, identifier):
    items = list(options.items())
    random.Random(int(hashlib.sha256(identifier.encode()).hexdigest(), 16)).shuffle(items)
    return dict(items)


def when2call(row):
    answers = row['answers']
    if not isinstance(answers, dict) or not answers or row['correct_answer'] not in answers:
        raise ValueError('Invalid When2Call labels/options')
    tools = [json.loads(tool) if isinstance(tool, str) else tool for tool in row['tools']]
    identifier = 'when2call-'+row['uuid']
    return {'id': identifier, 'split': 'test',
            'state': {'user_request': row['question'], 'available_tools': tools},
            'questions': {'decision': {'type': 'choice',
                'instructions': 'Select the best proposed response to the user given only the available tools. Consider whether a tool can satisfy the request and whether essential information is missing. Do not invent available tools or claim an action already happened.',
                'criteria': ordered_options(answers, identifier)}},
            'expected': {'decision': row['correct_answer']},
            'source': {'dataset': 'nvidia/When2Call', 'revision': HF_REVISION,
                       'upstream_split': 'test_mcq', 'source_id': row.get('source_id'), 'source': row.get('source')}}


def toolselect(text, index):
    parts = text.split('\n###\n')
    if len(parts) != 3 or not parts[0].startswith('User: ') or not parts[1].startswith('Tool Choices: '):
        raise ValueError(f'Unrecognised ToolSelect format at row {index}')
    options = {}
    for line in parts[1][len('Tool Choices: '):].splitlines():
        name, separator, description = line.partition(' = ')
        if not separator or not name or name in options:
            raise ValueError(f'Invalid ToolSelect options at row {index}')
        options[name] = description
    matches = re.findall(r'Act: CALLTOOL\["([^"\n]+)"\]', parts[2])
    if len(matches) != 1 or matches[0] not in options:
        raise ValueError(f'Invalid ToolSelect target at row {index}')
    identifier = f'toolselect-{index:04d}'
    return {'id': identifier, 'split': 'test', 'state': {'user_request': parts[0][len('User: '):]},
            'questions': {'tool': {'type': 'choice', 'instructions': 'Select the available tool whose description best satisfies the user request.',
                                  'criteria': ordered_options(options, identifier)}},
            'expected': {'tool': matches[0]},
            'source': {'dataset': 'facebookresearch/ToolVerifier ToolSelect', 'revision': TOOL_REVISION,
                       'upstream_split': 'train', 'row_index': index}}


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in rows), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='benchmarks/public')
    parser.add_argument('--sample-size', type=int, default=400)
    args = parser.parse_args()
    if args.sample_size < 1:
        parser.error('sample-size must be positive')
    root = Path(args.root)
    raw = root/'raw'
    when_rows = [when2call(json.loads(line)) for line in (raw/'when2call_test_mcq.jsonl').read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    tool_rows, rejected = [], []
    with (raw/'toolselect-train.csv').open(encoding='utf-8-sig', newline='') as handle:
        source_rows = list(csv.DictReader(handle))
        for index, row in enumerate(source_rows):
            try:
                tool_rows.append(toolselect(row['text'], index))
            except ValueError as exc:
                rejected.append({'row_index': index, 'reason': str(exc)})
    for rows in (when_rows, tool_rows):
        if len({row['id'] for row in rows}) != len(rows):
            raise ValueError('Duplicate source IDs')
        if any(not 1 <= len(next(iter(row['questions'].values()))['criteria']) <= 255 for row in rows):
            raise ValueError('Unsupported option count')
    # Label-stratified deterministic sample; report its deliberately balanced mix.
    buckets = {}
    for row in when_rows:
        buckets.setdefault(row['expected']['decision'], []).append(row)
    for bucket in buckets.values():
        bucket.sort(key=lambda row: hashlib.sha256(row['id'].encode()).hexdigest())
    sample = []
    while len(sample) < min(args.sample_size, len(when_rows)):
        for label in sorted(buckets):
            if buckets[label] and len(sample) < args.sample_size:
                sample.append(buckets[label].pop())
    write_jsonl(root/'when2call.full.jsonl', when_rows)
    write_jsonl(root/'when2call.sample.jsonl', sample)
    write_jsonl(root/'toolselect.jsonl', tool_rows)
    files = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(raw.iterdir()) if path.is_file()}
    outputs = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.glob('*.jsonl'))}
    manifest = {'raw_sha256': files, 'converted_sha256': outputs,
                'when2call': {'revision': HF_REVISION, 'license': 'CC-BY-4.0',
                    'attribution': 'NVIDIA Corporation; Ross, Mahabaleshwarka and Suhara, When2Call (NAACL 2025)',
                    'url': 'https://huggingface.co/datasets/nvidia/When2Call', 'full_rows': len(when_rows),
                    'sample_rows': len(sample), 'sample_labels': dict(Counter(row['expected']['decision'] for row in sample)),
                    'caveat': 'Published evaluation source for Kev; not a fresh untouched holdout. Balanced sample, not natural prevalence.'},
                'toolselect': {'revision': TOOL_REVISION, 'license': 'CC0-1.0',
                    'attribution': 'Meta ToolVerifier authors, Mekala et al. (2024)',
                    'url': 'https://github.com/facebookresearch/ToolVerifier', 'source_rows': len(source_rows), 'rows': len(tool_rows), 'excluded': rejected,
                    'caveat': 'Upstream training corpus evaluated exploratorily; not an official held-out ToolSelect score.'},
                'transforms': ['Keep source labels; all rows evaluation-only.',
                    'When2Call state contains question and available tools only; exclude target_tool, orig_tools and other answer metadata.',
                    'ToolSelect strips Thought/Act before building model inputs.',
                    'Deterministic per-ID option shuffle to reduce fixed-position bias.'],
                'no_training': True}
    (root/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'when2call_rows': len(when_rows), 'sample_rows': len(sample), 'toolselect_rows': len(tool_rows),
                      'sample_labels': manifest['when2call']['sample_labels'], 'toolselect_excluded': len(rejected)}, indent=2))


if __name__ == '__main__':
    main()
