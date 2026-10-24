import unittest
from scripts.investigation import InvestigationEngine
from scripts.answer_evaluator import evaluate


class AnswerEvaluatorTests(unittest.TestCase):
    def setUp(self): self.q = InvestigationEngine().questions
    def test_correct_and_wrong_numerical_answers(self):
        self.assertEqual(evaluate(self.q['attention_initial'], '[1.5,1]')['verdict'], 'correct')
        self.assertEqual(evaluate(self.q['attention_initial'], '[2,4]')['signal'], 'unweighted')
    def test_incomplete_is_not_conceptual_error(self):
        for answer in ['1', [1], [1,2,3]]:
            self.assertEqual(evaluate(self.q['attention_initial'], answer)['verdict'], 'incomplete')
    def test_common_vector_notation(self):
        for answer in ['1.5,1', '(1.5,1)', 'The answer is [1.5,1]']:
            self.assertEqual(evaluate(self.q['attention_initial'], answer)['verdict'], 'correct')
    def test_ambiguous_and_unsafe_are_unscored(self):
        for answer in [None, True, 'maybe', '__import__("os").system("false")', float('inf')]:
            self.assertEqual(evaluate(self.q['attention_initial'], answer)['verdict'], 'unscored')
    def test_dimension_explanation_only_scores_count(self):
        self.assertEqual(evaluate(self.q['dimension'], 'Two because each position adds separately')['verdict'], 'correct')
    def test_transfer_rubric_conservative_partial_and_negation(self):
        q=self.q['transfer_attention']
        self.assertEqual(evaluate(q, 'It combines value vectors according to their weights')['verdict'], 'correct')
        self.assertEqual(evaluate(q, 'It adds information')['verdict'], 'partial')
        self.assertEqual(evaluate(q, 'It does not combine value vectors using weights')['verdict'], 'unscored')
        self.assertEqual(evaluate(q, 'attention is amazing')['verdict'], 'unscored')
    def test_answer_size_bounded(self):
        with self.assertRaises(ValueError): evaluate(self.q['attention_initial'], 'x'*513)
