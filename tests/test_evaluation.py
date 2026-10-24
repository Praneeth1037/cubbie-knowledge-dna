import unittest
from scripts.evaluate import run_evaluation,unsupported
from scripts.demo_runner import replay
from scripts.investigation import InvestigationEngine


class EvaluationTests(unittest.TestCase):
    def test_results_are_recomputed_and_same_wrong_answer_distinguished(self):
        a,b=run_evaluation(),run_evaluation()
        self.assertEqual(a,b)
        self.assertTrue(a['mandatory_same_initial_answer_test'])
        self.assertTrue(a['synthetic_only'])
        self.assertFalse(a['validated_real_world_learning_study'])
        for row in a['summary']:
            self.assertEqual(row['cases'],7)
            self.assertLessEqual(row['labeled_cause_correct'],row['labeled_cases'])
    def test_adaptive_support_is_audited_from_actual_verdicts(self):
        result=run_evaluation()
        adaptive=next(r for r in result['summary'] if r['method']=='Knowledge DNA')
        self.assertEqual(adaptive['unsupported_conclusions'],0)
        self.assertEqual(adaptive['labeled_cause_correct'],4)
        self.assertTrue(unsupported('weighted_aggregation',[{'question_id':'weighted_probe','verdict':'incorrect'}],InvestigationEngine().questions))
    def test_counterfactual_and_transfer_are_separate(self):
        result=replay('B')['result']['investigation']['assessments']
        self.assertEqual([r['role'] for r in result],['practice','verification','transfer'])
        self.assertEqual(result[1]['answer_excerpt'],'[1, 5]')
    def test_synthetic_transcripts_reproduce_exactly(self):
        for name in ['A','B','C','D','academic','false_mastery']:
            self.assertEqual(replay(name),replay(name))
