"""Execute labeled synthetic trajectories and two disclosed deterministic baselines."""
import argparse
import json
from pathlib import Path
from statistics import mean
try:
    from .demo_runner import TRAJECTORIES, replay, answer_for
    from .investigation import InvestigationEngine
    from .answer_evaluator import evaluate
    from .hypothesis_engine import update, conclusion
except ImportError:
    from demo_runner import TRAJECTORIES, replay, answer_for
    from investigation import InvestigationEngine
    from answer_evaluator import evaluate
    from hypothesis_engine import update, conclusion

CASES=['A','B','C','D','scalar_gap','addition_gap','isolated']
FIXED=['attention_initial','dimension','scalar_probe','scalar_followup','addition_probe','addition_followup','weighted_probe','weighted_followup']


def unsupported(label,trace,questions):
    if not label:return False
    scored={t['question_id']:t['verdict'] for t in trace if 'question_id' in t and 'verdict' in t}
    if label=='incomplete_response':
        return not (scored.get('attention_initial')=='incomplete' and all(scored.get(q)=='correct' for q in ['dimension','scalar_probe','addition_probe','weighted_probe']))
    direct=[verdict for qid,verdict in scored.items() if questions[qid].get('direct_test')==label]
    return direct.count('incorrect')<2 or 'correct' in direct


def fixed_case(name):
    engine=InvestigationEngine();s=engine.start({});trace=[]
    for qid in FIXED:
        q=engine.questions[qid];answer=answer_for(q,TRAJECTORIES[name]['answers']);scoring=evaluate(q,answer)
        changes=update(s['hypotheses'],q,scoring)
        s['observations'].append(dict(question_id=qid,answer=answer,verdict=scoring['verdict'],signal=scoring['signal'],updates=changes))
        trace.append({'question_id':qid,'answer':answer,'verdict':scoring['verdict']})
    decision=conclusion(s,engine.questions)
    label=decision['hypothesis'] if decision else None
    uncertain=not label and any(o['verdict']=='incorrect' for o in s['observations'])
    return {'prediction':label,'repair':engine.patterns[label]['repair'] if label else None,
            'diagnostic_questions':len(FIXED),'unsupported_conclusion':unsupported(label,trace,engine.questions),
            'visible_revision':False,'uncertain':uncertain,'trace':trace}


def immediate_case(name):
    engine=InvestigationEngine();q=engine.questions['attention_initial'];answer=answer_for(q,TRAJECTORIES[name]['answers'])
    initial=evaluate(q,answer)
    trace=[{'question_id':q['id'],'answer':answer,'verdict':initial['verdict']}]
    if initial['verdict']!='correct':
        trace.append({'revealed_answer':q['expected']})
        practice=engine.questions['practice_weighted'];response=answer_for(practice,TRAJECTORIES[name]['answers'])
        trace.append({'question_id':practice['id'],'answer':response,'verdict':evaluate(practice,response)['verdict']})
    # This baseline explains/practices but makes no causal diagnosis. Do not invent one for it.
    return {'prediction':None,'repair':'weighted_sums' if initial['verdict']!='correct' else None,
            'diagnostic_questions':1,'unsupported_conclusion':False,'visible_revision':False,'uncertain':False,'trace':trace}


def adaptive_case(name):
    run=replay(name);r=run['result'];decision=r['report']['diagnosis'] or {};label=decision.get('hypothesis')
    return {'prediction':label,'repair':(r['report']['intervention'] or {}).get('id'),
            'diagnostic_questions':r['report']['diagnostic_questions_used'],
            'unsupported_conclusion':unsupported(label,run['trace'],InvestigationEngine().questions),
            'visible_revision':any(t.get('revision_message') for t in run['trace']),
            'uncertain':r['next']['kind']=='uncertain','trace':run['trace']}


def run_evaluation():
    methods={'Fixed questionnaire':fixed_case,'Immediate explanation':immediate_case,'Knowledge DNA':adaptive_case}
    rows=[];details={}
    labels=[name for name in CASES if TRAJECTORIES[name]['label'] is not None]
    for method,fn in methods.items():
        cases={name:fn(name) for name in CASES};details[method]=cases
        correct=sum(cases[name]['prediction']==TRAJECTORIES[name]['label'] for name in labels)
        repair_correct=sum(cases[name]['repair']==InvestigationEngine().patterns[TRAJECTORIES[name]['label']]['repair'] for name in labels)
        uncertain=sum(cases[name]['uncertain'] for name in ['C','isolated'])
        rows.append({'method':method,'labeled_cause_correct':correct,'labeled_cases':len(labels),
                     'mean_diagnostic_questions':round(mean(c['diagnostic_questions'] for c in cases.values()),3),
                     'unsupported_conclusions':sum(c['unsupported_conclusion'] for c in cases.values()),
                     'cases':len(cases),'correct_repair':repair_correct,
                     'uncertain_cases_handled':uncertain,'uncertain_cases':2,
                     'visible_counterevidence_revision':any(c['visible_revision'] for c in cases.values())})
    a,b=details['Knowledge DNA']['A'],details['Knowledge DNA']['B']
    mandatory=(a['trace'][0]['answer']==b['trace'][0]['answer'] and a['prediction']=='incomplete_response' and b['prediction']=='weighted_aggregation')
    assert mandatory,'Same wrong answer must support different outcomes after different evidence'
    return {'synthetic_only':True,'validated_real_world_learning_study':False,'seed':'deterministic; no randomness',
            'mandatory_same_initial_answer_test':mandatory,'summary':rows,'details':details}


def markdown(result):
    lines=['# Executed synthetic evaluation','',
           'These are authored synthetic trajectories, not a validated study of real student learning. Labels describe the simulated responses. No paid model or real academic account was used.','',
           '| Policy | Correct cause / labeled cases | Mean diagnostic questions | Unsupported causal claims / all cases | Correct targeted repair / labeled cases | Uncertain cases handled | Visible revision |',
           '| --- | --- | --- | --- | --- | --- | --- |']
    for r in result['summary']:
        lines.append(f"| {r['method']} | {r['labeled_cause_correct']}/{r['labeled_cases']} | {r['mean_diagnostic_questions']} | {r['unsupported_conclusions']}/{r['cases']} | {r['correct_repair']}/{r['labeled_cases']} | {r['uncertain_cases_handled']}/{r['uncertain_cases']} | {'yes' if r['visible_counterevidence_revision'] else 'no'} |")
    lines.extend(['','Mandatory same-initial-answer test: **PASS**. A and B both begin with `1`, then live tests distinguish response completeness from weighted aggregation.','',
                  'Methods: Fixed asks the same eight diagnostic items, then uses the same conservative evidence threshold as Knowledge DNA. It can be equally accurate but asks unnecessary items. Immediate explanation reveals the initial answer and gives weighted practice; it makes no causal claim and gets no invented diagnosis credit. Knowledge DNA chooses experiments from competing categorical predictions and visibly reduces support after contrary evidence.','',
                  'Four cases have a labeled cause; C and the isolated-error case require uncertainty, and D has no demonstrated gap. Scores above are counts, not statistical confidence. Unsupported means a nonempty cause without the required live evidence; all supported adaptive labels require two direct errors or the specific completeness checks.','',
                  'Limitations: the tiny hand-authored corpus shares its question bank and error assumptions with the engine; it is not held out, randomized, or independently annotated. Transfer is a conservative keyword rubric. Correct post-lesson answers were authored, so this evaluation cannot establish that instruction caused learning. Lower question count is relative to the fixed baseline, not immediate explanation.','',
                  'Reproduce: `python3 scripts/evaluate.py --output evaluation/results.json --markdown docs/evaluation.md`.'])
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--markdown',type=Path);args=p.parse_args()
    result=run_evaluation()
    for path,contents in [(args.output,json.dumps(result,indent=2)+'\n'),(args.markdown,markdown(result))]:
        if path:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(contents)
    print(json.dumps({'mandatory_same_initial_answer_test':result['mandatory_same_initial_answer_test'],'summary':result['summary']}))


if __name__=='__main__':main()
