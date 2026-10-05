import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from scripts.guide_downloads import GitHub, REPOSITORY, download_stats, package, publish, release_tag


class FakeGitHub:
    def __init__(self):
        self.release = None
        self.files = []
        self.uploads = 0
        self.creations = 0

    def get_release(self, tag):
        return self.release

    def create_release(self, guide):
        self.creations += 1
        self.release = {'id': 17, 'tag_name': release_tag(guide['id']), 'draft': False, 'prerelease': False}
        return self.release

    def assets(self, release_id):
        return self.files.copy()

    def upload(self, release_id, name, payload):
        self.uploads += 1
        self.files.append({'name': name, 'state': 'uploaded', 'size': len(payload), 'download_count': 0,
                           'browser_download_url': f'https://github.com/{REPOSITORY}/releases/download/guide-a/{name}'})
        return self.files[-1]


class DownloadTests(unittest.TestCase):
    def prepare(self, root, content):
        name, payload = package('a', {'guide.html': content})
        (root / '.local/downloads').mkdir(parents=True, exist_ok=True)
        (root / '.local/downloads' / name).write_bytes(payload)
        guide = {'id': 'a', 'title': '공략', 'url': 'https://example.com/guide.html',
                 'download_release_tag': 'guide-a', 'download_asset_name': name}
        (root / 'docs/data').mkdir(parents=True, exist_ok=True)
        (root / 'docs/data/guides.json').write_text(json.dumps({'guides': [guide]}), encoding='utf-8')
        return guide

    def test_zip_is_reproducible_and_includes_relative_images(self):
        entries = {'guide.html': b'<img src="images/map.png">', 'images/map.png': b'image'}
        first = package('a', entries)
        self.assertEqual(first, package('a', dict(reversed(list(entries.items())))))
        with zipfile.ZipFile(io.BytesIO(first[1])) as archive:
            self.assertEqual(archive.read('images/map.png'), b'image')
        self.assertNotEqual(first[0], package('a', {**entries, 'images/map.png': b'updated'})[0])

    def test_repeat_runs_do_not_reset_downloads_and_new_versions_preserve_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, client = Path(tmp), FakeGitHub()
            first = self.prepare(root, b'first')
            self.assertEqual(publish(root, client)['guides'][0]['download_count'], 0)
            client.files[0]['download_count'] = 9
            self.assertEqual(publish(root, client)['guides'][0]['download_count'], 9)
            self.assertEqual((client.creations, client.uploads), (1, 1))
            second = self.prepare(root, b'second')
            result = publish(root, client)['guides'][0]
            self.assertEqual(result['download_count'], 9)
            self.assertTrue(result['download_url'].endswith(second['download_asset_name']))
            self.assertFalse(result['download_url'].endswith(first['download_asset_name']))
            client.files[1]['download_count'] = 3
            self.assertEqual(publish(root, client)['guides'][0]['download_count'], 12)
            self.assertEqual((client.creations, client.uploads, len(client.files)), (1, 2, 2))

    def test_unrelated_files_and_incomplete_uploads_are_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, client = Path(tmp), FakeGitHub()
            guide = self.prepare(root, b'guide')
            publish(root, client)
            client.files.extend([{'name': 'other.zip', 'state': 'uploaded', 'download_count': 999},
                                 {'name': 'a-' + 'f' * 16 + '.zip', 'state': 'starter', 'download_count': 88}])
            self.assertEqual(download_stats(guide, client.files)['download_count'], 0)
            client.files[0]['download_count'] = -1
            with self.assertRaises(ValueError):
                download_stats(guide, client.files)

    def test_missing_current_asset_and_unsafe_urls_are_not_reported_as_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, client = Path(tmp), FakeGitHub()
            guide = self.prepare(root, b'guide')
            with self.assertRaises(ValueError):
                download_stats(guide, [])
            publish(root, client)
            client.files[0]['browser_download_url'] = 'https://other.example/guide.zip'
            with self.assertRaises(ValueError):
                download_stats(guide, client.files)

    def test_conflicting_upload_and_changed_package_are_rejected_without_overwriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, client = Path(tmp), FakeGitHub()
            guide = self.prepare(root, b'guide')
            publish(root, client)
            client.files[0]['size'] += 1
            with self.assertRaises(ValueError):
                publish(root, client)
            self.assertEqual(client.uploads, 1)
            (root / '.local/downloads' / guide['download_asset_name']).write_bytes(b'changed')
            with self.assertRaises(ValueError):
                publish(root, client)

    def test_draft_release_is_not_published_automatically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, client = Path(tmp), FakeGitHub()
            self.prepare(root, b'guide')
            client.release = {'id': 17, 'tag_name': 'guide-a', 'draft': True}
            with self.assertRaises(ValueError):
                publish(root, client)
            self.assertEqual(client.uploads, 0)

    def test_api_pagination_and_only_a_real_404_allows_release_creation(self):
        client = GitHub('test-token')
        with patch.object(client, 'request', side_effect=[[{'id': n} for n in range(100)], [{'id': 100}]]) as request:
            self.assertEqual(len(client.assets(17)), 101)
            self.assertTrue(request.call_args_list[1].args[0].endswith('page=2'))
        with patch.object(client, 'request', side_effect=HTTPError('https://api.github.com/', 404, 'Not found', {}, None)):
            self.assertIsNone(client.get_release('guide-a'))
        with patch.object(client, 'request', side_effect=HTTPError('https://api.github.com/', 403, 'Forbidden', {}, None)):
            with self.assertRaises(HTTPError):
                client.get_release('guide-a')
