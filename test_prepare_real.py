import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('prepare_real', Path(__file__).with_name('prepare-real-benchmark.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ExportTests(unittest.TestCase):
    def run_export(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'review.jsonl'
            output = Path(directory)/'labelled.jsonl'
            source.write_text(''.join(json.dumps(row)+'\n' for row in rows))
            module.export_reviewed(source, output)
            return [json.loads(line) for line in output.read_text().splitlines()]

    def row(self, identifier='one', split='dev', request='Read the README'):
        return {'id': identifier, 'split': split, 'session_group': 'one-session',
                'state': {'user_request': request}, 'review_status': 'approved',
                'expected_route': 'inspect', 'context_complete': True, 'privacy_reviewed': True}

    def test_pending_labels_are_not_exported(self):
        row = self.row()
        row['review_status'] = 'pending'
        with self.assertRaises(ValueError):
            self.run_export([row])

    def test_session_leakage_is_rejected(self):
        with self.assertRaises(ValueError):
            self.run_export([self.row(), self.row('two', 'test', 'Read the Dockerfile')])

    def test_context_review_is_required(self):
        row = self.row()
        row['context_complete'] = False
        with self.assertRaises(ValueError):
            self.run_export([row])

    def test_export_preserves_reviewed_label(self):
        rows = self.run_export([self.row()])
        self.assertEqual(rows[0]['expected']['route'], 'inspect')
        self.assertIn('respond', rows[0]['questions']['route']['criteria'])

if __name__ == '__main__':
    unittest.main()
