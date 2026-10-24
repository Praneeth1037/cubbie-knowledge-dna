import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from scripts.diagnose import DiagnosticService, unpack
from scripts.investigation import InvestigationError
from scripts.profile_store import ProfileStore, StoreError

ROOT=Path(__file__).resolve().parent.parent


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=ProfileStore(self.temp.name)
        self.service=DiagnosticService(lambda:self.store)
    def reply(self,r,answer,**extra):
        return self.service.handle(dict(action='answer',session_id=r['session_id'],revision=r['revision'],question_id=r['next']['question_id'],answer=answer,**extra))
    def test_start_answer_report_resume_receipts(self):
        r=self.service.handle({'action':'start'})
        self.assertTrue(r['storage']['saved']);self.assertEqual(r['engine_version'],'3.0')
        self.assertEqual(r['execution']['observations'],0)
        after=self.reply(r,'1')
        resumed=self.service.handle({'action':'resume'})
        self.assertEqual(after['session_id'],resumed['session_id'])
        self.assertEqual(after['next'],resumed['next'])
        self.assertEqual(after['execution']['evidence_digest'],resumed['execution']['evidence_digest'])
        reported=self.service.handle({'action':'report'})
        self.assertEqual(reported['investigation']['path'][0]['answer'],'1')
        self.assertNotIn('expected',json.dumps(after['next']))
    def test_stale_turn_preserves_disk(self):
        r=self.service.handle({'action':'start'});self.reply(r,'1')
        before=self.store.path('student').read_bytes()
        with self.assertRaises(InvestigationError):self.reply(r,'1')
        self.assertEqual(before,self.store.path('student').read_bytes())
    def test_duplicate_message_does_not_answer_a_different_question(self):
        r=self.service.handle({'action':'start'});r=self.reply(r,'1',message_id='message1')
        with self.assertRaises(InvestigationError):self.reply(r,2,message_id='message1')
    def test_broken_storage_keeps_diagnostics_running(self):
        def fail():raise StoreError('No persistent configuration','missing_data_dir')
        service=DiagnosticService(fail)
        r=service.handle({'action':'start'})
        self.assertEqual(r['storage']['mode'],'temporary');self.assertFalse(r['storage']['saved'])
        r=service.handle({'action':'answer','session_id':r['session_id'],'revision':r['revision'],
                          'question_id':'attention_initial','answer':'1','continuation':r['continuation']})
        self.assertEqual(r['next']['question_id'],'dimension')
        self.assertEqual(r['execution']['observations'],1)
        resumed=service.handle({'action':'resume','continuation':r['continuation']})
        self.assertEqual(resumed['next'],r['next'])
    def test_storage_failure_between_calls_uses_checkpoint(self):
        r=self.service.handle({'action':'start'})
        with patch.object(self.store,'update',side_effect=OSError('read only')):
            r=self.service.handle({'action':'answer','session_id':r['session_id'],'revision':r['revision'],
                                   'question_id':'attention_initial','answer':'1','continuation':r['continuation']})
        self.assertEqual(r['next']['question_id'],'dimension')
        self.assertFalse(r['storage']['saved'])
    def test_atomic_write_failure_keeps_applied_turn_in_temporary_checkpoint(self):
        r=self.service.handle({'action':'start'})
        before=self.store.path('student').read_bytes()
        with patch('scripts.profile_store.os.replace',side_effect=OSError('disk unavailable')):
            r=self.reply(r,'1')
        self.assertEqual(r['storage']['mode'],'temporary')
        self.assertEqual(r['execution']['observations'],1)
        self.assertEqual(r['next']['question_id'],'dimension')
        self.assertEqual(before,self.store.path('student').read_bytes())
    def test_full_investigation_runs_without_persistent_storage(self):
        from scripts.demo_runner import TRAJECTORIES,answer_for
        for scenario in 'ABCD':
            r=self.service.handle({'action':'start','temporary':True})
            for _ in range(20):
                pending=r['next']
                if pending['kind'] not in {'question','intervention'}:break
                request={'session_id':r['session_id'],'revision':r['revision'],
                         'continuation':r['continuation'],'temporary':True}
                if pending['kind']=='intervention':request['action']='repair'
                else:
                    q=self.service.engine.questions[pending['question_id']]
                    request.update(action='answer',question_id=q['id'],answer=answer_for(q,TRAJECTORIES[scenario]['answers']))
                r=self.service.handle(request)
                self.assertLess(len(json.dumps(r)),8000)
                self.assertFalse(r['storage']['saved'])
            report=self.service.handle({'action':'report','temporary':True,'continuation':r['continuation']})
            self.assertLess(len(json.dumps(report)),8000)
            self.assertEqual(report['next']['kind'],'uncertain' if scenario=='C' else 'complete')
    def test_corrupt_file_is_preserved_then_explicitly_quarantined(self):
        path=self.store.path('student');path.write_text('{broken')
        r=self.service.handle({'action':'start'})
        self.assertEqual(r['storage']['mode'],'temporary')
        self.assertEqual(path.read_text(),'{broken')
        recovered=self.service.handle({'action':'recover'})
        self.assertEqual(Path(recovered['recovery']['quarantined']).read_text(),'{broken')
        self.assertEqual(self.service.handle({'action':'start'})['storage']['mode'],'persistent')
    def test_malformed_forensic_record_can_resume_from_checkpoint_without_overwriting(self):
        r=self.service.handle({'action':'start'})
        path=self.store.path('student');profile=json.loads(path.read_text());profile['forensics']=[]
        path.write_text(json.dumps(profile));before=path.read_bytes()
        resumed=self.service.handle({'action':'resume','continuation':r['continuation']})
        self.assertEqual(resumed['storage']['mode'],'temporary')
        self.assertEqual(resumed['next'],r['next'])
        self.assertEqual(before,path.read_bytes())
    def test_legacy_progress_is_retained(self):
        from scripts.legacy_diagnose import DiagnosticEngine
        old=DiagnosticEngine()
        self.store.update('student',lambda p:old.transition(p,{'action':'start'}))
        before=self.store.load('student')['session']
        self.service.handle({'action':'start'})
        self.assertEqual(self.store.load('student')['session'],before)
    def test_skip_investigation_is_helpful_without_a_diagnosis(self):
        r=self.service.handle({'action':'start'})
        r=self.service.handle({'action':'skip','session_id':r['session_id'],'revision':r['revision']})
        self.assertEqual(r['next']['kind'],'intervention')
        self.assertIsNone(r['report']['diagnosis']['hypothesis'])
        self.assertTrue(r['report']['intervention']['requested_directly'])
    def test_failed_independent_check_never_claims_improvement(self):
        r=self.service.handle({'action':'start'});r=self.reply(r,[1.5,1]);r=self.reply(r,[99,99])
        self.assertFalse(r['report']['improvement_verified'])
        self.assertEqual(r['report']['understanding']['calculation'],'not demonstrated')
    def test_partial_transfer_is_not_verified(self):
        r=self.service.handle({'action':'start'});r=self.reply(r,[1.5,1]);r=self.reply(r,[1,5]);r=self.reply(r,'It adds information')
        self.assertEqual(r['report']['understanding']['transfer'],'partially demonstrated')
        self.assertFalse(r['report']['improvement_verified'])
    def test_checkpoint_validation_and_bounds(self):
        for token in ['garbage','a'*12001]:
            with self.assertRaises(ValueError):unpack(token)
    def test_no_history_and_storage_check(self):
        self.assertEqual(self.service.handle({'action':'resume'})['next']['kind'],'not_started')
        self.assertTrue(self.service.handle({'action':'storage-check'})['storage']['read_write_verified'])
        self.assertFalse(self.store.path('student').exists())
    def test_invalid_contracts_do_not_write(self):
        for request in [[],{}, {'action':'unknown'}, {'action':'start','question_budget':100}, {'action':'start','learner_id':'../escape'}]:
            with self.subTest(request=request),self.assertRaises(ValueError):self.service.handle(request)
        self.assertFalse(self.store.path('student').exists())


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.env=dict(os.environ,SKILL_DATA_DIR=self.tmp.name)
    def call(self,command,request=None,env=None):
        result=subprocess.run([sys.executable,str(ROOT/'scripts/diagnose.py'),command],input=json.dumps(request or {}),text=True,capture_output=True,env=env or self.env,timeout=5)
        self.assertEqual(result.stderr,'')
        self.assertLess(len(result.stdout),8000)
        return result,json.loads(result.stdout)
    def test_commands_execute_bounded_json_and_persist_across_processes(self):
        for command in ['storage-check','start','report','resume']:
            result,r=self.call(command);self.assertEqual(result.returncode,0,r);self.assertTrue(r['ok'])
        _,r=self.call('resume')
        _,a=self.call('answer',{'session_id':r['session_id'],'revision':r['revision'],'question_id':'attention_initial','answer':'1'})
        _,resumed=self.call('resume')
        self.assertEqual(a['next'],resumed['next'])
        self.assertEqual(a['execution']['evidence_digest'],resumed['execution']['evidence_digest'])
    def test_missing_environment_fallback(self):
        env=dict(self.env,HOME=self.tmp.name);env.pop('SKILL_DATA_DIR')
        result,r=self.call('start',env=env)
        self.assertEqual(result.returncode,0)
        self.assertEqual(r['storage']['configuration'],'persistent_home')
    def test_missing_both_environment_locations_returns_temporary_session(self):
        env=dict(self.env);env.pop('SKILL_DATA_DIR');env.pop('HOME',None)
        result,r=self.call('start',env=env)
        self.assertEqual(result.returncode,0)
        self.assertEqual(r['storage']['mode'],'temporary')
        self.assertEqual(r['next']['question_id'],'attention_initial')
    def test_input_file_is_supported_without_interactive_stdin(self):
        path=Path(self.tmp.name)/'request.json';path.write_text('{"question_budget":4}')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/diagnose.py'),'start','--input',str(path)],stdin=subprocess.DEVNULL,text=True,capture_output=True,env=self.env,timeout=5)
        self.assertEqual(result.returncode,0,result.stdout)
        self.assertEqual(json.loads(result.stdout)['engine_version'],'3.0')
    def test_demo_command_uses_real_engine(self):
        result,rows=self.call('demo')
        self.assertEqual(result.returncode,0)
        self.assertEqual([row['outcome'] for row in rows[:4]],['complete','complete','uncertain','complete'])
    def test_invalid_command_is_a_json_error(self):
        result,r=self.call('not-a-command')
        self.assertEqual(result.returncode,2)
        self.assertFalse(r['ok'])
