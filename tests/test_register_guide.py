import tempfile
import unittest
from pathlib import Path

import yaml
from scripts.register_guide import register


class RegistrationTests(unittest.TestCase):
    def root(self, path):
        (path / 'guides.yml').write_text('guides: []\n', encoding='utf-8')
        source = path / 'incoming.pdf'
        source.write_bytes(b'%PDF-first')
        return source

    def options(self, **changes):
        return {'guide_id': 'eve-zero-story', 'title': 'EVE ZERO 공략', 'original': True,
                'patch_repo': 'eve-zero-kr-patch', 'patch_games': {'eve-zero-kr-patch': {}}, **changes}

    def test_register_then_update_preserves_id_and_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.root(root)
            first = register(root, source, **self.options())
            self.assertEqual(first['action'], 'registered')
            self.assertEqual(source.read_bytes(), b'%PDF-first')
            source.write_bytes(b'%PDF-second')
            second = register(root, source, **self.options())
            records = yaml.safe_load((root / 'guides.yml').read_text(encoding='utf-8'))['guides']
            self.assertEqual(second['action'], 'updated')
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]['id'], 'eve-zero-story')
            self.assertEqual((root / second['file']).read_bytes(), b'%PDF-second')
            self.assertEqual((Path(second['backup']) / 'guide-before.pdf').read_bytes(), b'%PDF-first')

    def test_unconfirmed_or_unknown_game_fails_before_writing(self):
        for changes in ({'original': False}, {'patch_games': {}}, {'guide_id': '../bad'}):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = self.root(root)
                before = (root / 'guides.yml').read_bytes()
                with self.assertRaises(ValueError): register(root, source, **self.options(**changes))
                self.assertEqual((root / 'guides.yml').read_bytes(), before)
                self.assertFalse((root / 'guides').exists())

    def test_new_id_does_not_duplicate_existing_same_game_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.root(root)
            register(root, source, **self.options())
            with self.assertRaises(ValueError): register(root, source, **self.options(guide_id='another-id'))
            self.assertEqual(len(yaml.safe_load((root / 'guides.yml').read_text(encoding='utf-8'))['guides']), 1)

    def test_same_id_cannot_silently_move_to_another_game(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.root(root)
            register(root, source, **self.options())
            with self.assertRaises(ValueError):
                register(root, source, **self.options(patch_repo='other', patch_games={'other': {}}))

    def test_standalone_game_and_markdown_register_without_patch_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.root(root).with_suffix('.md')
            source.write_text('# 직접 작성한 공략', encoding='utf-8')
            result = register(root, source, **self.options(patch_repo='', game='내 게임', platforms=['PC']))
            record = yaml.safe_load((root / 'guides.yml').read_text(encoding='utf-8'))['guides'][0]
            self.assertEqual(record['patch_repo'], '')
            self.assertEqual(record['game'], '내 게임')
            self.assertEqual((root / result['file']).read_text(encoding='utf-8'), '# 직접 작성한 공략')
