import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('public_import', Path(__file__).with_name('import-public-benchmarks.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ImportTests(unittest.TestCase):
    def test_when2call_only_available_tools_and_question_enter_state(self):
        row = {'uuid':'one', 'question':'Question', 'tools':['{"name":"available"}'],
               'answers': {'call':'Call available', 'decline':'Cannot answer'}, 'correct_answer':'call',
               'target_tool':'SECRET_GOLD', 'orig_tools':['SECRET_GOLD']}
        result = module.when2call(row)
        self.assertEqual(result['state'], {'user_request':'Question','available_tools':[{'name':'available'}]})
        self.assertEqual(result['expected']['decision'], 'call')
        self.assertEqual(set(result['questions']['decision']['criteria']), set(row['answers']))

    def test_toolselect_strips_reasoning_and_action(self):
        text = 'User: Find a book\n###\nTool Choices: Books = Search books\nWeather = Forecast\n###\nThought: SECRET_REASONING\nAct: CALLTOOL["Books"]'
        result = module.toolselect(text, 0)
        self.assertEqual(result['expected']['tool'], 'Books')
        self.assertNotIn('SECRET_REASONING', str(result['state'])+str(result['questions']))
        self.assertNotIn('CALLTOOL', str(result['state'])+str(result['questions']))

    def test_missing_target_is_rejected_without_repair(self):
        text = 'User: Find a book\n###\nTool Choices: Books = Search books\n###\nAct: CALLTOOL["Missing"]'
        with self.assertRaises(ValueError):
            module.toolselect(text, 0)

    def test_option_order_is_repeatable(self):
        options = dict(a='A', b='B', c='C', d='D')
        self.assertEqual(module.ordered_options(options, 'same'), module.ordered_options(options, 'same'))
        self.assertEqual(module.ordered_options(options, 'same'), options)

if __name__ == '__main__':
    unittest.main()
