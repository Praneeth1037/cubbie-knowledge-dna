import unittest
from scripts.investigation import InvestigationEngine
from scripts.demo_runner import replay


class SelectionTests(unittest.TestCase):
    def test_unique_stable_identifiers(self):
        a,b=InvestigationEngine(),InvestigationEngine()
        self.assertEqual(list(a.questions),list(b.questions))
        self.assertIn('attention_initial',a.questions)
    def test_no_question_repetition(self):
        for scenario in 'ABCD':
            ids=[t['question_id'] for t in replay(scenario)['trace'] if 'question_id' in t]
            self.assertEqual(len(ids),len(set(ids)))
    def test_selection_has_interpretable_reason_and_score(self):
        trace=replay('A')['trace']
        dimension=trace[1]
        self.assertEqual(dimension['question_id'],'dimension')
        self.assertIn('separated_pair_weight',dimension['selection'])
        self.assertIn('not probabilities',dimension['selection']['assumption'])
    def test_budget_stops_without_unsupported_conclusion(self):
        e=InvestigationEngine();s=e.start({'question_budget':3})
        for _ in range(3):
            self.assertEqual(s['next']['kind'],'question')
            s=e.apply(s,{'action':'answer','question_id':s['next']['question_id'],'answer':'unclear'})
        self.assertEqual(s['next']['kind'],'uncertain')
        self.assertIsNone(s['conclusion']['hypothesis'])
    def test_prerequisite_graph_extended_without_breaking_legacy(self):
        g=InvestigationEngine().graph
        self.assertIn('scalar_multiplication',g.prerequisites('transformer_attention'))
        self.assertIn('vector_addition',g.prerequisites('weighted_sums'))
