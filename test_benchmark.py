import unittest
from benchmark import measure, summarize

class MetricsTests(unittest.TestCase):
    def test_brier_and_threshold_denominators(self):
        question = {'type': 'choice', 'criteria': {'a': '', 'b': ''}}
        correct = measure(question, 'a', {'type': 'choice', 'choice': 'a', 'probabilities': {'a': .9, 'b': .1}})
        wrong = measure(question, 'b', {'type': 'choice', 'choice': 'a', 'probabilities': {'a': .6, 'b': .4}})
        self.assertAlmostEqual(correct['brier'], .02)
        report = summarize([correct, wrong])['choice']
        self.assertEqual(report['accuracy'], .5)
        threshold = next(row for row in report['thresholds'] if row['threshold'] == .8)
        self.assertEqual(threshold['coverage'], .5)
        self.assertEqual(threshold['accepted_accuracy'], 1)
        empty = report['thresholds'][-1]
        self.assertIsNone(empty['accepted_accuracy'])

    def test_binary_negative_probability(self):
        row = measure({'type': 'noul'}, False, {'type': 'noul', 'noul': .1})
        self.assertTrue(row['correct'])
        self.assertEqual(row['top_probability'], .9)

    def test_ordinal_error(self):
        row = measure({'type': 'score', 'criteria': ['low', 'mid', 'high']}, 2,
                      {'type': 'score', 'score': 1.6, 'probabilities': {'0': .1, '1': .2, '2': .7}})
        self.assertAlmostEqual(row['absolute_error'], .4)
        self.assertNotIn('thresholds', summarize([row])['score'])

    def test_rejects_invalid_distribution(self):
        with self.assertRaises(ValueError):
            measure({'type': 'choice', 'criteria': {'a': '', 'b': ''}}, 'a',
                    {'type': 'choice', 'choice': 'a', 'probabilities': {'a': .9, 'b': .9}})

if __name__ == '__main__':
    unittest.main()
