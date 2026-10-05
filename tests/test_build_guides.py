import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml
from scripts.build_guides import build


class BuildTests(unittest.TestCase):
    def setup_root(self, path, records):
        (path / 'guides').mkdir()
        (path / 'README.md').write_text('<!-- WALKTHROUGHS:START -->\n<!-- WALKTHROUGHS:END -->', encoding='utf-8')
        (path / 'guides.yml').write_text(yaml.safe_dump({'guides': records}), encoding='utf-8')

    def item(self, **changes):
        return {'id': 'eve-story', 'patch_repo': 'eve-zero-kr-patch', 'title': '직접 만든 공략', 'file': 'guides/story.md', 'original': True, **changes}

    def test_empty_and_registered_markdown_linked_to_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root, [])
            self.assertEqual(build(root, {})['guides'], [])
            (root / 'guides.yml').write_text(yaml.safe_dump({'guides': [self.item()]}), encoding='utf-8')
            (root / 'guides/story.md').write_text('# 공략\n\n## 분기\n\n직접 작성한 설명.', encoding='utf-8')
            data = build(root, {'eve-zero-kr-patch': {'title': 'EVE ZERO', 'platforms': ['Dreamcast'], 'cover': 'covers/zero.webp'}})
            self.assertEqual(data['guides'][0]['game'], 'EVE ZERO')
            self.assertEqual(data['guides'][0]['patch_repo'], 'eve-zero-kr-patch')
            self.assertTrue(data['guides'][0]['url'].endswith('story.html'))
            self.assertIn('분기</h2>', (root / 'docs/guides/story.html').read_text(encoding='utf-8'))
            self.assertEqual(json.loads((root / 'docs/data/guides.json').read_text(encoding='utf-8')), data)

    def test_pdf_and_unlinked_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root, [self.item(file='guides/guide.pdf', patch_repo='', game='새 게임', platforms=['PC'])])
            (root / 'guides/guide.pdf').write_bytes(b'%PDF-test')
            data = build(root, {})
            self.assertEqual(data['guides'][0]['format'], 'PDF')
            self.assertEqual((root / 'docs/guides/guide.pdf').read_bytes(), b'%PDF-test')

    def test_download_package_preserves_document_images_and_last_collected_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root, [self.item(file='guides/eve/story.md')])
            (root / 'guides/eve/images').mkdir(parents=True)
            (root / 'guides/eve/story.md').write_text('# 공략\n\n![지도](images/map.png)', encoding='utf-8')
            (root / 'guides/eve/images/map.png').write_bytes(b'image')
            games = {'eve-zero-kr-patch': {'title': 'EVE ZERO', 'platforms': ['Dreamcast']}}
            data = build(root, games)
            guide = data['guides'][0]
            self.assertIsNone(guide['download_count'])
            with zipfile.ZipFile(root / '.local/downloads' / guide['download_asset_name']) as archive:
                self.assertEqual(archive.read('images/map.png'), b'image')
                self.assertIn('images/map.png', archive.read('story.html').decode('utf-8'))
            guide.update(download_count=12, download_url='https://example.com/download.zip')
            (root / 'docs/data/guides.json').write_text(json.dumps(data), encoding='utf-8')
            again = build(root, games)['guides'][0]
            self.assertEqual(again['download_asset_name'], guide['download_asset_name'])
            self.assertEqual(again['download_count'], 12)
            (root / 'guides/eve/images/map.png').write_bytes(b'new image')
            changed = build(root, games)['guides'][0]
            self.assertNotEqual(changed['download_asset_name'], guide['download_asset_name'])
            self.assertIsNone(changed['download_count'])


    def test_html_is_published_without_rewriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root, [self.item(file='guides/guide.html')])
            payload = '<!doctype html><html lang="ko"><script>window.guideReady=true</script><body>직접 만든 인터랙티브 공략</body></html>'
            (root / 'guides/guide.html').write_text(payload, encoding='utf-8')
            data = build(root, {'eve-zero-kr-patch': {'title': 'EVE ZERO', 'platforms': ['Dreamcast']}})
            self.assertEqual(data['guides'][0]['format'], 'HTML')
            self.assertTrue(data['guides'][0]['url'].endswith('guide.html'))
            self.assertEqual((root / 'docs/guides/guide.html').read_text(encoding='utf-8'), payload)

    def test_missing_files_unconfirmed_ownership_and_outside_paths_are_rejected(self):
        for changes in ({'original': False}, {'file': '../secret.pdf'}, {'file': 'guides/missing.pdf'}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                self.setup_root(root, [self.item(**changes)])
                with self.assertRaises(ValueError): build(root, {})
                self.assertFalse((root / 'docs/data/guides.json').exists())

    def test_unknown_patch_fails_before_publication(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.setup_root(root, [self.item()])
            (root / 'guides/story.md').write_text('공략', encoding='utf-8')
            with self.assertRaises(ValueError): build(root, {})
