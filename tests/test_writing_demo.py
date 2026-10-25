import json
import tempfile
import unittest
from scripts.demo_runner import replay,TRAJECTORIES,answer_for
from scripts.diagnose import DiagnosticService
from scripts.profile_store import ProfileStore
from scripts.investigation import InvestigationEngine
from scripts.answer_evaluator import evaluate


class WritingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.service=DiagnosticService(lambda:ProfileStore(self.temp.name))
    def reply(self,r,answer):
        return self.service.handle({'action':'answer','session_id':r['session_id'],'revision':r['revision'],
                                    'question_id':r['next']['question_id'],'answer':answer})
    def test_writing_demo_has_no_math_and_targets_the_supported_gap(self):
        r=replay('writing')
        text=' '.join(t.get('prompt','') for t in r['trace'])
        for term in ('vector','weights','tensor','matrix','calculate'):self.assertNotIn(term,text)
        self.assertEqual(r['result']['report']['diagnosis']['hypothesis'],'writing_link')
        self.assertTrue(r['result']['report']['improvement_verified'])
        self.assertEqual(r['result']['report']['understanding']['paragraph_application'],'demonstrated on independent examples')
        self.assertNotIn('calculation',r['result']['report']['understanding'])
    def test_first_wrong_choice_investigates_before_teaching(self):
        r=self.service.handle({'action':'start','scenario':'writing'});r=self.reply(r,'B')
        self.assertEqual(r['next']['kind'],'question');self.assertIsNone(r['report']['diagnosis'])
        self.assertEqual(r['next']['question_id'],'writing_claim_probe')
        r=self.reply(r,'B')
        h=next(h for h in r['hypotheses'] if h['id']=='writing_claim')
        self.assertEqual(h['status'],'less_supported')
    def test_claim_gap_gets_a_different_lesson(self):
        r=self.service.handle({'action':'start','scenario':'writing'})
        for answer in ['B','A','B']:r=self.reply(r,answer)
        self.assertEqual(r['next']['kind'],'intervention')
        self.assertEqual(r['next']['repair_id'],'writing_claim')
    def test_correct_intro_then_wrong_independent_choice_still_investigates(self):
        r=self.service.handle({'action':'start','scenario':'writing'});r=self.reply(r,'A')
        self.assertEqual(r['next']['phase'],'verification');r=self.reply(r,'A')
        self.assertEqual(r['next']['kind'],'question');self.assertEqual(r['next']['phase'],'diagnostic')
        self.assertIsNone(r['report']['diagnosis']);self.assertFalse(r['report']['improvement_verified'])
    def test_choice_parser_is_conservative(self):
        q=InvestigationEngine().questions['writing_initial']
        for text in ['A','a.','Option A']:self.assertEqual(evaluate(q,text)['verdict'],'correct')
        for text in ['maybe A or B','neither',1]:self.assertEqual(evaluate(q,text)['verdict'],'unscored')
    def test_writing_works_in_temporary_mode(self):
        r=self.service.handle({'action':'start','scenario':'writing','temporary':True})
        for _ in range(15):
            n=r['next']
            if n['kind'] not in {'question','intervention'}:break
            request=dict(session_id=r['session_id'],revision=r['revision'],temporary=True,continuation=r['continuation'])
            if n['kind']=='intervention':request['action']='repair'
            else:
                q=self.service.engine.questions[n['question_id']]
                request.update(action='answer',question_id=q['id'],answer=answer_for(q,TRAJECTORIES['writing']['answers']))
            r=self.service.handle(request);self.assertFalse(r['storage']['saved'])
            self.assertLess(len(json.dumps(r)),8000)
        self.assertTrue(r['report']['improvement_verified'])
    def test_saved_writing_resumes(self):
        r=self.service.handle({'action':'start','scenario':'writing'});r=self.reply(r,'B')
        resumed=DiagnosticService(lambda:ProfileStore(self.temp.name)).handle({'action':'resume'})
        self.assertEqual(resumed['next'],r['next'])
    def test_fresh_verification_preserves_failed_attempt_then_records_transfer(self):
        r=self.service.handle({'action':'start','scenario':'writing'})
        overrides=dict(TRAJECTORIES['writing']['answers'],writing_independent='A')
        for _ in range(15):
            n=r['next']
            if n['kind']=='intervention':
                r=self.service.handle({'action':'repair','session_id':r['session_id'],'revision':r['revision']})
            elif n['kind']=='question':
                r=self.reply(r,answer_for(self.service.engine.questions[n['question_id']],overrides))
            else:break
        self.assertFalse(r['report']['improvement_verified'])
        r=self.service.handle({'action':'verify','session_id':r['session_id'],'revision':r['revision']})
        self.assertEqual(r['next']['question_id'],'writing_independent_followup')
        r=self.reply(r,'Option A')
        r=self.reply(r,'I would connect the evidence to the main point and explain why it supports the claim.')
        self.assertTrue(r['report']['improvement_verified'])
        observations=ProfileStore(self.temp.name).load('student')['forensics']['current']['observations']
        checks=[o for o in observations if self.service.engine.questions[o['question_id']]['role']=='verification']
        self.assertEqual([(o['answer'],o['verdict']) for o in checks],[('A','incorrect'),('Option A','correct')])


class FailedIndependentRegressionTests(unittest.TestCase):
    def test_exact_reported_exchange_continues_investigation(self):
        e=InvestigationEngine();s=e.start({})
        s=e.apply(s,{'action':'answer','question_id':'attention_initial','answer':'1.5,1'})
        s=e.apply(s,{'action':'answer','question_id':'independent_attention','answer':'1,6'})
        self.assertEqual(s['next']['kind'],'question');self.assertEqual(s['next']['question_id'],'scalar_probe')
        self.assertIsNone(s['conclusion'])
        self.assertEqual(s['investigation_trigger'],'independent_attention')
    def test_repair_after_failed_independent_uses_a_new_verification(self):
        e=InvestigationEngine();s=e.start({})
        overrides={'attention_initial':'1.5,1','independent_attention':'1,6','weighted_probe':[5,10],'weighted_followup':[10,5]}
        asked=[]
        for _ in range(16):
            n=s['next']
            if n['kind']=='intervention':s=e.apply(s,{'action':'repair'});continue
            if n['kind']!='question':break
            q=e.questions[n['question_id']];asked.append(q['id'])
            answer=answer_for(q,overrides)
            s=e.apply(s,{'action':'answer','question_id':q['id'],'answer':answer})
        self.assertIn('independent_attention_followup',asked)
        self.assertEqual(len(asked),len(set(asked)))
        self.assertTrue(e.report(s)['report']['improvement_verified'])
    def test_previously_explained_intro_is_replaced(self):
        e=InvestigationEngine();s=e.start({'initial_exposed':True,'exposed_questions':['independent_attention']})
        self.assertEqual(s['next']['question_id'],'attention_fresh_initial')
        q=e.questions[s['next']['question_id']]
        s=e.apply(s,{'action':'answer','question_id':q['id'],'answer':q['expected']})
        self.assertEqual(s['next']['question_id'],'independent_attention_followup')
    def test_new_writing_intro_when_original_seen(self):
        self.assertEqual(InvestigationEngine().start({'scenario':'writing','initial_exposed':True})['next']['question_id'],'writing_fresh_initial')
