"""Registry integrity tests using copies and temporary files, never live writes."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import registry


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.data = registry.load(ROOT / 'data' / 'registry.json')
        self.asset = self.data['records'][0]['id']

    def cli(self, path, *args):
        return subprocess.run([sys.executable, str(ROOT / 'registry.py'), '--file', str(path), *args],
                              capture_output=True, text=True)

    def test_update_and_retirement_preserve_identity_and_history(self):
        original = copy.deepcopy(self.data)
        changed = registry.append(self.data, self.asset, 'updated', {'title': 'Updated public demo'})
        retired = registry.append(changed, self.asset, 'retired', {'reason': 'Demonstration complete'})
        for field in ('id', 'barcode_number', 'created_at'):
            self.assertEqual(original['records'][0][field], retired['records'][0][field])
        self.assertEqual(retired['records'][0]['status'], 'retired')
        self.assertEqual(retired['records'][0]['title'], 'Updated public demo')
        self.assertEqual(len(retired['records']), len(original['records']))
        self.assertEqual(retired['events'][:len(original['events'])], original['events'])
        registry.extends(original, changed)
        registry.extends(changed, retired)
        self.assertEqual(self.data, original)

    def test_retired_identity_cannot_change_or_be_reissued(self):
        retired = registry.append(self.data, self.asset, 'retired', {'reason': 'End of demo'})
        for action, changes in [('updated', {'title': 'Reused'}),
                                ('retired', {'reason': 'Again'}),
                                ('registered', self.data['events'][0]['changes'])]:
            with self.subTest(action=action), self.assertRaises(ValueError):
                registry.append(retired, self.asset, action, changes)

    def test_decimal_roundtrip_and_leading_zeroes(self):
        for record in self.data['records']:
            value = record['barcode_number']
            self.assertIsInstance(value, str)
            self.assertRegex(value, r'^[0-9]{39}$')
            self.assertEqual(str(uuid.UUID(int=int(value))), record['id'])
            self.assertEqual(registry.number(record['id']), value)
        # Fixed UUID4 fixture forces padding independently of the saved examples.
        low = '00000000-0000-4000-8000-000000000001'
        self.assertTrue(registry.number(low).startswith('0'))
        self.assertEqual(str(uuid.UUID(int=int(registry.number(low)))), low)

    def test_numeric_precision_and_encoding_drift_rejected(self):
        value = self.data['records'][0]['barcode_number']
        for replacement in (int(value), float(value), str(int(float(value))).zfill(39), value[:-1], '0' * 39):
            candidate = copy.deepcopy(self.data)
            candidate['records'][0]['barcode_number'] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                registry.validate(candidate)

    def test_duplicate_asset_registration_rejected(self):
        with self.assertRaisesRegex(ValueError, 'already issued'):
            registry.append(self.data, self.asset, 'registered', self.data['events'][0]['changes'])

    def test_duplicate_record_rejected(self):
        self.data['records'].append(copy.deepcopy(self.data['records'][0]))
        with self.assertRaises(ValueError):
            registry.validate(self.data)

    def test_duplicate_event_id_rejected(self):
        with patch.object(registry.uuid, 'uuid4', return_value=uuid.UUID(self.data['events'][0]['id'])):
            with self.assertRaisesRegex(ValueError, 'Duplicate event ID'):
                registry.append(self.data, self.asset, 'updated', {'title': 'Change'})

    def test_immutable_fields_cannot_be_updated(self):
        for field in ('id', 'barcode_number', 'created_at', 'kind', 'demonstration'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                registry.append(self.data, self.asset, 'updated', {field: 'replacement'})

    def test_consistent_history_rewrite_requires_previous_to_detect(self):
        rewritten = copy.deepcopy(self.data)
        rewritten['events'][0]['changes']['title'] = 'Rewritten origin'
        rewritten['records'][0]['title'] = 'Rewritten origin'
        registry.validate(rewritten)
        with self.assertRaisesRegex(ValueError, 'history'):
            registry.extends(self.data, rewritten)

    def test_valid_but_truncated_history_rejected_by_extends(self):
        truncated = copy.deepcopy(self.data)
        truncated['events'].pop()
        truncated['records'].pop()
        registry.validate(truncated)
        with self.assertRaisesRegex(ValueError, 'history'):
            registry.extends(self.data, truncated)

    def test_record_only_mutation_rejected(self):
        self.data['records'][0]['title'] = 'Not in history'
        with self.assertRaises(ValueError):
            registry.validate(self.data)

    def test_malicious_addresses_rejected(self):
        for value in ('javascript:alert(1)', 'http://example.com', '//example.com',
                      'https://user:secret@example.com', 'https://@example.com',
                      'https://:@example.com', 'https://example.com\\@evil.example',
                      'https://example.com\n.evil.example', 'https://exa%0ample.com',
                      'https://example.com:0', 'https://example.com:65536', 'https:///missing-host'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                registry.https(value)

    def test_valid_https_record_url(self):
        registry.https('https://example.com:443/assets/demo?view=public#details')

    def test_duplicate_json_properties_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'registry.json'
            path.write_text('{"schema":"globalgrid.identity.v1","schema":"globalgrid.identity.v1","records":[],"events":[]}')
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON property'):
                registry.load(path)

    def test_cli_refuses_invalid_mutation_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'registry.json'
            registry.save(path, self.data)
            original = path.read_bytes()
            for args in [('update', self.asset, '--url', 'javascript:alert(1)'),
                         ('update', self.asset),
                         ('retire', str(uuid.uuid4()), '--reason', 'Unknown')]:
                result = self.cli(path, *args)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['registry.json'])

    def test_cli_requires_public_acknowledgment_before_creating_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'registry.json'
            result = self.cli(path, 'register', '--title', 'Private by default',
                              '--kind', 'cable', '--url', 'https://example.com')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(path.exists())

    def test_refused_atomic_replace_preserves_file_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'registry.json'
            registry.save(path, self.data)
            original = path.read_bytes()
            changed = registry.append(self.data, self.asset, 'updated', {'title': 'Pending'})
            with patch.object(registry.os, 'replace', side_effect=PermissionError('write refused')):
                with self.assertRaises(PermissionError):
                    registry.save(path, changed)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['registry.json'])

    def test_cli_previous_detects_history_rewrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous, current = Path(tmp) / 'previous.json', Path(tmp) / 'registry.json'
            registry.save(previous, self.data)
            altered = copy.deepcopy(self.data)
            altered['events'][0]['changes']['title'] = 'Altered'
            altered['records'][0]['title'] = 'Altered'
            registry.save(current, altered)
            original = current.read_bytes()
            result = self.cli(current, 'validate', '--previous', str(previous))
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(current.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
