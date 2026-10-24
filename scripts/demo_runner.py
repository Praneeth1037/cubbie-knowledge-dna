"""Deterministic students replayed against the real 3.0 engine, never canned outcomes."""
import argparse
import json
import tempfile
from pathlib import Path
try:
    from .diagnose import DiagnosticService
    from .profile_store import ProfileStore
except ImportError:
    from diagnose import DiagnosticService
    from profile_store import ProfileStore

TRANSFER = 'Attention combines information from value vectors according to their weights.'
RECALL = 'Queries describe what information a token is looking for; keys are compared for a match; values contribute content.'
TRAJECTORIES = {
    'A': {'label': 'incomplete_response', 'answers': {'attention_initial': '1'}},
    'B': {'label': 'weighted_aggregation', 'answers': {'attention_initial': '1', 'weighted_probe': [5, 10], 'weighted_followup': [10, 5]}},
    'C': {'label': None, 'answers': {'attention_initial': '1', 'addition_probe': [1.5, 0], 'weighted_probe': [5, 10]}},
    'D': {'label': None, 'answers': {}},
    'false_mastery': {'label': 'incomplete_response', 'scenario': 'false_mastery', 'answers': {'attention_initial': '1'}},
    'academic': {'label': 'tensor_shapes', 'scenario': 'academic_forensics', 'answers': {'shape_initial': [2,4,8], 'shape_followup': [3,5,7]}},
    'scalar_gap': {'label': 'scalar_multiplication', 'answers': {'attention_initial': '1', 'scalar_probe': [2,0], 'scalar_followup': [4,2]}},
    'addition_gap': {'label': 'vector_addition', 'answers': {'attention_initial': '1', 'addition_probe': [1.5,0], 'addition_followup': [2,3]}},
    'isolated': {'label': None, 'answers': {'attention_initial': [1,1]}},
}


def answer_for(question, overrides):
    if question['id'] in overrides:
        return overrides[question['id']]
    if question['id'] == 'recall_qkv':
        return RECALL
    if question['role'] == 'transfer':
        return 'The mask shape must align with the correct attention dimensions.' if question['domain'] == 'shapes' else TRANSFER
    return question['expected']


def replay(name, service=None):
    trajectory = TRAJECTORIES[name]
    with tempfile.TemporaryDirectory(prefix='knowledge-dna-v3-demo-') as directory:
        service = service or DiagnosticService(lambda: ProfileStore(directory))
        request = {'action': 'start', 'learner_id': 'demo', 'scenario': trajectory.get('scenario', 'attention')}
        if name == 'academic':
            data = Path(__file__).resolve().parent.parent / 'data'
            request.update(synthetic_mode=True, sources=sum([
                json.loads((data / file).read_text())['sources'] for file in
                ('synthetic_canvas_feedback.json', 'synthetic_docs_notes.json')], []))
        response = service.handle(request)
        trace = []
        for _ in range(20):
            pending = response['next']
            if pending['kind'] not in {'question', 'intervention'}:
                break
            turn = {'learner_id': 'demo', 'session_id': response['session_id'], 'revision': response['revision']}
            if pending['kind'] == 'intervention':
                trace.append({'kind': 'lesson', 'repair': pending['repair_id'], 'lesson': pending['lesson']})
                response = service.handle(dict(turn, action='repair'))
            else:
                q = service.engine.questions[pending['question_id']]
                answer = answer_for(q, trajectory['answers'])
                event = {'question_id': q['id'], 'prompt': q['prompt'], 'selection': pending['selection'], 'answer': answer}
                response = service.handle(dict(turn, action='answer', question_id=q['id'], answer=answer))
                event.update(feedback=response['feedback'], verdict=response['last_observation']['verdict'], revision_message=response['revision_message'], hypotheses=response['hypotheses'])
                trace.append(event)
        else:
            raise AssertionError('Replay exceeded the resource bound')
        reported = service.handle({'action': 'report', 'learner_id': 'demo'})
        # Normalize volatile execution identifiers; transcripts are reproducible content.
        for key in ('continuation', 'execution', 'session_id', 'storage'):
            reported.pop(key, None)
        return {'trajectory': name, 'synthetic': True, 'expected_label': trajectory['label'], 'trace': trace, 'result': reported}


def run_all():
    return [{'trajectory': name, 'diagnosis': (run['result']['report']['diagnosis'] or {}).get('hypothesis'),
             'outcome': run['result']['next']['kind'], 'questions': run['result']['report']['diagnostic_questions_used'],
             'improvement_verified': run['result']['report']['improvement_verified']}
            for name in TRAJECTORIES for run in [replay(name)]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario', choices=list(TRAJECTORIES) + ['all'], default='all')
    parser.add_argument('--output', type=Path, help='Save reproducible synthetic transcripts to this directory')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    names = TRAJECTORIES if args.scenario == 'all' else [args.scenario]
    results = [replay(name) for name in names]
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)
        for run in results:
            (args.output / (run['trajectory'] + '.json')).write_text(json.dumps(run, indent=2) + '\n')
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps([{'trajectory': r['trajectory'], 'diagnosis': r['result']['report']['diagnosis'],
                           'outcome': r['result']['next']['kind']} for r in results], indent=2))


if __name__ == '__main__':
    main()
