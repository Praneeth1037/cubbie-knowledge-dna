"""Knowledge DNA 3.0 JSON CLI. Local, offline, bounded; no native Cubbie API calls."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid
import zlib

try:
    from .investigation import InvestigationEngine, InvestigationError
    from .profile_store import ProfileStore, StoreError
except ImportError:
    from investigation import InvestigationEngine, InvestigationError
    from profile_store import ProfileStore, StoreError

MUTATIONS = {'start', 'restart', 'answer', 'repair', 'skip', 'verify'}
READS = {'resume', 'report'}


def pack(state):
    raw = json.dumps(state, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()
    if len(raw) > 60000:
        raise InvestigationError('Session exceeds the bounded continuation size')
    return base64.urlsafe_b64encode(zlib.compress(raw, 9)).decode()


def unpack(token):
    if not isinstance(token, str) or len(token) > 12000:
        raise InvestigationError('Invalid continuation token')
    try:
        compressed = base64.b64decode(token, altchars=b'-_', validate=True)
        decoder = zlib.decompressobj()
        raw = decoder.decompress(compressed, 60001)
        if len(raw) > 60000 or not decoder.eof or decoder.unused_data:
            raise ValueError('Invalid compressed state')
        value = json.loads(raw)
        if not isinstance(value, dict) or type(value.get('revision')) is not int:
            raise ValueError('Invalid checkpoint')
        return value
    except (ValueError, zlib.error, UnicodeError, RecursionError) as exc:
        raise InvestigationError('Unreadable continuation token') from exc


class DiagnosticService:
    def __init__(self, store_factory=ProfileStore):
        self.engine = InvestigationEngine()
        self.store_factory = store_factory

    def advance(self, state, request):
        action = request['action']
        if action in {'start', 'restart'}:
            session = state.get('session')
            if not session or action == 'restart':
                session = self.engine.start(request)
            else:
                self.engine.validate(session)
            return {'session': session, 'revision': state.get('revision', 0) + 1}
        if not state.get('session'):
            raise InvestigationError('Start an investigation first', 'not_started')
        self.engine.validate(state['session'])
        if action in READS:
            return state
        if (request.get('session_id') != state['session']['id']
                or type(request.get('revision')) is not int or request['revision'] != state['revision']):
            raise InvestigationError('This turn is stale; resume the current session.', 'stale_turn')
        return {'session': self.engine.apply(state['session'], request), 'revision': state['revision'] + 1}

    def render(self, state, request, storage):
        result = self.engine.report(state['session'], full=request['action'] == 'report')
        result['revision'] = state['revision']
        result['storage'] = storage
        result['continuation'] = pack(state)
        raw = json.dumps(state['session']['observations'], sort_keys=True, separators=(',', ':')).encode()
        result['execution'] = {'engine': 'knowledge-dna', 'version': '3.0', 'command': request['action'],
                               'run_id': uuid.uuid4().hex[:12], 'observations': len(state['session']['observations']),
                               'evidence_digest': hashlib.sha256(raw).hexdigest()[:16]}
        # Keep normal text concise; developer-only report carries a bounded observation path.
        if len(json.dumps(result, ensure_ascii=False)) > 7900 and 'investigation' in result:
            result['investigation']['sources'] = [dict(s, excerpt=s.get('excerpt', '')[:60]) for s in result['investigation']['sources']]
            result['investigation']['path'] = [dict(o, answer=o['answer'][:40]) for o in result['investigation']['path']]
        if len(json.dumps(result, ensure_ascii=False)) > 7900:
            raise InvestigationError('Report exceeded the host read limit', 'report_too_large')
        return result

    def handle(self, request):
        if not isinstance(request, dict):
            raise InvestigationError('Request must be an object')
        action = request.get('action')
        if not isinstance(action, str) or action not in MUTATIONS | READS | {'storage-check', 'recover'}:
            raise InvestigationError('Unsupported action')
        learner = request.get('learner_id', 'student')
        if 'temporary' in request and type(request['temporary']) is not bool:
            raise InvestigationError('temporary must be a boolean')
        if not isinstance(learner, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}', learner):
            raise InvestigationError('Use an opaque learner ID with at most 64 letters, digits, underscores or hyphens')
        advanced = None
        failure = None
        if not request.get('temporary'):
            try:
                store = self.store_factory()
                if action == 'storage-check':
                    checked = store.check()
                    checked['storage'].update(mode='persistent', saved=False)
                    return checked
                if action == 'recover':
                    return {'ok': True, 'recovery': store.recover(learner), 'next': {'kind': 'not_started'}}

                def transition(profile):
                    nonlocal advanced
                    record = profile.get('forensics', {'version': 3, 'current': None, 'history': []})
                    if not isinstance(record, dict) or record.get('version') != 3 or not isinstance(record.get('history'), list):
                        raise InvestigationError('Invalid forensic profile; preserve it.', 'corrupt_profile')
                    state = {'session': record.get('current'), 'revision': profile['revision']}
                    advanced = self.advance(state, request)
                    if action == 'restart' and state['session']:
                        record['history'] = (record['history'] + [state['session']])[-10:]
                    record['current'] = advanced['session']
                    profile['forensics'] = record
                    return profile

                if action in MUTATIONS:
                    profile = store.update(learner, transition)
                    advanced['revision'] = profile['revision']
                else:
                    profile = store.load(learner)
                    record = profile.get('forensics', {})
                    advanced = {'session': record.get('current'), 'revision': profile['revision']}
                    if not advanced['session']:
                        return {'ok': True, 'engine_version': '3.0', 'next': {'kind': 'not_started'},
                                'storage': dict(store.storage_info(), mode='persistent', saved=False)}
                return self.render(advanced, request, dict(store.storage_info(), mode='persistent', saved=True))
            except InvestigationError as exc:
                if exc.code != 'corrupt_profile':
                    raise
                failure = {'code': exc.code, 'message': str(exc)}
                advanced = None
            except (OSError, StoreError) as exc:
                if getattr(exc, 'code', '') == 'invalid_learner_id':
                    raise
                failure = {'code': getattr(exc, 'code', 'io_error'), 'message': str(exc)}
        if action == 'recover':
            raise InvestigationError('Recovery requires writable persistent storage')
        storage = {'mode': 'temporary', 'saved': False,
                   'notice': 'Progress is not saved to disk. Pass the continuation token on every following command.',
                   'error': failure}
        if action == 'storage-check':
            return {'ok': True, 'engine_version': '3.0', 'storage': storage}
        if advanced is None:
            state = unpack(request['continuation']) if request.get('continuation') else {'session': None, 'revision': 0}
            if not state['session'] and action not in {'start', 'restart'}:
                raise InvestigationError('No saved state is available; supply the previous continuation or start a temporary session.', 'continuation_required')
            advanced = self.advance(state, request)
        return self.render(advanced, request, storage)


def no_constants(value):
    raise InvestigationError('Nonfinite JSON values are not accepted')


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        print(json.dumps({'ok': False, 'error': {'code': 'invalid_input', 'message': message}}))
        raise SystemExit(2)


def main():
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument('command', nargs='?', choices=sorted(MUTATIONS | READS | {'storage-check', 'demo', 'recover'}))
    parser.add_argument('--input', type=Path, help='JSON request file; otherwise read JSON from stdin')
    parser.add_argument('--sample', action='store_true', help='Run an isolated deterministic demo without touching learner records')
    args = parser.parse_args()
    try:
        if args.command == 'demo' or args.sample:
            try:
                from .demo_runner import run_all
            except ImportError:
                from demo_runner import run_all
            print(json.dumps(run_all(), ensure_ascii=False))
            return 0
        if args.input:
            with args.input.open(encoding='utf-8') as handle:
                raw = handle.read(24001)
        else:
            raw = '' if args.command in {'storage-check', 'recover', 'report', 'resume'} and sys.stdin.isatty() else sys.stdin.read(24001)
        if len(raw) > 24000:
            raise InvestigationError('Request exceeds 24000 characters')
        request = json.loads(raw, parse_constant=no_constants) if raw.strip() else {}
        if not isinstance(request, dict):
            raise InvestigationError('Request must be an object')
        if args.command:
            if request.get('action', args.command) != args.command:
                raise InvestigationError('Command and JSON action disagree')
            request['action'] = args.command
        print(json.dumps(DiagnosticService().handle(request), ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
        print(json.dumps({'ok': False, 'error': {'code': getattr(exc, 'code', 'invalid_input'), 'message': str(exc)}}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
