import unittest
from scripts.demo_runner import replay
from scripts.investigation import InvestigationEngine


class HypothesisTests(unittest.TestCase):
    def test_same_initial_answer_different_causes(self):
        a,b=replay('A'),replay('B')
        self.assertEqual(a['trace'][0]['answer'],b['trace'][0]['answer'])
        self.assertEqual(a['result']['report']['diagnosis']['hypothesis'],'incomplete_response')
        self.assertEqual(b['result']['report']['diagnosis']['hypothesis'],'weighted_aggregation')
        self.assertNotEqual([x.get('question_id') for x in a['trace']],[x.get('question_id') for x in b['trace']])
    def test_contradictory_evidence_revises_hypothesis(self):
        trace=replay('A')['trace']
        scalar=next(t for t in trace if t.get('question_id')=='scalar_probe')
        self.assertIn('less likely',scalar['revision_message'])
        h=next(h for h in scalar['hypotheses'] if h['id']=='scalar_multiplication')
        self.assertLess(h['score'],0)
    def test_no_label_from_initial_incomplete_answer(self):
        e=InvestigationEngine();s=e.start({});s=e.apply(s,{'action':'answer','question_id':'attention_initial','answer':'1'})
        self.assertIsNone(s['conclusion'])
        self.assertEqual(len(s['hypotheses']),4)
        self.assertEqual(s['next']['question_id'],'dimension')
    def test_inconsistency_remains_uncertain(self):
        r=replay('C')['result']
        self.assertEqual(r['next']['kind'],'uncertain')
        self.assertIsNone(r['report']['diagnosis']['hypothesis'])
        self.assertFalse(r['report']['improvement_verified'])
    def test_all_operations_do_not_require_repair(self):
        r=replay('D')['result']['report']
        self.assertIsNone(r['intervention'])
        self.assertEqual(r['understanding']['calculation'],'demonstrated on independent examples')
        self.assertFalse(r['improvement_verified'])
    def test_targeted_repair_and_independent_verification(self):
        r=replay('B');report=r['result']['report']
        self.assertEqual(report['intervention']['id'],'weighted_sums')
        self.assertTrue(report['improvement_verified'])
        independent=next(x for x in r['trace'] if x.get('question_id')=='independent_attention')
        self.assertEqual(independent['answer'],[1,5])
    def test_false_mastery_preserves_recall_application_distinction(self):
        r=replay('false_mastery')['result']['report']
        self.assertTrue(r['recall_application_mismatch'])
        self.assertEqual(r['understanding']['verbal_recall'],'demonstrated on diagnostic examples')
    def test_no_permanent_mastery_or_confidence_percentages(self):
        for name in 'ABCD':
            r=replay(name)['result']
            self.assertNotIn('confidence_percent',str(r))
            self.assertNotIn('permanent mastery',str(r['report']['understanding']))
