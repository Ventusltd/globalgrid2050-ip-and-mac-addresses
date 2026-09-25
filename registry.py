"""Small public identity registry. UUIDs identify assets, not network interfaces."""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import tempfile
import os
from urllib.parse import urlsplit
import uuid
import ipaddress

ROOT = Path(__file__).resolve().parent
DEFAULT = ROOT / 'data' / 'registry.json'
KINDS = {'solar-panel', 'cable', 'transformer', 'substation', 'inverter', 'site', 'software'}
SCHEMA = 'globalgrid.identity.v1'

def require(condition, message):
    if not condition:
        raise ValueError(message)

def identifier(value):
    require(isinstance(value, str), 'UUID must be text')
    parsed = uuid.UUID(value)
    require(str(parsed) == value and parsed.version == 4 and parsed.variant == uuid.RFC_4122, 'Canonical UUID4 required')
    return parsed

def number(value):
    return str(identifier(value).int).zfill(39)

def timestamp(value):
    require(isinstance(value, str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value)), 'UTC timestamp required')
    datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ')

def text(value):
    require(isinstance(value, str) and 0 < len(value.strip()) <= 240 and not any(ord(c) < 32 for c in value), 'Expected bounded nonempty text')

def https(value):
    require(isinstance(value, str) and len(value) <= 2048 and not any(c.isspace() or ord(c) < 32 for c in value) and '\\' not in value, 'Invalid address')
    parsed = urlsplit(value)
    require(parsed.scheme == 'https' and parsed.hostname and parsed.username is None and parsed.password is None and '%' not in parsed.netloc, 'HTTPS address without credentials required')
    try:
        ipaddress.ip_address(parsed.hostname)
    except ValueError:
        host = parsed.hostname.encode('idna').decode('ascii')
        require(len(host) <= 253 and all(re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', label) for label in host.rstrip('.').split('.')), 'Invalid hostname')
    if parsed.port is not None:
        require(0 < parsed.port <= 65535, 'Invalid port')

def validate(data):
    require(isinstance(data, dict) and set(data) == {'schema', 'records', 'events'}, 'Invalid registry fields')
    require(data['schema'] == SCHEMA and isinstance(data['records'], list) and isinstance(data['events'], list), 'Invalid schema')
    state, event_ids = {}, set()
    for event in data['events']:
        require(isinstance(event, dict) and set(event) == {'id', 'asset_id', 'action', 'at', 'changes'}, 'Invalid event fields')
        identifier(event['id']); identifier(event['asset_id']); timestamp(event['at'])
        require(event['id'] not in event_ids, 'Duplicate event ID'); event_ids.add(event['id'])
        asset, changes = event['asset_id'], event['changes']
        require(isinstance(changes, dict), 'Changes must be an object')
        if event['action'] == 'registered':
            require(asset not in state, 'Asset ID already issued')
            require(set(changes) == {'title', 'kind', 'record_url', 'demonstration'}, 'Registration fields invalid')
            require(changes['kind'] in KINDS and type(changes['demonstration']) is bool, 'Invalid kind/demo flag')
            text(changes['title']); https(changes['record_url'])
            state[asset] = {'id': asset, 'barcode_number': number(asset), **changes, 'status': 'active', 'created_at': event['at'], 'updated_at': event['at']}
        else:
            require(asset in state, 'Unknown asset')
            record = state[asset]
            require(record['status'] == 'active', 'Retired identity is terminal')
            require(event['at'] >= record['updated_at'], 'Event time moved backwards')
            if event['action'] == 'updated':
                require(bool(changes) and set(changes) <= {'title', 'record_url'}, 'Only title and record_url can change')
                if 'title' in changes: text(changes['title'])
                if 'record_url' in changes: https(changes['record_url'])
                record.update(changes)
            elif event['action'] == 'retired':
                require(set(changes) == {'reason'}, 'Retirement reason required'); text(changes['reason'])
                record['status'] = 'retired'
            else:
                raise ValueError('Unknown event action')
            record['updated_at'] = event['at']
    require(data['records'] == list(state.values()), 'Records must exactly equal event replay; identity and history cannot drift')
    return data

def load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON property: ' + key); result[key] = value
        return result
    return validate(json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=unique))

def append(data, asset, action, changes):
    validate(data)
    result = copy.deepcopy(data)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    result['events'].append({'id': str(uuid.uuid4()), 'asset_id': asset, 'action': action, 'at': now, 'changes': changes})
    if action == 'registered':
        result['records'].append({'id': asset, 'barcode_number': number(asset), **changes, 'status': 'active', 'created_at': now, 'updated_at': now})
    else:
        record = next((r for r in result['records'] if r['id'] == asset), None)
        require(record is not None, 'Unknown asset')
        if action == 'updated': record.update(changes)
        if action == 'retired': record['status'] = 'retired'
        record['updated_at'] = now
    return validate(result)

def extends(previous, current):
    validate(previous); validate(current)
    require(current['events'][:len(previous['events'])] == previous['events'], 'Published event history cannot be rewritten or truncated')

def save(path, data):
    validate(data)
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name); json.dump(data, handle, indent=2); handle.write('\n')
    try:
        load(temporary)
        os.replace(temporary, path)
    finally:
        if temporary.exists(): temporary.unlink()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, default=DEFAULT)
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('validate'); check.add_argument('--previous', type=Path)
    register = commands.add_parser('register')
    register.add_argument('--title', required=True); register.add_argument('--kind', choices=sorted(KINDS), required=True)
    register.add_argument('--url', required=True); register.add_argument('--demo', action='store_true')
    register.add_argument('--public', action='store_true', required=True, help='Acknowledge this record is suitable for public publication')
    update = commands.add_parser('update'); update.add_argument('id'); update.add_argument('--title'); update.add_argument('--url')
    retire = commands.add_parser('retire'); retire.add_argument('id'); retire.add_argument('--reason', required=True)
    args = parser.parse_args()
    data = load(args.file) if args.file.exists() else {'schema': SCHEMA, 'records': [], 'events': []}
    if args.command == 'validate':
        require(args.file.exists(), 'Registry missing')
        if args.previous: extends(load(args.previous), data)
        print(json.dumps({'status': 'pass', 'records': len(data['records']), 'distinct_ids': len({r['id'] for r in data['records']}), 'events': len(data['events'])})); return
    if args.command == 'register':
        asset = str(uuid.uuid4())
        result = append(data, asset, 'registered', {'title': args.title, 'kind': args.kind, 'record_url': args.url, 'demonstration': args.demo})
    elif args.command == 'update':
        asset = args.id; changes = {}
        if args.title is not None: changes['title'] = args.title
        if args.url is not None: changes['record_url'] = args.url
        result = append(data, asset, 'updated', changes)
    else:
        asset = args.id; result = append(data, asset, 'retired', {'reason': args.reason})
    save(args.file, result); print(asset)

if __name__ == '__main__':
    main()
